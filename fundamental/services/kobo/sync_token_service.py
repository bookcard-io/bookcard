# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Kobo sync token service.

Handles parsing and management of Kobo sync tokens from request headers.
Sync tokens track the state of synchronization between the device and server.
"""

from __future__ import annotations

import base64
import binascii
import json
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


def _parse_timestamp(ts_str: str | None) -> datetime | None:
    """Parse ISO format timestamp string to datetime.

    Kobo uses ISO format timestamps like "2025-01-15T12:00:00Z".
    Returns None if the string is empty or cannot be parsed.

    Parameters
    ----------
    ts_str : str | None
        ISO format timestamp string, or None/empty string.

    Returns
    -------
    datetime | None
        Parsed datetime with UTC timezone, or None if parsing fails.
    """
    if not ts_str:
        return None
    with suppress(ValueError, AttributeError):
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    return None


@dataclass
class SyncToken:
    """Kobo sync token for tracking synchronization state.

    Sync tokens are passed in request headers and track the last modified
    timestamps for different types of data (books, reading states, tags, etc.).
    This allows incremental synchronization by only sending changes since
    the last sync.

    Attributes
    ----------
    books_last_modified : datetime
        Last modification time for books to sync.
    books_last_created : datetime
        Last creation time for books (to distinguish new vs changed).
    reading_state_last_modified : datetime
        Last modification time for reading states.
    tags_last_modified : datetime
        Last modification time for tags/shelves.
    archive_last_modified : datetime
        Last modification time for archived books.
    """

    books_last_modified: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )
    books_last_created: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )
    reading_state_last_modified: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )
    tags_last_modified: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )
    archive_last_modified: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=UTC)
    )

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> SyncToken:
        """Parse sync token from request headers.

        Kobo sync tokens are passed in the `x-kobo-sync` header as a
        base64-encoded JSON object.

        Parameters
        ----------
        headers : dict[str, str]
            Request headers dictionary.

        Returns
        -------
        SyncToken
            Parsed sync token. Returns default values if header is missing.
        """
        sync_header = headers.get("x-kobo-sync", "")
        if not sync_header:
            return cls()

        try:
            # Decode base64
            decoded = base64.b64decode(sync_header)
            data = json.loads(decoded.decode("utf-8"))

            # Parse timestamps, defaulting to datetime.min for missing/invalid values
            def parse_timestamp(ts_str: str | None) -> datetime:
                parsed = _parse_timestamp(ts_str)
                return (
                    parsed if parsed is not None else datetime.min.replace(tzinfo=UTC)
                )

            return cls(
                books_last_modified=parse_timestamp(data.get("BooksLastModified")),
                books_last_created=parse_timestamp(data.get("BooksLastCreated")),
                reading_state_last_modified=parse_timestamp(
                    data.get("ReadingStateLastModified")
                ),
                tags_last_modified=parse_timestamp(data.get("TagsLastModified")),
                archive_last_modified=parse_timestamp(data.get("ArchiveLastModified")),
            )
        except (ValueError, json.JSONDecodeError, binascii.Error):
            # If parsing fails, return default token
            return cls()

    def to_headers(self, headers: dict[str, str]) -> None:
        """Add sync token to response headers.

        Encodes the sync token as base64 JSON and adds it to the headers
        dictionary.

        Parameters
        ----------
        headers : dict[str, str]
            Response headers dictionary to update.
        """

        def format_timestamp(dt: datetime) -> str:
            """Format datetime as Kobo timestamp string."""
            if dt == datetime.min.replace(tzinfo=UTC):
                return ""
            # Ensure UTC
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = {
            "BooksLastModified": format_timestamp(self.books_last_modified),
            "BooksLastCreated": format_timestamp(self.books_last_created),
            "ReadingStateLastModified": format_timestamp(
                self.reading_state_last_modified
            ),
            "TagsLastModified": format_timestamp(self.tags_last_modified),
            "ArchiveLastModified": format_timestamp(self.archive_last_modified),
        }

        # Remove empty values
        data = {k: v for k, v in data.items() if v}

        if data:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
            headers["x-kobo-sync"] = encoded

    def merge_from_store_response(self, response: httpx.Response) -> None:
        """Merge sync token state from Kobo Store API response.

        When proxying to Kobo Store, merge the sync token state from
        the store response to include store-side changes.

        Parameters
        ----------
        response : httpx.Response
            HTTPX Response object from Kobo Store.
        """
        store_sync_header = response.headers.get("x-kobo-sync", "")
        if not store_sync_header:
            return

        with suppress(ValueError, json.JSONDecodeError, binascii.Error):
            decoded = base64.b64decode(store_sync_header)
            data = json.loads(decoded.decode("utf-8"))
            self._merge_timestamps_from_data(data)

    def _merge_timestamps_from_data(self, data: dict[str, object]) -> None:
        """Merge timestamps from parsed sync token data.

        Parameters
        ----------
        data : dict[str, object]
            Parsed sync token data.
        """
        self._merge_timestamp(data, "BooksLastModified", "books_last_modified")
        self._merge_timestamp(data, "BooksLastCreated", "books_last_created")
        self._merge_timestamp(
            data, "ReadingStateLastModified", "reading_state_last_modified"
        )
        self._merge_timestamp(data, "TagsLastModified", "tags_last_modified")
        self._merge_timestamp(data, "ArchiveLastModified", "archive_last_modified")

    def _merge_timestamp(
        self, data: dict[str, object], key: str, attr_name: str
    ) -> None:
        """Merge a single timestamp field.

        Parameters
        ----------
        data : dict[str, object]
            Parsed sync token data.
        key : str
            Data key to read.
        attr_name : str
            Attribute name to update.
        """
        if key not in data:
            return

        ts_value = data[key]
        ts_str = (
            ts_value
            if isinstance(ts_value, str)
            else str(ts_value)
            if ts_value is not None
            else None
        )
        ts = _parse_timestamp(ts_str)
        if not ts:
            return

        current_ts = getattr(self, attr_name)
        if ts > current_ts:
            setattr(self, attr_name, ts)

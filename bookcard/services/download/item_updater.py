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

"""Download item update logic.

Separates business logic for updating download items from persistence.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypeVar

from bookcard.models.pvr import DownloadItemStatus
from bookcard.pvr.models import DownloadItem
from bookcard.services.download.status_mapper import (
    ClientStatusMapper,
    DefaultStatusMapper,
)

if TYPE_CHECKING:
    from bookcard.models.pvr import DownloadItem as DBDownloadItem

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DownloadItemUpdater:
    """Handles updating download items from client information.

    Follows SRP by focusing solely on item update logic.
    """

    def __init__(self, status_mapper: ClientStatusMapper | None = None) -> None:
        """Initialize updater.

        Parameters
        ----------
        status_mapper : ClientStatusMapper | None
            Status mapper to use. If None, uses DefaultStatusMapper.
        """
        self._status_mapper = status_mapper or DefaultStatusMapper()

    def update(self, db_item: "DBDownloadItem", client_item: DownloadItem) -> None:
        """Update database item with client information.

        Parameters
        ----------
        db_item : DownloadItem
            Database record to update.
        client_item : ClientItemInfo
            Item information from client.
        """
        self._update_progress(db_item, client_item)
        self._update_status(db_item, client_item)
        self._update_metadata(db_item, client_item)
        self._handle_completion(db_item)

    def _update_progress(
        self, db_item: "DBDownloadItem", client_item: DownloadItem
    ) -> None:
        """Update download progress.

        Parameters
        ----------
        db_item : DownloadItem
            Database item to update.
        client_item : ClientItemInfo
            Client item information.
        """
        progress = self._safe_extract(client_item, "progress", float)
        if progress is not None:
            db_item.progress = progress

    def _update_status(
        self, db_item: "DBDownloadItem", client_item: DownloadItem
    ) -> None:
        """Update download status.

        Parameters
        ----------
        db_item : DownloadItem
            Database item to update.
        client_item : ClientItemInfo
            Client item information.
        """
        status_str = self._safe_extract(client_item, "status", str)
        if status_str:
            db_item.status = self._status_mapper.map(status_str)

    def _update_metadata(
        self, db_item: "DBDownloadItem", client_item: DownloadItem
    ) -> None:
        """Update download metadata.

        Parameters
        ----------
        db_item : DownloadItem
            Database item to update.
        client_item : ClientItemInfo
            Client item information.
        """
        if "size_bytes" in client_item:
            db_item.size_bytes = client_item["size_bytes"]
        if "downloaded_bytes" in client_item:
            db_item.downloaded_bytes = client_item["downloaded_bytes"]
        if "download_speed_bytes_per_sec" in client_item:
            db_item.download_speed_bytes_per_sec = client_item[
                "download_speed_bytes_per_sec"
            ]
        if "eta_seconds" in client_item:
            db_item.eta_seconds = client_item["eta_seconds"]
        if "file_path" in client_item:
            db_item.file_path = client_item["file_path"]

    def _handle_completion(self, db_item: "DBDownloadItem") -> None:
        """Handle download completion.

        Parameters
        ----------
        db_item : DownloadItem
            Database item to check.
        """
        if db_item.status == DownloadItemStatus.COMPLETED and not db_item.completed_at:
            db_item.completed_at = datetime.now(UTC)

    def _safe_extract(
        self,
        data: DownloadItem,
        key: str,
        converter: Callable[[object], T],
        default: T | None = None,
    ) -> T | None:
        """Safely extract and convert value from dictionary.

        Parameters
        ----------
        data : ClientItemInfo
            Dictionary to extract from.
        key : str
            Key to extract.
        converter : Callable[[object], T]
            Function to convert value.
        default : T | None
            Default value if extraction fails.

        Returns
        -------
        T | None
            Converted value or default.
        """
        if key not in data:
            return default
        try:
            value = data.get(key)
            if value is None:
                return default
            return converter(value)
        except (ValueError, TypeError) as e:
            logger.warning("Failed to convert %s: %s (%s)", key, data.get(key), e)
            return default

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime.

        Returns
        -------
        datetime
            Current UTC datetime.
        """
        return datetime.now(UTC)

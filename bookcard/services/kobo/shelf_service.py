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

"""Kobo shelf service.

Syncs shelves/collections to Kobo format (tags).
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.core import Book

if TYPE_CHECKING:
    from bookcard.models.shelves import Shelf
    from bookcard.repositories.kobo_repository import KoboReadingStateRepository
    from bookcard.services.kobo.sync_token_service import SyncToken
    from bookcard.services.shelf_service import ShelfService


def convert_to_kobo_timestamp_string(dt: datetime) -> str:
    """Convert datetime to Kobo timestamp string format."""
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class KoboShelfService:
    """Service for syncing shelves to Kobo format.

    Handles conversion of shelves to Kobo tags and vice versa.

    Parameters
    ----------
    session : Session
        Database session.
    shelf_service : ShelfService
        Shelf service for querying shelves.
    reading_state_repo : KoboReadingStateRepository
        Repository for reading states (for filtering).
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        shelf_service: ShelfService,
        reading_state_repo: KoboReadingStateRepository,
    ) -> None:
        self._session = session
        self._shelf_service = shelf_service
        self._reading_state_repo = reading_state_repo

    def sync_shelves(
        self,
        user_id: int,
        library_id: int,
        sync_token: SyncToken,
        book_service: object | None = None,
    ) -> list[dict[str, object]]:
        """Get shelves to sync in Kobo format.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        sync_token : SyncToken
            Sync token with last sync timestamps.
        book_service : object | None
            Optional book service for querying book UUIDs.

        Returns
        -------
        list[dict[str, object]]
            List of shelf sync results in Kobo tag format.
        """
        sync_results: list[dict[str, object]] = []
        new_tags_last_modified = sync_token.tags_last_modified

        # Get shelves modified since last sync
        shelves = self._shelf_service.list_user_shelves(
            library_id=library_id,
            user_id=user_id,
            include_public=True,
        )

        for shelf in shelves:
            # Check if modified since last sync
            if shelf.last_modified <= sync_token.tags_last_modified:
                continue

            new_tags_last_modified = max(new_tags_last_modified, shelf.last_modified)

            # Create Kobo tag
            tag = self._create_kobo_tag(shelf, book_service)
            if not tag:
                continue

            # Determine if new or changed
            shelf_created = getattr(shelf, "created", None)
            if shelf_created is None:
                continue
            if shelf_created > sync_token.tags_last_modified:
                sync_results.append({"NewTag": tag})
            else:
                sync_results.append({"ChangedTag": tag})

        sync_token.tags_last_modified = new_tags_last_modified

        return sync_results

    def _create_kobo_tag(
        self, shelf: Shelf, book_service: object | None = None
    ) -> dict[str, object] | None:
        """Create Kobo tag from shelf.

        Parameters
        ----------
        shelf : Shelf
            Shelf instance.
        book_service : object | None
            Optional book service for querying book UUIDs.

        Returns
        -------
        dict[str, object] | None
            Kobo tag dictionary or None if invalid.
        """
        items: list[dict[str, object]] = []

        # Get book UUIDs from shelf
        for book_link in shelf.book_links:
            if book_link.book_id is None:
                continue

            # Try to get book UUID from Calibre DB if book_service is available
            book_uuid = str(book_link.book_id)  # Fallback to book_id
            if book_service and hasattr(book_service, "_book_repo"):
                book_repo = getattr(book_service, "_book_repo", None)
                if book_repo and hasattr(book_repo, "get_session"):
                    with (
                        suppress(SQLAlchemyError, AttributeError, TypeError),
                        book_repo.get_session() as calibre_session,
                    ):
                        stmt = select(Book).where(Book.id == book_link.book_id)
                        book = calibre_session.exec(stmt).first()
                        if book and book.uuid:
                            book_uuid = str(book.uuid)

            items.append({
                "RevisionId": book_uuid,
                "Type": "ProductRevisionTagItem",
            })

        tag: dict[str, object] = {
            "Created": convert_to_kobo_timestamp_string(shelf.created_at),
            "Id": shelf.uuid,
            "Items": items,
            "LastModified": convert_to_kobo_timestamp_string(shelf.last_modified),
            "Name": shelf.name,
            "Type": "UserTag",
        }

        return {"Tag": tag}

    def create_shelf_from_kobo(
        self, user_id: int, library_id: int, tag_data: dict[str, object]
    ) -> Shelf:
        """Create shelf from Kobo tag data.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        tag_data : dict[str, object]
            Kobo tag data.

        Returns
        -------
        Shelf
            Created shelf.
        """
        name_value = tag_data.get("Name", "")
        name = (
            name_value
            if isinstance(name_value, str)
            else str(name_value)
            if name_value
            else ""
        )
        if not name:
            msg = "Tag name is required"
            raise ValueError(msg)

        shelf = self._shelf_service.create_shelf(
            library_id=library_id,
            user_id=user_id,
            name=name,
            description=None,
            is_public=False,
        )

        # Add items if provided
        items = tag_data.get("Items", [])
        if items and isinstance(items, list):
            # Add books to shelf based on RevisionId (book UUID)
            # This would need to query Calibre DB to find books by UUID
            pass

        return shelf

    def update_shelf_from_kobo(self, shelf: Shelf, tag_data: dict[str, object]) -> None:
        """Update shelf from Kobo tag data.

        Parameters
        ----------
        shelf : Shelf
            Shelf to update.
        tag_data : dict[str, object]
            Kobo tag data.
        """
        name = tag_data.get("Name")
        if name:
            shelf.name = str(name)
            shelf.updated_at = datetime.now(UTC)

        # Update items if provided
        items = tag_data.get("Items", [])
        if items and isinstance(items, list):
            # Update shelf books based on RevisionId
            # This would need to query Calibre DB and update book links
            pass

        self._session.flush()

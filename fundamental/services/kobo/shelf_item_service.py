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

"""Kobo shelf item service.

Handles adding and removing items from shelves.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from fundamental.repositories.shelf_repository import (
    BookShelfLinkRepository,
    ShelfRepository,
)
from fundamental.services.shelf_service import ShelfService

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.api.schemas.kobo import KoboTagItemRequest
    from fundamental.services.kobo.book_lookup_service import KoboBookLookupService


class KoboShelfItemService:
    """Service for managing shelf items.

    Handles adding and removing books from shelves based on Kobo tag item requests.

    Parameters
    ----------
    session : Session
        Database session.
    book_lookup_service : KoboBookLookupService
        Book lookup service.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        book_lookup_service: KoboBookLookupService,
    ) -> None:
        self._session = session
        self._book_lookup_service = book_lookup_service

    def add_items_to_shelf(
        self, shelf_id: int, user_id: int, item_data: KoboTagItemRequest
    ) -> None:
        """Add items to a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        user_id : int
            User ID.
        item_data : KoboTagItemRequest
            Items to add.
        """
        shelf_repo = ShelfRepository(self._session)
        link_repo = BookShelfLinkRepository(self._session)
        shelf_service = ShelfService(self._session, shelf_repo, link_repo)

        for item in item_data.Items:
            if item.get("Type") != "ProductRevisionTagItem":
                continue

            revision_id = item.get("RevisionId")
            if not revision_id:
                continue

            # Find book by UUID
            book_result = self._book_lookup_service.find_book_by_uuid(str(revision_id))
            if book_result is None:
                continue

            book_id, _book = book_result

            # Add to shelf
            with suppress(ValueError):
                # Book already in shelf, ignore
                shelf_service.add_book_to_shelf(
                    shelf_id=shelf_id,
                    book_id=book_id,
                    user_id=user_id,
                )

    def remove_items_from_shelf(
        self, shelf_id: int, user_id: int, item_data: KoboTagItemRequest
    ) -> None:
        """Remove items from a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        user_id : int
            User ID.
        item_data : KoboTagItemRequest
            Items to remove.
        """
        shelf_repo = ShelfRepository(self._session)
        link_repo = BookShelfLinkRepository(self._session)
        shelf_service = ShelfService(self._session, shelf_repo, link_repo)

        for item in item_data.Items:
            if item.get("Type") != "ProductRevisionTagItem":
                continue

            revision_id = item.get("RevisionId")
            if not revision_id:
                continue

            # Find book by UUID
            book_result = self._book_lookup_service.find_book_by_uuid(str(revision_id))
            if book_result is None:
                continue

            book_id, _book = book_result

            # Remove from shelf
            with suppress(ValueError):
                # Book not in shelf, ignore
                shelf_service.remove_book_from_shelf(
                    shelf_id=shelf_id,
                    book_id=book_id,
                    user_id=user_id,
                )

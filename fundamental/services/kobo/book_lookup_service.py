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

"""Kobo book lookup service.

Handles book lookup by UUID and related operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import select

from fundamental.models.core import Book

if TYPE_CHECKING:
    from fundamental.repositories.models import BookWithFullRelations
    from fundamental.services.book_service import BookService


class KoboBookLookupService:
    """Service for looking up books by UUID.

    Handles conversion between book UUIDs and book IDs for Kobo operations.

    Parameters
    ----------
    book_service : BookService
        Book service for querying books.
    """

    def __init__(self, book_service: BookService) -> None:
        self._book_service = book_service

    def find_book_by_uuid(self, book_uuid: str) -> tuple[int, Book] | None:
        """Find book by UUID.

        Parameters
        ----------
        book_uuid : str
            Book UUID.

        Returns
        -------
        tuple[int, Book] | None
            Tuple of (book_id, Book) if found, None otherwise.
        """
        with self._book_service._book_repo.get_session() as calibre_session:  # noqa: SLF001
            stmt = select(Book).where(Book.uuid == book_uuid)
            book = calibre_session.exec(stmt).first()
            if book is None or book.id is None:
                return None
            return (book.id, book)

    def get_book_with_relations(self, book_id: int) -> BookWithFullRelations | None:
        """Get book with full relations.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        BookWithFullRelations | None
            Book with relations if found, None otherwise.
        """
        return self._book_service.get_book_full(book_id)

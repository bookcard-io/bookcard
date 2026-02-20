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

"""Response builder for multi-library book queries.

Delegates to per-library :class:`BookResponseBuilder` instances so that
thumbnail URLs, ``library_id``, and ``library_name`` are resolved from
the correct library for each book.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.services.book_response_builder import BookResponseBuilder

if TYPE_CHECKING:
    from bookcard.api.schemas import BookRead
    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
    from bookcard.services.book_service import BookService


class MultiLibraryResponseBuilder:
    """Build :class:`BookRead` DTOs for books that span multiple libraries.

    Parameters
    ----------
    book_services : dict[int, BookService]
        Mapping of ``library_id`` to :class:`BookService`.
    """

    def __init__(self, book_services: dict[int, BookService]) -> None:
        self._builders: dict[int, BookResponseBuilder] = {
            lib_id: BookResponseBuilder(svc) for lib_id, svc in book_services.items()
        }
        self._fallback = next(iter(self._builders.values())) if self._builders else None

    def build_book_read(
        self,
        book_with_rels: BookWithRelations | BookWithFullRelations,
        full: bool = False,
    ) -> BookRead:
        """Build a single :class:`BookRead` using the correct library context.

        Parameters
        ----------
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with related metadata (must have ``library_id`` set).
        full : bool
            Include full metadata.

        Returns
        -------
        BookRead
            Book DTO with correct ``library_id``, ``library_name``, and
            thumbnail URL for its source library.

        Raises
        ------
        ValueError
            If book ID is missing.
        """
        lib_id = book_with_rels.library_id
        builder = (
            self._builders.get(lib_id) if lib_id is not None else None
        ) or self._fallback

        if builder is None:
            msg = "No response builders configured"
            raise ValueError(msg)

        return builder.build_book_read(book_with_rels, full=full)

    def build_book_read_list(
        self,
        books: list[BookWithRelations | BookWithFullRelations],
        full: bool = False,
    ) -> list[BookRead]:
        """Build a list of :class:`BookRead` DTOs.

        Parameters
        ----------
        books : list[BookWithRelations | BookWithFullRelations]
            Books with related metadata.
        full : bool
            Include full metadata.

        Returns
        -------
        list[BookRead]
            Book DTOs (skips books without IDs).
        """
        return [
            self.build_book_read(b, full=full) for b in books if b.book.id is not None
        ]

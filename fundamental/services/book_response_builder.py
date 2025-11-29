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

"""Response builder for book operations.

Handles conversion from BookWithRelations to BookRead DTOs.
Follows SRP by handling only response transformation.
"""

from fundamental.api.schemas import BookRead
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.services.book_service import BookService


class BookResponseBuilder:
    """Builder for book response DTOs.

    Handles conversion from domain models to API response models.
    Follows SRP by handling only response transformation.
    """

    def __init__(self, book_service: BookService) -> None:
        """Initialize response builder.

        Parameters
        ----------
        book_service : BookService
            Book service for generating thumbnail URLs.
        """
        self._book_service = book_service

    def build_book_read(
        self,
        book_with_rels: BookWithRelations | BookWithFullRelations,
        full: bool = False,
    ) -> BookRead:
        """Build BookRead DTO from BookWithRelations.

        Parameters
        ----------
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with related metadata.
        full : bool
            If True, include full metadata details.

        Returns
        -------
        BookRead
            Book read DTO.

        Raises
        ------
        ValueError
            If book ID is missing.
        """
        book = book_with_rels.book
        if book.id is None:
            error_msg = "book_missing_id"
            raise ValueError(error_msg)

        thumbnail_url = self._book_service.get_thumbnail_url(book_with_rels)

        book_read = BookRead(
            id=book.id,
            title=book.title,
            authors=book_with_rels.authors,
            author_sort=book.author_sort,
            title_sort=book.sort,
            pubdate=book.pubdate,
            timestamp=book.timestamp,
            series=book_with_rels.series,
            series_index=book.series_index,
            isbn=book.isbn,
            uuid=book.uuid or "",
            thumbnail_url=thumbnail_url,
            has_cover=book.has_cover,
        )

        # Add full details if requested and available
        if full and isinstance(book_with_rels, BookWithFullRelations):
            book_read.tags = book_with_rels.tags
            book_read.identifiers = book_with_rels.identifiers
            book_read.description = book_with_rels.description
            book_read.publisher = book_with_rels.publisher
            book_read.publisher_id = book_with_rels.publisher_id
            book_read.languages = book_with_rels.languages
            book_read.language_ids = book_with_rels.language_ids
            book_read.rating = book_with_rels.rating
            book_read.rating_id = book_with_rels.rating_id
            book_read.series_id = book_with_rels.series_id
            book_read.formats = book_with_rels.formats

        return book_read

    def build_book_read_list(
        self,
        books: list[BookWithRelations | BookWithFullRelations],
        full: bool = False,
    ) -> list[BookRead]:
        """Build list of BookRead DTOs from BookWithRelations list.

        Parameters
        ----------
        books : list[BookWithRelations | BookWithFullRelations]
            List of books with related metadata.
        full : bool
            If True, include full metadata details.

        Returns
        -------
        list[BookRead]
            List of book read DTOs (skips books without IDs).
        """
        book_reads = []
        for book_with_rels in books:
            book = book_with_rels.book
            # Skip books without IDs (should not happen in Calibre, but type safety)
            if book.id is None:
                continue
            book_reads.append(self.build_book_read(book_with_rels, full=full))
        return book_reads

# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Book service for managing Calibre books.

Business logic for querying and serving book data from Calibre libraries.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.core import Book
from fundamental.repositories import (
    BookWithRelations,
    CalibreBookRepository,
)

if TYPE_CHECKING:
    from fundamental.models.config import Library


class BookService:
    """Operations for querying books from Calibre libraries.

    Parameters
    ----------
    library : Library
        Active Calibre library configuration.
    """

    def __init__(self, library: Library) -> None:
        self._library = library
        self._book_repo = CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )

    def list_books(
        self,
        page: int = 1,
        page_size: int = 20,
        search_query: str | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """List books with pagination.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        search_query : str | None
            Optional search query to filter by title or author.
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books with relations list, total count).
        """
        offset = (page - 1) * page_size
        books = self._book_repo.list_books(
            limit=page_size,
            offset=offset,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = self._book_repo.count_books(search_query=search_query)
        return books, total

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Get a book by ID.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithRelations | None
            Book with relations if found, None otherwise.
        """
        return self._book_repo.get_book(book_id)

    def get_thumbnail_url(self, book: Book | BookWithRelations) -> str | None:
        """Generate thumbnail URL for a book.

        Parameters
        ----------
        book : Book | BookWithRelations
            Book instance or BookWithRelations.

        Returns
        -------
        str | None
            Thumbnail URL if book has a cover, None otherwise.
        """
        book_id = book.id if isinstance(book, Book) else book.book.id
        has_cover = book.has_cover if isinstance(book, Book) else book.book.has_cover

        if not has_cover:
            return None

        # Calibre stores covers as cover.jpg in the book's path directory
        # Format: /api/books/{book_id}/cover
        return f"/api/books/{book_id}/cover"

    def get_thumbnail_path(self, book: Book | BookWithRelations) -> Path | None:
        """Get filesystem path to book cover thumbnail.

        Parameters
        ----------
        book : Book | BookWithRelations
            Book instance or BookWithRelations.

        Returns
        -------
        Path | None
            Path to cover image if exists, None otherwise.
        """
        book_obj = book if isinstance(book, Book) else book.book

        if not book_obj.has_cover:
            return None

        # Calibre stores covers as cover.jpg in the book's path directory
        library_path = Path(self._library.calibre_db_path)
        book_path = library_path / book_obj.path
        cover_path = book_path / "cover.jpg"

        if cover_path.exists():
            return cover_path
        return None

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series.

        Parameters
        ----------
        query : str
            Search query string.
        book_limit : int
            Maximum number of book matches to return (default: 3).
        author_limit : int
            Maximum number of author matches to return (default: 3).
        tag_limit : int
            Maximum number of tag matches to return (default: 3).
        series_limit : int
            Maximum number of series matches to return (default: 3).

        Returns
        -------
        dict[str, list[dict[str, str | int]]]
            Dictionary with keys 'books', 'authors', 'tags', 'series', each
            containing a list of matches with 'name' and 'id' fields.
        """
        return self._book_repo.search_suggestions(
            query=query,
            book_limit=book_limit,
            author_limit=author_limit,
            tag_limit=tag_limit,
            series_limit=series_limit,
        )

    def filter_suggestions(
        self,
        query: str,
        filter_type: str,
        limit: int = 10,
    ) -> list[dict[str, str | int]]:
        """Get filter suggestions for a specific filter type.

        Parameters
        ----------
        query : str
            Search query string.
        filter_type : str
            Type of filter: 'author', 'title', 'genre', 'publisher',
            'identifier', 'series', 'format', 'rating', 'language'.
        limit : int
            Maximum number of suggestions to return (default: 10).

        Returns
        -------
        list[dict[str, str | int]]
            List of suggestions with 'id' and 'name' fields.
        """
        return self._book_repo.filter_suggestions(
            query=query,
            filter_type=filter_type,
            limit=limit,
        )

    def list_books_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """List books with multiple filter criteria using OR conditions.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        author_ids : list[int] | None
            List of author IDs to filter by (OR condition).
        title_ids : list[int] | None
            List of book IDs to filter by (OR condition).
        genre_ids : list[int] | None
            List of tag IDs to filter by (OR condition).
        publisher_ids : list[int] | None
            List of publisher IDs to filter by (OR condition).
        identifier_ids : list[int] | None
            List of identifier IDs to filter by (OR condition).
        series_ids : list[int] | None
            List of series IDs to filter by (OR condition).
        formats : list[str] | None
            List of format strings to filter by (OR condition).
        rating_ids : list[int] | None
            List of rating IDs to filter by (OR condition).
        language_ids : list[int] | None
            List of language IDs to filter by (OR condition).
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books with relations list, total count).
        """
        offset = (page - 1) * page_size
        books = self._book_repo.list_books_with_filters(
            limit=page_size,
            offset=offset,
            author_ids=author_ids,
            title_ids=title_ids,
            genre_ids=genre_ids,
            publisher_ids=publisher_ids,
            identifier_ids=identifier_ids,
            series_ids=series_ids,
            formats=formats,
            rating_ids=rating_ids,
            language_ids=language_ids,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = self._book_repo.count_books_with_filters(
            author_ids=author_ids,
            title_ids=title_ids,
            genre_ids=genre_ids,
            publisher_ids=publisher_ids,
            identifier_ids=identifier_ids,
            series_ids=series_ids,
            formats=formats,
            rating_ids=rating_ids,
            language_ids=language_ids,
        )
        return books, total

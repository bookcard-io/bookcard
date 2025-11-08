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

"""Repository for querying Calibre SQLite database.

This repository connects directly to Calibre's metadata.db SQLite database
to query book information using SQLAlchemy ORM.
"""

from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import Session, create_engine, select

from fundamental.models.core import Author, Book, BookAuthorLink, BookSeriesLink, Series

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine


@dataclass
class BookWithRelations:
    """Book with related author and series data.

    Attributes
    ----------
    book : Book
        Book instance.
    authors : list[str]
        List of author names.
    series : str | None
        Series name if part of a series.
    """

    book: Book
    authors: list[str]
    series: str | None


class CalibreBookRepository:
    """Repository for querying books from Calibre SQLite database.

    Parameters
    ----------
    calibre_db_path : str
        Path to Calibre library directory (contains metadata.db).
    calibre_db_file : str
        Calibre database filename (default: 'metadata.db').
    """

    def __init__(
        self,
        calibre_db_path: str,
        calibre_db_file: str = "metadata.db",
    ) -> None:
        self._calibre_db_path = Path(calibre_db_path)
        self._calibre_db_file = calibre_db_file
        self._db_path = self._calibre_db_path / self._calibre_db_file
        self._engine: Engine | None = None

    def _unwrap_book_from_result(self, result: object) -> Book | None:
        """Extract Book instance from query result using strategy pattern.

        Tries multiple extraction strategies in order until one succeeds.

        Parameters
        ----------
        result : object
            Query result which may be a Row, tuple, Book instance, or other.

        Returns
        -------
        Book | None
            Extracted Book instance or None if extraction fails.
        """
        strategies = [
            self._extract_book_from_book_instance,
            self._extract_book_from_indexable_container,
            self._extract_book_from_attr,
            self._extract_book_from_getitem,
        ]

        for strategy in strategies:
            book = strategy(result)
            if book is not None:
                return book
        return None

    def _extract_book_from_book_instance(self, result: object) -> Book | None:
        """Extract Book from Book instance."""
        if isinstance(result, Book):
            return result
        return None

    def _extract_book_from_indexable_container(self, result: object) -> Book | None:
        """Extract Book from indexable container (e.g., tuple, list, Row)."""
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner0 = result[0]  # type: ignore[index]
            if isinstance(inner0, Book):
                return inner0
        return None

    def _extract_book_from_attr(self, result: object) -> Book | None:
        """Extract Book from object with 'Book' attribute (Row object)."""
        with suppress(AttributeError, TypeError):
            book = result.Book  # type: ignore[attr-defined]
            if isinstance(book, Book):
                return book
        return None

    def _extract_book_from_getitem(self, result: object) -> Book | None:
        """Extract Book from object supporting __getitem__ with 'Book' key."""
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            book = result["Book"]  # type: ignore[index, misc]
            if isinstance(book, Book):
                return book
        return None

    def _unwrap_series_name_from_result(self, result: object) -> str | None:
        """Extract series name from query result using strategy pattern.

        Parameters
        ----------
        result : object
            Query result which may be a Row, tuple, or other.

        Returns
        -------
        str | None
            Extracted series name or None if extraction fails.
        """
        strategies = [
            self._extract_series_name_from_indexable_container,
            self._extract_series_name_from_attr,
            self._extract_series_name_from_getitem,
        ]

        for strategy in strategies:
            series_name = strategy(result)
            if series_name is not None:
                return series_name
        return None

    def _extract_series_name_from_indexable_container(
        self, result: object
    ) -> str | None:
        """Extract series name from indexable container (e.g., tuple, Row)."""
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner1 = result[1]  # type: ignore[index]
            if isinstance(inner1, str):
                return inner1
            if inner1 is None:
                return None
        return None

    def _extract_series_name_from_attr(self, result: object) -> str | None:
        """Extract series name from object with 'series_name' attribute."""
        with suppress(AttributeError, TypeError):
            series_name = result.series_name  # type: ignore[attr-defined]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None

    def _extract_series_name_from_getitem(self, result: object) -> str | None:
        """Extract series name from object supporting __getitem__."""
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            series_name = result["series_name"]  # type: ignore[index, misc]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine for Calibre database.

        Returns
        -------
        Engine
            SQLAlchemy engine instance.

        Raises
        ------
        FileNotFoundError
            If Calibre database file does not exist.
        """
        if not self._db_path.exists():
            msg = f"Calibre database not found at {self._db_path}"
            raise FileNotFoundError(msg)
        if self._engine is None:
            db_url = f"sqlite:///{self._db_path}"
            self._engine = create_engine(db_url, echo=False, future=True)
        return self._engine

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a SQLModel session for the Calibre database.

        Yields
        ------
        Session
            SQLModel session.
        """
        engine = self._get_engine()
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

    def count_books(self, search_query: str | None = None) -> int:
        """Count total number of books, optionally filtered by search.

        Parameters
        ----------
        search_query : str | None
            Optional search query to filter by title or author.

        Returns
        -------
        int
            Total number of books.
        """
        with self._get_session() as session:
            if search_query:
                pattern = f"%{search_query}%"
                stmt = (
                    select(func.count(func.distinct(Book.id)))
                    .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(Author, BookAuthorLink.author == Author.id)
                    .where(
                        (Book.title.like(pattern)) | (Author.name.like(pattern))  # type: ignore[attr-defined]
                    )
                )
            else:
                stmt = select(func.count(Book.id))
            result = session.exec(stmt).one()
            return result if result else 0

    def list_books(
        self,
        limit: int = 20,
        offset: int = 0,
        search_query: str | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> list[BookWithRelations]:
        """List books with pagination and optional search.

        Parameters
        ----------
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
        search_query : str | None
            Optional search query to filter by title or author.
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').

        Returns
        -------
        list[BookWithRelations]
            List of books with authors and series.
        """
        # Validate sort_by to prevent SQL injection
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        sort_field = valid_sort_fields.get(sort_by, Book.timestamp)

        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        with self._get_session() as session:
            # Build base query with series
            series_alias = aliased(Series)
            stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            # Add search filter if provided
            if search_query:
                pattern = f"%{search_query}%"
                author_alias = aliased(Author)
                stmt = (
                    stmt.outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
                    .distinct()
                    .where(
                        (Book.title.like(pattern)) | (author_alias.name.like(pattern))  # type: ignore[attr-defined]
                    )
                )

            # Add ordering
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
            else:
                stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]

            # Add pagination
            stmt = stmt.limit(limit).offset(offset)

            # Execute query
            results = session.exec(stmt).all()

            books = []
            for result in results:
                book = self._unwrap_book_from_result(result)
                if book is None:
                    continue

                series_name = self._unwrap_series_name_from_result(result)

                # Get authors for this book
                if book.id is None:
                    continue

                authors_stmt = (
                    select(Author.name)
                    .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                    .where(BookAuthorLink.book == book.id)
                    .order_by(BookAuthorLink.id)
                )
                authors = list(session.exec(authors_stmt).all())

                books.append(
                    BookWithRelations(
                        book=book,
                        authors=authors,
                        series=series_name,
                    )
                )

            return books

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Get a book by ID.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithRelations | None
            Book with authors and series if found, None otherwise.
        """
        with self._get_session() as session:
            series_alias = aliased(Series)
            stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
                .where(Book.id == book_id)
            )
            result = session.exec(stmt).first()

            if result is None:
                return None

            book = self._unwrap_book_from_result(result)
            if book is None:
                return None

            series_name = self._unwrap_series_name_from_result(result)

            # Get authors for this book
            authors_stmt = (
                select(Author.name)
                .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                .where(BookAuthorLink.book == book_id)
                .order_by(BookAuthorLink.id)
            )
            authors = list(session.exec(authors_stmt).all())

            return BookWithRelations(
                book=book,
                authors=authors,
                series=series_name,
            )

    @staticmethod
    def _parse_datetime(value: str | float | None) -> datetime | None:
        """Parse Calibre datetime value.

        Calibre stores timestamps as Unix timestamps (seconds since epoch)
        or as ISO format strings, or None.

        Parameters
        ----------
        value : str | float | None
            Timestamp value (Unix timestamp or ISO string) or None.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if value is None:
            return None
        try:
            # Try parsing as Unix timestamp (float/int)
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, tz=UTC)
            # Try parsing as ISO string
            if isinstance(value, str):
                # Remove timezone info if present and try ISO format
                value_clean = value.replace("Z", "+00:00")
                try:
                    return datetime.fromisoformat(value_clean)
                except ValueError:
                    # Try parsing as Unix timestamp string
                    try:
                        return datetime.fromtimestamp(float(value_clean), tz=UTC)
                    except (ValueError, TypeError):
                        return None
            else:
                return None
        except (ValueError, AttributeError, OSError):
            return None

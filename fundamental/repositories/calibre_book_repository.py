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

"""Repository for querying Calibre SQLite database.

This repository connects directly to Calibre's metadata.db SQLite database
to query book information using SQLAlchemy ORM.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import event, func
from sqlalchemy.orm import aliased
from sqlmodel import Session, create_engine, select

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.models.media import Data
from fundamental.repositories.command_executor import CommandExecutor
from fundamental.repositories.delete_commands import (
    DeleteBookAuthorLinksCommand,
    DeleteBookCommand,
    DeleteBookLanguageLinksCommand,
    DeleteBookPublisherLinksCommand,
    DeleteBookRatingLinksCommand,
    DeleteBookSeriesLinksCommand,
    DeleteBookShelfLinksCommand,
    DeleteBookTagLinksCommand,
    DeleteCommentCommand,
    DeleteDataRecordsCommand,
    DeleteDirectoryCommand,
    DeleteFileCommand,
    DeleteIdentifiersCommand,
)
from fundamental.repositories.filters import FilterBuilder
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.repositories.suggestions import FilterSuggestionFactory
from fundamental.services.book_cover_extractor import BookCoverExtractor
from fundamental.services.book_metadata_extractor import BookMetadataExtractor

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Iterator

    from sqlalchemy import Engine

    from fundamental.services.book_metadata import BookMetadata


logger = logging.getLogger(__name__)


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

    @staticmethod
    def _get_calibre_sqlite_functions() -> list[tuple[str, int, Callable[..., object]]]:
        """Get list of SQLite functions to register for Calibre database.

        Returns
        -------
        list[tuple[str, int, Callable[..., object]]]
            List of tuples containing (function_name, num_args, function_impl).
            Each tuple defines a SQLite function to register.

        Notes
        -----
        To add a new function, simply add a tuple to this list:
        - function_name: Name of the SQL function (e.g., "my_function")
        - num_args: Number of arguments the function accepts (-1 for variable)
        - function_impl: Python callable that implements the function
        """
        return [
            (
                "title_sort",
                1,
                lambda x: x or "",
            ),
            (
                "uuid4",
                0,
                lambda: str(uuid4()),
            ),
        ]

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

            def _register_calibre_functions(
                dbapi_conn: sqlite3.Connection, connection_record: object
            ) -> None:
                """Register SQLite functions required by Calibre database.

                Registers functions needed by Calibre's database triggers.
                SQLite's create_function is idempotent, so it's safe to call
                multiple times - subsequent calls simply replace the function.

                To add a new function, add it to the list returned by
                _get_calibre_sqlite_functions().

                Parameters
                ----------
                dbapi_conn : sqlite3.Connection
                    SQLite database connection.
                connection_record : object
                    Connection record (required by event listener signature).
                """
                # connection_record is required by event listener signature but unused
                _ = connection_record
                # Register each function
                # Note: create_function is idempotent, so calling it multiple times
                # is safe and has negligible overhead
                for (
                    func_name,
                    num_args,
                    func_impl,
                ) in self._get_calibre_sqlite_functions():
                    dbapi_conn.create_function(func_name, num_args, func_impl)

            self._engine = create_engine(db_url, echo=False, future=True)
            event.listen(self._engine, "connect", _register_calibre_functions)
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
            Optional search query to filter by title, author, or tag.

        Returns
        -------
        int
            Total number of books.
        """
        with self._get_session() as session:
            if search_query:
                # Use case-insensitive search for SQLite
                query_lower = search_query.lower()
                pattern_lower = f"%{query_lower}%"
                author_alias = aliased(Author)
                tag_alias = aliased(Tag)
                series_search_alias = aliased(Series)
                stmt = (
                    select(func.count(func.distinct(Book.id)))
                    .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
                    .outerjoin(BookTagLink, Book.id == BookTagLink.book)
                    .outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
                    .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                    .outerjoin(
                        series_search_alias,
                        BookSeriesLink.series == series_search_alias.id,
                    )
                    .where(
                        (func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(author_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(tag_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(series_search_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
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
                # Use case-insensitive search for SQLite
                query_lower = search_query.lower()
                pattern_lower = f"%{query_lower}%"
                author_alias = aliased(Author)
                tag_alias = aliased(Tag)
                # Reuse the existing series_alias from the base query for search
                stmt = (
                    stmt.outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
                    .outerjoin(BookTagLink, Book.id == BookTagLink.book)
                    .outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
                    .distinct()
                    .where(
                        (func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(author_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(tag_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(series_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
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

    def _build_book_with_relations(
        self, session: Session, result: object
    ) -> BookWithRelations | None:
        """Build BookWithRelations from query result.

        Parameters
        ----------
        session : Session
            Database session.
        result : object
            Query result.

        Returns
        -------
        BookWithRelations | None
            Book with relations or None if extraction fails.
        """
        book = self._unwrap_book_from_result(result)
        if book is None or book.id is None:
            return None

        series_name = self._unwrap_series_name_from_result(result)

        authors_stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book.id)
            .order_by(BookAuthorLink.id)
        )
        authors = list(session.exec(authors_stmt).all())

        return BookWithRelations(
            book=book,
            authors=authors,
            series=series_name,
        )

    def _get_sort_field(self, sort_by: str) -> object:
        """Get sort field for query ordering.

        Parameters
        ----------
        sort_by : str
            Sort field name.

        Returns
        -------
        object
            SQLAlchemy column field for sorting.
        """
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        return valid_sort_fields.get(sort_by, Book.timestamp)  # type: ignore[return-value]

    def list_books_with_filters(
        self,
        limit: int = 20,
        offset: int = 0,
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
    ) -> list[BookWithRelations]:
        """List books with multiple filter criteria using OR conditions.

        Each filter type uses OR conditions (e.g., multiple authors = OR).
        Different filter types are combined with AND conditions.

        Parameters
        ----------
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
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
        list[BookWithRelations]
            List of books with authors and series.
        """
        sort_field = self._get_sort_field(sort_by)
        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        with self._get_session() as session:
            series_alias = aliased(Series)
            base_stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            stmt = (
                FilterBuilder(base_stmt)
                .with_author_ids(author_ids)
                .with_title_ids(title_ids)
                .with_genre_ids(genre_ids)
                .with_publisher_ids(publisher_ids)
                .with_identifier_ids(identifier_ids)
                .with_series_ids(series_ids, series_alias)
                .with_formats(formats)
                .with_rating_ids(rating_ids)
                .with_language_ids(language_ids)
                .build()
            )

            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
            else:
                stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]

            stmt = stmt.limit(limit).offset(offset)
            results = session.exec(stmt).all()

            books = []
            for result in results:
                book_with_rels = self._build_book_with_relations(session, result)
                if book_with_rels:
                    books.append(book_with_rels)

            return books

    def count_books_with_filters(
        self,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
    ) -> int:
        """Count books matching filter criteria.

        Parameters
        ----------
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

        Returns
        -------
        int
            Total number of books matching the filters.
        """
        with self._get_session() as session:
            series_alias = aliased(Series)
            base_stmt = (
                select(func.count(func.distinct(Book.id)))
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            stmt = (
                FilterBuilder(base_stmt)
                .with_author_ids(author_ids)
                .with_title_ids(title_ids)
                .with_genre_ids(genre_ids)
                .with_publisher_ids(publisher_ids)
                .with_identifier_ids(identifier_ids)
                .with_series_ids(series_ids, series_alias)
                .with_formats(formats)
                .with_rating_ids(rating_ids)
                .with_language_ids(language_ids)
                .build()
            )

            result = session.exec(stmt).one()
            return result if result else 0

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
            # Ensure we get a list[str] even if backend returns row tuples
            author_rows = session.exec(authors_stmt).all()
            authors = [row[0] if isinstance(row, tuple) else row for row in author_rows]

            return BookWithRelations(
                book=book,
                authors=authors,
                series=series_name,
            )

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Get a book by ID with all related metadata for editing.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithFullRelations | None
            Book with all related metadata if found, None otherwise.
        """
        with self._get_session() as session:
            # Get book with series
            series_alias = aliased(Series)
            stmt = (
                select(
                    Book,
                    series_alias.name.label("series_name"),
                    series_alias.id.label("series_id"),
                )  # type: ignore[attr-defined]
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

            # Extract series info
            series_name = self._unwrap_series_name_from_result(result)
            series_id = None
            with suppress(AttributeError, TypeError, KeyError, IndexError):
                if hasattr(result, "series_id"):
                    series_id = result.series_id  # type: ignore[attr-defined]
                elif hasattr(result, "__getitem__"):
                    series_id = result[2]  # type: ignore[index]

            # Get authors
            authors_stmt = (
                select(Author.name)
                .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                .where(BookAuthorLink.book == book_id)
                .order_by(BookAuthorLink.id)
            )
            author_rows = session.exec(authors_stmt).all()
            authors = [row[0] if isinstance(row, tuple) else row for row in author_rows]

            # Get tags
            tags_stmt = (
                select(Tag.name)
                .join(BookTagLink, Tag.id == BookTagLink.tag)
                .where(BookTagLink.book == book_id)
                .order_by(BookTagLink.id)
            )
            tags = list(session.exec(tags_stmt).all())

            # Get identifiers
            identifiers_stmt = (
                select(Identifier.type, Identifier.val)
                .where(Identifier.book == book_id)
                .order_by(Identifier.id)
            )
            identifiers = [
                {"type": ident_type, "val": ident_val}
                for ident_type, ident_val in session.exec(identifiers_stmt).all()
            ]

            # Get comment/description
            comment_stmt = select(Comment.text).where(Comment.book == book_id)
            comment_result = session.exec(comment_stmt).first()
            description = comment_result if comment_result else None

            # Get publisher
            publisher_stmt = (
                select(Publisher.name, Publisher.id)
                .join(BookPublisherLink, Publisher.id == BookPublisherLink.publisher)
                .where(BookPublisherLink.book == book_id)
            )
            publisher_result = session.exec(publisher_stmt).first()
            publisher = None
            publisher_id = None
            if publisher_result:
                publisher, publisher_id = publisher_result

            # Get languages
            language_stmt = (
                select(Language.lang_code, Language.id)
                .join(BookLanguageLink, Language.id == BookLanguageLink.lang_code)
                .where(BookLanguageLink.book == book_id)
                .order_by(BookLanguageLink.item_order)
            )
            language_results = list(session.exec(language_stmt).all())
            languages: list[str] = []
            language_ids: list[int] = []
            for lang_code, lang_id in language_results:
                languages.append(lang_code)
                if lang_id is not None:
                    language_ids.append(lang_id)

            # Get rating
            rating_stmt = (
                select(Rating.rating, Rating.id)
                .join(BookRatingLink, Rating.id == BookRatingLink.rating)
                .where(BookRatingLink.book == book_id)
            )
            rating_result = session.exec(rating_stmt).first()
            rating = None
            rating_id = None
            if rating_result:
                rating, rating_id = rating_result

            # Get file formats
            formats_stmt = (
                select(Data.format, Data.uncompressed_size, Data.name)
                .where(Data.book == book_id)
                .order_by(Data.format)
            )
            formats = [
                {"format": fmt, "size": size, "name": name or ""}
                for fmt, size, name in session.exec(formats_stmt).all()
            ]

            return BookWithFullRelations(
                book=book,
                authors=authors,
                series=series_name,
                series_id=series_id,
                tags=tags,
                identifiers=identifiers,
                description=description,
                publisher=publisher,
                publisher_id=publisher_id,
                languages=languages,
                language_ids=language_ids,
                rating=rating,
                rating_id=rating_id,
                formats=formats,
            )

    def _normalize_string_set(self, strings: list[str]) -> set[str]:
        """Normalize a list of strings for comparison.

        Parameters
        ----------
        strings : list[str]
            List of strings to normalize.

        Returns
        -------
        set[str]
            Set of normalized (lowercased, stripped) strings, excluding empty ones.
        """
        return {s.strip().lower() for s in strings if s.strip()}

    def _update_book_fields(
        self,
        book: Book,
        title: str | None = None,
        pubdate: datetime | None = None,
        series_index: float | None = None,
    ) -> None:
        """Update direct book fields.

        Parameters
        ----------
        book : Book
            Book instance to update.
        title : str | None
            Book title to update.
        pubdate : datetime | None
            Publication date to update.
        series_index : float | None
            Series index to update.
        """
        if title is not None:
            book.title = title
        if pubdate is not None:
            book.pubdate = pubdate
        if series_index is not None:
            book.series_index = series_index
        book.last_modified = datetime.now(UTC)

    def _update_book_authors(
        self, session: Session, book_id: int, author_names: list[str]
    ) -> None:
        """Update book authors (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        author_names : list[str]
            List of author names to set (replaces existing).
        """
        # Get current authors
        current_authors_stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book_id)
            .order_by(BookAuthorLink.id)
        )
        current_author_names = self._normalize_string_set(
            list(session.exec(current_authors_stmt).all())
        )

        # Normalize new author names
        normalized_new_authors = self._normalize_string_set(author_names)

        # Check if authors are actually changing
        if current_author_names == normalized_new_authors:
            # Authors haven't changed, no update needed
            return

        # Authors are changing - delete existing author links
        delete_links_stmt = select(BookAuthorLink).where(BookAuthorLink.book == book_id)
        existing_links = list(session.exec(delete_links_stmt).all())
        self._delete_links_and_flush(session, existing_links)

        # Create or get authors and create links
        for author_name in author_names:
            if not author_name.strip():
                continue
            # Find or create author
            author_stmt = select(Author).where(Author.name == author_name)
            author = session.exec(author_stmt).first()
            if author is None:
                author = Author(name=author_name)
                session.add(author)
                session.flush()
            if author.id is None:
                continue
            # Recreate link (we removed all links above)
            link = BookAuthorLink(book=book_id, author=author.id)
            session.add(link)

    def _update_book_series(
        self,
        session: Session,
        book_id: int,
        series_name: str | None = None,
        series_id: int | None = None,
    ) -> None:
        """Update book series (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        series_name : str | None
            Series name to set (creates if doesn't exist).
        series_id : int | None
            Series ID to set (if provided, series_name is ignored).
        """
        # Get current series link
        current_link_stmt = select(BookSeriesLink).where(BookSeriesLink.book == book_id)
        current_link = session.exec(current_link_stmt).first()

        # Determine if we should remove series or set a new one
        should_remove = series_name == "" or (
            series_id is None and series_name is not None and not series_name.strip()
        )

        if should_remove:
            # Remove series - delete link if present
            self._delete_links_and_flush(
                session, [current_link] if current_link is not None else []
            )
            return

        # Determine target series ID
        target_series_id = series_id
        if target_series_id is None and series_name is not None and series_name.strip():
            # Find or create series
            series_stmt = select(Series).where(Series.name == series_name)
            series = session.exec(series_stmt).first()
            if series is None:
                series = Series(name=series_name)
                session.add(series)
                session.flush()
            if series.id is not None:
                target_series_id = series.id

        # Check if series is actually changing
        current_series_id = current_link.series if current_link else None
        if current_series_id == target_series_id:
            # Series hasn't changed, no update needed
            return

        # Series is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target series is specified
        if target_series_id is not None:
            link = BookSeriesLink(book=book_id, series=target_series_id)
            session.add(link)

    def _update_book_tags(
        self, session: Session, book_id: int, tag_names: list[str]
    ) -> None:
        """Update book tags (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        tag_names : list[str]
            List of tag names to set (replaces existing).
        """
        # Get current tags
        current_tags_stmt = (
            select(Tag.name)
            .join(BookTagLink, Tag.id == BookTagLink.tag)
            .where(BookTagLink.book == book_id)
        )
        current_tag_names = self._normalize_string_set(
            list(session.exec(current_tags_stmt).all())
        )

        # Normalize new tag names
        normalized_new_tags = self._normalize_string_set(tag_names)

        # Check if tags are actually changing
        if current_tag_names == normalized_new_tags:
            # Tags haven't changed, no update needed
            return

        # Tags are changing - delete existing tag links
        delete_tags_stmt = select(BookTagLink).where(BookTagLink.book == book_id)
        existing_tag_links = list(session.exec(delete_tags_stmt).all())
        self._delete_links_and_flush(session, existing_tag_links)

        # Create or get tags and create links
        for tag_name in tag_names:
            if not tag_name.strip():
                continue
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag = session.exec(tag_stmt).first()
            if tag is None:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()
            if tag.id is None:
                continue
            link = BookTagLink(book=book_id, tag=tag.id)
            session.add(link)

    def _update_book_identifiers(
        self, session: Session, book_id: int, identifiers: list[dict[str, str]]
    ) -> None:
        """Update book identifiers (one-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        identifiers : list[dict[str, str]]
            List of identifiers with 'type' and 'val' keys (replaces existing).
        """
        # Get current identifiers
        current_identifiers_stmt = select(Identifier).where(Identifier.book == book_id)
        current_identifiers = session.exec(current_identifiers_stmt).all()
        current_identifiers_set = {
            (ident.type.lower().strip(), ident.val.strip())
            for ident in current_identifiers
            if ident.val.strip()
        }

        # Normalize new identifiers (type and val, filter empty)
        normalized_new_identifiers = {
            (
                ident_data.get("type", "isbn").lower().strip(),
                ident_data.get("val", "").strip(),
            )
            for ident_data in identifiers
            if ident_data.get("val", "").strip()
        }

        # Check if identifiers are actually changing
        if current_identifiers_set == normalized_new_identifiers:
            # Identifiers haven't changed, no update needed
            return

        # Identifiers are changing - delete existing identifiers
        self._delete_links_and_flush(session, list(current_identifiers))

        # Create new identifiers
        for ident_data in identifiers:
            ident_type = ident_data.get("type", "isbn")
            ident_val = ident_data.get("val", "")
            if ident_val.strip():
                ident = Identifier(book=book_id, type=ident_type, val=ident_val)
                session.add(ident)

    def _update_book_description(
        self, session: Session, book_id: int, description: str
    ) -> None:
        """Update book description/comment (one-to-one relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        description : str
            Book description/comment to set.
        """
        comment_stmt = select(Comment).where(Comment.book == book_id)
        comment = session.exec(comment_stmt).first()
        if comment is None:
            comment = Comment(book=book_id, text=description)
            session.add(comment)
        else:
            comment.text = description

    def _delete_links_and_flush(self, session: Session, links: list[object]) -> None:
        """Delete multiple links and flush the session.

        Helper method to delete multiple link relationships and immediately flush
        the session to ensure the deletes are processed before inserting new links.
        This prevents UNIQUE constraint violations when updating relationships.

        Parameters
        ----------
        session : Session
            Database session.
        links : list[object]
            List of link objects to delete. Can be empty.

        Notes
        -----
        This method is idempotent - if links is empty, it does nothing.
        """
        if links:
            for link in links:
                session.delete(link)
            session.flush()

    def _update_book_publisher(
        self,
        session: Session,
        book_id: int,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
    ) -> None:
        """Update book publisher (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        publisher_name : str | None
            Publisher name to set (creates if doesn't exist).
        publisher_id : int | None
            Publisher ID to set (if provided, publisher_name is ignored).
        """
        # Get current publisher link
        current_link_stmt = select(BookPublisherLink).where(
            BookPublisherLink.book == book_id
        )
        current_link = session.exec(current_link_stmt).first()

        # Determine target publisher ID
        target_publisher_id = publisher_id
        if target_publisher_id is None and publisher_name is not None:
            # Find or create publisher
            publisher_stmt = select(Publisher).where(Publisher.name == publisher_name)
            publisher = session.exec(publisher_stmt).first()
            if publisher is None:
                publisher = Publisher(name=publisher_name)
                session.add(publisher)
                session.flush()
            if publisher.id is not None:
                target_publisher_id = publisher.id

        # Check if publisher is actually changing
        current_publisher_id = current_link.publisher if current_link else None
        if current_publisher_id == target_publisher_id:
            # Publisher hasn't changed, no update needed
            return

        # Publisher is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target publisher is specified
        if target_publisher_id is not None:
            link = BookPublisherLink(book=book_id, publisher=target_publisher_id)
            session.add(link)

    def _get_current_language_ids(
        self, session: Session, book_id: int
    ) -> tuple[list[BookLanguageLink], set[int]]:
        """Get current language links and their IDs.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.

        Returns
        -------
        tuple[list[BookLanguageLink], set[int]]
            Tuple of (current links, set of language IDs).
        """
        current_links_stmt = select(BookLanguageLink).where(
            BookLanguageLink.book == book_id
        )
        current_links = list(session.exec(current_links_stmt).all())
        current_language_ids = {link.lang_code for link in current_links}
        return current_links, current_language_ids

    def _find_or_create_language(
        self, session: Session, lang_code: str
    ) -> Language | None:
        """Find or create a language by code.

        Parameters
        ----------
        session : Session
            Database session.
        lang_code : str
            Language code (ISO 639-1).

        Returns
        -------
        Language | None
            Language instance, or None if creation failed.
        """
        language_stmt = select(Language).where(Language.lang_code == lang_code)
        language = session.exec(language_stmt).first()
        if language is None:
            language = Language(lang_code=lang_code)
            session.add(language)
            session.flush()
        return language

    def _resolve_language_ids(
        self,
        session: Session,
        language_ids: list[int] | None = None,
        language_codes: list[str] | None = None,
    ) -> list[int]:
        """Resolve language_ids or language_codes to a list of language IDs.

        Parameters
        ----------
        session : Session
            Database session.
        language_ids : list[int] | None
            List of language IDs (takes priority).
        language_codes : list[str] | None
            List of language codes to resolve.

        Returns
        -------
        list[int]
            List of resolved language IDs.
        """
        if language_ids is not None:
            return language_ids

        if language_codes is None:
            return []

        target_language_ids: list[int] = []
        for lang_code in language_codes:
            language = self._find_or_create_language(session, lang_code)
            if language is not None and language.id is not None:
                target_language_ids.append(language.id)

        return target_language_ids

    def _remove_duplicate_ids(self, ids: list[int]) -> list[int]:
        """Remove duplicates from a list while preserving order.

        Parameters
        ----------
        ids : list[int]
            List of IDs that may contain duplicates.

        Returns
        -------
        list[int]
            List of unique IDs in original order.
        """
        seen: set[int] = set()
        unique_ids: list[int] = []
        for item_id in ids:
            if item_id not in seen:
                seen.add(item_id)
                unique_ids.append(item_id)
        return unique_ids

    def _delete_existing_language_links(
        self, session: Session, current_links: list[BookLanguageLink]
    ) -> None:
        """Delete existing language links.

        Parameters
        ----------
        session : Session
            Database session.
        current_links : list[BookLanguageLink]
            List of existing language links to delete.
        """
        for link in current_links:
            session.delete(link)
        session.flush()

    def _create_language_links(
        self, session: Session, book_id: int, language_ids: list[int]
    ) -> None:
        """Create new language links.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        language_ids : list[int]
            List of language IDs to create links for.
        """
        for order, target_language_id in enumerate(language_ids):
            existing_link_stmt = select(BookLanguageLink).where(
                BookLanguageLink.book == book_id,
                BookLanguageLink.lang_code == target_language_id,
            )
            existing_link = session.exec(existing_link_stmt).first()
            if existing_link is None:
                link = BookLanguageLink(
                    book=book_id,
                    lang_code=target_language_id,
                    item_order=order,
                )
                session.add(link)

    def _update_book_language(
        self,
        session: Session,
        book_id: int,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
    ) -> None:
        """Update book languages (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        language_codes : list[str] | None
            List of language codes to set (creates if doesn't exist).
        language_ids : list[int] | None
            List of language IDs to set (if provided, language_codes is ignored).
        """
        current_links, current_language_ids = self._get_current_language_ids(
            session, book_id
        )

        target_language_ids = self._resolve_language_ids(
            session, language_ids, language_codes
        )
        target_language_ids = self._remove_duplicate_ids(target_language_ids)

        if set(target_language_ids) == current_language_ids:
            return

        self._delete_existing_language_links(session, current_links)
        self._create_language_links(session, book_id, target_language_ids)

    def _update_book_rating(
        self,
        session: Session,
        book_id: int,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        """Update book rating (many-to-many relationship).

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        rating_value : int | None
            Rating value to set (creates if doesn't exist).
        rating_id : int | None
            Rating ID to set (if provided, rating_value is ignored).
        """
        # Get current rating link
        current_link_stmt = select(BookRatingLink).where(BookRatingLink.book == book_id)
        current_link = session.exec(current_link_stmt).first()

        # Determine target rating ID
        target_rating_id = rating_id
        if target_rating_id is None and rating_value is not None:
            # Find or create rating
            rating_stmt = select(Rating).where(Rating.rating == rating_value)
            rating = session.exec(rating_stmt).first()
            if rating is None:
                rating = Rating(rating=rating_value)
                session.add(rating)
                session.flush()
            if rating.id is not None:
                target_rating_id = rating.id

        # Check if rating is actually changing
        current_rating_id = current_link.rating if current_link else None
        if current_rating_id == target_rating_id:
            # Rating hasn't changed, no update needed
            return

        # Rating is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target rating is specified
        if target_rating_id is not None:
            link = BookRatingLink(book=book_id, rating=target_rating_id)
            session.add(link)

    def update_book(
        self,
        book_id: int,
        title: str | None = None,
        pubdate: datetime | None = None,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        series_index: float | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> BookWithFullRelations | None:
        """Update book metadata.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        title : str | None
            Book title to update.
        pubdate : datetime | None
            Publication date to update.
        author_names : list[str] | None
            List of author names to set (replaces existing).
        series_name : str | None
            Series name to set (creates if doesn't exist).
        series_id : int | None
            Series ID to set (if provided, series_name is ignored).
        series_index : float | None
            Series index to update.
        tag_names : list[str] | None
            List of tag names to set (replaces existing).
        identifiers : list[dict[str, str]] | None
            List of identifiers with 'type' and 'val' keys (replaces existing).
        description : str | None
            Book description/comment to set.
        publisher_name : str | None
            Publisher name to set (creates if doesn't exist).
        publisher_id : int | None
            Publisher ID to set (if provided, publisher_name is ignored).
        language_codes : list[str] | None
            List of language codes to set (creates if doesn't exist).
        language_ids : list[int] | None
            List of language IDs to set (if provided, language_codes is ignored).
        rating_value : int | None
            Rating value to set (creates if doesn't exist).
        rating_id : int | None
            Rating ID to set (if provided, rating_value is ignored).

        Returns
        -------
        BookWithFullRelations | None
            Updated book with all relations if found, None otherwise.
        """
        with self._get_session() as session:
            # Disable autoflush to prevent errors with Calibre-specific SQLite functions
            # (e.g., title_sort) that may be referenced in triggers
            with session.no_autoflush:
                # Get existing book
                book_stmt = select(Book).where(Book.id == book_id)
                book = session.exec(book_stmt).first()
                if book is None:
                    return None

                # Update authors first (before book fields to avoid trigger issues)
                if author_names is not None:
                    self._update_book_authors(session, book_id, author_names)

                # Update series
                if series_name is not None or series_id is not None:
                    self._update_book_series(session, book_id, series_name, series_id)

                # Update tags
                if tag_names is not None:
                    self._update_book_tags(session, book_id, tag_names)

                # Update identifiers
                if identifiers is not None:
                    self._update_book_identifiers(session, book_id, identifiers)

                # Update description
                if description is not None:
                    self._update_book_description(session, book_id, description)

                # Update publisher
                if publisher_id is not None or publisher_name is not None:
                    self._update_book_publisher(
                        session, book_id, publisher_name, publisher_id
                    )

                # Update language
                if language_ids is not None or language_codes is not None:
                    self._update_book_language(
                        session,
                        book_id,
                        language_codes=language_codes,
                        language_ids=language_ids,
                    )

                # Update rating
                if rating_id is not None or rating_value is not None:
                    self._update_book_rating(session, book_id, rating_value, rating_id)

                # Update book fields last (after all other operations to avoid
                # triggering title_sort function during intermediate flushes)
                self._update_book_fields(
                    book, title=title, pubdate=pubdate, series_index=series_index
                )

            session.commit()
            session.refresh(book)

            # Return updated book with full relations
            return self.get_book_full(book_id)

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
        if not query or not query.strip():
            return {"books": [], "authors": [], "tags": [], "series": []}

        results = {
            "books": [],
            "authors": [],
            "tags": [],
            "series": [],
        }

        with self._get_session() as session:
            # Use func.lower for case-insensitive search in SQLite
            query_lower = query.strip().lower()
            pattern_lower = f"%{query_lower}%"

            # Search books by title
            book_stmt = (
                select(Book.id, Book.title)
                .where(func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(book_limit)
            )
            book_results = session.exec(book_stmt).all()
            results["books"] = [
                {"id": book_id, "name": book_title}
                for book_id, book_title in book_results
            ]

            # Search authors
            author_stmt = (
                select(Author.id, Author.name)
                .where(func.lower(Author.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(author_limit)
            )
            author_results = session.exec(author_stmt).all()
            results["authors"] = [
                {"id": author_id, "name": author_name}
                for author_id, author_name in author_results
            ]

            # Search tags
            tag_stmt = (
                select(Tag.id, Tag.name)
                .where(func.lower(Tag.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(tag_limit)
            )
            tag_results = session.exec(tag_stmt).all()
            results["tags"] = [
                {"id": tag_id, "name": tag_name} for tag_id, tag_name in tag_results
            ]

            # Search series
            series_stmt = (
                select(Series.id, Series.name)
                .where(func.lower(Series.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(series_limit)
            )
            series_results = session.exec(series_stmt).all()
            results["series"] = [
                {"id": series_id, "name": series_name}
                for series_id, series_name in series_results
            ]

        return results

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
        if not query or not query.strip():
            return []

        strategy = FilterSuggestionFactory.get_strategy(filter_type)
        if strategy is None:
            return []

        with self._get_session() as session:
            return strategy.get_suggestions(session, query, limit)

    def get_library_stats(self) -> dict[str, int | float]:
        """Get library statistics.

        Returns aggregate statistics about the library including:
        - Total number of books
        - Total number of unique series
        - Total number of unique authors
        - Total number of unique tags
        - Total number of books with ratings
        - Total content size in bytes

        Returns
        -------
        dict[str, int | float]
            Dictionary with keys:
            - 'total_books': Total number of books
            - 'total_series': Total number of unique series
            - 'total_authors': Total number of unique authors
            - 'total_tags': Total number of unique tags
            - 'total_ratings': Total number of books with ratings
            - 'total_content_size': Total file size in bytes
        """
        with self._get_session() as session:
            # Count total books
            books_stmt = select(func.count(Book.id))
            total_books = session.exec(books_stmt).one() or 0

            # Count unique series (series that are linked to books)
            series_stmt = select(
                func.count(func.distinct(BookSeriesLink.series))
            ).select_from(BookSeriesLink)
            total_series = session.exec(series_stmt).one() or 0

            # Count unique authors (authors that are linked to books)
            authors_stmt = select(
                func.count(func.distinct(BookAuthorLink.author))
            ).select_from(BookAuthorLink)
            total_authors = session.exec(authors_stmt).one() or 0

            # Count unique tags (tags that are linked to books)
            tags_stmt = select(func.count(func.distinct(BookTagLink.tag))).select_from(
                BookTagLink
            )
            total_tags = session.exec(tags_stmt).one() or 0

            # Count books with ratings (books that have a rating link)
            ratings_stmt = select(
                func.count(func.distinct(BookRatingLink.book))
            ).select_from(BookRatingLink)
            total_ratings = session.exec(ratings_stmt).one() or 0

            # Sum total content size
            content_size_stmt = select(func.sum(Data.uncompressed_size))
            total_content_size = session.exec(content_size_stmt).one() or 0
            if total_content_size is None:
                total_content_size = 0

            return {
                "total_books": total_books,
                "total_series": total_series,
                "total_authors": total_authors,
                "total_tags": total_tags,
                "total_ratings": total_ratings,
                "total_content_size": int(total_content_size),
            }

    @staticmethod
    def _sanitize_filename(name: str, max_length: int = 96) -> str:
        """Sanitize filename by removing invalid characters.

        Parameters
        ----------
        name : str
            Filename to sanitize.
        max_length : int
            Maximum length for the sanitized filename (default: 96).

        Returns
        -------
        str
            Sanitized filename safe for filesystem use.
        """
        invalid_chars = '<>:"/\\|?*'
        sanitized = "".join(c if c not in invalid_chars else "_" for c in name)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized.strip() or "Unknown"

    def _get_or_create_author(self, session: Session, author_name: str) -> Author:
        """Get existing author or create a new one.

        Parameters
        ----------
        session : Session
            Database session.
        author_name : str
            Author name.

        Returns
        -------
        Author
            Author instance with valid ID.

        Raises
        ------
        ValueError
            If author creation fails.
        """
        author_stmt = select(Author).where(Author.name == author_name)
        author = session.exec(author_stmt).first()
        if author is None:
            author = Author(name=author_name, sort=author_name)
            session.add(author)
            session.flush()

        if author.id is None:
            msg = "Failed to create author"
            raise ValueError(msg)

        return author

    def _create_book_record(
        self,
        session: Session,
        title: str,
        author_name: str,
        book_path_str: str,
        pubdate: datetime | None = None,
        series_index: float | None = None,
    ) -> Book:
        """Create a new book record in the database.

        Parameters
        ----------
        session : Session
            Database session.
        title : str
            Book title.
        author_name : str
            Author name for sorting.
        book_path_str : str
            Book path string (Author/Title format).
        pubdate : datetime | None
            Publication date. If None, uses current date.
        series_index : float | None
            Series index. If None, defaults to 1.0.

        Returns
        -------
        Book
            Created book instance with valid ID.

        Raises
        ------
        ValueError
            If book creation fails.
        """
        now = datetime.now(UTC)
        book_uuid = str(uuid4())
        db_book = Book(
            title=title,
            sort=title,
            author_sort=author_name,
            timestamp=now,
            pubdate=pubdate if pubdate is not None else now,
            series_index=series_index if series_index is not None else 1.0,
            flags=1,
            uuid=book_uuid,
            path=book_path_str,
            has_cover=False,
            last_modified=now,
        )
        session.add(db_book)
        session.flush()

        if db_book.id is None:
            msg = "Failed to create book"
            raise ValueError(msg)

        return db_book

    def _save_book_file(
        self,
        file_path: Path,
        library_path: Path,
        book_path_str: str,
        title_dir: str,
        file_format: str,
    ) -> None:
        """Save book file to library directory structure.

        Parameters
        ----------
        file_path : Path
            Source file path (temporary location).
        library_path : Path
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).
        title_dir : str
            Sanitized title directory name.
        file_format : str
            File format extension.
        """
        import shutil

        book_dir = library_path / book_path_str
        book_dir.mkdir(parents=True, exist_ok=True)
        library_file_path = book_dir / f"{title_dir}.{file_format.lower()}"
        shutil.copy2(file_path, library_file_path)

    def _save_book_cover(
        self,
        cover_data: bytes,
        library_path: Path,
        book_path_str: str,
    ) -> bool:
        """Save book cover image to library directory structure.

        Saves cover as cover.jpg in the book's directory. Converts image
        to JPEG format if necessary.

        Parameters
        ----------
        cover_data : bytes
            Cover image data as bytes.
        library_path : Path
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).

        Returns
        -------
        bool
            True if cover was saved successfully, False otherwise.
        """
        from io import BytesIO

        from PIL import Image

        try:
            # Load image from bytes
            img = Image.open(BytesIO(cover_data))

            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Save as JPEG
            book_dir = library_path / book_path_str
            book_dir.mkdir(parents=True, exist_ok=True)
            cover_path = book_dir / "cover.jpg"

            # Save with quality 85 (good balance of size and quality)
            img.save(cover_path, format="JPEG", quality=85)
        except (OSError, ValueError, TypeError, AttributeError):
            # If image processing fails, return False
            # This allows the book to be added even if cover extraction fails
            return False
        else:
            return True

    def _extract_book_data(
        self, file_path: Path, file_format: str
    ) -> tuple[BookMetadata, bytes | None]:
        """Extract metadata and cover art from book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.
        file_format : str
            File format extension.

        Returns
        -------
        tuple[BookMetadata, bytes | None]
            Tuple of (BookMetadata, cover_data).
        """
        extractor = BookMetadataExtractor()
        metadata = extractor.extract_metadata(file_path, file_format, file_path.name)

        cover_extractor = BookCoverExtractor()
        cover_data = cover_extractor.extract_cover(file_path, file_format)

        return metadata, cover_data

    def _normalize_book_info(
        self, title: str | None, author_name: str | None, metadata: BookMetadata
    ) -> tuple[str, str]:
        """Normalize title and author name from provided values or metadata.

        Parameters
        ----------
        title : str | None
            Provided title.
        author_name : str | None
            Provided author name.
        metadata : object
            Extracted BookMetadata.

        Returns
        -------
        tuple[str, str]
            Tuple of (normalized_title, normalized_author_name).
        """
        if title is None:
            title = metadata.title
        if not title or title.strip() == "":
            title = "Unknown"

        if author_name is None or author_name.strip() == "":
            author_name = metadata.author
        if not author_name or author_name.strip() == "":
            author_name = "Unknown"

        return title, author_name

    def _create_book_database_records(
        self,
        session: Session,
        title: str,
        author_name: str,
        book_path_str: str,
        metadata: BookMetadata,
        file_format_upper: str,
        title_dir: str,
        file_size: int,
    ) -> tuple[Book, int]:
        """Create all database records for a new book.

        Parameters
        ----------
        session : Session
            Database session.
        title : str
            Book title.
        author_name : str
            Author name.
        book_path_str : str
            Book path string.
        metadata : BookMetadata
            Extracted BookMetadata.
        file_format_upper : str
            File format in uppercase.
        title_dir : str
            Sanitized title directory name.
        file_size : int
            File size in bytes.

        Returns
        -------
        tuple[Book, int]
            Tuple of (created Book, book_id).
        """
        author = self._get_or_create_author(session, author_name)
        sort_title = metadata.sort_title or title

        db_book = self._create_book_record(
            session,
            title,
            author_name,
            book_path_str,
            pubdate=metadata.pubdate,
            series_index=metadata.series_index,
        )

        if metadata.sort_title and db_book.sort != sort_title:
            db_book.sort = sort_title

        if db_book.id is None:
            msg = "Book ID is None after creation"
            raise ValueError(msg)

        book_id = db_book.id

        book_author_link = BookAuthorLink(book=book_id, author=author.id)
        session.add(book_author_link)

        self._add_book_metadata(session, book_id, metadata)

        db_data = Data(
            book=book_id,
            format=file_format_upper,
            uncompressed_size=file_size,
            name=title_dir,
        )
        session.add(db_data)

        return db_book, book_id

    def add_book(
        self,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        library_path: Path | None = None,
    ) -> int:
        """Add a book directly to the Calibre database.

        Creates a book record, author record, and data entry for the file format.
        Saves the file to the library directory structure.
        Follows the same approach as calibre-web by directly manipulating the database.

        Parameters
        ----------
        file_path : Path
            Path to the uploaded book file (temporary location).
        file_format : str
            File format extension (e.g., 'epub', 'pdf', 'mobi').
        title : str | None
            Book title. If None, uses filename without extension.
        author_name : str | None
            Author name. If None, uses 'Unknown'.
        library_path : Path | None
            Library root path. If None, uses calibre_db_path.

        Returns
        -------
        int
            ID of the newly created book.

        Raises
        ------
        ValueError
            If file_path doesn't exist or file_format is invalid.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        if library_path is None:
            library_path = self._calibre_db_path

        metadata, cover_data = self._extract_book_data(file_path, file_format)
        title, author_name = self._normalize_book_info(title, author_name, metadata)

        file_format_upper = file_format.upper().lstrip(".")
        author_dir = self._sanitize_filename(author_name)
        title_dir = self._sanitize_filename(title)
        book_path_str = f"{author_dir}/{title_dir}".replace("\\", "/")

        with self._get_session() as session:
            file_size = file_path.stat().st_size
            db_book, book_id = self._create_book_database_records(
                session,
                title,
                author_name,
                book_path_str,
                metadata,
                file_format_upper,
                title_dir,
                file_size,
            )

            self._save_book_file(
                file_path, library_path, book_path_str, title_dir, file_format
            )

            if cover_data:
                cover_saved = self._save_book_cover(
                    cover_data, library_path, book_path_str
                )
                if cover_saved:
                    db_book.has_cover = True
                    session.add(db_book)

            session.commit()
            return book_id

    def _match_files_by_extension(
        self,
        all_files: list[Path],
        data_records: list[Data],
        existing_paths: list[Path],
        book_id: int,
    ) -> list[Path]:
        """Match files by extension when pattern matching fails.

        Parameters
        ----------
        all_files : list[Path]
            All files found in the book directory.
        data_records : list[Data]
            Data records from database.
        existing_paths : list[Path]
            Paths already matched via pattern matching.
        book_id : int
            Book ID for logging.

        Returns
        -------
        list[Path]
            Additional file paths matched by extension.
        """
        matched_paths: list[Path] = []

        if not data_records:
            if all_files:
                logger.warning(
                    "No Data records found for book_id=%d, but files exist: %s",
                    book_id,
                    [str(f.name) for f in all_files],
                )
            return matched_paths

        # Collect all expected formats from Data records
        expected_formats = {dr.format.lower() for dr in data_records}

        # Match files by extension
        for file_path in all_files:
            file_ext = file_path.suffix.lower().lstrip(".")
            if file_ext in expected_formats and file_path not in existing_paths:
                matched_paths.append(file_path)

        if matched_paths:
            logger.debug(
                "Matched %d files by extension for book_id=%d: %s",
                len(matched_paths),
                book_id,
                [str(p.name) for p in matched_paths],
            )

        return matched_paths

    def _collect_filesystem_paths(
        self,
        session: Session,
        book_id: int,
        book_path: str,
        library_path: Path,
    ) -> tuple[list[Path], Path | None]:
        """Collect filesystem paths for book files before deletion.

        Parameters
        ----------
        session : Session
            Database session for querying Data records.
        book_id : int
            Calibre book ID.
        book_path : str
            Book path string from database.
        library_path : Path
            Library root path.

        Returns
        -------
        tuple[list[Path], Path | None]
            Tuple of (list of file paths to delete, book directory path).
        """
        filesystem_paths: list[Path] = []
        book_dir = library_path / book_path

        if not (book_dir.exists() and book_dir.is_dir()):
            logger.warning(
                "Book directory does not exist or is not a directory: %r",
                book_dir,
            )
            return filesystem_paths, None

        # Find all book files from Data table
        data_stmt = select(Data).where(Data.book == book_id)
        data_records = list(session.exec(data_stmt).all())

        logger.debug("Found %d Data records for book_id=%d", len(data_records), book_id)

        for data_record in data_records:
            file_name = data_record.name or f"{book_id}"
            format_lower = data_record.format.lower()

            # Pattern 1: {name}.{format}
            file_path = book_dir / f"{file_name}.{format_lower}"
            if file_path.exists():
                filesystem_paths.append(file_path)

            # Pattern 2: {book_id}.{format}
            alt_file_path = book_dir / f"{book_id}.{format_lower}"
            if alt_file_path.exists() and alt_file_path not in filesystem_paths:
                filesystem_paths.append(alt_file_path)

        # List all files in directory for fallback matching
        all_files: list[Path] = []
        try:
            all_files = [f for f in book_dir.iterdir() if f.is_file()]
        except OSError as e:
            logger.warning("Failed to list files in book_dir %r: %s", book_dir, e)

        # Fallback: If we didn't find files via Data records, try matching by extension
        # This handles cases where filenames don't match expected patterns
        extension_matched = self._match_files_by_extension(
            all_files, data_records, filesystem_paths, book_id
        )
        filesystem_paths.extend(extension_matched)

        # Add cover.jpg if it exists
        cover_path = book_dir / "cover.jpg"
        if cover_path.exists():
            filesystem_paths.append(cover_path)

        logger.debug(
            "Collected %d filesystem paths for book_id=%d: %s",
            len(filesystem_paths),
            book_id,
            [str(p.name) for p in filesystem_paths],
        )

        return filesystem_paths, book_dir

    def _execute_database_deletion_commands(
        self,
        session: Session,
        book_id: int,
        book: Book,
    ) -> None:
        """Execute all database deletion commands for a book.

        Parameters
        ----------
        session : Session
            Database session for executing commands.
        book_id : int
            Calibre book ID.
        book : Book
            Book instance to delete.

        Raises
        ------
        Exception
            If any command fails, all previous commands are undone.
        """
        executor = CommandExecutor()

        # Execute deletion commands in order
        # If any fails, all previous commands are automatically undone
        executor.execute(DeleteBookAuthorLinksCommand(session, book_id))
        executor.execute(DeleteBookTagLinksCommand(session, book_id))
        executor.execute(DeleteBookPublisherLinksCommand(session, book_id))
        executor.execute(DeleteBookLanguageLinksCommand(session, book_id))
        executor.execute(DeleteBookRatingLinksCommand(session, book_id))
        executor.execute(DeleteBookSeriesLinksCommand(session, book_id))
        executor.execute(DeleteBookShelfLinksCommand(session, book_id))
        executor.execute(DeleteCommentCommand(session, book_id))
        executor.execute(DeleteIdentifiersCommand(session, book_id))
        executor.execute(DeleteDataRecordsCommand(session, book_id))

        # Delete the book record itself (must be last for database integrity)
        executor.execute(DeleteBookCommand(session, book))

        # Clear executor after successful execution
        executor.clear()

    def _execute_filesystem_deletion_commands(
        self,
        filesystem_paths: list[Path],
        book_dir: Path | None,
    ) -> None:
        """Execute filesystem deletion commands for book files.

        Parameters
        ----------
        filesystem_paths : list[Path]
            List of file paths to delete.
        book_dir : Path | None
            Book directory path to delete if empty.

        Raises
        ------
        OSError
            If filesystem operations fail. All previous file deletions
            are automatically undone.
        """
        if not filesystem_paths:
            return

        fs_executor = CommandExecutor()

        # Execute file deletion commands
        for file_path in filesystem_paths:
            fs_executor.execute(DeleteFileCommand(file_path))

        # Delete directory if empty (must be last)
        if book_dir and book_dir.exists() and book_dir.is_dir():
            fs_executor.execute(DeleteDirectoryCommand(book_dir))

        # If any filesystem operation fails, undo all filesystem operations
        # Database changes are already committed, so we don't undo those
        # This is acceptable as filesystem cleanup can be done manually

    def _get_book_or_raise(self, session: Session, book_id: int) -> Book:
        """Get book by ID or raise ValueError if not found.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.

        Returns
        -------
        Book
            Book instance.

        Raises
        ------
        ValueError
            If book not found.
        """
        book_stmt = select(Book).where(Book.id == book_id)
        book = session.exec(book_stmt).first()
        if book is None:
            msg = "book_not_found"
            raise ValueError(msg)
        return book

    def delete_book(
        self,
        book_id: int,
        delete_files_from_drive: bool = False,
        library_path: Path | None = None,
    ) -> None:
        """Delete a book and all its related data.

        Uses command pattern with compensating undos for atomic deletion.
        If any command fails, all previous commands are automatically undone.
        Follows SRP by delegating to command classes.

        Parameters
        ----------
        book_id : int
            Calibre book ID to delete.
        delete_files_from_drive : bool
            If True, also delete files from filesystem (default: False).
        library_path : Path | None
            Library root path for filesystem operations.
            If None, uses calibre_db_path.

        Raises
        ------
        ValueError
            If book not found.
        OSError
            If filesystem operations fail (only if delete_files_from_drive is True).
        """
        with self._get_session() as session:
            try:
                # Get book to verify it exists and get path info
                book = self._get_book_or_raise(session, book_id)

                # Collect filesystem paths BEFORE deleting Data records
                # (We need Data records to determine which files to delete)
                filesystem_paths: list[Path] = []
                book_dir: Path | None = None
                if delete_files_from_drive and library_path and book.path:
                    filesystem_paths, book_dir = self._collect_filesystem_paths(
                        session, book_id, book.path, library_path
                    )

                # Execute database deletion commands
                self._execute_database_deletion_commands(session, book_id, book)

                # Commit database changes after all commands succeed
                session.commit()

                # Perform filesystem operations after successful DB commit
                if delete_files_from_drive:
                    self._execute_filesystem_deletion_commands(
                        filesystem_paths, book_dir
                    )

            except Exception:
                # Rollback database session on any error
                session.rollback()
                raise

    def _add_book_metadata(
        self,
        session: Session,
        book_id: int,
        metadata: BookMetadata,  # type: ignore[name-defined, misc]
    ) -> None:
        """Add all metadata relationships to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        metadata : BookMetadata
            Extracted book metadata from fundamental.services.book_metadata_extractor.
        """
        # Add description if available
        if metadata.description:
            from fundamental.models.core import Comment

            comment = Comment(book=book_id, text=metadata.description)
            session.add(comment)

        # Add tags if available
        if metadata.tags:
            self._add_book_tags(session, book_id, metadata.tags)

        # Add publisher if available
        if metadata.publisher:
            self._add_book_publisher(session, book_id, metadata.publisher)

        # Add identifiers if available
        if metadata.identifiers:
            self._add_book_identifiers(session, book_id, metadata.identifiers)

        # Add languages if available
        if metadata.languages:
            self._add_book_languages(session, book_id, metadata.languages)

        # Add series if available
        if metadata.series:
            self._add_book_series(session, book_id, metadata.series)

        # Add additional contributors
        if metadata.contributors:
            self._add_book_contributors(session, book_id, metadata.contributors)

    def _add_book_tags(
        self, session: Session, book_id: int, tag_names: list[str]
    ) -> None:
        """Add tags to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        tag_names : list[str]
            List of tag names to add.
        """
        for tag_name in tag_names:
            if not tag_name.strip():
                continue
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag = session.exec(tag_stmt).first()
            if tag is None:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()
            if tag.id is not None:
                link_stmt = select(BookTagLink).where(
                    BookTagLink.book == book_id, BookTagLink.tag == tag.id
                )
                existing_link = session.exec(link_stmt).first()
                if existing_link is None:
                    link = BookTagLink(book=book_id, tag=tag.id)
                    session.add(link)

    def _add_book_publisher(
        self, session: Session, book_id: int, publisher_name: str
    ) -> None:
        """Add publisher to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        publisher_name : str
            Publisher name.
        """
        from fundamental.models.core import Publisher

        pub_stmt = select(Publisher).where(Publisher.name == publisher_name)
        publisher = session.exec(pub_stmt).first()
        if publisher is None:
            publisher = Publisher(name=publisher_name, sort=publisher_name)
            session.add(publisher)
            session.flush()
        if publisher.id is not None:
            link_stmt = select(BookPublisherLink).where(
                BookPublisherLink.book == book_id,
                BookPublisherLink.publisher == publisher.id,
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookPublisherLink(book=book_id, publisher=publisher.id)
                session.add(link)

    def _add_book_identifiers(
        self, session: Session, book_id: int, identifiers: list[dict[str, str]]
    ) -> None:
        """Add identifiers to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        identifiers : list[dict[str, str]]
            List of identifiers with 'type' and 'val' keys.
        """
        # Deduplicate by type - keep the first occurrence of each type
        # to avoid UNIQUE constraint violations
        # Note: Calibre allows multiple identifier types (isbn10, isbn13, asin, etc.)
        # but only one identifier per type per book (UNIQUE constraint on book+type)
        seen_types: set[str] = set()
        unique_identifiers: list[dict[str, str]] = []
        for ident_data in identifiers:
            ident_type = ident_data.get("type", "isbn")
            if ident_type not in seen_types:
                seen_types.add(ident_type)
                unique_identifiers.append(ident_data)

        for ident_data in unique_identifiers:
            ident_type = ident_data.get("type", "isbn")
            ident_val = ident_data.get("val", "")
            if not ident_val.strip():
                continue

            # Check if identifier with this type already exists for this book
            # (UNIQUE constraint on book+type)
            existing_stmt = select(Identifier).where(
                Identifier.book == book_id, Identifier.type == ident_type
            )
            existing = session.exec(existing_stmt).first()

            if existing is None:
                # Create new identifier
                ident = Identifier(book=book_id, type=ident_type, val=ident_val)
                session.add(ident)
            else:
                # Update existing identifier value
                existing.val = ident_val

    def _add_book_languages(
        self, session: Session, book_id: int, language_codes: list[str]
    ) -> None:
        """Add languages to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        language_codes : list[str]
            List of language codes.
        """
        for lang_code in language_codes:
            if not lang_code.strip():
                continue
            lang = self._find_or_create_language(session, lang_code)
            if lang is None or lang.id is None:
                continue
            link_stmt = select(BookLanguageLink).where(
                BookLanguageLink.book == book_id,
                BookLanguageLink.lang_code == lang.id,
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookLanguageLink(book=book_id, lang_code=lang.id, item_order=0)
                session.add(link)

    def _add_book_series(
        self, session: Session, book_id: int, series_name: str
    ) -> None:
        """Add series to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        series_name : str
            Series name.
        """
        series_stmt = select(Series).where(Series.name == series_name)
        series = session.exec(series_stmt).first()
        if series is None:
            series = Series(name=series_name, sort=series_name)
            session.add(series)
            session.flush()
        if series.id is not None:
            link_stmt = select(BookSeriesLink).where(
                BookSeriesLink.book == book_id, BookSeriesLink.series == series.id
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookSeriesLink(book=book_id, series=series.id)
                session.add(link)

    def _add_book_contributors(
        self, session: Session, book_id: int, contributors: list
    ) -> None:
        """Add additional contributors as authors.

        Calibre doesn't have separate contributor roles, so we add
        non-author contributors as additional authors.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        contributors : list
            List of Contributor objects from metadata.
        """
        for contributor in contributors:
            # Skip if already added as primary author or if role is 'author'
            if contributor.role and contributor.role != "author" and contributor.name:
                # Add as additional author (Calibre limitation)
                author = self._get_or_create_author(session, contributor.name)
                # Check if link already exists
                link_stmt = select(BookAuthorLink).where(
                    BookAuthorLink.book == book_id, BookAuthorLink.author == author.id
                )
                existing_link = session.exec(link_stmt).first()
                if existing_link is None:
                    link = BookAuthorLink(book=book_id, author=author.id)
                    session.add(link)

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

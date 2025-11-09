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
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

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
from fundamental.repositories.filters import FilterBuilder
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.repositories.suggestions import FilterSuggestionFactory

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterator

    from sqlalchemy import Engine


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

            def _register_title_sort(
                dbapi_conn: sqlite3.Connection, connection_record: object
            ) -> None:
                """Register title_sort SQLite function.

                Calibre's database triggers reference this function, which
                normalizes titles for sorting (removing articles, etc.).
                This implementation returns the title as-is for simplicity.

                Parameters
                ----------
                dbapi_conn : sqlite3.Connection
                    SQLite database connection.
                connection_record : object
                    Connection record (required by event listener signature).
                """
                # connection_record is required by event listener signature but unused
                _ = connection_record
                dbapi_conn.create_function("title_sort", 1, lambda x: x or "")

            self._engine = create_engine(db_url, echo=False, future=True)
            event.listen(self._engine, "connect", _register_title_sort)
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
            authors = list(session.exec(authors_stmt).all())

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
            authors = list(session.exec(authors_stmt).all())

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
        existing_links = session.exec(delete_links_stmt).all()
        for link in existing_links:
            session.delete(link)

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
            # Create link if doesn't exist
            link_stmt = select(BookAuthorLink).where(
                BookAuthorLink.book == book_id,
                BookAuthorLink.author == author.id,
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
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
            if current_link is not None:
                session.delete(current_link)
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
        if current_link is not None:
            session.delete(current_link)

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
        existing_tag_links = session.exec(delete_tags_stmt).all()
        for link in existing_tag_links:
            session.delete(link)

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
        for ident in current_identifiers:
            session.delete(ident)

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
        if current_link is not None:
            session.delete(current_link)

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
        if current_link is not None:
            session.delete(current_link)

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

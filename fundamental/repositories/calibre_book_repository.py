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

"""Refactored repository for querying Calibre SQLite database.

This repository has been refactored to follow SOLID principles:
- Single Responsibility: Delegates to specialized services
- Open/Closed: Extensible through dependency injection
- Liskov Substitution: Implements IBookRepository interface
- Interface Segregation: Uses focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Generator

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

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
from fundamental.repositories.book_metadata_service import BookMetadataService
from fundamental.repositories.book_relationship_manager import BookRelationshipManager
from fundamental.repositories.book_search_service import BookSearchService
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
from fundamental.repositories.file_manager import CalibreFileManager
from fundamental.repositories.filters import FilterBuilder
from fundamental.repositories.interfaces import (
    IBookMetadataService,
    IBookRelationshipManager,
    IBookRepository,
    IBookSearchService,
    IFileManager,
    ILibraryStatisticsService,
    ISessionManager,
)
from fundamental.repositories.library_statistics_service import (
    LibraryStatisticsService,
)
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.repositories.session_manager import CalibreSessionManager
from fundamental.repositories.suggestions import FilterSuggestionFactory

if TYPE_CHECKING:
    from sqlalchemy.sql import Select, Subquery

    from fundamental.services.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class CalibreBookRepository(IBookRepository):
    """Repository for querying books from Calibre SQLite database.

    Refactored to follow SOLID principles by delegating to specialized services.
    Uses dependency injection for all dependencies.

    Parameters
    ----------
    calibre_db_path : str
        Path to Calibre library directory (contains metadata.db).
    calibre_db_file : str
        Calibre database filename (default: 'metadata.db').
    session_manager : ISessionManager | None
        Optional session manager (creates default if None).
    file_manager : IFileManager | None
        Optional file manager (creates default if None).
    relationship_manager : IBookRelationshipManager | None
        Optional relationship manager (creates default if None).
    metadata_service : IBookMetadataService | None
        Optional metadata service (creates default if None).
    search_service : IBookSearchService | None
        Optional search service (creates default if None).
    statistics_service : ILibraryStatisticsService | None
        Optional statistics service (creates default if None).
    """

    def __init__(
        self,
        calibre_db_path: str,
        calibre_db_file: str = "metadata.db",
        session_manager: ISessionManager | None = None,
        file_manager: IFileManager | None = None,
        relationship_manager: IBookRelationshipManager | None = None,
        metadata_service: IBookMetadataService | None = None,
        search_service: IBookSearchService | None = None,
        statistics_service: ILibraryStatisticsService | None = None,
    ) -> None:
        self._calibre_db_path = Path(calibre_db_path)
        self._calibre_db_file = calibre_db_file

        # Dependency injection - use provided services or create defaults
        self._session_manager = session_manager or CalibreSessionManager(
            calibre_db_path, calibre_db_file
        )
        self._file_manager = file_manager or CalibreFileManager()
        self._relationship_manager = relationship_manager or BookRelationshipManager()
        self._metadata_service = metadata_service or BookMetadataService()
        self._search_service = search_service or BookSearchService()
        self._statistics_service = statistics_service or LibraryStatisticsService()

    def dispose(self) -> None:
        """Dispose of the database engine and close all connections."""
        self._session_manager.dispose()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a SQLModel session for the Calibre database.

        Yields
        ------
        Session
            SQLModel session.
        """
        with self._session_manager.get_session() as session:
            yield session

    # Result unwrapping helpers (kept here as they're query-specific)
    def _unwrap_book_from_result(self, result: object) -> Book | None:
        """Extract Book instance from query result using strategy pattern."""
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
        """Extract series name from query result using strategy pattern."""
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

    # Query building helpers
    def _get_sort_field(self, sort_by: str) -> object | None:
        """Get sort field for query ordering.

        Parameters
        ----------
        sort_by : str
            Sort field name.

        Returns
        -------
        object | None
            SQLAlchemy column or function for sorting, or None for random sort.
        """
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        if sort_by == "random":
            return None  # Special case for random sorting
        return valid_sort_fields.get(sort_by, Book.timestamp)  # type: ignore[return-value]

    def _build_author_books_subquery(
        self,
        session: Session,
        author_id: int | None,
    ) -> Subquery | None:
        """Build optional subquery for author filter in list_books."""
        if author_id is None:
            return None

        author_books_subquery: Subquery = (
            select(BookAuthorLink.book)
            .where(BookAuthorLink.author == author_id)
            .subquery()
        )
        author_book_count = session.exec(
            select(func.count()).select_from(author_books_subquery)
        ).one()
        logger.debug(
            "Author filter active in list_books: author_id=%s, linked_books=%s",
            author_id,
            author_book_count,
        )
        return author_books_subquery

    def _apply_pubdate_filter(
        self,
        stmt: Select,
        pubdate_month: int | None,
        pubdate_day: int | None,
    ) -> Select:
        """Apply publication date filtering to a query.

        Parameters
        ----------
        stmt : Select
            SQLAlchemy select statement.
        pubdate_month : int | None
            Optional month (1-12) to filter by.
        pubdate_day : int | None
            Optional day (1-31) to filter by.

        Returns
        -------
        Select
            Statement with date filters applied.
        """
        conditions = []
        if pubdate_month is not None:
            # SQLite strftime returns month as '01'-'12', so format month as 2-digit
            month_str = f"{pubdate_month:02d}"
            conditions.append(
                func.strftime("%m", Book.pubdate) == month_str  # type: ignore[attr-defined]
            )
        if pubdate_day is not None:
            # SQLite strftime returns day as '01'-'31', so format day as 2-digit
            day_str = f"{pubdate_day:02d}"
            conditions.append(
                func.strftime("%d", Book.pubdate) == day_str  # type: ignore[attr-defined]
            )
        if conditions:
            # Combine conditions with AND, and ensure pubdate is not NULL
            combined_condition = Book.pubdate.isnot(None)  # type: ignore[attr-defined]
            for condition in conditions:
                combined_condition = combined_condition & condition  # type: ignore[assignment]
            stmt = stmt.where(combined_condition)
        return stmt

    def _build_list_books_base_query(
        self,
        search_query: str | None,
    ) -> Select:
        """Build base query for list_books including series and optional search."""
        series_alias = aliased(Series)
        stmt = (
            select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
            .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
            .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
        )

        if not search_query:
            return stmt

        # Use case-insensitive search for SQLite
        query_lower = search_query.lower()
        pattern_lower = f"%{query_lower}%"
        author_alias = aliased(Author)
        tag_alias = aliased(Tag)

        return (
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

    def _apply_ordering_and_pagination(
        self,
        stmt: Select,
        sort_field: object | None,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> Select:
        """Apply ordering and pagination to a list_books query.

        Parameters
        ----------
        stmt : Select
            SQLAlchemy select statement.
        sort_field : object | None
            Sort field (column) or None for random sorting.
        sort_order : str
            Sort order: 'asc' or 'desc' (ignored for random).
        limit : int
            Maximum number of results.
        offset : int
            Number of results to skip.

        Returns
        -------
        Select
            Statement with ordering and pagination applied.
        """
        if sort_field is None:
            # Random sorting using SQLite's random() function
            stmt = stmt.order_by(func.random())  # type: ignore[attr-defined]
        elif sort_order == "desc":
            stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
        else:
            stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]

        return stmt.limit(limit).offset(offset)

    def _build_book_with_relations(
        self, session: Session, result: object
    ) -> BookWithRelations | None:
        """Build BookWithRelations from query result."""
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

    def _build_books_from_results(
        self,
        session: Session,
        results: list[object],
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """Build list of `BookWithRelations` from raw query results."""
        books: list[BookWithRelations | BookWithFullRelations] = []
        for result in results:
            book_with_relations = self._build_book_with_relations(session, result)
            if book_with_relations is not None:
                books.append(book_with_relations)
        return books

    # Metadata fetching helpers (for enriching books)
    def _fetch_tags_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[str]]:
        """Fetch tags map for given book IDs."""
        tags_stmt = (
            select(BookTagLink.book, Tag.name)
            .join(Tag, BookTagLink.tag == Tag.id)
            .where(BookTagLink.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(BookTagLink.book, BookTagLink.id)
        )
        tags_map: dict[int, list[str]] = {}
        for book_id, tag_name in session.exec(tags_stmt).all():
            if book_id not in tags_map:
                tags_map[book_id] = []
            tags_map[book_id].append(tag_name)
        return tags_map

    def _fetch_identifiers_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str]]]:
        """Fetch identifiers map for given book IDs."""
        identifiers_stmt = (
            select(Identifier.book, Identifier.type, Identifier.val)
            .where(Identifier.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(Identifier.book, Identifier.id)
        )
        identifiers_map: dict[int, list[dict[str, str]]] = {}
        for book_id, ident_type, ident_val in session.exec(identifiers_stmt).all():
            if book_id not in identifiers_map:
                identifiers_map[book_id] = []
            identifiers_map[book_id].append({"type": ident_type, "val": ident_val})
        return identifiers_map

    def _fetch_descriptions_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, str | None]:
        """Fetch descriptions map for given book IDs."""
        comments_stmt = select(Comment.book, Comment.text).where(
            Comment.book.in_(book_ids)  # type: ignore[attr-defined]
        )
        return dict(session.exec(comments_stmt).all())

    def _fetch_publishers_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[str | None, int | None]]:
        """Fetch publishers map for given book IDs."""
        publishers_stmt = (
            select(BookPublisherLink.book, Publisher.name, Publisher.id)
            .join(Publisher, BookPublisherLink.publisher == Publisher.id)
            .where(BookPublisherLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        publishers_map: dict[int, tuple[str | None, int | None]] = {}
        for book_id, pub_name, pub_id in session.exec(publishers_stmt).all():
            publishers_map[book_id] = (pub_name, pub_id)
        return publishers_map

    def _fetch_languages_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[list[str], list[int]]]:
        """Fetch languages map for given book IDs."""
        languages_stmt = (
            select(BookLanguageLink.book, Language.lang_code, Language.id)
            .join(Language, Language.id == BookLanguageLink.lang_code)
            .where(BookLanguageLink.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(BookLanguageLink.book, BookLanguageLink.item_order)
        )
        languages_map: dict[int, tuple[list[str], list[int]]] = {}
        for book_id, lang_code, lang_id in session.exec(languages_stmt).all():
            if book_id not in languages_map:
                languages_map[book_id] = ([], [])
            languages_map[book_id][0].append(lang_code)
            if lang_id is not None:
                languages_map[book_id][1].append(lang_id)
        return languages_map

    def _fetch_ratings_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[int | None, int | None]]:
        """Fetch ratings map for given book IDs."""
        ratings_stmt = (
            select(BookRatingLink.book, Rating.rating, Rating.id)
            .join(Rating, BookRatingLink.rating == Rating.id)
            .where(BookRatingLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        ratings_map: dict[int, tuple[int | None, int | None]] = {}
        for book_id, rating, rating_id in session.exec(ratings_stmt).all():
            ratings_map[book_id] = (rating, rating_id)
        return ratings_map

    def _fetch_formats_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str | int]]]:
        """Fetch formats map for given book IDs."""
        formats_stmt = (
            select(Data.book, Data.format, Data.uncompressed_size, Data.name)
            .where(Data.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(Data.book, Data.format)
        )
        formats_map: dict[int, list[dict[str, str | int]]] = {}
        for book_id, fmt, size, name in session.exec(formats_stmt).all():
            if book_id not in formats_map:
                formats_map[book_id] = []
            formats_map[book_id].append({
                "format": fmt,
                "size": size,
                "name": name or "",
            })
        return formats_map

    def _fetch_series_ids_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, int | None]:
        """Fetch series IDs map for given book IDs."""
        series_ids_stmt = (
            select(BookSeriesLink.book, Series.id)
            .join(Series, BookSeriesLink.series == Series.id)
            .where(BookSeriesLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        return dict(session.exec(series_ids_stmt).all())

    def _build_enriched_book(
        self,
        book_with_rels: BookWithRelations,
        tags_map: dict[int, list[str]],
        identifiers_map: dict[int, list[dict[str, str]]],
        descriptions_map: dict[int, str | None],
        publishers_map: dict[int, tuple[str | None, int | None]],
        languages_map: dict[int, tuple[list[str], list[int]]],
        ratings_map: dict[int, tuple[int | None, int | None]],
        formats_map: dict[int, list[dict[str, str | int]]],
        series_ids_map: dict[int, int | None],
    ) -> BookWithFullRelations | None:
        """Build BookWithFullRelations from BookWithRelations and metadata maps."""
        book_id = book_with_rels.book.id
        if book_id is None:
            return None

        publisher_data = publishers_map.get(book_id, (None, None))
        languages_data = languages_map.get(book_id, ([], []))
        ratings_data = ratings_map.get(book_id, (None, None))

        return BookWithFullRelations(
            book=book_with_rels.book,
            authors=book_with_rels.authors,
            series=book_with_rels.series,
            series_id=series_ids_map.get(book_id),
            tags=tags_map.get(book_id, []),
            identifiers=identifiers_map.get(book_id, []),
            description=descriptions_map.get(book_id),
            publisher=publisher_data[0],
            publisher_id=publisher_data[1],
            languages=languages_data[0],
            language_ids=languages_data[1],
            rating=ratings_data[0],
            rating_id=ratings_data[1],
            formats=formats_map.get(book_id, []),
        )

    def _enrich_books_with_full_details(
        self,
        session: Session,
        books: list[BookWithRelations],
    ) -> list[BookWithFullRelations]:
        """Enrich a list of BookWithRelations with full details."""
        if not books:
            return []

        book_ids = [book.book.id for book in books if book.book.id is not None]
        if not book_ids:
            return []

        # Fetch all metadata maps using helper methods
        tags_map = self._fetch_tags_map(session, book_ids)
        identifiers_map = self._fetch_identifiers_map(session, book_ids)
        descriptions_map = self._fetch_descriptions_map(session, book_ids)
        publishers_map = self._fetch_publishers_map(session, book_ids)
        languages_map = self._fetch_languages_map(session, book_ids)
        ratings_map = self._fetch_ratings_map(session, book_ids)
        formats_map = self._fetch_formats_map(session, book_ids)
        series_ids_map = self._fetch_series_ids_map(session, book_ids)

        # Build enriched books
        enriched_books: list[BookWithFullRelations] = []
        for book_with_rels in books:
            enriched_book = self._build_enriched_book(
                book_with_rels,
                tags_map,
                identifiers_map,
                descriptions_map,
                publishers_map,
                languages_map,
                ratings_map,
                formats_map,
                series_ids_map,
            )
            if enriched_book is not None:
                enriched_books.append(enriched_book)

        return enriched_books

    # Public API methods
    def count_books(
        self,
        search_query: str | None = None,
        author_id: int | None = None,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> int:
        """Count total number of books, optionally filtered by search."""
        with self.get_session() as session:
            logger.debug(
                "count_books called with search_query=%r, author_id=%r, pubdate_month=%s, pubdate_day=%s",
                search_query,
                author_id,
                pubdate_month,
                pubdate_day,
            )

            # Optional subquery for author filter to avoid join conflicts with search
            author_books_subquery = None
            if author_id is not None:
                author_books_subquery = (
                    select(BookAuthorLink.book)
                    .where(BookAuthorLink.author == author_id)
                    .subquery()
                )

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

            # Apply author filter if present
            if author_books_subquery is not None:
                author_book_count = session.exec(
                    select(func.count()).select_from(author_books_subquery)
                ).one()
                logger.debug(
                    "Author filter active in count_books: author_id=%s, linked_books=%s",
                    author_id,
                    author_book_count,
                )
                stmt = stmt.where(Book.id.in_(author_books_subquery))  # type: ignore[arg-type]

            # Apply publication date filter if present
            stmt = self._apply_pubdate_filter(
                stmt=stmt,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )

            logger.debug("count_books SQL statement: %s", stmt)

            result = session.exec(stmt).one()
            logger.debug("count_books result=%s", result)
            return result if result else 0

    def list_books(
        self,
        limit: int = 20,
        offset: int = 0,
        search_query: str | None = None,
        author_id: int | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """List books with pagination and optional search."""
        logger.debug(
            "list_books called with limit=%s, offset=%s, search_query=%r, author_id=%r, sort_by=%s, sort_order=%s, full=%s, pubdate_month=%s, pubdate_day=%s",
            limit,
            offset,
            search_query,
            author_id,
            sort_by,
            sort_order,
            full,
            pubdate_month,
            pubdate_day,
        )

        sort_field = self._get_sort_field(sort_by)
        normalized_sort_order = sort_order.lower()
        if normalized_sort_order not in {"asc", "desc"}:
            normalized_sort_order = "desc"

        with self.get_session() as session:
            # Optional subquery for author filter to avoid join conflicts with search
            author_books_subquery = self._build_author_books_subquery(
                session,
                author_id,
            )

            # Build base query with series and apply search conditions
            stmt = self._build_list_books_base_query(
                search_query=search_query,
            )

            # Apply author filter if present
            if author_books_subquery is not None:
                author_filter_condition = Book.id.in_(  # type: ignore[union-attr]
                    author_books_subquery,
                )
                stmt = stmt.where(author_filter_condition)

            # Apply publication date filter if present
            stmt = self._apply_pubdate_filter(
                stmt=stmt,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )

            logger.debug("list_books SQL statement: %s", stmt)

            # Add ordering and pagination
            stmt = self._apply_ordering_and_pagination(
                stmt=stmt,
                sort_field=sort_field,
                sort_order=normalized_sort_order,
                limit=limit,
                offset=offset,
            )

            # Execute query
            results = session.exec(stmt).all()
            logger.debug(
                "list_books raw result rows=%s (before unwrap)",
                len(results),
            )

            books = self._build_books_from_results(session, results)

            if author_id is not None:
                sample_ids = [b.book.id for b in books[:5] if b.book.id is not None]
                logger.debug(
                    "list_books after unwrap: books_count=%s, sample_book_ids=%s",
                    len(books),
                    sample_ids,
                )

            # Enrich with full details if requested
            if full:
                base_books: list[BookWithRelations] = [
                    b for b in books if isinstance(b, BookWithRelations)
                ]
                return self._enrich_books_with_full_details(
                    session,
                    base_books,
                )  # type: ignore[invalid-return-type]

            return books

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
        full: bool = False,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """List books with multiple filter criteria using OR conditions."""
        sort_field = self._get_sort_field(sort_by)
        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        with self.get_session() as session:
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

            # Apply ordering
            if sort_field is None:
                # Random sorting
                stmt = stmt.order_by(func.random())  # type: ignore[attr-defined]
            elif sort_order.lower() == "desc":
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

            # Enrich with full details if requested
            if full:
                return self._enrich_books_with_full_details(session, books)  # type: ignore[invalid-return-type]

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
        """Count books matching filter criteria."""
        with self.get_session() as session:
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
        """Get a book by ID."""
        with self.get_session() as session:
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
        """Get a book by ID with all related metadata for editing."""
        with self.get_session() as session:
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

    def _update_book_relationships(
        self,
        session: Session,
        book_id: int,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        """Update all book relationships.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID to update.
        author_names : list[str] | None
            Author names to update.
        series_name : str | None
            Series name to update.
        series_id : int | None
            Series ID to update.
        tag_names : list[str] | None
            Tag names to update.
        identifiers : list[dict[str, str]] | None
            Identifiers to update.
        description : str | None
            Description to update.
        publisher_name : str | None
            Publisher name to update.
        publisher_id : int | None
            Publisher ID to update.
        language_codes : list[str] | None
            Language codes to update.
        language_ids : list[int] | None
            Language IDs to update.
        rating_value : int | None
            Rating value to update.
        rating_id : int | None
            Rating ID to update.
        """
        # Update authors first (before book fields to avoid trigger issues)
        if author_names is not None:
            self._relationship_manager.update_authors(session, book_id, author_names)

        # Update series
        if series_name is not None or series_id is not None:
            self._relationship_manager.update_series(
                session, book_id, series_name, series_id
            )

        # Update tags
        if tag_names is not None:
            self._relationship_manager.update_tags(session, book_id, tag_names)

        # Update identifiers
        if identifiers is not None:
            self._relationship_manager.update_identifiers(session, book_id, identifiers)

        # Update description
        if description is not None:
            comment_stmt = select(Comment).where(Comment.book == book_id)
            comment = session.exec(comment_stmt).first()
            if comment is None:
                comment = Comment(book=book_id, text=description)
                session.add(comment)
            else:
                comment.text = description

        # Update publisher
        if publisher_id is not None or publisher_name is not None:
            self._relationship_manager.update_publisher(
                session, book_id, publisher_name, publisher_id
            )

        # Update language
        if language_ids is not None or language_codes is not None:
            self._relationship_manager.update_languages(
                session,
                book_id,
                language_codes=language_codes,
                language_ids=language_ids,
            )

        # Update rating
        if rating_id is not None or rating_value is not None:
            self._relationship_manager.update_rating(
                session, book_id, rating_value, rating_id
            )

    def _update_book_fields(
        self,
        book: Book,
        title: str | None = None,
        pubdate: datetime | None = None,
        series_index: float | None = None,
    ) -> None:
        """Update book core fields.

        Parameters
        ----------
        book : Book
            Book instance to update.
        title : str | None
            Title to update.
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
        """Update book metadata."""
        with self.get_session() as session:
            # Disable autoflush to prevent errors with Calibre-specific SQLite functions
            # (e.g., title_sort) that may be referenced in triggers
            with session.no_autoflush:
                # Get existing book
                book_stmt = select(Book).where(Book.id == book_id)
                book = session.exec(book_stmt).first()
                if book is None:
                    return None

                # Store old path for potential file move
                old_path = book.path

                # Get existing authors before update to check if path needs to change
                existing_authors_stmt = (
                    select(Author.name)
                    .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                    .where(BookAuthorLink.book == book_id)
                    .order_by(BookAuthorLink.id)
                )
                existing_authors = list(session.exec(existing_authors_stmt).all())
                existing_title = book.title

                # Update relationships first (before book fields to avoid trigger issues)
                self._update_book_relationships(
                    session,
                    book_id,
                    author_names=author_names,
                    series_name=series_name,
                    series_id=series_id,
                    tag_names=tag_names,
                    identifiers=identifiers,
                    description=description,
                    publisher_name=publisher_name,
                    publisher_id=publisher_id,
                    language_codes=language_codes,
                    language_ids=language_ids,
                    rating_value=rating_value,
                    rating_id=rating_id,
                )

                # Get updated authors after relationship update
                updated_authors_stmt = (
                    select(Author.name)
                    .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                    .where(BookAuthorLink.book == book_id)
                    .order_by(BookAuthorLink.id)
                )
                updated_authors = list(session.exec(updated_authors_stmt).all())

                # Determine final author and title for path calculation
                final_author_names = (
                    updated_authors if author_names is not None else existing_authors
                )
                final_title = title if title is not None else existing_title

                # Calculate new path if author or title changed
                new_path = self._calculate_book_path(final_author_names, final_title)

                # Update book path if it changed
                if new_path and new_path != old_path:
                    book.path = new_path
                    # Move files after database update but before commit
                    # This ensures we have the new path in the database
                    # but files are moved atomically
                    library_path = self._get_library_path()
                    try:
                        self._file_manager.move_book_directory(
                            old_book_path=old_path,
                            new_book_path=new_path,
                            library_path=library_path,
                        )
                        logger.info(
                            "Moved book directory: book_id=%d, %s -> %s",
                            book_id,
                            old_path,
                            new_path,
                        )
                    except OSError:
                        logger.exception(
                            "Failed to move book directory for book_id=%d",
                            book_id,
                        )
                        # Rollback path change on filesystem error
                        book.path = old_path
                        raise

                # Update book fields last (after all other operations to avoid
                # triggering title_sort function during intermediate flushes)
                self._update_book_fields(
                    book, title=title, pubdate=pubdate, series_index=series_index
                )

            session.commit()
            session.refresh(book)

            # Return updated book with full relations
            return self.get_book_full(book_id)

    def _get_library_path(self) -> Path:
        """Get library root path from calibre_db_path.

        Returns
        -------
        Path
            Library root path.
        """
        if self._calibre_db_path.is_dir():
            return self._calibre_db_path
        return self._calibre_db_path.parent

    def add_book(
        self,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        pubdate: datetime | None = None,
        library_path: Path | None = None,
    ) -> int:
        """Add a book directly to the Calibre database."""
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        if library_path is None:
            library_path = self._calibre_db_path

        # Extract metadata and cover using metadata service
        metadata, cover_data = self._metadata_service.extract_metadata(
            file_path, file_format
        )

        # Normalize title and author
        if title is None:
            title = metadata.title
        if not title or title.strip() == "":
            title = "Unknown"

        if author_name is None or author_name.strip() == "":
            author_name = metadata.author
        if not author_name or author_name.strip() == "":
            author_name = "Unknown"

        # Use provided pubdate, fallback to metadata pubdate, then None
        # (None will use file metadata or current date in _create_book_record)
        if pubdate is None:
            pubdate = metadata.pubdate

        file_format_upper = file_format.upper().lstrip(".")
        author_dir = self._sanitize_filename(author_name)
        title_dir = self._sanitize_filename(title)
        book_path_str = f"{author_dir}/{title_dir}".replace("\\", "/")

        with self.get_session() as session:
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
                pubdate=pubdate,
            )

            # Save file using file manager
            self._file_manager.save_book_file(
                file_path, library_path, book_path_str, title_dir, file_format
            )

            # Save cover if available
            if cover_data:
                cover_saved = self._file_manager.save_book_cover(
                    cover_data, library_path, book_path_str
                )
                if cover_saved:
                    db_book.has_cover = True
                    session.add(db_book)

            session.commit()
            return book_id

    def _sanitize_filename(self, name: str, max_length: int = 96) -> str:
        """Sanitize filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        sanitized = "".join(c if c not in invalid_chars else "_" for c in name)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized.strip() or "Unknown"

    def _calculate_book_path(
        self, author_names: list[str] | None, title: str | None
    ) -> str | None:
        """Calculate book path from author names and title.

        Parameters
        ----------
        author_names : list[str] | None
            List of author names. If None, returns None.
        title : str | None
            Book title. If None, returns None.

        Returns
        -------
        str | None
            Book path string (Author/Title format) or None if insufficient data.
        """
        if not author_names or not title:
            return None

        # Use first author for directory structure (Calibre convention)
        author_name = author_names[0] if author_names else "Unknown"
        author_dir = self._sanitize_filename(author_name)
        title_dir = self._sanitize_filename(title)
        return f"{author_dir}/{title_dir}".replace("\\", "/")

    def _get_or_create_author(self, session: Session, author_name: str) -> Author:
        """Get existing author or create a new one."""
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
        """Create a new book record in the database."""
        now = datetime.now(UTC)
        book_uuid = str(uuid4())
        db_book = Book(
            title=title,
            sort=title,
            author_sort=author_name,
            timestamp=now,
            pubdate=pubdate,  # Use provided pubdate (from API or file), None will use model default
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
        pubdate: datetime | None = None,
    ) -> tuple[Book, int]:
        """Create all database records for a new book."""
        author = self._get_or_create_author(session, author_name)
        sort_title = metadata.sort_title or title

        # Use provided pubdate (from metadata provider API), fallback to file metadata
        final_pubdate = pubdate if pubdate is not None else metadata.pubdate

        db_book = self._create_book_record(
            session,
            title,
            author_name,
            book_path_str,
            pubdate=final_pubdate,
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

        # Add metadata using relationship manager
        self._relationship_manager.add_metadata(session, book_id, metadata)

        db_data = Data(
            book=book_id,
            format=file_format_upper,
            uncompressed_size=file_size,
            name=title_dir,
        )
        session.add(db_data)

        return db_book, book_id

    def _raise_book_not_found_error(self) -> None:
        """Raise ValueError for book not found.

        Raises
        ------
        ValueError
            Always raises with message "book_not_found".
        """
        msg = "book_not_found"
        raise ValueError(msg)

    def delete_book(
        self,
        book_id: int,
        delete_files_from_drive: bool = False,
        library_path: Path | None = None,
    ) -> None:
        """Delete a book and all its related data."""
        with self.get_session() as session:
            try:
                # Get book to verify it exists and get path info
                book_stmt = select(Book).where(Book.id == book_id)
                book = session.exec(book_stmt).first()
                if book is None:
                    self._raise_book_not_found_error()

                # Collect filesystem paths BEFORE deleting Data records
                # (We need Data records to determine which files to delete)
                filesystem_paths: list[Path] = []
                book_dir: Path | None = None
                if delete_files_from_drive and library_path and book.path:
                    filesystem_paths, book_dir = self._file_manager.collect_book_files(
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

    def _execute_database_deletion_commands(
        self,
        session: Session,
        book_id: int,
        book: Book,
    ) -> None:
        """Execute all database deletion commands for a book."""
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
        """Execute filesystem deletion commands for book files."""
        if not filesystem_paths:
            return

        fs_executor = CommandExecutor()

        # Execute file deletion commands
        for file_path in filesystem_paths:
            fs_executor.execute(DeleteFileCommand(file_path))

        # Delete directory if empty (must be last)
        if book_dir and book_dir.exists() and book_dir.is_dir():
            fs_executor.execute(DeleteDirectoryCommand(book_dir))

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series."""
        if not query or not query.strip():
            return {"books": [], "authors": [], "tags": [], "series": []}

        with self.get_session() as session:
            return self._search_service.search_suggestions(
                session,
                query,
                book_limit,
                author_limit,
                tag_limit,
                series_limit,
            )

    def filter_suggestions(
        self,
        query: str,
        filter_type: str,
        limit: int = 10,
    ) -> list[dict[str, str | int]]:
        """Get filter suggestions for a specific filter type."""
        if not query or not query.strip():
            return []

        strategy = FilterSuggestionFactory.get_strategy(filter_type)
        if strategy is None:
            return []

        with self.get_session() as session:
            return strategy.get_suggestions(session, query, limit)

    def get_library_stats(self) -> dict[str, int | float]:
        """Get library statistics."""
        with self.get_session() as session:
            return self._statistics_service.get_statistics(session)

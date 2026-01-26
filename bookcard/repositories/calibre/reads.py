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

"""Read operations for the Calibre book repository."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookSeriesLink,
    Series,
)
from bookcard.models.media import Data
from bookcard.repositories.filters import FilterBuilder
from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
from bookcard.repositories.suggestions import FilterSuggestionFactory

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from bookcard.repositories.interfaces import (
        IBookSearchService,
        ILibraryStatisticsService,
        ISessionManager,
    )

    from .enrichment import BookEnrichmentService
    from .pathing import BookPathService
    from .queries import BookQueryBuilder
    from .retry import SQLiteRetryPolicy
    from .unwrapping import ResultUnwrapper

logger = logging.getLogger(__name__)


class BookReadOperations:
    """Read-only operations for `CalibreBookRepository`."""

    def __init__(
        self,
        *,
        session_manager: ISessionManager,
        retry_policy: SQLiteRetryPolicy,
        unwrapper: ResultUnwrapper,
        queries: BookQueryBuilder,
        enrichment: BookEnrichmentService,
        search_service: IBookSearchService,
        statistics_service: ILibraryStatisticsService,
        pathing: BookPathService,
        calibre_db_path: Path,
    ) -> None:
        self._session_manager: ISessionManager = session_manager
        self._retry: SQLiteRetryPolicy = retry_policy
        self._unwrapper: ResultUnwrapper = unwrapper
        self._queries: BookQueryBuilder = queries
        self._enrichment: BookEnrichmentService = enrichment
        self._search_service = search_service
        self._statistics_service = statistics_service
        self._pathing = pathing
        self._calibre_db_path = calibre_db_path

    def count_books(
        self,
        *,
        search_query: str | None = None,
        author_id: int | None = None,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> int:
        """Count total number of books, optionally filtered by search.

        Parameters
        ----------
        search_query : str | None
            Optional search query.
        author_id : int | None
            Optional author id filter.
        pubdate_month : int | None
            Optional publication month filter.
        pubdate_day : int | None
            Optional publication day filter.

        Returns
        -------
        int
            Number of matching books.
        """

        def _op(session: Session) -> int:
            stmt = self._queries.build_count_stmt(search_query=search_query)

            if author_id is not None:
                author_books_subquery = self._queries.build_author_books_subquery(
                    session, author_id
                )
                if author_books_subquery is not None:
                    stmt = stmt.where(Book.id.in_(author_books_subquery))  # type: ignore[arg-type]

            stmt = self._queries.apply_pubdate_filter(
                stmt,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )
            result = session.exec(stmt).one()  # type: ignore[arg-type]
            return int(result) if result else 0

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="count_books",
        )

    def list_books(
        self,
        *,
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
        sort_field = self._queries.get_sort_field(sort_by)
        normalized_sort_order = sort_order.lower()
        if normalized_sort_order not in {"asc", "desc"}:
            normalized_sort_order = "desc"

        def _op(session: Session) -> list[BookWithRelations | BookWithFullRelations]:
            author_books_subquery = self._queries.build_author_books_subquery(
                session, author_id
            )

            stmt = self._queries.build_list_base_stmt(search_query=search_query)
            if author_books_subquery is not None:
                stmt = stmt.where(Book.id.in_(author_books_subquery))  # type: ignore[arg-type]

            stmt = self._queries.apply_pubdate_filter(
                stmt,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )

            stmt = self._queries.apply_ordering_and_pagination(
                stmt,
                sort_field=sort_field,
                sort_order=normalized_sort_order,
                limit=limit,
                offset=offset,
            )

            results = session.exec(stmt).all()  # type: ignore[arg-type]
            base_books = self._build_books_from_results(session, results)

            if full:
                return cast(
                    "list[BookWithRelations | BookWithFullRelations]",
                    self._enrichment.enrich_books_with_full_details(
                        session, base_books
                    ),
                )
            self._enrich_base_books_for_list(session, base_books)
            return cast("list[BookWithRelations | BookWithFullRelations]", base_books)

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="list_books",
        )

    def list_books_with_filters(
        self,
        *,
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
        sort_field = self._queries.get_sort_field(sort_by)
        normalized_sort_order = sort_order.lower()
        if normalized_sort_order not in {"asc", "desc"}:
            normalized_sort_order = "desc"

        def _op(session: Session) -> list[BookWithRelations | BookWithFullRelations]:
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

            stmt = self._queries.apply_ordering_and_pagination(
                stmt,
                sort_field=sort_field,
                sort_order=normalized_sort_order,
                limit=limit,
                offset=offset,
            )

            results = session.exec(stmt).all()  # type: ignore[arg-type]
            base_books = self._build_books_from_results(session, results)
            if full:
                return cast(
                    "list[BookWithRelations | BookWithFullRelations]",
                    self._enrichment.enrich_books_with_full_details(
                        session, base_books
                    ),
                )
            self._enrich_base_books_for_list(session, base_books)
            return cast("list[BookWithRelations | BookWithFullRelations]", base_books)

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="list_books_with_filters",
        )

    def count_books_with_filters(
        self,
        *,
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

        def _op(session: Session) -> int:
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
            result = session.exec(stmt).one()  # type: ignore[arg-type]
            return int(result) if result else 0

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="count_books_with_filters",
        )

    def get_book(self, *, book_id: int) -> BookWithRelations | None:
        """Get a book by ID."""

        def _op(session: Session) -> BookWithRelations | None:
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

            book = self._unwrapper.unwrap_book(result)
            if book is None:
                return None

            series_name = self._unwrapper.unwrap_series_name(result)

            authors = self._fetch_author_names(session, book_id=book_id)
            formats = self._enrichment.fetch_formats_map(session, [book_id]).get(
                book_id, []
            )
            base = BookWithRelations(
                book=book,
                authors=authors,
                series=series_name,
                formats=formats,
            )
            self._enrich_base_books_for_list(session, [base])
            return base

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="get_book",
        )

    def get_book_full(self, *, book_id: int) -> BookWithFullRelations | None:
        """Get a book by ID with all related metadata for editing."""

        def _op(session: Session) -> BookWithFullRelations | None:
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

            book = self._unwrapper.unwrap_book(result)
            if book is None:
                return None

            series_name = self._unwrapper.unwrap_series_name(result)
            authors = self._fetch_author_names(session, book_id=book_id)
            formats = self._fetch_formats_for_book(session, book=book)
            base = BookWithRelations(
                book=book,
                authors=authors,
                series=series_name,
                formats=formats,
            )
            enriched = self._enrichment.enrich_books_with_full_details(session, [base])
            return enriched[0] if enriched else None

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="get_book_full",
        )

    def search_suggestions(
        self,
        *,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series."""
        if not query or not query.strip():
            return {"books": [], "authors": [], "tags": [], "series": []}

        def _op(session: Session) -> dict[str, list[dict[str, str | int]]]:
            return self._search_service.search_suggestions(
                session,
                query,
                book_limit,
                author_limit,
                tag_limit,
                series_limit,
            )

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="search_suggestions",
        )

    def filter_suggestions(
        self,
        *,
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

        def _op(session: Session) -> list[dict[str, str | int]]:
            return strategy.get_suggestions(session, query, limit)

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="filter_suggestions",
        )

    def get_library_stats(self) -> dict[str, int | float]:
        """Get library statistics."""

        def _op(session: Session) -> dict[str, int | float]:
            return self._statistics_service.get_statistics(session)

        return self._retry.run_read(
            self._session_manager.get_session,
            _op,
            operation_name="get_library_stats",
        )

    def _build_books_from_results(
        self, session: Session, results: Sequence[object]
    ) -> list[BookWithRelations]:
        books: list[BookWithRelations] = []
        for result in results:
            built = self._build_book_with_relations(session, result)
            if built is not None:
                books.append(built)
        return books

    def _enrich_base_books_for_list(
        self,
        session: Session,
        books: list[BookWithRelations],
    ) -> None:
        """Populate list-level metadata on BookWithRelations.

        Notes
        -----
        This is intentionally lighter than `enrich_books_with_full_details`:
        it adds only IDs + tag names needed for list UIs.
        """
        self._enrichment.enrich_books_for_list(session, books)

    def _build_book_with_relations(
        self, session: Session, result: object
    ) -> BookWithRelations | None:
        book = self._unwrapper.unwrap_book(result)
        if book is None or book.id is None:
            return None

        series_name = self._unwrapper.unwrap_series_name(result)
        authors = self._fetch_author_names(session, book_id=book.id)
        formats = self._fetch_formats_for_book(session, book=book)
        return BookWithRelations(
            book=book, authors=authors, series=series_name, formats=formats
        )

    def _fetch_author_names(self, session: Session, *, book_id: int) -> list[str]:
        authors_stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book_id)
            .order_by(BookAuthorLink.id)
        )
        author_rows = session.exec(authors_stmt).all()
        return [row[0] if isinstance(row, tuple) else row for row in author_rows]

    def _fetch_formats_for_book(
        self, session: Session, *, book: Book
    ) -> list[dict[str, str | int]]:
        formats_stmt = (
            select(Data.format, Data.uncompressed_size, Data.name)
            .where(Data.book == book.id)
            .order_by(Data.format)
        )

        # Determine library root path
        if self._calibre_db_path.is_dir():
            library_root = self._calibre_db_path
        else:
            library_root = self._calibre_db_path.parent

        book_dir = library_root / book.path

        results = []
        for fmt, size, name in session.exec(formats_stmt).all():
            # Validate file existence to avoid stale data
            exists = False
            format_lower = fmt.lower()

            # 1. Check with stored name
            file_name = name or f"{book.id}"
            candidate = book_dir / f"{file_name}.{format_lower}"
            if candidate.exists():
                exists = True

            # 2. Check with book ID
            if not exists:
                candidate = book_dir / f"{book.id}.{format_lower}"
                if candidate.exists():
                    exists = True

            # 3. Check directory scan
            if not exists and book_dir.exists():
                for file_in_dir in book_dir.iterdir():
                    if (
                        file_in_dir.is_file()
                        and file_in_dir.suffix.lower() == f".{format_lower}"
                    ):
                        exists = True
                        break

            if exists:
                results.append({"format": fmt, "size": size, "name": name or ""})

        return results

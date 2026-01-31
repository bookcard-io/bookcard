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

"""Calibre book repository facade.

This module keeps the public repository API small and delegates the heavy logic
to focused modules (reads, writes, formats, deletion, query building, etc.).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from bookcard.repositories.book_metadata_service import BookMetadataService
from bookcard.repositories.book_relationship_manager import BookRelationshipManager
from bookcard.repositories.book_search_service import BookSearchService
from bookcard.repositories.file_manager import CalibreFileManager
from bookcard.repositories.interfaces import (
    IBookMetadataService,
    IBookRelationshipManager,
    IBookRepository,
    IBookSearchService,
    IFileManager,
    ILibraryStatisticsService,
    ISessionManager,
)
from bookcard.repositories.library_statistics_service import LibraryStatisticsService
from bookcard.repositories.session_manager import CalibreSessionManager

from .deletion import BookDeletionOperations
from .enrichment import BookEnrichmentService
from .formats import BookFormatOperations
from .pathing import BookPathService
from .queries import BookQueryBuilder
from .reads import BookReadOperations
from .retry import SQLiteRetryPolicy
from .unwrapping import ResultUnwrapper
from .writes import BookWriteOperations

if TYPE_CHECKING:
    from collections.abc import Generator
    from datetime import datetime

    from sqlalchemy.sql.elements import ColumnElement
    from sqlmodel import Session

    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations


class CalibreBookRepository(IBookRepository):
    """Repository for querying and mutating a Calibre SQLite database.

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

        self._session_manager = session_manager or CalibreSessionManager(
            calibre_db_path, calibre_db_file
        )
        self._file_manager = file_manager or CalibreFileManager()
        self._relationship_manager = relationship_manager or BookRelationshipManager()
        self._metadata_service = metadata_service or BookMetadataService()
        self._search_service = search_service or BookSearchService()
        self._statistics_service = statistics_service or LibraryStatisticsService()

        self._retry = SQLiteRetryPolicy(max_retries=3)
        self._unwrapper = ResultUnwrapper()
        self._queries = BookQueryBuilder()
        self._enrichment = BookEnrichmentService(calibre_db_path=self._calibre_db_path)
        self._pathing = BookPathService()

        self._reads = BookReadOperations(
            session_manager=self._session_manager,
            retry_policy=self._retry,
            unwrapper=self._unwrapper,
            queries=self._queries,
            enrichment=self._enrichment,
            search_service=self._search_service,
            statistics_service=self._statistics_service,
            pathing=self._pathing,
            calibre_db_path=self._calibre_db_path,
        )
        self._formats = BookFormatOperations(
            session_manager=self._session_manager,
            retry_policy=self._retry,
            file_manager=self._file_manager,
            pathing=self._pathing,
            calibre_db_path=self._calibre_db_path,
        )
        self._deletion = BookDeletionOperations(
            session_manager=self._session_manager,
            retry_policy=self._retry,
            file_manager=self._file_manager,
        )
        self._writes = BookWriteOperations(
            session_manager=self._session_manager,
            retry_policy=self._retry,
            file_manager=self._file_manager,
            relationship_manager=self._relationship_manager,
            metadata_service=self._metadata_service,
            pathing=self._pathing,
            calibre_db_path=self._calibre_db_path,
            get_book_full=self.get_book_full,
        )

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

    def get_library_path(self) -> Path:
        """Get library root path from `calibre_db_path`.

        Returns
        -------
        Path
            Library root path.
        """
        if self._calibre_db_path.is_dir():
            return self._calibre_db_path
        return self._calibre_db_path.parent

    def count_books(
        self,
        search_query: str | None = None,
        author_id: int | None = None,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> int:
        """Count total number of books, optionally filtered by search."""
        return self._reads.count_books(
            search_query=search_query,
            author_id=author_id,
            pubdate_month=pubdate_month,
            pubdate_day=pubdate_day,
        )

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
        return self._reads.list_books(
            limit=limit,
            offset=offset,
            search_query=search_query,
            author_id=author_id,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
            pubdate_month=pubdate_month,
            pubdate_day=pubdate_day,
        )

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
        return self._reads.list_books_with_filters(
            limit=limit,
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
            full=full,
        )

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
        return self._reads.count_books_with_filters(
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

    def list_books_by_filter(
        self,
        filter_expression: ColumnElement[bool],
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """List books matching a custom SQLAlchemy filter expression."""
        return self._reads.list_books_by_filter(
            filter_expression=filter_expression,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
        )

    def count_books_by_filter(
        self,
        filter_expression: ColumnElement[bool],
    ) -> int:
        """Count books matching a custom SQLAlchemy filter expression."""
        return self._reads.count_books_by_filter(
            filter_expression=filter_expression,
        )

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Get a book by ID."""
        return self._reads.get_book(book_id=book_id)

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Get a book by ID with all related metadata for editing."""
        return self._reads.get_book_full(book_id=book_id)

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
        author_sort: str | None = None,
        title_sort: str | None = None,
    ) -> BookWithFullRelations | None:
        """Update book metadata."""
        return self._writes.update_book(
            book_id=book_id,
            title=title,
            pubdate=pubdate,
            author_names=author_names,
            series_name=series_name,
            series_id=series_id,
            series_index=series_index,
            tag_names=tag_names,
            identifiers=identifiers,
            description=description,
            publisher_name=publisher_name,
            publisher_id=publisher_id,
            language_codes=language_codes,
            language_ids=language_ids,
            rating_value=rating_value,
            rating_id=rating_id,
            author_sort=author_sort,
            title_sort=title_sort,
        )

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
        return self._writes.add_book(
            file_path=file_path,
            file_format=file_format,
            title=title,
            author_name=author_name,
            pubdate=pubdate,
            library_path=library_path,
        )

    def add_format(
        self,
        book_id: int,
        file_path: Path,
        file_format: str,
        replace: bool = False,
    ) -> None:
        """Add a format to an existing book."""
        self._formats.add_format(
            book_id=book_id,
            file_path=file_path,
            file_format=file_format,
            replace=replace,
        )

    def delete_format(
        self,
        book_id: int,
        file_format: str,
        delete_file_from_drive: bool = True,
    ) -> None:
        """Delete a format from an existing book."""
        self._formats.delete_format(
            book_id=book_id,
            file_format=file_format,
            delete_file_from_drive=delete_file_from_drive,
        )

    def delete_book(
        self,
        book_id: int,
        delete_files_from_drive: bool = False,
        library_path: Path | None = None,
    ) -> None:
        """Delete a book and all its related data."""
        self._deletion.delete_book(
            book_id=book_id,
            delete_files_from_drive=delete_files_from_drive,
            library_path=library_path,
        )

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series."""
        return self._reads.search_suggestions(
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
        """Get filter suggestions for a specific filter type."""
        return self._reads.filter_suggestions(
            query=query,
            filter_type=filter_type,
            limit=limit,
        )

    def get_library_stats(self) -> dict[str, int | float]:
        """Get library statistics."""
        return self._reads.get_library_stats()

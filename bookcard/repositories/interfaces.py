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

"""Interfaces for Calibre repository components.

This module defines abstract interfaces following the Interface Segregation
Principle (ISP) and Dependency Inversion Principle (DIP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from datetime import datetime
    from pathlib import Path

    from sqlmodel import Session
    from sqlmodel.sql.expression import SelectOfScalar

    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
    from bookcard.services.book_metadata import BookMetadata


class ISessionManager(ABC):
    """Interface for database session management."""

    @abstractmethod
    def get_session(self) -> AbstractContextManager[Session]:
        """Get a database session context manager.

        Returns
        -------
        AbstractContextManager[Session]
            Context manager that yields a SQLModel session.
        """
        ...

    @abstractmethod
    def dispose(self) -> None:
        """Dispose of the database engine and close all connections."""
        ...


class IFileManager(ABC):
    """Interface for filesystem operations."""

    @abstractmethod
    def save_book_file(
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
        file_path : "Path"
            Source file path (temporary location).
        library_path : "Path"
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).
        title_dir : str
            Sanitized title directory name.
        file_format : str
            File format extension.
        """
        ...

    @abstractmethod
    def save_book_cover(
        self,
        cover_data: bytes,
        library_path: Path,
        book_path_str: str,
    ) -> bool:
        """Save book cover image to library directory structure.

        Parameters
        ----------
        cover_data : bytes
            Cover image data as bytes.
        library_path : "Path"
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).

        Returns
        -------
        bool
            True if cover was saved successfully, False otherwise.
        """
        ...

    @abstractmethod
    def collect_book_files(
        self,
        session: Session,
        book_id: int,
        book_path: str,
        library_path: Path,
    ) -> tuple[list[Path], Path | None]:
        """Collect filesystem paths for book files.

        Parameters
        ----------
        session : Session
            Database session for querying Data records.
        book_id : int
            Calibre book ID.
        book_path : str
            Book path string from database.
        library_path : "Path"
            Library root path.

        Returns
        -------
        tuple[list[Path], Path | None]
            Tuple of (list of file paths, book directory path).
        """
        ...

    @abstractmethod
    def move_book_directory(
        self,
        old_book_path: str,
        new_book_path: str,
        library_path: Path,
    ) -> None:
        """Move book directory and all its contents to a new location.

        Moves all files in the book directory including:
        - All book format files (epub, pdf, mobi, etc.)
        - Companion files (cover.jpg, metadata.opf, etc.)
        - Any other files in the directory

        After moving, cleans up empty directories.

        Parameters
        ----------
        old_book_path : str
            Current book path string (Author/Title format).
        new_book_path : str
            New book path string (Author/Title format).
        library_path : "Path"
            Library root path.

        Raises
        ------
        OSError
            If filesystem operations fail.
        """
        ...


class IBookRelationshipManager(ABC):
    """Interface for managing book relationships."""

    @abstractmethod
    def update_authors(
        self,
        session: Session,
        book_id: int,
        author_names: list[str],
    ) -> None:
        """Update book authors.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        author_names : list[str]
            List of author names to set (replaces existing).
        """
        ...

    @abstractmethod
    def update_series(
        self,
        session: Session,
        book_id: int,
        series_name: str | None = None,
        series_id: int | None = None,
    ) -> None:
        """Update book series.

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
        ...

    @abstractmethod
    def update_tags(
        self,
        session: Session,
        book_id: int,
        tag_names: list[str],
    ) -> None:
        """Update book tags.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        tag_names : list[str]
            List of tag names to set (replaces existing).
        """
        ...

    @abstractmethod
    def update_identifiers(
        self,
        session: Session,
        book_id: int,
        identifiers: list[dict[str, str]],
    ) -> None:
        """Update book identifiers.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        identifiers : list[dict[str, str]]
            List of identifiers with 'type' and 'val' keys (replaces existing).
        """
        ...

    @abstractmethod
    def update_publisher(
        self,
        session: Session,
        book_id: int,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
    ) -> None:
        """Update book publisher.

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
        ...

    @abstractmethod
    def update_languages(
        self,
        session: Session,
        book_id: int,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
    ) -> None:
        """Update book languages.

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
        ...

    @abstractmethod
    def update_rating(
        self,
        session: Session,
        book_id: int,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        """Update book rating.

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
        ...

    @abstractmethod
    def add_metadata(
        self,
        session: Session,
        book_id: int,
        metadata: BookMetadata,
    ) -> None:
        """Add all metadata relationships to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        metadata : BookMetadata
            Extracted book metadata.
        """
        ...


class IBookMetadataService(ABC):
    """Interface for metadata extraction and management."""

    @abstractmethod
    def extract_metadata(
        self,
        file_path: Path,
        file_format: str,
    ) -> tuple[BookMetadata, bytes | None]:
        """Extract metadata and cover art from book file.

        Parameters
        ----------
        file_path : "Path"
            Path to the book file.
        file_format : str
            File format extension.

        Returns
        -------
        tuple[BookMetadata, bytes | None]
            Tuple of (BookMetadata, cover_data).
        """
        ...


class IBookSearchService(ABC):
    """Interface for book search functionality."""

    @abstractmethod
    def search_suggestions(
        self,
        session: Session,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series.

        Parameters
        ----------
        session : Session
            Database session.
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
        ...


class ILibraryStatisticsService(ABC):
    """Interface for library statistics."""

    @abstractmethod
    def get_statistics(self, session: Session) -> dict[str, int | float]:
        """Get library statistics.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        dict[str, int | float]
            Dictionary with statistics keys:
            - 'total_books': Total number of books
            - 'total_series': Total number of unique series
            - 'total_authors': Total number of unique authors
            - 'total_tags': Total number of unique tags
            - 'total_ratings': Total number of books with ratings
            - 'total_content_size': Total file size in bytes
        """
        ...


class IBookRepository(ABC):
    """Interface for book repository operations."""

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        """List books with pagination and optional search.

        Parameters
        ----------
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
        search_query : str | None
            Optional search query to filter by title or author.
        author_id : int | None
            Optional author ID to filter by.
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').
        full : bool
            If True, return full book details with all metadata (default: False).
        pubdate_month : int | None
            Optional month (1-12) to filter books by publication date month.
        pubdate_day : int | None
            Optional day (1-31) to filter books by publication date day.

        Returns
        -------
        list[BookWithRelations | BookWithFullRelations]
            List of books with authors and series. If full=True, includes all metadata.
        """
        ...

    @abstractmethod
    def count_books(
        self,
        search_query: str | None = None,
        author_id: int | None = None,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> int:
        """Count total number of books, optionally filtered by search.

        Parameters
        ----------
        search_query : str | None
            Optional search query to filter by title, author, or tag.
        author_id : int | None
            Optional author ID to filter by.
        pubdate_month : int | None
            Optional month (1-12) to filter books by publication date month.
        pubdate_day : int | None
            Optional day (1-31) to filter books by publication date day.

        Returns
        -------
        int
            Total number of books.
        """
        ...

    @abstractmethod
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
        """List books with multiple filter criteria.

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
        full : bool
            If True, return full book details with all metadata (default: False).

        Returns
        -------
        list[BookWithRelations | BookWithFullRelations]
            List of books with authors and series. If full=True, includes all metadata.
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def list_books_by_ids_query(
        self,
        book_ids_query: SelectOfScalar[int],
        *,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """List books whose IDs are returned by a query.

        Parameters
        ----------
        book_ids_query : SelectOfScalar[int]
            Statement returning the matching `Book.id` values.
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
        sort_by : str
            Field to sort by.
        sort_order : str
            Sort order ('asc' or 'desc').
        full : bool
            If True, return full book details with all metadata.

        Returns
        -------
        list[BookWithRelations | BookWithFullRelations]
            List of books matching the query.
        """
        ...

    @abstractmethod
    def count_books_by_ids_query(self, book_ids_query: SelectOfScalar[int]) -> int:
        """Count books whose IDs are returned by a query.

        Parameters
        ----------
        book_ids_query : SelectOfScalar[int]
            Statement returning the matching `Book.id` values.

        Returns
        -------
        int
            Total number of matching books.
        """
        ...

    @abstractmethod
    def update_book(
        self,
        book_id: int,
        title: str | None = None,
        pubdate: datetime | None = None,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        series_index: float | None = None,
        isbn: str | None = None,
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
        """Update book metadata.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        title : str | None
            Book title to update.
        pubdate : "datetime | None"
            Publication date to update.
        author_names : list[str] | None
            List of author names to set (replaces existing).
        series_name : str | None
            Series name to set (creates if doesn't exist).
        series_id : int | None
            Series ID to set (if provided, series_name is ignored).
        series_index : float | None
            Series index to update.
        isbn : str | None
            ISBN identifier to set (first-class field).
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
        author_sort : str | None
            Author sort value to set.
        title_sort : str | None
            Title sort value to set.

        Returns
        -------
        BookWithFullRelations | None
            Updated book with all relations if found, None otherwise.
        """
        ...

    @abstractmethod
    def add_book(
        self,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        pubdate: datetime | None = None,
        library_path: Path | None = None,
    ) -> int:
        """Add a book directly to the Calibre database.

        Parameters
        ----------
        file_path : "Path"
            Path to the uploaded book file (temporary location).
        file_format : str
            File format extension (e.g., 'epub', 'pdf', 'mobi').
        title : str | None
            Book title. If None, uses filename without extension.
        author_name : str | None
            Author name. If None, uses 'Unknown'.
        pubdate : datetime | None
            Publication date override. If None, uses publication date extracted
            from file metadata (if available).
        library_path : "Path" | None
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
        ...

    @abstractmethod
    def delete_book(
        self,
        book_id: int,
        delete_files_from_drive: bool = False,
        library_path: Path | None = None,
    ) -> None:
        """Delete a book and all its related data.

        Parameters
        ----------
        book_id : int
            Calibre book ID to delete.
        delete_files_from_drive : bool
            If True, also delete files from filesystem (default: False).
        library_path : "Path" | None
            Library root path for filesystem operations.
            If None, uses calibre_db_path.

        Raises
        ------
        ValueError
            If book not found.
        OSError
            If filesystem operations fail (only if delete_files_from_drive is True).
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def get_library_stats(self) -> dict[str, int | float]:
        """Get library statistics.

        Returns
        -------
        dict[str, int | float]
            Dictionary with statistics keys.
        """
        ...

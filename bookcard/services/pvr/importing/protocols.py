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

"""Protocols for PVR import service."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from bookcard.models.config import Library
from bookcard.services.ingest.file_discovery_service import FileGroup

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.models import BookWithRelations


class SessionFactory(Protocol):
    """Factory for creating database sessions."""

    @contextmanager
    def create_session(self) -> Iterator["Session"]:
        """Create a new session context."""
        ...


class MetricsRecorder(Protocol):
    """Protocol for recording metrics."""

    def increment(
        self, metric: str, value: int = 1, tags: dict[str, Any] | None = None
    ) -> None:
        """Increment a counter metric."""
        ...

    def timing(
        self, metric: str, value: float, tags: dict[str, Any] | None = None
    ) -> None:
        """Record a timing metric."""
        ...


class LibraryProtocol(Protocol):
    """Protocol for library objects."""

    id: int | None
    name: str
    calibre_db_path: str
    library_root: str | None


# Use forward references for types not available at runtime or to avoid circular imports
class BookServiceProtocol(Protocol):
    """Protocol for BookService (minimal for typing)."""

    @property
    def library(self) -> LibraryProtocol:
        """
        Get the active library configuration.

        Returns
        -------
        LibraryProtocol
            The active library configuration object.
        """
        ...

    def get_book(self, book_id: int) -> "BookWithRelations | None":
        """
        Get a book by ID.

        Parameters
        ----------
        book_id : int
            The ID of the book to retrieve.

        Returns
        -------
        BookWithRelations | None
            The book with its relations if found, None otherwise.
        """
        ...

    def get_format_file_path(self, book_id: int, file_format: str) -> Path:
        """
        Get file path for a book format.

        Parameters
        ----------
        book_id : int
            The ID of the book.
        file_format : str
            The format of the file (e.g., 'epub', 'mobi').

        Returns
        -------
        Path
            The absolute path to the book file.
        """
        ...


class BookServiceFactory(Protocol):
    """Factory for creating book services."""

    def create(self, library: Library) -> BookServiceProtocol:
        """
        Create book service for library.

        Parameters
        ----------
        library : Library
            The library to create service for.

        Returns
        -------
        BookServiceProtocol
            The created book service.
        """
        ...


class IngestServiceProtocol(Protocol):
    """Protocol for IngestProcessorService."""

    def process_file_group(
        self,
        file_group: FileGroup,
        user_id: int | None = None,
    ) -> int:
        """
        Process a file group.

        Parameters
        ----------
        file_group : FileGroup
            The group of files to process.
        user_id : int | None, optional
            The ID of the user initiating the process, by default None.

        Returns
        -------
        int
            The ID of the created history record.
        """
        ...

    def fetch_and_store_metadata(
        self,
        history_id: int,
        metadata_hint: dict | None = None,
    ) -> dict | None:
        """
        Fetch and store metadata.

        Parameters
        ----------
        history_id : int
            The ID of the history record.
        metadata_hint : dict | None, optional
            Optional metadata hints to assist fetching, by default None.

        Returns
        -------
        dict | None
            The fetched metadata dictionary if successful, None otherwise.
        """
        ...

    def add_book_to_library(
        self,
        history_id: int,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        pubdate: datetime | None = None,
    ) -> int:
        """
        Add book to library.

        Parameters
        ----------
        history_id : int
            The ID of the history record.
        file_path : Path
            The path to the book file.
        file_format : str
            The format of the book file.
        title : str | None, optional
            The title of the book, by default None.
        author_name : str | None, optional
            The name of the author, by default None.
        pubdate : datetime | None, optional
            The publication date, by default None.

        Returns
        -------
        int
            The ID of the added book.
        """
        ...

    def add_format_to_book(
        self,
        book_id: int,
        file_path: Path,
        file_format: str,
    ) -> None:
        """
        Add format to book.

        Parameters
        ----------
        book_id : int
            The ID of the book.
        file_path : Path
            The path to the file to add.
        file_format : str
            The format of the file.
        """
        ...

    def finalize_history(
        self,
        history_id: int,
        book_ids: list[int],
    ) -> None:
        """
        Finalize history.

        Parameters
        ----------
        history_id : int
            The ID of the history record.
        book_ids : list[int]
            List of book IDs associated with this history.
        """
        ...

    def get_active_library(self) -> Library:
        """
        Get active library.

        Returns
        -------
        Library
            The active library configuration.
        """
        ...

    def create_book_service(self, library: Library) -> BookServiceProtocol:
        """
        Create book service.

        Parameters
        ----------
        library : Library
            The library configuration to create the service for.

        Returns
        -------
        BookServiceProtocol
            An instance of the book service.
        """
        ...


class TrackedBookServiceProtocol(Protocol):
    """Protocol for TrackedBookService."""

    # Add methods if needed by PVRImportService


class FileDiscoveryProtocol(Protocol):
    """Protocol for FileDiscoveryService."""

    def discover_files(self, ingest_dir: Path) -> list[Path]:
        """
        Discover files in directory.

        Parameters
        ----------
        ingest_dir : Path
            The directory to search for files.

        Returns
        -------
        list[Path]
            A list of discovered file paths.
        """
        ...

    def group_files_by_directory(self, files: list[Path]) -> list[FileGroup]:
        """
        Group files by directory.

        Parameters
        ----------
        files : list[Path]
            The list of files to group.

        Returns
        -------
        list[FileGroup]
            A list of file groups organized by directory.
        """
        ...

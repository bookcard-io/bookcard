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

"""Post-ingest processors for book upload tasks.

Follows Open/Closed Principle - new format processors can be added
without modifying existing code.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from sqlmodel import Session, select

from fundamental.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from fundamental.models.core import Book
from fundamental.models.media import Data

logger = logging.getLogger(__name__)


class PostIngestProcessor(ABC):
    """Abstract base class for post-ingest processors.

    Follows Open/Closed Principle - new format processors can be added
    by implementing this interface without modifying existing code.
    """

    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        """Check if this processor supports the given file format.

        Parameters
        ----------
        file_format : str
            File format to check (e.g., 'epub', 'mobi').

        Returns
        -------
        bool
            True if this processor can handle the format.
        """
        ...

    @abstractmethod
    def process(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,
        user_id: int,
    ) -> None:
        """Process a book after ingestion.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Library
            Library configuration.
        user_id : int
            User ID who triggered the upload.

        Raises
        ------
        Exception
            If processing fails. Exceptions should be caught by caller
            to prevent failing the upload.
        """
        ...


class EPUBAutoFixPolicy:
    """Policy for determining if EPUB auto-fix should run.

    Follows Single Responsibility Principle by handling only
    configuration checking logic.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize EPUB auto-fix policy.

        Parameters
        ----------
        session : Session
            Database session for querying configuration.
        """
        self._session = session

    def should_auto_fix(self) -> bool:
        """Check if EPUB auto-fix on ingest is enabled.

        Returns
        -------
        bool
            True if auto-fix should run, False otherwise.
        """
        # Check if auto-fix on ingest is enabled
        stmt = select(ScheduledTasksConfig).limit(1)
        scheduled_config = self._session.exec(stmt).first()
        if (
            scheduled_config is None
            or not scheduled_config.epub_fixer_auto_fix_on_ingest
        ):
            logger.debug("EPUB auto-fix on ingest is disabled")
            return False

        # Check if EPUB fixer is enabled
        stmt = select(EPUBFixerConfig).limit(1)
        epub_config = self._session.exec(stmt).first()
        if not epub_config or not epub_config.enabled:
            logger.debug("EPUB fixer is disabled")
            return False

        return True


class LibraryPathResolver:
    """Service for resolving file paths within a library.

    Follows Single Responsibility Principle by handling only
    file path resolution logic.
    """

    def __init__(self, library: Library) -> None:
        """Initialize library path resolver.

        Parameters
        ----------
        library : Library
            Library configuration object.
        """
        self._library = library

    def get_library_root(self) -> Path:
        """Get library root directory path.

        Returns
        -------
        Path
            Path to library root directory.
        """
        from fundamental.services.epub_fixer.services.library import LibraryLocator

        locator = LibraryLocator(self._library)
        return locator.get_location()

    def get_book_file_path(
        self,
        book: Book,
        data: Data,
    ) -> Path | None:
        """Get file path for a book format.

        Parameters
        ----------
        book : Book
            Book model.
        data : Data
            Data record for the format.

        Returns
        -------
        Path | None
            Path to the book file if found, None otherwise.
        """
        library_path = self.get_library_root()
        book_dir = library_path / book.path

        # Primary path: {name}.{format}
        file_name = data.name or str(book.id)
        primary = book_dir / f"{file_name}.{data.format.lower()}"
        if primary.exists():
            return primary

        # Alternative path: {book_id}.{format}
        alt = book_dir / f"{book.id}.{data.format.lower()}"
        if alt.exists():
            return alt

        logger.warning(
            "Book file not found at %s or %s for book_id=%d, format=%s",
            primary,
            alt,
            book.id,
            data.format,
        )
        return None


class EPUBPostIngestProcessor(PostIngestProcessor):
    """Post-ingest processor for EPUB files.

    Handles automatic EPUB fixing after book ingestion.
    Follows Single Responsibility Principle by focusing only on EPUB processing.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize EPUB post-ingest processor.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session
        self._policy = EPUBAutoFixPolicy(session)

    def supports_format(self, file_format: str) -> bool:
        """Check if this processor supports EPUB format.

        Parameters
        ----------
        file_format : str
            File format to check.

        Returns
        -------
        bool
            True if format is EPUB.
        """
        return file_format.lower() == "epub"

    def process(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,
        user_id: int,
    ) -> None:
        """Process EPUB file after ingestion.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Library
            Library configuration.
        user_id : int
            User ID who triggered the upload.

        Raises
        ------
        Exception
            If processing fails. Should be caught by caller.
        """
        # Check if auto-fix should run
        if not self._policy.should_auto_fix():
            return

        # Get book and EPUB data
        stmt = (
            select(Book, Data)
            .join(Data)
            .where(Book.id == book_id)
            .where(Data.format == "EPUB")
        )
        result = session.exec(stmt).first()
        if result is None:
            logger.debug("EPUB format not found for book %d", book_id)
            return

        book, data = result

        # Resolve file path
        path_resolver = LibraryPathResolver(library)
        file_path = path_resolver.get_book_file_path(book, data)
        if file_path is None:
            logger.warning("EPUB file not found for book_id=%d", book_id)
            return

        # Process EPUB file
        from fundamental.services.epub_fixer_service import EPUBFixerService

        fixer_service = EPUBFixerService(session)

        fix_run = fixer_service.process_epub_file(
            file_path=file_path,
            book_id=book_id,
            book_title=book.title,
            user_id=user_id,
            library_id=library.id if library else None,
            manually_triggered=False,  # Automatic, not manual
        )

        # Log results
        if fix_run.id is not None:
            fixes = fixer_service.get_fixes_for_run(fix_run.id)
            if fixes:
                logger.info(
                    "Auto-fixed EPUB on ingest: book_id=%d, file=%s, fixes_applied=%d",
                    book_id,
                    file_path,
                    len(fixes),
                )
            else:
                logger.debug("No fixes needed for EPUB on ingest: book_id=%d", book_id)

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

from fundamental.models.auth import UserSetting
from fundamental.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from fundamental.models.conversion import ConversionMethod
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


class ConversionAutoConvertPolicy:
    """Policy for determining if auto-conversion should run.

    Follows Single Responsibility Principle by handling only
    configuration checking logic.
    """

    def __init__(self, session: Session, user_id: int) -> None:  # type: ignore[type-arg]
        """Initialize conversion auto-convert policy.

        Parameters
        ----------
        session : Session
            Database session for querying user settings.
        user_id : int
            User ID to check settings for.
        """
        self._session = session
        self._user_id = user_id

    def should_auto_convert(self) -> bool:
        """Check if auto-convert on import is enabled for user.

        Returns
        -------
        bool
            True if auto-convert should run, False otherwise.
        """
        stmt = (
            select(UserSetting)
            .where(UserSetting.user_id == self._user_id)
            .where(UserSetting.key == "auto_convert_on_import")
        )
        setting = self._session.exec(stmt).first()
        if setting is None:
            logger.debug(
                "Auto-convert on import setting not found, defaulting to False"
            )
            return False

        return setting.value.lower() == "true"

    def get_target_format(self) -> str:
        """Get target format for conversion.

        Returns
        -------
        str
            Target format (default: "epub").
        """
        stmt = (
            select(UserSetting)
            .where(UserSetting.user_id == self._user_id)
            .where(UserSetting.key == "auto_convert_target_format")
        )
        setting = self._session.exec(stmt).first()
        if setting is None:
            return "epub"

        return setting.value.lower()

    def get_ignored_formats(self) -> list[str]:
        """Get list of ignored formats.

        Returns
        -------
        list[str]
            List of format strings to ignore.
        """
        stmt = (
            select(UserSetting)
            .where(UserSetting.user_id == self._user_id)
            .where(UserSetting.key == "auto_convert_ignored_formats")
        )
        setting = self._session.exec(stmt).first()
        if setting is None:
            return []

        # Parse JSON array or comma-separated string
        import json

        try:
            formats = json.loads(setting.value)
            if isinstance(formats, list):
                return [f.upper() for f in formats if isinstance(f, str)]
        except (json.JSONDecodeError, TypeError):
            # Fallback to comma-separated string
            if setting.value:
                return [
                    f.strip().upper() for f in setting.value.split(",") if f.strip()
                ]

        return []

    def should_backup_original(self) -> bool:
        """Check if original should be backed up.

        Returns
        -------
        bool
            True if backup is enabled, False otherwise.
        """
        stmt = (
            select(UserSetting)
            .where(UserSetting.user_id == self._user_id)
            .where(UserSetting.key == "auto_convert_backup_originals")
        )
        setting = self._session.exec(stmt).first()
        if setting is None:
            return True  # Default to backing up

        return setting.value.lower() == "true"


class ConversionPostIngestProcessor(PostIngestProcessor):
    """Post-ingest processor for automatic format conversion.

    Handles automatic format conversion after book ingestion.
    Follows Single Responsibility Principle by focusing only on conversion processing.
    """

    def __init__(self, session: Session, user_id: int) -> None:  # type: ignore[type-arg]
        """Initialize conversion post-ingest processor.

        Parameters
        ----------
        session : Session
            Database session.
        user_id : int
            User ID who triggered the upload.
        """
        self._session = session
        self._user_id = user_id
        self._policy = ConversionAutoConvertPolicy(session, user_id)

    def supports_format(self, _file_format: str) -> bool:
        """Check if this processor supports the given format.

        This processor supports all formats (it checks if conversion is needed).

        Parameters
        ----------
        _file_format : str
            File format to check (unused, processor supports all formats).

        Returns
        -------
        bool
            Always returns True (supports all formats).
        """
        return True

    def process(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,
        user_id: int,
    ) -> None:
        """Process book after ingestion for automatic conversion.

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
        # Check if auto-convert should run
        if not self._policy.should_auto_convert():
            logger.debug("Auto-convert on import is disabled for user %d", user_id)
            return

        # Get book and uploaded format
        stmt = select(Book).where(Book.id == book_id)
        book = session.exec(stmt).first()
        if book is None:
            logger.warning("Book %d not found for conversion", book_id)
            return

        # Get the format that was just uploaded (most recent)
        # Note: We'll get all formats and pick the one that matches the upload
        # For now, we'll get the first format (the one just added)
        stmt = select(Data).where(Data.book == book_id).limit(1)
        data = session.exec(stmt).first()
        if data is None:
            logger.warning("No format data found for book %d", book_id)
            return

        original_format = data.format.upper()
        target_format = self._policy.get_target_format().upper()
        ignored_formats = self._policy.get_ignored_formats()

        # Check if conversion is needed
        if original_format == target_format:
            logger.debug(
                "Book %d already in target format %s, skipping conversion",
                book_id,
                target_format,
            )
            return

        if original_format in ignored_formats:
            logger.debug(
                "Book %d format %s is in ignored formats, skipping conversion",
                book_id,
                original_format,
            )
            return

        # Check if target format already exists
        stmt = (
            select(Data).where(Data.book == book_id).where(Data.format == target_format)
        )
        if session.exec(stmt).first() is not None:
            logger.debug(
                "Book %d already has target format %s, skipping conversion",
                book_id,
                target_format,
            )
            return

        # Perform conversion
        try:
            from fundamental.services.conversion_service import ConversionService

            conversion_service = ConversionService(session, library)
            backup_original = self._policy.should_backup_original()

            conversion_service.convert_book(
                book_id=book_id,
                original_format=original_format,
                target_format=target_format,
                user_id=user_id,
                conversion_method=ConversionMethod.AUTO_IMPORT,
                backup_original=backup_original,
            )

            logger.info(
                "Auto-converted book %d from %s to %s on import",
                book_id,
                original_format,
                target_format,
            )
        except (ValueError, OSError, RuntimeError) as e:
            # Log error but don't fail the upload
            # Catch specific exceptions: ValueError (validation), OSError (file ops),
            # RuntimeError (conversion failures)
            logger.warning(
                "Failed to auto-convert book %d from %s to %s: %s",
                book_id,
                original_format,
                target_format,
                e,
                exc_info=True,
            )

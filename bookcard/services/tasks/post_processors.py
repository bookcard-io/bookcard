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

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.auth import UserSetting
from bookcard.models.config import EPUBFixerConfig, Library
from bookcard.models.conversion import ConversionMethod
from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.repositories import CalibreBookRepository

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
        user_id: int | None = None,
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
        user_id : int | None
            User ID who triggered the upload (None for library-level auto-ingest).

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

    def __init__(
        self,
        session: Session,
        library: Library | None,  # type: ignore[type-arg]
    ) -> None:
        """Initialize EPUB auto-fix policy.

        Parameters
        ----------
        session : Session
            Database session for querying configuration.
        library : Library | None
            Library configuration to check for auto-fix settings.
        """
        self._session = session
        self._library = library

    def should_auto_fix(self) -> bool:
        """Check if EPUB auto-fix on ingest is enabled.

        Returns
        -------
        bool
            True if auto-fix should run, False otherwise.
        """
        # Check if library is provided
        if self._library is None:
            logger.debug("EPUB auto-fix on ingest: library is None")
            return False

        # Check if auto-fix on ingest is enabled for this library
        if not self._library.epub_fixer_auto_fix_on_ingest:
            logger.debug(
                "EPUB auto-fix on ingest is disabled for library %d", self._library.id
            )
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
        from bookcard.services.epub_fixer.services.library import LibraryLocator

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
        library: Library | None,
        user_id: int | None = None,
    ) -> None:
        """Process EPUB file after ingestion.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Library | None
            Library configuration (None if not available).
        user_id : int | None
            User ID who triggered the upload (None for library-level auto-ingest).

        Raises
        ------
        Exception
            If processing fails. Should be caught by caller.
        """
        # Check if auto-fix should run
        policy = EPUBAutoFixPolicy(session, library)
        if not policy.should_auto_fix():
            return

        # Get book and EPUB data
        # We need to query the Calibre database, not the application database
        if library is None:
            logger.warning(
                "Cannot resolve EPUB file path: library is None for book_id=%d", book_id
            )
            return

        calibre_repo = CalibreBookRepository(str(library.calibre_db_path))
        with calibre_repo.get_session() as calibre_session:
            stmt = (
                select(Book, Data)
                .join(Data)
                .where(Book.id == book_id)
                .where(Data.format == "EPUB")
            )
            result = calibre_session.exec(stmt).first()

        if result is None:
            logger.debug("EPUB format not found for book %d", book_id)
            return

        book, data = result

        # Resolve file path (requires library)
        path_resolver = LibraryPathResolver(library)
        file_path = path_resolver.get_book_file_path(book, data)
        if file_path is None:
            logger.warning("EPUB file not found for book_id=%d", book_id)
            return

        # Process EPUB file
        from bookcard.services.epub_fixer_service import EPUBFixerService

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
    """Policy for determining if auto-conversion should run (user-level).

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


class LibraryConversionAutoConvertPolicy:
    """Policy for determining if auto-conversion should run (library-level).

    Follows Single Responsibility Principle by handling only
    configuration checking logic for library-level auto-convert settings.
    """

    def __init__(self, library: Library) -> None:
        """Initialize library-level conversion auto-convert policy.

        Parameters
        ----------
        library : Library
            Library configuration to check settings for.
        """
        self._library = library

    def should_auto_convert(self) -> bool:
        """Check if auto-convert on ingest is enabled for library.

        Returns
        -------
        bool
            True if auto-convert should run, False otherwise.
        """
        return self._library.auto_convert_on_ingest

    def get_target_format(self) -> str:
        """Get target format for conversion.

        Returns
        -------
        str
            Target format (default: "epub").
        """
        if self._library.auto_convert_target_format:
            return self._library.auto_convert_target_format.lower()
        return "epub"

    def get_ignored_formats(self) -> list[str]:
        """Get list of ignored formats.

        Returns
        -------
        list[str]
            List of format strings to ignore.
        """
        if not self._library.auto_convert_ignored_formats:
            return []

        # Parse JSON array or comma-separated string
        import json

        try:
            formats = json.loads(self._library.auto_convert_ignored_formats)
            if isinstance(formats, list):
                return [f.upper() for f in formats if isinstance(f, str)]
        except (json.JSONDecodeError, TypeError):
            # Fallback to comma-separated string
            if self._library.auto_convert_ignored_formats:
                return [
                    f.strip().upper()
                    for f in self._library.auto_convert_ignored_formats.split(",")
                    if f.strip()
                ]

        return []

    def should_backup_original(self) -> bool:
        """Check if original should be backed up.

        Returns
        -------
        bool
            True if backup is enabled, False otherwise.
        """
        return self._library.auto_convert_backup_originals


class ConversionPostIngestProcessor(PostIngestProcessor):
    """Post-ingest processor for automatic format conversion.

    Handles automatic format conversion after book ingestion.
    Supports both user-level (for manual uploads) and library-level
    (for auto-ingest) conversion policies.
    Follows Single Responsibility Principle by focusing only on conversion processing.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        user_id: int | None = None,
        library: Library | None = None,
    ) -> None:
        """Initialize conversion post-ingest processor.

        Parameters
        ----------
        session : Session
            Database session.
        user_id : int | None
            User ID who triggered the upload (for user-level policy).
            Required if library is None.
        library : Library | None
            Library configuration (for library-level policy).
            If provided, library-level policy is used; otherwise user-level.
        """
        self._session = session
        self._user_id = user_id
        self._library = library

        # Use library-level policy if library is provided, otherwise user-level
        if library is not None:
            self._policy = LibraryConversionAutoConvertPolicy(library)
            self._policy_type = "library"
        elif user_id is not None:
            self._policy = ConversionAutoConvertPolicy(session, user_id)
            self._policy_type = "user"
        else:
            msg = "Either user_id or library must be provided"
            raise ValueError(msg)

        self._uploaded_format: str | None = None

    def supports_format(self, file_format: str) -> bool:
        """Check if this processor supports the given format.

        This processor supports all formats (it checks if conversion is needed).
        Stores the format for use in process().

        Parameters
        ----------
        file_format : str
            File format that was just uploaded.

        Returns
        -------
        bool
            Always returns True (supports all formats).
        """
        # Store the uploaded format for use in process()
        self._uploaded_format = file_format.upper()
        return True

    def process(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,
        user_id: int | None = None,
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
        user_id : int | None
            User ID who triggered the upload (None for library-level auto-ingest).

        Raises
        ------
        Exception
            If processing fails. Should be caught by caller.
        """
        # Check if auto-convert should run
        if not self._policy.should_auto_convert():
            self._log_auto_convert_disabled(library, user_id)
            return

        # Get original format
        # Use Calibre session for querying book data
        calibre_repo = CalibreBookRepository(str(library.calibre_db_path))
        with calibre_repo.get_session() as calibre_session:
            original_format = self._get_original_format(calibre_session, book_id)
            if original_format is None:
                return

            # Check if conversion is needed
            target_format = self._policy.get_target_format().upper()
            if not self._should_convert(
                calibre_session, book_id, original_format, target_format
            ):
                return

        # Perform conversion
        self._perform_conversion(
            session, book_id, library, original_format, target_format, user_id
        )

    def _log_auto_convert_disabled(self, library: Library, user_id: int | None) -> None:
        """Log that auto-convert is disabled.

        Parameters
        ----------
        library : Library
            Library configuration.
        user_id : int | None
            User ID (if user-level policy).
        """
        if self._policy_type == "library":
            logger.debug(
                "Auto-convert on ingest is disabled for library %d", library.id
            )
        else:
            logger.debug(
                "Auto-convert on import is disabled for user %d",
                user_id if user_id is not None else 0,
            )

    def _get_original_format(
        self,
        session: Session,
        book_id: int,  # type: ignore[type-arg]
    ) -> str | None:
        """Get the original format of the uploaded book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.

        Returns
        -------
        str | None
            Original format in uppercase, or None if not found.
        """
        if self._uploaded_format is None:
            # Fallback: query for all formats and use the first one
            logger.warning(
                "Uploaded format not available for book %d, querying formats",
                book_id,
            )
            try:
                # Use nested transaction to prevent session rollback on error
                with session.begin_nested():
                    stmt = select(Data).where(Data.book == book_id).limit(1)
                    data = session.exec(stmt).first()
                if data is None:
                    logger.warning("No format data found for book %d", book_id)
                    return None
                return data.format.upper()
            except SQLAlchemyError as e:
                logger.warning("Failed to query Data table for book %d: %s", book_id, e)
                return None

        # Query for the Data record matching the uploaded format
        stmt = (
            select(Data)
            .where(Data.book == book_id)
            .where(Data.format == self._uploaded_format)
        )
        try:
            # Use nested transaction to prevent session rollback on error
            with session.begin_nested():
                data = session.exec(stmt).first()
        except SQLAlchemyError as e:
            # Clean up logs: don't dump stack trace for expected schema errors
            logger.warning(
                "Failed to query Data table for book %d: %s (assuming uploaded format is correct)",
                book_id,
                e,
            )
            return self._uploaded_format

        if data is None:
            logger.warning(
                "Format %s not found for book %d",
                self._uploaded_format,
                book_id,
            )
            # If not found in DB but we know what we uploaded, return that
            return self._uploaded_format
        return self._uploaded_format

    def _should_convert(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        original_format: str,
        target_format: str,
    ) -> bool:
        """Check if conversion should be performed.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        original_format : str
            Original format in uppercase.
        target_format : str
            Target format in uppercase.

        Returns
        -------
        bool
            True if conversion should be performed, False otherwise.
        """
        # Check if already in target format
        if original_format == target_format:
            logger.debug(
                "Book %d already in target format %s, skipping conversion",
                book_id,
                target_format,
            )
            return False

        # Check if format is ignored
        ignored_formats = self._policy.get_ignored_formats()
        if original_format in ignored_formats:
            logger.debug(
                "Book %d format %s is in ignored formats, skipping conversion",
                book_id,
                original_format,
            )
            return False

        # Check if target format already exists
        # Check against 'data' table name, handle different naming in Calibre
        # The table name might be different or mapped differently in SQLModel
        stmt = (
            select(Data).where(Data.book == book_id).where(Data.format == target_format)
        )
        try:
            # Use nested transaction to prevent session rollback on error
            with session.begin_nested():
                if session.exec(stmt).first() is not None:
                    logger.debug(
                        "Book %d already has target format %s, skipping conversion",
                        book_id,
                        target_format,
                    )
                    return False
        except SQLAlchemyError as e:
            # If table check fails (e.g. table not found), assume format doesn't exist
            # This handles cases where Calibre schema might differ
            logger.warning(
                "Failed to check existing format for book %d: %s (assuming not present)",
                book_id,
                e,
            )

        return True

    def _perform_conversion(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,
        original_format: str,
        target_format: str,
        user_id: int | None,
    ) -> None:
        """Perform the actual conversion.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        library : Library
            Library configuration.
        original_format : str
            Original format in uppercase.
        target_format : str
            Target format in uppercase.
        user_id : int | None
            User ID (None for library-level auto-ingest).
        """
        try:
            from bookcard.services.conversion import create_conversion_service

            conversion_service = create_conversion_service(session, library)
            backup_original = self._policy.should_backup_original()

            conversion_service.convert_book(
                book_id=book_id,
                original_format=original_format,
                target_format=target_format,
                user_id=user_id,
                conversion_method=ConversionMethod.AUTO_IMPORT,
                backup_original=backup_original,
            )

            if self._policy_type == "library":
                logger.info(
                    "Auto-converted book %d from %s to %s on ingest (library-level)",
                    book_id,
                    original_format,
                    target_format,
                )
            else:
                logger.info(
                    "Auto-converted book %d from %s to %s on import (user-level)",
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

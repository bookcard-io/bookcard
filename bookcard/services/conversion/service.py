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

"""Book format conversion service.

Refactored to follow SOLID principles with clear separation of concerns:
- Orchestration only (high-level business logic)
- Dependency injection for all collaborators
- Strategy pattern for conversion execution
"""

import logging
import shutil
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from sqlmodel import Session

from bookcard.api.schemas.conversion import ConversionRequest
from bookcard.models.config import Library
from bookcard.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)
from bookcard.models.core import Book

if TYPE_CHECKING:
    from bookcard.models.kcc_config import KCCConversionProfile
from bookcard.services.conversion.backup import FileBackupService
from bookcard.services.conversion.book_repository import BookRepository
from bookcard.services.conversion.exceptions import (
    FormatNotFoundError,
)
from bookcard.services.conversion.repository import ConversionRepository
from bookcard.services.conversion.strategies.protocol import (
    ConversionStrategy,
)

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)


class ConversionService:
    """Service for converting book formats.

    Handles high-level orchestration of format conversion operations,
    delegating to specialized collaborators for specific responsibilities.

    Parameters
    ----------
    session : Session
        Database session.
    library : Library
        Library configuration.
    book_repository : BookRepository
        Repository for accessing book data.
    conversion_repository : ConversionRepository
        Repository for managing conversion records.
    conversion_strategy : ConversionStrategy
        Strategy for executing conversions.
    backup_service : FileBackupService | None
        Optional service for backing up original files.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library: Library,
        book_repository: BookRepository,
        conversion_repository: ConversionRepository,
        conversion_strategy: ConversionStrategy,
        backup_service: FileBackupService | None = None,
    ) -> None:
        """Initialize conversion service.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        book_repository : BookRepository
            Repository for accessing book data.
        conversion_repository : ConversionRepository
            Repository for managing conversion records.
        conversion_strategy : ConversionStrategy
            Strategy for executing conversions.
        backup_service : FileBackupService | None
            Optional service for backing up original files.
        """
        self._session = session
        self._library = library
        self._book_repository = book_repository
        self._conversion_repository = conversion_repository
        self._conversion_strategy = conversion_strategy
        self._backup_service = backup_service or FileBackupService()

    @property
    def _library_root(self) -> Path:
        """Resolve the library root path.

        Returns
        -------
        Path
            Library root path.
        """
        if self._library.library_root:
            return Path(self._library.library_root)
        return Path(self._library.calibre_db_path)

    def check_existing_conversion(
        self,
        book_id: int,
        original_format: str,
        target_format: str,
    ) -> BookConversion | None:
        """Check if a conversion already exists.

        Parameters
        ----------
        book_id : int
            Book ID.
        original_format : str
            Source format.
        target_format : str
            Target format.

        Returns
        -------
        BookConversion | None
            Existing conversion if found, None otherwise.
        """
        original_format_upper = self._normalize_format(original_format)
        target_format_upper = self._normalize_format(target_format)

        return self._conversion_repository.find_existing(
            book_id=book_id,
            original_format=original_format_upper,
            target_format=target_format_upper,
            status=ConversionStatus.COMPLETED,
        )

    def convert_book(
        self,
        book_id: int,
        original_format: str,
        target_format: str,
        user_id: int | None = None,
        conversion_method: ConversionMethod = ConversionMethod.MANUAL,
        backup_original: bool = True,
    ) -> BookConversion:
        """Convert a book from one format to another.

        Parameters
        ----------
        book_id : int
            Book ID to convert.
        original_format : str
            Source format (e.g., "MOBI", "AZW3").
        target_format : str
            Target format (e.g., "EPUB", "KEPUB").
        user_id : int | None
            User ID who triggered the conversion (None for automatic).
        conversion_method : ConversionMethod
            How conversion was triggered.
        backup_original : bool
            Whether to backup original file before conversion.

        Returns
        -------
        BookConversion
            Conversion record with status and file paths.

        Raises
        ------
        BookNotFoundError
            If book not found.
        FormatNotFoundError
            If source format not found.
        ConverterNotAvailableError
            If converter not available.
        ConversionError
            If conversion fails.
        """
        # Normalize formats
        original_format_upper = self._normalize_format(original_format)
        target_format_upper = self._normalize_format(target_format)

        # Check for existing conversion
        existing = self.check_existing_conversion(
            book_id, original_format_upper, target_format_upper
        )
        if existing:
            logger.info(
                "Conversion already exists: book_id=%d, %s -> %s",
                book_id,
                original_format_upper,
                target_format_upper,
            )
            return existing

        # Validate conversion request
        request = self._validate_conversion_request(
            book_id, original_format_upper, target_format_upper
        )

        # Check if target format already exists
        if self._book_repository.format_exists(book_id, target_format_upper):
            logger.info(
                "Target format %s already exists for book_id=%d",
                target_format_upper,
                book_id,
            )
            return self._record_existing_format(
                request,
                user_id,
                conversion_method,
            )

        # Perform conversion
        return self._perform_conversion(
            request,
            user_id,
            conversion_method,
            backup_original,
        )

    def _normalize_format(self, format_name: str) -> str:
        """Normalize format string.

        Parameters
        ----------
        format_name : str
            Format string.

        Returns
        -------
        str
            Normalized format (uppercase, no leading dot).
        """
        return format_name.upper().lstrip(".")

    def _validate_conversion_request(
        self,
        book_id: int,
        original_format: str,
        target_format: str,
    ) -> "ConversionRequest":
        """Validate conversion request and get book.

        Parameters
        ----------
        book_id : int
            Book ID.
        original_format : str
            Source format.
        target_format : str
            Target format.

        Returns
        -------
        ConversionRequest
            Validated conversion request.

        Raises
        ------
        BookNotFoundError
            If book not found.
        FormatNotFoundError
            If source format not found.
        """
        # Get book (raises BookNotFoundError if not found)
        book = self._book_repository.get_book(book_id)

        # Verify source format exists
        original_file_path = self._book_repository.get_book_file_path(
            book, book_id, original_format, self._library_root
        )
        if original_file_path is None:
            raise FormatNotFoundError(book_id, original_format)

        return ConversionRequest(
            book_id=book_id,
            original_format=original_format,
            target_format=target_format,
        )

    def _record_existing_format(
        self,
        request: "ConversionRequest",
        user_id: int | None,
        conversion_method: ConversionMethod,
    ) -> BookConversion:
        """Record that target format already exists.

        Parameters
        ----------
        request : ConversionRequest
            Conversion request.
        user_id : int | None
            User ID.
        conversion_method : ConversionMethod
            Conversion method.

        Returns
        -------
        BookConversion
            Conversion record.
        """
        book = self._book_repository.get_book(request.book_id)
        original_file_path = self._book_repository.get_book_file_path(
            book,
            request.book_id,
            request.original_format,
            self._library_root,
        )

        conversion = BookConversion(
            book_id=request.book_id,
            library_id=self._library.id if self._library else None,
            user_id=user_id,
            original_format=request.original_format,
            target_format=request.target_format,
            original_file_path=str(original_file_path) if original_file_path else "",
            converted_file_path=str(original_file_path) if original_file_path else "",
            original_backed_up=False,
            conversion_method=conversion_method,
            status=ConversionStatus.COMPLETED,
            created_at=self._now(),
            completed_at=self._now(),
        )

        conversion = self._conversion_repository.save(conversion)
        self._session.commit()
        return conversion

    def _perform_conversion(
        self,
        request: "ConversionRequest",
        user_id: int | None,
        conversion_method: ConversionMethod,
        backup_original: bool,
    ) -> BookConversion:
        """Perform the actual conversion.

        Parameters
        ----------
        request : ConversionRequest
            Conversion request.
        user_id : int | None
            User ID.
        conversion_method : ConversionMethod
            Conversion method.
        backup_original : bool
            Whether to backup original.

        Returns
        -------
        BookConversion
            Conversion record.

        Raises
        ------
        ConversionError
            If conversion fails.
        """
        book = self._book_repository.get_book(request.book_id)
        original_file_path = self._book_repository.get_book_file_path(
            book,
            request.book_id,
            request.original_format,
            self._library_root,
        )
        if original_file_path is None:
            raise FormatNotFoundError(request.book_id, request.original_format)

        # Create conversion record (in progress)
        conversion = BookConversion(
            book_id=request.book_id,
            library_id=self._library.id if self._library else None,
            user_id=user_id,
            original_format=request.original_format,
            target_format=request.target_format,
            original_file_path=str(original_file_path),
            converted_file_path="",  # Will be set after conversion
            original_backed_up=False,
            conversion_method=conversion_method,
            status=ConversionStatus.FAILED,  # Will update on success
            created_at=self._now(),
        )

        # Backup original if requested
        backup_path: Path | None = None
        if backup_original:
            backup_path = self._backup_service.backup(original_file_path)
            conversion.original_backed_up = True
            if backup_path:
                conversion.backup_file_path = str(backup_path)

        try:
            # Perform conversion
            converted_file_path = self._execute_conversion(
                original_file_path,
                request.target_format,
                book,
                request.book_id,
                user_id=user_id,
            )

            # Add converted format to Calibre database
            self._book_repository.add_format_to_calibre(
                request.book_id, converted_file_path, request.target_format
            )

            # Update conversion record
            conversion.converted_file_path = str(converted_file_path)
            conversion.status = ConversionStatus.COMPLETED
            conversion.completed_at = self._now()

            conversion = self._conversion_repository.save(conversion)
            self._session.commit()
            logger.info(
                "Conversion successful: book_id=%d, %s -> %s, path=%s",
                request.book_id,
                request.original_format,
                request.target_format,
                converted_file_path,
            )
        except Exception as e:
            # Update conversion record with error
            conversion.status = ConversionStatus.FAILED
            conversion.error_message = str(e)
            conversion.completed_at = self._now()
            conversion = self._conversion_repository.save(conversion)
            self._session.commit()
            raise

        return conversion

    def _execute_conversion(
        self,
        input_path: Path,
        target_format: str,
        book: Book,
        book_id: int,
        user_id: int | None = None,
    ) -> Path:
        """Execute the conversion using the conversion strategy.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        target_format : str
            Target format.
        book : Book
            Book record.
        book_id : int
            Book ID.
        user_id : int | None
            Optional user ID for retrieving KCC profile.

        Returns
        -------
        Path
            Path to converted file.

        Raises
        ------
        ConversionError
            If conversion fails.
        """
        # Create temporary output file
        output_suffix = f".{target_format.lower()}"
        with NamedTemporaryFile(
            delete=False, suffix=output_suffix, prefix="calibre_convert_"
        ) as temp_file:
            temp_output_path = Path(temp_file.name)

        try:
            # Check if this is a comic format and we have a user_id
            # If so, retrieve user's KCC profile
            source_format = input_path.suffix.upper().lstrip(".")
            profile_getter = None
            if user_id and source_format in {"CBZ", "CBR", "CB7", "PDF"}:
                from bookcard.services.conversion.strategies.composite import (
                    is_comic_format,
                )

                if is_comic_format(source_format):
                    from bookcard.services.kcc_profile_service import (
                        KCCProfileService,
                    )

                    profile_service = KCCProfileService(self._session)

                    def profile_getter() -> "KCCConversionProfile | None":
                        return profile_service.get_default_profile(user_id)

            # Execute conversion using strategy
            # If strategy is composite and we have a profile getter, use it
            from bookcard.services.conversion.strategies.composite import (
                CompositeConversionStrategy,
            )

            if (
                isinstance(self._conversion_strategy, CompositeConversionStrategy)
                and profile_getter
            ):
                # Composite strategy with profile support
                self._conversion_strategy.convert(
                    input_path,
                    target_format,
                    temp_output_path,
                    profile_getter=profile_getter,
                )
            else:
                # Standard strategy
                self._conversion_strategy.convert(
                    input_path, target_format, temp_output_path
                )

            # Determine final output path
            book_dir = self._library_root / book.path
            book_dir.mkdir(parents=True, exist_ok=True)

            # Determine output filename - use same name as existing format
            data = self._book_repository.get_format_data(book_id, target_format)
            if data and data.name:
                file_name = data.name
            else:
                # Get any existing format's name
                first_format = self._get_first_format(book_id)
                first_data = self._book_repository.get_format_data(
                    book_id, first_format
                )
                file_name = (
                    first_data.name if first_data and first_data.name else str(book_id)
                )

            final_path = book_dir / f"{file_name}.{target_format.lower()}"

            # Move file to final location
            shutil.move(str(temp_output_path), str(final_path))
            logger.debug("Converted file saved to: %s", final_path)
        except Exception:
            # Clean up temp file on error
            with suppress(OSError):
                if temp_output_path.exists():
                    temp_output_path.unlink()
            raise
        else:
            return final_path

    def _get_first_format(self, book_id: int) -> str:
        """Get first available format for a book.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        str
            First format found, or empty string if none.
        """
        # Try common formats
        for fmt in ["EPUB", "MOBI", "AZW3", "PDF"]:
            if self._book_repository.format_exists(book_id, fmt):
                return fmt
        return ""

    def _now(self) -> "datetime":
        """Get current UTC datetime.

        Returns
        -------
        datetime
            Current UTC datetime.
        """
        from datetime import UTC, datetime

        return datetime.now(UTC)

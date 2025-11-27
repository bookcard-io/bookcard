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

Handles format conversion using Calibre's ebook-convert command.
Follows SRP by focusing solely on conversion operations.
"""

import logging
import shutil
import subprocess  # noqa: S404
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.config import Library
from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.repositories import CalibreBookRepository
from fundamental.services.conversion_utils import raise_conversion_error

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)


class ConversionService:
    """Service for converting book formats.

    Handles format conversion using Calibre's ebook-convert command,
    backup of originals, and logging conversion history.

    Parameters
    ----------
    session : Session
        Database session.
    library : Library
        Library configuration.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library: Library,
    ) -> None:
        """Initialize conversion service.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        """
        self._session = session
        self._library = library
        self._book_repo = CalibreBookRepository(
            calibre_db_path=str(library.calibre_db_path),
        )

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
        stmt = (
            select(BookConversion)
            .where(BookConversion.book_id == book_id)
            .where(BookConversion.original_format == original_format.upper())
            .where(BookConversion.target_format == target_format.upper())
            .where(BookConversion.status == ConversionStatus.COMPLETED)
        )
        return self._session.exec(stmt).first()

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
        ValueError
            If book not found, format not found, converter not available,
            or conversion fails.
        """
        # Normalize formats
        original_format_upper = original_format.upper().lstrip(".")
        target_format_upper = target_format.upper().lstrip(".")

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

        # Get book and verify format exists
        book = self._get_book(book_id)
        original_file_path = self._get_book_file_path(
            book, book_id, original_format_upper
        )
        if original_file_path is None:
            msg = (
                f"Original format {original_format_upper} not found for book {book_id}"
            )
            raise ValueError(msg)

        # Check if target format already exists
        if self._format_exists(book_id, target_format_upper):
            logger.info(
                "Target format %s already exists for book_id=%d",
                target_format_upper,
                book_id,
            )
            # Create a conversion record for tracking
            conversion = self._create_conversion_record(
                book_id=book_id,
                original_format=original_format_upper,
                target_format=target_format_upper,
                original_file_path=str(original_file_path),
                converted_file_path=str(original_file_path),  # Already exists
                user_id=user_id,
                conversion_method=conversion_method,
                original_backed_up=False,
                status=ConversionStatus.COMPLETED,
            )
            self._session.commit()
            return conversion

        # Get converter path
        converter_path = self._get_converter_path()
        if not converter_path or not Path(converter_path).exists():
            msg = "Calibre converter not found. Please configure converter_path in settings."
            raise ValueError(msg)

        # Create conversion record (in progress)
        conversion = self._create_conversion_record(
            book_id=book_id,
            original_format=original_format_upper,
            target_format=target_format_upper,
            original_file_path=str(original_file_path),
            converted_file_path="",  # Will be set after conversion
            user_id=user_id,
            conversion_method=conversion_method,
            original_backed_up=False,
            status=ConversionStatus.FAILED,  # Will update on success
        )

        # Backup original if requested
        backup_path: Path | None = None
        if backup_original:
            backup_path = self._backup_original_file(original_file_path)
            conversion.original_backed_up = True
            if backup_path:
                conversion.backup_file_path = str(backup_path)

        try:
            # Perform conversion
            converted_file_path = self._execute_conversion(
                converter_path, original_file_path, target_format_upper, book, book_id
            )

            # Add converted format to Calibre database
            self._add_format_to_calibre(
                book_id, converted_file_path, target_format_upper
            )

            # Update conversion record
            conversion.converted_file_path = str(converted_file_path)
            conversion.status = ConversionStatus.COMPLETED
            conversion.completed_at = self._now()

            self._session.commit()
            logger.info(
                "Conversion successful: book_id=%d, %s -> %s",
                book_id,
                original_format_upper,
                target_format_upper,
            )
        except Exception as e:
            # Update conversion record with error
            conversion.status = ConversionStatus.FAILED
            conversion.error_message = str(e)
            conversion.completed_at = self._now()
            self._session.commit()

            logger.exception(
                "Conversion failed: book_id=%d, %s -> %s",
                book_id,
                original_format_upper,
                target_format_upper,
            )
            raise
        else:
            return conversion

    def _get_book(self, book_id: int) -> Book:
        """Get book from Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        Book
            Book record.

        Raises
        ------
        ValueError
            If book not found.
        """
        with self._book_repo.get_session() as session:
            stmt = select(Book).where(Book.id == book_id)
            book = session.exec(stmt).first()
            if book is None:
                msg = f"Book {book_id} not found"
                raise ValueError(msg)
            return book

    def _get_book_file_path(
        self, book: Book, book_id: int, format_upper: str
    ) -> Path | None:
        """Get file path for a book format.

        Parameters
        ----------
        book : Book
            Book record.
        format_upper : str
            Format in uppercase.

        Returns
        -------
        Path | None
            File path if found, None otherwise.
        """
        # Determine library path
        library_path = Path(self._library.calibre_db_path)
        if self._library.library_root:
            library_path = Path(self._library.library_root)

        book_dir = library_path / book.path

        # Try common filename patterns
        with self._book_repo.get_session() as session:
            stmt = (
                select(Data)
                .where(Data.book == book_id)
                .where(Data.format == format_upper)
            )
            data = session.exec(stmt).first()
            if data is None:
                return None

            file_name = data.name or str(book_id)
            # Primary path: {name}.{format}
            primary = book_dir / f"{file_name}.{format_upper.lower()}"
            if primary.exists():
                return primary

            # Alternative path: {book_id}.{format}
            alt = book_dir / f"{book_id}.{format_upper.lower()}"
            if alt.exists():
                return alt

        return None

    def _format_exists(self, book_id: int, format_upper: str) -> bool:
        """Check if a format already exists for a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        format_upper : str
            Format in uppercase.

        Returns
        -------
        bool
            True if format exists, False otherwise.
        """
        with self._book_repo.get_session() as session:
            stmt = (
                select(Data)
                .where(Data.book == book_id)
                .where(Data.format == format_upper)
            )
            return session.exec(stmt).first() is not None

    def _get_converter_path(self) -> str | None:
        """Get path to Calibre ebook-convert binary.

        Returns
        -------
        str | None
            Path to converter if found, None otherwise.
        """
        # First check Docker installation path
        docker_path = Path("/app/calibre/ebook-convert")
        if docker_path.exists():
            return str(docker_path)

        # Fallback to PATH lookup
        converter = shutil.which("ebook-convert")
        if converter:
            return converter

        return None

    def _backup_original_file(self, original_path: Path) -> Path | None:
        """Backup original file before conversion.

        Parameters
        ----------
        original_path : Path
            Path to original file.

        Returns
        -------
        Path | None
            Path to backup file if created, None otherwise.
        """
        try:
            # Create backup in same directory with .bak extension
            backup_path = original_path.with_suffix(original_path.suffix + ".bak")
            shutil.copy2(original_path, backup_path)
            logger.debug(
                "Backed up original file: %s -> %s", original_path, backup_path
            )
        except (OSError, shutil.Error) as e:
            logger.warning("Failed to backup original file %s: %s", original_path, e)
            return None
        else:
            return backup_path

    def _execute_conversion(
        self,
        converter_path: str,
        input_path: Path,
        target_format: str,
        book: Book,
        book_id: int,
    ) -> Path:
        """Execute Calibre ebook-convert command.

        Parameters
        ----------
        converter_path : str
            Path to ebook-convert binary.
        input_path : Path
            Path to input file.
        target_format : str
            Target format (e.g., "EPUB").

        Returns
        -------
        Path
            Path to converted file.

        Raises
        ------
        ValueError
            If conversion fails.
        """
        # Create temporary output file
        output_suffix = f".{target_format.lower()}"
        with NamedTemporaryFile(
            delete=False, suffix=output_suffix, prefix="calibre_convert_"
        ) as temp_file:
            output_path = Path(temp_file.name)

        try:
            # Run ebook-convert command
            cmd = [
                converter_path,
                str(input_path),
                str(output_path),
            ]

            logger.debug("Running conversion: %s", " ".join(cmd))
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown conversion error"
                msg = f"Conversion failed: {error_msg}"
                raise_conversion_error(msg)
            if not output_path.exists():
                msg = "Conversion completed but output file not found"
                raise_conversion_error(msg)

            library_path = Path(self._library.calibre_db_path)
            if self._library.library_root:
                library_path = Path(self._library.library_root)

            book_dir = library_path / book.path
            book_dir.mkdir(parents=True, exist_ok=True)

            # Determine output filename - use same name as existing format
            with self._book_repo.get_session() as session:
                stmt = select(Data).where(Data.book == book_id).limit(1)
                data = session.exec(stmt).first()
                file_name = data.name if data and data.name else str(book_id)

            final_path = book_dir / f"{file_name}.{target_format.lower()}"

            # Move file to final location
            shutil.move(str(output_path), str(final_path))
            logger.debug("Converted file saved to: %s", final_path)
        except subprocess.TimeoutExpired:
            msg = "Conversion timed out after 5 minutes"
            raise_conversion_error(msg)
        except Exception:
            # Clean up temp file on error
            with suppress(OSError):
                output_path.unlink()
            raise
        else:
            return final_path

    def _add_format_to_calibre(
        self, book_id: int, file_path: Path, format_upper: str
    ) -> None:
        """Add converted format to Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_path : Path
            Path to converted file.
        format_upper : str
            Format in uppercase.
        """
        file_size = file_path.stat().st_size
        file_name = file_path.stem

        with self._book_repo.get_session() as session:
            # Check if format already exists
            stmt = (
                select(Data)
                .where(Data.book == book_id)
                .where(Data.format == format_upper)
            )
            existing = session.exec(stmt).first()

            if existing:
                # Update existing record
                existing.uncompressed_size = file_size
                existing.name = file_name
                session.add(existing)
            else:
                # Create new Data record
                data = Data(
                    book=book_id,
                    format=format_upper,
                    uncompressed_size=file_size,
                    name=file_name,
                )
                session.add(data)

            session.commit()

    def _create_conversion_record(
        self,
        book_id: int,
        original_format: str,
        target_format: str,
        original_file_path: str,
        converted_file_path: str,
        user_id: int | None,
        conversion_method: ConversionMethod,
        original_backed_up: bool,
        status: ConversionStatus,
    ) -> BookConversion:
        """Create a conversion history record.

        Parameters
        ----------
        book_id : int
            Book ID.
        original_format : str
            Source format.
        target_format : str
            Target format.
        original_file_path : str
            Path to original file.
        converted_file_path : str
            Path to converted file.
        user_id : int | None
            User ID.
        conversion_method : ConversionMethod
            Conversion method.
        original_backed_up : bool
            Whether original was backed up.
        status : ConversionStatus
            Conversion status.

        Returns
        -------
        BookConversion
            Conversion record.
        """
        conversion = BookConversion(
            book_id=book_id,
            library_id=self._library.id if self._library else None,
            user_id=user_id,
            original_format=original_format,
            target_format=target_format,
            original_file_path=original_file_path,
            converted_file_path=converted_file_path,
            original_backed_up=original_backed_up,
            conversion_method=conversion_method,
            status=status,
            created_at=self._now(),
        )
        self._session.add(conversion)
        self._session.flush()
        return conversion

    def _now(self) -> "datetime":
        """Get current UTC datetime.

        Returns
        -------
        datetime
            Current UTC datetime.
        """
        from datetime import UTC, datetime

        return datetime.now(UTC)

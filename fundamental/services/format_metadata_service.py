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

"""Service for extracting detailed metadata from book format files.

Provides detailed technical information about specific format files,
such as version, page count, DRM status, and validation.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pypdf import PdfReader

from fundamental.api.schemas.books import FormatMetadataResponse
from fundamental.services.epub_fixer.core.epub import EPUBReader

if TYPE_CHECKING:
    from pathlib import Path

    from fundamental.repositories.calibre_book_repository import CalibreBookRepository

logger = logging.getLogger(__name__)


class FormatMetadataService:
    """Service for extracting detailed metadata from book format files."""

    def __init__(self, book_repo: CalibreBookRepository) -> None:
        """Initialize format metadata service.

        Parameters
        ----------
        book_repo : CalibreBookRepository
            Book repository for accessing file paths.
        """
        self._book_repo = book_repo

    def get_format_metadata(
        self, book_id: int, file_format: str
    ) -> FormatMetadataResponse:
        """Get detailed metadata for a specific format of a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_format : str
            Format extension (e.g. 'epub').

        Returns
        -------
        FormatMetadataResponse
            Detailed format metadata.

        Raises
        ------
        ValueError
            If book or format not found.
        """
        file_format_upper = file_format.upper().lstrip(".")

        # Get book and file path
        book_with_rels = self._book_repo.get_book_full(book_id)
        if book_with_rels is None:
            msg = "book_not_found"
            raise ValueError(msg)

        # Find the format data
        format_data = next(
            (
                f
                for f in book_with_rels.formats
                if str(f.get("format", "")).upper() == file_format_upper
            ),
            None,
        )

        if format_data is None:
            msg = f"Format {file_format_upper} not found for book {book_id}"
            raise ValueError(msg)

        # Get file path
        file_path = self._resolve_file_path(
            book_with_rels, format_data, file_format_upper, book_id
        )

        # Basic file info
        stats = file_path.stat()
        created_at = datetime.fromtimestamp(stats.st_ctime, tz=UTC)
        modified_at = datetime.fromtimestamp(stats.st_mtime, tz=UTC)
        size = stats.st_size

        # Initialize response
        library_path = self._book_repo.get_library_path()
        response = FormatMetadataResponse(
            format=file_format_upper,
            size=size,
            path=str(file_path.relative_to(library_path)),
            created_at=created_at,
            modified_at=modified_at,
            mime_type=self._get_mime_type(file_format_upper),
        )

        # Format-specific extraction
        if file_format_upper == "EPUB":
            self._extract_epub_details(file_path, response)
        elif file_format_upper == "PDF":
            self._extract_pdf_details(file_path, response)

        return response

    def _resolve_file_path(
        self,
        book_with_rels: object,
        format_data: dict[str, str | int],
        file_format_upper: str,
        book_id: int,
    ) -> Path:
        """Resolve the file path for a book format.

        Parameters
        ----------
        book_with_rels : object
            Book with relations object containing book path.
        format_data : dict[str, str | int]
            Format data dictionary.
        file_format_upper : str
            Format in uppercase.
        book_id : int
            Book ID.

        Returns
        -------
        Path
            Resolved file path.

        Raises
        ------
        ValueError
            If file cannot be located.
        """
        library_path = self._book_repo.get_library_path()
        book_path = getattr(book_with_rels, "book", None)
        if book_path is None:
            msg = "Book path not found"
            raise ValueError(msg)
        book_dir = library_path / book_path.path

        file_name = format_data.get("name", "")
        if not file_name:
            file_name = str(book_id)

        file_path = book_dir / f"{file_name}.{file_format_upper.lower()}"

        if file_path.exists():
            return file_path

        # Try fallback: {book_id}.{format}
        file_path = book_dir / f"{book_id}.{file_format_upper.lower()}"
        if file_path.exists():
            return file_path

        # Try finding by extension
        try:
            for f in book_dir.iterdir():
                if f.is_file() and f.suffix.lower() == f".{file_format_upper.lower()}":
                    return f
        except OSError as e:
            logger.exception("Failed to iterate book directory")
            msg = f"Could not locate file for {file_format_upper}"
            raise ValueError(msg) from e

        msg = f"File not found for format {file_format_upper}"
        raise ValueError(msg)

    def _get_mime_type(self, format_upper: str) -> str:
        """Get MIME type for format."""
        mime_types = {
            "EPUB": "application/epub+zip",
            "PDF": "application/pdf",
            "MOBI": "application/x-mobipocket-ebook",
            "AZW3": "application/vnd.amazon.ebook",
            "FB2": "application/x-fictionbook+xml",
            "CBZ": "application/vnd.comicbook+zip",
            "CBR": "application/vnd.comicbook+rar",
            "TXT": "text/plain",
        }
        return mime_types.get(format_upper, "application/octet-stream")

    def _extract_epub_details(
        self, file_path: Path, response: FormatMetadataResponse
    ) -> None:
        """Extract EPUB-specific details."""
        try:
            reader = EPUBReader()
            contents = reader.read(file_path)

            # Determine version from opf
            # This is a simplified check
            response.version = "Unknown"

            # Check for encryption (simplified)
            # Real DRM check would inspect rights.xml or similar
            if (
                "META-INF/rights.xml" in contents.files
                or "META-INF/encryption.xml" in contents.files
            ):
                response.encryption = "DRM Protected"
            else:
                response.encryption = "None"

            # Basic validation status
            # If we successfully read it, it's at least a valid zip structure
            response.validation_status = "Valid Structure"

        except (OSError, ValueError, KeyError, AttributeError) as e:
            response.validation_status = "Invalid"
            response.validation_issues.append(str(e))
        except Exception as e:
            logger.exception("Unexpected error extracting EPUB details")
            response.validation_status = "Invalid"
            response.validation_issues.append(str(e))

    def _extract_pdf_details(
        self, file_path: Path, response: FormatMetadataResponse
    ) -> None:
        """Extract PDF-specific details."""
        try:
            reader = PdfReader(file_path)

            # Page count
            with contextlib.suppress(AttributeError, IndexError):
                response.page_count = len(reader.pages)

            # Version
            # PyPDF might expose version
            if hasattr(reader, "pdf_header"):
                response.version = reader.pdf_header

            # Encryption
            if reader.is_encrypted:
                response.encryption = "Encrypted"
            else:
                response.encryption = "None"

            response.validation_status = "Valid"

        except (OSError, ValueError, AttributeError) as e:
            response.validation_status = "Invalid"
            response.validation_issues.append(str(e))
        except Exception as e:
            logger.exception("Unexpected error extracting PDF details")
            response.validation_status = "Invalid"
            response.validation_issues.append(str(e))

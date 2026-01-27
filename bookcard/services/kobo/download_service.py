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

"""Kobo download service.

Handles business logic for downloading book files for Kobo devices.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from bookcard.repositories.models import BookWithFullRelations
    from bookcard.services.book_service import BookService


@dataclass
class DownloadFileInfo:
    """Information about a book file to download.

    Parameters
    ----------
    file_path : Path
        Full path to the book file.
    filename : str
        Filename for the download.
    media_type : str
        MIME type for the file.
    """

    file_path: Path
    filename: str
    media_type: str


# Media type mapping for book formats
MEDIA_TYPES: dict[str, str] = {
    "EPUB": "application/epub+zip",
    "KEPUB": "application/epub+zip",
    "PDF": "application/pdf",
    "MOBI": "application/x-mobipocket-ebook",
}


class KoboDownloadService:
    """Service for handling Kobo book downloads.

    Handles finding book formats, resolving file paths, and validating
    file existence for Kobo device downloads.

    Parameters
    ----------
    book_service : BookService
        Book service for querying books.
    """

    def __init__(self, book_service: BookService) -> None:
        self._book_service = book_service

    def get_download_file_info(
        self, book_id: int, book_format: str
    ) -> DownloadFileInfo:
        """Get file information for downloading a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        book_format : str
            Book format (e.g., "EPUB", "KEPUB", "PDF").

        Returns
        -------
        DownloadFileInfo
            File information including path, filename, and media type.

        Raises
        ------
        HTTPException
            If book not found (404).
            If format not found (404).
            If file not found (404).
        """
        book_with_rels = self._book_service.get_book_full(book_id)
        if book_with_rels is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            )

        format_data = self._find_format(book_with_rels, book_format)
        if format_data is None:
            format_upper = book_format.upper()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"format_not_found: {format_upper}",
            )

        library_path = self._resolve_library_path()
        file_path, filename = self._resolve_file_path(
            book_with_rels.book, library_path, book_id, book_format, format_data
        )

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="file_not_found",
            )

        media_type = self._get_media_type(book_format)
        return DownloadFileInfo(
            file_path=file_path,
            filename=filename,
            media_type=media_type,
        )

    def _find_format(
        self,
        book_with_rels: BookWithFullRelations,
        book_format: str,
    ) -> dict[str, object] | None:
        """Find format data in book formats.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with relations.
        book_format : str
            Book format to find.

        Returns
        -------
        dict[str, object] | None
            Format data if found, None otherwise.
        """
        formats = getattr(book_with_rels, "formats", []) or []
        format_upper = book_format.upper()
        for fmt in formats:
            if fmt.get("format", "").upper() == format_upper:
                return fmt
        return None

    def _resolve_library_path(self) -> Path:
        """Resolve the library root path.

        Returns
        -------
        Path
            Library root path.
        """
        library = self._book_service._library  # noqa: SLF001
        lib_root = getattr(library, "library_root", None)
        if lib_root:
            return Path(lib_root)

        library_db_path = library.calibre_db_path
        library_db_path_obj = Path(library_db_path)
        if library_db_path_obj.is_dir():
            return library_db_path_obj
        return library_db_path_obj.parent

    def _resolve_file_path(
        self,
        book: object,
        library_path: Path,
        book_id: int,
        book_format: str,
        format_data: dict[str, object],
    ) -> tuple[Path, str]:
        """Resolve the file path and filename.

        Parameters
        ----------
        book : object
            Book object with path attribute.
        library_path : Path
            Library root path.
        book_id : int
            Book ID.
        book_format : str
            Book format.
        format_data : dict[str, object]
            Format data from book formats.

        Returns
        -------
        tuple[Path, str]
            Tuple of (file_path, filename).
        """
        book_path = library_path / getattr(book, "path", "")
        file_name = format_data.get("name", f"{book_id}.{book_format.lower()}")
        if not isinstance(file_name, str):
            file_name = f"{book_id}.{book_format.lower()}"

        # Ensure correct extension
        if not file_name.lower().endswith(f".{book_format.lower()}"):
            file_name = f"{file_name}.{book_format.lower()}"

        file_path = book_path / file_name

        # Try alternative naming if file doesn't exist
        if not file_path.exists():
            alt_file_name = f"{book_id}.{book_format.lower()}"
            alt_file_path = book_path / alt_file_name
            if alt_file_path.exists():
                return alt_file_path, alt_file_name

        return file_path, file_name

    def _get_media_type(self, book_format: str) -> str:
        """Get media type for book format.

        Parameters
        ----------
        book_format : str
            Book format.

        Returns
        -------
        str
            MIME type for the format.
        """
        format_upper = book_format.upper()
        return MEDIA_TYPES.get(format_upper, "application/octet-stream")

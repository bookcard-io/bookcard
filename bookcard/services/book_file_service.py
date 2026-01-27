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
"""File resolution utilities for book formats."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from bookcard.repositories.models import Book, BookWithFullRelations
    from bookcard.services.book_service import BookService


class BookFileService:
    """Service for resolving book file paths and download names."""

    def __init__(self, book_service: BookService) -> None:
        self._book_service = book_service

    def resolve_file_path(
        self,
        book: Book,
        book_id: int,
        file_format: str,
        format_data: dict[str, str | int],
    ) -> tuple[Path, str]:
        """Resolve the absolute file path and filename for a book format."""
        library_path = self._get_library_path()
        book_path = library_path / book.path
        file_name = self.get_file_name(format_data, book_id, file_format)
        file_path = book_path / file_name

        if file_path.exists():
            return file_path, file_name

        alt_file_name = f"{book_id}.{file_format.lower()}"
        alt_file_path = book_path / alt_file_name
        if alt_file_path.exists():
            return alt_file_path, alt_file_name

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"file_not_found: tried {file_path} and {alt_file_path}",
        )

    @staticmethod
    def build_download_filename(
        book_with_rels: BookWithFullRelations, book_id: int, file_format: str
    ) -> str:
        """Create a safe download filename using author and title."""
        authors_str = (
            ", ".join(book_with_rels.authors) if book_with_rels.authors else ""
        )
        safe_author = "".join(
            c for c in authors_str if c.isalnum() or c in (" ", "-", "_", ",")
        ).strip()
        if not safe_author:
            safe_author = "Unknown"

        safe_title = "".join(
            c for c in book_with_rels.book.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_title:
            safe_title = f"book_{book_id}"

        return f"{safe_author} - {safe_title}.{file_format.lower()}"

    def _get_library_path(self) -> Path:
        """Resolve the library root path from service configuration."""
        lib_root = getattr(self._book_service._library, "library_root", None)  # noqa: SLF001
        if lib_root:
            return Path(lib_root)

        library_db_path = self._book_service._library.calibre_db_path  # noqa: SLF001
        library_db_path_obj = Path(library_db_path)
        if library_db_path_obj.is_dir():
            return library_db_path_obj
        return library_db_path_obj.parent

    @staticmethod
    def get_file_name(
        format_data: dict[str, str | int], book_id: int, file_format: str
    ) -> str:
        """Compute filename for a book format, ensuring correct extension."""
        file_name = format_data.get("name", "")
        if not file_name or not isinstance(file_name, str):
            return f"{book_id}.{file_format.lower()}"

        expected_suffix = f".{file_format.lower()}"
        if not file_name.lower().endswith(expected_suffix):
            return f"{file_name}{expected_suffix}"
        return file_name

# Copyright (C) 2026 knguyen and others
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

"""Protocols for book merge dependencies."""

from pathlib import Path
from typing import Protocol

from bookcard.models.core import Book
from bookcard.models.media import Data


class BookRepository(Protocol):
    """Repository for book data access."""

    def get(self, book_id: int) -> Book | None:
        """Get book by ID."""
        ...

    def get_or_raise(self, book_id: int) -> Book:
        """Get book or raise BookNotFoundError."""
        ...

    def get_many_or_raise(self, book_ids: list[int]) -> list[Book]:
        """Get multiple books or raise if any not found."""
        ...

    def get_with_data(self, book_id: int) -> tuple[Book, list[Data]] | None:
        """Get book with associated data records."""
        ...

    def add_format(
        self,
        *,
        book_id: int,
        file_path: Path,
        file_format: str,
        replace: bool = False,
    ) -> None:
        """Add format to book using standard mechanism."""
        ...

    def save(self, instance: object) -> None:
        """Save instance to database."""
        ...

    def delete(self, instance: object) -> None:
        """Delete instance from database."""
        ...

    def delete_data(self, data: Data) -> None:
        """Delete data record."""
        ...

    def commit(self) -> None:
        """Commit changes."""
        ...

    def flush(self) -> None:
        """Flush changes."""
        ...


class FileStorage(Protocol):
    """Abstract file storage operations."""

    def move_file(self, src: Path, dest: Path) -> None:
        """Move file from src to dest."""
        ...

    def copy_file(self, src: Path, dest: Path) -> None:
        """Copy file from src to dest."""
        ...

    def delete_directory(self, path: Path) -> None:
        """Delete directory and its contents."""
        ...

    def backup_file(self, path: Path) -> None:
        """Backup file (e.g. rename with .bak suffix)."""
        ...

    def get_image_quality(self, path: Path) -> dict[str, int]:
        """Get image quality metrics."""
        ...

    def get_unique_bak_path(self, file_path: Path) -> Path:
        """Get unique backup path."""
        ...

    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...

    def find_file(self, directory: Path, stem: str, extension: str) -> Path | None:
        """Find file in directory with stem and extension (case-insensitive)."""
        ...

    def ensure_dir(self, path: Path) -> None:
        """Ensure parent directory exists."""
        ...

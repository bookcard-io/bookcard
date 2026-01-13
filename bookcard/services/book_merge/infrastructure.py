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

"""Concrete implementations for book merge infrastructure."""

import shutil
from pathlib import Path

from PIL import Image
from sqlmodel import Session, select

from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.services.book_merge.exceptions import BookNotFoundError


class SQLBookRepository:
    """SQLModel implementation of BookRepository."""

    def __init__(self, session: Session, library_path: Path) -> None:
        self._session = session
        self._library_path = library_path

    def get(self, book_id: int) -> Book | None:
        """Get a book by ID."""
        return self._session.get(Book, book_id)

    def get_or_raise(self, book_id: int) -> Book:
        """Get a book by ID or raise BookNotFoundError."""
        book = self.get(book_id)
        if not book:
            raise BookNotFoundError(book_id)
        return book

    def get_many_or_raise(self, book_ids: list[int]) -> list[Book]:
        """Get multiple books by IDs or raise BookNotFoundError if any is missing."""
        return [self.get_or_raise(book_id) for book_id in book_ids]

    def get_with_data(self, book_id: int) -> tuple[Book, list[Data]] | None:
        """Get a book and its associated data records."""
        book = self.get(book_id)
        if not book:
            return None
        data = self._session.exec(select(Data).where(Data.book == book_id)).all()
        return book, list(data)

    def add_format(
        self,
        *,
        book_id: int,
        file_path: Path,
        file_format: str,
        replace: bool = False,
    ) -> None:
        """Add a format to a book using standard logic."""
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        file_format_upper = file_format.upper().lstrip(".")

        # Check for existing format
        existing_data = self._session.exec(
            select(Data).where(Data.book == book_id)
        ).all()
        existing_format_record = next(
            (d for d in existing_data if d.format == file_format_upper), None
        )
        if existing_format_record is not None and not replace:
            msg = f"Format {file_format_upper} already exists for book {book_id}"
            raise FileExistsError(msg)

        # Determine target directory name
        # Use existing format's name if available, otherwise parse from book path
        book = self.get_or_raise(book_id)
        title_dir = existing_data[0].name if existing_data else Path(book.path).name

        # Construct destination path
        library_path = self._library_path
        book_dir = library_path / book.path

        if not book_dir.exists():
            book_dir.mkdir(parents=True, exist_ok=True)

        dest_filename = f"{title_dir}.{file_format_upper.lower()}"
        dest_path = book_dir / dest_filename

        # Move file and update DB
        # Note: Direct file operations used here to avoid circular dependencies
        shutil.move(str(file_path), str(dest_path))

        file_size = dest_path.stat().st_size

        if existing_format_record:
            existing_format_record.uncompressed_size = file_size
            existing_format_record.name = title_dir
            self._session.add(existing_format_record)
        else:
            new_data = Data(
                book=book_id,
                format=file_format_upper,
                uncompressed_size=file_size,
                name=title_dir,
            )
            self._session.add(new_data)

        # Update last_modified
        from datetime import UTC, datetime

        book.last_modified = datetime.now(UTC)
        self._session.add(book)
        self._session.flush()

    def save(self, instance: object) -> None:
        """Save a model instance to the session."""
        self._session.add(instance)

    def delete(self, instance: object) -> None:
        """Delete a model instance from the session."""
        self._session.delete(instance)

    def delete_data(self, data: Data) -> None:
        """Delete a data record."""
        self._session.delete(data)

    def commit(self) -> None:
        """Commit the session."""
        self._session.commit()

    def flush(self) -> None:
        """Flush the session."""
        self._session.flush()


class LocalFileStorage:
    """Local filesystem implementation of FileStorage."""

    def __init__(self, library_path: str) -> None:
        self._library_path = Path(library_path)

    def move_file(self, src: Path, dest: Path) -> None:
        """Move a file from src to dest."""
        if not src.exists():
            return
        self.ensure_dir(dest)
        shutil.move(str(src), str(dest))

    def copy_file(self, src: Path, dest: Path) -> None:
        """Copy a file from src to dest."""
        if not src.exists():
            return
        self.ensure_dir(dest)
        shutil.copy2(str(src), str(dest))

    def delete_directory(self, path: Path) -> None:
        """Delete a directory and its contents."""
        if path.exists() and path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

    def backup_file(self, path: Path) -> None:
        """Backup a file by renaming it with a .bak extension."""
        if not path.exists():
            return
        bak_path = self.get_unique_bak_path(path)
        shutil.move(str(path), str(bak_path))

    def get_image_quality(self, path: Path) -> dict[str, int]:
        """Get image quality metrics (area, size)."""
        if not path.exists():
            return {"area": 0, "size": 0, "width": 0, "height": 0}

        size = path.stat().st_size
        try:
            with Image.open(path) as img:
                width, height = img.size
                return {
                    "area": width * height,
                    "size": size,
                    "width": width,
                    "height": height,
                }
        except Exception:  # noqa: BLE001
            return {"area": 0, "size": size, "width": 0, "height": 0}

    def get_unique_bak_path(self, file_path: Path) -> Path:
        """Generate a unique backup path with .bakN extension."""
        counter = 1
        bak_path = file_path.with_name(f"{file_path.name}.bak{counter}")
        while bak_path.exists():
            counter += 1
            bak_path = file_path.with_name(f"{file_path.name}.bak{counter}")
        return bak_path

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path.exists()

    def find_file(self, directory: Path, stem: str, extension: str) -> Path | None:
        """Find file in directory with stem and extension (case-insensitive)."""
        if not directory.exists() or not directory.is_dir():
            return None

        target_stem = stem.lower()
        target_ext = extension.lower().lstrip(".")

        for path in directory.iterdir():
            if not path.is_file():
                continue

            if (
                path.stem.lower() == target_stem
                and path.suffix.lower().lstrip(".") == target_ext
            ):
                return path

        return None

    def ensure_dir(self, path: Path) -> None:
        """Ensure the parent directory of a path exists."""
        path.parent.mkdir(parents=True, exist_ok=True)

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

"""Photo storage implementation for file system operations."""

from contextlib import suppress
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from fundamental.services.author.interfaces import PhotoStorageInterface
from fundamental.services.author_exceptions import PhotoStorageError


class FileSystemPhotoStorage(PhotoStorageInterface):
    """File system implementation of photo storage.

    Handles saving and deleting photos on the file system.
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize file system photo storage.

        Parameters
        ----------
        base_path : Path
            Base directory for storing photos.
        """
        self._base_path = base_path
        self._ensure_base_directory_exists()

    def _ensure_base_directory_exists(self) -> None:
        """Ensure the base directory exists, creating it if necessary."""
        self._base_path.mkdir(parents=True, exist_ok=True)
        (self._base_path / "authors").mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str, author_id: int) -> str:
        """Save photo and return relative path.

        Parameters
        ----------
        content : bytes
            Photo content.
        filename : str
            Original filename.
        author_id : int
            Author metadata ID.

        Returns
        -------
        str
            Relative path to saved photo.

        Raises
        ------
        PhotoStorageError
            If save operation fails.
        """
        photos_dir = self._base_path / "authors" / str(author_id)
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_ext = Path(filename).suffix.lower()
        content_hash = sha256(content).hexdigest()[:8]
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{content_hash}{file_ext}"
        photo_path = photos_dir / safe_filename

        # Save file
        try:
            photo_path.write_bytes(content)
        except OSError as exc:
            msg = f"failed_to_save_file: {exc!s}"
            raise PhotoStorageError(msg) from exc

        # Return relative path
        return str(photo_path.relative_to(self._base_path))

    def delete(self, path: str) -> None:
        """Delete photo at path.

        Parameters
        ----------
        path : str
            Relative path to photo.

        Raises
        ------
        PhotoStorageError
            If delete operation fails.
        """
        photo_path = self.get_full_path(path)
        if photo_path.exists():
            with suppress(OSError):
                photo_path.unlink()

    def get_full_path(self, relative_path: str) -> Path:
        """Get full path from relative path.

        Parameters
        ----------
        relative_path : str
            Relative path to photo.

        Returns
        -------
        Path
            Full path to photo.
        """
        return self._base_path / relative_path

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

"""File storage helpers used by services."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path


class FileStorageService:
    """Handles file storage operations."""

    def __init__(self, data_directory: str = "/data") -> None:
        self._data_directory = Path(data_directory)
        self._ensure_data_directory_exists()

    def _ensure_data_directory_exists(self) -> None:
        """Ensure the data directory exists."""
        self._data_directory.mkdir(parents=True, exist_ok=True)

    def get_user_assets_dir(self, user_id: int) -> Path:
        """Get the assets directory path for a user."""
        return self._data_directory / str(user_id) / "assets"

    def save_profile_picture(self, user_id: int, content: bytes, filename: str) -> str:
        """Save profile picture and return relative path."""
        assets_dir = self.get_user_assets_dir(user_id)
        assets_dir.mkdir(parents=True, exist_ok=True)

        file_ext = Path(filename).suffix.lower()
        picture_filename = f"profile_picture{file_ext}"
        picture_path = assets_dir / picture_filename

        try:
            picture_path.write_bytes(content)
        except OSError as exc:
            msg = f"failed_to_save_file: {exc!s}"
            raise ValueError(msg) from exc

        return str(picture_path.relative_to(self._data_directory))

    def delete_profile_picture(self, picture_path: str) -> None:
        """Delete profile picture file."""
        if not picture_path:
            return

        file_path = Path(picture_path)
        if file_path.is_absolute():
            with suppress(OSError):
                file_path.unlink()
        else:
            full_path = self._data_directory / picture_path
            with suppress(OSError):
                full_path.unlink()

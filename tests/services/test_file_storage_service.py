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

"""Tests for file storage service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bookcard.services.file_storage_service import FileStorageService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Return a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def service(temp_data_dir: Path) -> FileStorageService:
    """Return a FileStorageService with a temp directory."""
    return FileStorageService(data_directory=str(temp_data_dir))


# ---------------------------------------------------------------------------
# __init__ tests
# ---------------------------------------------------------------------------


class TestInit:
    """Tests for FileStorageService.__init__."""

    def test_init_creates_data_directory(self, tmp_path: Path) -> None:
        """Init creates the data directory if it doesn't exist."""
        data_dir = tmp_path / "new_data"
        assert not data_dir.exists()

        FileStorageService(data_directory=str(data_dir))

        assert data_dir.exists()

    def test_init_existing_directory(self, temp_data_dir: Path) -> None:
        """Init succeeds when data directory already exists."""
        service = FileStorageService(data_directory=str(temp_data_dir))

        assert service._data_directory == temp_data_dir


# ---------------------------------------------------------------------------
# get_user_assets_dir tests
# ---------------------------------------------------------------------------


class TestGetUserAssetsDir:
    """Tests for FileStorageService.get_user_assets_dir."""

    def test_get_user_assets_dir(
        self, service: FileStorageService, temp_data_dir: Path
    ) -> None:
        """Returns correct path for user assets directory."""
        result = service.get_user_assets_dir(42)

        assert result == temp_data_dir / "42" / "assets"


# ---------------------------------------------------------------------------
# save_profile_picture tests
# ---------------------------------------------------------------------------


class TestSaveProfilePicture:
    """Tests for FileStorageService.save_profile_picture."""

    @pytest.mark.parametrize(
        ("filename", "expected_ext"),
        [
            ("photo.jpg", ".jpg"),
            ("photo.JPEG", ".jpeg"),
            ("photo.PNG", ".png"),
            ("image.gif", ".gif"),
        ],
    )
    def test_save_profile_picture_success(
        self,
        service: FileStorageService,
        temp_data_dir: Path,
        filename: str,
        expected_ext: str,
    ) -> None:
        """Save creates file and returns relative path."""
        content = b"fake image data"

        result = service.save_profile_picture(1, content, filename)

        assert result == f"1/assets/profile_picture{expected_ext}"
        saved_path = temp_data_dir / result
        assert saved_path.exists()
        assert saved_path.read_bytes() == content

    def test_save_profile_picture_creates_assets_dir(
        self,
        service: FileStorageService,
        temp_data_dir: Path,
    ) -> None:
        """Save creates assets directory if it doesn't exist."""
        assets_dir = temp_data_dir / "1" / "assets"
        assert not assets_dir.exists()

        service.save_profile_picture(1, b"data", "pic.jpg")

        assert assets_dir.exists()

    def test_save_profile_picture_overwrites_existing(
        self,
        service: FileStorageService,
        temp_data_dir: Path,
    ) -> None:
        """Save overwrites existing file with same name."""
        service.save_profile_picture(1, b"old data", "pic.jpg")
        service.save_profile_picture(1, b"new data", "other.jpg")

        saved_path = temp_data_dir / "1" / "assets" / "profile_picture.jpg"
        assert saved_path.read_bytes() == b"new data"

    def test_save_profile_picture_os_error(
        self,
        service: FileStorageService,
    ) -> None:
        """Save raises ValueError on OS error."""
        with (
            patch.object(Path, "write_bytes", side_effect=OSError("disk full")),
            pytest.raises(ValueError, match="failed_to_save_file"),
        ):
            service.save_profile_picture(1, b"data", "pic.jpg")


# ---------------------------------------------------------------------------
# delete_profile_picture tests
# ---------------------------------------------------------------------------


class TestDeleteProfilePicture:
    """Tests for FileStorageService.delete_profile_picture."""

    def test_delete_profile_picture_relative_path(
        self,
        service: FileStorageService,
        temp_data_dir: Path,
    ) -> None:
        """Delete removes file using relative path."""
        # Create file first
        relative_path = service.save_profile_picture(1, b"data", "pic.jpg")
        full_path = temp_data_dir / relative_path
        assert full_path.exists()

        service.delete_profile_picture(relative_path)

        assert not full_path.exists()

    def test_delete_profile_picture_absolute_path(
        self,
        service: FileStorageService,
        tmp_path: Path,
    ) -> None:
        """Delete removes file using absolute path."""
        file_path = tmp_path / "absolute_pic.jpg"
        file_path.write_bytes(b"data")
        assert file_path.exists()

        service.delete_profile_picture(str(file_path))

        assert not file_path.exists()

    def test_delete_profile_picture_empty_path(
        self,
        service: FileStorageService,
    ) -> None:
        """Delete does nothing for empty path."""
        # Should not raise
        service.delete_profile_picture("")

    def test_delete_profile_picture_nonexistent_file(
        self,
        service: FileStorageService,
    ) -> None:
        """Delete silently handles nonexistent file."""
        # Should not raise (uses suppress)
        service.delete_profile_picture("nonexistent/path/pic.jpg")

    def test_delete_profile_picture_os_error_suppressed(
        self,
        service: FileStorageService,
        temp_data_dir: Path,
    ) -> None:
        """Delete suppresses OS errors (e.g., permission denied)."""
        relative_path = service.save_profile_picture(1, b"data", "pic.jpg")

        with patch.object(Path, "unlink", side_effect=OSError("permission denied")):
            # Should not raise due to suppress
            service.delete_profile_picture(relative_path)

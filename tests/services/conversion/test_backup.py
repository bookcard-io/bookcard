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

"""Tests for FileBackupService to achieve 100% coverage."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from fundamental.services.conversion.backup import FileBackupService


@pytest.fixture
def backup_service() -> FileBackupService:
    """Create FileBackupService instance.

    Returns
    -------
    FileBackupService
        Service instance.
    """
    return FileBackupService()


@pytest.fixture
def test_file(temp_dir: Path) -> Path:
    """Create a test file for backup operations.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory fixture.

    Returns
    -------
    Path
        Path to test file.
    """
    test_file_path = temp_dir / "test.mobi"
    test_file_path.write_text("test content")
    return test_file_path


@pytest.mark.parametrize(
    ("file_suffix", "expected_backup_suffix"),
    [
        (".mobi", ".mobi.bak"),
        (".epub", ".epub.bak"),
        (".azw3", ".azw3.bak"),
        (".pdf", ".pdf.bak"),
    ],
)
def test_backup_creates_backup_with_correct_suffix(
    backup_service: FileBackupService,
    temp_dir: Path,
    file_suffix: str,
    expected_backup_suffix: str,
) -> None:
    """Test backup creates file with correct .bak suffix.

    Parameters
    ----------
    backup_service : FileBackupService
        Backup service fixture.
    temp_dir : Path
        Temporary directory fixture.
    file_suffix : str
        Original file suffix.
    expected_backup_suffix : str
        Expected backup file suffix.
    """
    original_file = temp_dir / f"test{file_suffix}"
    original_file.write_text("test content")

    backup_path = backup_service.backup(original_file)

    assert backup_path is not None
    assert backup_path == original_file.with_suffix(file_suffix + ".bak")
    assert backup_path.exists()
    assert backup_path.read_text() == "test content"


def test_backup_returns_backup_path_on_success(
    backup_service: FileBackupService,
    test_file: Path,
) -> None:
    """Test backup returns backup path on success.

    Parameters
    ----------
    backup_service : FileBackupService
        Backup service fixture.
    test_file : Path
        Test file fixture.
    """
    backup_path = backup_service.backup(test_file)

    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path != test_file


def test_backup_returns_none_on_oserror(
    backup_service: FileBackupService,
) -> None:
    """Test backup returns None on OSError.

    Parameters
    ----------
    backup_service : FileBackupService
        Backup service fixture.
    """
    non_existent_file = Path("/non/existent/file.mobi")

    with patch("shutil.copy2", side_effect=OSError("Permission denied")):
        backup_path = backup_service.backup(non_existent_file)

    assert backup_path is None


def test_backup_returns_none_on_shutil_error(
    backup_service: FileBackupService,
    test_file: Path,
) -> None:
    """Test backup returns None on shutil.Error.

    Parameters
    ----------
    backup_service : FileBackupService
        Backup service fixture.
    test_file : Path
        Test file fixture.
    """
    with patch("shutil.copy2", side_effect=shutil.Error("Copy failed")):
        backup_path = backup_service.backup(test_file)

    assert backup_path is None


def test_restore_raises_not_implemented_error(
    backup_service: FileBackupService,
    test_file: Path,
) -> None:
    """Test restore raises NotImplementedError.

    Parameters
    ----------
    backup_service : FileBackupService
        Backup service fixture.
    test_file : Path
        Test file fixture.
    """
    backup_path = test_file.with_suffix(test_file.suffix + ".bak")

    with pytest.raises(
        NotImplementedError, match="Restore functionality not yet implemented"
    ):
        backup_service.restore(backup_path)

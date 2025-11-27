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

"""Tests for backup service."""

from pathlib import Path

from fundamental.services.epub_fixer.services.backup import (
    BackupService,
    NullBackupService,
)


def test_backup_service_init_enabled(temp_dir: Path) -> None:
    """Test BackupService initialization with backups enabled."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    assert service._enabled is True
    assert backup_dir.exists()


def test_backup_service_init_disabled(temp_dir: Path) -> None:
    """Test BackupService initialization with backups disabled."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=False)

    assert service._enabled is False
    # Directory should not be created when disabled
    assert not backup_dir.exists()


def test_backup_service_create_backup_success(temp_dir: Path) -> None:
    """Test BackupService creates backup successfully."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    # Create test file
    test_file = temp_dir / "test.epub"
    test_file.write_text("test content")

    backup_path = service.create_backup(test_file)

    assert backup_path is not None
    backup_file = Path(backup_path)
    assert backup_file.exists()
    assert backup_file.read_text() == "test content"


def test_backup_service_create_backup_disabled(temp_dir: Path) -> None:
    """Test BackupService doesn't create backup when disabled."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=False)

    test_file = temp_dir / "test.epub"
    test_file.write_text("test content")

    backup_path = service.create_backup(test_file)

    assert backup_path is None


def test_backup_service_create_backup_nonexistent(temp_dir: Path) -> None:
    """Test BackupService handles nonexistent file."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    nonexistent = temp_dir / "nonexistent.epub"

    backup_path = service.create_backup(nonexistent)

    assert backup_path is None


def test_backup_service_restore_backup_success(temp_dir: Path) -> None:
    """Test BackupService restores backup successfully."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    # Create backup
    test_file = temp_dir / "test.epub"
    test_file.write_text("original content")
    backup_path = service.create_backup(test_file)

    # Modify original
    test_file.write_text("modified content")

    # Restore
    assert backup_path is not None
    result = service.restore_backup(backup_path, test_file)

    assert result is True
    assert test_file.read_text() == "original content"


def test_backup_service_restore_backup_nonexistent(temp_dir: Path) -> None:
    """Test BackupService handles nonexistent backup."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    nonexistent_backup = temp_dir / "nonexistent_backup.epub"
    target = temp_dir / "target.epub"

    result = service.restore_backup(nonexistent_backup, target)

    assert result is False


def test_backup_service_backup_timestamp(temp_dir: Path) -> None:
    """Test BackupService creates backup with timestamp."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    test_file = temp_dir / "test.epub"
    test_file.write_text("test content")

    backup_path = service.create_backup(test_file)

    assert backup_path is not None
    backup_file = Path(backup_path)
    # Filename should include timestamp
    assert "test_" in backup_file.name
    assert backup_file.suffix == ".epub"


def test_null_backup_service_create_backup() -> None:
    """Test NullBackupService create_backup returns None."""
    service = NullBackupService()

    result = service.create_backup(Path("/any/path.epub"))

    assert result is None


def test_null_backup_service_restore_backup() -> None:
    """Test NullBackupService restore_backup returns False."""
    service = NullBackupService()

    result = service.restore_backup(Path("/backup.epub"), Path("/target.epub"))

    assert result is False


def test_backup_service_string_paths(temp_dir: Path) -> None:
    """Test BackupService accepts string paths."""
    backup_dir = temp_dir / "backups"
    service = BackupService(str(backup_dir), enabled=True)

    test_file = temp_dir / "test.epub"
    test_file.write_text("test content")

    backup_path = service.create_backup(str(test_file))

    assert backup_path is not None
    assert Path(backup_path).exists()

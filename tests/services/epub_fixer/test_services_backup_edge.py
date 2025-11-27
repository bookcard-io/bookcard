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

"""Additional edge case tests for backup service to reach 100% coverage."""

from pathlib import Path
from unittest.mock import patch

from fundamental.services.epub_fixer.services.backup import BackupService


def test_backup_service_create_backup_oserror(temp_dir: Path) -> None:
    """Test BackupService handles OSError during backup creation."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    test_file = temp_dir / "test.epub"
    test_file.write_text("test content")

    # Mock shutil.copy2 to raise OSError
    with patch("shutil.copy2", side_effect=OSError("Permission denied")):
        backup_path = service.create_backup(test_file)

        assert backup_path is None


def test_backup_service_restore_backup_oserror(temp_dir: Path) -> None:
    """Test BackupService handles OSError during restore."""
    backup_dir = temp_dir / "backups"
    service = BackupService(backup_dir, enabled=True)

    # Create backup
    test_file = temp_dir / "test.epub"
    test_file.write_text("original content")
    backup_path = service.create_backup(test_file)

    assert backup_path is not None
    backup_file = Path(backup_path)

    # Mock shutil.copy2 to raise OSError
    with patch("shutil.copy2", side_effect=OSError("Permission denied")):
        result = service.restore_backup(backup_file, test_file)

        assert result is False

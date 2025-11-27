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

"""Backup service for EPUB files.

Handles backup creation and restoration following Single Responsibility Principle.
"""

import shutil
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


class IBackupService(Protocol):
    """Protocol for backup service interface.

    Allows dependency injection and testing with mock implementations.
    """

    def create_backup(self, file_path: str | Path) -> str | None:
        """Create backup of file.

        Parameters
        ----------
        file_path : str | Path
            Path to file to backup.

        Returns
        -------
        str | None
            Path to backup file if created, None otherwise.
        """
        ...

    def restore_backup(self, backup_path: str | Path, target_path: str | Path) -> bool:
        """Restore file from backup.

        Parameters
        ----------
        backup_path : str | Path
            Path to backup file.
        target_path : str | Path
            Path to restore file to.

        Returns
        -------
        bool
            True if restoration successful, False otherwise.
        """
        ...


class BackupService:
    """Service for creating and restoring EPUB file backups.

    Parameters
    ----------
    backup_directory : str | Path
        Directory to store backups.
    enabled : bool
        Whether backups are enabled (default: True).
    """

    def __init__(self, backup_directory: str | Path, enabled: bool = True) -> None:
        """Initialize backup service.

        Parameters
        ----------
        backup_directory : str | Path
            Directory to store backups.
        enabled : bool
            Whether backups are enabled.
        """
        self._backup_directory = Path(backup_directory)
        self._enabled = enabled

        if self._enabled:
            self._backup_directory.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: str | Path) -> str | None:
        """Create backup of file with timestamp.

        Parameters
        ----------
        file_path : str | Path
            Path to file to backup.

        Returns
        -------
        str | None
            Path to backup file if created, None if disabled or failed.
        """
        if not self._enabled:
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            return None

        with suppress(OSError, ValueError):
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self._backup_directory / backup_filename

            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        return None

    def restore_backup(self, backup_path: str | Path, target_path: str | Path) -> bool:
        """Restore file from backup.

        Parameters
        ----------
        backup_path : str | Path
            Path to backup file.
        target_path : str | Path
            Path to restore file to.

        Returns
        -------
        bool
            True if restoration successful, False otherwise.
        """
        backup_path = Path(backup_path)
        target_path = Path(target_path)

        if not backup_path.exists():
            return False

        with suppress(OSError, ValueError):
            shutil.copy2(backup_path, target_path)
            return True
        return False


class NullBackupService:
    """No-op backup service for testing.

    Implements IBackupService but does nothing.
    """

    def create_backup(self, _file_path: str | Path) -> str | None:
        """Create backup (no-op).

        Parameters
        ----------
        _file_path : str | Path
            Path to file (ignored).

        Returns
        -------
        None
            Always returns None.
        """
        return None

    def restore_backup(
        self, _backup_path: str | Path, _target_path: str | Path
    ) -> bool:
        """Restore backup (no-op).

        Parameters
        ----------
        _backup_path : str | Path
            Path to backup (ignored).
        _target_path : str | Path
            Target path (ignored).

        Returns
        -------
        bool
            Always returns False.
        """
        return False

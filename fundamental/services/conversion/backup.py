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

"""File backup service for conversion operations.

Handles backup and restore of original files before conversion,
following SRP by focusing solely on file backup operations.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class FileBackupService:
    """Service for backing up and restoring files.

    Handles backup operations for original files before conversion,
    providing a clean interface for file backup management.

    Methods
    -------
    backup(path: Path) -> Path | None
        Create a backup of the file.
    restore(backup_path: Path) -> None
        Restore a file from backup (not currently implemented).
    """

    def backup(self, path: Path) -> Path | None:
        """Backup original file before conversion.

        Creates a backup in the same directory with a .bak extension.

        Parameters
        ----------
        path : Path
            Path to original file.

        Returns
        -------
        Path | None
            Path to backup file if created, None if backup failed.
        """
        try:
            # Create backup in same directory with .bak extension
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup_path)
            logger.debug("Backed up original file: %s -> %s", path, backup_path)
        except (OSError, shutil.Error) as e:
            logger.warning("Failed to backup original file %s: %s", path, e)
            return None
        else:
            return backup_path

    def restore(self, backup_path: Path) -> None:
        """Restore a file from backup.

        Parameters
        ----------
        backup_path : Path
            Path to backup file.

        Raises
        ------
        NotImplementedError
            Restore functionality not yet implemented.
        """
        msg = "Restore functionality not yet implemented"
        raise NotImplementedError(msg)

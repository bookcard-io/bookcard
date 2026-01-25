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

"""Metadata DB backup task implementation."""

import logging
import re
import shutil
import time
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.tasks.base import BaseTask

if TYPE_CHECKING:
    from bookcard.models.config import Library

logger = logging.getLogger(__name__)


class MetadataDbBackupTask(BaseTask):
    """Task for backing up library metadata databases.

    Backs up the metadata.db (or configured file) for all libraries,
    keeping a configurable number of recent backups (default 100).
    """

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute the backup task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing the database session.
        """
        session = worker_context["session"]
        library_repo = LibraryRepository(session)

        # 1. Find all configured libraries
        libraries = list(library_repo.list())
        if not libraries:
            logger.info("No libraries configured for backup.")
            return

        total_libraries = len(libraries)
        logger.info("Starting metadata backup for %d libraries", total_libraries)

        success_count = 0
        fail_count = 0

        for i, library in enumerate(libraries):
            try:
                self._backup_library(library)
                success_count += 1
            except Exception:
                logger.exception(
                    "Failed to backup library '%s' (ID: %s)", library.name, library.id
                )
                fail_count += 1

            # Update progress
            self.update_progress((i + 1) / total_libraries)

        logger.info(
            "Metadata backup completed. Success: %d, Failed: %d",
            success_count,
            fail_count,
        )
        if fail_count > 0:
            msg = f"Backup failed for {fail_count} libraries"
            raise RuntimeError(msg)

    def _backup_library(self, library: "Library") -> None:
        """Create backup for a single library and rotate old backups.

        Parameters
        ----------
        library : Library
            Library model instance.
        """
        db_path_str = library.calibre_db_path
        db_filename = library.calibre_db_file or "metadata.db"

        if not db_path_str:
            logger.warning("Library '%s' has no path configured", library.name)
            return

        db_path = Path(db_path_str) / db_filename

        if not db_path.exists() or not db_path.is_file():
            logger.warning("Database file not found at %s", db_path)
            return

        # Create backup
        timestamp = int(time.time())
        # Naming scheme: {stem}.{unix_ts}{suffix}.bk
        # e.g. metadata.1737763200.db.bk
        backup_filename = f"{db_path.stem}.{timestamp}{db_path.suffix}.bk"
        backup_path = db_path.parent / backup_filename

        logger.info("Backing up %s to %s", db_path, backup_path)
        shutil.copy2(db_path, backup_path)

        # Rotate backups
        self._rotate_backups(db_path)

    def _rotate_backups(self, db_path: Path, max_backups: int = 100) -> None:
        """Rotate backups, keeping only the most recent ones.

        Parameters
        ----------
        db_path : Path
            Path to the original database file.
        max_backups : int
            Maximum number of backups to keep.
        """
        parent_dir = db_path.parent
        stem = db_path.stem
        suffix = db_path.suffix

        # Pattern to match: {stem}.{digits}{suffix}.bk
        # We need to escape special characters in stem and suffix for regex
        escaped_stem = re.escape(stem)
        escaped_suffix = re.escape(suffix)
        pattern = re.compile(rf"^{escaped_stem}\.(\d+){escaped_suffix}\.bk$")

        backups = []

        # Scan directory for backups
        try:
            for file_path in parent_dir.iterdir():
                if not file_path.is_file():
                    continue

                match = pattern.match(file_path.name)
                if match:
                    ts = int(match.group(1))
                    backups.append((ts, file_path))
        except OSError:
            logger.warning("Failed to list backups in %s", parent_dir, exc_info=True)
            return

        # Sort by timestamp descending (newest first)
        backups.sort(key=lambda x: x[0], reverse=True)

        # Remove old backups
        if len(backups) > max_backups:
            to_remove = backups[max_backups:]
            logger.info("Removing %d old backups for %s", len(to_remove), db_path.name)

            for _, file_path in to_remove:
                with suppress(OSError):
                    file_path.unlink()

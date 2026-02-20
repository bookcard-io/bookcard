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

"""Download monitoring task implementation.

Task for monitoring active downloads via the DownloadMonitorService.
"""

import logging
import os
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select

from bookcard.database import EngineSessionFactory
from bookcard.models.config import Library
from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.services.download_monitor_service import DownloadMonitorService
from bookcard.services.pvr_import_service import PVRImportService
from bookcard.services.security import DataEncryptor
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class DownloadMonitorTask(BaseTask):
    """Task for monitoring active downloads."""

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute the download monitor task.

        Checks for completed downloads and imports them grouped by their
        target ``library_id`` so each batch is processed against the correct
        Calibre library.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing database session.
        """
        session = worker_context["session"]

        try:
            encryption_key = os.environ.get("BOOKCARD_FERNET_KEY", "")
            encryptor = DataEncryptor(encryption_key) if encryption_key else None
            service = DownloadMonitorService(session, encryptor=encryptor)
            service.check_downloads()

            # Discover distinct library_ids with pending completed downloads
            library_ids = self._get_pending_library_ids(session)

            if not library_ids:
                logger.debug("No pending completed downloads to import.")
            else:
                self._import_by_library(session, library_ids)

            # Since this is a periodic check, we mark it as 100% complete
            update_progress = worker_context.get("update_progress")
            if update_progress:
                update_progress(1.0)

        except Exception:
            logger.exception("Error executing download monitor task")
            raise

    @staticmethod
    def _get_pending_library_ids(session: Session) -> list[int]:
        """Return distinct library_ids for pending completed downloads.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        list[int]
            Distinct library IDs with pending imports.
        """
        stmt = (
            select(TrackedBook.library_id)
            .join(DownloadItem)
            .where(DownloadItem.status == DownloadItemStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.FAILED)
            .distinct()
        )
        return list(session.exec(stmt).all())

    @staticmethod
    def _import_by_library(session: Session, library_ids: list[int]) -> None:
        """Import pending downloads grouped by library.

        Parameters
        ----------
        session : Session
            Database session.
        library_ids : list[int]
            Library IDs with pending downloads.
        """
        engine = session.bind
        if not isinstance(engine, Engine):
            logger.warning("Session has no bound engine, cannot create session factory")
            return

        session_factory = EngineSessionFactory(engine)

        for library_id in library_ids:
            library = session.get(Library, library_id)
            if library is None:
                logger.warning(
                    "Library id=%d referenced by pending download no longer exists; "
                    "skipping.",
                    library_id,
                )
                continue

            import_service = PVRImportService(session, session_factory, library)
            results = import_service.import_pending_downloads()

            if results.successful > 0:
                logger.info(
                    "Imported %d pending downloads for library '%s' (id=%d)",
                    results.successful,
                    library.name,
                    library_id,
                )
            if results.failed > 0:
                logger.warning(
                    "Failed to import %d pending downloads for library '%s' (id=%d)",
                    results.failed,
                    library.name,
                    library_id,
                )

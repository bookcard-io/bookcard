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

from bookcard.database import EngineSessionFactory
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.download_monitor_service import DownloadMonitorService
from bookcard.services.pvr_import_service import PVRImportService
from bookcard.services.security import DataEncryptor
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class DownloadMonitorTask(BaseTask):
    """Task for monitoring active downloads."""

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute the download monitor task.

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

            # Process any completed downloads
            # We need the active library
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            active_library = library_service.get_active_library()

            if active_library:
                # We need to construct a session factory from the session's engine
                # The session in worker_context should be bound to an engine
                engine = session.bind
                if not engine:
                    logger.warning(
                        "Session has no bound engine, cannot create session factory"
                    )
                else:
                    session_factory = EngineSessionFactory(engine)
                    import_service = PVRImportService(
                        session, session_factory, active_library
                    )
                    results = import_service.import_pending_downloads()
                    if results.successful > 0:
                        logger.info("Imported %d pending downloads", results.successful)
                    if results.failed > 0:
                        logger.warning(
                            "Failed to import %d pending downloads", results.failed
                        )
            else:
                logger.info(
                    "No active library found. Skipping pending downloads import."
                )

            # Since this is a periodic check, we mark it as 100% complete when done
            # The next run will be a new task instance
            update_progress = worker_context.get("update_progress")
            if update_progress:
                update_progress(1.0)

        except Exception:
            logger.exception("Error executing download monitor task")
            raise

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

"""Task adapter for OpenLibrary dump ingestion.

Bridges the new architecture with the existing task system, allowing
for gradual migration without breaking existing functionality.
"""

import logging
from typing import Any

from fundamental.services.tasks.base import BaseTask
from fundamental.services.tasks.openlibrary.adapters import (
    CancellationCheckerAdapter,
    DatabaseRepositoryAdapter,
    ProgressReporterAdapter,
)
from fundamental.services.tasks.openlibrary.config import IngestionConfig
from fundamental.services.tasks.openlibrary.orchestrator import (
    OpenLibraryDumpIngestOrchestrator,
)

logger = logging.getLogger(__name__)


class OpenLibraryDumpIngestTask(BaseTask):
    """Adapter that bridges the new architecture with the existing task system.

    This class maintains compatibility with the existing task system while
    using the improved architecture internally. This allows for gradual
    migration without breaking existing functionality.

    Parameters
    ----------
    task_id : int
        Database task ID.
    user_id : int
        User ID creating the task.
    metadata : dict[str, Any]
        Task metadata. Can contain 'data_directory', 'process_authors',
        'process_works', 'process_editions', 'batch_size'.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize OpenLibrary dump ingest task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata. Can contain 'data_directory', 'process_authors',
            'process_works', 'process_editions', 'batch_size'.
        """
        super().__init__(task_id, user_id, metadata)
        self.config = IngestionConfig(
            data_directory=metadata.get("data_directory", "/data"),
            batch_size=metadata.get("batch_size", 10000),
            process_authors=metadata.get("process_authors", True),
            process_works=metadata.get("process_works", True),
            process_editions=metadata.get("process_editions", True),
        )

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute OpenLibrary dump ingestion task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.

        Raises
        ------
        Exception
            If ingestion fails.
        """
        from sqlmodel import Session  # noqa: TC002

        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        # Create adapters
        repository = DatabaseRepositoryAdapter(session)
        progress_reporter = ProgressReporterAdapter(update_progress)
        cancellation_checker = CancellationCheckerAdapter(self.check_cancelled)

        # Create and run orchestrator
        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=self.config,
            repository=repository,
            progress_reporter=progress_reporter,
            cancellation_checker=cancellation_checker,
        )

        try:
            orchestrator.run()
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            repository.rollback()
            raise

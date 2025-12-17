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

"""Library scan task implementation.

Handles scanning Calibre libraries, matching authors/books to external
data sources, and ingesting metadata.

This task only handles task-specific concerns and delegates
the actual scanning to the orchestrator.
"""

import logging
from typing import Any

from sqlmodel import Session

from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.library_scanning.scan_configuration import (
    DatabaseScanConfigurationProvider,
)
from bookcard.services.library_scanning.scan_factories import (
    PipelineContextFactory,
    RegistryDataSourceFactory,
    StandardPipelineFactory,
)
from bookcard.services.library_scanning.scan_orchestrator import (
    LibraryScanOrchestrator,
)
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class LibraryScanTask(BaseTask):
    """Task for scanning a Calibre library.

    This task only handles task-specific concerns and delegates
    the actual scanning to the orchestrator.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
        orchestrator: LibraryScanOrchestrator | None = None,
    ) -> None:
        """Initialize library scan task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing library_id and optional data_source_config.
        orchestrator : LibraryScanOrchestrator | None
            Scan orchestrator (will be created if not provided).
        """
        super().__init__(task_id, user_id, metadata)

        # Validate required metadata
        self.library_id = metadata.get("library_id")
        if not self.library_id:
            msg = "library_id is required in task metadata"
            raise ValueError(msg)

        # Extract data source configuration
        data_source_config = metadata.get("data_source_config", {})
        if isinstance(data_source_config, dict):
            self.data_source_name = data_source_config.get("name", "openlibrary")
            self.data_source_kwargs = data_source_config.get("kwargs", {})
        else:
            self.data_source_name = "openlibrary"
            self.data_source_kwargs = {}

        self.orchestrator = orchestrator

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute the library scan task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing database session and task service.
        """
        session = worker_context["session"]
        update_progress = worker_context.get("update_progress")

        def progress_callback(
            progress: float,
            metadata: dict[str, Any] | None = None,
        ) -> None:
            """Update task progress with optional metadata.

            Parameters
            ----------
            progress : float
                Progress value between 0.0 and 1.0.
            metadata : dict[str, Any] | None
                Optional metadata (stage, current_item, counts, etc.).
            """
            if update_progress:
                update_progress(progress, metadata)

        def _raise_library_id_required() -> None:
            """Raise ValueError for missing library_id."""
            msg = "library_id is required"
            raise ValueError(msg)

        try:
            # Validate library_id is present
            if not self.library_id:
                _raise_library_id_required()

            # Create orchestrator if not injected
            if not hasattr(self, "orchestrator") or not self.orchestrator:
                self.orchestrator = self._create_orchestrator(session)

            # Execute scan
            # Type assertion: library_id is guaranteed to be int after validation
            library_id = int(self.library_id)
            result = self.orchestrator.scan_library(
                library_id=library_id,
                metadata=self.metadata,
                session=session,
                progress_callback=progress_callback,
            )

            # Handle result if needed
            if not result["success"]:
                logger.error(
                    "Scan failed for library %d: %s",
                    self.library_id,
                    result.get("message", "Unknown error"),
                )

        except Exception:
            logger.exception("Error executing library scan task")
            raise

    def _create_orchestrator(
        self,
        session: Session,
    ) -> LibraryScanOrchestrator:
        """Create default orchestrator with standard dependencies.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        LibraryScanOrchestrator
            Configured scan orchestrator.
        """
        library_repo = LibraryRepository(session)
        config_provider = DatabaseScanConfigurationProvider(session)
        data_source_factory = RegistryDataSourceFactory()
        pipeline_factory = StandardPipelineFactory()
        context_factory = PipelineContextFactory(library_repo)

        return LibraryScanOrchestrator(
            config_provider=config_provider,
            data_source_factory=data_source_factory,
            pipeline_factory=pipeline_factory,
            context_factory=context_factory,
        )

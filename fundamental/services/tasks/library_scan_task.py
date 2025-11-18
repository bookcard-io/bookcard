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
"""

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.models.config import Library

from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.crawl import CrawlStage
from fundamental.services.library_scanning.pipeline.executor import PipelineExecutor
from fundamental.services.library_scanning.pipeline.ingest import IngestStage
from fundamental.services.library_scanning.pipeline.link import LinkStage
from fundamental.services.library_scanning.pipeline.match import MatchStage
from fundamental.services.library_scanning.pipeline.score import ScoreStage
from fundamental.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class LibraryScanTask(BaseTask):
    """Task for scanning a Calibre library.

    Crawls the library, matches authors/books to external data sources,
    ingests metadata, creates linkages, and scores similarities.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
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
        """
        super().__init__(task_id, user_id, metadata)
        self.library_id = metadata.get("library_id")
        if not self.library_id:
            msg = "library_id is required in task metadata"
            raise ValueError(msg)

        # Data source configuration
        data_source_config = metadata.get("data_source_config", {})
        self.data_source_name = data_source_config.get("name", "openlibrary")
        self.data_source_kwargs = data_source_config.get("kwargs", {})

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute the library scan task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing database session and task service.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context.get("update_progress")

        def _raise_library_id_error() -> None:
            """Raise ValueError for missing library_id."""
            error_msg = "library_id is required"
            raise ValueError(error_msg)

        def _raise_library_not_found_error(library_id: int | None) -> None:
            """Raise ValueError for library not found."""
            if library_id is None:
                error_msg = "Library not found (library_id is None)"
            else:
                error_msg = f"Library {library_id} not found"
            raise ValueError(error_msg)

        try:
            # Get library
            if self.library_id is None:
                _raise_library_id_error()

            # Type assertion: library_id is guaranteed to be int after check
            library_id = cast("int", self.library_id)

            library_repo = LibraryRepository(session)
            library = library_repo.get(library_id)

            if not library:
                _raise_library_not_found_error(library_id)

            # Type assertion: library is guaranteed to be Library after check
            # (library is non-None after the check above)
            library_obj = cast("Library", library)

            # Create data source
            data_source = DataSourceRegistry.create_source(
                self.data_source_name,
                **self.data_source_kwargs,
            )

            # Create pipeline context
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

            context = PipelineContext(
                library_id=library_id,
                library=library_obj,
                session=session,
                data_source=data_source,
                progress_callback=progress_callback,
            )

            # Create pipeline stages
            stages = [
                CrawlStage(),
                MatchStage(),
                IngestStage(),
                LinkStage(),
                ScoreStage(),
            ]

            # Create pipeline executor
            executor = PipelineExecutor(
                stages=stages,
                progress_callback=progress_callback,
            )

            # Execute pipeline
            result = executor.execute(context)

            if result["success"]:
                logger.info(
                    "Library scan completed successfully for library %d",
                    self.library_id,
                )
            else:
                logger.warning(
                    "Library scan completed with errors for library %d: %s",
                    self.library_id,
                    result.get("message", "Unknown error"),
                )

        except Exception:
            logger.exception("Error executing library scan task")
            raise

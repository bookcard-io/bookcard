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

"""Deduplicate worker for merging duplicate authors."""

import logging
from collections.abc import Sequence
from typing import Any

from fundamental.database import create_db_engine, get_session
from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.deduplicate import DeduplicateStage
from fundamental.services.library_scanning.workers.base import BaseWorker
from fundamental.services.library_scanning.workers.progress import JobProgressTracker
from fundamental.services.library_scanning.workers.task_tracker import ScanTaskTracker
from fundamental.services.messaging.base import MessageBroker
from fundamental.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class NoOpDataSource(BaseDataSource):
    """Dummy data source for context.

    Used when a data source is required but not actually needed
    (e.g., for stages that only use database operations).
    """

    def search_author(self, query: str) -> list[AuthorData]:  # noqa: ARG002
        """Search for authors (no-op).

        Parameters
        ----------
        query : str
            Search query (unused).

        Returns
        -------
        list[AuthorData]
            Empty list.
        """
        return []

    def get_author(self, key: str) -> AuthorData | None:  # noqa: ARG002
        """Get author by key (no-op).

        Parameters
        ----------
        key : str
            Author key (unused).

        Returns
        -------
        AuthorData | None
            None.
        """
        return None

    def search_book(
        self,
        title: str | None = None,  # noqa: ARG002
        isbn: str | None = None,  # noqa: ARG002
        authors: Sequence[str] | None = None,  # noqa: ARG002
    ) -> Sequence[BookData]:
        """Search for books (no-op).

        Parameters
        ----------
        title : str | None
            Book title (unused).
        isbn : str | None
            ISBN (unused).
        authors : Sequence[str] | None
            Author names (unused).

        Returns
        -------
        Sequence[BookData]
            Empty sequence.
        """
        return []

    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:  # noqa: ARG002
        """Get book by key (no-op).

        Parameters
        ----------
        key : str
            Book key (unused).
        skip_authors : bool
            Whether to skip authors (unused).

        Returns
        -------
        BookData | None
            None.
        """
        return None

    @property
    def name(self) -> str:
        """Get data source name.

        Returns
        -------
        str
            Data source name.
        """
        return "noop"


class DeduplicateWorker(BaseWorker):
    """Worker that runs deduplication."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "deduplicate_jobs",
        output_topic: str = "score_jobs",
        min_name_similarity: float = 0.85,
    ) -> None:
        """Initialize deduplicate worker."""
        super().__init__(broker, input_topic, output_topic)
        self.min_name_similarity = min_name_similarity
        self.engine = create_db_engine()

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a deduplication job.

        Parameters
        ----------
        payload : dict[str, Any]
            Job payload with 'library_id'.

        Returns
        -------
        dict[str, Any] | None
            Payload to trigger next stage, or None.
        """
        library_id = payload.get("library_id")
        if not library_id:
            logger.error("Invalid deduplicate payload: %s", payload)
            return None

        task_id = payload.get("task_id")
        logger.info(
            "DeduplicateWorker: Starting deduplication for library %s (task: %s)",
            library_id,
            task_id,
        )

        if task_id and isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            if tracker.is_cancelled(task_id):
                logger.info("Task %d cancelled, skipping deduplication", task_id)
                return None

        with get_session(self.engine) as session:
            library_repo = LibraryRepository(session)
            library = library_repo.get(library_id)

            if not library:
                logger.error("Library %s not found", library_id)
                return None

            # Create context (some fields like data_source are unused by DeduplicateStage)
            context = PipelineContext(
                library_id=library_id,
                library=library,
                session=session,
                data_source=NoOpDataSource(),
            )

            stage = DeduplicateStage(min_name_similarity=self.min_name_similarity)

            try:
                result = stage.execute(context)
                if result.success:
                    logger.info("Deduplication completed: %s", result.message)
                    # Pass task_id to next stage
                    return payload.copy()  # Trigger next stage
                logger.warning(
                    "Deduplication completed with issues: %s", result.message
                )
            except Exception:
                if task_id:
                    task_tracker = ScanTaskTracker()
                    task_tracker.fail_task(task_id, "Deduplication failed")
                logger.exception("Deduplication failed for library %s", library_id)
                raise

        return None

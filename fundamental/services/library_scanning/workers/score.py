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

"""Score worker for calculating author similarities."""

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
from fundamental.services.library_scanning.pipeline.score import ScoreStage
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


class ScoreWorker(BaseWorker):
    """Worker that runs scoring."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "score_jobs",
        output_topic: str = "completion_jobs",
        min_similarity: float = 0.2,
        stale_data_max_age_days: int | None = None,
    ) -> None:
        """Initialize score worker."""
        super().__init__(broker, input_topic, output_topic)
        self.min_similarity = min_similarity
        self.stale_data_max_age_days = stale_data_max_age_days
        self.engine = create_db_engine()

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a score job.

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
            logger.error("Invalid score payload: %s", payload)
            return None

        task_id = payload.get("task_id")

        if task_id and isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            if tracker.is_cancelled(task_id):
                logger.info("Task %d cancelled, skipping scoring", task_id)
                return None

        logger.info("Starting scoring for library %s", library_id)

        with get_session(self.engine) as session:
            library_repo = LibraryRepository(session)
            library = library_repo.get(library_id)

            if not library:
                logger.error("Library %s not found", library_id)
                return None

            context = PipelineContext(
                library_id=library_id,
                library=library,
                session=session,
                data_source=NoOpDataSource(),
            )

            stage = ScoreStage(
                min_similarity=self.min_similarity,
                stale_data_max_age_days=self.stale_data_max_age_days,
            )

            try:
                result = stage.execute(context)
                logger.info("Scoring result: %s", result.message)

                if result.success and self.output_topic:
                    # Always publish to completion topic to trigger completion worker
                    # Pass task_id to completion worker
                    return payload.copy()
            except Exception:
                if task_id:
                    task_tracker = ScanTaskTracker()
                    task_tracker.fail_task(task_id, "Scoring failed")
                logger.exception("Scoring failed for library %s", library_id)
                raise

        return None

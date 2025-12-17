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

"""Crawl worker for scanning Calibre libraries."""

import logging
from typing import Any

from sqlmodel import select

from bookcard.models.core import Author
from bookcard.repositories import CalibreBookRepository
from bookcard.services.library_scanning.workers.base import BaseWorker
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.library_scanning.workers.task_tracker import ScanTaskTracker
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class CrawlWorker(BaseWorker):
    """Worker that crawls Calibre libraries and emits authors."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "scan_jobs",
        output_topic: str = "match_queue",
    ) -> None:
        """Initialize crawl worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str
            Topic to listen for scan jobs.
        output_topic : str
            Topic to publish found authors to.
        """
        super().__init__(broker, input_topic, output_topic)

    def _check_task_cancelled(self, task_id: int) -> bool:
        """Check if task is cancelled.

        Parameters
        ----------
        task_id : int
            Task ID.

        Returns
        -------
        bool
            True if cancelled.
        """
        if isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            if tracker.is_cancelled(task_id):
                logger.info("Scan task %d cancelled", task_id)
                return True
        return False

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a scan job.

        Parameters
        ----------
        payload : dict[str, Any]
            Scan job payload. Must contain 'library_id' and 'calibre_db_path'.

        Returns
        -------
        dict[str, Any] | None
            None (emits multiple messages manually).
        """
        library_id = payload.get("library_id")
        calibre_db_path = payload.get("calibre_db_path")

        if not library_id or not calibre_db_path:
            logger.error("Invalid scan job payload: %s", payload)
            return None

        task_id = payload.get("task_id")
        logger.info("Starting crawl for library %s at %s", library_id, calibre_db_path)

        # Start task tracking if task_id is provided
        if task_id:
            task_tracker = ScanTaskTracker()
            task_tracker.start_task(task_id)

            # Check for cancellation
            if self._check_task_cancelled(task_id):
                return None

        try:
            repo = CalibreBookRepository(calibre_db_path)
            with repo.get_session() as session:
                # Fetch authors
                stmt = select(Author)
                all_authors = session.exec(stmt).all()
                total_authors_count = len(all_authors)

                # Initialize progress tracker
                if isinstance(self.broker, RedisBroker):
                    tracker = JobProgressTracker(self.broker)
                    tracker.initialize_job(library_id, total_authors_count, task_id)

                    if total_authors_count == 0:
                        # If no authors, we are done immediately.
                        # Trigger scoring directly as there is no work to flow down.
                        logger.info("No authors found, skipping to scoring")
                        self.broker.publish(
                            "score_jobs",
                            {"library_id": library_id, "task_id": task_id},
                        )
                        return None

                for author in all_authors:
                    # Check cancellation inside loop
                    if task_id and self._check_task_cancelled(task_id):
                        return None

                    # Emit author for matching
                    # We need to serialize the author. SQLModel.model_dump() is useful.
                    author_data = author.model_dump()

                    message = {
                        "task_id": task_id,
                        "library_id": library_id,
                        "author": author_data,
                        "source": "crawl_worker",
                    }

                    if self.output_topic:
                        self.broker.publish(self.output_topic, message)

            logger.info("Finished crawl for library %s", library_id)

        except Exception:
            logger.exception("Failed to crawl library %s", library_id)
            raise

        return None

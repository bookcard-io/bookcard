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

"""Completion worker for logging scan completion."""

import logging
from typing import Any

from bookcard.services.library_scanning.workers.base import BaseWorker
from bookcard.services.library_scanning.workers.task_tracker import ScanTaskTracker
from bookcard.services.messaging.base import MessageBroker

logger = logging.getLogger(__name__)


class CompletionWorker(BaseWorker):
    """Worker that logs scan completion."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "completion_jobs",
        output_topic: str | None = None,
    ) -> None:
        """Initialize completion worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str
            Topic to listen for completion events.
        output_topic : str | None
            Optional output topic (not used for completion worker).
        """
        super().__init__(broker, input_topic, output_topic)

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a completion event.

        Parameters
        ----------
        payload : dict[str, Any]
            Job payload with 'library_id' and 'task_id'.

        Returns
        -------
        dict[str, Any] | None
            None (end of pipeline).
        """
        library_id = payload.get("library_id")
        task_id = payload.get("task_id")

        if not library_id:
            logger.error("Invalid completion payload: %s", payload)
            return None

        logger.info(
            "CompletionWorker: Processing completion for library %s (task: %s)",
            library_id,
            task_id,
        )

        # Mark task as complete
        if task_id:
            task_tracker = ScanTaskTracker()
            task_tracker.complete_task(task_id, {"library_id": library_id})

        logger.info("=" * 80)
        logger.info(
            "Library scan COMPLETE for library %s (task_id: %s)",
            library_id,
            task_id,
        )
        logger.info(
            "All stages completed: Crawl -> Match -> Ingest -> Link -> Deduplicate -> Score",
        )
        logger.info("=" * 80)

        return None

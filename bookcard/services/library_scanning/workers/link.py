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

"""Link worker for linking authors to library context."""

import logging
from typing import Any

from bookcard.database import create_db_engine, get_session
from bookcard.services.library_scanning.pipeline.link import LinkStageFactory
from bookcard.services.library_scanning.workers.base import BaseWorker
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.library_scanning.workers.serialization import (
    deserialize_match_result,
)
from bookcard.services.library_scanning.workers.task_tracker import ScanTaskTracker
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class LinkWorker(BaseWorker):
    """Worker that links matched authors to local library."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "link_queue",
        output_topic: str | None = None,  # End of per-item pipeline
        completion_topic: str = "score_jobs",
    ) -> None:
        """Initialize link worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str
            Topic to listen for ingested authors.
        output_topic : str | None
            Optional output topic (e.g., for deduplication trigger).
        completion_topic : str
            Topic to publish to if this worker finishes the last item of a job.
        """
        super().__init__(broker, input_topic, output_topic)
        self.completion_topic = completion_topic
        self.engine = create_db_engine()

    def _check_completion(
        self,
        library_id: int,
        task_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Check if job is complete and trigger next stage if so.

        Parameters
        ----------
        library_id : int
            Library ID.
        task_id : int | None
            Optional task ID (if not provided, will be retrieved from Redis).
        payload : dict[str, Any] | None
            Optional payload to pass through single-author mode flags.
        """
        if isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            # Get task_id BEFORE marking as processed (keys may be deleted)
            if task_id is None:
                task_id = tracker.get_task_id(library_id)
            if tracker.mark_item_processed(library_id):
                # Mark link stage as complete
                if task_id:
                    task_tracker = ScanTaskTracker()
                    task_tracker.update_stage_progress(task_id, "link", 1.0)
                # Pass through single-author mode flags if present
                completion_payload = {"library_id": library_id, "task_id": task_id}
                if payload:
                    if payload.get("single_author_mode"):
                        completion_payload["single_author_mode"] = True
                    target_id = payload.get("target_author_metadata_id")
                    if target_id:
                        completion_payload["target_author_metadata_id"] = target_id
                self.broker.publish(
                    self.completion_topic,
                    completion_payload,
                )

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a link request.

        Parameters
        ----------
        payload : dict[str, Any]
            Must contain 'match_result' and 'library_id'.

        Returns
        -------
        dict[str, Any] | None
            None (end of pipeline) or payload if output topic set.
        """
        match_result_dict = payload.get("match_result")
        library_id = payload.get("library_id")
        task_id = payload.get("task_id")

        if not match_result_dict or not library_id:
            logger.error("Invalid link payload: %s", payload)
            # Can't check completion because we don't have library_id
            return None

        # Extract author info early for logging
        author_name = match_result_dict.get("matched_entity", {}).get("name", "Unknown")
        author_key = match_result_dict.get("matched_entity", {}).get("key", "Unknown")
        logger.info(
            "LinkWorker: Processing author %s (%s) (library: %s, task: %s)",
            author_name,
            author_key,
            library_id,
            task_id,
        )

        # Mark link stage as started (idempotent - only first item triggers this)
        if task_id and isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            if tracker.mark_stage_started(library_id, "link"):
                task_tracker = ScanTaskTracker()
                task_tracker.update_stage_progress(task_id, "link", 0.0)

        try:
            match_result = deserialize_match_result(match_result_dict)
        except Exception:
            logger.exception("Failed to validate match result: %s", match_result_dict)
            self._check_completion(library_id, task_id, payload)
            return None

        with get_session(self.engine) as session:
            components = LinkStageFactory.create_components(session=session)
            mapping_service = components["mapping_service"]

            try:
                result = mapping_service.create_or_update_mapping(
                    match_result, library_id
                )

                if result:
                    _mapping, was_created = result
                    action = "Created" if was_created else "Updated"
                    logger.info(
                        "%s mapping for author %s (Calibre ID: %s)",
                        action,
                        match_result.matched_entity.name,
                        match_result.calibre_author_id,
                    )
                    # Mark completion - LinkWorker is the end of per-item pipeline
                    self._check_completion(library_id, task_id, payload)
                    if self.output_topic:
                        # Pass task_id through if present
                        return payload
                    return None
                logger.warning(
                    "Failed to link author %s (Calibre ID: %s)",
                    match_result.matched_entity.name,
                    match_result.calibre_author_id,
                )
                # Mark completion even on failure (item is done processing)
                self._check_completion(library_id, task_id, payload)
            except Exception:
                logger.exception(
                    "Error linking author %s", match_result.matched_entity.name
                )
                # Mark completion even on error (item is done processing)
                self._check_completion(library_id, task_id, payload)
                raise
            else:
                return None

        # If we get here, something went wrong - mark completion to avoid hanging
        self._check_completion(library_id, task_id)
        return None

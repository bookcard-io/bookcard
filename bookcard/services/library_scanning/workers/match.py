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

"""Match worker for matching authors against external sources."""

import dataclasses
import logging
from typing import Any

from pydantic import ValidationError

from bookcard.database import create_db_engine, get_session
from bookcard.models.core import Author
from bookcard.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from bookcard.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from bookcard.services.library_scanning.matching.types import MatchResult
from bookcard.services.library_scanning.workers.base import BaseWorker
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class MatchWorker(BaseWorker):
    """Worker that matches authors to external data sources."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "match_queue",
        output_topic: str = "ingest_queue",
        min_confidence: float = 0.5,
        stale_data_max_age_days: int | None = None,
        data_source_name: str = "openlibrary",
        completion_topic: str = "score_jobs",
    ) -> None:
        """Initialize match worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str
            Topic to listen for authors.
        output_topic : str
            Topic to publish match results to.
        min_confidence : float
            Minimum confidence score.
        stale_data_max_age_days : int | None
            Max age of existing mappings.
        data_source_name : str
            Name of data source to use.
        """
        super().__init__(broker, input_topic, output_topic)
        self.min_confidence = min_confidence
        self.stale_data_max_age_days = stale_data_max_age_days
        self.engine = create_db_engine()
        self.orchestrator = MatchingOrchestrator(min_confidence=min_confidence)
        self.completion_topic = completion_topic

        # Create data source (assume no rate limit delay for worker for now, or config it)
        # Pass engine for openlibrary_dump data source
        kwargs = {}
        if data_source_name == "openlibrary_dump":
            kwargs["engine"] = self.engine
        self.data_source = DataSourceRegistry.create_source(data_source_name, **kwargs)

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
                # Pass through single-author mode flags if present
                completion_payload = {"library_id": library_id, "task_id": task_id}
                if payload:
                    if payload.get("single_author_mode"):
                        completion_payload["single_author_mode"] = True
                    target_id = payload.get("target_author_metadata_id")
                    if target_id:
                        completion_payload["target_author_metadata_id"] = target_id
                self.broker.publish(self.completion_topic, completion_payload)

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process an author match request.

        Parameters
        ----------
        payload : dict[str, Any]
            Must contain 'author' dict and 'library_id'.

        Returns
        -------
        dict[str, Any] | None
            Match result payload or None if skipped/no match.
        """
        author_data, library_id, task_id = self._extract_and_log_payload(payload)
        if author_data is None or library_id is None:
            return None

        if self._is_cancelled(library_id, task_id, payload):
            return None

        try:
            author = Author.model_validate(author_data)
        except ValidationError:
            logger.exception("Failed to validate author data: %s", author_data)
            return None

        force_rematch = payload.get("force_rematch", False)
        openlibrary_key = payload.get("openlibrary_key")

        try:
            match_result = self._perform_match(
                author=author,
                library_id=library_id,
                force_rematch=force_rematch,
                openlibrary_key=openlibrary_key,
            )

            if match_result:
                return self._build_match_result_payload(
                    match_result=match_result,
                    author=author,
                    library_id=library_id,
                    task_id=task_id,
                    payload=payload,
                )

            self._handle_no_match(author, library_id, task_id, payload)
        except Exception:
            logger.exception("Error matching author %s", author.name)
            # On error, we also mark as processed (failed but done) to avoid hanging the job
            self._check_completion(library_id, task_id, payload)
            raise
        else:
            return None

    def _extract_and_log_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, int | None, int | None]:
        """Extract core fields from payload and log the start of processing.

        Parameters
        ----------
        payload : dict[str, Any]
            Raw payload from message broker.

        Returns
        -------
        tuple[dict[str, Any] | None, int | None, int | None]
            Tuple of (author_data, library_id, task_id). Author or library may
            be None for invalid payloads (already logged).
        """
        author_data = payload.get("author")
        library_id = payload.get("library_id")
        task_id = payload.get("task_id")

        if not author_data or not library_id:
            logger.error("Invalid match payload: %s", payload)
            return None, None, task_id

        author_name = author_data.get("name", "Unknown")
        logger.info(
            "MatchWorker: Processing author %s (library: %s, task: %s)",
            author_name,
            library_id,
            task_id,
        )
        return author_data, int(library_id), task_id

    def _is_cancelled(
        self,
        library_id: int | None,
        task_id: int | None,
        payload: dict[str, Any],
    ) -> bool:
        """Check whether the job is cancelled and mark completion if so.

        Parameters
        ----------
        library_id : int | None
            Library identifier from payload.
        task_id : int | None
            Optional task identifier.
        payload : dict[str, Any]
            Payload for passing through completion if needed.

        Returns
        -------
        bool
            True if job is cancelled and processing should stop, False otherwise.
        """
        if (
            not task_id
            or library_id is None
            or not isinstance(self.broker, RedisBroker)
        ):
            return False

        tracker = JobProgressTracker(self.broker)
        tracker.mark_stage_started(library_id, "match")

        if tracker.is_cancelled(task_id):
            logger.debug("Task %d cancelled, skipping match", task_id)
            self._check_completion(library_id, task_id, payload)
            return True

        return False

    def _perform_match(
        self,
        author: Author,
        library_id: int,
        force_rematch: bool,
        openlibrary_key: str | None,
    ) -> MatchResult | None:
        """Execute match orchestration and return MatchResult, if any.

        Parameters
        ----------
        author : Author
            Calibre author to match.
        library_id : int
            Library identifier.
        force_rematch : bool
            Whether to force rematching even if a fresh mapping exists.
        openlibrary_key : str | None
            Optional specific OpenLibrary key to match against.

        Returns
        -------
        MatchResult | None
            Match result if a new match was found, otherwise None.
        """
        with get_session(self.engine) as session:
            return self.orchestrator.process_match_request(
                session=session,
                author=author,
                library_id=library_id,
                data_source=self.data_source,
                force_rematch=force_rematch,
                openlibrary_key=openlibrary_key,
                stale_data_max_age_days=self.stale_data_max_age_days,
            )

    def _build_match_result_payload(
        self,
        match_result: MatchResult,
        author: Author,
        library_id: int,
        task_id: int | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Build outgoing payload for a successful match result."""
        result_dict = dataclasses.asdict(match_result)

        result: dict[str, Any] = {
            "task_id": task_id,
            "library_id": library_id,
            "match_result": result_dict,
            "calibre_author_id": author.id,
            "author_name": author.name,
        }

        if payload.get("single_author_mode"):
            result["single_author_mode"] = True
            target_id = payload.get("target_author_metadata_id")
            if target_id:
                result["target_author_metadata_id"] = target_id

        return result

    def _handle_no_match(
        self,
        author: Author,
        library_id: int,
        task_id: int | None,
        payload: dict[str, Any],
    ) -> None:
        """Handle completion logic when no match result is returned."""
        # If no match_result (skipped or unmatched handled internally),
        # check completion and return None
        # For unmatched authors in single-author mode, we need to get the author_metadata_id
        # from the mapping that was just created
        target_author_metadata_id = None
        if payload.get("single_author_mode") and author.id:
            from bookcard.services.library_scanning.pipeline.link_components import (
                AuthorMappingRepository,
            )

            with get_session(self.engine) as lookup_session:
                mapping_repo = AuthorMappingRepository(lookup_session)
                mapping = mapping_repo.find_by_calibre_author_id_and_library(
                    author.id,
                    library_id,
                )
                if mapping:
                    target_author_metadata_id = mapping.author_metadata_id
                    payload["target_author_metadata_id"] = target_author_metadata_id

        self._check_completion(library_id, task_id, payload)

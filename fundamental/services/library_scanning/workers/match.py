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
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from fundamental.database import create_db_engine, get_session
from fundamental.models.author_metadata import AuthorMetadata
from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
    MappingData,
)
from fundamental.services.library_scanning.workers.base import BaseWorker
from fundamental.services.library_scanning.workers.progress import JobProgressTracker
from fundamental.services.messaging.base import MessageBroker
from fundamental.services.messaging.redis_broker import RedisBroker

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

    def _check_completion(self, library_id: int, task_id: int | None = None) -> None:
        """Check if job is complete and trigger next stage if so.

        Parameters
        ----------
        library_id : int
            Library ID.
        task_id : int | None
            Optional task ID (if not provided, will be retrieved from Redis).
        """
        if isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            # Get task_id BEFORE marking as processed (keys may be deleted)
            if task_id is None:
                task_id = tracker.get_task_id(library_id)
            if tracker.mark_item_processed(library_id):
                self.broker.publish(
                    self.completion_topic,
                    {"library_id": library_id, "task_id": task_id},
                )

    def _should_skip_match(
        self,
        calibre_author_id: int,
        library_id: int,
    ) -> bool:
        """Check if match should be skipped."""
        if self.stale_data_max_age_days is None:
            return False

        with get_session(self.engine) as session:
            mapping_repo = AuthorMappingRepository(session)
            existing_mapping = mapping_repo.find_by_calibre_author_id_and_library(
                calibre_author_id,
                library_id,
            )

            if not existing_mapping:
                return False

            now = datetime.now(UTC)
            mapping_date = existing_mapping.updated_at or existing_mapping.created_at
            if mapping_date.tzinfo is None:
                mapping_date = mapping_date.replace(tzinfo=UTC)

            days_since = (now - mapping_date).days
            return days_since < self.stale_data_max_age_days

    def _handle_unmatched_author(
        self, author: Author, library_id: int, task_id: int | None
    ) -> None:
        """Handle case where no match is found for an author.

        Creates an AuthorMetadata record with openlibrary_key=None and links it.
        """
        if author.id is None:
            msg = "Author ID cannot be None for unmatched handling"
            raise ValueError(msg)

        logger.info("No match found for %s - creating unmatched record", author.name)

        with get_session(self.engine) as session:
            # Create unmatched metadata
            unmatched_metadata = AuthorMetadata(
                name=author.name,
                openlibrary_key=None,
            )
            session.add(unmatched_metadata)
            session.flush()

            if unmatched_metadata.id is None:
                msg = "Failed to generate ID for unmatched metadata"
                raise ValueError(msg)

            # Create or update mapping
            mapping_repo = AuthorMappingRepository(session)
            existing_mapping = mapping_repo.find_by_calibre_author_id_and_library(
                author.id, library_id
            )

            mapping_data = MappingData(
                library_id=library_id,
                calibre_author_id=author.id,
                author_metadata_id=unmatched_metadata.id,
                confidence_score=0.0,
                matched_by="unmatched",
            )

            if existing_mapping:
                mapping_repo.update(existing_mapping, mapping_data)
            else:
                mapping_repo.create(mapping_data)

            session.commit()

        self._check_completion(library_id, task_id)

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
        author_data = payload.get("author")
        library_id = payload.get("library_id")
        task_id = payload.get("task_id")

        if not author_data or not library_id:
            logger.error("Invalid match payload: %s", payload)
            return None

        author_name = author_data.get("name", "Unknown")
        logger.info(
            "MatchWorker: Processing author %s (library: %s, task: %s)",
            author_name,
            library_id,
            task_id,
        )

        # Mark match stage as started (idempotent - only first item triggers this)
        if task_id and isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            tracker.mark_stage_started(library_id, "match")

            if tracker.is_cancelled(task_id):
                logger.debug("Task %d cancelled, skipping match", task_id)
                # Mark as processed to drain the queue
                self._check_completion(library_id, task_id)
                return None

        try:
            author = Author.model_validate(author_data)
        except ValidationError:
            logger.exception("Failed to validate author data: %s", author_data)
            return None

        if author.id is None:
            logger.warning("Author has no ID: %s", author.name)
            self._check_completion(library_id, task_id)
            return None

        # Check staleness
        if self._should_skip_match(author.id, library_id):
            logger.info(
                "Skipping match for fresh author %s (ID: %s)", author.name, author.id
            )
            self._check_completion(library_id, task_id)
            return None

        # Perform match
        try:
            match_result = self.orchestrator.match(author, self.data_source)

            if match_result:
                # Add calibre ID to result for tracking
                match_result.calibre_author_id = author.id

                logger.info(
                    "Matched author %s -> %s (confidence: %.2f)",
                    author.name,
                    match_result.matched_entity.name,
                    match_result.confidence_score,
                )

                # Serialize match result (MatchResult is a dataclass)
                result_dict = dataclasses.asdict(match_result)

                return {
                    "task_id": task_id,
                    "library_id": library_id,
                    "match_result": result_dict,
                    "calibre_author_id": author.id,
                    "author_name": author.name,
                }

            self._handle_unmatched_author(author, library_id, task_id)
        except Exception:
            logger.exception("Error matching author %s", author.name)
            # On error, we also mark as processed (failed but done) to avoid hanging the job
            self._check_completion(library_id, task_id)
            raise
        else:
            return None

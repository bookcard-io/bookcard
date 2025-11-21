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

"""Ingest worker for fetching and storing author metadata."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from fundamental.database import create_db_engine, get_session
from fundamental.models.author_metadata import AuthorMetadata
from fundamental.models.config import LibraryScanProviderConfig
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.pipeline.ingest import IngestStageFactory
from fundamental.services.library_scanning.workers.base import BaseWorker
from fundamental.services.library_scanning.workers.progress import JobProgressTracker
from fundamental.services.library_scanning.workers.serialization import (
    deserialize_match_result,
)
from fundamental.services.messaging.base import MessageBroker
from fundamental.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class IngestWorker(BaseWorker):
    """Worker that ingests author metadata."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str = "ingest_queue",
        output_topic: str = "link_queue",
        data_source_name: str = "openlibrary",
        stale_data_max_age_days: int | None = None,
        stale_data_refresh_interval_days: int | None = None,
        completion_topic: str = "score_jobs",
    ) -> None:
        """Initialize ingest worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str
            Topic to listen for match results.
        output_topic : str
            Topic to publish to link queue.
        data_source_name : str
            Data source name.
        stale_data_max_age_days : int | None
            Max age for stale data.
        stale_data_refresh_interval_days : int | None
            Refresh interval.
        completion_topic : str
            Topic to publish to if this worker finishes the last item of a job.
        """
        super().__init__(broker, input_topic, output_topic)
        self.data_source_name = data_source_name
        self.stale_data_max_age_days = stale_data_max_age_days
        self.stale_data_refresh_interval_days = stale_data_refresh_interval_days
        self.completion_topic = completion_topic
        self.engine = create_db_engine()

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

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process an ingest request.

        Parameters
        ----------
        payload : dict[str, Any]
            Must contain 'match_result' and 'library_id'.

        Returns
        -------
        dict[str, Any] | None
            Payload for link queue.
        """
        match_result_dict = payload.get("match_result")
        library_id = payload.get("library_id")
        task_id = payload.get("task_id")

        if not match_result_dict or not library_id:
            logger.error("Invalid ingest payload: %s", payload)
            return None

        # Extract author info early for logging
        author_name = match_result_dict.get("matched_entity", {}).get("name", "Unknown")
        author_key = match_result_dict.get("matched_entity", {}).get("key", "Unknown")
        logger.info(
            "IngestWorker: Processing author %s (%s) (library: %s, task: %s)",
            author_name,
            author_key,
            library_id,
            task_id,
        )

        # Mark ingest stage as started (idempotent - only first item triggers this)
        if task_id and isinstance(self.broker, RedisBroker):
            tracker = JobProgressTracker(self.broker)
            tracker.mark_stage_started(library_id, "ingest")

            if tracker.is_cancelled(task_id):
                logger.debug("Task %d cancelled, skipping ingest", task_id)
                # Mark as processed to drain the queue
                self._check_completion(library_id, task_id)
                return None

        try:
            # Reconstruct MatchResult
            match_result = deserialize_match_result(match_result_dict)
        except (KeyError, TypeError, ValueError):
            logger.exception("Failed to validate match result: %s", match_result_dict)
            self._check_completion(library_id, task_id)
            return None

        author_key = match_result.matched_entity.key
        author_name = match_result.matched_entity.name

        with get_session(self.engine) as session:
            # Load provider config to get stale data settings
            provider_config = self._load_provider_config(session, self.data_source_name)
            stale_max_age = (
                provider_config.stale_data_max_age_days
                if provider_config
                else self.stale_data_max_age_days
            )
            stale_refresh_interval = (
                provider_config.stale_data_refresh_interval_days
                if provider_config
                else self.stale_data_refresh_interval_days
            )
            max_works_per_author = (
                provider_config.max_works_per_author if provider_config else 1000
            )

            # Check if we should skip fetching due to fresh data
            if self._should_skip_fetch(
                session, author_key, stale_max_age, stale_refresh_interval
            ):
                logger.info(
                    "Skipping fetch for author %s (%s) - data is fresh",
                    author_name,
                    author_key,
                )
                # Still pass through to link worker even if we skip fetch
                # Do NOT mark completion here, LinkWorker will do it
                return payload

            # Create data source
            # Pass engine for openlibrary_dump data source
            kwargs = {}
            if self.data_source_name == "openlibrary_dump":
                kwargs["engine"] = self.engine
            data_source = DataSourceRegistry.create_source(
                self.data_source_name, **kwargs
            )

            # Create components
            components = IngestStageFactory.create_components(
                session=session,
                data_source=data_source,
                max_works_per_author=max_works_per_author,
            )

            author_fetcher = components["author_fetcher"]
            ingestion_uow = components["ingestion_uow"]

            try:
                logger.info("Fetching data for author %s (%s)", author_name, author_key)
                author_data = author_fetcher.fetch_author(author_key)

                if author_data:
                    ingestion_uow.ingest_author(match_result, author_data)
                    # Session commit happens via context manager on success, but uow might need explicit commit?
                    # context manager commits at end.

                    logger.info("Ingested author %s", author_name)

                    # Pass through for linking (task_id already in payload)
                    return payload
                logger.warning("Could not fetch data for author %s", author_name)
                self._check_completion(library_id, task_id)
            except Exception:
                logger.exception("Error ingesting author %s", author_name)
                self._check_completion(library_id, task_id)
                raise
            else:
                return None

    def _load_provider_config(
        self, session: Session, provider_name: str
    ) -> LibraryScanProviderConfig | None:
        """Load provider configuration from database.

        Parameters
        ----------
        session : Session
            Database session.
        provider_name : str
            Provider name.

        Returns
        -------
        LibraryScanProviderConfig | None
            Provider configuration if found, None otherwise.
        """
        stmt = select(LibraryScanProviderConfig).where(
            LibraryScanProviderConfig.provider_name == provider_name
        )
        return session.exec(stmt).first()

    def _should_skip_fetch(
        self,
        session: Session,
        author_key: str,
        stale_data_max_age_days: int | None,
        stale_data_refresh_interval_days: int | None,
    ) -> bool:
        """Check if author fetch should be skipped due to stale data settings.

        Parameters
        ----------
        session : Session
            Database session.
        author_key : str
            Author key identifier.
        stale_data_max_age_days : int | None
            Maximum age in days before data is considered stale.
        stale_data_refresh_interval_days : int | None
            Minimum interval between refreshes in days.

        Returns
        -------
        bool
            True if fetch should be skipped, False otherwise.
        """
        # If no stale data settings, always fetch
        if stale_data_max_age_days is None and stale_data_refresh_interval_days is None:
            return False

        # Normalize key to OpenLibrary convention: ensure /authors/ prefix
        if not author_key.startswith("/authors/"):
            normalized_key = f"/authors/{author_key.replace('authors/', '')}"
        else:
            normalized_key = author_key

        # Check if author exists in database
        stmt = select(AuthorMetadata).where(
            AuthorMetadata.openlibrary_key == normalized_key
        )
        existing = session.exec(stmt).first()

        if not existing or not existing.last_synced_at:
            # Author doesn't exist or has no sync date, fetch it
            return False

        now = datetime.now(UTC)
        # Normalize last_synced_at to timezone-aware if needed
        last_synced = existing.last_synced_at
        if last_synced.tzinfo is None:
            last_synced = last_synced.replace(tzinfo=UTC)

        days_since_sync = (now - last_synced).days

        # Check max age: if data is older than max_age, fetch it
        if (
            stale_data_max_age_days is not None
            and days_since_sync >= stale_data_max_age_days
        ):
            return False

        # Check refresh interval: if less than interval has passed, skip
        if (
            stale_data_refresh_interval_days is not None
            and days_since_sync < stale_data_refresh_interval_days
        ):
            return True

        # If we have max_age but data is fresh, skip
        return (
            stale_data_max_age_days is not None
            and days_since_sync < stale_data_max_age_days
        )

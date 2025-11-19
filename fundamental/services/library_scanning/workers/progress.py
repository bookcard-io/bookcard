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

"""Progress tracking for distributed scan jobs."""

import logging

from fundamental.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class JobProgressTracker:
    """Tracks progress of distributed jobs using Redis."""

    def __init__(self, broker: RedisBroker) -> None:
        """Initialize tracker.

        Parameters
        ----------
        broker : RedisBroker
            Redis broker instance.
        """
        self.broker = broker
        self.client = broker.client
        self.prefix = "scan:progress"

    def _get_total_key(self, library_id: int) -> str:
        return f"{self.prefix}:{library_id}:total"

    def _get_processed_key(self, library_id: int) -> str:
        return f"{self.prefix}:{library_id}:processed"

    def _get_task_id_key(self, library_id: int) -> str:
        return f"{self.prefix}:{library_id}:task_id"

    def _get_stage_started_key(self, library_id: int, stage: str) -> str:
        return f"{self.prefix}:{library_id}:stage_started:{stage}"

    def _get_cancellation_key(self, task_id: int) -> str:
        return f"{self.prefix}:cancelled:{task_id}"

    def mark_stage_started(self, library_id: int, stage: str) -> bool:
        """Mark a stage as started (idempotent).

        Parameters
        ----------
        library_id : int
            Library ID.
        stage : str
            Stage name.

        Returns
        -------
        bool
            True if this was the first time marking this stage as started,
            False if already started.
        """
        key = self._get_stage_started_key(library_id, stage)
        # SETNX returns 1 if key was set, 0 if it already existed
        was_set = self.client.setnx(key, "1")
        if was_set:
            # Set expiry to match job expiry
            self.client.expire(key, 86400)
        return bool(was_set)

    def clear_job(self, library_id: int) -> None:
        """Clear any existing job data for a library.

        Parameters
        ----------
        library_id : int
            Library ID.
        """
        keys_to_delete = [
            self._get_total_key(library_id),
            self._get_processed_key(library_id),
            self._get_task_id_key(library_id),
        ]
        # Also clear stage started keys
        keys_to_delete.extend(
            self._get_stage_started_key(library_id, stage)
            for stage in ["match", "ingest", "link"]
        )

        self.client.delete(*keys_to_delete)
        logger.info("Cleared scan job data for library %d", library_id)

    def initialize_job(
        self, library_id: int, total_items: int, task_id: int | None = None
    ) -> None:
        """Initialize job counters.

        Parameters
        ----------
        library_id : int
            Library ID.
        total_items : int
            Total number of items to process.
        task_id : int | None
            Optional task ID to store for later retrieval.
        """
        # Set total and reset processed
        pipe = self.client.pipeline()
        # Ensure values are converted to strings/ints as required by redis-py
        # Some redis-py versions strictly require bytes/str/int/float
        pipe.set(self._get_total_key(library_id), str(total_items))
        pipe.set(self._get_processed_key(library_id), "0")
        if task_id is not None:
            pipe.set(self._get_task_id_key(library_id), str(task_id))
        # Set expiry (e.g., 24 hours) to prevent leak
        pipe.expire(self._get_total_key(library_id), 86400)
        pipe.expire(self._get_processed_key(library_id), 86400)
        if task_id is not None:
            pipe.expire(self._get_task_id_key(library_id), 86400)
        pipe.execute()
        logger.info(
            "Initialized scan job for library %d with %d items", library_id, total_items
        )

    def mark_item_processed(self, library_id: int) -> bool:
        """Mark an item as processed (either successfully or dropped).

        Parameters
        ----------
        library_id : int
            Library ID.

        Returns
        -------
        bool
            True if this was the LAST item (job complete), False otherwise.
        """
        # Check if total exists before incrementing (avoid unnecessary increments)
        total_val = self.client.get(self._get_total_key(library_id))

        if total_val is None:
            # Job not initialized or already completed - this can happen if:
            # 1. Job was already completed and keys were cleaned up
            # 2. Delayed messages from a previous scan
            # 3. New scan hasn't initialized yet
            # In these cases, we can't track progress, so just return False
            logger.debug(
                "Total count not found for library %d (job may be completed or not initialized)",
                library_id,
            )
            return False

        processed = self.client.incr(self._get_processed_key(library_id))
        total = int(total_val)

        logger.debug("Library %d progress: %d/%d", library_id, processed, total)

        if processed >= total:
            logger.info(
                "Library %d scan job complete (%d/%d)", library_id, processed, total
            )
            # Cleanup keys
            self.client.delete(self._get_total_key(library_id))
            self.client.delete(self._get_processed_key(library_id))
            self.client.delete(self._get_task_id_key(library_id))
            # Cleanup stage started keys
            for stage in ["match", "ingest", "link"]:
                self.client.delete(self._get_stage_started_key(library_id, stage))
            return True

        return False

    def get_task_id(self, library_id: int) -> int | None:
        """Get task ID for a library job.

        Parameters
        ----------
        library_id : int
            Library ID.

        Returns
        -------
        int | None
            Task ID if found, None otherwise.
        """
        task_id_val = self.client.get(self._get_task_id_key(library_id))
        return int(task_id_val) if task_id_val else None

    def is_cancelled(self, task_id: int) -> bool:
        """Check if task has been cancelled.

        Parameters
        ----------
        task_id : int
            Task ID.

        Returns
        -------
        bool
            True if cancelled, False otherwise.
        """
        return bool(self.client.exists(self._get_cancellation_key(task_id)))

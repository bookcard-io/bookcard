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

Invokes the legacy ScanWorkerManager to perform the actual scan,
but allows the scan to be tracked and managed via the unified TaskRunner.
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlmodel import select

from bookcard.config import AppConfig
from bookcard.models.library_scanning import LibraryScanState
from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.library_scanning.workers.manager import ScanWorkerManager
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import WorkerContext

logger = logging.getLogger(__name__)


class LibraryScanTask(BaseTask):
    """Task for executing a library scan.

    This task acts as a bridge to the specialized ScanWorkerManager pipeline.
    It takes the scan configuration from metadata and triggers the distributed
    workers via Redis.
    """

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute library scan task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context.
        """
        # 1. Get library_id and data_source_config from metadata
        library_id = self.metadata.get("library_id")
        if not library_id:
            msg = "library_id is required in task metadata"
            raise ValueError(msg)

        data_source_config = self.metadata.get("data_source_config")
        if not data_source_config:
            # Should have been set by the service, but fallback if missing
            data_source_config = {"name": "openlibrary", "kwargs": {}}

        redis_url = self._get_redis_url(worker_context)
        if not redis_url:
            logger.warning(
                "Redis URL not found in worker context. Library scan requires Redis."
            )
            msg = "Library scan requires Redis but Redis URL is not available."
            raise RuntimeError(msg)

        logger.info(
            "Starting library scan task %s for library %s via ScanWorkerManager",
            self.task_id,
            library_id,
        )

        # 3. Instantiate Manager (or use injected one)
        manager = ScanWorkerManager(redis_url)

        # 4. Trigger the scan (publish to Redis)
        # We assume the workers are ALREADY running (managed by bootstrap).
        # We just need to publish the job.

        # Get library details
        session = (
            worker_context.session
            if isinstance(worker_context, WorkerContext)
            else worker_context["session"]
        )
        library_repo = LibraryRepository(session)
        library = library_repo.get(library_id)
        if not library:
            msg = f"Library {library_id} not found"
            raise ValueError(msg)

        # Clear old job data
        tracker = JobProgressTracker(manager.broker)
        tracker.clear_job(library_id)

        # Create/Update scan state to pending
        # This ensures the monitoring loop has a record to track immediately
        stmt = select(LibraryScanState).where(LibraryScanState.library_id == library_id)
        scan_state = session.exec(stmt).first()

        if scan_state:
            scan_state.scan_status = "pending"
            scan_state.updated_at = datetime.now(UTC)
        else:
            scan_state = LibraryScanState(
                library_id=library_id,
                scan_status="pending",
                updated_at=datetime.now(UTC),
            )
            session.add(scan_state)
        session.commit()

        # Create payload
        payload = {
            "task_id": self.task_id,  # Important: Link specialized workers to this Task
            "library_id": library_id,
            "calibre_db_path": library.calibre_db_path,
            "calibre_db_file": library.calibre_db_file or "metadata.db",
            "data_source_config": data_source_config,
        }

        # Publish
        manager.broker.publish("scan_jobs", payload)

        self._monitor_scan_progress(tracker, library_id, session)

    def _get_redis_url(
        self, worker_context: dict[str, Any] | WorkerContext
    ) -> str | None:
        """Try to retrieve Redis URL from context or environment.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context.

        Returns
        -------
        str | None
            Redis URL or None.
        """
        # 1. Try context (if injected)
        if isinstance(worker_context, dict) and "redis_url" in worker_context:
            return str(worker_context["redis_url"])

        # 2. Fallback to Config/Env
        # This is robust for a task execution
        try:
            return AppConfig._get_redis_url()  # noqa: SLF001
        except ValueError:
            return None

    def _raise_scan_failed(self) -> None:
        """Raise RuntimeError for failed scan."""
        msg = "Library scan failed (marked in ScanState)"
        raise RuntimeError(msg)

    def _monitor_scan_progress(
        self,
        tracker: JobProgressTracker,  # noqa: ARG002
        library_id: int,
        session: Any,  # noqa: ANN401
    ) -> None:
        """Monitor the scan progress until completion."""
        logger.info("Monitoring scan progress for library %s...", library_id)

        missing_state_retries = 0
        max_missing_state_retries = 12

        while True:
            # Check for cancellation
            if self.check_cancelled():
                # We should signal the distributed workers to stop?
                # tracker.cancel_job(library_id)? (Not implemented yet)
                logger.info("Task cancelled, stopping monitor.")
                return

            # Check scan state from DB
            try:
                # We need to expire cached objects to see updates from other transactions
                session.expire_all()

                state = session.get(LibraryScanState, library_id)
                if state:
                    missing_state_retries = 0
                    if state.scan_status == "completed":
                        logger.info("Scan completed successfully.")
                        self.update_progress(1.0)
                        return
                    if state.scan_status == "failed":
                        self._raise_scan_failed()
                else:
                    missing_state_retries += 1

            except Exception:  # noqa: BLE001
                # Catching generic Exception is intentional here to prevent loop crash
                # monitoring should be resilient
                logger.warning("Error checking scan state, retrying...", exc_info=True)
                missing_state_retries += 1

            if missing_state_retries > max_missing_state_retries:
                msg = f"Scan state for library {library_id} disappeared or cannot be retrieved after multiple attempts."
                raise RuntimeError(msg)

            time.sleep(5)

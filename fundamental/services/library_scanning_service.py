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

"""Library scanning service for managing scans and task creation."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

from fundamental.models.library_scanning import LibraryScanState
from fundamental.models.tasks import TaskType
from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_scanning.workers.progress import JobProgressTracker
from fundamental.services.messaging.redis_broker import RedisBroker
from fundamental.services.task_service import TaskService

if TYPE_CHECKING:
    from fundamental.services.messaging.base import MessageBroker

logger = logging.getLogger(__name__)


class LibraryScanningService:
    """Service for managing library scans and task creation.

    Handles publishing scan jobs to Redis message queue, managing scan
    configuration, and tracking scan state.
    """

    def __init__(
        self,
        session: Session,
        message_broker: "MessageBroker | None",
    ) -> None:
        """Initialize library scanning service.

        Parameters
        ----------
        session : Session
            Database session.
        message_broker : MessageBroker | None
            Message broker for publishing scan jobs. Can be None for read-only operations.
        """
        self.session = session
        self.message_broker = message_broker
        self.library_repo = LibraryRepository(session)

    def scan_library(
        self,
        library_id: int,
        user_id: int,
        data_source_config: dict[str, Any] | None = None,
    ) -> int:
        """Publish a library scan job to Redis queue.

        Parameters
        ----------
        library_id : int
            ID of library to scan.
        user_id : int
            ID of user initiating the scan.
        data_source_config : dict[str, Any] | None
            Optional data source configuration.
            Default: {"name": "openlibrary", "kwargs": {}}.

        Returns
        -------
        int
            Task ID for tracking the scan.

        Raises
        ------
        ValueError
            If library is not found or message broker not available.
        """
        # Verify library exists
        library = self.library_repo.get(library_id)
        if not library:
            msg = f"Library {library_id} not found"
            raise ValueError(msg)

        if self.message_broker is None:
            msg = "Message broker not available"
            raise ValueError(msg)

        # Default data source configuration
        if data_source_config is None:
            data_source_config = {"name": "openlibrary", "kwargs": {}}

        # Create task record
        task_service = TaskService(self.session)
        task_metadata = {
            "library_id": library_id,
            "data_source_config": data_source_config,
        }
        task = task_service.create_task(
            task_type=TaskType.LIBRARY_SCAN,
            user_id=user_id,
            metadata=task_metadata,
        )

        if task.id is None:
            msg = "Failed to create task record"
            raise RuntimeError(msg)

        task_id = task.id

        # Clear any existing scan job data in Redis
        if isinstance(self.message_broker, RedisBroker):
            tracker = JobProgressTracker(self.message_broker)
            tracker.clear_job(library_id)

        # Create scan job payload (include task_id for progress tracking)
        payload = {
            "task_id": task_id,
            "library_id": library_id,
            "calibre_db_path": library.calibre_db_path,
            "calibre_db_file": library.calibre_db_file or "metadata.db",
            "data_source_config": data_source_config,
        }

        # Publish to scan_jobs queue (CrawlWorker will pick it up)
        self.message_broker.publish("scan_jobs", payload)

        # Update scan state
        self._update_scan_state(library_id, "pending", task_id)

        logger.info(
            "Published library scan job for library %d to Redis queue (task_id: %d)",
            library_id,
            task_id,
        )

        return task_id

    def get_scan_state(self, library_id: int) -> LibraryScanState | None:
        """Get scan state for a library.

        Parameters
        ----------
        library_id : int
            ID of library.

        Returns
        -------
        LibraryScanState | None
            Scan state if found, None otherwise.
        """
        stmt = select(LibraryScanState).where(
            LibraryScanState.library_id == library_id,
        )
        return self.session.exec(stmt).first()

    def _update_scan_state(
        self,
        library_id: int,
        status: str,
        task_id: int | None = None,  # noqa: ARG002
    ) -> None:
        """Update scan state for a library.

        Parameters
        ----------
        library_id : int
            ID of library.
        status : str
            Scan status.
        task_id : int | None
            Optional task ID.
        """
        stmt = select(LibraryScanState).where(
            LibraryScanState.library_id == library_id,
        )
        scan_state = self.session.exec(stmt).first()

        if scan_state:
            scan_state.scan_status = status
            scan_state.updated_at = datetime.now(UTC)
            if status == "completed":
                scan_state.last_scan_at = datetime.now(UTC)
        else:
            scan_state = LibraryScanState(
                library_id=library_id,
                scan_status=status,
            )
            self.session.add(scan_state)

        self.session.commit()

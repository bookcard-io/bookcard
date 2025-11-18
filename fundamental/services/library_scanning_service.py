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

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


class LibraryScanningService:
    """Service for managing library scans and task creation.

    Handles creating and enqueuing LIBRARY_SCAN tasks, managing scan
    configuration, and tracking scan state.
    """

    def __init__(
        self,
        session: Session,
        task_runner: "TaskRunner | None",
    ) -> None:
        """Initialize library scanning service.

        Parameters
        ----------
        session : Session
            Database session.
        task_runner : TaskRunner | None
            Task runner for enqueuing tasks. Can be None for read-only operations.
        """
        self.session = session
        self.task_runner = task_runner
        self.library_repo = LibraryRepository(session)

    def scan_library(
        self,
        library_id: int,
        user_id: int,
        data_source_config: dict[str, Any] | None = None,
    ) -> int:
        """Create and enqueue a library scan task.

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
            If library is not found.
        """
        # Verify library exists
        library = self.library_repo.get(library_id)
        if not library:
            msg = f"Library {library_id} not found"
            raise ValueError(msg)

        # Default data source configuration
        if data_source_config is None:
            data_source_config = {"name": "openlibrary", "kwargs": {}}

        # Create task payload
        payload = {
            "library_id": library_id,
            "data_source_config": data_source_config,
        }

        # Enqueue scan task
        if self.task_runner is None:
            msg = "Task runner not available"
            raise ValueError(msg)

        task_id = self.task_runner.enqueue(
            task_type=TaskType.LIBRARY_SCAN,
            payload=payload,
            user_id=user_id,
        )

        # Update scan state
        self._update_scan_state(library_id, "pending", task_id)

        logger.info(
            "Enqueued library scan task %d for library %d",
            task_id,
            library_id,
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

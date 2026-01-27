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

"""Library scan orchestration.

This orchestrator coordinates:
1) selecting libraries to scan
2) writing scan state transitions
3) dispatching a scan job to distributed workers
4) monitoring scan state to terminal completion
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.tasks.library_scan.errors import (
    LibraryNotFoundError,
    ScanDispatchError,
)
from bookcard.services.tasks.library_scan.monitor import ScanProgressMonitor
from bookcard.services.tasks.library_scan.publisher import ScanJob, ScanJobPublisher
from bookcard.services.tasks.library_scan.state_repository import (
    LibraryScanStateRepository,
)
from bookcard.services.tasks.library_scan.types import DataSourceConfig, ScanStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlmodel import Session

    from bookcard.models.config import Library


class LibraryScanOrchestrator:
    """Orchestrates one or more library scans.

    Parameters
    ----------
    session : Session
        Database session.
    job_publisher : ScanJobPublisher
        Publisher for scan jobs.
    state_repo : LibraryScanStateRepository
        Repository for scan state persistence.
    monitor : ScanProgressMonitor
        Monitor for waiting on terminal scan states.
    """

    def __init__(
        self,
        session: Session,
        *,
        job_publisher: ScanJobPublisher,
        state_repo: LibraryScanStateRepository | None = None,
        monitor: ScanProgressMonitor | None = None,
    ) -> None:
        self._session = session
        self._library_repo = LibraryRepository(session)
        self._state_repo = state_repo or LibraryScanStateRepository(session)
        self._publisher = job_publisher
        self._monitor = monitor or ScanProgressMonitor(self._state_repo)

    def resolve_libraries(self, library_id: int | None) -> list[Library]:
        """Resolve which libraries should be scanned.

        Parameters
        ----------
        library_id : int | None
            If provided, scan only that library; otherwise scan all.

        Returns
        -------
        list[Library]
            Libraries to scan.

        Raises
        ------
        LibraryNotFoundError
            If a specific library_id is requested but not found.
        """
        if library_id is not None:
            library = self._library_repo.get(library_id)
            if library is None:
                msg = f"Library {library_id} not found"
                raise LibraryNotFoundError(msg)
            return [library]

        return list(self._library_repo.list())

    def scan(
        self,
        *,
        task_id: int,
        library_id: int | None,
        data_source_config: DataSourceConfig,
        is_cancelled: Callable[[], bool] | None = None,
        update_overall_progress: Callable[[float], None] | None = None,
    ) -> None:
        """Run scan(s) for resolved libraries.

        Parameters
        ----------
        task_id : int
            Task ID for linking distributed workers.
        library_id : int | None
            Specific library to scan, or None for all.
        data_source_config : DataSourceConfig
            Data source configuration.
        is_cancelled : Callable[[], bool] | None, optional
            Cancellation predicate.
        update_overall_progress : Callable[[float], None] | None, optional
            Callback used to update unified task progress for multi-library scans.

        Raises
        ------
        ScanDispatchError
            If a scan job cannot be dispatched.
        RuntimeError
            If one or more libraries fail scanning (aggregated error).
        """
        libraries = self.resolve_libraries(library_id)
        if not libraries:
            if update_overall_progress is not None:
                update_overall_progress(1.0)
            return

        failed: list[int] = []
        total = len(libraries)

        for idx, library in enumerate(libraries, start=1):
            if is_cancelled is not None and is_cancelled():
                return

            if library.id is None:
                continue

            try:
                self._scan_one(
                    task_id=task_id,
                    library=library,
                    data_source_config=data_source_config,
                    is_cancelled=is_cancelled,
                    update_task_progress=(
                        update_overall_progress if total == 1 else None
                    ),
                )
            except (ScanDispatchError, RuntimeError, ValueError):
                failed.append(library.id)

            if total > 1 and update_overall_progress is not None:
                update_overall_progress(idx / total)

        if failed:
            msg = f"Scans failed for libraries: {failed}"
            raise RuntimeError(msg)

    def _scan_one(
        self,
        *,
        task_id: int,
        library: Library,
        data_source_config: DataSourceConfig,
        is_cancelled: Callable[[], bool] | None,
        update_task_progress: Callable[[float], None] | None,
    ) -> None:
        """Dispatch and monitor a scan for a single library."""
        if library.id is None:
            return

        library_id = library.id

        self._publisher.clear_previous_progress(library_id)
        self._state_repo.upsert_status(library_id, ScanStatus.PENDING)

        job = ScanJob(
            task_id=task_id, library=library, data_source_config=data_source_config
        )

        try:
            self._publisher.publish(job)
        except ScanDispatchError:
            self._state_repo.upsert_status(library_id, ScanStatus.FAILED)
            raise

        self._monitor.wait_for_terminal_state(
            library_id,
            is_cancelled=is_cancelled,
            on_terminal_progress=update_task_progress,
        )

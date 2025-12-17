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

"""Simple thread-based scheduler for periodic tasks.

Monitors ScheduledTasksConfig and triggers tasks at configured times.
Uses any TaskRunner implementation (thread, dramatiq, celery) for execution.
Supports multiple scheduled task types via task definitions.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from sqlmodel import Session

from bookcard.services.scheduler.base import BaseScheduler, ScheduledTaskDefinition

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from bookcard.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


class TaskScheduler(BaseScheduler):
    """Scheduler for periodic tasks using threads.

    Monitors ScheduledTasksConfig and triggers tasks at configured times.
    Supports multiple scheduled task types via task definitions.
    Uses any TaskRunner implementation for execution.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    task_runner : TaskRunner
        Task runner for enqueueing tasks.
    task_definitions : list[ScheduledTaskDefinition] | None
        Optional list of task definitions. If None, uses default definitions.
    """

    def __init__(
        self,
        engine: Engine,  # type: ignore[name-defined]
        task_runner: TaskRunner,  # type: ignore[name-defined]
        task_definitions: list[ScheduledTaskDefinition] | None = None,
    ) -> None:
        """Initialize task scheduler.

        Parameters
        ----------
        engine : Engine
            Database engine.
        task_runner : TaskRunner
            Task runner instance.
        task_definitions : list[ScheduledTaskDefinition] | None
            Optional list of task definitions. If None, uses default definitions.
        """
        super().__init__(engine, task_runner, task_definitions)
        self._scheduler_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the scheduler."""
        # Start scheduler thread to check and trigger tasks
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler",
            daemon=True,
        )
        self._scheduler_thread.start()
        logger.info(
            "Task scheduler started with %d task definitions",
            len(self._task_definitions),
        )

    def _scheduler_loop(self) -> None:
        """Check for scheduled tasks in a loop."""
        import time as time_module

        while not self._shutdown:
            try:
                with Session(self._engine) as session:  # type: ignore[arg-type]
                    self._check_and_trigger_tasks(session)
            except Exception:
                logger.exception("Error in scheduler loop")

            # Check every minute
            time_module.sleep(60)

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        logger.info("Shutting down task scheduler...")
        self._shutdown = True

        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)

        logger.info("Task scheduler shut down")

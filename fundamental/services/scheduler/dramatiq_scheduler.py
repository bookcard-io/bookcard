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

"""Dramatiq-based scheduler for scheduled tasks.

Uses Dramatiq with Redis broker to schedule and execute periodic tasks.
Runs in-process workers for simplicity. Supports multiple scheduled task types
via configuration mapping.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import ShutdownNotifications, TimeLimit
from sqlmodel import Session

from fundamental.services.scheduler.base import BaseScheduler, ScheduledTaskDefinition

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


def setup_dramatiq_broker(redis_url: str) -> RedisBroker:
    """Set up Dramatiq broker with Redis.

    Parameters
    ----------
    redis_url : str
        Redis connection URL.

    Returns
    -------
    RedisBroker
        Configured Redis broker.
    """
    broker = RedisBroker(url=redis_url)
    broker.add_middleware(TimeLimit(time_limit=3600000))  # 1 hour max
    broker.add_middleware(ShutdownNotifications())
    dramatiq.set_broker(broker)
    return broker


def execute_scheduled_task(
    task_type: str,
    _user_id: int | None = None,
    _metadata: dict | None = None,
) -> None:
    """Dramatiq actor for executing scheduled tasks.

    This actor is called by the scheduler to execute tasks.
    It creates a task record and enqueues it via the task runner.

    Parameters
    ----------
    task_type : str
        Task type to execute.
    _user_id : int | None
        User ID (None for system tasks). Unused, prefixed with _.
    _metadata : dict | None
        Task metadata. Unused, prefixed with _.
    """
    # This will be called by Dramatiq worker
    # The actual task execution is handled by the task runner
    logger.info("Scheduled task triggered: %s", task_type)
    # Task runner will handle the actual execution


# Register as Dramatiq actor if dramatiq is available
if dramatiq is not None:
    execute_scheduled_task = dramatiq.actor(max_retries=3, time_limit=3600000)(
        execute_scheduled_task
    )


class DramatiqScheduler(BaseScheduler):
    """Scheduler for periodic tasks using Dramatiq.

    Monitors ScheduledTasksConfig and triggers tasks at configured times.
    Supports multiple scheduled task types via task definitions.
    Runs in-process workers for simplicity.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    redis_url : str
        Redis connection URL.
    task_runner : TaskRunner
        Task runner for enqueueing tasks.
    task_definitions : list[ScheduledTaskDefinition] | None
        Optional list of task definitions. If None, uses default definitions.
    """

    def __init__(
        self,
        engine: Engine,  # type: ignore[name-defined]
        redis_url: str,
        task_runner: TaskRunner,  # type: ignore[name-defined]
        task_definitions: list[ScheduledTaskDefinition] | None = None,
    ) -> None:
        """Initialize Dramatiq scheduler.

        Parameters
        ----------
        engine : Engine
            Database engine.
        redis_url : str
            Redis URL.
        task_runner : TaskRunner
            Task runner instance.
        task_definitions : list[ScheduledTaskDefinition] | None
            Optional list of task definitions. If None, uses default definitions.
        """
        super().__init__(engine, task_runner, task_definitions)
        self._redis_url = redis_url
        self._broker = setup_dramatiq_broker(redis_url)
        self._worker: dramatiq.Worker | None = None
        self._scheduler_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the scheduler and worker."""
        # Start Dramatiq worker in a separate thread
        self._worker = dramatiq.Worker(self._broker, worker_threads=1)
        self._worker.start()

        # Start scheduler thread to check and trigger tasks
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="DramatiqScheduler",
            daemon=True,
        )
        self._scheduler_thread.start()
        logger.info(
            "Dramatiq scheduler started with %d task definitions",
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
        """Shutdown the scheduler and worker."""
        logger.info("Shutting down Dramatiq scheduler...")
        self._shutdown = True

        if self._worker:
            self._worker.stop()

        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)

        logger.info("Dramatiq scheduler shut down")

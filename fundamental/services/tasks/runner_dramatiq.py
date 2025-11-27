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

"""Dramatiq task runner implementation.

Uses Dramatiq with Redis broker for distributed task execution.
Tasks are executed by Dramatiq workers and tracked in the database.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import ShutdownNotifications, TimeLimit

from fundamental.database import get_session as _get_session
from fundamental.models.tasks import TaskStatus, TaskType  # noqa: TC001
from fundamental.services.task_service import TaskService
from fundamental.services.tasks.base import TaskRunner
from fundamental.services.tasks.factory import create_task
from fundamental.services.tasks.task_executor import TaskExecutor

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


def _execute_task_actor(
    task_id: int,
    user_id: int,
    task_type: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None,
    engine: Engine,  # type: ignore[name-defined]
) -> None:
    """Dramatiq actor function for executing tasks.

    This function is called by Dramatiq workers to execute tasks.
    It follows the same pattern as ThreadTaskRunner but runs in Dramatiq workers.

    Parameters
    ----------
    task_id : int
        Database task ID.
    user_id : int
        User ID who created the task.
    task_type : str
        Task type string.
    payload : dict[str, Any]
        Task payload data.
    metadata : dict[str, Any] | None
        Task metadata.
    engine : Engine
        SQLAlchemy engine for database access.
    """
    try:
        with _get_session(engine) as session:
            task_service = TaskService(session)
            task = task_service.get_task(task_id)

            if task is None:
                logger.warning("Task %s not found in database", task_id)
                return

            # Mark task as started
            task_service.start_task(task_id)

            # Create task instance
            task_metadata = (metadata or {}).copy()
            task_metadata["task_type"] = task_type
            task_metadata.update(payload)
            task_instance = create_task(task_id, user_id, task_metadata)

            # Create progress callback
            def update_progress(
                progress: float,
                meta: dict[str, Any] | None = None,
                _task_id: int = task_id,
                _task_service: TaskService = task_service,
            ) -> None:
                """Update task progress in database."""
                _task_service.update_task_progress(_task_id, progress, meta)

            worker_context = {
                "session": session,
                "task_service": task_service,
                "update_progress": update_progress,
            }

            # Execute task using executor service
            executor = TaskExecutor(task_service)
            executor.execute_task(task_id, task_instance, worker_context)

    except Exception:
        logger.exception("Error executing task %s", task_id)


class DramatiqTaskRunner(TaskRunner):
    """Dramatiq-based task runner implementation.

    Uses Dramatiq with Redis broker for distributed task execution.
    Tasks are executed by Dramatiq workers and tracked in the database.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    redis_url : str
        Redis connection URL.
    task_factory : Callable[[int, int, dict], BaseTask]
        Factory function to create task instances (optional, uses default if not provided).
    """

    def __init__(
        self,
        engine: Engine,  # type: ignore[name-defined]
        redis_url: str,
        _task_factory: Callable[[int, int, dict[str, Any]], Any] | None = None,  # type: ignore[name-defined]
    ) -> None:
        """Initialize Dramatiq task runner.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine.
        redis_url : str
            Redis connection URL.
        _task_factory : Callable[[int, int, dict], BaseTask] | None
            Factory function to create task instances (unused, kept for interface compatibility).
        """
        if dramatiq is None:
            msg = "dramatiq package is not installed. Install with: pip install dramatiq[redis]"
            raise ImportError(msg)

        self._engine = engine
        self._redis_url = redis_url
        self._broker = RedisBroker(url=redis_url)
        self._broker.add_middleware(TimeLimit(time_limit=3600000))  # 1 hour max
        self._broker.add_middleware(ShutdownNotifications())
        dramatiq.set_broker(self._broker)

        # Create actor for task execution
        # We need to capture engine in closure, so we create a partial function
        def execute_task(
            task_id: int,
            user_id: int,
            task_type: str,
            payload: dict[str, Any],
            metadata: dict[str, Any] | None = None,
        ) -> None:
            """Execute task with engine captured from closure."""
            _execute_task_actor(
                task_id, user_id, task_type, payload, metadata, self._engine
            )

        # Register as Dramatiq actor
        self._task_actor = dramatiq.actor(
            max_retries=3,
            time_limit=3600000,
            actor_name="execute_task",
        )(execute_task)

        # Start worker in a separate thread (in-process worker)
        self._worker: dramatiq.Worker | None = None
        self._worker_thread: threading.Thread | None = None
        self._start_worker()

    def _start_worker(self) -> None:
        """Start the Dramatiq worker in a background thread."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker = dramatiq.Worker(self._broker, worker_threads=4)
            self._worker_thread = threading.Thread(
                target=self._worker.start,
                name="DramatiqWorker",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("Dramatiq task runner worker started")

    def enqueue(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        user_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Enqueue a task for execution.

        Parameters
        ----------
        task_type : TaskType
            Type of task to execute.
        payload : dict[str, Any]
            Task-specific payload data.
        user_id : int
            ID of user creating the task.
        metadata : dict[str, Any] | None
            Optional metadata to store with the task.

        Returns
        -------
        int
            Task ID for tracking the task.
        """
        # Create task record in database
        with _get_session(self._engine) as session:
            task_service = TaskService(session)
            task = task_service.create_task(task_type, user_id, metadata)
            task_id = task.id

        if task_id is None:
            msg = "Failed to create task record"
            raise RuntimeError(msg)

        # Enqueue via Dramatiq
        try:
            self._task_actor.send(
                task_id=task_id,
                user_id=user_id,
                task_type=task_type.value,
                payload=payload,
                metadata=metadata,
            )
            logger.info(
                "Task %s (%s) enqueued via Dramatiq for user %s",
                task_id,
                task_type,
                user_id,
            )
        except Exception:
            logger.exception("Failed to enqueue task %s via Dramatiq", task_id)
            # Mark task as failed if enqueue fails
            with _get_session(self._engine) as session:
                task_service = TaskService(session)
                task_service.fail_task(task_id, "Failed to enqueue task via Dramatiq")
            raise

        return task_id

    def cancel(self, task_id: int) -> bool:
        """Cancel a running or pending task.

        Parameters
        ----------
        task_id : int
            ID of task to cancel.

        Returns
        -------
        bool
            True if cancellation was successful, False otherwise.
        """
        with _get_session(self._engine) as session:
            task_service = TaskService(session)
            task = task_service.get_task(task_id)

            if task is None:
                return False

            # For Dramatiq, we can't directly cancel a running task
            # We mark it as cancelled in the database, and the task should check
            # cancellation status periodically
            return task_service.cancel_task(task_id)

    def get_status(self, task_id: int) -> TaskStatus:
        """Get current status of a task.

        Parameters
        ----------
        task_id : int
            ID of task to check.

        Returns
        -------
        TaskStatus
            Current status of the task.
        """
        with _get_session(self._engine) as session:
            task_service = TaskService(session)
            task = task_service.get_task(task_id)
            if task is None:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)
            return task.status

    def get_progress(self, task_id: int) -> float:
        """Get current progress of a task.

        Parameters
        ----------
        task_id : int
            ID of task to check.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        with _get_session(self._engine) as session:
            task_service = TaskService(session)
            task = task_service.get_task(task_id)
            if task is None:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)
            return task.progress

    def shutdown(self) -> None:
        """Shutdown the task runner and stop workers."""
        logger.info("Shutting down Dramatiq task runner...")

        if self._worker:
            self._worker.stop()

        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
            if self._worker_thread.is_alive():
                logger.warning("Dramatiq worker thread did not shut down gracefully")

        logger.info("Dramatiq task runner shut down complete")

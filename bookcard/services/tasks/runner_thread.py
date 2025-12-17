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

"""Thread-based task runner implementation.

Provides a simple in-process task execution system using Python threads.
No external dependencies required (no Redis). Suitable for development
and small deployments.
"""

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from typing import TYPE_CHECKING, Any

from bookcard.database import get_session as _get_session
from bookcard.services.task_service import TaskService
from bookcard.services.tasks.base import BaseTask, TaskRunner
from bookcard.services.tasks.task_executor import TaskExecutor

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine

    from bookcard.models.tasks import TaskStatus, TaskType

logger = logging.getLogger(__name__)


class ThreadTaskRunner(TaskRunner):
    """Thread-based task runner implementation.

    Executes tasks in background threads with an in-memory queue.
    Tasks are persisted to the database for tracking.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    task_factory : Callable[[TaskType, int, dict], BaseTask]
    Factory function to create task instances from task type.
    """

    def __init__(
        self,
        engine: Engine,  # type: ignore[name-defined]
        task_factory: Callable[[int, int, dict[str, Any]], BaseTask],
    ) -> None:
        """Initialize thread task runner.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine.
        task_factory : Callable[[TaskType, int, dict], BaseTask]
            Factory function to create task instances.
        """
        self._engine = engine
        self._task_factory = task_factory
        self._queue: queue.Queue[
            tuple[int, TaskType, dict[str, Any], int, dict[str, Any] | None]
        ] = queue.Queue()
        self._running_tasks: dict[int, BaseTask] = {}
        self._lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._shutdown = False
        self._start_worker()

    def _start_worker(self) -> None:
        """Start the worker thread."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="TaskWorker",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("Thread task runner worker started")

    def _worker_loop(self) -> None:
        """Process tasks from the queue in a background thread."""
        while not self._shutdown:
            # Get task from queue with timeout to allow shutdown check
            # Use suppress to ignore Empty exception (expected when timeout occurs)
            with contextlib.suppress(queue.Empty):
                item = self._queue.get(timeout=1.0)
                task_id, _task_type, payload, user_id, metadata = item

                try:
                    with _get_session(self._engine) as session:
                        task_service = TaskService(session)
                        task = task_service.get_task(task_id)
                        if task is None:
                            logger.warning("Task %s not found in database", task_id)
                            continue

                        # Mark task as started
                        task_service.start_task(task_id)

                        # Create task instance - include task_type in metadata
                        # Merge payload into metadata before creating task instance
                        # so that tasks can access payload data in __init__
                        task_metadata = (metadata or {}).copy()
                        task_metadata["task_type"] = task.task_type
                        task_metadata.update(payload)
                        task_instance = self._task_factory(
                            task_id, user_id, task_metadata
                        )

                        # Store running task for cancellation
                        with self._lock:
                            self._running_tasks[task_id] = task_instance

                        # Execute task with progress callback
                        # Capture task_id and task_service in closure using default args
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
                            "enqueue_task": self.enqueue,
                        }

                        try:
                            # Execute task using executor service (SRP: execution logic separated)
                            executor = TaskExecutor(task_service)
                            executor.execute_task(
                                task_id, task_instance, worker_context
                            )
                        finally:
                            # Remove from running tasks
                            with self._lock:
                                self._running_tasks.pop(task_id, None)

                except Exception:
                    logger.exception("Error processing task %s", task_id)

                finally:
                    self._queue.task_done()

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

        # Add to queue
        self._queue.put((task_id, task_type, payload, user_id, metadata))
        logger.info("Task %s (%s) queued for user %s", task_id, task_type, user_id)

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

            # If task is running, mark it for cancellation
            with self._lock:
                if task_id in self._running_tasks:
                    task_instance = self._running_tasks[task_id]
                    task_instance.mark_cancelled()

            # Update database
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
        """Shutdown the task runner and wait for running tasks to complete."""
        logger.info("Shutting down thread task runner...")
        self._shutdown = True

        # Wait for queue to empty
        self._queue.join()

        # Wait for worker thread
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5.0)
            if self._worker_thread.is_alive():
                logger.warning("Worker thread did not shut down gracefully")

        logger.info("Thread task runner shut down complete")

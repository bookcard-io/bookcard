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

"""Thread-based task runner implementation."""

from __future__ import annotations

import logging
import queue
import threading
from typing import TYPE_CHECKING, Any

from bookcard.database import get_session as _get_session
from bookcard.services.task_service import TaskService
from bookcard.services.tasks.base import TaskRunner
from bookcard.services.tasks.task_executor import TaskExecutor
from bookcard.services.tasks.thread_runner.context import TaskContextBuilder
from bookcard.services.tasks.thread_runner.queue import TaskQueueManager
from bookcard.services.tasks.thread_runner.types import QueuedTask
from bookcard.services.tasks.thread_runner.worker import WorkerPool

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor

    from sqlalchemy import Engine

    from bookcard.models.tasks import TaskStatus, TaskType
    from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class ThreadTaskRunner(TaskRunner):
    """Thread-based task runner implementation.

    Executes tasks in background threads with an in-memory queue.
    Tasks are persisted to the database for tracking.
    """

    def __init__(
        self,
        engine: Engine,
        task_factory: Callable[[int, int, dict[str, Any]], BaseTask],
        executor: Executor | None = None,
        max_workers: int = 8,
    ) -> None:
        """Initialize thread task runner.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine.
        task_factory : Callable[[int, int, dict[str, Any]], BaseTask]
            Factory function to create task instances.
        executor : Executor | None
            Optional executor instance.
        max_workers : int
            Maximum number of workers (default: 8).
        """
        self._engine = engine
        self._task_factory = task_factory

        # Components
        self._queue = TaskQueueManager()
        self._worker_pool = WorkerPool(executor=executor, max_workers=max_workers)
        self._context_builder = TaskContextBuilder(
            session_factory=lambda: _get_session(self._engine),
            service_factory=TaskService,
            task_factory=task_factory,
        )

        # State
        self._running_tasks: dict[int, BaseTask] = {}
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._worker_thread: threading.Thread | None = None

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
        while not self._shutdown_event.is_set():
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                # Submit task to executor
                future = self._worker_pool.submit(self._execute_task, item)

                # Mark task as done in queue only when execution completes
                future.add_done_callback(lambda _: self._queue.task_done())
            except Exception:
                logger.exception("Failed to submit task")
                # If submission fails, we must mark it as done to avoid blocking join()
                self._queue.task_done()

    def _execute_task(self, item: QueuedTask) -> None:
        """Execute a single task.

        This runs inside the ThreadPoolExecutor.
        """
        task_id = item.task_id

        try:
            with self._context_builder.build_service_context() as (
                session,
                task_service,
            ):
                task = task_service.get_task(task_id)
                if task is None:
                    logger.warning("Task %s not found in database", task_id)
                    return

                # Mark task as started
                task_service.start_task(task_id)

                # Create task instance
                task_instance = self._context_builder.create_task_instance(
                    task_id=task_id,
                    user_id=item.user_id,
                    payload=item.payload,
                    metadata=item.metadata,
                    task_type=item.task_type,
                )

                # Store running task for cancellation
                with self._lock:
                    self._running_tasks[task_id] = task_instance

                # Execute task with progress callback
                def update_progress(
                    progress: float,
                    meta: dict[str, Any] | None = None,
                    _task_id: int = task_id,
                    _task_service: TaskService = task_service,
                ) -> None:
                    """Update task progress in database."""
                    _task_service.update_task_progress(_task_id, progress, meta)

                # Build worker context for TaskExecutor
                worker_context = {
                    "session": session,
                    "task_service": task_service,
                    "update_progress": update_progress,
                    "enqueue_task": self.enqueue,
                }

                try:
                    # Execute task using executor service
                    executor = TaskExecutor(task_service)
                    executor.execute_task(task_id, task_instance, worker_context)
                finally:
                    # Remove from running tasks
                    with self._lock:
                        self._running_tasks.pop(task_id, None)

        except Exception as e:
            logger.exception("Error processing task %s", task_id)
            # Ensure task is marked as failed if something went wrong outside TaskExecutor
            try:
                with self._context_builder.build_service_context() as (
                    _,
                    task_service,
                ):
                    task_service.fail_task(task_id, str(e))
            except Exception:
                logger.exception("Failed to mark task %s as failed", task_id)
        finally:
            with self._lock:
                self._running_tasks.pop(task_id, None)

    def enqueue(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        user_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Enqueue a task for execution."""
        # Create task record in database
        with self._context_builder.build_service_context() as (_, task_service):
            task = task_service.create_task(task_type, user_id, metadata)
            task_id = task.id

        if task_id is None:
            msg = "Failed to create task record"
            raise RuntimeError(msg)

        # Add to queue
        item = QueuedTask(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            user_id=user_id,
            metadata=metadata,
        )
        self._queue.put(item)
        logger.info("Task %s (%s) queued for user %s", task_id, task_type, user_id)

        return task_id

    def cancel(self, task_id: int) -> bool:
        """Cancel a running or pending task."""
        with self._context_builder.build_service_context() as (_, task_service):
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
        """Get current status of a task."""
        with self._context_builder.build_service_context() as (_, task_service):
            task = task_service.get_task(task_id)
            if task is None:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)
            return task.status

    def get_progress(self, task_id: int) -> float:
        """Get current progress of a task."""
        with self._context_builder.build_service_context() as (_, task_service):
            task = task_service.get_task(task_id)
            if task is None:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)
            return task.progress

    def shutdown(self) -> None:
        """Shutdown the task runner and wait for running tasks to complete."""
        logger.info("Shutting down thread task runner...")
        self._shutdown_event.set()

        # Wait for queue to empty
        self._queue.join()

        # Wait for worker thread
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5.0)
            if self._worker_thread.is_alive():
                logger.warning("Worker thread did not shut down gracefully")

        # Shutdown executor
        self._worker_pool.shutdown(wait=True)

        logger.info("Thread task runner shut down complete")

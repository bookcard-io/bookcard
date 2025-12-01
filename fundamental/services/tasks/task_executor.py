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

"""Task execution service.

Handles execution of tasks, error handling, and completion logic.
Follows SRP by focusing solely on task execution orchestration.
Follows IOC by accepting dependencies (TaskService, error formatter).
"""

from __future__ import annotations

import logging
import time
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import PendingRollbackError
from sqlmodel import Session

from fundamental.models.tasks import TaskStatus

if TYPE_CHECKING:
    from fundamental.services.task_service import TaskService
    from fundamental.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Service for executing tasks and handling completion/failure.

    Orchestrates task execution, handles errors, and manages task lifecycle.
    Follows SRP by handling only execution orchestration.
    Follows IOC by accepting TaskService as a dependency.
    """

    def __init__(self, task_service: TaskService) -> None:
        """Initialize task executor.

        Parameters
        ----------
        task_service : TaskService
            Service for task database operations.
        """
        self._task_service = task_service

    def execute_task(
        self,
        task_id: int,
        task_instance: BaseTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Execute a task and handle completion or failure.

        Parameters
        ----------
        task_id : int
            ID of the task to execute.
        task_instance : BaseTask
            Task instance to execute.
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress callback.
        """
        start_time = time.time()

        try:
            # Execute the task
            task_instance.run(worker_context)
            duration = time.time() - start_time

            # Check if task was cancelled
            task = self._task_service.get_task(task_id)
            if task and task.status == TaskStatus.CANCELLED:
                logger.info("Task %s was cancelled", task_id)
                return

            # Task completed successfully - normalize and save metadata
            final_metadata = (
                dict(task_instance.metadata) if task_instance.metadata else {}
            )
            self._task_service.complete_task(
                task_id, final_metadata, normalize_metadata=True
            )

            # Record completion statistics
            self._task_service.record_task_completion(
                task_id,
                TaskStatus.COMPLETED,
                duration,
            )

            logger.info("Task %s completed in %.2fs", task_id, duration)

        except Exception as exc:
            duration = time.time() - start_time
            error_message = self._format_error(exc)

            logger.exception("Task %s failed: %s", task_id, error_message)

            # Handle session rollback if needed before accessing task
            session = worker_context.get("session")
            if session and isinstance(session, Session):
                # Try to rollback if session is in error state
                # Session may already be closed or in an invalid state, so suppress errors
                with suppress(Exception):
                    session.rollback()

            # Get task to check current status
            try:
                task = self._task_service.get_task(task_id)
            except PendingRollbackError:
                # Session is in error state, rollback and retry
                if session and isinstance(session, Session):
                    session.rollback()
                task = self._task_service.get_task(task_id)

            if not task or task.status != TaskStatus.FAILED:
                # Only fail if not already failed
                self._task_service.fail_task(task_id, error_message)

            # Record task completion - wrap in try/except to prevent
            # statistics errors from masking the original error
            try:
                self._task_service.record_task_completion(
                    task_id,
                    TaskStatus.FAILED,
                    duration,
                    error_message,
                )
            except Exception:
                logger.exception(
                    "Failed to record task completion statistics for task %s",
                    task_id,
                )

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """Format exception into a user-friendly error message.

        Parameters
        ----------
        exc : Exception
            Exception to format.

        Returns
        -------
        str
            Formatted error message.
        """
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        # Build a more helpful error message
        if exc_msg:
            error_msg = f"{exc_type}: {exc_msg}"
        else:
            error_msg = f"{exc_type}: An error occurred"

        # If the error message is just an attribute name (like "total_count"),
        # provide more context
        if len(error_msg.split()) == 1 and not error_msg.endswith(":"):
            error_msg = (
                f"{exc_type}: Failed to access '{exc_msg}'. "
                "This may indicate a database query issue."
            )

        return error_msg

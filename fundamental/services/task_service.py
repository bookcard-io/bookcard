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

"""Task service for managing background tasks.

Provides CRUD operations for tasks and task statistics.
Follows SRP by handling only task persistence and retrieval.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import desc, select
from sqlmodel import Session  # noqa: TC002

from fundamental.models.tasks import Task, TaskStatistics, TaskStatus, TaskType

if TYPE_CHECKING:
    from collections.abc import Sequence


class TaskService:
    """Service for managing tasks and task statistics.

    Provides methods for creating, retrieving, updating, and cancelling tasks.
    Also handles task statistics aggregation.

    Parameters
    ----------
    session : Session
        Database session for task operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize task service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def create_task(
        self,
        task_type: TaskType,
        user_id: int,
        metadata: dict | None = None,
    ) -> Task:
        """Create a new task record.

        Parameters
        ----------
        task_type : TaskType
            Type of task to create.
        user_id : int
            ID of user creating the task.
        metadata : dict | None
            Optional metadata dictionary.

        Returns
        -------
        Task
            Created task instance.
        """
        task = Task(
            task_type=task_type,
            status=TaskStatus.PENDING,
            progress=0.0,
            user_id=user_id,
            metadata=metadata,
        )
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def get_task(self, task_id: int, user_id: int | None = None) -> Task | None:
        """Get a task by ID.

        Parameters
        ----------
        task_id : int
            Task ID to retrieve.
        user_id : int | None
            Optional user ID to filter by (for security).

        Returns
        -------
        Task | None
            Task instance if found, None otherwise.
        """
        stmt = select(Task).where(Task.id == task_id)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return self._session.exec(stmt).first()  # type: ignore[call-overload]

    def list_tasks(
        self,
        user_id: int | None = None,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Task]:
        """List tasks with optional filters.

        Parameters
        ----------
        user_id : int | None
            Optional user ID to filter by.
        status : TaskStatus | None
            Optional status to filter by.
        task_type : TaskType | None
            Optional task type to filter by.
        limit : int
            Maximum number of tasks to return (default: 50).
        offset : int
            Number of tasks to skip (default: 0).

        Returns
        -------
        Sequence[Task]
            List of matching tasks.
        """
        stmt = select(Task)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        stmt = stmt.order_by(desc(Task.created_at)).limit(limit).offset(offset)
        return self._session.exec(stmt).all()  # type: ignore[call-overload]

    def update_task_progress(
        self,
        task_id: int,
        progress: float,
        metadata: dict | None = None,
    ) -> None:
        """Update task progress and optional metadata.

        Parameters
        ----------
        task_id : int
            Task ID to update.
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict | None
            Optional metadata to merge into existing metadata.
        """
        task = self._session.get(Task, task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)

        if not 0.0 <= progress <= 1.0:
            msg = "Progress must be between 0.0 and 1.0"
            raise ValueError(msg)

        task.progress = progress
        if metadata is not None:
            if task.task_data is None:
                task.task_data = {}
            task.task_data.update(metadata)
        self._session.add(task)
        self._session.commit()

    def start_task(self, task_id: int) -> None:
        """Mark a task as started.

        Parameters
        ----------
        task_id : int
            Task ID to start.
        """
        task = self._session.get(Task, task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        self._session.add(task)
        self._session.commit()

    def complete_task(self, task_id: int, metadata: dict | None = None) -> None:
        """Mark a task as completed.

        Parameters
        ----------
        task_id : int
            Task ID to complete.
        metadata : dict | None
            Optional metadata to merge into existing metadata.
        """
        task = self._session.get(Task, task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)

        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = datetime.now(UTC)
        if metadata is not None:
            if task.task_data is None:
                task.task_data = {}
            task.task_data.update(metadata)
        self._session.add(task)
        self._session.commit()

    def fail_task(self, task_id: int, error_message: str) -> None:
        """Mark a task as failed.

        Parameters
        ----------
        task_id : int
            Task ID to mark as failed.
        error_message : str
            Error message describing the failure.
        """
        task = self._session.get(Task, task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)

        task.status = TaskStatus.FAILED
        task.error_message = error_message[:2000]  # Truncate if too long
        task.completed_at = datetime.now(UTC)
        self._session.add(task)
        self._session.commit()

    def cancel_task(self, task_id: int, user_id: int | None = None) -> bool:
        """Cancel a task.

        Parameters
        ----------
        task_id : int
            Task ID to cancel.
        user_id : int | None
            Optional user ID to verify ownership.

        Returns
        -------
        bool
            True if cancellation was successful, False if task not found
            or already in terminal state.
        """
        task = self._session.get(Task, task_id)
        if task is None:
            return False

        if user_id is not None and task.user_id != user_id:
            return False

        if task.is_complete:
            return False

        task.status = TaskStatus.CANCELLED
        task.cancelled_at = datetime.now(UTC)
        self._session.add(task)
        self._session.commit()
        return True

    def get_task_statistics(
        self,
        task_type: TaskType | None = None,
    ) -> Sequence[TaskStatistics]:
        """Get task statistics.

        Parameters
        ----------
        task_type : TaskType | None
            Optional task type to filter by.

        Returns
        -------
        Sequence[TaskStatistics]
            List of task statistics.
        """
        stmt = select(TaskStatistics)
        if task_type is not None:
            stmt = stmt.where(TaskStatistics.task_type == task_type)
        stmt = stmt.order_by(TaskStatistics.task_type)
        return self._session.exec(stmt).all()  # type: ignore[call-overload]

    def record_task_completion(
        self,
        task_id: int,
        status: TaskStatus,
        duration: float | None = None,
        error: str | None = None,  # noqa: ARG002
    ) -> None:
        """Record task completion and update statistics.

        Parameters
        ----------
        task_id : int
            Task ID that completed.
        status : TaskStatus
            Final status of the task.
        duration : float | None
            Task duration in seconds.
        error : str | None
            Error message if task failed (reserved for future use).
        """
        task = self._session.get(Task, task_id)
        if task is None:
            return

        # Get or create statistics record
        stats = self._session.exec(  # type: ignore[call-overload]
            select(TaskStatistics).where(
                TaskStatistics.task_type == task.task_type,
            ),
        ).first()

        if stats is None:
            stats = TaskStatistics(
                task_type=task.task_type,
                total_count=0,
                success_count=0,
                failure_count=0,
            )
            self._session.add(stats)

        # Update statistics
        stats.total_count += 1
        if status == TaskStatus.COMPLETED:
            stats.success_count += 1
        elif status == TaskStatus.FAILED:
            stats.failure_count += 1

        if duration is not None:
            if stats.avg_duration is None:
                stats.avg_duration = duration
                stats.min_duration = duration
                stats.max_duration = duration
            else:
                # Running average: (old_avg * (n-1) + new_value) / n
                stats.avg_duration = (
                    stats.avg_duration * (stats.total_count - 1) + duration
                ) / stats.total_count
                if stats.min_duration is None or duration < stats.min_duration:
                    stats.min_duration = duration
                if stats.max_duration is None or duration > stats.max_duration:
                    stats.max_duration = duration

        stats.last_run_at = datetime.now(UTC)
        self._session.add(stats)
        self._session.commit()

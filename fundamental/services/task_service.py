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

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from sqlmodel import Session  # noqa: TC002

from fundamental.models.tasks import Task, TaskStatistics, TaskStatus, TaskType

logger = logging.getLogger(__name__)

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
            task_data=metadata,
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
        # Use session.get() to ensure we get a Task instance, not a Row
        task = self._session.get(Task, task_id)
        if task is None:
            return None

        # Filter by user_id if provided
        if user_id is not None and task.user_id != user_id:
            return None

        # Eagerly load the user relationship
        self._session.refresh(task, ["user"])
        return task

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
        stmt = select(Task).options(selectinload(Task.user))
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        stmt = stmt.order_by(desc(Task.created_at)).limit(limit).offset(offset)
        results = self._session.exec(stmt).all()  # type: ignore[call-overload]

        # Extract Task instances from Row objects if needed
        task_instances = []
        for result in results:
            if isinstance(result, Task):
                task_instances.append(result)
            else:
                # Result is a Row object, extract the Task from it
                # Row objects with selectinload return tuples/rows with the model as first element
                # or accessible via ['Task'] key
                mapping = getattr(result, "_mapping", None)
                if mapping is not None and "Task" in mapping:
                    task_instances.append(mapping["Task"])
                elif hasattr(result, "__getitem__"):
                    # Try to get first element (Task should be first)
                    try:
                        task_instances.append(result[0])
                    except (IndexError, KeyError):
                        logger.exception(
                            "Could not extract Task from Row: %s", type(result)
                        )
                        continue
                else:
                    logger.error(
                        "Unexpected result type in list_tasks: %s", type(result)
                    )

        return task_instances

    def update_task_progress(
        self,
        task_id: int,
        progress: float,
        metadata: dict | None = None,
    ) -> None:
        """Update task progress and optional metadata.

        For progress updates, only progress-related fields are kept in metadata
        to avoid cluttering the display. Non-progress fields from initial metadata
        are preserved but not shown in progress updates.

        Parameters
        ----------
        task_id : int
            Task ID to update.
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict | None
            Optional metadata to merge into existing metadata.
            Progress-related fields (status, current_file, processed_records)
            will replace existing values. Other fields are preserved.
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
            # Create a new dict to ensure SQLModel detects the change
            # SQLModel doesn't detect in-place updates to mutable objects
            updated_task_data = dict(task.task_data)

            # For progress updates, only keep progress-related fields
            # Filter out non-progress fields like task_type, data_directory, etc.
            progress_fields = {"status", "current_file", "processed_records"}
            if any(key in progress_fields for key in metadata):
                # This is a progress update - replace task_data with only progress fields
                # This ensures the display only shows progress-related information
                filtered_metadata = {
                    k: v for k, v in metadata.items() if k in progress_fields
                }
                # Only keep progress fields in task_data for display
                updated_task_data = filtered_metadata
            else:
                # Not a progress update, merge all metadata normally
                updated_task_data.update(metadata)

            task.task_data = updated_task_data
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

    def complete_task(
        self,
        task_id: int,
        metadata: dict | None = None,
        normalize_metadata: bool = True,
    ) -> None:
        """Mark a task as completed.

        Parameters
        ----------
        task_id : int
            Task ID to complete.
        metadata : dict | None
            Optional metadata to merge into existing metadata.
        normalize_metadata : bool
            Whether to normalize metadata (e.g., convert book_id to book_ids).
            Defaults to True.
        """
        from fundamental.services.tasks.metadata_normalizer import (
            TaskMetadataNormalizer,
        )

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

            # Normalize metadata if requested (e.g., ensure book_ids is present)
            if normalize_metadata:
                normalized_metadata = TaskMetadataNormalizer.normalize_metadata(
                    metadata,
                    task.task_data,
                )
            else:
                normalized_metadata = metadata

            # Merge metadata, preserving existing values
            # Create a new dict to ensure SQLModel detects the change
            updated_task_data = dict(task.task_data)
            updated_task_data.update(normalized_metadata)
            task.task_data = updated_task_data

        self._session.add(task)
        self._session.commit()
        # Refresh to ensure all changes are loaded
        self._session.refresh(task)

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

    def _extract_task_statistics(self, result: object) -> TaskStatistics | None:
        """Extract TaskStatistics from query result.

        Parameters
        ----------
        result : object
            Query result that may be a TaskStatistics instance or Row object.

        Returns
        -------
        TaskStatistics | None
            Extracted TaskStatistics instance or None if extraction fails.
        """
        if isinstance(result, TaskStatistics):
            return result
        mapping = getattr(result, "_mapping", None)
        if mapping is not None and "TaskStatistics" in mapping:
            return mapping["TaskStatistics"]
        if hasattr(result, "__getitem__"):
            try:
                return result[0]
            except (IndexError, KeyError):
                return None
        return None

    def _update_statistics_duration(
        self, stats: TaskStatistics, duration: float, total_count: int
    ) -> None:
        """Update duration statistics.

        Parameters
        ----------
        stats : TaskStatistics
            Statistics object to update.
        duration : float
            Task duration in seconds.
        total_count : int
            Total number of tasks (for running average calculation).
        """
        if stats.avg_duration is None:
            stats.avg_duration = duration
            stats.min_duration = duration
            stats.max_duration = duration
        else:
            # Running average: (old_avg * (n-1) + new_value) / n
            stats.avg_duration = (
                stats.avg_duration * (total_count - 1) + duration
            ) / total_count
            if stats.min_duration is None or duration < stats.min_duration:
                stats.min_duration = duration
            if stats.max_duration is None or duration > stats.max_duration:
                stats.max_duration = duration

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
        result = self._session.exec(  # type: ignore[call-overload]
            select(TaskStatistics).where(
                TaskStatistics.task_type == task.task_type,
            ),
        ).first()

        stats = self._extract_task_statistics(result) if result is not None else None

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
            self._update_statistics_duration(stats, duration, stats.total_count)

        stats.last_run_at = datetime.now(UTC)
        # Only add if it's a new stats object (already added above)
        # For existing stats, they're already in the session
        # Check if stats is in the added list to avoid double-adding
        if hasattr(self._session, "added"):
            added_list = getattr(self._session, "added", [])
            if stats not in added_list:
                self._session.add(stats)
        self._session.commit()

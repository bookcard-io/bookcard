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

"""Base classes for task execution and task runner abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fundamental.models.tasks import TaskStatus, TaskType  # noqa: TC001


class TaskRunner(ABC):
    """Abstract base class for task runners.

    Provides a unified interface for different task execution backends
    (Dramatiq, Celery, thread-based, etc.). Follows IOC pattern to allow
    swapping implementations without changing task code.

    Methods
    -------
    enqueue(task_type, payload, user_id, metadata)
        Enqueue a task for execution.
    cancel(task_id)
        Cancel a running or pending task.
    get_status(task_id)
        Get current status of a task.
    get_progress(task_id)
        Get current progress of a task (0.0 to 1.0).
    """

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError


class BaseTask(ABC):
    """Abstract base class for task implementations.

    All task implementations should extend this class and implement
    the run() method. Provides common functionality for progress tracking,
    metadata storage, and cancellation checking.

    Attributes
    ----------
    task_id : int
        Database ID of the task.
    user_id : int
        ID of user who created the task.
    metadata : dict[str, Any]
        Task metadata dictionary.

    Methods
    -------
    run(worker_context)
        Execute the task logic (must be implemented by subclasses).
    update_progress(progress)
        Update task progress (0.0 to 1.0).
    set_metadata(key, value)
        Set a metadata key-value pair.
    check_cancelled()
        Check if task has been cancelled.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize base task.

        Parameters
        ----------
        task_id : int
            Database ID of the task.
        user_id : int
            ID of user who created the task.
        metadata : dict[str, Any] | None
            Initial metadata dictionary.
        """
        self.task_id = task_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self._cancelled = False

    @abstractmethod
    def run(self, worker_context: Any) -> None:  # noqa: ANN401
        """Execute the task logic.

        This method must be implemented by subclasses to perform
        the actual work of the task.

        Parameters
        ----------
        worker_context : Any
            Worker-specific context object (e.g., database session,
            task runner instance).
        """
        raise NotImplementedError

    def update_progress(self, progress: float) -> None:
        """Update task progress.

        Parameters
        ----------
        progress : float
            Progress value between 0.0 and 1.0.

        Raises
        ------
        ValueError
            If progress is not between 0.0 and 1.0.
        """
        if not 0.0 <= progress <= 1.0:
            msg = "Progress must be between 0.0 and 1.0"
            raise ValueError(msg)
        # Progress updates are handled by the task runner implementation
        # This method is provided for subclasses to call

    def set_metadata(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Set a metadata key-value pair.

        Parameters
        ----------
        key : str
            Metadata key.
        value : Any
            Metadata value (must be JSON-serializable).
        """
        self.metadata[key] = value

    def check_cancelled(self) -> bool:
        """Check if task has been cancelled.

        Tasks should call this method periodically during execution
        to allow graceful cancellation.

        Returns
        -------
        bool
            True if task has been cancelled, False otherwise.
        """
        return self._cancelled

    def mark_cancelled(self) -> None:
        """Mark task as cancelled.

        Called by task runner when cancellation is requested.
        """
        self._cancelled = True

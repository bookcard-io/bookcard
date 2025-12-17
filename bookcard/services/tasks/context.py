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

"""Worker context for task execution.

Provides typed interface for worker context following Interface Segregation Principle.
Uses Protocol to avoid circular imports while maintaining type safety.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from sqlmodel import Session

from bookcard.models.tasks import TaskType

ProgressCallback = Callable[[float, dict[str, Any] | None], None]
EnqueueTaskCallback = Callable[
    [TaskType, dict[str, Any], int, dict[str, Any] | None], int
]


class TaskServiceProtocol(Protocol):
    """Protocol for task service interface.

    Defines the interface without importing the concrete TaskService class,
    avoiding circular imports while maintaining type safety.
    Follows Dependency Inversion Principle.
    """

    def update_task_progress(
        self,
        task_id: int,
        progress: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update task progress in database.

        Parameters
        ----------
        task_id : int
            Task ID to update.
        progress : float
            Progress value (0.0 to 1.0).
        metadata : dict[str, Any] | None
            Optional metadata to store.
        """
        ...


@dataclass
class WorkerContext:
    """Typed worker context for task execution.

    Provides compile-time guarantees for worker context structure.
    Follows Interface Segregation Principle by defining a clear interface.

    Attributes
    ----------
    session : Session
        Database session for task operations.
    update_progress : ProgressCallback
        Callback function for updating task progress.
    task_service : TaskServiceProtocol
        Task service for database operations. Uses Protocol to avoid
        circular imports while maintaining type safety.
    enqueue_task : EnqueueTaskCallback
        Callback function for enqueuing new tasks.
    """

    session: Session  # type: ignore[type-arg]
    update_progress: ProgressCallback
    task_service: TaskServiceProtocol

    # used to enqueue child tasks (e.g. IngestBookTask)
    enqueue_task: EnqueueTaskCallback | None = None

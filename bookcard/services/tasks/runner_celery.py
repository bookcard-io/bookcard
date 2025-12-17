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

"""Celery task runner implementation (stub).

This is a placeholder for future Celery integration.
Requires Redis/RabbitMQ and celery package.
"""

from __future__ import annotations

from typing import Any

from bookcard.models.tasks import TaskStatus, TaskType  # noqa: TC001
from bookcard.services.tasks.base import TaskRunner


class CeleryTaskRunner(TaskRunner):
    """Celery-based task runner implementation (stub).

    This implementation requires:
    - Redis or RabbitMQ broker
    - celery package installed
    - Worker process running separately

    Not yet implemented - raises NotImplementedError.
    """

    def enqueue(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        user_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Enqueue a task for execution (not implemented).

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

        Raises
        ------
        NotImplementedError
            Celery support not yet implemented.
        """
        msg = "Celery task runner not yet implemented"
        raise NotImplementedError(msg)

    def cancel(self, task_id: int) -> bool:
        """Cancel a running or pending task (not implemented).

        Parameters
        ----------
        task_id : int
            ID of task to cancel.

        Returns
        -------
        bool
            True if cancellation was successful.

        Raises
        ------
        NotImplementedError
            Celery support not yet implemented.
        """
        msg = "Celery task runner not yet implemented"
        raise NotImplementedError(msg)

    def get_status(self, task_id: int) -> TaskStatus:
        """Get current status of a task (not implemented).

        Parameters
        ----------
        task_id : int
            ID of task to check.

        Returns
        -------
        TaskStatus
            Current status of the task.

        Raises
        ------
        NotImplementedError
            Celery support not yet implemented.
        """
        msg = "Celery task runner not yet implemented"
        raise NotImplementedError(msg)

    def get_progress(self, task_id: int) -> float:
        """Get current progress of a task (not implemented).

        Parameters
        ----------
        task_id : int
            ID of task to check.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.

        Raises
        ------
        NotImplementedError
            Celery support not yet implemented.
        """
        msg = "Celery task runner not yet implemented"
        raise NotImplementedError(msg)

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

"""Task queue management."""

from __future__ import annotations

import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookcard.services.tasks.thread_runner.types import QueuedTask


class TaskQueueManager:
    """Manages the task queue.

    Handles enqueueing and dequeueing of tasks.
    """

    def __init__(self) -> None:
        """Initialize task queue manager."""
        self._queue: queue.Queue[QueuedTask] = queue.Queue()

    def put(self, item: QueuedTask) -> None:
        """Add a task to the queue.

        Parameters
        ----------
        item : QueuedTask
            The task to add.
        """
        self._queue.put(item)

    def get(self, timeout: float | None = None) -> QueuedTask:
        """Get a task from the queue.

        Parameters
        ----------
        timeout : float | None
            Timeout in seconds.

        Returns
        -------
        QueuedTask
            The retrieved task.

        Raises
        ------
        queue.Empty
            If the queue is empty after timeout.
        """
        return self._queue.get(timeout=timeout)

    def task_done(self) -> None:
        """Indicate that a formerly enqueued task is complete."""
        self._queue.task_done()

    def join(self) -> None:
        """Block until all items in the queue have been gotten and processed."""
        self._queue.join()

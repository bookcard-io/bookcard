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

"""Tests for TaskQueueManager."""

from __future__ import annotations

import queue

import pytest

from bookcard.models.tasks import TaskType
from bookcard.services.tasks.thread_runner.queue import TaskQueueManager
from bookcard.services.tasks.thread_runner.types import QueuedTask


class TestTaskQueueManager:
    """Tests for TaskQueueManager."""

    def test_init(self) -> None:
        """Test initialization."""
        manager = TaskQueueManager()
        assert isinstance(manager._queue, queue.Queue)

    def test_put_and_get(self) -> None:
        """Test putting and getting items."""
        manager = TaskQueueManager()
        item = QueuedTask(
            task_id=1,
            task_type=TaskType.BOOK_UPLOAD,
            payload={},
            user_id=1,
            metadata=None,
        )
        manager.put(item)
        retrieved = manager.get(timeout=1.0)
        assert retrieved == item

    def test_get_timeout(self) -> None:
        """Test get raises Empty on timeout."""
        manager = TaskQueueManager()
        with pytest.raises(queue.Empty):
            manager.get(timeout=0.01)

    def test_task_done_and_join(self) -> None:
        """Test task_done and join."""
        manager = TaskQueueManager()
        item = QueuedTask(
            task_id=1,
            task_type=TaskType.BOOK_UPLOAD,
            payload={},
            user_id=1,
            metadata=None,
        )
        manager.put(item)
        manager.get()

        # Verify join blocks (we can't easily test blocking, but we can test it returns
        # when task_done is called)
        manager.task_done()
        manager.join()  # Should return immediately

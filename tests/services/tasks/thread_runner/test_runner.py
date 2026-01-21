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

"""Tests for ThreadTaskRunner."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.tasks import Task, TaskStatus, TaskType
from bookcard.services.task_service import TaskService
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.thread_runner import ThreadTaskRunner
from bookcard.services.tasks.thread_runner.queue import TaskQueueManager

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return mock SQLAlchemy engine."""
    return MagicMock()


@pytest.fixture
def mock_task_factory() -> MagicMock:
    """Return mock task factory function."""

    def factory(task_id: int, user_id: int, metadata: dict) -> BaseTask:
        task = MagicMock(spec=BaseTask)
        task.task_id = task_id
        task.user_id = user_id
        task.metadata = metadata
        task.check_cancelled.return_value = False
        return task

    return factory  # type: ignore[return-value]


class TestThreadTaskRunnerInit:
    """Test ThreadTaskRunner initialization."""

    def test_init_starts_worker(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test __init__ starts worker thread."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            runner = ThreadTaskRunner(mock_engine, mock_task_factory)
            assert runner._worker_thread is not None
            assert runner._worker_thread.is_alive()
            runner.shutdown()

    def test_init_creates_queue(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test __init__ creates queue."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            runner = ThreadTaskRunner(mock_engine, mock_task_factory)
            assert isinstance(runner._queue, TaskQueueManager)
            runner.shutdown()


class TestEnqueue:
    """Test enqueue method."""

    def test_enqueue_creates_task(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test enqueue creates task in database."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING,
                user_id=1,
            )
            mock_task_service.create_task.return_value = mock_task
            # Make worker thread fail to get task so it doesn't process
            mock_task_service.get_task.return_value = None
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                # Give worker thread a moment to process any pending items
                time.sleep(0.1)
                task_id = runner.enqueue(
                    TaskType.BOOK_UPLOAD,
                    {"key": "value"},
                    user_id=1,
                    metadata={"meta": "data"},
                )
                assert task_id == 1
                # Verify task was created in database
                mock_task_service.create_task.assert_called_once()
                runner.shutdown()

    def test_enqueue_raises_on_failed_creation(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test enqueue raises RuntimeError when task creation fails."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=None,  # type: ignore[arg-type]
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING,
                user_id=1,
            )
            mock_task_service.create_task.return_value = mock_task
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                with pytest.raises(RuntimeError, match="Failed to create task record"):
                    runner.enqueue(
                        TaskType.BOOK_UPLOAD,
                        {"key": "value"},
                        user_id=1,
                    )
                runner.shutdown()


class TestCancel:
    """Test cancel method."""

    def test_cancel_task_not_found(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test cancel returns False when task not found."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task_service.get_task.return_value = None
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                result = runner.cancel(task_id=999)
                assert result is False
                runner.shutdown()

    def test_cancel_running_task(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test cancel marks running task as cancelled."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.RUNNING,
                user_id=1,
            )
            mock_task_service.get_task.return_value = mock_task
            mock_task_service.cancel_task.return_value = True
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                mock_task_instance = MagicMock(spec=BaseTask)
                runner._running_tasks[1] = mock_task_instance
                result = runner.cancel(task_id=1)
                assert result is True
                mock_task_instance.mark_cancelled.assert_called_once()
                runner.shutdown()


class TestGetStatus:
    """Test get_status method."""

    def test_get_status_success(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test get_status returns task status."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.RUNNING,
                user_id=1,
            )
            mock_task_service.get_task.return_value = mock_task
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                status = runner.get_status(task_id=1)
                assert status == TaskStatus.RUNNING
                runner.shutdown()

    def test_get_status_not_found(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test get_status raises ValueError when task not found."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task_service.get_task.return_value = None
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                with pytest.raises(ValueError, match="Task 999 not found"):
                    runner.get_status(task_id=999)
                runner.shutdown()


class TestGetProgress:
    """Test get_progress method."""

    def test_get_progress_success(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test get_progress returns task progress."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.RUNNING,
                user_id=1,
                progress=0.5,
            )
            mock_task_service.get_task.return_value = mock_task
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                progress = runner.get_progress(task_id=1)
                assert progress == 0.5
                runner.shutdown()

    def test_get_progress_not_found(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test get_progress raises ValueError when task not found."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task_service.get_task.return_value = None
            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)
                with pytest.raises(ValueError, match="Task 999 not found"):
                    runner.get_progress(task_id=999)
                runner.shutdown()


class TestWorkerLoop:
    """Test _worker_loop method."""

    def test_worker_loop_processes_task(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test _worker_loop processes queued task."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING,
                user_id=1,
            )
            mock_task_service.get_task.return_value = mock_task
            with (
                patch(
                    "bookcard.services.tasks.thread_runner.runner.TaskService",
                    return_value=mock_task_service,
                ),
                patch(
                    "bookcard.services.tasks.thread_runner.runner.TaskExecutor"
                ) as mock_executor_class,
            ):
                mock_executor = MagicMock()
                mock_executor_class.return_value = mock_executor
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)

                # Mock the worker pool to execute synchronously for testing
                # We need to execute the function AND return a future-like object
                mock_future = MagicMock()
                mock_future.add_done_callback = lambda cb: cb(mock_future)

                def submit_side_effect(
                    fn: Callable[..., Any], *args: object, **kwargs: object
                ) -> MagicMock:
                    fn(*args, **kwargs)
                    return mock_future

                with (
                    patch.object(
                        runner._worker_pool, "submit", side_effect=submit_side_effect
                    ),
                    patch.object(runner, "_execute_task") as mock_execute_task,
                ):
                    runner.enqueue(TaskType.BOOK_UPLOAD, {}, 1)
                    time.sleep(0.2)
                    mock_execute_task.assert_called()

                runner.shutdown()

    def test_execute_task_logic(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test _execute_task logic directly."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING,
                user_id=1,
            )
            mock_task_service.get_task.return_value = mock_task

            with (
                patch(
                    "bookcard.services.tasks.thread_runner.runner.TaskService",
                    return_value=mock_task_service,
                ),
                patch(
                    "bookcard.services.tasks.thread_runner.runner.TaskExecutor"
                ) as mock_executor_class,
            ):
                mock_executor = MagicMock()
                mock_executor_class.return_value = mock_executor

                runner = ThreadTaskRunner(mock_engine, mock_task_factory)

                # Create a queued task item
                from bookcard.services.tasks.thread_runner.types import QueuedTask

                item = QueuedTask(1, TaskType.BOOK_UPLOAD, {}, 1, None)

                # Run _execute_task directly
                runner._execute_task(item)

                mock_task_service.start_task.assert_called_once_with(1)
                mock_executor.execute_task.assert_called_once()
                runner.shutdown()

    def test_execute_task_handles_exception(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test _execute_task handles exceptions."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_task_service = MagicMock(spec=TaskService)
            mock_task = Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING,
                user_id=1,
            )
            mock_task_service.get_task.return_value = mock_task
            mock_task_service.start_task.side_effect = Exception("Test error")

            with patch(
                "bookcard.services.tasks.thread_runner.runner.TaskService",
                return_value=mock_task_service,
            ):
                runner = ThreadTaskRunner(mock_engine, mock_task_factory)

                from bookcard.services.tasks.thread_runner.types import QueuedTask

                item = QueuedTask(1, TaskType.BOOK_UPLOAD, {}, 1, None)

                runner._execute_task(item)

                # Should have called fail_task
                mock_task_service.fail_task.assert_called_with(1, "Test error")
                runner.shutdown()


class TestShutdown:
    """Test shutdown method."""

    def test_shutdown_waits_for_queue(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test shutdown waits for queue to empty."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            runner = ThreadTaskRunner(mock_engine, mock_task_factory)

            # Mock queue to simulate having items
            runner._queue = MagicMock()
            runner._queue.join = MagicMock()

            runner.shutdown()

            runner._queue.join.assert_called_once()

    def test_shutdown_waits_for_thread(
        self, mock_engine: MagicMock, mock_task_factory: MagicMock
    ) -> None:
        """Test shutdown waits for worker thread."""
        with patch(
            "bookcard.services.tasks.thread_runner.runner._get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            runner = ThreadTaskRunner(mock_engine, mock_task_factory)

            # Mock worker thread
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = False
            runner._worker_thread = mock_thread

            runner.shutdown()

            mock_thread.join.assert_called_once()
            assert runner._shutdown_event.is_set()

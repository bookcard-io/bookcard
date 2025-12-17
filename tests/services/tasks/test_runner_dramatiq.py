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

"""Tests for DramatiqTaskRunner to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.tasks import Task, TaskStatus, TaskType
from bookcard.services.task_service import TaskService
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.runner_dramatiq import (
    DramatiqTaskRunner,
    _execute_task_actor,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return mock SQLAlchemy engine."""
    return MagicMock()


@pytest.fixture
def mock_dramatiq() -> MagicMock:
    """Return mock dramatiq module."""
    mock_dramatiq = MagicMock()
    mock_worker = MagicMock()
    mock_actor = MagicMock()
    mock_dramatiq.Worker.return_value = mock_worker
    mock_dramatiq.set_broker = MagicMock()
    mock_dramatiq.actor.return_value = mock_actor
    return mock_dramatiq


@pytest.fixture
def mock_broker() -> MagicMock:
    """Return mock RedisBroker."""
    broker = MagicMock()
    broker.add_middleware = MagicMock()
    return broker


@pytest.fixture
def mock_worker() -> MagicMock:
    """Return mock Dramatiq worker."""
    worker = MagicMock()
    worker.start = MagicMock()
    worker.stop = MagicMock()
    return worker


@pytest.fixture
def mock_actor() -> MagicMock:
    """Return mock Dramatiq actor."""
    actor = MagicMock()
    actor.send = MagicMock()
    return actor


@pytest.fixture
def runner(
    mock_engine: MagicMock,
    mock_dramatiq: MagicMock,
    mock_broker: MagicMock,
    mock_worker: MagicMock,
    mock_actor: MagicMock,
) -> DramatiqTaskRunner:
    """Return DramatiqTaskRunner instance for testing."""
    mock_dramatiq.Worker.return_value = mock_worker
    mock_dramatiq.actor.return_value = mock_actor

    with (
        patch("bookcard.services.tasks.runner_dramatiq.dramatiq", mock_dramatiq),
        patch(
            "bookcard.services.tasks.runner_dramatiq.RedisBroker",
            return_value=mock_broker,
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.TimeLimit",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.ShutdownNotifications",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.threading.Thread"
        ) as mock_thread_class,
    ):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_thread_class.return_value = mock_thread
        return DramatiqTaskRunner(
            engine=mock_engine,
            redis_url="redis://localhost:6379/0",
        )


@pytest.fixture
def mock_task() -> Task:
    """Return mock Task instance."""
    return Task(
        id=1,
        task_type=TaskType.BOOK_UPLOAD,
        status=TaskStatus.PENDING,
        user_id=1,
        progress=0.0,
    )


@pytest.fixture
def mock_base_task() -> MagicMock:
    """Return mock BaseTask instance."""
    task = MagicMock(spec=BaseTask)
    task.task_id = 1
    task.user_id = 1
    task.metadata = {}
    return task


# ============================================================================
# Tests for __init__
# ============================================================================


def test_init_without_dramatiq(mock_engine: MagicMock) -> None:
    """Test __init__ raises ImportError when dramatiq is None."""
    with (
        patch("bookcard.services.tasks.runner_dramatiq.dramatiq", None),
        pytest.raises(ImportError, match="dramatiq package is not installed"),
    ):
        DramatiqTaskRunner(
            engine=mock_engine,
            redis_url="redis://localhost:6379/0",
        )


def test_init_success(
    mock_engine: MagicMock,
    mock_dramatiq: MagicMock,
    mock_broker: MagicMock,
    mock_worker: MagicMock,
    mock_actor: MagicMock,
) -> None:
    """Test successful initialization."""
    mock_dramatiq.Worker.return_value = mock_worker
    mock_dramatiq.actor.return_value = mock_actor

    with (
        patch("bookcard.services.tasks.runner_dramatiq.dramatiq", mock_dramatiq),
        patch(
            "bookcard.services.tasks.runner_dramatiq.RedisBroker",
            return_value=mock_broker,
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.TimeLimit",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.ShutdownNotifications",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.threading.Thread"
        ) as mock_thread_class,
    ):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_thread_class.return_value = mock_thread

        runner = DramatiqTaskRunner(
            engine=mock_engine,
            redis_url="redis://localhost:6379/0",
        )

        assert runner._engine == mock_engine
        assert runner._redis_url == "redis://localhost:6379/0"
        assert runner._broker == mock_broker
        # dramatiq.actor returns a decorator, which then wraps the function
        # So _task_actor is the result of actor()(execute_task), not just actor()
        assert runner._task_actor is not None
        mock_broker.add_middleware.assert_called()
        mock_dramatiq.set_broker.assert_called_once_with(mock_broker)
        # actor is called with kwargs, then the result is called with the function
        mock_dramatiq.actor.assert_called_once()
        mock_dramatiq.Worker.assert_called_once_with(mock_broker, worker_threads=4)


def test_start_worker_when_thread_alive(
    runner: DramatiqTaskRunner,
    mock_dramatiq: MagicMock,
    mock_worker: MagicMock,
) -> None:
    """Test _start_worker does not create new worker when thread is already alive."""
    # Set up runner with an alive thread
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True
    runner._worker_thread = mock_thread
    runner._worker = mock_worker

    # Reset call count
    mock_dramatiq.Worker.reset_mock()

    # Call _start_worker again
    runner._start_worker()

    # Should not create new worker if thread is alive
    mock_dramatiq.Worker.assert_not_called()


def test_closure_function_calls_execute_task_actor(
    mock_engine: MagicMock,
    mock_dramatiq: MagicMock,
    mock_broker: MagicMock,
    mock_worker: MagicMock,
) -> None:
    """Test that the closure function created in __init__ calls _execute_task_actor."""
    # Capture the closure function before it's wrapped by dramatiq.actor
    closure_func = None

    def actor_decorator(*args: object, **kwargs: object) -> object:
        """Mock dramatiq.actor decorator that captures the function."""

        def decorator(func: object) -> object:
            nonlocal closure_func
            closure_func = func
            return func  # Return the function itself for testing

        return decorator

    mock_dramatiq.Worker.return_value = mock_worker
    mock_dramatiq.actor.side_effect = actor_decorator

    with (
        patch("bookcard.services.tasks.runner_dramatiq.dramatiq", mock_dramatiq),
        patch(
            "bookcard.services.tasks.runner_dramatiq.RedisBroker",
            return_value=mock_broker,
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.TimeLimit",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.ShutdownNotifications",
            return_value=MagicMock(),
        ),
        patch(
            "bookcard.services.tasks.runner_dramatiq.threading.Thread"
        ) as mock_thread_class,
        patch(
            "bookcard.services.tasks.runner_dramatiq._execute_task_actor"
        ) as mock_execute,
    ):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_thread_class.return_value = mock_thread

        runner = DramatiqTaskRunner(
            engine=mock_engine,
            redis_url="redis://localhost:6379/0",
        )

        # Call the closure function directly (it's stored in _task_actor)
        assert closure_func is not None
        closure_func(
            task_id=1,
            user_id=1,
            task_type=TaskType.BOOK_UPLOAD.value,
            payload={"key": "value"},
            metadata={"meta": "data"},
        )

        # Verify _execute_task_actor was called with correct arguments
        # The closure passes self.enqueue as the enqueue_callback parameter
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0][0] == 1  # task_id
        assert call_args[0][1] == 1  # user_id
        assert call_args[0][2] == TaskType.BOOK_UPLOAD.value  # task_type
        assert call_args[0][3] == {"key": "value"}  # payload
        assert call_args[0][4] == {"meta": "data"}  # metadata
        assert call_args[0][5] == mock_engine  # engine
        assert call_args[0][6] == runner.enqueue  # enqueue_callback


# ============================================================================
# Tests for _execute_task_actor
# ============================================================================


def test_execute_task_actor_success(
    mock_engine: MagicMock,
    mock_task: Task,
    mock_base_task: MagicMock,
) -> None:
    """Test _execute_task_actor successfully executes task."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
        patch(
            "bookcard.services.tasks.runner_dramatiq.create_task"
        ) as mock_create_task,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskExecutor"
        ) as mock_executor_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.get_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        mock_create_task.return_value = mock_base_task

        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        _execute_task_actor(
            task_id=1,
            user_id=1,
            task_type=TaskType.BOOK_UPLOAD.value,
            payload={"key": "value"},
            metadata={"meta": "data"},
            engine=mock_engine,
            enqueue_callback=MagicMock(),
        )

        mock_task_service.get_task.assert_called_once_with(1)
        mock_task_service.start_task.assert_called_once_with(1)
        mock_create_task.assert_called_once()
        mock_executor.execute_task.assert_called_once()


def test_execute_task_actor_task_not_found(
    mock_engine: MagicMock,
) -> None:
    """Test _execute_task_actor when task is not found."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
        patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.get_task.return_value = None
        mock_task_service_class.return_value = mock_task_service

        _execute_task_actor(
            task_id=1,
            user_id=1,
            task_type=TaskType.BOOK_UPLOAD.value,
            payload={},
            metadata=None,
            engine=mock_engine,
            enqueue_callback=MagicMock(),
        )

        mock_logger.warning.assert_called_once_with("Task %s not found in database", 1)


def test_execute_task_actor_exception(
    mock_engine: MagicMock,
) -> None:
    """Test _execute_task_actor handles exceptions."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger,
    ):
        mock_get_session.return_value.__enter__.side_effect = RuntimeError(
            "Database error"
        )
        mock_get_session.return_value.__exit__.return_value = None

        _execute_task_actor(
            task_id=1,
            user_id=1,
            task_type=TaskType.BOOK_UPLOAD.value,
            payload={},
            metadata=None,
            engine=mock_engine,
            enqueue_callback=MagicMock(),
        )

        mock_logger.exception.assert_called_once_with("Error executing task %s", 1)


# ============================================================================
# Tests for enqueue
# ============================================================================


def test_enqueue_success(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
    mock_task: Task,
    mock_actor: MagicMock,
) -> None:
    """Test successful enqueue."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
        patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        runner._task_actor = mock_actor

        task_id = runner.enqueue(
            task_type=TaskType.BOOK_UPLOAD,
            payload={"key": "value"},
            user_id=1,
            metadata={"meta": "data"},
        )

        assert task_id == 1
        mock_task_service.create_task.assert_called_once()
        mock_actor.send.assert_called_once_with(
            task_id=1,
            user_id=1,
            task_type=TaskType.BOOK_UPLOAD.value,
            payload={"key": "value"},
            metadata={"meta": "data"},
        )
        mock_logger.info.assert_called_once()


def test_enqueue_task_id_none(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
) -> None:
    """Test enqueue raises RuntimeError when task_id is None."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task = Task(
            id=None,  # type: ignore[arg-type]
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.PENDING,
            user_id=1,
        )
        mock_task_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        with pytest.raises(RuntimeError, match="Failed to create task record"):
            runner.enqueue(
                task_type=TaskType.BOOK_UPLOAD,
                payload={},
                user_id=1,
            )


def test_enqueue_send_exception(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
    mock_task: Task,
    mock_actor: MagicMock,
) -> None:
    """Test enqueue handles exception when sending to Dramatiq."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
        patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        runner._task_actor = mock_actor
        mock_actor.send.side_effect = RuntimeError("Send failed")

        with pytest.raises(RuntimeError, match="Send failed"):
            runner.enqueue(
                task_type=TaskType.BOOK_UPLOAD,
                payload={},
                user_id=1,
            )

        mock_logger.exception.assert_called_once()
        # Verify fail_task was called
        assert mock_task_service.fail_task.call_count == 1


# ============================================================================
# Tests for cancel
# ============================================================================


@pytest.mark.parametrize(
    ("task_exists", "cancel_result", "expected"),
    [
        (True, True, True),
        (True, False, False),
        (False, None, False),
    ],
)
def test_cancel(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
    mock_task: Task,
    task_exists: bool,
    cancel_result: bool | None,
    expected: bool,
) -> None:
    """Test cancel method with various scenarios."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        if task_exists:
            mock_task_service.get_task.return_value = mock_task
            if cancel_result is not None:
                mock_task_service.cancel_task.return_value = cancel_result
        else:
            mock_task_service.get_task.return_value = None
        mock_task_service_class.return_value = mock_task_service

        result = runner.cancel(task_id=1)

        assert result == expected
        mock_task_service.get_task.assert_called_once_with(1)
        if task_exists:
            mock_task_service.cancel_task.assert_called_once_with(1)


# ============================================================================
# Tests for get_status
# ============================================================================


def test_get_status_success(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
    mock_task: Task,
) -> None:
    """Test get_status returns task status."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.get_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        status = runner.get_status(task_id=1)

        assert status == TaskStatus.PENDING
        mock_task_service.get_task.assert_called_once_with(1)


def test_get_status_task_not_found(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
) -> None:
    """Test get_status raises ValueError when task not found."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.get_task.return_value = None
        mock_task_service_class.return_value = mock_task_service

        with pytest.raises(ValueError, match="Task 1 not found"):
            runner.get_status(task_id=1)


# ============================================================================
# Tests for get_progress
# ============================================================================


def test_get_progress_success(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
    mock_task: Task,
) -> None:
    """Test get_progress returns task progress."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task.progress = 0.5
        mock_task_service.get_task.return_value = mock_task
        mock_task_service_class.return_value = mock_task_service

        progress = runner.get_progress(task_id=1)

        assert progress == 0.5
        mock_task_service.get_task.assert_called_once_with(1)


def test_get_progress_task_not_found(
    runner: DramatiqTaskRunner,
    mock_engine: MagicMock,
) -> None:
    """Test get_progress raises ValueError when task not found."""
    with (
        patch(
            "bookcard.services.tasks.runner_dramatiq._get_session"
        ) as mock_get_session,
        patch(
            "bookcard.services.tasks.runner_dramatiq.TaskService"
        ) as mock_task_service_class,
    ):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_task_service = MagicMock(spec=TaskService)
        mock_task_service.get_task.return_value = None
        mock_task_service_class.return_value = mock_task_service

        with pytest.raises(ValueError, match="Task 1 not found"):
            runner.get_progress(task_id=1)


# ============================================================================
# Tests for shutdown
# ============================================================================


def test_shutdown_with_worker(
    runner: DramatiqTaskRunner,
    mock_worker: MagicMock,
) -> None:
    """Test shutdown stops worker."""
    with patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger:
        runner._worker = mock_worker
        runner._worker_thread = MagicMock()
        runner._worker_thread.is_alive.return_value = False

        runner.shutdown()

        mock_worker.stop.assert_called_once()
        mock_logger.info.assert_called()


def test_shutdown_without_worker(
    runner: DramatiqTaskRunner,
) -> None:
    """Test shutdown when worker is None."""
    with patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger:
        runner._worker = None
        runner._worker_thread = None

        runner.shutdown()

        mock_logger.info.assert_called()


def test_shutdown_thread_alive(
    runner: DramatiqTaskRunner,
    mock_worker: MagicMock,
) -> None:
    """Test shutdown when thread is still alive after join."""
    with (
        patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger,
    ):
        runner._worker = mock_worker
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        runner._worker_thread = mock_thread

        runner.shutdown()

        mock_worker.stop.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=5.0)
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called()


def test_shutdown_thread_not_alive(
    runner: DramatiqTaskRunner,
    mock_worker: MagicMock,
) -> None:
    """Test shutdown when thread is not alive after join."""
    with patch("bookcard.services.tasks.runner_dramatiq.logger") as mock_logger:
        runner._worker = mock_worker
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        runner._worker_thread = mock_thread

        runner.shutdown()

        mock_worker.stop.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=5.0)
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_called()

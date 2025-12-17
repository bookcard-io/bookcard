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

"""Tests for tasks routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

import bookcard.api.routes.tasks as tasks
from bookcard.models.auth import User
from bookcard.models.tasks import Task, TaskStatistics, TaskStatus, TaskType
from bookcard.services.messaging.redis_broker import RedisBroker

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def admin_user() -> User:
    """Create an admin user."""
    return User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def regular_user() -> User:
    """Create a regular user."""
    return User(
        id=2,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )


@pytest.fixture
def mock_permission_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock PermissionService to allow all permissions."""

    class MockPermissionService:
        def __init__(self, session: object) -> None:
            pass

        def check_permission(
            self,
            user: User,
            resource: str,
            action: str,
            context: dict[str, object] | None = None,
        ) -> None:
            pass  # Always allow

    monkeypatch.setattr(tasks, "PermissionService", MockPermissionService)


@pytest.fixture
def mock_request() -> Request:
    """Create a mock Request with app state."""
    request = MagicMock(spec=Request)
    request.app.state = MagicMock()
    return request


class TestGetTaskRunner:
    """Test _get_task_runner function."""

    def test_get_task_runner_success(self, mock_request: Request) -> None:
        """Test _get_task_runner returns task runner when available."""
        mock_runner = MagicMock()
        mock_request.app.state.task_runner = mock_runner

        result = tasks._get_task_runner(mock_request)

        assert result == mock_runner

    def test_get_task_runner_not_initialized(self, mock_request: Request) -> None:
        """Test _get_task_runner raises HTTPException when not initialized (covers lines 69-74)."""
        delattr(mock_request.app.state, "task_runner")

        with pytest.raises(HTTPException) as exc_info:
            tasks._get_task_runner(mock_request)

        assert isinstance(exc_info.value, HTTPException)
        exc = exc_info.value
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.detail == "Task runner not initialized"


class TestListTasks:
    """Test list_tasks endpoint."""

    def test_list_tasks_admin_user(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks for admin user (shows all tasks) (covers lines 114-173)."""
        task1 = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        task2 = Task(
            id=2,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=2,
            created_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [task1, task2]
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=50,
            )

            assert len(result.items) == 2
            assert result.total == 2
            assert result.page == 1
            assert result.page_size == 50
            # Admin should see all tasks (user_id=None)
            # Note: FastAPI Query() objects are passed, so we check the call differently
            call_args = mock_service.list_tasks.call_args
            assert call_args.kwargs["user_id"] is None
            assert call_args.kwargs["limit"] == 50
            assert call_args.kwargs["offset"] == 0

    def test_list_tasks_regular_user(
        self,
        session: DummySession,
        regular_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks for regular user (shows only own tasks)."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            user_id=2,  # Same as regular_user.id
            created_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [task]
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=regular_user,
                page=1,
                page_size=50,
            )

            assert len(result.items) == 1
            # Regular user should only see their own tasks
            # Note: FastAPI Query() objects are passed, so we check the call differently
            call_args = mock_service.list_tasks.call_args
            assert call_args.kwargs["user_id"] == 2
            assert call_args.kwargs["limit"] == 50
            assert call_args.kwargs["offset"] == 0

    def test_list_tasks_with_filters(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks with status and task_type filters."""
        task = Task(
            id=1,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=1,
            created_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [task]
            mock_service_class.return_value = mock_service

            tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=10,
                status=TaskStatus.RUNNING,
                task_type=TaskType.LIBRARY_SCAN,
            )

            mock_service.list_tasks.assert_called_once_with(
                user_id=None,
                status=TaskStatus.RUNNING,
                task_type=TaskType.LIBRARY_SCAN,
                limit=10,
                offset=0,
            )

    def test_list_tasks_with_pagination(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks with pagination."""
        tasks_list = [
            Task(
                id=i,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                user_id=1,
                created_at=datetime.now(UTC),
            )
            for i in range(1, 51)  # 50 tasks
        ]

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = tasks_list
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=2,
                page_size=25,
            )

            assert result.page == 2
            assert result.page_size == 25
            # Full page, so total is estimated
            assert result.total == 25 * 3  # page_size * (page + 1)
            # Note: FastAPI Query() objects are passed, so we check the call differently
            call_args = mock_service.list_tasks.call_args
            assert call_args.kwargs["user_id"] is None
            assert call_args.kwargs["limit"] == 25
            assert call_args.kwargs["offset"] == 25

    def test_list_tasks_full_page_estimation(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks estimates total when full page is returned (covers line 168)."""
        # Return exactly page_size tasks to trigger the estimation logic
        tasks_list = [
            Task(
                id=i,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                user_id=1,
                created_at=datetime.now(UTC),
            )
            for i in range(1, 26)  # Exactly 25 tasks (page_size)
        ]

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = tasks_list
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=25,
            )

            assert result.page == 1
            assert result.page_size == 25
            assert len(result.items) == 25
            # When full page is returned, total is estimated as page_size * (page + 1)
            assert result.total == 25 * 2  # page_size * (page + 1) = 25 * 2

    def test_list_tasks_with_row_extraction(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks extracts Task from Row object (covers lines 134-145)."""
        # Create a mock Row-like object
        mock_row = MagicMock()
        mock_row._mapping = {
            "Task": Task(
                id=1,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                user_id=1,
                created_at=datetime.now(UTC),
            )
        }

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [mock_row]
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=50,
            )

            assert len(result.items) == 1

    def test_list_tasks_with_indexable_row(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks extracts Task from indexable Row object."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        # Create a mock indexable object
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: task if key == 0 else None

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [mock_row]
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=50,
            )

            assert len(result.items) == 1

    def test_list_tasks_with_invalid_row(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test list_tasks handles invalid Row objects gracefully."""
        # Create a mock row that raises IndexError
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=IndexError())

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tasks.return_value = [mock_row]
            mock_service_class.return_value = mock_service

            result = tasks.list_tasks(
                session=session,
                current_user=admin_user,
                page=1,
                page_size=50,
            )

            # Invalid rows should be skipped
            assert len(result.items) == 0


class TestGetTask:
    """Test get_task endpoint."""

    def test_get_task_success(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task returns task when found (covers lines 210-224)."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            user_id=1,
            created_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            result = tasks.get_task(
                session=session,
                current_user=admin_user,
                task_id=1,
            )

            assert result.id == 1
            assert result.task_type == TaskType.BOOK_UPLOAD
            assert result.status == TaskStatus.COMPLETED
            mock_service.get_task.assert_called_once_with(1, user_id=None)

    def test_get_task_not_found(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task raises 404 when task not found."""
        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tasks.get_task(
                    session=session,
                    current_user=admin_user,
                    task_id=999,
                )

            assert isinstance(exc_info.value, HTTPException)
            exc = exc_info.value
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "task_not_found"

    def test_get_task_regular_user_own_task(
        self,
        session: DummySession,
        regular_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task for regular user accessing own task."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            user_id=2,  # Same as regular_user.id
            created_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            result = tasks.get_task(
                session=session,
                current_user=regular_user,
                task_id=1,
            )

            assert result.id == 1
            mock_service.get_task.assert_called_once_with(1, user_id=2)


class TestCancelTask:
    """Test cancel_task endpoint."""

    def test_cancel_task_success(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
        mock_request: Request,
    ) -> None:
        """Test cancel_task succeeds (covers lines 271-310)."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        mock_runner = MagicMock()
        mock_runner.cancel.return_value = True
        mock_request.app.state.task_runner = mock_runner

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            result = tasks.cancel_task(
                request=mock_request,
                session=session,
                current_user=admin_user,
                task_id=1,
            )

            assert result.success is True
            assert result.message == "Task cancelled successfully"
            mock_runner.cancel.assert_called_once_with(1)

    def test_cancel_task_library_scan_with_redis(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
        mock_request: Request,
    ) -> None:
        """Test cancel_task propagates cancellation for library scan tasks."""
        task = Task(
            id=1,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        mock_runner = MagicMock()
        mock_runner.cancel.return_value = True
        mock_request.app.state.task_runner = mock_runner

        mock_redis_client = MagicMock()
        mock_broker = MagicMock(spec=RedisBroker)
        mock_broker.client = mock_redis_client
        mock_request.app.state.scan_worker_broker = mock_broker

        with (
            patch("bookcard.api.routes.tasks.TaskService") as mock_service_class,
            patch("bookcard.api.routes.tasks.JobProgressTracker") as mock_tracker_class,
        ):
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            mock_tracker = MagicMock()
            mock_tracker._get_cancellation_key.return_value = "cancel:1"
            mock_tracker_class.return_value = mock_tracker

            result = tasks.cancel_task(
                request=mock_request,
                session=session,
                current_user=admin_user,
                task_id=1,
            )

            assert result.success is True
            mock_redis_client.setex.assert_called_once_with("cancel:1", 86400, "1")

    def test_cancel_task_not_found(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
        mock_request: Request,
    ) -> None:
        """Test cancel_task raises 404 when task not found."""
        mock_runner = MagicMock()
        mock_request.app.state.task_runner = mock_runner

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tasks.cancel_task(
                    request=mock_request,
                    session=session,
                    current_user=admin_user,
                    task_id=999,
                )

            assert isinstance(exc_info.value, HTTPException)
            exc = exc_info.value
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "task_not_found"

    def test_cancel_task_runner_not_available(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
        mock_request: Request,
    ) -> None:
        """Test cancel_task raises 503 when task runner not available."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        mock_request.app.state.task_runner = None

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tasks.cancel_task(
                    request=mock_request,
                    session=session,
                    current_user=admin_user,
                    task_id=1,
                )

            assert isinstance(exc_info.value, HTTPException)
            exc = exc_info.value
            assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert exc.detail == "Task runner not available"

    def test_cancel_task_failure(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
        mock_request: Request,
    ) -> None:
        """Test cancel_task returns failure when cancel returns False."""
        task = Task(
            id=1,
            task_type=TaskType.BOOK_UPLOAD,
            status=TaskStatus.RUNNING,
            progress=0.5,
            user_id=1,
            created_at=datetime.now(UTC),
        )
        mock_runner = MagicMock()
        mock_runner.cancel.return_value = False
        mock_request.app.state.task_runner = mock_runner

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task.return_value = task
            mock_service_class.return_value = mock_service

            result = tasks.cancel_task(
                request=mock_request,
                session=session,
                current_user=admin_user,
                task_id=1,
            )

            assert result.success is False
            assert result.message == "Task could not be cancelled"


class TestGetTaskStatistics:
    """Test get_task_statistics endpoint."""

    def test_get_task_statistics_admin(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task_statistics for admin user (covers lines 341-373)."""
        stats = TaskStatistics(
            task_type=TaskType.BOOK_UPLOAD,
            total_count=10,
            success_count=8,
            failure_count=2,
            avg_duration=5.5,
            min_duration=1.0,
            max_duration=10.0,
            last_run_at=datetime.now(UTC),
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task_statistics.return_value = [stats]
            mock_service_class.return_value = mock_service

            result = tasks.get_task_statistics(
                session=session,
                current_user=admin_user,
            )

            assert len(result) == 1
            assert result[0].task_type == TaskType.BOOK_UPLOAD
            assert result[0].total_count == 10
            assert result[0].success_count == 8
            assert result[0].failure_count == 2
            assert result[0].success_rate == 0.8  # 8/10

    def test_get_task_statistics_with_zero_total(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task_statistics handles zero total_count."""
        stats = TaskStatistics(
            task_type=TaskType.BOOK_UPLOAD,
            total_count=0,
            success_count=0,
            failure_count=0,
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task_statistics.return_value = [stats]
            mock_service_class.return_value = mock_service

            result = tasks.get_task_statistics(
                session=session,
                current_user=admin_user,
            )

            assert len(result) == 1
            assert result[0].success_rate == 0.0

    def test_get_task_statistics_regular_user(
        self,
        session: DummySession,
        regular_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task_statistics raises 403 for non-admin users."""
        with pytest.raises(HTTPException) as exc_info:
            tasks.get_task_statistics(
                session=session,
                current_user=regular_user,
            )

        assert isinstance(exc_info.value, HTTPException)
        exc = exc_info.value
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.detail == "Only administrators can view task statistics"

    def test_get_task_statistics_with_task_type_filter(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task_statistics with task_type filter."""
        stats = TaskStatistics(
            task_type=TaskType.LIBRARY_SCAN,
            total_count=5,
            success_count=4,
            failure_count=1,
        )

        with patch("bookcard.api.routes.tasks.TaskService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_task_statistics.return_value = [stats]
            mock_service_class.return_value = mock_service

            tasks.get_task_statistics(
                session=session,
                current_user=admin_user,
                task_type=TaskType.LIBRARY_SCAN,
            )

            mock_service.get_task_statistics.assert_called_once_with(
                task_type=TaskType.LIBRARY_SCAN
            )


class TestGetTaskTypes:
    """Test get_task_types endpoint."""

    def test_get_task_types(
        self,
        session: DummySession,
        admin_user: User,
        mock_permission_service: None,
    ) -> None:
        """Test get_task_types returns all task types (covers lines 401-404)."""
        result = tasks.get_task_types(
            session=session,
            current_user=admin_user,
        )

        assert len(result.task_types) == len(list(TaskType))
        assert all(task_type in result.task_types for task_type in TaskType)

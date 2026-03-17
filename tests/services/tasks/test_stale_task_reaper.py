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

"""Tests for StaleTaskReaper service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from bookcard.models.config import ScheduledTasksConfig
from bookcard.models.tasks import Task, TaskStatus, TaskType
from bookcard.services.tasks.base import TaskRunner
from bookcard.services.tasks.stale_task_reaper import StaleTaskReaper


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return mock SQLAlchemy engine."""
    return MagicMock()


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Return mock task runner."""
    return MagicMock(spec=TaskRunner)


@pytest.fixture
def reaper(mock_engine: MagicMock, mock_task_runner: MagicMock) -> StaleTaskReaper:
    """Create StaleTaskReaper instance with mocks."""
    return StaleTaskReaper(mock_engine, mock_task_runner)


class TestStaleTaskReaperInit:
    """Test StaleTaskReaper initialization."""

    def test_init_stores_dependencies(
        self, mock_engine: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test __init__ stores engine and task runner."""
        reaper = StaleTaskReaper(mock_engine, mock_task_runner)
        assert reaper._engine is mock_engine
        assert reaper._task_runner is mock_task_runner


class TestReap:
    """Test reap method."""

    def test_reap_returns_zero_when_no_config(self, reaper: StaleTaskReaper) -> None:
        """Test reap returns 0 when ScheduledTasksConfig is missing."""
        with patch.object(reaper, "_get_max_runtime_seconds", return_value=None):
            assert reaper.reap() == 0

    def test_reap_returns_zero_when_no_stale_tasks(
        self, reaper: StaleTaskReaper
    ) -> None:
        """Test reap returns 0 when no stale tasks found."""
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = []

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
            assert reaper.reap() == 0

    def test_reap_fails_and_cancels_stale_tasks(
        self, reaper: StaleTaskReaper, mock_task_runner: MagicMock
    ) -> None:
        """Test reap marks stale tasks as FAILED and sends cancel signal."""
        stale_task = Task(
            id=42,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            user_id=1,
            started_at=datetime.now(UTC) - timedelta(hours=12),
        )
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = [stale_task]

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            result = reaper.reap()

            assert result == 1
            mock_task_runner.cancel.assert_called_once_with(42)
            mock_task_service.fail_task.assert_called_once()
            call_args = mock_task_service.fail_task.call_args
            assert call_args[0][0] == 42
            assert "reaped by watchdog" in call_args[0][1]

    def test_reap_multiple_stale_tasks(
        self, reaper: StaleTaskReaper, mock_task_runner: MagicMock
    ) -> None:
        """Test reap handles multiple stale tasks."""
        stale_tasks = [
            Task(
                id=i,
                task_type=TaskType.LIBRARY_SCAN,
                status=TaskStatus.RUNNING,
                user_id=1,
                started_at=datetime.now(UTC) - timedelta(hours=12),
            )
            for i in range(1, 4)
        ]
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = stale_tasks

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            result = reaper.reap()

            assert result == 3
            assert mock_task_runner.cancel.call_count == 3
            assert mock_task_service.fail_task.call_count == 3

    def test_reap_skips_task_with_none_id(
        self, reaper: StaleTaskReaper, mock_task_runner: MagicMock
    ) -> None:
        """Test reap skips tasks with id=None."""
        task_no_id = Task(
            id=None,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            user_id=1,
        )
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = [task_no_id]

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            result = reaper.reap()

            assert result == 0
            mock_task_runner.cancel.assert_not_called()
            mock_task_service.fail_task.assert_not_called()

    def test_reap_continues_when_cancel_raises(
        self, reaper: StaleTaskReaper, mock_task_runner: MagicMock
    ) -> None:
        """Test reap continues processing when task_runner.cancel raises."""
        stale_task = Task(
            id=42,
            task_type=TaskType.LIBRARY_SCAN,
            status=TaskStatus.RUNNING,
            user_id=1,
            started_at=datetime.now(UTC) - timedelta(hours=12),
        )
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = [stale_task]
        mock_task_runner.cancel.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            result = reaper.reap()

            assert result == 1
            mock_task_service.fail_task.assert_called_once()

    def test_reap_returns_zero_on_db_error(self, reaper: StaleTaskReaper) -> None:
        """Test reap returns 0 when database scan fails."""
        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=36000),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session",
                side_effect=SQLAlchemyError("Connection lost"),
            ),
        ):
            assert reaper.reap() == 0

    def test_reap_error_message_contains_hours(
        self, reaper: StaleTaskReaper, mock_task_runner: MagicMock
    ) -> None:
        """Test the error message includes human-readable hours."""
        stale_task = Task(
            id=1,
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            status=TaskStatus.RUNNING,
            user_id=1,
            started_at=datetime.now(UTC) - timedelta(hours=15),
        )
        mock_task_service = MagicMock()
        mock_task_service.find_stale_running_tasks.return_value = [stale_task]

        with (
            patch.object(reaper, "_get_max_runtime_seconds", return_value=7200),
            patch(
                "bookcard.services.tasks.stale_task_reaper.Session"
            ) as mock_session_cls,
            patch(
                "bookcard.services.tasks.stale_task_reaper.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session_cls.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            reaper.reap()

            error_msg = mock_task_service.fail_task.call_args[0][1]
            assert "2h" in error_msg
            assert "reaped by watchdog" in error_msg


class TestGetMaxRuntimeSeconds:
    """Test _get_max_runtime_seconds method."""

    def test_returns_seconds_from_config(self, reaper: StaleTaskReaper) -> None:
        """Test returns duration_hours * 3600 when config exists."""
        config = ScheduledTasksConfig(duration_hours=10)
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = config

        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            return_value=mock_session,
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            result = reaper._get_max_runtime_seconds()
            assert result == 36000

    def test_returns_none_when_no_config(self, reaper: StaleTaskReaper) -> None:
        """Test returns None when ScheduledTasksConfig row doesn't exist."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            return_value=mock_session,
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            assert reaper._get_max_runtime_seconds() is None

    def test_returns_none_on_db_error(self, reaper: StaleTaskReaper) -> None:
        """Test returns None when database read fails."""
        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            side_effect=SQLAlchemyError("Connection error"),
        ):
            assert reaper._get_max_runtime_seconds() is None

    def test_returns_none_for_invalid_duration(self, reaper: StaleTaskReaper) -> None:
        """Test returns None when duration_hours is not a valid int."""
        config = MagicMock()
        config.duration_hours = "invalid"
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = config

        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            return_value=mock_session,
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            assert reaper._get_max_runtime_seconds() is None

    def test_returns_none_for_zero_duration(self, reaper: StaleTaskReaper) -> None:
        """Test returns None when duration_hours is zero."""
        config = ScheduledTasksConfig(duration_hours=0)
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = config

        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            return_value=mock_session,
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            assert reaper._get_max_runtime_seconds() is None

    def test_returns_none_for_negative_duration(self, reaper: StaleTaskReaper) -> None:
        """Test returns None when duration_hours is negative."""
        config = ScheduledTasksConfig(duration_hours=-5)
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = config

        with patch(
            "bookcard.services.tasks.stale_task_reaper.Session",
            return_value=mock_session,
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            assert reaper._get_max_runtime_seconds() is None

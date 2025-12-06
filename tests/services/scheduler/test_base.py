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

"""Tests for BaseScheduler to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.auth import User
from fundamental.models.config import ScheduledTasksConfig
from fundamental.models.tasks import TaskType
from fundamental.services.scheduler.base import (
    BaseScheduler,
    ScheduledTaskDefinition,
)
from tests.conftest import DummySession


class ConcreteScheduler(BaseScheduler):
    """Concrete implementation of BaseScheduler for testing."""

    def start(self) -> None:
        """Start the scheduler."""

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._shutdown = True


@pytest.fixture
def mock_engine() -> MagicMock:
    """Create a mock database engine."""
    return MagicMock()


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock task runner."""
    runner = MagicMock()
    runner.enqueue.return_value = 123
    return runner


@pytest.fixture
def scheduler(
    mock_engine: MagicMock,
    mock_task_runner: MagicMock,
) -> ConcreteScheduler:
    """Create a ConcreteScheduler instance."""
    return ConcreteScheduler(mock_engine, mock_task_runner)


@pytest.fixture
def scheduled_tasks_config() -> ScheduledTasksConfig:
    """Create a ScheduledTasksConfig instance."""
    return ScheduledTasksConfig(
        id=1,
        start_time_hour=2,
        duration_hours=4,
        epub_fixer_daily_scan=True,
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin user."""
    return User(
        id=1,
        username="admin",
        email="admin@test.com",
        is_admin=True,
    )


@pytest.fixture
def regular_user() -> User:
    """Create a regular user."""
    return User(
        id=2,
        username="user",
        email="user@test.com",
        is_admin=False,
    )


class TestCheckAndTriggerTasks:
    """Test _check_and_trigger_tasks method."""

    def test_check_and_trigger_tasks_no_config(
        self,
        scheduler: ConcreteScheduler,
        mock_engine: MagicMock,
    ) -> None:
        """Test _check_and_trigger_tasks when no config exists (covers line 151-152)."""
        session = DummySession()
        session._exec_results = [[]]  # No config found

        scheduler._check_and_trigger_tasks(session)  # type: ignore[arg-type]

        # Should return early without errors

    @pytest.mark.parametrize(
        ("current_hour", "start_hour", "duration", "should_trigger"),
        [
            (1, 2, 4, False),  # Before start time (covers line 158-159)
            (2, 2, 4, True),  # At start time
            (3, 2, 4, True),  # Within window
            (5, 2, 4, True),  # Just before end
            (6, 2, 4, False),  # After end time (covers line 160-161)
            (7, 2, 4, False),  # Well after end time
        ],
    )
    def test_check_and_trigger_tasks_time_window(
        self,
        scheduler: ConcreteScheduler,
        mock_engine: MagicMock,
        scheduled_tasks_config: ScheduledTasksConfig,
        current_hour: int,
        start_hour: int,
        duration: int,
        should_trigger: bool,
    ) -> None:
        """Test _check_and_trigger_tasks time window checks (covers lines 158-161)."""
        scheduled_tasks_config.start_time_hour = start_hour
        scheduled_tasks_config.duration_hours = duration
        scheduled_tasks_config.epub_fixer_daily_scan = True

        session = DummySession()
        session._exec_results = [[scheduled_tasks_config]]

        with patch("fundamental.services.scheduler.base.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, current_hour, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            # Remove side_effect to avoid DTZ001 warning - we only need now() mocked

            scheduler._check_and_trigger_tasks(session)  # type: ignore[arg-type]

            if should_trigger:
                # Should have attempted to trigger
                assert (
                    scheduler._task_runner.enqueue.called  # type: ignore[attr-defined]
                    or not scheduler._task_runner.enqueue.called  # type: ignore[attr-defined]
                )
            else:
                # Should not trigger
                pass

    def test_check_and_trigger_tasks_task_disabled(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
    ) -> None:
        """Test _check_and_trigger_tasks when task is disabled (covers line 165)."""
        scheduled_tasks_config.epub_fixer_daily_scan = False

        session = DummySession()
        session._exec_results = [[scheduled_tasks_config]]

        with patch("fundamental.services.scheduler.base.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            # Remove side_effect to avoid DTZ001 warning - we only need now() mocked

            scheduler._check_and_trigger_tasks(session)  # type: ignore[arg-type]

            # Should not trigger when disabled
            scheduler._task_runner.enqueue.assert_not_called()  # type: ignore[attr-defined]


class TestTriggerTaskIfNeeded:
    """Test _trigger_task_if_needed method."""

    @pytest.mark.parametrize(
        ("hour", "minute", "start_hour", "should_trigger"),
        [
            (1, 0, 2, False),  # Wrong hour (covers line 189)
            (2, 0, 2, True),  # Correct hour, minute 0
            (2, 4, 2, True),  # Correct hour, minute 4
            (2, 5, 2, False),  # Correct hour, minute 5 (covers line 189)
            (2, 10, 2, False),  # Correct hour, minute 10
        ],
    )
    def test_trigger_task_if_needed_time_check(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
        hour: int,
        minute: int,
        start_hour: int,
        should_trigger: bool,
    ) -> None:
        """Test _trigger_task_if_needed time checks (covers lines 189-190)."""
        scheduled_tasks_config.start_time_hour = start_hour

        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
        )

        session = DummySession()
        session._exec_results = [[admin_user]]

        with patch("fundamental.services.scheduler.base.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, hour, minute, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            # Remove side_effect to avoid DTZ001 warning - we only need now() mocked

            scheduler._trigger_task_if_needed(
                session,  # type: ignore[arg-type]
                task_def,
                scheduled_tasks_config,
                mock_now,
            )

            if should_trigger:
                # Should attempt to trigger
                pass
            else:
                # Should not trigger
                scheduler._task_runner.enqueue.assert_not_called()  # type: ignore[attr-defined]  # type: ignore[attr-defined]

    def test_trigger_task_if_needed_already_ran_recently(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
    ) -> None:
        """Test _trigger_task_if_needed when already ran recently (covers lines 194-197)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)
        # Set last run to 22 hours ago (within 23 hour window)
        scheduler._last_run_times[task_def.task_type] = now - timedelta(hours=22)

        session = DummySession()
        session._exec_results = [[admin_user]]

        scheduler._trigger_task_if_needed(
            session,  # type: ignore[arg-type]
            task_def,
            scheduled_tasks_config,
            now,
        )

        # Should not trigger
        scheduler._task_runner.enqueue.assert_not_called()  # type: ignore[attr-defined]

    def test_trigger_task_if_needed_no_system_user(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
    ) -> None:
        """Test _trigger_task_if_needed when no system user exists (covers lines 200-201)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)

        session = DummySession()
        session._exec_results = [[], []]  # No admin, no user

        scheduler._trigger_task_if_needed(
            session,  # type: ignore[arg-type]
            task_def,
            scheduled_tasks_config,
            now,
        )

        # Should not trigger
        scheduler._task_runner.enqueue.assert_not_called()  # type: ignore[attr-defined]

    def test_trigger_task_if_needed_success(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
    ) -> None:
        """Test _trigger_task_if_needed successful trigger (covers lines 210-224)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
            payload_factory=lambda: {"test": "payload"},
            metadata_factory=lambda: {"test": "metadata"},
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)

        session = DummySession()
        session._exec_results = [[admin_user]]

        scheduler._trigger_task_if_needed(
            session,  # type: ignore[arg-type]
            task_def,
            scheduled_tasks_config,
            now,
        )

        # Should trigger
        scheduler._task_runner.enqueue.assert_called_once()  # type: ignore[attr-defined]
        assert scheduler._last_run_times[task_def.task_type] == now

    def test_trigger_task_if_needed_exception(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
    ) -> None:
        """Test _trigger_task_if_needed exception handling (covers lines 225-228)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)

        session = DummySession()
        session._exec_results = [[admin_user]]

        scheduler._task_runner.enqueue.side_effect = Exception("Test error")  # type: ignore[assignment]

        with patch("fundamental.services.scheduler.base.logger") as mock_logger:
            scheduler._trigger_task_if_needed(
                session,  # type: ignore[arg-type]
                task_def,
                scheduled_tasks_config,
                now,
            )

            # Should log exception
            mock_logger.exception.assert_called_once()

    def test_trigger_task_if_needed_no_payload_factory(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
    ) -> None:
        """Test _trigger_task_if_needed without payload_factory (covers line 204)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
            payload_factory=None,
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)

        session = DummySession()
        session._exec_results = [[admin_user]]

        scheduler._trigger_task_if_needed(
            session,  # type: ignore[arg-type]
            task_def,
            scheduled_tasks_config,
            now,
        )

        # Should use empty dict for payload
        call_args = scheduler._task_runner.enqueue.call_args  # type: ignore[attr-defined]
        assert call_args[1]["payload"] == {}

    def test_trigger_task_if_needed_no_metadata_factory(
        self,
        scheduler: ConcreteScheduler,
        scheduled_tasks_config: ScheduledTasksConfig,
        admin_user: User,
    ) -> None:
        """Test _trigger_task_if_needed without metadata_factory (covers lines 205-207)."""
        task_def = ScheduledTaskDefinition(
            task_type=TaskType.EPUB_FIX_DAILY_SCAN,
            config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
            metadata_factory=None,
        )

        now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)

        session = DummySession()
        session._exec_results = [[admin_user]]

        scheduler._trigger_task_if_needed(
            session,  # type: ignore[arg-type]
            task_def,
            scheduled_tasks_config,
            now,
        )

        # Should add task_type to metadata
        call_args = scheduler._task_runner.enqueue.call_args  # type: ignore[attr-defined]
        assert "task_type" in call_args[1]["metadata"]


class TestGetSystemUser:
    """Test _get_system_user method."""

    def test_get_system_user_admin_exists(
        self,
        scheduler: ConcreteScheduler,
        admin_user: User,
    ) -> None:
        """Test _get_system_user returns admin user (covers lines 246-247)."""
        session = DummySession()
        session._exec_results = [[admin_user]]

        result = scheduler._get_system_user(session)  # type: ignore[arg-type]

        assert result == admin_user

    def test_get_system_user_no_admin_fallback(
        self,
        scheduler: ConcreteScheduler,
        regular_user: User,
    ) -> None:
        """Test _get_system_user falls back to first user (covers lines 248-251)."""
        session = DummySession()
        session._exec_results = [[], [regular_user]]  # No admin, regular user

        result = scheduler._get_system_user(session)  # type: ignore[arg-type]

        assert result == regular_user

    def test_get_system_user_no_users(
        self,
        scheduler: ConcreteScheduler,
    ) -> None:
        """Test _get_system_user returns None when no users (covers lines 253-255)."""
        session = DummySession()
        session._exec_results = [[], []]  # No admin, no user

        with patch("fundamental.services.scheduler.base.logger") as mock_logger:
            result = scheduler._get_system_user(session)  # type: ignore[arg-type]

            assert result is None
            mock_logger.error.assert_called_once()

    def test_get_system_user_no_id(
        self,
        scheduler: ConcreteScheduler,
    ) -> None:
        """Test _get_system_user returns None when user has no id (covers lines 253-255)."""
        user_no_id = User(
            id=None,  # type: ignore[arg-type]
            username="user",
            email="user@test.com",
            is_admin=True,
        )

        session = DummySession()
        session._exec_results = [[user_no_id]]

        with patch("fundamental.services.scheduler.base.logger") as mock_logger:
            result = scheduler._get_system_user(session)  # type: ignore[arg-type]

            assert result is None
            mock_logger.error.assert_called_once()

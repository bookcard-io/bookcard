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

"""Tests for APScheduler service."""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Engine
from sqlmodel import Session

from bookcard.models.auth import User
from bookcard.models.config import ScheduledJobDefinition
from bookcard.models.tasks import TaskType
from bookcard.services.scheduler.service import APSchedulerService
from bookcard.services.tasks.base import TaskRunner


class TestAPSchedulerService:
    """Tests for APSchedulerService."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """Mock SQLAlchemy engine."""
        return MagicMock(spec=Engine)

    @pytest.fixture
    def mock_task_runner(self) -> MagicMock:
        """Mock task runner."""
        return MagicMock(spec=TaskRunner)

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Mock database session."""
        session = MagicMock(spec=Session)
        session.exec.return_value.first.return_value = None
        return session

    @pytest.fixture
    def service(
        self, mock_engine: MagicMock, mock_task_runner: MagicMock
    ) -> APSchedulerService:
        """Create service instance with mocks."""
        with patch("bookcard.services.scheduler.service.BackgroundScheduler"):
            return APSchedulerService(mock_engine, mock_task_runner)

    def test_start(self, service: APSchedulerService) -> None:
        """Test start method."""
        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.running = False
        with patch.object(service, "refresh_jobs") as mock_refresh:
            service.start()
            mock_scheduler.start.assert_called_once()
            mock_refresh.assert_called_once()

    def test_start_already_running(self, service: APSchedulerService) -> None:
        """Test start method when already running."""
        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.running = True
        with patch.object(service, "refresh_jobs") as mock_refresh:
            service.start()
            mock_scheduler.start.assert_not_called()
            mock_refresh.assert_called_once()

    def test_shutdown(self, service: APSchedulerService) -> None:
        """Test shutdown method."""
        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.running = True
        service.shutdown()
        mock_scheduler.shutdown.assert_called_once_with(wait=True)

    def test_refresh_jobs_no_config(
        self,
        service: APSchedulerService,
        mock_engine: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test refresh_jobs with no enabled jobs."""
        # Ensure context manager returns the mock session we are configuring
        mock_session.__enter__.return_value = mock_session

        with patch(
            "bookcard.services.scheduler.service.Session", return_value=mock_session
        ):
            # Configure mock to return empty list for jobs query
            mock_jobs_result = MagicMock()
            mock_jobs_result.all.return_value = []
            mock_session.exec.return_value = mock_jobs_result

            mock_scheduler = cast("MagicMock", service._scheduler)

            # Set up user jobs to be removed (internal jobs are preserved)
            user_job = MagicMock()
            user_job.id = "pvr_download_monitor"
            internal_job = MagicMock()
            internal_job.id = "_internal_stale_task_reaper"
            mock_scheduler.get_jobs.return_value = [user_job, internal_job]

            service.refresh_jobs()

            # Verify user jobs were removed but internal jobs preserved
            user_job.remove.assert_called_once()
            internal_job.remove.assert_not_called()

            # Verify no jobs were added (add_job not called)
            mock_scheduler.add_job.assert_not_called()

    def test_refresh_jobs_no_user(
        self,
        service: APSchedulerService,
        mock_engine: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test refresh_jobs with no system user."""
        # Ensure context manager returns the mock session we are configuring
        mock_session.__enter__.return_value = mock_session

        with patch(
            "bookcard.services.scheduler.service.Session", return_value=mock_session
        ):
            job = ScheduledJobDefinition(
                job_name="test_job",
                task_type=TaskType.PVR_DOWNLOAD_MONITOR,
                cron_expression="*/5 * * * *",
                enabled=True,
            )

            mock_jobs_result = MagicMock()
            mock_jobs_result.all.return_value = [job]

            mock_user_result = MagicMock()
            mock_user_result.first.return_value = None

            # Sequence: jobs query, user query (admin), user query (any)
            # The code tries admin first, then any user.
            mock_session.exec.side_effect = [
                mock_jobs_result,
                mock_user_result,
                mock_user_result,
            ]

            mock_scheduler = cast("MagicMock", service._scheduler)
            mock_scheduler.remove_all_jobs.reset_mock()

            service.refresh_jobs()

            mock_scheduler.remove_all_jobs.assert_not_called()

    def test_refresh_jobs_success(
        self,
        service: APSchedulerService,
        mock_engine: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test successful job refresh."""
        # Ensure context manager returns the mock session we are configuring
        mock_session.__enter__.return_value = mock_session

        with patch(
            "bookcard.services.scheduler.service.Session", return_value=mock_session
        ):
            # Setup mocks
            job1 = ScheduledJobDefinition(
                job_name="pvr_download_monitor",
                task_type=TaskType.PVR_DOWNLOAD_MONITOR,
                cron_expression="*/5 * * * *",
                enabled=True,
                arguments={"test": 1},
            )
            job2 = ScheduledJobDefinition(
                job_name="epub_fix_daily_scan",
                task_type=TaskType.EPUB_FIX_DAILY_SCAN,
                cron_expression="0 4 * * *",
                enabled=True,
            )

            user = User(id=1, is_admin=True)

            mock_jobs_result = MagicMock()
            mock_jobs_result.all.return_value = [job1, job2]

            mock_user_result = MagicMock()
            mock_user_result.first.return_value = user

            # Sequence: jobs, user
            mock_session.exec.side_effect = [mock_jobs_result, mock_user_result]

            mock_scheduler = cast("MagicMock", service._scheduler)

            # Set up existing user job to be cleared
            old_job = MagicMock()
            old_job.id = "old_job"
            mock_scheduler.get_jobs.return_value = [old_job]

            service.refresh_jobs()

            # Should clear existing user jobs
            old_job.remove.assert_called_once()

            # Should add 2 jobs
            assert mock_scheduler.add_job.call_count == 2

            # Verify download monitor job
            call_args_list = mock_scheduler.add_job.call_args_list

            # Check first job (Download Monitor)
            _args1, kwargs1 = call_args_list[0]
            assert kwargs1["id"] == "pvr_download_monitor"
            assert isinstance(kwargs1["trigger"], CronTrigger)
            assert kwargs1["args"][0] == TaskType.PVR_DOWNLOAD_MONITOR
            assert kwargs1["args"][1] == {"test": 1}

            # Check second job (EPUB Fixer)
            _args2, kwargs2 = call_args_list[1]
            assert kwargs2["id"] == "epub_fix_daily_scan"
            assert isinstance(kwargs2["trigger"], CronTrigger)
            assert kwargs2["args"][0] == TaskType.EPUB_FIX_DAILY_SCAN

    def test_refresh_jobs_invalid_cron(
        self,
        service: APSchedulerService,
        mock_engine: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test refresh_jobs with invalid cron expression."""
        # Ensure context manager returns the mock session we are configuring
        mock_session.__enter__.return_value = mock_session

        with patch(
            "bookcard.services.scheduler.service.Session", return_value=mock_session
        ):
            # Setup mocks with invalid config
            job = ScheduledJobDefinition(
                job_name="test_job",
                task_type=TaskType.PVR_DOWNLOAD_MONITOR,
                cron_expression="invalid",
                enabled=True,
            )

            user = User(id=1, is_admin=True)

            mock_jobs_result = MagicMock()
            mock_jobs_result.all.return_value = [job]

            mock_user_result = MagicMock()
            mock_user_result.first.return_value = user

            mock_session.exec.side_effect = [mock_jobs_result, mock_user_result]

            mock_scheduler = cast("MagicMock", service._scheduler)
            mock_scheduler.get_jobs.return_value = []

            # Mock CronTrigger to raise ValueError
            with patch(
                "bookcard.services.scheduler.service.CronTrigger.from_crontab",
                side_effect=ValueError("Invalid cron"),
            ):
                service.refresh_jobs()

                # Should not add any jobs if cron fails
                mock_scheduler.add_job.assert_not_called()

    def test_execute_task(
        self,
        service: APSchedulerService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task execution callback."""
        task_type = TaskType.PVR_DOWNLOAD_MONITOR
        payload = {"test": "data"}
        user_id = 1
        metadata = {"meta": "data"}

        with patch.object(service, "_has_active_task_of_type", return_value=False):
            service._execute_task(task_type, payload, user_id, metadata)

        # The scheduler may augment metadata with runtime limits derived from
        # ScheduledTasksConfig.duration_hours. Ensure we preserve original metadata
        # and do not mutate the caller's dict.
        assert metadata == {"meta": "data"}

        mock_task_runner.enqueue.assert_called_once()
        _args, kwargs = mock_task_runner.enqueue.call_args
        assert kwargs["task_type"] == task_type
        assert kwargs["payload"] == payload
        assert kwargs["user_id"] == user_id
        assert kwargs["metadata"]["meta"] == "data"
        assert isinstance(kwargs["metadata"].get("max_runtime_seconds"), int)
        assert kwargs["metadata"]["max_runtime_seconds"] > 0

    def test_execute_task_skipped_when_active(
        self,
        service: APSchedulerService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task execution is skipped when an active task already exists."""
        with patch.object(service, "_has_active_task_of_type", return_value=True):
            service._execute_task(
                TaskType.PVR_DOWNLOAD_MONITOR,
                {},
                1,
                {},
            )

        mock_task_runner.enqueue.assert_not_called()

    def test_execute_task_error(
        self,
        service: APSchedulerService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task execution error handling."""
        mock_task_runner.enqueue.side_effect = RuntimeError("Enqueue failed")

        # Should not raise exception
        with patch.object(service, "_has_active_task_of_type", return_value=False):
            service._execute_task(
                TaskType.PVR_DOWNLOAD_MONITOR,
                {},
                1,
                {},
            )


class TestStaleTaskReaperRegistration:
    """Tests for stale task reaper registration in the scheduler."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """Mock SQLAlchemy engine."""
        return MagicMock(spec=Engine)

    @pytest.fixture
    def mock_task_runner(self) -> MagicMock:
        """Mock task runner."""
        return MagicMock(spec=TaskRunner)

    @pytest.fixture
    def service(
        self, mock_engine: MagicMock, mock_task_runner: MagicMock
    ) -> APSchedulerService:
        """Create service instance with mocks."""
        with patch("bookcard.services.scheduler.service.BackgroundScheduler"):
            return APSchedulerService(mock_engine, mock_task_runner)

    def test_init_creates_stale_task_reaper(self, service: APSchedulerService) -> None:
        """Test __init__ creates StaleTaskReaper instance."""
        from bookcard.services.tasks.stale_task_reaper import StaleTaskReaper

        assert isinstance(service._stale_task_reaper, StaleTaskReaper)

    def test_start_registers_reaper_job(self, service: APSchedulerService) -> None:
        """Test start() registers the reaper as an interval job."""
        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.running = False
        with patch.object(service, "refresh_jobs"):
            service.start()

        # The reaper job should be registered via add_job
        add_job_calls = mock_scheduler.add_job.call_args_list
        reaper_calls = [
            c
            for c in add_job_calls
            if c.kwargs.get("id") == "_internal_stale_task_reaper"
        ]
        assert len(reaper_calls) == 1
        call_kwargs = reaper_calls[0].kwargs
        assert call_kwargs["replace_existing"] is True
        # Bound methods create new objects each access; compare underlying function + instance
        func = call_kwargs["func"]
        assert func.__func__ is type(service._stale_task_reaper).reap
        assert func.__self__ is service._stale_task_reaper

    def test_reaper_registered_before_refresh_jobs(
        self, service: APSchedulerService
    ) -> None:
        """Test the reaper is registered before refresh_jobs is called."""
        call_order: list[str] = []

        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.running = False

        def track_add_job(*args: object, **kwargs: object) -> None:
            if kwargs.get("id") == "_internal_stale_task_reaper":
                call_order.append("reaper_registered")

        mock_scheduler.add_job.side_effect = track_add_job

        def track_refresh() -> None:
            call_order.append("refresh_jobs")

        with patch.object(service, "refresh_jobs", side_effect=track_refresh):
            service.start()

        assert call_order == ["reaper_registered", "refresh_jobs"]


class TestRemoveUserJobs:
    """Tests for _remove_user_jobs method."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """Mock SQLAlchemy engine."""
        return MagicMock(spec=Engine)

    @pytest.fixture
    def mock_task_runner(self) -> MagicMock:
        """Mock task runner."""
        return MagicMock(spec=TaskRunner)

    @pytest.fixture
    def service(
        self, mock_engine: MagicMock, mock_task_runner: MagicMock
    ) -> APSchedulerService:
        """Create service instance with mocks."""
        with patch("bookcard.services.scheduler.service.BackgroundScheduler"):
            return APSchedulerService(mock_engine, mock_task_runner)

    def test_removes_user_jobs(self, service: APSchedulerService) -> None:
        """Test user jobs are removed."""
        user_job = MagicMock()
        user_job.id = "my_custom_job"

        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.get_jobs.return_value = [user_job]

        service._remove_user_jobs()

        user_job.remove.assert_called_once()

    def test_preserves_internal_jobs(self, service: APSchedulerService) -> None:
        """Test internal jobs (prefixed _internal_) are preserved."""
        internal_job = MagicMock()
        internal_job.id = "_internal_stale_task_reaper"

        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.get_jobs.return_value = [internal_job]

        service._remove_user_jobs()

        internal_job.remove.assert_not_called()

    def test_mixed_jobs(self, service: APSchedulerService) -> None:
        """Test correct handling of mixed user and internal jobs."""
        user_job_1 = MagicMock()
        user_job_1.id = "pvr_download_monitor"
        user_job_2 = MagicMock()
        user_job_2.id = "epub_fix_daily_scan"
        internal_job = MagicMock()
        internal_job.id = "_internal_stale_task_reaper"

        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.get_jobs.return_value = [user_job_1, internal_job, user_job_2]

        service._remove_user_jobs()

        user_job_1.remove.assert_called_once()
        user_job_2.remove.assert_called_once()
        internal_job.remove.assert_not_called()

    def test_empty_job_list(self, service: APSchedulerService) -> None:
        """Test no-op when there are no jobs."""
        mock_scheduler = cast("MagicMock", service._scheduler)
        mock_scheduler.get_jobs.return_value = []

        service._remove_user_jobs()


class TestHasActiveTaskOfType:
    """Tests for _has_active_task_of_type on the scheduler."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """Mock SQLAlchemy engine."""
        return MagicMock(spec=Engine)

    @pytest.fixture
    def mock_task_runner(self) -> MagicMock:
        """Mock task runner."""
        return MagicMock(spec=TaskRunner)

    @pytest.fixture
    def service(
        self, mock_engine: MagicMock, mock_task_runner: MagicMock
    ) -> APSchedulerService:
        """Create service instance with mocks."""
        with patch("bookcard.services.scheduler.service.BackgroundScheduler"):
            return APSchedulerService(mock_engine, mock_task_runner)

    def test_returns_true_when_active_task_exists(
        self, service: APSchedulerService
    ) -> None:
        """Test returns True when TaskService finds an active task."""
        mock_task_service = MagicMock()
        mock_task_service.has_active_task_of_type.return_value = True

        mock_session = MagicMock()
        with (
            patch(
                "bookcard.services.scheduler.service.Session",
                return_value=mock_session,
            ),
            patch(
                "bookcard.services.scheduler.service.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            result = service._has_active_task_of_type(TaskType.LIBRARY_SCAN)

        assert result is True

    def test_returns_false_when_no_active_task(
        self, service: APSchedulerService
    ) -> None:
        """Test returns False when no active task found."""
        mock_task_service = MagicMock()
        mock_task_service.has_active_task_of_type.return_value = False

        mock_session = MagicMock()
        with (
            patch(
                "bookcard.services.scheduler.service.Session",
                return_value=mock_session,
            ),
            patch(
                "bookcard.services.scheduler.service.TaskService",
                return_value=mock_task_service,
            ),
        ):
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            result = service._has_active_task_of_type(TaskType.LIBRARY_SCAN)

        assert result is False

    def test_returns_false_on_db_error(self, service: APSchedulerService) -> None:
        """Test returns False (safe default) when database query fails."""
        from sqlalchemy.exc import SQLAlchemyError

        with patch(
            "bookcard.services.scheduler.service.Session",
            side_effect=SQLAlchemyError("Connection lost"),
        ):
            result = service._has_active_task_of_type(TaskType.LIBRARY_SCAN)

        assert result is False

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
            mock_scheduler.remove_all_jobs.reset_mock()

            service.refresh_jobs()

            # Verify remove_all_jobs was called to clear any existing jobs
            mock_scheduler.remove_all_jobs.assert_called_once()

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

            service.refresh_jobs()

            # Should clear existing jobs
            mock_scheduler = cast("MagicMock", service._scheduler)
            mock_scheduler.remove_all_jobs.assert_called_once()

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

            # Mock CronTrigger to raise ValueError
            with patch(
                "bookcard.services.scheduler.service.CronTrigger.from_crontab",
                side_effect=ValueError("Invalid cron"),
            ):
                service.refresh_jobs()

                # Should clear jobs but not add any if cron fails
                mock_scheduler = cast("MagicMock", service._scheduler)
                mock_scheduler.remove_all_jobs.assert_called_once()
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

        service._execute_task(task_type, payload, user_id, metadata)

        mock_task_runner.enqueue.assert_called_once_with(
            task_type=task_type,
            payload=payload,
            user_id=user_id,
            metadata=metadata,
        )

    def test_execute_task_error(
        self,
        service: APSchedulerService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task execution error handling."""
        mock_task_runner.enqueue.side_effect = RuntimeError("Enqueue failed")

        # Should not raise exception
        service._execute_task(
            TaskType.PVR_DOWNLOAD_MONITOR,
            {},
            1,
            {},
        )

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

"""Tests for scheduled jobs endpoints."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from bookcard.api.routes import admin
from bookcard.models.config import ScheduledJobDefinition
from bookcard.models.tasks import Task, TaskStatus, TaskType
from tests.conftest import DummySession


def test_list_scheduled_jobs_populates_last_run_info(session: DummySession) -> None:
    """Test list_scheduled_jobs populates last_run_at and last_run_status."""
    # Setup data
    job1 = ScheduledJobDefinition(
        id=1,
        job_name="job1",
        task_type=TaskType.METADATA_BACKUP,
        cron_expression="0 0 * * *",
        enabled=True,
    )
    job2 = ScheduledJobDefinition(
        id=2,
        job_name="job2",
        task_type=TaskType.LIBRARY_SCAN,
        cron_expression="0 1 * * *",
        enabled=False,
    )

    # Mock jobs query result
    session.add_exec_result([job1, job2])

    # Mock last task for job1 (completed)
    task1 = Task(
        id=101,
        task_type=TaskType.METADATA_BACKUP,
        status=TaskStatus.COMPLETED,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        started_at=datetime(2023, 1, 1, 12, 0, 1, tzinfo=UTC),
        completed_at=datetime(2023, 1, 1, 12, 0, 2, tzinfo=UTC),
        user_id=1,
    )
    session.add_exec_result([task1])

    # Mock last task for job2 (none)
    session.add_exec_result([])

    # Execute
    results = admin.list_scheduled_jobs(session)

    # Verify
    assert len(results) == 2

    # Job 1 should have last run info
    assert results[0].job_name == "job1"
    assert results[0].last_run_status == TaskStatus.COMPLETED
    assert results[0].last_run_at == task1.started_at

    # Job 2 should have no last run info
    assert results[1].job_name == "job2"
    assert results[1].last_run_status is None
    assert results[1].last_run_at is None


def test_update_scheduled_job_updates_cron_and_enabled(
    session: DummySession, mock_request: MagicMock
) -> None:
    """Test update_scheduled_job updates cron expression and enabled status."""
    # Setup
    job = ScheduledJobDefinition(
        id=1,
        job_name="test_job",
        task_type=TaskType.METADATA_BACKUP,
        cron_expression="0 0 * * *",
        enabled=False,
    )
    session.add_exec_result([job])

    # Mock scheduler
    mock_scheduler = MagicMock()
    mock_request.app.state.scheduler = mock_scheduler

    # Execute
    payload = MagicMock()
    payload.cron_expression = "0 12 * * *"
    payload.enabled = True

    result = admin.update_scheduled_job(mock_request, session, "test_job", payload)

    # Verify
    assert result.cron_expression == "0 12 * * *"
    assert result.enabled is True
    assert session.commit_count == 1
    mock_scheduler.refresh_jobs.assert_called_once()


def test_update_scheduled_job_invalid_cron(
    session: DummySession, mock_request: MagicMock
) -> None:
    """Test update_scheduled_job raises 400 for invalid cron."""
    # Setup
    job = ScheduledJobDefinition(
        id=1,
        job_name="test_job",
        task_type=TaskType.METADATA_BACKUP,
        cron_expression="0 0 * * *",
        enabled=False,
    )
    session.add_exec_result([job])

    # Execute
    payload = MagicMock()
    payload.cron_expression = "invalid cron"
    payload.enabled = None

    with pytest.raises(HTTPException) as exc:
        admin.update_scheduled_job(mock_request, session, "test_job", payload)

    assert isinstance(exc.value, HTTPException)
    assert exc.value.status_code == 400


def test_update_scheduled_job_not_found(
    session: DummySession, mock_request: MagicMock
) -> None:
    """Test update_scheduled_job raises 404 if job not found."""
    # Setup
    session.add_exec_result([])

    # Execute
    payload = MagicMock()
    payload.cron_expression = "0 0 * * *"

    with pytest.raises(HTTPException) as exc:
        admin.update_scheduled_job(mock_request, session, "unknown_job", payload)

    assert isinstance(exc.value, HTTPException)
    assert exc.value.status_code == 404

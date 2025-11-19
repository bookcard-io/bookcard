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

"""Tests for task models to achieve 100% coverage."""

from datetime import UTC, datetime, timedelta

import pytest

from fundamental.models.tasks import Task, TaskStatus, TaskType


@pytest.fixture
def task() -> Task:
    """Create a basic task."""
    return Task(
        id=1,
        task_type=TaskType.BOOK_UPLOAD,
        status=TaskStatus.PENDING,
        user_id=1,
    )


def test_task_duration_not_started(task: Task) -> None:
    """Test duration property when task hasn't started."""
    task.started_at = None
    assert task.duration is None


def test_task_duration_with_completed_at(task: Task) -> None:
    """Test duration property with completed_at."""
    task.started_at = datetime.now(UTC) - timedelta(seconds=10)
    task.completed_at = datetime.now(UTC)
    duration = task.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_task_duration_with_cancelled_at(task: Task) -> None:
    """Test duration property with cancelled_at."""
    task.started_at = datetime.now(UTC) - timedelta(seconds=5)
    task.cancelled_at = datetime.now(UTC)
    duration = task.duration
    assert duration is not None
    assert duration == pytest.approx(5.0, abs=1.0)


def test_task_duration_with_naive_started_at(task: Task) -> None:
    """Test duration property with naive started_at datetime."""
    # Create naive datetime by removing timezone info from UTC datetime
    # This simulates a naive datetime that the code will assume is UTC
    now_utc = datetime.now(UTC)
    naive_start = now_utc.replace(tzinfo=None) - timedelta(seconds=10)
    task.started_at = naive_start
    task.completed_at = now_utc
    duration = task.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_task_duration_with_naive_end_time(task: Task) -> None:
    """Test duration property with naive end time."""
    # Create naive datetime by removing timezone info from UTC datetime
    # This simulates a naive datetime that the code will assume is UTC
    now_utc = datetime.now(UTC)
    task.started_at = now_utc - timedelta(seconds=10)
    naive_end = now_utc.replace(tzinfo=None)
    task.completed_at = naive_end
    duration = task.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_task_duration_running_no_end_time(task: Task) -> None:
    """Test duration property for running task (no end time)."""
    task.started_at = datetime.now(UTC) - timedelta(seconds=10)
    task.completed_at = None
    task.cancelled_at = None
    duration = task.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_task_is_complete_completed(task: Task) -> None:
    """Test is_complete property for completed task."""
    task.status = TaskStatus.COMPLETED
    assert task.is_complete is True


def test_task_is_complete_failed(task: Task) -> None:
    """Test is_complete property for failed task."""
    task.status = TaskStatus.FAILED
    assert task.is_complete is True


def test_task_is_complete_cancelled(task: Task) -> None:
    """Test is_complete property for cancelled task."""
    task.status = TaskStatus.CANCELLED
    assert task.is_complete is True


def test_task_is_complete_pending(task: Task) -> None:
    """Test is_complete property for pending task."""
    task.status = TaskStatus.PENDING
    assert task.is_complete is False


def test_task_is_complete_running(task: Task) -> None:
    """Test is_complete property for running task."""
    task.status = TaskStatus.RUNNING
    assert task.is_complete is False

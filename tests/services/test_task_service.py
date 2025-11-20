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

"""Tests for TaskService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest

from fundamental.models.tasks import Task, TaskStatistics, TaskStatus, TaskType
from fundamental.services.task_service import TaskService

if TYPE_CHECKING:
    from tests.conftest import DummySession
else:
    from tests.conftest import DummySession  # noqa: TC001


@pytest.fixture
def task_service(session: DummySession) -> TaskService:  # type: ignore[valid-type]
    """Create TaskService instance with dummy session."""
    return TaskService(session)  # type: ignore[arg-type]


@pytest.fixture
def task() -> Task:
    """Create a basic task."""
    return Task(
        id=1,
        task_type=TaskType.BOOK_UPLOAD,
        status=TaskStatus.PENDING,
        user_id=1,
        progress=0.0,
    )


@pytest.fixture
def task_statistics() -> TaskStatistics:
    """Create task statistics."""
    return TaskStatistics(
        id=1,
        task_type=TaskType.BOOK_UPLOAD,
        total_count=0,
        success_count=0,
        failure_count=0,
    )


class TestTaskServiceInit:
    """Test TaskService initialization."""

    def test_init_stores_session(self, session: DummySession) -> None:  # type: ignore[valid-type]
        """Test __init__ stores session."""
        service = TaskService(session)  # type: ignore[arg-type]
        assert service._session == session


class TestCreateTask:
    """Test create_task method."""

    @pytest.mark.parametrize(
        ("task_type", "user_id", "metadata"),
        [
            (TaskType.BOOK_UPLOAD, 1, None),
            (TaskType.LIBRARY_SCAN, 2, {"library_id": 1}),
            (TaskType.AUTHOR_METADATA_FETCH, 3, {"author_id": "OL123A"}),
        ],
    )
    def test_create_task_success(
        self,
        task_service: TaskService,
        task_type: TaskType,
        user_id: int,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Test create_task creates task with correct attributes."""
        task = task_service.create_task(task_type, user_id, metadata)
        assert task.task_type == task_type
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.user_id == user_id
        # Task model uses 'task_data' field, and create_task sets it to metadata
        assert task.task_data == metadata
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]
        assert task in task_service._session.added  # type: ignore[attr-defined]


class TestGetTask:
    """Test get_task method."""

    def test_get_task_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test get_task returns task when found."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.get_task(1)
        assert result == task
        # refresh is called with ["user"] relationship
        assert len(session.refreshed) > 0

    def test_get_task_not_found(self, task_service: TaskService) -> None:
        """Test get_task returns None when task not found."""
        result = task_service.get_task(999)
        assert result is None

    def test_get_task_with_user_id_match(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test get_task returns task when user_id matches."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.get_task(1, user_id=1)
        assert result == task

    def test_get_task_with_user_id_mismatch(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test get_task returns None when user_id doesn't match."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.get_task(1, user_id=999)
        assert result is None


class TestListTasks:
    """Test list_tasks method."""

    @pytest.fixture
    def tasks(self) -> list[Task]:
        """Create multiple tasks."""
        return [
            Task(
                id=i,
                task_type=TaskType.BOOK_UPLOAD,
                status=TaskStatus.PENDING if i % 2 == 0 else TaskStatus.RUNNING,
                user_id=1 if i < 3 else 2,
                progress=0.0,
            )
            for i in range(1, 6)
        ]

    def test_list_tasks_no_filters(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks returns all tasks when no filters."""
        session.set_exec_result(tasks)
        result = task_service.list_tasks()
        assert len(result) == 5
        assert all(isinstance(t, Task) for t in result)

    def test_list_tasks_with_user_id(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks filters by user_id."""
        # The filter is applied in SQL, so we simulate the filtered results
        user_tasks = [t for t in tasks if t.user_id == 1]
        session.set_exec_result(user_tasks)
        result = task_service.list_tasks(user_id=1)
        # Should return filtered tasks (2 tasks with user_id=1 from the fixture)
        assert len(result) == 2

    def test_list_tasks_with_status(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks filters by status."""
        # The filter is applied in SQL, so we simulate the filtered results
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        session.set_exec_result(pending_tasks)
        result = task_service.list_tasks(status=TaskStatus.PENDING)
        # Should return filtered tasks (2 pending tasks from the fixture)
        assert len(result) == 2

    def test_list_tasks_with_task_type(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks filters by task_type."""
        session.set_exec_result(tasks)
        result = task_service.list_tasks(task_type=TaskType.BOOK_UPLOAD)
        assert len(result) == 5

    def test_list_tasks_with_limit(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks respects limit."""
        session.set_exec_result(tasks[:2])
        result = task_service.list_tasks(limit=2)
        assert len(result) == 2

    def test_list_tasks_with_offset(
        self, task_service: TaskService, tasks: list[Task], session: DummySession
    ) -> None:
        """Test list_tasks respects offset."""
        session.set_exec_result(tasks[2:])
        result = task_service.list_tasks(offset=2)
        assert len(result) == 3

    def test_list_tasks_row_object_with_mapping(
        self, task_service: TaskService, session: DummySession
    ) -> None:
        """Test list_tasks handles Row objects with _mapping."""
        mock_row = Mock()
        mock_row._mapping = {"Task": task}
        session.set_exec_result([mock_row])
        result = task_service.list_tasks()
        assert len(result) == 1
        assert result[0] == task

    def test_list_tasks_row_object_with_getitem(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test list_tasks handles Row objects with __getitem__."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(return_value=task)
        session.set_exec_result([mock_row])
        result = task_service.list_tasks()
        assert len(result) == 1
        assert result[0] == task

    def test_list_tasks_row_object_getitem_index_error(
        self, task_service: TaskService, session: DummySession
    ) -> None:
        """Test list_tasks handles IndexError from Row object."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(side_effect=IndexError())
        session.set_exec_result([mock_row])
        result = task_service.list_tasks()
        assert len(result) == 0

    def test_list_tasks_row_object_getitem_key_error(
        self, task_service: TaskService, session: DummySession
    ) -> None:
        """Test list_tasks handles KeyError from Row object."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(side_effect=KeyError())
        session.set_exec_result([mock_row])
        result = task_service.list_tasks()
        assert len(result) == 0

    def test_list_tasks_unexpected_type(
        self, task_service: TaskService, session: DummySession
    ) -> None:
        """Test list_tasks handles unexpected result types."""
        unexpected = Mock()
        del unexpected._mapping
        del unexpected.__getitem__
        session.set_exec_result([unexpected])
        result = task_service.list_tasks()
        assert len(result) == 0


class TestUpdateTaskProgress:
    """Test update_task_progress method."""

    def test_update_task_progress_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test update_task_progress updates task progress."""
        session._entities_by_class_and_id[Task] = {1: task}
        task_service.update_task_progress(1, 0.5)
        assert task.progress == 0.5
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]

    def test_update_task_progress_with_metadata(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test update_task_progress updates metadata."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.task_data = {"existing": "value"}
        task_service.update_task_progress(1, 0.5, {"new": "data"})
        assert task.progress == 0.5
        assert task.task_data == {"existing": "value", "new": "data"}

    def test_update_task_progress_with_metadata_no_task_data(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test update_task_progress creates task_data if None."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.task_data = None
        task_service.update_task_progress(1, 0.5, {"new": "data"})
        assert task.task_data == {"new": "data"}

    def test_update_task_progress_task_not_found(
        self, task_service: TaskService
    ) -> None:
        """Test update_task_progress raises ValueError when task not found."""
        with pytest.raises(ValueError, match="Task 999 not found"):
            task_service.update_task_progress(999, 0.5)

    @pytest.mark.parametrize("progress", [-0.1, 1.1, 2.0])
    def test_update_task_progress_invalid_progress(
        self,
        task_service: TaskService,
        task: Task,
        session: DummySession,
        progress: float,
    ) -> None:
        """Test update_task_progress raises ValueError for invalid progress."""
        session._entities_by_class_and_id[Task] = {1: task}
        with pytest.raises(ValueError, match=r"Progress must be between 0.0 and 1.0"):
            task_service.update_task_progress(1, progress)


class TestStartTask:
    """Test start_task method."""

    def test_start_task_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test start_task marks task as running."""
        session._entities_by_class_and_id[Task] = {1: task}
        task_service.start_task(1)
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]

    def test_start_task_not_found(self, task_service: TaskService) -> None:
        """Test start_task raises ValueError when task not found."""
        with pytest.raises(ValueError, match="Task 999 not found"):
            task_service.start_task(999)


class TestCompleteTask:
    """Test complete_task method."""

    def test_complete_task_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test complete_task marks task as completed."""
        session._entities_by_class_and_id[Task] = {1: task}
        task_service.complete_task(1)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0
        assert task.completed_at is not None
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]
        assert task in session.refreshed

    def test_complete_task_with_metadata(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test complete_task merges metadata."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.task_data = {"existing": "value"}
        task_service.complete_task(1, {"new": "data"})
        assert task.task_data == {"existing": "value", "new": "data"}

    def test_complete_task_with_metadata_no_task_data(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test complete_task creates task_data if None."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.task_data = None
        task_service.complete_task(1, {"new": "data"})
        assert task.task_data == {"new": "data"}

    def test_complete_task_with_normalize_metadata_false(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test complete_task with normalize_metadata=False."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.task_data = {"existing": "value"}
        task_service.complete_task(1, {"new": "data"}, normalize_metadata=False)
        assert task.task_data == {"existing": "value", "new": "data"}

    def test_complete_task_not_found(self, task_service: TaskService) -> None:
        """Test complete_task raises ValueError when task not found."""
        with pytest.raises(ValueError, match="Task 999 not found"):
            task_service.complete_task(999)


class TestFailTask:
    """Test fail_task method."""

    def test_fail_task_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test fail_task marks task as failed."""
        session._entities_by_class_and_id[Task] = {1: task}
        task_service.fail_task(1, "Error message")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Error message"
        assert task.completed_at is not None
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]

    def test_fail_task_truncates_long_message(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test fail_task truncates error message if too long."""
        session._entities_by_class_and_id[Task] = {1: task}
        long_message = "x" * 3000
        task_service.fail_task(1, long_message)
        assert task.error_message is not None
        assert len(task.error_message) == 2000
        assert task.error_message == long_message[:2000]

    def test_fail_task_not_found(self, task_service: TaskService) -> None:
        """Test fail_task raises ValueError when task not found."""
        with pytest.raises(ValueError, match="Task 999 not found"):
            task_service.fail_task(999, "Error")


class TestCancelTask:
    """Test cancel_task method."""

    def test_cancel_task_success(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test cancel_task cancels pending task."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.cancel_task(1)
        assert result is True
        assert task.status == TaskStatus.CANCELLED
        assert task.cancelled_at is not None
        assert task_service._session.commit_count == 1  # type: ignore[attr-defined]

    def test_cancel_task_not_found(self, task_service: TaskService) -> None:
        """Test cancel_task returns False when task not found."""
        result = task_service.cancel_task(999)
        assert result is False

    def test_cancel_task_with_user_id_match(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test cancel_task cancels when user_id matches."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.cancel_task(1, user_id=1)
        assert result is True

    def test_cancel_task_with_user_id_mismatch(
        self, task_service: TaskService, task: Task, session: DummySession
    ) -> None:
        """Test cancel_task returns False when user_id doesn't match."""
        session._entities_by_class_and_id[Task] = {1: task}
        result = task_service.cancel_task(1, user_id=999)
        assert result is False

    @pytest.mark.parametrize(
        "status",
        [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
    )
    def test_cancel_task_already_complete(
        self,
        task_service: TaskService,
        task: Task,
        session: DummySession,
        status: TaskStatus,
    ) -> None:
        """Test cancel_task returns False when task already complete."""
        session._entities_by_class_and_id[Task] = {1: task}
        task.status = status
        result = task_service.cancel_task(1)
        assert result is False


class TestGetTaskStatistics:
    """Test get_task_statistics method."""

    def test_get_task_statistics_all(
        self,
        task_service: TaskService,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test get_task_statistics returns all statistics."""
        stats_list = [task_statistics]
        session.set_exec_result(stats_list)
        result = task_service.get_task_statistics()
        assert len(result) == 1

    def test_get_task_statistics_with_task_type(
        self,
        task_service: TaskService,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test get_task_statistics filters by task_type."""
        session.set_exec_result([task_statistics])
        result = task_service.get_task_statistics(task_type=TaskType.BOOK_UPLOAD)
        assert len(result) == 1


class TestExtractTaskStatistics:
    """Test _extract_task_statistics method."""

    def test_extract_task_statistics_from_instance(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _extract_task_statistics returns TaskStatistics instance."""
        result = task_service._extract_task_statistics(task_statistics)
        assert result == task_statistics

    def test_extract_task_statistics_from_mapping(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _extract_task_statistics extracts from _mapping."""
        mock_row = Mock()
        mock_row._mapping = {"TaskStatistics": task_statistics}
        result = task_service._extract_task_statistics(mock_row)
        assert result == task_statistics

    def test_extract_task_statistics_from_getitem(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _extract_task_statistics extracts from __getitem__."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(return_value=task_statistics)
        result = task_service._extract_task_statistics(mock_row)
        assert result == task_statistics

    def test_extract_task_statistics_getitem_index_error(
        self, task_service: TaskService
    ) -> None:
        """Test _extract_task_statistics handles IndexError."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(side_effect=IndexError())
        result = task_service._extract_task_statistics(mock_row)
        assert result is None

    def test_extract_task_statistics_getitem_key_error(
        self, task_service: TaskService
    ) -> None:
        """Test _extract_task_statistics handles KeyError."""
        mock_row = Mock()
        del mock_row._mapping
        mock_row.__getitem__ = Mock(side_effect=KeyError())
        result = task_service._extract_task_statistics(mock_row)
        assert result is None

    def test_extract_task_statistics_no_mapping_no_getitem(
        self, task_service: TaskService
    ) -> None:
        """Test _extract_task_statistics returns None for invalid object."""
        invalid = Mock()
        del invalid._mapping
        del invalid.__getitem__
        result = task_service._extract_task_statistics(invalid)
        assert result is None


class TestUpdateStatisticsDuration:
    """Test _update_statistics_duration method."""

    def test_update_statistics_duration_first_update(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration sets initial values."""
        task_service._update_statistics_duration(task_statistics, 10.5, 1)
        assert task_statistics.avg_duration == 10.5
        assert task_statistics.min_duration == 10.5
        assert task_statistics.max_duration == 10.5

    def test_update_statistics_duration_running_average(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration calculates running average."""
        task_statistics.avg_duration = 10.0
        task_statistics.min_duration = 5.0
        task_statistics.max_duration = 15.0
        task_service._update_statistics_duration(task_statistics, 20.0, 2)
        assert task_statistics.avg_duration == 15.0  # (10.0 * 1 + 20.0) / 2
        assert task_statistics.min_duration == 5.0
        assert task_statistics.max_duration == 20.0

    def test_update_statistics_duration_updates_min(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration updates min duration."""
        task_statistics.avg_duration = 10.0
        task_statistics.min_duration = 5.0
        task_statistics.max_duration = 15.0
        task_service._update_statistics_duration(task_statistics, 3.0, 2)
        assert task_statistics.min_duration == 3.0

    def test_update_statistics_duration_updates_max(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration updates max duration."""
        task_statistics.avg_duration = 10.0
        task_statistics.min_duration = 5.0
        task_statistics.max_duration = 15.0
        task_service._update_statistics_duration(task_statistics, 25.0, 2)
        assert task_statistics.max_duration == 25.0

    def test_update_statistics_duration_min_none(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration handles None min_duration."""
        task_statistics.avg_duration = 10.0
        task_statistics.min_duration = None
        task_statistics.max_duration = 15.0
        task_service._update_statistics_duration(task_statistics, 5.0, 2)
        assert task_statistics.min_duration == 5.0

    def test_update_statistics_duration_max_none(
        self, task_service: TaskService, task_statistics: TaskStatistics
    ) -> None:
        """Test _update_statistics_duration handles None max_duration."""
        task_statistics.avg_duration = 10.0
        task_statistics.min_duration = 5.0
        task_statistics.max_duration = None
        task_service._update_statistics_duration(task_statistics, 25.0, 2)
        assert task_statistics.max_duration == 25.0


class TestRecordTaskCompletion:
    """Test record_task_completion method."""

    def test_record_task_completion_task_not_found(
        self, task_service: TaskService
    ) -> None:
        """Test record_task_completion returns early when task not found."""
        task_service.record_task_completion(999, TaskStatus.COMPLETED)
        assert task_service._session.commit_count == 0  # type: ignore[attr-defined]

    def test_record_task_completion_creates_statistics(
        self,
        task_service: TaskService,
        task: Task,
        session: DummySession,
    ) -> None:
        """Test record_task_completion creates statistics if not exists."""
        session._entities_by_class_and_id[Task] = {1: task}
        session.set_exec_result([])  # No existing statistics
        # Clear any previously added entities
        session.added.clear()  # type: ignore[attr-defined]
        task_service.record_task_completion(1, TaskStatus.COMPLETED, duration=10.5)
        # Statistics should be added
        stats_added = [e for e in session.added if isinstance(e, TaskStatistics)]  # type: ignore[attr-defined]
        assert len(stats_added) == 1
        stats = stats_added[0]
        assert stats.total_count == 1
        assert stats.success_count == 1
        assert stats.failure_count == 0

    def test_record_task_completion_updates_existing_statistics(
        self,
        task_service: TaskService,
        task: Task,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test record_task_completion updates existing statistics."""
        session._entities_by_class_and_id[Task] = {1: task}
        session.set_exec_result([task_statistics])
        task_service.record_task_completion(1, TaskStatus.COMPLETED, duration=10.5)
        assert task_statistics.total_count == 1
        assert task_statistics.success_count == 1
        assert task_statistics.failure_count == 0
        assert task_statistics.avg_duration == 10.5

    def test_record_task_completion_failed_status(
        self,
        task_service: TaskService,
        task: Task,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test record_task_completion updates failure_count for failed status."""
        session._entities_by_class_and_id[Task] = {1: task}
        session.set_exec_result([task_statistics])
        task_service.record_task_completion(1, TaskStatus.FAILED)
        assert task_statistics.total_count == 1
        assert task_statistics.success_count == 0
        assert task_statistics.failure_count == 1

    def test_record_task_completion_with_duration(
        self,
        task_service: TaskService,
        task: Task,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test record_task_completion updates duration statistics."""
        session._entities_by_class_and_id[Task] = {1: task}
        session.set_exec_result([task_statistics])
        task_service.record_task_completion(1, TaskStatus.COMPLETED, duration=15.0)
        assert task_statistics.avg_duration == 15.0
        assert task_statistics.min_duration == 15.0
        assert task_statistics.max_duration == 15.0

    def test_record_task_completion_without_duration(
        self,
        task_service: TaskService,
        task: Task,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test record_task_completion doesn't update duration if None."""
        session._entities_by_class_and_id[Task] = {1: task}
        session.set_exec_result([task_statistics])
        task_statistics.avg_duration = 10.0
        task_service.record_task_completion(1, TaskStatus.COMPLETED, duration=None)
        assert task_statistics.avg_duration == 10.0  # Unchanged

    def test_record_task_completion_extracts_from_row(
        self,
        task_service: TaskService,
        task: Task,
        task_statistics: TaskStatistics,
        session: DummySession,
    ) -> None:
        """Test record_task_completion extracts statistics from Row object."""
        session._entities_by_class_and_id[Task] = {1: task}
        mock_row = Mock()
        mock_row._mapping = {"TaskStatistics": task_statistics}
        session.set_exec_result([mock_row])
        task_service.record_task_completion(1, TaskStatus.COMPLETED)
        assert task_statistics.total_count == 1

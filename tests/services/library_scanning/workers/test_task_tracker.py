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

"""Tests for ScanTaskTracker to achieve 100% coverage."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from fundamental.services.library_scanning.workers.task_tracker import ScanTaskTracker


@pytest.fixture
def tracker() -> ScanTaskTracker:
    """Create ScanTaskTracker instance.

    Returns
    -------
    ScanTaskTracker
        Tracker instance.
    """
    with patch(
        "fundamental.services.library_scanning.workers.task_tracker.create_db_engine"
    ):
        return ScanTaskTracker()


class TestScanTaskTrackerInit:
    """Test ScanTaskTracker initialization."""

    def test_init_creates_engine(self) -> None:
        """Test __init__ creates engine (covers line 50)."""
        with patch(
            "fundamental.services.library_scanning.workers.task_tracker.create_db_engine"
        ) as mock_create:
            tracker = ScanTaskTracker()
            assert tracker.engine is not None
            mock_create.assert_called_once()


class TestScanTaskTrackerStartTask:
    """Test ScanTaskTracker.start_task method."""

    def test_start_task_success(self, tracker: ScanTaskTracker) -> None:
        """Test start_task successfully starts task (covers line 60).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        with patch.object(tracker, "_with_retry") as mock_retry:
            tracker.start_task(123)
            mock_retry.assert_called_once()
            call_args = mock_retry.call_args
            assert "start task 123" in str(call_args)


class TestScanTaskTrackerUpdateStageProgress:
    """Test ScanTaskTracker.update_stage_progress method."""

    @pytest.mark.parametrize(
        ("stage", "stage_progress", "metadata"),
        [
            ("crawl", 0.0, None),
            ("match", 0.5, {"extra": "data"}),
            ("ingest", 1.0, None),
            ("link", 0.0, {"key": "value"}),
            ("deduplicate", 0.5, None),
            ("score", 1.0, None),
        ],
    )
    def test_update_stage_progress(
        self,
        tracker: ScanTaskTracker,
        stage: str,
        stage_progress: float,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Test update_stage_progress (covers lines 86-113).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        stage : str
            Stage name.
        stage_progress : float
            Stage progress.
        metadata : dict[str, Any] | None
            Optional metadata.
        """
        with patch.object(tracker, "_with_retry") as mock_retry:
            tracker.update_stage_progress(123, stage, stage_progress, metadata)
            mock_retry.assert_called_once()
            call_args = mock_retry.call_args
            assert "update task 123 progress" in str(call_args)


class TestScanTaskTrackerCompleteTask:
    """Test ScanTaskTracker.complete_task method."""

    @pytest.mark.parametrize(
        ("task_id", "metadata"),
        [
            (123, None),
            (456, {"result": "success"}),
        ],
    )
    def test_complete_task(
        self,
        tracker: ScanTaskTracker,
        task_id: int,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Test complete_task (covers lines 129-136).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        task_id : int
            Task ID.
        metadata : dict[str, Any] | None
            Optional metadata.
        """
        with patch.object(tracker, "_with_retry") as mock_retry:
            tracker.complete_task(task_id, metadata)
            mock_retry.assert_called_once()
            call_args = mock_retry.call_args
            assert f"complete task {task_id}" in str(call_args)


class TestScanTaskTrackerFailTask:
    """Test ScanTaskTracker.fail_task method."""

    @pytest.mark.parametrize(
        ("task_id", "error_message"),
        [
            (123, "Test error"),
            (456, "Another error"),
        ],
    )
    def test_fail_task(
        self,
        tracker: ScanTaskTracker,
        task_id: int,
        error_message: str,
    ) -> None:
        """Test fail_task (covers lines 152-157).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        task_id : int
            Task ID.
        error_message : str
            Error message.
        """
        with patch.object(tracker, "_with_retry") as mock_retry:
            tracker.fail_task(task_id, error_message)
            mock_retry.assert_called_once()
            call_args = mock_retry.call_args
            assert f"fail task {task_id}" in str(call_args)


class TestScanTaskTrackerGetStageRange:
    """Test ScanTaskTracker._get_stage_range method."""

    @pytest.mark.parametrize(
        ("stage", "expected_range"),
        [
            ("crawl", 0.1),
            ("match", 0.2),
            ("ingest", 0.2),
            ("link", 0.1),
            ("deduplicate", 0.2),
            ("score", 0.15),
            ("completion", 0.05),
            ("unknown", 0.0),
        ],
    )
    def test_get_stage_range(
        self, tracker: ScanTaskTracker, stage: str, expected_range: float
    ) -> None:
        """Test _get_stage_range (covers lines 172-179).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        stage : str
            Stage name.
        expected_range : float
            Expected range.
        """
        result = tracker._get_stage_range(stage)
        # Use approximate comparison for floating point values
        assert abs(result - expected_range) < 0.0001


class TestScanTaskTrackerWithRetry:
    """Test ScanTaskTracker._with_retry method."""

    def test_with_retry_success(self, tracker: ScanTaskTracker) -> None:
        """Test _with_retry succeeds on first attempt.

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        mock_operation = MagicMock()
        with patch(
            "fundamental.services.library_scanning.workers.task_tracker.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            tracker._with_retry(mock_operation, "test operation")
            mock_operation.assert_called_once_with(mock_session)

    def test_with_retry_operational_error_retries(
        self, tracker: ScanTaskTracker
    ) -> None:
        """Test _with_retry retries on OperationalError (covers lines 198-233).

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        mock_operation = MagicMock()
        lock_error = OperationalError(
            "statement", None, RuntimeError("database is locked")
        )

        with (
            patch(
                "fundamental.services.library_scanning.workers.task_tracker.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.task_tracker.time.sleep"
            ) as mock_sleep,
            patch(
                "fundamental.services.library_scanning.workers.task_tracker.random.uniform"
            ) as mock_uniform,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # First call raises lock error, second succeeds
            mock_operation.side_effect = [lock_error, None]

            tracker._with_retry(mock_operation, "test operation", max_retries=2)

            assert mock_operation.call_count == 2
            mock_sleep.assert_called_once()
            mock_uniform.assert_called_once()

    def test_with_retry_operational_error_max_retries(
        self, tracker: ScanTaskTracker
    ) -> None:
        """Test _with_retry raises after max retries.

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        mock_operation = MagicMock()
        lock_error = OperationalError(
            "statement", None, RuntimeError("database is locked")
        )

        with (
            patch(
                "fundamental.services.library_scanning.workers.task_tracker.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.task_tracker.time.sleep"
            ),
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Always raises lock error
            mock_operation.side_effect = lock_error

            with pytest.raises(OperationalError):
                tracker._with_retry(mock_operation, "test operation", max_retries=2)

    def test_with_retry_other_exception(self, tracker: ScanTaskTracker) -> None:
        """Test _with_retry raises on non-lock error.

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        mock_operation = MagicMock()
        other_error = ValueError("Other error")

        with patch(
            "fundamental.services.library_scanning.workers.task_tracker.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_operation.side_effect = other_error

            with pytest.raises(ValueError, match="Other error"):
                tracker._with_retry(mock_operation, "test operation")

    def test_with_retry_operational_error_not_locked(
        self, tracker: ScanTaskTracker
    ) -> None:
        """Test _with_retry raises on OperationalError that's not a lock error.

        Parameters
        ----------
        tracker : ScanTaskTracker
            Tracker instance.
        """
        mock_operation = MagicMock()
        other_operational_error = OperationalError(
            "statement", None, RuntimeError("other error")
        )

        with patch(
            "fundamental.services.library_scanning.workers.task_tracker.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_operation.side_effect = other_operational_error

            with pytest.raises(OperationalError):
                tracker._with_retry(mock_operation, "test operation")

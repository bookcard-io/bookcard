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

"""Tests for LibraryScanTask."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.library_scanning import LibraryScanState
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.tasks.library_scan_task import LibraryScanTask


class TestLibraryScanTask:
    """Tests for LibraryScanTask."""

    def test_monitor_scan_progress_missing_state_retry_limit(self) -> None:
        """Test that monitor raises RuntimeError if state is missing for too long."""
        task = LibraryScanTask(task_id=1, user_id=1, metadata={})
        mock_session = MagicMock()
        mock_tracker = MagicMock(spec=JobProgressTracker)

        # Mock session.get to always return None
        mock_session.get.return_value = None
        mock_session.expire_all.return_value = None

        # Patch time.sleep specifically in the module under test
        with patch(
            "bookcard.services.tasks.library_scan_task.time.sleep"
        ) as mock_sleep:
            with pytest.raises(
                RuntimeError, match="disappeared or cannot be retrieved"
            ):
                task._monitor_scan_progress(mock_tracker, 1, mock_session)

            # Verify it retried enough times to hit limit
            assert mock_session.get.call_count >= 13
            assert mock_sleep.call_count >= 12

    def test_monitor_scan_progress_recovers_after_missing_state(self) -> None:
        """Test that monitor recovers if state appears after being missing."""
        task = LibraryScanTask(task_id=1, user_id=1, metadata={})
        mock_session = MagicMock()
        mock_tracker = MagicMock(spec=JobProgressTracker)

        # Mock session.get to return None twice, then a completed state
        completed_state = MagicMock(spec=LibraryScanState)
        completed_state.scan_status = "completed"

        mock_session.get.side_effect = [None, None, completed_state]
        mock_session.expire_all.return_value = None

        with (
            patch.object(task, "update_progress") as mock_update_progress,
            patch("bookcard.services.tasks.library_scan_task.time.sleep") as mock_sleep,
        ):
            task._monitor_scan_progress(mock_tracker, 1, mock_session)

            # Should not raise exception
            assert mock_session.get.call_count == 3
            assert mock_sleep.call_count == 2
            mock_update_progress.assert_called_with(1.0)

    def test_monitor_scan_progress_db_failure_retry_limit(self) -> None:
        """Test that monitor raises RuntimeError if DB fetch fails for too long."""
        task = LibraryScanTask(task_id=1, user_id=1, metadata={})
        mock_session = MagicMock()
        mock_tracker = MagicMock(spec=JobProgressTracker)

        # Mock session.get to always raise Exception
        mock_session.get.side_effect = Exception("DB Connection failed")
        mock_session.expire_all.return_value = None

        with patch(
            "bookcard.services.tasks.library_scan_task.time.sleep"
        ) as mock_sleep:
            with pytest.raises(
                RuntimeError, match="disappeared or cannot be retrieved"
            ):
                task._monitor_scan_progress(mock_tracker, 1, mock_session)

            assert mock_session.get.call_count >= 13
            assert mock_sleep.call_count >= 12

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

"""Tests for library scan monitoring behavior."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from bookcard.services.tasks.library_scan.errors import (
    ScanFailedError,
    ScanStateUnavailableError,
)
from bookcard.services.tasks.library_scan.monitor import ScanProgressMonitor
from bookcard.services.tasks.library_scan.state_repository import (
    LibraryScanStateRepository,
)


@dataclass
class _State:
    scan_status: str


class TestScanProgressMonitor:
    """Unit tests for ``ScanProgressMonitor``."""

    def test_missing_state_retry_limit(self) -> None:
        """Monitor raises when state is missing for too long."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.get_by_library_id.return_value = None
        repo.refresh_view.return_value = None

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )

        with pytest.raises(
            ScanStateUnavailableError, match="disappeared or cannot be retrieved"
        ):
            monitor.wait_for_terminal_state(1)

        assert repo.get_by_library_id.call_count >= 13
        assert len(sleep_calls) >= 12

    def test_recovers_after_missing_state(self) -> None:
        """Monitor succeeds when state eventually appears as completed."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.side_effect = [None, None, _State("completed")]

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        progress: list[float] = []

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )
        monitor.wait_for_terminal_state(1, on_terminal_progress=progress.append)

        assert repo.get_by_library_id.call_count == 3
        assert len(sleep_calls) == 2
        assert progress == [1.0]

    def test_db_failure_retry_limit(self) -> None:
        """Monitor raises when DB errors persist."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.side_effect = SQLAlchemyError("DB Connection failed")

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )

        with pytest.raises(
            ScanStateUnavailableError, match="disappeared or cannot be retrieved"
        ):
            monitor.wait_for_terminal_state(1)

        assert repo.get_by_library_id.call_count >= 13
        assert len(sleep_calls) >= 12

    def test_failed_state_raises(self) -> None:
        """Monitor raises when scan is marked failed."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.return_value = _State("failed")

        monitor = ScanProgressMonitor(
            repo, sleep=lambda _: None, poll_interval_seconds=0.0
        )

        with pytest.raises(ScanFailedError, match="marked in ScanState"):
            monitor.wait_for_terminal_state(1)

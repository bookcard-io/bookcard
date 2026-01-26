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

"""Scan progress monitoring.

This module contains a polling monitor that watches the scan state in the DB.
It is isolated to keep the task adapter thin and to allow focused unit tests.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError

from bookcard.services.tasks.library_scan.errors import (
    ScanFailedError,
    ScanStateUnavailableError,
)
from bookcard.services.tasks.library_scan.types import ScanStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.services.tasks.library_scan.state_repository import (
        LibraryScanStateRepository,
    )


class ScanProgressMonitor:
    """Polls scan state until completion, failure, or cancellation.

    Parameters
    ----------
    state_repo : LibraryScanStateRepository
        Repository for reading scan state.
    sleep : Callable[[float], None], optional
        Sleep function, injected for testability.
    poll_interval_seconds : float, optional
        Polling interval in seconds.
    max_missing_state_retries : int, optional
        Maximum consecutive retries allowed when state is missing or cannot be read.
    """

    def __init__(
        self,
        state_repo: LibraryScanStateRepository,
        *,
        sleep: Callable[[float], None] = time.sleep,
        poll_interval_seconds: float = 5.0,
        max_missing_state_retries: int = 12,
    ) -> None:
        self._state_repo = state_repo
        self._sleep = sleep
        self._poll_interval_seconds = float(poll_interval_seconds)
        self._max_missing_state_retries = int(max_missing_state_retries)

    def wait_for_terminal_state(
        self,
        library_id: int,
        *,
        is_cancelled: Callable[[], bool] | None = None,
        on_terminal_progress: Callable[[float], None] | None = None,
    ) -> None:
        """Wait until scan reaches a terminal state.

        Parameters
        ----------
        library_id : int
            Library identifier.
        is_cancelled : Callable[[], bool] | None, optional
            Cancellation predicate. When it returns True, monitoring stops early.
        on_terminal_progress : Callable[[float], None] | None, optional
            Optional callback invoked when a terminal state is reached. Used to
            update unified task progress (e.g., set to 1.0 on completion).

        Raises
        ------
        ScanFailedError
            If the scan state is marked as failed.
        ScanStateUnavailableError
            If scan state cannot be retrieved within retry limits.
        """
        consecutive_missing_or_error = 0

        while True:
            if is_cancelled is not None and is_cancelled():
                return

            try:
                self._state_repo.refresh_view()
                state = self._state_repo.get_by_library_id(library_id)
            except SQLAlchemyError as exc:
                consecutive_missing_or_error += 1
                if consecutive_missing_or_error > self._max_missing_state_retries:
                    msg = (
                        f"Scan state for library {library_id} disappeared or cannot be retrieved "
                        "after multiple attempts."
                    )
                    raise ScanStateUnavailableError(msg) from exc
                self._sleep(self._poll_interval_seconds)
                continue

            if state is None:
                consecutive_missing_or_error += 1
                if consecutive_missing_or_error > self._max_missing_state_retries:
                    msg = (
                        f"Scan state for library {library_id} disappeared or cannot be retrieved "
                        "after multiple attempts."
                    )
                    raise ScanStateUnavailableError(msg)
                self._sleep(self._poll_interval_seconds)
                continue

            consecutive_missing_or_error = 0

            status = state.scan_status
            if status == ScanStatus.COMPLETED.value:
                if on_terminal_progress is not None:
                    on_terminal_progress(1.0)
                return
            if status == ScanStatus.FAILED.value:
                msg = "Library scan failed (marked in ScanState)"
                raise ScanFailedError(msg)

            self._sleep(self._poll_interval_seconds)

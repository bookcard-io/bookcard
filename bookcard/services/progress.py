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

"""Shared progress tracking utilities.

Provides common progress tracking and reporting functionality following
DRY principles and improving code cohesion. This module is independent
of the task system to avoid circular import issues.
"""


def calculate_progress(current: int, total: int) -> float:
    """Calculate progress as a float between 0.0 and 1.0.

    Parameters
    ----------
    current : int
        Current number of items processed.
    total : int
        Total number of items to process.

    Returns
    -------
    float
        Progress value between 0.0 and 1.0.
    """
    if total > 0:
        return min(1.0, max(0.0, current / total))
    return 0.0


def calculate_log_interval(total_items: int, default_interval: int = 25) -> int:
    """Calculate appropriate log interval based on total items.

    Uses 10% of total or default interval, whichever is more frequent.

    Parameters
    ----------
    total_items : int
        Total number of items to process.
    default_interval : int
        Default interval to use. Defaults to 25.

    Returns
    -------
    int
        Calculated log interval (at least 1).
    """
    if total_items <= 0:
        return 1
    percentage_interval = max(1, total_items // 10)
    return max(1, min(default_interval, percentage_interval))


def should_log_progress(current: int, total: int, log_interval: int) -> bool:
    """Check if progress should be logged at current position.

    Parameters
    ----------
    current : int
        Current number of items processed.
    total : int
        Total number of items to process.
    log_interval : int
        Interval between progress logs.

    Returns
    -------
    bool
        True if progress should be logged, False otherwise.
    """
    return current % log_interval == 0 or current == total


class BaseProgressTracker:
    """Base class for progress tracking with shared functionality.

    Provides common progress tracking logic that can be reused by
    different progress tracker implementations, following DRY principles.

    Parameters
    ----------
    total_items : int
        Total number of items to process.
    log_interval : int
        Interval between progress logs.
    """

    def __init__(self, total_items: int, log_interval: int) -> None:
        """Initialize base progress tracker.

        Parameters
        ----------
        total_items : int
            Total number of items to process.
        log_interval : int
            Interval between progress logs.
        """
        self.total_items = total_items
        self.processed_items = 0
        self.log_interval = log_interval
        self._progress = 0.0

    def _update_progress(self, current: int) -> float:
        """Update internal progress state.

        Parameters
        ----------
        current : int
            Current number of items processed.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        self.processed_items = current
        self._progress = calculate_progress(current, self.total_items)
        return self._progress

    def should_log_at(self, current: int) -> bool:
        """Check if progress should be logged at current position.

        Parameters
        ----------
        current : int
            Current number of items processed.

        Returns
        -------
        bool
            True if progress should be logged, False otherwise.
        """
        return should_log_progress(current, self.total_items, self.log_interval)

    @property
    def progress(self) -> float:
        """Get current progress.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress


__all__ = [
    "BaseProgressTracker",
    "calculate_log_interval",
    "calculate_progress",
    "should_log_progress",
]

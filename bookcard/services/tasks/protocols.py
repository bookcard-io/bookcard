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

"""Shared protocols for task system.

These protocols define generic interfaces that can be used across
different task implementations, allowing for dependency injection
and improved testability following the Dependency Inversion Principle.
"""

from typing import Any, Protocol


class ProgressReporter(Protocol):
    """Protocol for progress reporting.

    Allows different implementations of progress reporting to be injected,
    improving testability and flexibility.
    """

    def report(self, progress: float, metadata: dict[str, Any] | None = None) -> None:
        """Report progress.

        Parameters
        ----------
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict[str, Any] | None
            Optional metadata to include with progress update.
        """
        ...


class CancellationChecker(Protocol):
    """Protocol for checking task cancellation.

    Allows different cancellation checking mechanisms to be injected.
    """

    def is_cancelled(self) -> bool:
        """Check if task is cancelled.

        Returns
        -------
        bool
            True if task has been cancelled, False otherwise.
        """
        ...


__all__ = [
    "CancellationChecker",
    "ProgressReporter",
]

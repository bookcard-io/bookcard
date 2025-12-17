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

"""Progress reporting adapter for OpenLibrary tasks.

Provides task-specific progress reporting adapter that implements
the ProgressReporter protocol for use in the task system.
"""

from collections.abc import Callable
from typing import Any


class ProgressReporterAdapter:
    """Adapter for progress update callback implementing ProgressReporter protocol.

    Converts the existing callback-based progress reporting to the
    ProgressReporter protocol, providing a unified interface.

    Parameters
    ----------
    update_progress : Callable
        Progress update callback function that accepts (progress, metadata).
    """

    def __init__(
        self, update_progress: Callable[[float, dict[str, Any] | None], None]
    ) -> None:
        """Initialize progress reporter adapter.

        Parameters
        ----------
        update_progress : Callable
            Progress update callback function.
        """
        self.update_progress = update_progress

    def report(self, progress: float, metadata: dict[str, Any] | None = None) -> None:
        """Report progress.

        Parameters
        ----------
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict[str, Any] | None
            Optional metadata to include with progress update.
        """
        self.update_progress(progress, metadata)

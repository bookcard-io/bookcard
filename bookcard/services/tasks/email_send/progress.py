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

"""Progress tracking for email send task.

Decouples progress tracking from business logic following SRP.
"""

from collections.abc import Callable

from bookcard.services.tasks.context import ProgressCallback


class ProgressTracker:
    """Tracks progress through discrete steps.

    Provides a clean interface for progress updates without hard-coding
    progress values throughout the business logic.
    """

    def __init__(
        self,
        callback: ProgressCallback,
        total_steps: int,
        check_cancellation: Callable[[], None],
    ) -> None:
        """Initialize progress tracker.

        Parameters
        ----------
        callback : ProgressCallback
            Progress update callback.
        total_steps : int
            Total number of steps in the process.
        check_cancellation : Callable[[], None]
            Function to check for cancellation (raises if cancelled).
        """
        self.callback = callback
        self.total_steps = total_steps
        self.current_step = 0
        self.check_cancellation = check_cancellation

    def advance(self, message: str | None = None) -> None:
        """Advance to next step and update progress.

        Parameters
        ----------
        message : str | None
            Optional progress message.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        self.check_cancellation()
        self.current_step += 1
        progress = self.current_step / self.total_steps
        metadata = {"message": message} if message is not None else None
        self.callback(progress, metadata)

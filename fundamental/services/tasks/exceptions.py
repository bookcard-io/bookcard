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

"""Domain-specific exceptions for task operations.

Provides clear exception hierarchy for better error handling.
Follows Open/Closed Principle by using domain-specific exceptions
instead of generic ValueError.
"""


class TaskError(Exception):
    """Base exception for task errors."""


class TaskCancelledError(TaskError):
    """Exception raised when task is cancelled.

    Follows DRY by centralizing cancellation handling.
    """

    def __init__(self, task_id: int) -> None:
        """Initialize cancellation error.

        Parameters
        ----------
        task_id : int
            ID of the cancelled task.
        """
        super().__init__(f"Task {task_id} was cancelled")
        self.task_id = task_id


class LibraryNotConfiguredError(TaskError):
    """Raised when no active library is configured."""

    def __init__(self) -> None:
        """Initialize library not configured error."""
        super().__init__("No active library configured")


class EmailServerNotConfiguredError(TaskError):
    """Raised when email server is not configured or disabled."""

    def __init__(self) -> None:
        """Initialize email server not configured error."""
        super().__init__("email_server_not_configured_or_disabled")


class BookNotFoundError(TaskError):
    """Raised when book is not found."""

    def __init__(self, book_id: int) -> None:
        """Initialize book not found error.

        Parameters
        ----------
        book_id : int
            ID of the book that was not found.
        """
        self.book_id = book_id
        super().__init__(f"book_not_found: Book {book_id} not found")

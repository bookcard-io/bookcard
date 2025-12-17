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

"""Tests for task exceptions to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.services.tasks.exceptions import (
    BookNotFoundError,
    EmailServerNotConfiguredError,
    LibraryNotConfiguredError,
    TaskCancelledError,
    TaskError,
)


class TestTaskError:
    """Test TaskError base exception."""

    def test_task_error(self) -> None:
        """Test TaskError can be raised."""
        with pytest.raises(TaskError):
            raise TaskError("Test error")


class TestTaskCancelledError:
    """Test TaskCancelledError exception."""

    def test_task_cancelled_error(self) -> None:
        """Test TaskCancelledError initialization."""
        error = TaskCancelledError(task_id=123)

        assert error.task_id == 123
        assert str(error) == "Task 123 was cancelled"

    def test_task_cancelled_error_raises(self) -> None:
        """Test TaskCancelledError can be raised."""
        with pytest.raises(TaskCancelledError) as exc_info:
            raise TaskCancelledError(task_id=456)

        assert exc_info.value.task_id == 456


class TestLibraryNotConfiguredError:
    """Test LibraryNotConfiguredError exception."""

    def test_library_not_configured_error(self) -> None:
        """Test LibraryNotConfiguredError initialization."""
        error = LibraryNotConfiguredError()

        assert str(error) == "No active library configured"

    def test_library_not_configured_error_raises(self) -> None:
        """Test LibraryNotConfiguredError can be raised."""
        with pytest.raises(LibraryNotConfiguredError):
            raise LibraryNotConfiguredError


class TestEmailServerNotConfiguredError:
    """Test EmailServerNotConfiguredError exception."""

    def test_email_server_not_configured_error(self) -> None:
        """Test EmailServerNotConfiguredError initialization."""
        error = EmailServerNotConfiguredError()

        assert str(error) == "email_server_not_configured_or_disabled"

    def test_email_server_not_configured_error_raises(self) -> None:
        """Test EmailServerNotConfiguredError can be raised."""
        with pytest.raises(EmailServerNotConfiguredError):
            raise EmailServerNotConfiguredError


class TestBookNotFoundError:
    """Test BookNotFoundError exception."""

    def test_book_not_found_error(self) -> None:
        """Test BookNotFoundError initialization (covers lines 73-74)."""
        error = BookNotFoundError(book_id=789)

        assert error.book_id == 789
        assert str(error) == "book_not_found: Book 789 not found"

    def test_book_not_found_error_raises(self) -> None:
        """Test BookNotFoundError can be raised."""
        with pytest.raises(BookNotFoundError) as exc_info:
            raise BookNotFoundError(book_id=999)

        assert exc_info.value.book_id == 999

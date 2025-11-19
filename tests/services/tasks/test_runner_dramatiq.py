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

"""Tests for DramatiqTaskRunner."""

from __future__ import annotations

import pytest

from fundamental.models.tasks import TaskType
from fundamental.services.tasks.runner_dramatiq import DramatiqTaskRunner


@pytest.fixture
def runner() -> DramatiqTaskRunner:
    """Return DramatiqTaskRunner instance for testing."""
    return DramatiqTaskRunner()


class TestDramatiqTaskRunnerEnqueue:
    """Test enqueue method."""

    def test_enqueue_raises_not_implemented(self, runner: DramatiqTaskRunner) -> None:
        """Test enqueue raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dramatiq task runner not yet implemented"
        ):
            runner.enqueue(
                task_type=TaskType.BOOK_UPLOAD,
                payload={"key": "value"},
                user_id=1,
                metadata={"meta": "data"},
            )


class TestDramatiqTaskRunnerCancel:
    """Test cancel method."""

    def test_cancel_raises_not_implemented(self, runner: DramatiqTaskRunner) -> None:
        """Test cancel raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dramatiq task runner not yet implemented"
        ):
            runner.cancel(task_id=1)


class TestDramatiqTaskRunnerGetStatus:
    """Test get_status method."""

    def test_get_status_raises_not_implemented(
        self, runner: DramatiqTaskRunner
    ) -> None:
        """Test get_status raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dramatiq task runner not yet implemented"
        ):
            runner.get_status(task_id=1)


class TestDramatiqTaskRunnerGetProgress:
    """Test get_progress method."""

    def test_get_progress_raises_not_implemented(
        self, runner: DramatiqTaskRunner
    ) -> None:
        """Test get_progress raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dramatiq task runner not yet implemented"
        ):
            runner.get_progress(task_id=1)

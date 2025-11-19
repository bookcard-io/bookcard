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

"""Tests for BaseTask.update_progress to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.services.tasks.base import BaseTask


class ConcreteTask(BaseTask):
    """Concrete implementation of BaseTask for testing."""

    def run(self, worker_context: object) -> None:
        """Dummy run implementation."""


class TestBaseTaskUpdateProgress:
    """Test BaseTask.update_progress method."""

    @pytest.fixture
    def task(self) -> ConcreteTask:
        """Create a concrete task instance."""
        return ConcreteTask(task_id=1, user_id=1, metadata={})

    @pytest.mark.parametrize(
        "progress",
        [0.0, 0.5, 1.0, 0.25, 0.75, 0.999, 0.001],
    )
    def test_update_progress_valid(self, task: ConcreteTask, progress: float) -> None:
        """Test update_progress accepts valid progress values."""
        # Should not raise
        task.update_progress(progress)

    @pytest.mark.parametrize(
        "progress",
        [-0.1, -1.0, 1.1, 2.0, -0.001],
    )
    def test_update_progress_invalid(self, task: ConcreteTask, progress: float) -> None:
        """Test update_progress raises ValueError for invalid progress."""
        with pytest.raises(ValueError, match=r"Progress must be between 0.0 and 1.0"):
            task.update_progress(progress)

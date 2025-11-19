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

"""Tests for CeleryTaskRunner."""

from __future__ import annotations

import pytest

from fundamental.models.tasks import TaskType
from fundamental.services.tasks.runner_celery import CeleryTaskRunner


@pytest.fixture
def runner() -> CeleryTaskRunner:
    """Return CeleryTaskRunner instance for testing."""
    return CeleryTaskRunner()


class TestCeleryTaskRunnerEnqueue:
    """Test enqueue method."""

    def test_enqueue_raises_not_implemented(self, runner: CeleryTaskRunner) -> None:
        """Test enqueue raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Celery task runner not yet implemented"
        ):
            runner.enqueue(
                task_type=TaskType.BOOK_UPLOAD,
                payload={"key": "value"},
                user_id=1,
                metadata={"meta": "data"},
            )


class TestCeleryTaskRunnerCancel:
    """Test cancel method."""

    def test_cancel_raises_not_implemented(self, runner: CeleryTaskRunner) -> None:
        """Test cancel raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Celery task runner not yet implemented"
        ):
            runner.cancel(task_id=1)


class TestCeleryTaskRunnerGetStatus:
    """Test get_status method."""

    def test_get_status_raises_not_implemented(self, runner: CeleryTaskRunner) -> None:
        """Test get_status raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Celery task runner not yet implemented"
        ):
            runner.get_status(task_id=1)


class TestCeleryTaskRunnerGetProgress:
    """Test get_progress method."""

    def test_get_progress_raises_not_implemented(
        self, runner: CeleryTaskRunner
    ) -> None:
        """Test get_progress raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Celery task runner not yet implemented"
        ):
            runner.get_progress(task_id=1)

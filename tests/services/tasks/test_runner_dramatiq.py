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

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.tasks.runner_dramatiq import DramatiqTaskRunner


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return mock SQLAlchemy engine."""
    return MagicMock()


@pytest.fixture
def runner(mock_engine: MagicMock) -> DramatiqTaskRunner:
    """Return DramatiqTaskRunner instance for testing."""
    # Mock dramatiq dependencies to avoid requiring Redis/dramatiq for tests
    mock_dramatiq = MagicMock()
    mock_broker = MagicMock()
    mock_worker = MagicMock()
    mock_actor = MagicMock()

    mock_dramatiq.Worker.return_value = mock_worker
    mock_dramatiq.set_broker = MagicMock()
    mock_dramatiq.actor.return_value = mock_actor

    with (
        patch("fundamental.services.tasks.runner_dramatiq.dramatiq", mock_dramatiq),
        patch(
            "fundamental.services.tasks.runner_dramatiq.RedisBroker",
            return_value=mock_broker,
        ),
        patch(
            "fundamental.services.tasks.runner_dramatiq.TimeLimit",
            return_value=MagicMock(),
        ),
        patch(
            "fundamental.services.tasks.runner_dramatiq.ShutdownNotifications",
            return_value=MagicMock(),
        ),
    ):
        return DramatiqTaskRunner(
            engine=mock_engine,
            redis_url="redis://localhost:6379/0",
        )


@pytest.mark.skipif(
    True, reason="DramatiqTaskRunner requires Redis and dramatiq package"
)
class TestDramatiqTaskRunnerEnqueue:
    """Test enqueue method."""

    def test_enqueue_creates_task(
        self, runner: DramatiqTaskRunner, mock_engine: MagicMock
    ) -> None:
        """Test enqueue creates task and sends to Dramatiq."""
        # This test would require mocking database operations
        # and Dramatiq actor.send() calls


@pytest.mark.skipif(
    True, reason="DramatiqTaskRunner requires Redis and dramatiq package"
)
class TestDramatiqTaskRunnerCancel:
    """Test cancel method."""

    def test_cancel_updates_task_status(
        self, runner: DramatiqTaskRunner, mock_engine: MagicMock
    ) -> None:
        """Test cancel updates task status in database."""
        # This test would require mocking database operations


@pytest.mark.skipif(
    True, reason="DramatiqTaskRunner requires Redis and dramatiq package"
)
class TestDramatiqTaskRunnerGetStatus:
    """Test get_status method."""

    def test_get_status_returns_task_status(
        self, runner: DramatiqTaskRunner, mock_engine: MagicMock
    ) -> None:
        """Test get_status retrieves task status from database."""
        # This test would require mocking database operations


@pytest.mark.skipif(
    True, reason="DramatiqTaskRunner requires Redis and dramatiq package"
)
class TestDramatiqTaskRunnerGetProgress:
    """Test get_progress method."""

    def test_get_progress_returns_task_progress(
        self, runner: DramatiqTaskRunner, mock_engine: MagicMock
    ) -> None:
        """Test get_progress retrieves task progress from database."""
        # This test would require mocking database operations

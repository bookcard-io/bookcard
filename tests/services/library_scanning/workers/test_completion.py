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

"""Tests for CompletionWorker to achieve 100% coverage."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.library_scanning.workers.completion import CompletionWorker
from fundamental.services.messaging.base import MessageBroker


@pytest.fixture
def mock_broker() -> MagicMock:
    """Create a mock message broker.

    Returns
    -------
    MagicMock
        Mock broker.
    """
    return MagicMock(spec=MessageBroker)


@pytest.fixture
def completion_worker(mock_broker: MagicMock) -> CompletionWorker:
    """Create CompletionWorker instance.

    Parameters
    ----------
    mock_broker : MagicMock
        Mock broker.

    Returns
    -------
    CompletionWorker
        Worker instance.
    """
    return CompletionWorker(mock_broker)


class TestCompletionWorkerInit:
    """Test CompletionWorker initialization."""

    def test_init_with_defaults(self, mock_broker: MagicMock) -> None:
        """Test __init__ with default parameters.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        worker = CompletionWorker(mock_broker)
        assert worker.broker == mock_broker
        assert worker.input_topic == "completion_jobs"
        assert worker.output_topic is None

    @pytest.mark.parametrize(
        ("input_topic", "output_topic"),
        [
            ("custom_input", None),
            ("custom_input", "custom_output"),
        ],
    )
    def test_init_with_custom_topics(
        self,
        mock_broker: MagicMock,
        input_topic: str,
        output_topic: str | None,
    ) -> None:
        """Test __init__ with custom topics.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        input_topic : str
            Input topic.
        output_topic : str | None
            Output topic.
        """
        worker = CompletionWorker(mock_broker, input_topic, output_topic)
        assert worker.input_topic == input_topic
        assert worker.output_topic == output_topic


class TestCompletionWorkerProcess:
    """Test CompletionWorker.process method."""

    @pytest.mark.parametrize(
        ("payload", "expected_task_id"),
        [
            ({"library_id": 1, "task_id": 123}, 123),
            ({"library_id": 1, "task_id": None}, None),
            ({"library_id": 1}, None),
        ],
    )
    def test_process_with_valid_payload(
        self,
        completion_worker: CompletionWorker,
        payload: dict[str, Any],
        expected_task_id: int | None,
    ) -> None:
        """Test process() with valid payload (covers lines 63-86).

        Parameters
        ----------
        completion_worker : CompletionWorker
            Worker instance.
        payload : dict[str, Any]
            Payload to process.
        expected_task_id : int | None
            Expected task ID.
        """
        with patch(
            "fundamental.services.library_scanning.workers.completion.ScanTaskTracker"
        ) as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            result = completion_worker.process(payload)

            assert result is None
            if expected_task_id:
                mock_tracker.complete_task.assert_called_once_with(
                    expected_task_id, {"library_id": payload["library_id"]}
                )
            else:
                mock_tracker.complete_task.assert_not_called()

    def test_process_without_library_id(
        self, completion_worker: CompletionWorker
    ) -> None:
        """Test process() without library_id returns None.

        Parameters
        ----------
        completion_worker : CompletionWorker
            Worker instance.
        """
        payload = {"task_id": 123}
        result = completion_worker.process(payload)
        assert result is None

    def test_process_with_empty_payload(
        self, completion_worker: CompletionWorker
    ) -> None:
        """Test process() with empty payload returns None.

        Parameters
        ----------
        completion_worker : CompletionWorker
            Worker instance.
        """
        payload = {}
        result = completion_worker.process(payload)
        assert result is None

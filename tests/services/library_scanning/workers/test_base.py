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

"""Tests for BaseWorker to achieve 100% coverage."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from bookcard.services.library_scanning.workers.base import BaseWorker
from bookcard.services.messaging.base import Message, MessageBroker


class ConcreteWorker(BaseWorker):
    """Concrete implementation of BaseWorker for testing."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str | None = None,
        output_topic: str | None = None,
        process_return: dict[str, Any] | None = None,
        process_exception: Exception | None = None,
    ) -> None:
        """Initialize concrete worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker.
        input_topic : str | None
            Input topic.
        output_topic : str | None
            Output topic.
        process_return : dict[str, Any] | None
            Value to return from process().
        process_exception : Exception | None
            Exception to raise from process().
        """
        super().__init__(broker, input_topic, output_topic)
        self._process_return = process_return
        self._process_exception = process_exception

    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process payload.

        Parameters
        ----------
        payload : dict[str, Any]
            Payload to process.

        Returns
        -------
        dict[str, Any] | None
            Process result.
        """
        if self._process_exception:
            raise self._process_exception
        return self._process_return


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
def mock_message() -> MagicMock:
    """Create a mock message.

    Returns
    -------
    MagicMock
        Mock message.
    """
    message = MagicMock(spec=Message)
    message.payload = {"test": "data"}
    return message


class TestBaseWorkerInit:
    """Test BaseWorker initialization."""

    def test_init_stores_broker_and_topics(self, mock_broker: MagicMock) -> None:
        """Test __init__ stores broker and topics.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        worker = ConcreteWorker(mock_broker, input_topic="input", output_topic="output")
        assert worker.broker == mock_broker
        assert worker.input_topic == "input"
        assert worker.output_topic == "output"

    @pytest.mark.parametrize(
        ("input_topic", "output_topic"),
        [
            (None, None),
            ("input", None),
            (None, "output"),
            ("input", "output"),
        ],
    )
    def test_init_with_various_topics(
        self,
        mock_broker: MagicMock,
        input_topic: str | None,
        output_topic: str | None,
    ) -> None:
        """Test __init__ with various topic combinations.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        input_topic : str | None
            Input topic.
        output_topic : str | None
            Output topic.
        """
        worker = ConcreteWorker(mock_broker, input_topic, output_topic)
        assert worker.input_topic == input_topic
        assert worker.output_topic == output_topic


class TestBaseWorkerStart:
    """Test BaseWorker.start method."""

    def test_start_with_input_topic_subscribes(self, mock_broker: MagicMock) -> None:
        """Test start() subscribes when input_topic is set.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        worker = ConcreteWorker(mock_broker, input_topic="input")
        worker.start()
        mock_broker.subscribe.assert_called_once_with("input", worker._handle_message)

    def test_start_without_input_topic_logs(self, mock_broker: MagicMock) -> None:
        """Test start() logs when no input_topic (covers line 74).

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        worker = ConcreteWorker(mock_broker, input_topic=None)
        worker.start()
        mock_broker.subscribe.assert_not_called()


class TestBaseWorkerHandleMessage:
    """Test BaseWorker._handle_message method."""

    def test_handle_message_success_with_output(
        self, mock_broker: MagicMock, mock_message: MagicMock
    ) -> None:
        """Test _handle_message publishes result when output_topic set.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        mock_message : MagicMock
            Mock message.
        """
        result = {"result": "data"}
        worker = ConcreteWorker(
            mock_broker,
            output_topic="output",
            process_return=result,
        )
        worker._handle_message(mock_message)
        mock_broker.publish.assert_called_once_with("output", result)

    def test_handle_message_success_without_output(
        self, mock_broker: MagicMock, mock_message: MagicMock
    ) -> None:
        """Test _handle_message doesn't publish when no output_topic.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        mock_message : MagicMock
            Mock message.
        """
        result = {"result": "data"}
        worker = ConcreteWorker(
            mock_broker,
            output_topic=None,
            process_return=result,
        )
        worker._handle_message(mock_message)
        mock_broker.publish.assert_not_called()

    def test_handle_message_success_with_none_result(
        self, mock_broker: MagicMock, mock_message: MagicMock
    ) -> None:
        """Test _handle_message doesn't publish when result is None.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        mock_message : MagicMock
            Mock message.
        """
        worker = ConcreteWorker(
            mock_broker,
            output_topic="output",
            process_return=None,
        )
        worker._handle_message(mock_message)
        mock_broker.publish.assert_not_called()

    def test_handle_message_exception_raises(
        self, mock_broker: MagicMock, mock_message: MagicMock
    ) -> None:
        """Test _handle_message raises exception on error (covers lines 86-92).

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        mock_message : MagicMock
            Mock message.
        """
        exception = ValueError("Test error")
        worker = ConcreteWorker(
            mock_broker,
            process_exception=exception,
        )
        with pytest.raises(ValueError, match="Test error"):
            worker._handle_message(mock_message)

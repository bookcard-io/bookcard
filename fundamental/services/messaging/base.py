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

"""Abstract base classes for messaging system."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Message(ABC):
    """Abstract message envelope."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Get message ID."""

    @property
    @abstractmethod
    def payload(self) -> dict[str, Any]:
        """Get message payload."""

    @abstractmethod
    def ack(self) -> None:
        """Acknowledge message processing."""

    @abstractmethod
    def nack(self) -> None:
        """Negative acknowledge (failure)."""


class MessagePublisher(ABC):
    """Abstract message publisher."""

    @abstractmethod
    def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publish a message to a topic.

        Parameters
        ----------
        topic : str
            Topic/queue name.
        message : dict[str, Any]
            Message payload.
        """


class MessageSubscriber(ABC):
    """Abstract message subscriber."""

    @abstractmethod
    def subscribe(
        self,
        topic: str,
        handler: Callable[[Message], None],
    ) -> None:
        """Subscribe to a topic.

        Parameters
        ----------
        topic : str
            Topic/queue name.
        handler : Callable[[Message], None]
            Callback function to handle messages.
        """

    @abstractmethod
    def start(self) -> None:
        """Start consuming messages (blocking or non-blocking depending on impl)."""

    @abstractmethod
    def stop(self) -> None:
        """Stop consuming messages."""


class MessageBroker(MessagePublisher, MessageSubscriber, ABC):
    """Abstract message broker combining publisher and subscriber capabilities."""

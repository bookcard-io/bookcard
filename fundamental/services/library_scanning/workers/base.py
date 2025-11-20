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

"""Base worker implementation for distributed scan workers.

This is the base class for scan workers in the library scanning pipeline.
These workers are distinct from task runners (see fundamental/services/tasks/).

Scan Workers:
    - Process messages from Redis pub/sub topics
    - Implement pipeline stages (crawl, match, ingest, link, etc.)
    - Subscribe to input topics and publish to output topics
    - Managed by ScanWorkerManager

Task Runners:
    - Execute BaseTask instances
    - Use task factory/registry pattern
    - Support thread/Celery/Dramatiq backends
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from fundamental.services.messaging.base import Message, MessageBroker

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Abstract base worker that processes messages from a queue."""

    def __init__(
        self,
        broker: MessageBroker,
        input_topic: str | None = None,
        output_topic: str | None = None,
    ) -> None:
        """Initialize worker.

        Parameters
        ----------
        broker : MessageBroker
            Message broker for Pub/Sub.
        input_topic : str | None
            Topic to subscribe to. If None, worker is a producer-only or manual trigger.
        output_topic : str | None
            Topic to publish results to. If None, worker is a sink.
        """
        self.broker = broker
        self.input_topic = input_topic
        self.output_topic = output_topic

    def start(self) -> None:
        """Start the worker."""
        if self.input_topic:
            logger.info(
                "Worker %s subscribing to %s", self.__class__.__name__, self.input_topic
            )
            self.broker.subscribe(self.input_topic, self._handle_message)
        else:
            logger.info(
                "Worker %s has no input topic (producer only)", self.__class__.__name__
            )

    def _handle_message(self, message: Message) -> None:
        """Handle incoming message from broker.

        Parameters
        ----------
        message : Message
            Message to process.
        """
        try:
            result = self.process(message.payload)
            if result and self.output_topic:
                self.broker.publish(self.output_topic, result)
        except Exception:
            logger.exception("Error processing message in %s", self.__class__.__name__)
            raise  # Will trigger NACK in broker if supported

    @abstractmethod
    def process(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Process a message payload.

        Parameters
        ----------
        payload : dict[str, Any]
            Input message payload.

        Returns
        -------
        dict[str, Any] | None
            Result payload to publish to output topic, or None to skip publishing.
        """

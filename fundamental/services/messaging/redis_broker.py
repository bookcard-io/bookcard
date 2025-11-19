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

"""Redis implementation of messaging system."""

import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

import redis

from fundamental.services.messaging.base import Message, MessageBroker

logger = logging.getLogger(__name__)


class RedisMessage(Message):
    """Redis message implementation."""

    def __init__(
        self,
        msg_id: str,
        payload: dict[str, Any],
        raw_message: bytes | str,
        broker: "RedisBroker",
    ) -> None:
        """Initialize Redis message.

        Parameters
        ----------
        msg_id : str
            Message ID.
        payload : dict[str, Any]
            Deserialized payload.
        raw_message : bytes | str
            Raw Redis message object (if applicable for ack).
        broker : RedisBroker
            Reference to broker for operations.
        """
        self._id = msg_id
        self._payload = payload
        self._raw_message = raw_message
        self._broker = broker

    @property
    def id(self) -> str:
        """Get message ID."""
        return self._id

    @property
    def payload(self) -> dict[str, Any]:
        """Get message payload."""
        return self._payload

    def ack(self) -> None:
        """Acknowledge message processing.

        For simple Pub/Sub, ACK is a no-op.
        For Streams or Lists, implementation would differ.
        Here we assume List-based queueing for persistence/work distribution.
        """
        # In a simple RPOP list implementation, the message is removed on read.
        # A more robust implementation would use RPOPLPUSH to a processing queue and then LREM.

    def nack(self) -> None:
        """Negative acknowledge (failure)."""
        # Ideally, push back to queue or DLQ.


class RedisBroker(MessageBroker):
    """Redis-based message broker using Lists for queues."""

    def __init__(
        self,
        redis_url: str,
        poll_interval: float = 0.1,
        prefix: str = "fundamental:queue:",
    ) -> None:
        """Initialize Redis broker.

        Parameters
        ----------
        redis_url : str
            Redis connection URL.
        poll_interval : float
            Time to sleep between polls when queue is empty.
        prefix : str
            Prefix for Redis keys.
        """
        self.client = redis.from_url(redis_url)
        self.poll_interval = poll_interval
        self.prefix = prefix
        self._running = False
        self._threads: list[threading.Thread] = []
        self._stop_events: list[threading.Event] = []

    def _get_queue_name(self, topic: str) -> str:
        return f"{self.prefix}{topic}"

    def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publish a message to a queue (LPUSH)."""
        queue_name = self._get_queue_name(topic)
        # Add a message ID if not present
        if "message_id" not in message:
            message["message_id"] = str(uuid.uuid4())

        payload_str = json.dumps(message)
        self.client.lpush(queue_name, payload_str)
        logger.debug("Published message to %s: %s", topic, message.get("message_id"))

    def subscribe(
        self,
        topic: str,
        handler: Callable[[Message], None],
    ) -> None:
        """Subscribe to a queue (worker loop).

        Starts a daemon thread that polls the queue.
        """
        queue_name = self._get_queue_name(topic)
        stop_event = threading.Event()
        self._stop_events.append(stop_event)

        def worker() -> None:
            logger.info("Started worker for queue: %s", queue_name)
            while not stop_event.is_set():
                try:
                    # BRPOP blocks until a message is available or timeout
                    # timeout=1 allows checking stop_event periodically
                    result = self.client.brpop(queue_name, timeout=1)
                    if result:
                        _, data = result
                        payload = json.loads(data)
                        msg = RedisMessage(
                            msg_id=payload.get("message_id", "unknown"),
                            payload=payload,
                            raw_message=data,
                            broker=self,
                        )
                        try:
                            handler(msg)
                            msg.ack()
                        except Exception:
                            logger.exception("Error handling message in %s", topic)
                            msg.nack()
                except redis.ConnectionError:
                    logger.exception("Redis connection error, retrying...")
                    time.sleep(5)
                except Exception:
                    logger.exception("Unexpected error in worker %s", topic)
                    time.sleep(1)

        t = threading.Thread(target=worker, daemon=True, name=f"worker-{topic}")
        self._threads.append(t)
        # Note: We don't start here, we wait for explicit start() call or auto-start
        # Depending on usage. For now, let's auto-start if broker is running.
        if self._running:
            t.start()

    def start(self) -> None:
        """Start all registered consumers."""
        self._running = True
        for t in self._threads:
            if not t.is_alive():
                t.start()

    def stop(self) -> None:
        """Stop all consumers."""
        self._running = False
        for event in self._stop_events:
            event.set()
        for t in self._threads:
            t.join(timeout=2.0)

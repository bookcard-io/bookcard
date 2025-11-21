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

"""Worker manager for starting and managing distributed scan workers."""

import logging
import os

from fundamental.services.library_scanning.workers.completion import CompletionWorker
from fundamental.services.library_scanning.workers.crawl import CrawlWorker
from fundamental.services.library_scanning.workers.deduplicate import DeduplicateWorker
from fundamental.services.library_scanning.workers.ingest import IngestWorker
from fundamental.services.library_scanning.workers.link import LinkWorker
from fundamental.services.library_scanning.workers.match import MatchWorker
from fundamental.services.library_scanning.workers.score import ScoreWorker
from fundamental.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class ScanWorkerManager:
    """Manages lifecycle of distributed scan workers."""

    def __init__(self, redis_url: str, threads_per_worker: int = 1) -> None:
        """Initialize worker manager.

        Parameters
        ----------
        redis_url : str
            Redis connection URL.
        threads_per_worker : int
            Number of threads to start per worker type.
        """
        self.broker = RedisBroker(redis_url)
        self.threads_per_worker = threads_per_worker
        self.workers: list[
            CrawlWorker
            | MatchWorker
            | IngestWorker
            | LinkWorker
            | DeduplicateWorker
            | ScoreWorker
            | CompletionWorker
        ] = []
        self._started = False

    def start_workers(self) -> None:
        """Start all scan workers."""
        if self._started:
            logger.warning("Workers already started")
            return

        logger.info(
            "Starting distributed scan workers (%d threads per worker)...",
            self.threads_per_worker,
        )

        # Create workers (multiple instances for parallelism)
        # MatchWorker uses HTTP data source for better performance
        # IngestWorker uses PostgreSQL dump for fast data retrieval
        self.workers = []
        for _ in range(self.threads_per_worker):
            self.workers.extend([
                CrawlWorker(self.broker),
                MatchWorker(self.broker, data_source_name="openlibrary"),
                IngestWorker(self.broker, data_source_name="openlibrary_dump"),
                LinkWorker(self.broker),
                DeduplicateWorker(self.broker),
                ScoreWorker(self.broker),
                CompletionWorker(self.broker),
            ])

        # Start workers
        for worker in self.workers:
            worker.start()

        # Start broker (starts all worker threads)
        self.broker.start()

        self._started = True
        logger.info("All scan workers started and listening for jobs")

    def stop_workers(self) -> None:
        """Stop all workers gracefully."""
        if not self._started:
            return

        logger.info("Stopping scan workers...")
        self.broker.stop()
        self._started = False
        logger.info("All scan workers stopped")

    @staticmethod
    def get_redis_url() -> str:
        """Get Redis URL from environment.

        Returns
        -------
        str
            Redis connection URL.

        Raises
        ------
        ValueError
            If Redis URL cannot be determined.
        """
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")

        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        return f"redis://{redis_host}:{redis_port}/0"

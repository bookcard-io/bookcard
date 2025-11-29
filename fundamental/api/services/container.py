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

"""IoC container for application services.

Provides factory methods for creating and managing application services,
following the Inversion of Control principle to reduce coupling.
"""

import logging
from typing import TYPE_CHECKING

from fundamental.config import AppConfig
from fundamental.database import get_session
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_watcher_service import IngestWatcherService
from fundamental.services.library_scanning.workers.manager import ScanWorkerManager
from fundamental.services.messaging.redis_broker import RedisBroker
from fundamental.services.scheduler import TaskScheduler
from fundamental.services.tasks.runner_factory import create_task_runner

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)

# Common infrastructure exceptions that services may raise
INFRASTRUCTURE_EXCEPTIONS = (
    ConnectionError,
    ValueError,
    RuntimeError,
    ImportError,
    OSError,
)


class ServiceContainer:
    """IoC container for application services.

    Provides factory methods for creating services with proper error handling
    and logging. Services are created lazily and can return None if dependencies
    are not available.

    Parameters
    ----------
    config : AppConfig
        Application configuration.
    engine : Engine
        Database engine.
    """

    def __init__(self, config: AppConfig, engine: "Engine") -> None:
        """Initialize service container.

        Parameters
        ----------
        config : AppConfig
            Application configuration.
        engine : Engine
            Database engine.
        """
        self.config = config
        self.engine = engine

    def create_task_runner(self) -> "TaskRunner | None":
        """Create task runner instance.

        Returns
        -------
        TaskRunner | None
            Task runner instance, or None if creation fails.
        """
        try:
            return create_task_runner(self.engine, self.config)
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(
                "Failed to initialize task runner: %s. Tasks will not be available.",
                exc,
            )
            return None

    def create_redis_broker(self) -> RedisBroker | None:
        """Create Redis broker instance.

        Returns
        -------
        RedisBroker | None
            Redis broker instance, or None if Redis is disabled or creation fails.
        """
        if not self.config.redis_enabled:
            logger.info("Redis features not enabled.")
            return None

        try:
            broker = RedisBroker(self.config.redis_url)
            logger.info("Initialized Redis broker for library scanning")
        except INFRASTRUCTURE_EXCEPTIONS as exc:
            logger.warning(
                "Failed to initialize Redis broker for scanning: %s. Library scanning will not be available.",
                exc,
            )
            return None
        else:
            return broker

    def create_scan_worker_manager(self) -> ScanWorkerManager | None:
        """Create scan worker manager instance.

        Returns
        -------
        ScanWorkerManager | None
            Scan worker manager instance, or None if Redis is disabled or creation fails.
        """
        if not self.config.redis_enabled:
            return None

        try:
            return ScanWorkerManager(self.config.redis_url)
        except INFRASTRUCTURE_EXCEPTIONS as exc:
            logger.warning(
                "Failed to initialize scan worker manager: %s. Library scanning will not be available.",
                exc,
            )
            return None

    def create_scheduler(
        self, task_runner: "TaskRunner | None"
    ) -> TaskScheduler | None:
        """Create task scheduler instance.

        Parameters
        ----------
        task_runner : TaskRunner | None
            Task runner instance (required for scheduler).

        Returns
        -------
        TaskScheduler | None
            Task scheduler instance, or None if dependencies are not available.
        """
        if not self.config.redis_enabled:
            logger.info("Scheduler not initialized: Redis is disabled")
            return None

        if task_runner is None:
            logger.info("Scheduler not initialized: Task runner is not available")
            return None

        try:
            scheduler = TaskScheduler(self.engine, task_runner)
            logger.info("Initialized TaskScheduler for periodic tasks")
        except INFRASTRUCTURE_EXCEPTIONS as exc:
            logger.warning(
                "Failed to initialize scheduler: %s.",
                exc,
            )
            return None
        else:
            return scheduler

    def create_ingest_watcher(
        self, task_runner: "TaskRunner | None"
    ) -> IngestWatcherService | None:
        """Create ingest watcher service instance.

        Parameters
        ----------
        task_runner : TaskRunner | None
            Task runner instance (required for watcher).

        Returns
        -------
        IngestWatcherService | None
            Ingest watcher service instance, or None if dependencies are not available
            or ingest is disabled.
        """
        if not self.config.redis_enabled or task_runner is None:
            logger.info(
                "Ingest watcher not initialized: Redis or task runner not available"
            )
            return None

        try:
            # Check if ingest is enabled before creating watcher
            with get_session(self.engine) as session:
                config_service = IngestConfigService(session)
                config = config_service.get_config()

                if not config.enabled:
                    logger.info("Ingest service is disabled")
                    return None

            # Create watcher service with engine (creates sessions on demand)
            watcher = IngestWatcherService(
                engine=self.engine,
                task_runner=task_runner,
            )
            logger.info("Initialized ingest watcher service")
        except INFRASTRUCTURE_EXCEPTIONS as exc:
            logger.warning(
                "Failed to initialize ingest watcher: %s. Automatic ingest will not be available.",
                exc,
            )
            return None
        else:
            return watcher

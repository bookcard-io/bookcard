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

"""Service bootstrap and lifecycle management.

Handles initialization, startup, and shutdown of application services.
"""

import logging
from typing import Protocol

from fastapi import FastAPI

from fundamental.api.services.container import (
    INFRASTRUCTURE_EXCEPTIONS,
    ServiceContainer,
)

logger = logging.getLogger(__name__)


class BackgroundService(Protocol):
    """Protocol for services that can be started and stopped."""

    def start(self) -> None:
        """Start the service."""
        ...

    def stop(self) -> None:
        """Stop the service."""
        ...


class ScanWorkerService(Protocol):
    """Protocol for scan worker services."""

    def start_workers(self) -> None:
        """Start scan workers."""
        ...

    def stop_workers(self) -> None:
        """Stop scan workers."""
        ...


class IngestWatcherServiceProtocol(Protocol):
    """Protocol for ingest watcher services."""

    def start_watching(self) -> None:
        """Start watching for ingest files."""
        ...

    def stop_watching(self) -> None:
        """Stop watching for ingest files."""
        ...


class TaskRunnerProtocol(Protocol):
    """Protocol for task runners with shutdown capability."""

    def shutdown(self) -> None:
        """Shutdown the task runner."""
        ...


def initialize_services(app: FastAPI, container: ServiceContainer) -> None:
    """Initialize all application services.

    Should be called after migrations have run.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    container : ServiceContainer
        Service container for creating services.
    """
    # Initialize task runner
    app.state.task_runner = container.create_task_runner()

    # Initialize scan worker manager and broker
    app.state.scan_worker_broker = container.create_redis_broker()
    app.state.scan_worker_manager = container.create_scan_worker_manager()

    # Initialize scheduler (depends on task runner, so initialize after)
    app.state.scheduler = container.create_scheduler(app.state.task_runner)

    # Initialize ingest watcher (depends on task runner, so initialize after)
    app.state.ingest_watcher = container.create_ingest_watcher(app.state.task_runner)


def _get_background_services(app: FastAPI) -> list[tuple[str, object]]:
    """Get list of background services that need to be started/stopped.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.

    Returns
    -------
    list[tuple[str, object]]
        List of (name, service) tuples.
    """
    services: list[tuple[str, object]] = []

    if hasattr(app.state, "scan_worker_manager") and app.state.scan_worker_manager:
        services.append(("scan workers", app.state.scan_worker_manager))

    if hasattr(app.state, "scheduler") and app.state.scheduler:
        services.append(("scheduler", app.state.scheduler))

    if hasattr(app.state, "ingest_watcher") and app.state.ingest_watcher:
        services.append(("ingest watcher", app.state.ingest_watcher))

    return services


def start_background_services(app: FastAPI) -> None:
    """Start background services (scan workers, scheduler, ingest watcher).

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    services = _get_background_services(app)

    for name, service in services:
        try:
            if hasattr(service, "start_workers"):
                # Scan worker manager
                service.start_workers()  # type: ignore[attr-defined]
            elif hasattr(service, "start_watching"):
                # Ingest watcher
                service.start_watching()  # type: ignore[attr-defined]
            elif hasattr(service, "start"):
                # Scheduler or other services with start()
                service.start()  # type: ignore[attr-defined]
        except INFRASTRUCTURE_EXCEPTIONS as e:
            logger.warning(
                "Failed to start %s: %s. Service will not be available.",
                name,
                e,
            )


def stop_background_services(app: FastAPI) -> None:
    """Stop background services gracefully.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    services = _get_background_services(app)

    # Stop in reverse order
    for name, service in reversed(services):
        try:
            if hasattr(service, "stop_workers"):
                # Scan worker manager
                service.stop_workers()  # type: ignore[attr-defined]
            elif hasattr(service, "stop_watching"):
                # Ingest watcher
                service.stop_watching()  # type: ignore[attr-defined]
            elif hasattr(service, "shutdown"):
                # Scheduler or other services with shutdown()
                service.shutdown()  # type: ignore[attr-defined]
        except (RuntimeError, OSError) as e:
            logger.warning("Error stopping %s: %s", name, e)

    # Ensure background task runners are stopped so that reload/shutdown
    # is clean and does not leak worker threads.
    if hasattr(app.state, "task_runner") and app.state.task_runner:
        shutdown = getattr(app.state.task_runner, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()
            except (RuntimeError, OSError) as e:
                logger.warning("Error shutting down task runner: %s", e)

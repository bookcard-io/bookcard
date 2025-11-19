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

"""FastAPI application factory.

Creates and configures the FastAPI app, registers routers, and initializes
application state. Designed for IOC and testability.
"""

import asyncio
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine

from dotenv import load_dotenv
from fastapi import FastAPI

from fundamental.api.middleware.auth_middleware import AuthMiddleware
from fundamental.api.routes.admin import router as admin_router
from fundamental.api.routes.auth import router as auth_router
from fundamental.api.routes.authors import router as authors_router
from fundamental.api.routes.books import router as books_router
from fundamental.api.routes.devices import router as devices_router
from fundamental.api.routes.fs import router as fs_router
from fundamental.api.routes.library_scanning import router as library_scanning_router
from fundamental.api.routes.metadata import router as metadata_router
from fundamental.api.routes.shelves import router as shelves_router
from fundamental.api.routes.tasks import router as tasks_router
from fundamental.config import AppConfig
from fundamental.database import create_db_engine
from fundamental.services.library_scanning.workers.manager import ScanWorkerManager
from fundamental.services.messaging.redis_broker import RedisBroker
from fundamental.services.tasks.runner_factory import create_task_runner

logger = logging.getLogger(__name__)

try:
    # Imported lazily in function to avoid hard dependency at import time in tests
    from alembic import command as _alembic_command  # type: ignore
    from alembic.config import Config as _AlembicConfig  # type: ignore
except ImportError:  # pragma: no cover - only for environments without Alembic
    _alembic_command = None  # type: ignore[assignment]
    _AlembicConfig = None  # type: ignore[assignment]


# Load environment variables from .env file
load_dotenv()


def _setup_logging() -> None:
    """Configure application-wide logging to output to stdout.

    Sets up a console handler that outputs all log messages to stdout with
    a formatted output including timestamp, level, logger name, and message.
    This configuration ensures that all logging calls throughout the application
    will be visible in standard output when running with `make dev`.
    """
    # Get log level from environment, default to INFO for development
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure logging using basicConfig, which sets up root logger
    # force=True ensures it reconfigures even if logging was already configured
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,  # Override any existing configuration
    )

    # Configure application-specific logger
    app_logger = logging.getLogger("fundamental")
    app_logger.setLevel(numeric_level)
    app_logger.propagate = True


def _register_routers(app: FastAPI) -> None:
    """Register all API routers with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(authors_router)
    app.include_router(books_router)
    app.include_router(devices_router)
    app.include_router(fs_router)
    app.include_router(library_scanning_router)
    app.include_router(metadata_router)
    app.include_router(shelves_router)
    app.include_router(tasks_router)


def _initialize_task_runner(app: FastAPI, engine: "Engine", cfg: AppConfig) -> None:
    """Initialize task runner for the application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    engine : Any
        Database engine.
    cfg : AppConfig
        Application configuration.
    """
    try:
        app.state.task_runner = create_task_runner(engine, cfg)
    except (ValueError, RuntimeError, OSError) as exc:
        logger.warning(
            "Failed to initialize task runner: %s. Tasks will not be available.",
            exc,
        )
        app.state.task_runner = None


def _initialize_scan_workers(app: FastAPI, cfg: AppConfig) -> None:
    """Initialize scan worker manager and broker.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    cfg : AppConfig
        Application configuration.
    """
    if not cfg.redis_enabled:
        logger.info("Redis features not enabled.")
        app.state.scan_worker_broker = None
        app.state.scan_worker_manager = None
        return

    try:
        broker = RedisBroker(cfg.redis_url)
        app.state.scan_worker_broker = broker
        app.state.scan_worker_manager = ScanWorkerManager(cfg.redis_url)
        logger.info("Initialized Redis broker for library scanning")
    except (ConnectionError, ValueError, RuntimeError, ImportError) as exc:
        logger.warning(
            "Failed to initialize Redis broker for scanning: %s. Library scanning will not be available.",
            exc,
        )
        app.state.scan_worker_broker = None
        app.state.scan_worker_manager = None


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    config : AppConfig | None
        Optional configuration to initialize the app with; if ``None``,
        environment variables are used.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.
    """
    # Configure logging first, before any other operations
    _setup_logging()

    cfg = config or AppConfig.from_env()

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan manager.

        Runs database migrations at startup when enabled and ensures that
        background services (such as the task runner) are shut down gracefully
        during application shutdown or reload.
        """
        try:
            if (
                cfg.alembic_enabled
                and _AlembicConfig is not None
                and _alembic_command is not None
            ):
                alembic_cfg = _AlembicConfig()
                alembic_cfg.set_main_option(
                    "script_location", "fundamental/db/migrations"
                )
                await asyncio.to_thread(_alembic_command.upgrade, alembic_cfg, "head")

            # Access app.state early to ensure it is created by Starlette.
            _ = getattr(app, "state", None)

            # Start scan workers if Redis is configured
            scan_worker_manager = getattr(app.state, "scan_worker_manager", None)
            if scan_worker_manager:
                try:
                    scan_worker_manager.start_workers()
                except (ConnectionError, ValueError, RuntimeError) as e:
                    logger.warning(
                        "Failed to start scan workers: %s. Library scanning will not be available.",
                        e,
                    )

            # Yield control to allow the application to serve requests.
            yield

        except asyncio.CancelledError:
            # Uvicorn's reload and shutdown mechanisms may cancel the lifespan
            # task (common on Windows with the file-watcher/reloader).
            # Treat this as a graceful shutdown so background workers can stop
            # cleanly without surfacing noisy tracebacks.
            logger.info("Application lifespan cancelled; shutting down gracefully.")
        finally:
            # Stop scan workers gracefully
            scan_worker_manager = getattr(app.state, "scan_worker_manager", None)
            if scan_worker_manager:
                try:
                    scan_worker_manager.stop_workers()
                except (RuntimeError, OSError) as e:
                    logger.warning("Error stopping scan workers: %s", e)

            # Ensure background task runners are stopped so that reload/shutdown
            # is clean and does not leak worker threads.
            task_runner = getattr(app.state, "task_runner", None)
            shutdown = getattr(task_runner, "shutdown", None) if task_runner else None
            if callable(shutdown):
                shutdown()

    app = FastAPI(
        title="Fundamental",
        version="0.1.0",
        summary="Self-hosted ebook management and reading API",
        lifespan=_lifespan,
    )

    # Application state
    engine = create_db_engine(cfg)
    app.state.engine = engine
    app.state.config = cfg

    # Initialize task runner
    _initialize_task_runner(app, engine, cfg)

    # Initialize scan worker manager and broker
    _initialize_scan_workers(app, cfg)

    # Register routers
    _register_routers(app)

    # Middleware (best-effort attachment of user claims)
    app.add_middleware(AuthMiddleware)

    return app


# Default application instance for ASGI servers
app = create_app()

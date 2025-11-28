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
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.requests import Request

from fundamental.api.middleware.auth_middleware import AuthMiddleware
from fundamental.api.routes.admin import router as admin_router
from fundamental.api.routes.auth import router as auth_router
from fundamental.api.routes.authors import router as authors_router
from fundamental.api.routes.books import router as books_router
from fundamental.api.routes.devices import router as devices_router
from fundamental.api.routes.epub_fixer import router as epub_fixer_router
from fundamental.api.routes.fs import router as fs_router
from fundamental.api.routes.ingest import router as ingest_router
from fundamental.api.routes.library_scanning import router as library_scanning_router
from fundamental.api.routes.metadata import router as metadata_router
from fundamental.api.routes.reading import router as reading_router
from fundamental.api.routes.shelves import router as shelves_router
from fundamental.api.routes.tasks import router as tasks_router
from fundamental.config import AppConfig
from fundamental.database import create_db_engine, get_session
from fundamental.services.author_exceptions import NoActiveLibraryError
from fundamental.services.ingest.exceptions import (
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_watcher_service import IngestWatcherService
from fundamental.services.library_scanning.workers.manager import ScanWorkerManager
from fundamental.services.messaging.redis_broker import RedisBroker
from fundamental.services.scheduler import TaskScheduler
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
    app.include_router(epub_fixer_router)
    app.include_router(fs_router)
    app.include_router(ingest_router)
    app.include_router(library_scanning_router)
    app.include_router(metadata_router)
    app.include_router(reading_router)
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


def _initialize_scheduler(
    app: FastAPI,
    engine: "Engine",
    cfg: AppConfig,  # type: ignore[name-defined]
) -> None:
    """Initialize task scheduler for periodic tasks.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    engine : Engine
        Database engine.
    cfg : AppConfig
        Application configuration.
    """
    # Only initialize if Redis is enabled and task runner is available
    if not cfg.redis_enabled:
        logger.info("Scheduler not initialized: Redis is disabled")
        app.state.scheduler = None
        return

    if app.state.task_runner is None:
        logger.info("Scheduler not initialized: Task runner is not available")
        app.state.scheduler = None
        return

    try:
        app.state.scheduler = TaskScheduler(engine, app.state.task_runner)
        logger.info("Initialized TaskScheduler for periodic tasks")
    except (ConnectionError, ValueError, RuntimeError, ImportError) as exc:
        logger.warning(
            "Failed to initialize scheduler: %s.",
            exc,
        )
        app.state.scheduler = None


async def _run_migrations(cfg: AppConfig) -> None:
    """Run database migrations if enabled.

    Parameters
    ----------
    cfg : AppConfig
        Application configuration.
    """
    if (
        cfg.alembic_enabled
        and _AlembicConfig is not None
        and _alembic_command is not None
    ):
        alembic_cfg = _AlembicConfig()
        alembic_cfg.set_main_option("script_location", "fundamental/db/migrations")
        await asyncio.to_thread(_alembic_command.upgrade, alembic_cfg, "head")


def _start_background_services(app: FastAPI) -> None:
    """Start background services (scan workers, scheduler, ingest watcher).

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    # Start scan workers if Redis is configured
    if app.state.scan_worker_manager:
        try:
            app.state.scan_worker_manager.start_workers()
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.warning(
                "Failed to start scan workers: %s. Library scanning will not be available.",
                e,
            )

    # Start scheduler if configured
    if app.state.scheduler:
        try:
            app.state.scheduler.start()
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.warning(
                "Failed to start scheduler: %s. Scheduled tasks will not be available.",
                e,
            )

    # Start ingest watcher if configured
    if app.state.ingest_watcher:
        try:
            app.state.ingest_watcher.start_watching()
        except (ConnectionError, ValueError, RuntimeError, OSError) as e:
            logger.warning(
                "Failed to start ingest watcher: %s. Automatic ingest will not be available.",
                e,
            )


def _stop_background_services(app: FastAPI) -> None:
    """Stop background services gracefully.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    # Stop ingest watcher gracefully
    if app.state.ingest_watcher:
        try:
            app.state.ingest_watcher.stop_watching()
        except (RuntimeError, OSError) as e:
            logger.warning("Error stopping ingest watcher: %s", e)

    # Stop scheduler gracefully
    if app.state.scheduler:
        try:
            app.state.scheduler.shutdown()
        except (RuntimeError, OSError) as e:
            logger.warning("Error stopping scheduler: %s", e)

    # Stop scan workers gracefully
    if app.state.scan_worker_manager:
        try:
            app.state.scan_worker_manager.stop_workers()
        except (RuntimeError, OSError) as e:
            logger.warning("Error stopping scan workers: %s", e)

    # Ensure background task runners are stopped so that reload/shutdown
    # is clean and does not leak worker threads.
    if app.state.task_runner:
        shutdown = getattr(app.state.task_runner, "shutdown", None)
        if callable(shutdown):
            shutdown()


def _initialize_ingest_watcher(app: FastAPI, engine: "Engine", cfg: AppConfig) -> None:  # type: ignore[name-defined]
    """Initialize ingest watcher service.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    engine : Engine
        Database engine.
    cfg : AppConfig
        Application configuration.
    """
    if not cfg.redis_enabled or app.state.task_runner is None:
        logger.info(
            "Ingest watcher not initialized: Redis or task runner not available"
        )
        app.state.ingest_watcher = None
        return

    try:
        # Check if ingest is enabled before creating watcher
        with get_session(engine) as session:
            config_service = IngestConfigService(session)
            config = config_service.get_config()

            if not config.enabled:
                logger.info("Ingest service is disabled")
                app.state.ingest_watcher = None
                return

        # Create watcher service with engine (creates sessions on demand)
        watcher = IngestWatcherService(
            engine=engine,
            task_runner=app.state.task_runner,
        )
        app.state.ingest_watcher = watcher
        logger.info("Initialized ingest watcher service")
    except (ConnectionError, ValueError, RuntimeError, ImportError) as exc:
        logger.warning(
            "Failed to initialize ingest watcher: %s. Automatic ingest will not be available.",
            exc,
        )
        app.state.ingest_watcher = None


def _setup_app_state(app: FastAPI, engine: "Engine", cfg: AppConfig) -> None:  # type: ignore[name-defined]
    """Set up application state and initialize services.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    engine : Engine
        Database engine.
    cfg : AppConfig
        Application configuration.
    """
    # Application state
    app.state.engine = engine
    app.state.config = cfg


def _initialize_services(app: FastAPI) -> None:
    """Initialize all application services.

    Should be called after migrations have run.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    engine = app.state.engine
    cfg = app.state.config

    # Initialize task runner
    _initialize_task_runner(app, engine, cfg)

    # Initialize scan worker manager and broker
    _initialize_scan_workers(app, cfg)

    # Initialize scheduler (depends on task runner, so initialize after)
    _initialize_scheduler(app, engine, cfg)

    # Initialize ingest watcher (depends on task runner, so initialize after)
    _initialize_ingest_watcher(app, engine, cfg)


def _configure_app(app: FastAPI) -> None:
    """Configure FastAPI application (routers, endpoints, middleware).

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """

    # Register exception handlers for domain-specific exceptions
    @app.exception_handler(IngestHistoryNotFoundError)
    def ingest_history_not_found_handler(
        _request: Request, exc: IngestHistoryNotFoundError
    ) -> JSONResponse:
        """Handle IngestHistoryNotFoundError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(NoActiveLibraryError)
    def no_active_library_handler(
        _request: Request, exc: NoActiveLibraryError
    ) -> JSONResponse:
        """Handle NoActiveLibraryError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IngestHistoryCreationError)
    def ingest_history_creation_error_handler(
        _request: Request, exc: IngestHistoryCreationError
    ) -> JSONResponse:
        """Handle IngestHistoryCreationError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    # Register routers
    _register_routers(app)

    # Add health check endpoint
    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint for Docker and load balancers.

        Returns
        -------
        JSONResponse
            JSON response with status "ok".
        """
        return JSONResponse(content={"status": "ok"})

    # Middleware (best-effort attachment of user claims)
    app.add_middleware(AuthMiddleware)


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
            await _run_migrations(cfg)

            # Access app.state early to ensure it is created by Starlette.
            _ = getattr(app, "state", None)

            # Initialize services that depend on database tables being present
            _initialize_services(app)

            _start_background_services(app)

            # Yield control to allow the application to serve requests.
            yield

        except asyncio.CancelledError:
            # Uvicorn's reload and shutdown mechanisms may cancel the lifespan
            # task (common on Windows with the file-watcher/reloader).
            # Treat this as a graceful shutdown so background workers can stop
            # cleanly without surfacing noisy tracebacks.
            logger.info("Application lifespan cancelled; shutting down gracefully.")
        finally:
            _stop_background_services(app)

    app = FastAPI(
        title="Fundamental",
        version="0.1.0",
        summary="Self-hosted ebook management and reading API",
        lifespan=_lifespan,
    )

    # Set up application state
    engine = create_db_engine(cfg)
    _setup_app_state(app, engine, cfg)

    # Configure application (routers, endpoints, middleware)
    _configure_app(app)

    return app


# Default application instance for ASGI servers
app = create_app()

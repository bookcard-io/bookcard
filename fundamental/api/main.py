# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""FastAPI application factory.

Creates and configures the FastAPI app, registers routers, and initializes
application state. Designed for IOC and testability.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from fundamental.api.middleware.auth_middleware import AuthMiddleware
from fundamental.api.routes.admin import router as admin_router
from fundamental.api.routes.auth import router as auth_router
from fundamental.api.routes.books import router as books_router
from fundamental.api.routes.fs import router as fs_router
from fundamental.config import AppConfig
from fundamental.database import create_db_engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

try:
    # Imported lazily in function to avoid hard dependency at import time in tests
    from alembic import command as _alembic_command  # type: ignore
    from alembic.config import Config as _AlembicConfig  # type: ignore
except ImportError:  # pragma: no cover - only for environments without Alembic
    _alembic_command = None  # type: ignore[assignment]
    _AlembicConfig = None  # type: ignore[assignment]


def _setup_logging() -> None:
    """Configure application-wide logging to output to stdout.

    Sets up a console handler that outputs all log messages to stdout with
    a formatted output including timestamp, level, logger name, and message.
    This configuration ensures that all logging calls throughout the application
    will be visible in standard output when running with `make dev`.
    """
    # Get log level from environment, default to INFO for development
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
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
    app.include_router(books_router)
    app.include_router(fs_router)


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

        Runs database migrations at startup when enabled.
        """
        if (
            cfg.alembic_enabled
            and _AlembicConfig is not None
            and _alembic_command is not None
        ):
            alembic_cfg = _AlembicConfig()
            alembic_cfg.set_main_option("script_location", "fundamental/db/migrations")
            await asyncio.to_thread(_alembic_command.upgrade, alembic_cfg, "head")
        _ = getattr(app, "state", None)
        yield

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

    # Register routers
    _register_routers(app)

    # Middleware (best-effort attachment of user claims)
    app.add_middleware(AuthMiddleware)

    return app


# Default application instance for ASGI servers
app = create_app()

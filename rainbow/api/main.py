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

import logging
import os
import sys

from fastapi import FastAPI

from rainbow.api.middleware.auth_middleware import AuthMiddleware
from rainbow.api.routes.auth import router as auth_router
from rainbow.config import AppConfig
from rainbow.database import create_db_engine


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
    app_logger = logging.getLogger("moose")
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

    app = FastAPI(
        title="Rainbow",
        version="0.1.0",
        summary="Self-hosted ebook management and reading API",
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

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

from dotenv import load_dotenv
from fastapi import FastAPI

from bookcard.api.exceptions import register_exception_handlers
from bookcard.api.health import register_health_endpoints
from bookcard.api.lifespan import create_lifespan
from bookcard.api.logging_config import setup_logging
from bookcard.api.middleware_config import register_middleware
from bookcard.api.routers import register_routers
from bookcard.config import AppConfig
from bookcard.database import create_db_engine

# Load environment variables from .env file
load_dotenv()


def configure_app(app: FastAPI) -> None:
    """Configure FastAPI application (routers, endpoints, middleware).

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    register_exception_handlers(app)
    register_routers(app)
    register_health_endpoints(app)
    register_middleware(app)


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
    setup_logging()

    cfg = config or AppConfig.from_env()

    # Create database engine
    engine = create_db_engine(cfg)

    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Bookcard",
        version="0.1.0",
        summary="Self-hosted ebook management and reading API",
        lifespan=create_lifespan(cfg, engine),
    )

    # Set up application state
    app.state.engine = engine
    app.state.config = cfg

    # Configure application (routers, endpoints, middleware)
    configure_app(app)

    return app


# Default application instance for ASGI servers
# Note: For better testability, consider using lazy initialization
# or factory pattern instead of creating at module level
app = create_app()

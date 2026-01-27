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

"""Application lifespan management.

Handles startup and shutdown lifecycle of the FastAPI application,
including database migrations and service initialization.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from bookcard.api.services.bootstrap import (
    initialize_services,
    start_background_services,
    stop_background_services,
)
from bookcard.api.services.container import ServiceContainer
from bookcard.config import AppConfig

if TYPE_CHECKING:
    from sqlalchemy import Engine

logger = logging.getLogger(__name__)

try:
    # Imported lazily in function to avoid hard dependency at import time in tests
    from alembic import command as _alembic_command
    from alembic.config import Config as _AlembicConfig
except ImportError:  # pragma: no cover - only for environments without Alembic
    _alembic_command = None  # type: ignore[assignment]
    _AlembicConfig = None  # type: ignore[assignment]


async def run_migrations(cfg: AppConfig) -> None:
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
        alembic_cfg.set_main_option("script_location", "bookcard/db/migrations")
        await asyncio.to_thread(_alembic_command.upgrade, alembic_cfg, "head")


def create_lifespan(
    cfg: AppConfig, engine: "Engine"
) -> Callable[[FastAPI], AsyncIterator[None]]:
    """Create lifespan context manager for the FastAPI application.

    Parameters
    ----------
    cfg : AppConfig
        Application configuration.
    engine : Engine
        Database engine.

    Returns
    -------
    Callable[[FastAPI], AsyncIterator[None]]
        Lifespan context manager function (decorated by asynccontextmanager).
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan manager.

        Runs database migrations at startup when enabled and ensures that
        background services (such as the task runner) are shut down gracefully
        during application shutdown or reload.

        Parameters
        ----------
        app : FastAPI
            FastAPI application instance.
        """
        try:
            await run_migrations(cfg)

            # Access app.state early to ensure it is created by Starlette.
            _ = getattr(app, "state", None)

            # Initialize services that depend on database tables being present
            container = ServiceContainer(cfg, engine)
            initialize_services(app, container)

            start_background_services(app)

            # Yield control to allow the application to serve requests.
            yield

        except asyncio.CancelledError:
            # Uvicorn's reload and shutdown mechanisms may cancel the lifespan
            # task (common on Windows with the file-watcher/reloader).
            # Treat this as a graceful shutdown so background workers can stop
            # cleanly without surfacing noisy tracebacks.
            logger.info("Application lifespan cancelled; shutting down gracefully.")
        finally:
            stop_background_services(app)

    return lifespan  # type: ignore[return]

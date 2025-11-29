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

"""Router registration for the FastAPI application.

Uses a registry pattern to allow easy addition of new routers without
modifying the registration function.
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter

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

# Registry of all routers to be registered with the application
ROUTERS: list[APIRouter] = [
    auth_router,
    admin_router,
    authors_router,
    books_router,
    devices_router,
    epub_fixer_router,
    fs_router,
    ingest_router,
    library_scanning_router,
    metadata_router,
    reading_router,
    shelves_router,
    tasks_router,
]


def register_routers(app: FastAPI) -> None:
    """Register all API routers with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    for router in ROUTERS:
        app.include_router(router)

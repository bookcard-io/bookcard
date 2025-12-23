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

from bookcard.api.routes.admin import router as admin_router
from bookcard.api.routes.auth import router as auth_router
from bookcard.api.routes.authors import router as authors_router
from bookcard.api.routes.books import router as books_router
from bookcard.api.routes.comic import router as comic_router
from bookcard.api.routes.devices import router as devices_router
from bookcard.api.routes.download_clients import router as download_clients_router
from bookcard.api.routes.epub_fixer import router as epub_fixer_router
from bookcard.api.routes.fs import router as fs_router
from bookcard.api.routes.indexers import router as indexers_router
from bookcard.api.routes.ingest import router as ingest_router
from bookcard.api.routes.kcc import router as kcc_router
from bookcard.api.routes.kobo import router as kobo_router
from bookcard.api.routes.libraries import router as libraries_router
from bookcard.api.routes.library_scanning import router as library_scanning_router
from bookcard.api.routes.metadata import router as metadata_router
from bookcard.api.routes.opds import router as opds_router
from bookcard.api.routes.plugins import router as plugins_router
from bookcard.api.routes.reading import router as reading_router
from bookcard.api.routes.shelves import router as shelves_router
from bookcard.api.routes.tasks import router as tasks_router

# Registry of all routers to be registered with the application
ROUTERS: list[APIRouter] = [
    auth_router,
    admin_router,
    authors_router,
    books_router,
    comic_router,
    devices_router,
    download_clients_router,
    epub_fixer_router,
    fs_router,
    indexers_router,
    ingest_router,
    kcc_router,
    libraries_router,
    library_scanning_router,
    kobo_router,
    metadata_router,
    opds_router,
    plugins_router,
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

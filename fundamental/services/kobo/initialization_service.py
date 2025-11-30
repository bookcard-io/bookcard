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

"""Kobo initialization service.

Handles device initialization and resource URL generation.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING
from urllib.parse import unquote

import httpx

from fundamental.api.schemas.kobo import KoboInitializationResponse

if TYPE_CHECKING:
    from fundamental.services.kobo.store_proxy_service import KoboStoreProxyService

if TYPE_CHECKING:
    from fastapi import Request

# Kobo Store API URL
KOBO_STOREAPI_URL = "https://storeapi.kobo.com"

# Kobo native resources (fallback when proxy is disabled)
NATIVE_KOBO_RESOURCES = {
    "library_sync": "/kobo/{auth_token}/v1/library/sync",
    "library_metadata": "/kobo/{auth_token}/v1/library/{Ids}/metadata",
    "reading_state": "/kobo/{auth_token}/v1/library/{Ids}/state",
    "tags": "/kobo/{auth_token}/v1/library/tags",
    "image_host": "//cdn.kobo.com/book-images/",
    "image_url_template": "https://cdn.kobo.com/book-images/{ImageId}/{Width}/{Height}/false/image.jpg",
    "image_url_quality_template": "https://cdn.kobo.com/book-images/{ImageId}/{Width}/{Height}/{Quality}/{IsGreyscale}/image.jpg",
}


class KoboInitializationService:
    """Service for handling Kobo device initialization.

    Fetches resources from Kobo Store or uses local resources,
    and transforms URLs to point to local server.

    Parameters
    ----------
    proxy_service : KoboStoreProxyService
        Store proxy service.
    """

    def __init__(self, proxy_service: KoboStoreProxyService) -> None:
        self._proxy_service = proxy_service

    def get_initialization_resources(
        self, request: Request, auth_token: str
    ) -> KoboInitializationResponse:
        """Get initialization resources for Kobo device.

        Parameters
        ----------
        request : Request
            FastAPI request.
        auth_token : str
            Authentication token.

        Returns
        -------
        KoboInitializationResponse
            Initialization response with resources.
        """
        kobo_resources = self._fetch_resources_from_store()

        if not kobo_resources:
            kobo_resources = NATIVE_KOBO_RESOURCES.copy()

        # Update image URLs with our base URL
        base_url = str(request.base_url).rstrip("/")
        kobo_resources = self._transform_resource_urls(
            kobo_resources, base_url, auth_token
        )

        return KoboInitializationResponse(Resources=kobo_resources)

    def _fetch_resources_from_store(self) -> dict[str, object] | None:
        """Fetch resources from Kobo Store.

        Returns
        -------
        dict[str, object] | None
            Resources if successfully fetched, None otherwise.
        """
        if not self._proxy_service.should_proxy():
            return None

        with suppress(httpx.HTTPError, httpx.RequestError, KeyError):
            url = f"{KOBO_STOREAPI_URL}/v1/initialization"
            response = httpx.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if "Resources" in data:
                    return data["Resources"]

        return None

    def _transform_resource_urls(
        self, resources: dict[str, object], base_url: str, auth_token: str
    ) -> dict[str, object]:
        """Transform resource URLs to point to local server.

        Parameters
        ----------
        resources : dict[str, object]
            Resources dictionary.
        base_url : str
            Base URL for local server.
        auth_token : str
            Authentication token.

        Returns
        -------
        dict[str, object]
            Resources with transformed URLs.
        """
        resources["image_host"] = base_url
        resources["image_url_template"] = unquote(
            f"{base_url}/kobo/{auth_token}/{{ImageId}}/{{Width}}/{{Height}}/false/image.jpg"
        )
        resources["image_url_quality_template"] = unquote(
            f"{base_url}/kobo/{auth_token}/{{ImageId}}/{{Width}}/{{Height}}/{{Quality}}/{{IsGreyscale}}/image.jpg"
        )
        return resources

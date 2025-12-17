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

"""Kobo Store proxy service.

Proxies requests to Kobo Store API and merges responses with local sync data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from bookcard.models.config import IntegrationConfig
    from bookcard.services.kobo.sync_token_service import SyncToken

logger = logging.getLogger(__name__)

KOBO_STOREAPI_URL = "https://storeapi.kobo.com"


class KoboStoreProxyService:
    """Service for proxying requests to Kobo Store API.

    When proxy mode is enabled, forwards requests to the official
    Kobo Store API and merges responses with local data.

    Parameters
    ----------
    integration_config : IntegrationConfig | None
        Integration configuration (for kobo_proxy_enabled flag).
    """

    def __init__(self, integration_config: IntegrationConfig | None = None) -> None:
        self._integration_config = integration_config

    def should_proxy(self) -> bool:
        """Check if proxy mode is enabled.

        Returns
        -------
        bool
            True if proxy is enabled, False otherwise.
        """
        if self._integration_config is None:
            return False
        return self._integration_config.kobo_proxy_enabled

    async def proxy_request(
        self,
        path: str,
        method: str,
        headers: dict[str, str],
        data: bytes | None = None,
        sync_token: SyncToken | None = None,
    ) -> httpx.Response:
        """Proxy a request to Kobo Store API.

        Parameters
        ----------
        path : str
            API path (without base URL).
        method : str
            HTTP method.
        headers : dict[str, str]
            Request headers.
        data : bytes | None
            Request body data.
        sync_token : SyncToken | None
            Optional sync token to add to headers.

        Returns
        -------
        httpx.Response
            Response from Kobo Store.

        Raises
        ------
        httpx.HTTPError
            If request fails.
        """
        url = f"{KOBO_STOREAPI_URL}/{path.lstrip('/')}"

        # Prepare headers (remove Host, add sync token if provided)
        outgoing_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
        if sync_token:
            sync_token.to_headers(outgoing_headers)

        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.request(
                method=method,
                url=url,
                headers=outgoing_headers,
                content=data,
                follow_redirects=False,
            )

    def merge_sync_responses(
        self,
        local_results: list[dict[str, object]],
        store_results: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Merge local and store sync responses.

        Parameters
        ----------
        local_results : list[dict[str, object]]
            Local sync results.
        store_results : list[dict[str, object]]
            Store sync results.

        Returns
        -------
        list[dict[str, object]]
            Merged results.
        """
        # Simple merge: combine both lists
        # In a more sophisticated implementation, we could deduplicate
        # based on EntitlementId or RevisionId
        return local_results + store_results

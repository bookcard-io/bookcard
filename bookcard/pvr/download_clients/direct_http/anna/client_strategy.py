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

"""Client switching strategy for Anna's Archive."""

import logging
from collections.abc import Callable
from typing import TypeVar, cast

import httpx

from bookcard.pvr.base.interfaces import HttpClientProtocol
from bookcard.pvr.download_clients.direct_http.bypass import BypassClient
from bookcard.pvr.download_clients.direct_http.protocols import StreamingHttpClient

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ClientSwitchingStrategy:
    """Manages switching between standard and bypass clients."""

    def __init__(
        self,
        primary_factory: Callable[[], HttpClientProtocol],
        bypass_factory: Callable[[], StreamingHttpClient] | None = None,
        flaresolverr_url: str | None = None,
        flaresolverr_path: str = "/v1",
        flaresolverr_timeout: int = 60000,
        use_seleniumbase: bool = False,
    ) -> None:
        self._primary_factory = primary_factory
        if bypass_factory is None:
            self._bypass_factory = lambda: cast(
                "StreamingHttpClient",
                BypassClient(
                    flaresolverr_url=flaresolverr_url,
                    flaresolverr_path=flaresolverr_path,
                    flaresolverr_timeout=flaresolverr_timeout,
                    use_seleniumbase=use_seleniumbase,
                ),
            )
        else:
            self._bypass_factory = bypass_factory

    def execute(self, operation: Callable[[StreamingHttpClient], T]) -> T:
        """Execute operation with primary client, fallback to bypass if needed."""
        # Try standard client first
        with cast(
            "Callable[[], StreamingHttpClient]", self._primary_factory
        )() as client:
            try:
                return operation(client)
            except httpx.HTTPStatusError as e:
                # If blocked (403/429), try switching
                if e.response.status_code in (403, 429):
                    logger.info(
                        "Standard client blocked (%s), switching to bypass client",
                        e.response.status_code,
                    )
                    try:
                        with self._bypass_factory() as bypass_client:
                            return operation(bypass_client)
                    except (httpx.HTTPError, RuntimeError) as bypass_error:
                        logger.warning(
                            "Bypass client also failed: %s", bypass_error, exc_info=True
                        )
                        raise
                raise

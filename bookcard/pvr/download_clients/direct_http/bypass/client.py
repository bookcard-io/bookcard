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

"""Cloudflare bypass client."""

from types import TracebackType
from typing import TYPE_CHECKING, Any

from bookcard.pvr.download_clients.direct_http.bypass.config import (
    FlareSolverrConfig,
    SeleniumBaseConfig,
)
from bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy import (
    FlareSolverrStrategy,
)
from bookcard.pvr.download_clients.direct_http.bypass.response import (
    BypassResponse,
    BypassResponseFactory,
)
from bookcard.pvr.download_clients.direct_http.bypass.seleniumbase_strategy import (
    SeleniumBaseStrategy,
)

if TYPE_CHECKING:
    from bookcard.pvr.download_clients.direct_http.bypass.strategy import (
        BypassStrategy,
    )


class BypassClient:
    """Cloudflare bypass client using FlareSolverr or SeleniumBase.

    Parameters
    ----------
    flaresolverr_url : str | None
        FlareSolverr service URL (default: http://flaresolverr:8191)
    flaresolverr_path : str
        FlareSolverr API path (default: /v1)
    flaresolverr_timeout : int
        FlareSolverr timeout in milliseconds (default: 60000)
    use_seleniumbase : bool
        Use SeleniumBase instead of FlareSolverr (default: False)
    """

    def __init__(
        self,
        flaresolverr_url: str | None = None,
        flaresolverr_path: str = "/v1",
        flaresolverr_timeout: int = 60000,
        use_seleniumbase: bool = False,
    ) -> None:
        """Initialize bypass client."""
        # Create strategy based on configuration
        if use_seleniumbase:
            seleniumbase_config = SeleniumBaseConfig()
            self._strategy: BypassStrategy = SeleniumBaseStrategy(seleniumbase_config)
        else:
            flaresolverr_config = FlareSolverrConfig(
                url=flaresolverr_url or FlareSolverrConfig.url,
                path=flaresolverr_path,
                timeout=flaresolverr_timeout,
            )
            self._strategy = FlareSolverrStrategy(flaresolverr_config)

        self._response_factory = BypassResponseFactory()

    def get(self, url: str, **kwargs: Any) -> BypassResponse:  # noqa: ANN401
        """Perform HTTP GET request with Cloudflare bypass.

        Parameters
        ----------
        url : str
            URL to fetch.
        **kwargs : Any
            Additional arguments (follow_redirects and extensions are ignored).

        Returns
        -------
        BypassResponse
            Response from bypass operation.
        """
        # Remove unsupported kwargs
        kwargs.pop("follow_redirects", None)
        kwargs.pop("extensions", None)

        result = self._strategy.fetch(url)

        if result.success and result.html is not None:
            return self._response_factory.create_success(url, result.html)
        return self._response_factory.create_error(url)

    def __enter__(self) -> "BypassClient":
        """Enter context manager.

        Returns
        -------
        BypassClient
            Self instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if exception occurred.
        exc_val : BaseException | None
            Exception value if exception occurred.
        exc_tb : TracebackType | None
            Traceback if exception occurred.
        """
        # No cleanup needed for FlareSolverr
        # SeleniumBase drivers are cleaned up in strategy

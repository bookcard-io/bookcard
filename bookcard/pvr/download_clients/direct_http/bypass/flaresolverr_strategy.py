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

"""FlareSolverr bypass strategy implementation."""

import logging
from typing import TYPE_CHECKING

from requests import exceptions as requests_exceptions

from bookcard.pvr.download_clients.direct_http.bypass.config import FlareSolverrConfig
from bookcard.pvr.download_clients.direct_http.bypass.constants import (
    BypassConstants,
)
from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult
from bookcard.pvr.download_clients.direct_http.bypass.strategy import BypassStrategy

if TYPE_CHECKING:
    import requests
else:
    try:
        import requests
    except ImportError:
        requests = None

logger = logging.getLogger(__name__)


class FlareSolverrStrategy(BypassStrategy):
    """FlareSolverr bypass strategy."""

    def __init__(self, config: FlareSolverrConfig) -> None:
        """Initialize FlareSolverr strategy.

        Parameters
        ----------
        config : FlareSolverrConfig
            Configuration for FlareSolverr.
        """
        self._config = config
        self.validate_dependencies()

    def validate_dependencies(self) -> None:
        """Validate required dependencies are available.

        Raises
        ------
        ImportError
            If requests library is not available.
        """
        if requests is None:
            msg = "requests library required for FlareSolverr"
            raise ImportError(msg)

    def fetch(self, url: str) -> BypassResult:
        """Fetch HTML via FlareSolverr.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        BypassResult
            Result containing HTML or error information.
        """
        html = self._do_fetch(url)
        if html:
            return BypassResult(html=html)
        return BypassResult(html=None, error="Failed to fetch from FlareSolverr")

    def _do_fetch(self, url: str) -> str | None:
        """Perform actual fetch operation.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        str | None
            HTML content or None if fetch failed.
        """
        connect_timeout = BypassConstants.FLARESOLVERR_CONNECT_TIMEOUT
        read_timeout = min(
            (self._config.timeout / 1000)
            + BypassConstants.FLARESOLVERR_READ_TIMEOUT_BUFFER,
            BypassConstants.FLARESOLVERR_MAX_READ_TIMEOUT,
        )

        try:
            response = requests.post(
                f"{self._config.url}{self._config.path}",
                headers={"Content-Type": "application/json"},
                json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": self._config.timeout,
                },
                timeout=(connect_timeout, read_timeout),
            )
            response.raise_for_status()
            result = response.json()

            status = result.get("status", "unknown")
            message = result.get("message", "")
            logger.debug(
                "FlareSolverr response for '%s': %s - %s", url, status, message
            )

            if status != "ok":
                logger.warning(
                    "FlareSolverr failed for '%s': %s - %s", url, status, message
                )
                return None

            solution = result.get("solution")
            html = solution.get("response", "") if solution else ""

            if not html:
                logger.warning("FlareSolverr returned empty response for '%s'", url)
                return None
        except requests_exceptions.Timeout:
            timeout_msg = (
                f"FlareSolverr timed out for '{url}' "
                f"(connect: {connect_timeout}s, read: {read_timeout:.0f}s)"
            )
            logger.warning(timeout_msg)
            return None
        except requests_exceptions.RequestException as e:
            logger.warning("FlareSolverr request failed for '%s': %s", url, e)
            return None
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                "FlareSolverr returned malformed response for '%s': %s", url, e
            )
            return None
        else:
            return html

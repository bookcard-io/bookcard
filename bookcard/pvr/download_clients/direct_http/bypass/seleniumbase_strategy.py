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

"""SeleniumBase bypass strategy implementation."""

import logging
from contextlib import suppress

from seleniumbase import Driver

from bookcard.pvr.download_clients.direct_http.bypass.config import SeleniumBaseConfig
from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult
from bookcard.pvr.download_clients.direct_http.bypass.strategy import BypassStrategy

logger = logging.getLogger(__name__)


class SeleniumBaseStrategy(BypassStrategy):
    """SeleniumBase bypass strategy."""

    def __init__(self, config: SeleniumBaseConfig) -> None:
        """Initialize SeleniumBase strategy.

        Parameters
        ----------
        config : SeleniumBaseConfig
            Configuration for SeleniumBase.
        """
        self._config = config
        self.validate_dependencies()

    def validate_dependencies(self) -> None:
        """Validate required dependencies are available.

        Raises
        ------
        ImportError
            If SeleniumBase Driver is not available.
        """
        if Driver is None:
            msg = "SeleniumBase Driver required for internal bypass"
            raise ImportError(msg)

    def fetch(self, url: str) -> BypassResult:
        """Fetch HTML via SeleniumBase.

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
        return BypassResult(html=None, error="Failed to fetch from SeleniumBase")

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
        driver = None
        try:
            logger.debug("Creating SeleniumBase driver for bypass")
            driver = Driver(
                uc=True,
                headless=self._config.headless,
                incognito=self._config.incognito,
                locale=self._config.locale,
                ad_block=self._config.ad_block,
            )
            driver.set_page_load_timeout(self._config.page_load_timeout)

            logger.debug("Opening URL with SeleniumBase: %s", url)
            # SeleniumBase Driver has uc_open_with_reconnect method but type stubs don't include it
            driver.uc_open_with_reconnect(  # type: ignore[attr-defined, misc]
                url, reconnect_time=self._config.reconnect_time
            )

            html = driver.page_source
            if not html:
                logger.warning("SeleniumBase returned empty page for '%s'", url)
                return None

            logger.debug("SeleniumBase bypass successful for '%s'", url)
        except (TimeoutError, RuntimeError, AttributeError) as e:
            logger.warning("SeleniumBase bypass failed for '%s': %s", url, e)
            return None
        except Exception as e:  # noqa: BLE001
            # SeleniumBase/undetected-chromedriver may raise generic Exception
            # (e.g., "Chrome not found! Install it first!")
            logger.warning(
                "SeleniumBase driver initialization failed for '%s': %s", url, e
            )
            return None
        else:
            return html
        finally:
            if driver:
                with suppress(Exception):
                    driver.quit()

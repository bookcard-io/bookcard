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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from seleniumbase import Driver

from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult
from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_engine import (
    BypassEngine,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods import (
    DEFAULT_BYPASS_METHODS,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    CLOUDFLARE_INDICATORS,
    DDOS_GUARD_INDICATORS,
    DEFAULT_MAX_FETCH_RETRIES,
    DRIVER_RESET_ERRORS,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.cookie_store import (
    ThreadSafeCookieStore,
    ThreadSafeUserAgentStore,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.display_manager import (
    VirtualDisplayManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.driver_factory import (
    DriverFactory,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.driver_manager import (
    DriverManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.process_manager import (
    DockerProcessManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.strategy import BypassStrategy

if TYPE_CHECKING:
    from bookcard.pvr.download_clients.direct_http.bypass.config import (
        SeleniumBaseConfig,
    )

logger = logging.getLogger(__name__)


def _looks_like_protection_page(html: str) -> bool:
    """Heuristically detect if HTML looks like a protection/challenge page."""
    text = html.lower()
    return any(
        indicator in text
        for indicator in (CLOUDFLARE_INDICATORS + DDOS_GUARD_INDICATORS)
    )


class SeleniumBaseStrategy(BypassStrategy):
    """SeleniumBase bypass strategy.

    This class orchestrates the bypass process by composing specialized
    components for display management, driver lifecycle, process cleanup,
    and bypass execution.
    """

    def __init__(self, config: SeleniumBaseConfig) -> None:
        """Initialize SeleniumBase strategy.

        Parameters
        ----------
        config : SeleniumBaseConfig
            Configuration for SeleniumBase.
        """
        self._config = config
        self.validate_dependencies()

        # Initialize dependencies (Dependency Injection)
        self._process_manager = DockerProcessManager()
        self._display_manager = VirtualDisplayManager(
            reconnect_time=self._config.reconnect_time
        )
        self._driver_factory = DriverFactory(config)
        self._driver_manager = DriverManager(self._process_manager)
        self._cookie_store = ThreadSafeCookieStore()
        self._user_agent_store = ThreadSafeUserAgentStore()
        self._bypass_engine = BypassEngine(DEFAULT_BYPASS_METHODS)

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

    def _try_fetch_with_cached_session(self, url: str) -> str | None:
        """Try a plain HTTP fetch with cached cookies/UA.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        str | None
            HTML if request succeeds and doesn't look like a protection page.
        """
        cookies = self._cookie_store.get_cookie_values_for_url(url)
        if not cookies:
            return None

        headers: dict[str, str] = {}
        if ua := self._user_agent_store.get_user_agent_for_url(url):
            headers["User-Agent"] = ua

        try:
            response = httpx.get(
                url,
                cookies=cookies,
                headers=headers,
                follow_redirects=True,
                timeout=10.0,
            )
        except httpx.HTTPError as e:
            logger.debug("Cached-cookie HTTP fetch failed for %s: %s", url, e)
            return None

        if response.status_code != 200:
            logger.debug(
                "Cached-cookie HTTP fetch blocked for %s (status=%s)",
                url,
                response.status_code,
            )
            return None
        if not response.text:
            return None
        if _looks_like_protection_page(response.text):
            logger.debug("Cached-cookie HTTP fetch still shows protection for %s", url)
            return None

        logger.debug("Cached bypass cookies worked; skipped SeleniumBase for %s", url)
        return response.text

    def _apply_cached_cookies_to_driver(
        self,
        driver: Driver,  # type: ignore[invalid-type-form]
        url: str,
    ) -> None:
        """Apply cached cookies to a fresh driver session (best-effort)."""
        try:
            parsed = urlparse(url)
            origin = (
                f"{parsed.scheme}://{parsed.netloc}/"
                if parsed.scheme and parsed.netloc
                else ""
            )
        except ValueError:
            return

        if not origin:
            return

        cookies_to_apply = self._cookie_store.get_cookie_dicts_for_url(url)
        if not cookies_to_apply:
            return

        try:
            driver.uc_open_with_reconnect(
                origin, reconnect_time=min(self._config.reconnect_time, 1.0)
            )
        except (AttributeError, RuntimeError, TimeoutError, ValueError):
            return

        applied = 0
        for cookie in cookies_to_apply:
            try:
                driver.add_cookie(cookie)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                continue
            else:
                applied += 1

        if applied:
            logger.debug("Applied %d cached cookies for %s", applied, parsed.netloc)

    def _attempt_fetch_with_bypass(
        self,
        driver: Driver,  # type: ignore[invalid-type-form]
        url: str,
    ) -> str | None:
        """Attempt to fetch URL and bypass protection.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        url : str
            URL to fetch.

        Returns
        -------
        str | None
            HTML content if successful, None otherwise.
        """
        self._apply_cached_cookies_to_driver(driver, url)

        logger.debug("Opening URL with SeleniumBase: %s", url)
        # SeleniumBase Driver has uc_open_with_reconnect method but type stubs don't include it
        driver.uc_open_with_reconnect(url, reconnect_time=self._config.reconnect_time)

        try:
            logger.debug(
                "Page loaded - URL: %s, Title: %s",
                driver.get_current_url(),
                driver.get_title(),
            )
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Could not get page info: %s", e)

        logger.debug("Starting bypass process...")
        if self._bypass_engine.attempt_bypass(driver, max_retries=6):
            self._cookie_store.extract_from_driver(driver, url)
            self._user_agent_store.extract_from_driver(driver, url)
            html = driver.page_source
            if html:
                logger.debug("SeleniumBase bypass successful for '%s'", url)
                return html

        logger.warning("Bypass completed but page still shows protection")
        try:
            body = driver.get_text("body")
            logger.debug(
                "Page content: %s...",
                body[:500] if len(body) > 500 else body,
            )
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Could not get page body: %s", e)
        return None

    def _handle_driver_error(
        self,
        e: Exception,
        attempt: int,
        max_retries: int,
        url: str,
        driver: Driver | None,  # type: ignore[invalid-type-form]
    ) -> Driver | None:  # type: ignore[invalid-type-form]
        """Handle driver errors and restart if needed.

        Parameters
        ----------
        e : Exception
            The exception that occurred.
        attempt : int
            Current attempt number.
        max_retries : int
            Maximum number of retries.
        url : str
            URL being fetched.
        driver : Driver | None
            Current driver instance.

        Returns
        -------
        Driver | None
            Driver instance (None if restarted).
        """
        error_name = type(e).__name__
        logger.warning(
            "SeleniumBase driver error (attempt %d/%d) for '%s': %s",
            attempt + 1,
            max_retries,
            url,
            e,
        )
        if error_name in DRIVER_RESET_ERRORS:
            logger.info("Restarting Chrome due to browser error...")
            self._driver_manager.quit(driver)
            return None
        return driver

    def _do_fetch(
        self, url: str, max_retries: int = DEFAULT_MAX_FETCH_RETRIES
    ) -> str | None:
        """Perform actual fetch operation with bypass.

        Parameters
        ----------
        url : str
            URL to fetch.
        max_retries : int
            Maximum number of retry attempts.

        Returns
        -------
        str | None
            HTML content or None if fetch failed.
        """
        if cached_html := self._try_fetch_with_cached_session(url):
            return cached_html

        # Clean up orphan processes before starting Selenium
        self._process_manager.cleanup_orphans()

        # Ensure virtual display is initialized before creating driver
        screen_width, screen_height = self._driver_factory.get_screen_size()
        self._display_manager.ensure_initialized(
            screen_width, screen_height, self._config.headless
        )

        driver = None
        try:
            for attempt in range(max_retries):
                try:
                    if driver is None:
                        logger.debug("Creating SeleniumBase driver for bypass")
                        driver = self._driver_factory.create()

                    html = self._attempt_fetch_with_bypass(driver, url)
                    if html:
                        return html

                except (TimeoutError, RuntimeError, AttributeError) as e:
                    driver = self._handle_driver_error(
                        e, attempt, max_retries, url, driver
                    )
                except (
                    OSError,
                    ConnectionError,
                    BrokenPipeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    IndexError,
                ) as e:
                    # SeleniumBase/undetected-chromedriver may raise various exceptions
                    # Catch common webdriver-related exceptions instead of blind Exception
                    driver = self._handle_driver_error(
                        e, attempt, max_retries, url, driver
                    )

            logger.error("Bypass failed after %d attempts", max_retries)
            return None

        finally:
            if driver:
                self._driver_manager.quit(driver)

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

"""Cookie and User-Agent storage for bypass operations."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlparse

if TYPE_CHECKING:
    from seleniumbase import Driver

from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    CF_COOKIE_NAMES,
    DDG_COOKIE_NAMES,
    FULL_COOKIE_DOMAINS,
)

logger = logging.getLogger(__name__)


def _get_base_domain(domain: str) -> str:
    """Extract base domain from hostname (e.g., 'www.example.com' -> 'example.com').

    Parameters
    ----------
    domain : str
        Hostname to extract base domain from.

    Returns
    -------
    str
        Base domain.
    """
    return ".".join(domain.split(".")[-2:]) if "." in domain else domain


def _should_extract_cookie(name: str, extract_all: bool) -> bool:
    """Determine if a cookie should be extracted based on its name.

    Parameters
    ----------
    name : str
        Cookie name.
    extract_all : bool
        Whether to extract all cookies.

    Returns
    -------
    bool
        True if cookie should be extracted.
    """
    if extract_all:
        return True
    is_cf = name in CF_COOKIE_NAMES or name.startswith("cf_")
    is_ddg = name in DDG_COOKIE_NAMES or name.startswith("__ddg")
    return is_cf or is_ddg


class CookieStore(Protocol):
    """Protocol for cookie storage."""

    def get(self, domain: str) -> dict[str, dict]:
        """Get cookies for a domain.

        Parameters
        ----------
        domain : str
            Base domain to get cookies for.

        Returns
        -------
        dict[str, dict]
            Dictionary of cookie name to cookie data.
        """
        ...

    def set(self, domain: str, cookies: dict[str, dict]) -> None:
        """Store cookies for a domain.

        Parameters
        ----------
        domain : str
            Base domain to store cookies for.
        cookies : dict[str, dict]
            Dictionary of cookie name to cookie data.
        """
        ...


class ThreadSafeCookieStore:
    """Thread-safe cookie storage implementation."""

    def __init__(self) -> None:
        """Initialize cookie store."""
        self._cookies: dict[str, dict[str, dict]] = {}
        self._lock = threading.Lock()

    def get(self, domain: str) -> dict[str, dict]:
        """Get cookies for a domain.

        Parameters
        ----------
        domain : str
            Base domain to get cookies for.

        Returns
        -------
        dict[str, dict]
            Dictionary of cookie name to cookie data (copied).
        """
        with self._lock:
            return self._cookies.get(domain, {}).copy()

    def set(self, domain: str, cookies: dict[str, dict]) -> None:
        """Store cookies for a domain.

        Parameters
        ----------
        domain : str
            Base domain to store cookies for.
        cookies : dict[str, dict]
            Dictionary of cookie name to cookie data.
        """
        with self._lock:
            self._cookies[domain] = cookies.copy()

    def extract_from_driver(
        self,
        driver: Driver,  # type: ignore[invalid-type-form, misc]
        url: str,
    ) -> None:
        """Extract cookies from Chrome driver after successful bypass.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        url : str
            URL that was bypassed.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            if not domain:
                return

            base_domain = _get_base_domain(domain)
            extract_all = base_domain in FULL_COOKIE_DOMAINS

            cookies_found = {}
            for cookie in driver.get_cookies():
                name = cookie.get("name", "")
                if _should_extract_cookie(name, extract_all):
                    cookies_found[name] = {
                        "value": cookie.get("value", ""),
                        "domain": cookie.get("domain", domain),
                        "path": cookie.get("path", "/"),
                        "expiry": cookie.get("expiry"),
                        "secure": cookie.get("secure", True),
                        "httpOnly": cookie.get("httpOnly", True),
                    }

            if not cookies_found:
                return

            self.set(base_domain, cookies_found)

            cookie_type = "all" if extract_all else "protection"
            logger.debug(
                "Extracted %d %s cookies for %s",
                len(cookies_found),
                cookie_type,
                base_domain,
            )

        except (AttributeError, RuntimeError, KeyError, TypeError) as e:
            logger.debug("Failed to extract cookies: %s", e)

    def get_cookie_values_for_url(self, url: str) -> dict[str, str]:
        """Get valid cookie name/value pairs for a URL.

        Parameters
        ----------
        url : str
            URL to retrieve cookies for.

        Returns
        -------
        dict[str, str]
            Mapping of cookie name to cookie value. Empty if none available or
            if cached cookies are expired.
        """
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if not hostname:
            return {}

        base_domain = _get_base_domain(hostname)
        cookies = self.get(base_domain)
        if not cookies:
            return {}

        # If cf_clearance is expired, drop the whole cache for the domain.
        cf_clearance = cookies.get("cf_clearance", {})
        expiry = cf_clearance.get("expiry")
        if isinstance(expiry, (int, float)) and time.time() > float(expiry):
            logger.debug("Cached bypass cookies expired for %s", base_domain)
            self.set(base_domain, {})
            return {}

        return {
            name: data.get("value", "")
            for name, data in cookies.items()
            if isinstance(name, str) and data.get("value")
        }

    def get_cookie_dicts_for_url(self, url: str) -> list[dict]:
        """Get Selenium-compatible cookie dicts for a URL.

        Parameters
        ----------
        url : str
            URL to retrieve cookies for.

        Returns
        -------
        list[dict]
            List of cookie dictionaries suitable for `driver.add_cookie()`.
            Returns empty list if none available or cookies are expired.
        """
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if not hostname:
            return []

        base_domain = _get_base_domain(hostname)
        cookies = self.get(base_domain)
        if not cookies:
            return []

        cf_clearance = cookies.get("cf_clearance", {})
        expiry = cf_clearance.get("expiry")
        if isinstance(expiry, (int, float)) and time.time() > float(expiry):
            logger.debug("Cached bypass cookies expired for %s", base_domain)
            self.set(base_domain, {})
            return []

        out: list[dict] = []
        for name, data in cookies.items():
            if not isinstance(name, str):
                continue
            value = data.get("value")
            if not value:
                continue

            cookie: dict = {
                "name": name,
                "value": value,
                "domain": data.get("domain") or hostname,
                "path": data.get("path") or "/",
            }
            cookie_expiry = data.get("expiry")
            if isinstance(cookie_expiry, (int, float)):
                cookie["expiry"] = int(cookie_expiry)
            out.append(cookie)
        return out


class UserAgentStore(Protocol):
    """Protocol for user agent storage."""

    def get(self, domain: str) -> str | None:
        """Get user agent for a domain.

        Parameters
        ----------
        domain : str
            Base domain to get user agent for.

        Returns
        -------
        str | None
            User agent string or None if not found.
        """
        ...

    def set(self, domain: str, user_agent: str) -> None:
        """Store user agent for a domain.

        Parameters
        ----------
        domain : str
            Base domain to store user agent for.
        user_agent : str
            User agent string.
        """
        ...


class ThreadSafeUserAgentStore:
    """Thread-safe user agent storage implementation."""

    def __init__(self) -> None:
        """Initialize user agent store."""
        self._user_agents: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, domain: str) -> str | None:
        """Get user agent for a domain.

        Parameters
        ----------
        domain : str
            Base domain to get user agent for.

        Returns
        -------
        str | None
            User agent string or None if not found.
        """
        with self._lock:
            return self._user_agents.get(domain)

    def set(self, domain: str, user_agent: str) -> None:
        """Store user agent for a domain.

        Parameters
        ----------
        domain : str
            Base domain to store user agent for.
        user_agent : str
            User agent string.
        """
        with self._lock:
            self._user_agents[domain] = user_agent
            logger.debug("Stored UA for %s: %s...", domain, user_agent[:60])

    def extract_from_driver(
        self,
        driver: Driver,  # type: ignore[invalid-type-form, misc]
        url: str,
    ) -> None:
        """Extract user agent from Chrome driver.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        url : str
            URL that was accessed.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            if not domain:
                return

            base_domain = _get_base_domain(domain)
            user_agent = driver.execute_script("return navigator.userAgent")
            if user_agent:
                self.set(base_domain, user_agent)
            else:
                logger.debug("No UA captured for %s", base_domain)

        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Failed to extract user agent: %s", e)

    def get_user_agent_for_url(self, url: str) -> str | None:
        """Get stored user agent for a URL.

        Parameters
        ----------
        url : str
            URL to retrieve stored user agent for.

        Returns
        -------
        str | None
            Stored user agent string for the URL's base domain, if available.
        """
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if not hostname:
            return None
        return self.get(_get_base_domain(hostname))

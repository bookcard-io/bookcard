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

"""Driver factory for creating and configuring Chrome drivers."""

import logging
import os
import random
import socket
import time
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING

from seleniumbase import Driver

from bookcard.pvr.download_clients.direct_http.anna.config import AnnaArchiveConfig
from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    COMMON_RESOLUTIONS,
)

if TYPE_CHECKING:
    from bookcard.pvr.download_clients.direct_http.bypass.config import (
        SeleniumBaseConfig,
    )

logger = logging.getLogger(__name__)

# Use SystemRandom for non-cryptographic randomness (satisfies S311)
_sys_random = random.SystemRandom()


class DriverFactory:
    """Factory for creating and configuring Chrome drivers."""

    def __init__(self, config: "SeleniumBaseConfig") -> None:
        """Initialize driver factory.

        Parameters
        ----------
        config : SeleniumBaseConfig
            Configuration for driver creation.
        """
        self._config = config
        self._screen_size: tuple[int, int] | None = None

    def _generate_screen_size(self) -> tuple[int, int]:
        """Generate a random screen size from common resolutions.

        Returns
        -------
        tuple[int, int]
            Screen width and height in pixels.
        """
        resolutions = [(w, h) for w, h, _ in COMMON_RESOLUTIONS]
        weights = [weight for _, _, weight in COMMON_RESOLUTIONS]
        return _sys_random.choices(resolutions, weights=weights)[0]

    def get_screen_size(self) -> tuple[int, int]:
        """Get current screen size, generating one if not set.

        Returns
        -------
        tuple[int, int]
            Screen width and height in pixels.
        """
        if self._screen_size is None:
            self._screen_size = self._generate_screen_size()
            logger.debug(
                "Generated initial screen size: %dx%d",
                self._screen_size[0],
                self._screen_size[1],
            )
        return self._screen_size

    def _is_docker(self) -> bool:
        """Check if running in Docker environment."""
        return Path("/.dockerenv").exists() or os.environ.get("DOCKERMODE") == "true"

    def _get_chromium_args(self) -> list[str]:
        """Build Chrome arguments for driver initialization.

        Returns
        -------
        list[str]
            List of Chrome command-line arguments.
        """
        arguments = [
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--allow-running-insecure-content",
            "--ignore-certificate-errors-spki-list",
            "--ignore-certificate-errors-skip-list",
        ]

        # Essential flags for Docker/restricted environments
        if self._is_docker():
            arguments.extend([
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",  # Overcome limited resource problems
            ])

        host_rules = self._build_host_resolver_rules()
        if host_rules:
            arguments.append(f"--host-resolver-rules={', '.join(host_rules)}")
            logger.debug(
                "Chrome: Using host resolver rules for %d hosts", len(host_rules)
            )

        return arguments

    def _build_host_resolver_rules(self) -> list[str]:
        """Pre-resolve AA hostnames and build Chrome host resolver rules."""
        host_rules = []
        try:
            for url in AnnaArchiveConfig().mirrors:
                hostname = urllib.parse.urlparse(url).hostname
                if not hostname:
                    continue

                try:
                    # Resolve to IPv4
                    results = socket.getaddrinfo(hostname, 443, socket.AF_INET)
                    if results:
                        ip = results[0][4][0]
                        host_rules.append(f"MAP {hostname} {ip}")
                        logger.debug("Chrome: Pre-resolved %s -> %s", hostname, ip)
                    else:
                        logger.warning("Chrome: No addresses returned for %s", hostname)
                except socket.gaierror as e:
                    logger.warning("Chrome: Could not pre-resolve %s: %s", hostname, e)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            logger.warning("Error pre-resolving hostnames for Chrome: %s", e)

        return host_rules

    def create(self) -> Driver:  # type: ignore[invalid-type-form]
        """Create a fresh Chrome driver instance.

        Returns
        -------
        Driver
            SeleniumBase driver instance.
        """
        chromium_args = self._get_chromium_args()
        screen_width, screen_height = self.get_screen_size()

        logger.debug("Creating Chrome driver with args: %s", chromium_args)
        logger.debug("Browser screen size: %sx%s", screen_width, screen_height)

        driver = Driver(
            uc=True,
            headless=self._config.headless,
            incognito=self._config.incognito,
            locale=self._config.locale,
            ad_block=self._config.ad_block,
            size=f"{screen_width},{screen_height}",
            chromium_arg=chromium_args,
        )
        driver.set_page_load_timeout(self._config.page_load_timeout)
        time.sleep(self._config.reconnect_time)
        logger.debug("Chrome browser ready")
        return driver

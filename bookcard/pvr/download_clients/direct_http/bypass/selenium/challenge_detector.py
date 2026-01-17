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

"""Challenge detection for protection systems."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    CLOUDFLARE_INDICATORS,
    DDOS_GUARD_INDICATORS,
)

if TYPE_CHECKING:
    from seleniumbase import Driver

logger = logging.getLogger(__name__)


def _get_page_info(sb: "Driver") -> tuple[str, str, str]:  # type: ignore[invalid-type-form]
    """Extract page title, body text, and current URL safely.

    Parameters
    ----------
    sb : Driver
        SeleniumBase driver instance.

    Returns
    -------
    tuple[str, str, str]
        Title, body text, and current URL.
    """
    try:
        title = sb.get_title().lower()
    except (AttributeError, RuntimeError, TimeoutError):
        title = ""
    try:
        body = sb.get_text("body").lower()
    except (AttributeError, RuntimeError, TimeoutError):
        body = ""
    try:
        current_url = sb.get_current_url()
    except (AttributeError, RuntimeError, TimeoutError):
        current_url = ""
    return title, body, current_url


def _check_indicators(title: str, body: str, indicators: list[str]) -> str | None:
    """Check if any indicator is present in title or body.

    Parameters
    ----------
    title : str
        Page title.
    body : str
        Page body text.
    indicators : list[str]
        List of indicators to check for.

    Returns
    -------
    str | None
        Found indicator or None.
    """
    for indicator in indicators:
        if indicator in title or indicator in body:
            return indicator
    return None


class ChallengeDetector(ABC):
    """Abstract base class for challenge detection."""

    @abstractmethod
    def detect(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Detect if this challenge type is present.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if challenge detected.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this challenge type.

        Returns
        -------
        str
            Challenge type name.
        """
        ...


class CloudflareDetector(ChallengeDetector):
    """Detector for Cloudflare challenges."""

    def detect(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Detect Cloudflare challenge.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if Cloudflare challenge detected.
        """
        try:
            title, body, current_url = _get_page_info(driver)

            # Check indicators
            if found := _check_indicators(title, body, CLOUDFLARE_INDICATORS):
                logger.debug("Cloudflare indicator found: '%s'", found)
                return True

            # Check URL patterns
            if (
                "cf-" in body
                or "cloudflare" in current_url.lower()
                or "/cdn-cgi/" in current_url
            ):
                return True

        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.warning("Error detecting Cloudflare challenge: %s", e)
        return False

    def get_name(self) -> str:
        """Get challenge type name.

        Returns
        -------
        str
            "cloudflare"
        """
        return "cloudflare"


class DdosGuardDetector(ChallengeDetector):
    """Detector for DDoS-Guard challenges."""

    def detect(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Detect DDoS-Guard challenge.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if DDoS-Guard challenge detected.
        """
        try:
            title, body, _ = _get_page_info(driver)
            if found := _check_indicators(title, body, DDOS_GUARD_INDICATORS):
                logger.debug("DDOS-Guard indicator found: '%s'", found)
                return True
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.warning("Error detecting DDoS-Guard challenge: %s", e)
        return False

    def get_name(self) -> str:
        """Get challenge type name.

        Returns
        -------
        str
            "ddos_guard"
        """
        return "ddos_guard"


class ChallengeDetectionService:
    """Service for detecting challenge types."""

    def __init__(self, detectors: list[ChallengeDetector] | None = None) -> None:
        """Initialize detection service.

        Parameters
        ----------
        detectors : list[ChallengeDetector] | None
            List of challenge detectors. Defaults to Cloudflare and DDoS-Guard.
        """
        self._detectors = detectors or [
            DdosGuardDetector(),
            CloudflareDetector(),
        ]

    def detect(self, driver: "Driver") -> str:  # type: ignore[invalid-type-form]
        """Detect challenge type.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        str
            Challenge type: 'cloudflare', 'ddos_guard', or 'none'.
        """
        for detector in self._detectors:
            if detector.detect(driver):
                return detector.get_name()
        return "none"

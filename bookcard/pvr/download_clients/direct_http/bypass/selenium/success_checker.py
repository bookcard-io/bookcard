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

"""Success checking for bypass operations."""

import logging
from typing import TYPE_CHECKING

import emoji

from bookcard.pvr.download_clients.direct_http.bypass.selenium.challenge_detector import (
    _get_page_info,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    CLOUDFLARE_INDICATORS,
    DDOS_GUARD_INDICATORS,
    MIN_BODY_LENGTH,
    MIN_CONTENT_LENGTH_FOR_BYPASS,
    MIN_EMOJI_COUNT,
)

if TYPE_CHECKING:
    from seleniumbase import Driver

logger = logging.getLogger(__name__)


def _check_indicators(title: str, body: str, indicators: list[str]) -> bool:
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
    bool
        True if any indicator found.
    """
    return any(indicator in title or indicator in body for indicator in indicators)


def _has_cloudflare_patterns(body: str, url: str) -> bool:
    """Check for Cloudflare-specific patterns in body or URL.

    Parameters
    ----------
    body : str
        Page body text.
    url : str
        Current URL.

    Returns
    -------
    bool
        True if Cloudflare patterns detected.
    """
    return "cf-" in body or "cloudflare" in url.lower() or "/cdn-cgi/" in url


class SuccessChecker:
    """Checks if bypass was successful."""

    def is_bypassed(self, driver: "Driver", escape_emojis: bool = True) -> bool:  # type: ignore[invalid-type-form]
        """Check if the protection has been bypassed.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        escape_emojis : bool
            Whether to check for emojis as bypass indicator.

        Returns
        -------
        bool
            True if bypassed.
        """
        try:
            title, body, current_url = _get_page_info(driver)
            body_len = len(body.strip())

            # Long page content = probably bypassed
            if body_len > MIN_CONTENT_LENGTH_FOR_BYPASS:
                logger.debug(
                    "Page content too long, probably bypassed (len: %d)", body_len
                )
                return True

            # Multiple emojis = probably real content
            if escape_emojis:
                try:
                    emoji_list_result = emoji.emoji_list(body)
                    if len(emoji_list_result) >= MIN_EMOJI_COUNT:
                        logger.debug("Detected emojis in page, probably bypassed")
                        return True
                except (AttributeError, TypeError):
                    logger.debug("Error checking emojis")

            # Check for protection indicators (means NOT bypassed)
            if _check_indicators(
                title, body, CLOUDFLARE_INDICATORS + DDOS_GUARD_INDICATORS
            ):
                return False

            # Cloudflare URL patterns
            if _has_cloudflare_patterns(body, current_url):
                logger.debug("Cloudflare patterns detected in page")
                return False

            # Page too short = still loading
            if body_len < MIN_BODY_LENGTH:
                logger.debug("Page content too short, might still be loading")
                return False

        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.warning("Error checking bypass status: %s", e)
            return False
        else:
            logger.debug(
                "Bypass check passed - Title: '%s', Body length: %d",
                title[:100],
                body_len,
            )
            return True

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

"""Countdown handling for Anna's Archive."""

import logging
import re
from contextlib import suppress

from bs4 import BeautifulSoup

from bookcard.pvr.download_clients.direct_http.protocols import TimeProvider

logger = logging.getLogger(__name__)


class CountdownHandler:
    """Manages countdown detection and waiting."""

    def __init__(self, time_provider: TimeProvider, max_seconds: int) -> None:
        self._time = time_provider
        self._max_seconds = max_seconds

    def handle_countdown(self, soup: BeautifulSoup, html_str: str) -> int:
        """
        Check for countdown and wait if necessary.

        Returns
        -------
            int: The detected countdown seconds.

        Raises
        ------
            TimeoutError: If countdown exceeds max_seconds.
        """
        seconds = self._extract_countdown_seconds(soup, html_str)
        if seconds <= 0:
            return 0

        logger.info("AA countdown detected: %ds", seconds)
        if seconds > self._max_seconds:
            logger.warning("Countdown too long (%ds), aborting", seconds)
            msg = f"Countdown too long: {seconds}s"
            raise TimeoutError(msg)

        self._time.sleep(seconds + 1)
        return seconds

    def _extract_countdown_seconds(self, soup: BeautifulSoup, html_str: str) -> int:
        elem = soup.find("span", class_="js-partner-countdown")
        if elem:
            with suppress(ValueError):
                return int(elem.get_text(strip=True))

        for elem in soup.find_all(
            ["span", "div"],
            class_=lambda c: c and ("timer" in c.lower() or "countdown" in c.lower()),
        ):
            try:
                seconds = int(elem.get_text(strip=True))
                if 0 < seconds < 300:
                    return seconds
            except (ValueError, TypeError):
                pass

        patterns = [
            r"data-countdown=[\"'](\d+)[\"']",
            r"countdown:\s*(\d+)",
            r"(?:var|let|const)\s+countdown\s*=\s*(\d+)",
            r"countdownSeconds\s*=\s*(\d+)",
            r"[\"']countdown[_-]?seconds[\"']\s*:\s*(\d+)",
            r"wait\s+(\d+)\s+seconds",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_str, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

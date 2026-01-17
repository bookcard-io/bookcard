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

"""Resolver for Libgen URLs."""

import logging
import urllib.parse
from collections.abc import Callable
from typing import ClassVar

from bs4 import BeautifulSoup

from bookcard.pvr.base.interfaces import HttpClientProtocol

logger = logging.getLogger(__name__)


class LibgenResolver:
    """Resolver for Libgen URLs."""

    MIRRORS: ClassVar[list[str]] = [
        "https://libgen.li",
        "https://libgen.rs",
        "https://libgen.is",
        "https://libgen.st",
    ]

    def __init__(self, http_client_factory: Callable[[], HttpClientProtocol]) -> None:
        """Initialize Libgen resolver.

        Parameters
        ----------
        http_client_factory : Callable[[], HttpClientProtocol]
            Factory for creating HTTP clients.
        """
        self._http_client_factory = http_client_factory

    def resolve(self, md5: str) -> str | None:
        """Resolve Libgen download URL for an MD5.

        Parameters
        ----------
        md5 : str
            MD5 hash of the file.

        Returns
        -------
        str | None
            Direct download URL if found, None otherwise.
        """
        if not md5:
            return None

        # Try mirrors
        for mirror in self.MIRRORS:
            try:
                # Different mirrors use different URL structures
                # libgen.li uses ads.php?md5=...
                # others might use distinct structures, but ads.php is common for the download page
                url = f"{mirror}/ads.php?md5={md5}"
                logger.debug("Trying Libgen mirror: %s", url)

                with self._http_client_factory() as client:
                    try:
                        response = client.get(url, follow_redirects=True, timeout=10.0)
                    except (OSError, RuntimeError, ValueError) as e:
                        # Continue to next mirror on connection error
                        logger.debug(
                            "Connection error checking Libgen mirror %s: %s", mirror, e
                        )
                        continue

                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for the GET link
                    # Libgen.li style: <a href="get.php?md5=...">GET</a>
                    # Common pattern is a link containing "get.php"
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        text = a.get_text().strip().upper()
                        # Check for common download link patterns
                        if "get.php" in href or text == "GET":
                            # Ensure we have a full URL
                            download_url = urllib.parse.urljoin(mirror, href)
                            logger.info("Resolved Libgen URL: %s", download_url)
                            return download_url

            except (OSError, RuntimeError, ValueError) as e:
                logger.debug("Error checking Libgen mirror %s: %s", mirror, e)
                continue

        return None

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

"""Cover URL validator for DNB provider.

This module handles validation of cover image URLs from DNB,
following Single Responsibility Principle.
"""

from __future__ import annotations

import logging
from typing import ClassVar

import httpx

logger = logging.getLogger(__name__)


class CoverValidator:
    """Validator for DNB cover image URLs.

    This class is responsible solely for validating and retrieving
    cover image URLs from DNB's cover service.

    Attributes
    ----------
    COVER_BASE_URL : str
        Base URL for DNB cover service.
    VALID_IMAGE_TYPES : set[str]
        Set of valid image content types.
    """

    COVER_BASE_URL: ClassVar[str] = "https://portal.dnb.de/opac/mvb/cover"
    VALID_IMAGE_TYPES: ClassVar[set[str]] = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/bmp",
    }

    def __init__(self, timeout: int = 10) -> None:
        """Initialize cover validator.

        Parameters
        ----------
        timeout : int
            Request timeout in seconds.
        """
        self.timeout = timeout

    def get_cover_url(self, isbn: str | None) -> str | None:
        """Get validated cover URL for ISBN.

        Validates that the cover URL actually returns an image
        before returning it.

        Parameters
        ----------
        isbn : str | None
            ISBN identifier.

        Returns
        -------
        str | None
            Valid cover URL, or None if not available or invalid.
        """
        if not isbn:
            return None

        cover_url = f"{self.COVER_BASE_URL}?isbn={isbn}"

        try:
            response = httpx.head(
                cover_url, timeout=self.timeout, follow_redirects=True
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            # Extract main content type (remove charset and other parameters)
            main_content_type = content_type.split(";")[0].strip()

            if main_content_type in self.VALID_IMAGE_TYPES:
                return cover_url

            # If HTML response, try to extract image URL
            if "text/html" in content_type:
                return self._extract_image_from_html(cover_url)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug("DNB cover not found for ISBN: %s", isbn)
            else:
                logger.warning("DNB cover validation failed for ISBN %s: %s", isbn, e)
        except httpx.RequestError as e:
            logger.debug("DNB cover request failed for ISBN %s: %s", isbn, e)

        return None

    def _extract_image_from_html(self, url: str) -> str | None:
        """Extract image URL from HTML wrapper response.

        Some DNB cover URLs return HTML that wraps the actual image.
        This method attempts to extract the actual image URL.

        Parameters
        ----------
        url : str
            Cover URL that returned HTML.

        Returns
        -------
        str | None
            Extracted image URL, or None if extraction fails.
        """
        try:
            response = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()

            # Check if response is actually an image despite HTML content-type
            content = response.content
            if len(content) > 4 and content[:4] in (b"\xff\xd8\xff", b"\x89PNG"):
                return url

            # Try to parse HTML and extract image URL
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")
            img_tag = soup.find("img")
            if img_tag and img_tag.get("src"):
                img_src = img_tag["src"]
                # Make absolute URL if relative
                if img_src.startswith("/"):
                    from urllib.parse import urljoin

                    return urljoin(url, img_src)
                if img_src.startswith("http"):
                    return img_src

        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
            AttributeError,
            ValueError,
            KeyError,
        ) as e:
            logger.debug("Failed to extract image URL from HTML: %s", e)

        return None

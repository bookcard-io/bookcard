# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Google Books API metadata provider.

This provider fetches book metadata from the Google Books API.
Documentation: https://developers.google.com/books/docs/v1/using
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import (
    quote,  # noqa: F401 (kept for future query building enhancements)
)

import httpx

from fundamental.metadata.base import (
    MetadataProvider,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class GoogleBooksProvider(MetadataProvider):
    """Metadata provider for Google Books API.

    This provider uses the Google Books API v1 to search for books
    and retrieve metadata. It handles clean JSON API responses.
    """

    API_BASE_URL = "https://www.googleapis.com/books/v1"
    SEARCH_ENDPOINT = f"{API_BASE_URL}/volumes"
    BOOK_URL_BASE = "https://books.google.com/books?id="
    SOURCE_ID = "google"
    SOURCE_NAME = "Google Books"
    SOURCE_DESCRIPTION = "Google Books API"
    REQUEST_TIMEOUT = 10  # seconds

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize Google Books provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled.
        timeout : int
            Request timeout in seconds.
        """
        super().__init__(enabled)
        self.timeout = timeout

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about Google Books source.

        Returns
        -------
        MetadataSourceInfo
            Source information.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url="https://books.google.com/",
        )

    def search(
        self,
        query: str,
        locale: str = "en",
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books using Google Books API.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en').
        max_results : int
            Maximum number of results (default: 10).

        Returns
        -------
        Sequence[MetadataRecord]
            Sequence of metadata records.

        Raises
        ------
        MetadataProviderNetworkError
            If network request fails.
        MetadataProviderTimeoutError
            If request times out.
        MetadataProviderParseError
            If response cannot be parsed.
        """
        if not self.is_enabled():
            return []

        if not query or not query.strip():
            return []

        try:
            # Build search query
            search_query = self._build_search_query(query)
            params = {
                "q": search_query,
                "maxResults": min(max_results, 40),  # API limit is 40
                "langRestrict": locale,
            }

            # Make API request
            response = httpx.get(
                self.SEARCH_ENDPOINT,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            items = data.get("items", [])

            records = []
            for item in items[:max_results]:
                try:
                    record = self._parse_item(item)
                    if record:
                        records.append(record)
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    logger.warning("Failed to parse Google Books item: %s", e)
                    continue
        except httpx.TimeoutException as e:
            msg = f"Google Books API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"Google Books API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (KeyError, ValueError, TypeError) as e:
            msg = f"Failed to parse Google Books API response: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return records

    def _build_search_query(self, query: str) -> str:
        """Build search query from input string.

        Parameters
        ----------
        query : str
            Raw search query.

        Returns
        -------
        str
            Cleaned search query string (NOT URL-encoded).
        """
        # Let the HTTP client handle URL encoding via params; avoid double-encoding.
        # Future enhancement: add field qualifiers (intitle:, inauthor:) like calibre-web.
        return query.strip()

    def _parse_item(self, item: dict) -> MetadataRecord | None:
        """Parse a single item from Google Books API response.

        Parameters
        ----------
        item : dict
            Item data from API response.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            volume_info = item.get("volumeInfo", {})
            book_id = item.get("id", "")

            if not book_id:
                return None

            # volume_info might be missing, use empty dict as fallback
            volume_info = volume_info or {}

            # Extract basic info
            title = volume_info.get("title", "")

            # Require at least a title to create a meaningful record
            if not title:
                return None
            authors = volume_info.get("authors", [])
            description = volume_info.get("description", "")

            # Extract cover image
            cover_url = self._extract_cover_url(volume_info)

            # Extract identifiers (ISBN, etc.)
            identifiers = self._extract_identifiers(volume_info)

            # Extract series info
            series, series_index = self._extract_series_info(volume_info)

            # Extract other metadata
            publisher = volume_info.get("publisher")
            published_date = volume_info.get("publishedDate")
            rating = volume_info.get("averageRating")
            languages = volume_info.get("language", "")
            categories = volume_info.get("categories", [])

            # Build record
            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=book_id,
                title=title,
                authors=authors if isinstance(authors, list) else [],
                url=f"{self.BOOK_URL_BASE}{book_id}",
                cover_url=cover_url,
                description=description,
                series=series,
                series_index=series_index,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=float(rating) if rating is not None else None,
                languages=[languages]
                if languages and isinstance(languages, str)
                else [],
                tags=categories if isinstance(categories, list) else [],
            )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.warning("Error parsing Google Books item: %s", e)
            return None

    def _extract_cover_url(self, volume_info: dict) -> str | None:
        """Extract cover image URL from volume info.

        Parameters
        ----------
        volume_info : dict
            Volume information dictionary.

        Returns
        -------
        str | None
            Cover URL or None if not available.
        """
        image_links = volume_info.get("imageLinks", {})
        if not image_links:
            return None

        # Try thumbnail first, then small, then medium
        cover_url = (
            image_links.get("thumbnail")
            or image_links.get("small")
            or image_links.get("medium")
        )

        if not cover_url:
            return None

        # Remove edge curl parameter and request higher resolution
        cover_url = cover_url.replace("&edge=curl", "")
        if "&fife=" not in cover_url:
            cover_url += "&fife=w800-h900"

        # Ensure HTTPS
        return cover_url.replace("http://", "https://")

    def _extract_identifiers(self, volume_info: dict) -> dict[str, str]:
        """Extract identifiers (ISBN, etc.) from volume info.

        Parameters
        ----------
        volume_info : dict
            Volume information dictionary.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type -> value.
        """
        identifiers: dict[str, str] = {}

        industry_identifiers = volume_info.get("industryIdentifiers", [])
        for identifier in industry_identifiers:
            id_type = identifier.get("type", "").lower()
            id_value = identifier.get("identifier", "")
            if id_type and id_value:
                # Normalize identifier types
                if "isbn" in id_type:
                    identifiers["isbn"] = id_value
                else:
                    identifiers[id_type] = id_value

        return identifiers

    def _extract_series_info(
        self, _volume_info: dict
    ) -> tuple[str | None, float | None]:
        """Extract series information from volume info.

        Parameters
        ----------
        _volume_info : dict
            Volume information dictionary (unused, reserved for future use).

        Returns
        -------
        tuple[str | None, float | None]
            Tuple of (series name, series index).
        """
        # Google Books API doesn't directly provide series info
        # This would need to be extracted from title or other fields
        # For now, return None values
        return None, None

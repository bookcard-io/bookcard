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

"""ComicVine API metadata provider.

This provider fetches comic book metadata from the ComicVine API.
Documentation: https://comicvine.gamespot.com/api/documentation
"""

from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import quote

import httpx

from bookcard.metadata.base import (
    MetadataProvider,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class ComicVineProvider(MetadataProvider):
    """Metadata provider for ComicVine API.

    This provider uses the ComicVine API to search for comic book issues
    and retrieve metadata. It handles JSON API responses.
    """

    API_BASE_URL = "https://comicvine.gamespot.com/api"
    SEARCH_ENDPOINT = f"{API_BASE_URL}/search"
    BASE_URL = "https://comicvine.gamespot.com/"
    SOURCE_ID = "comicvine"
    SOURCE_NAME = "ComicVine"
    SOURCE_DESCRIPTION = "ComicVine Books"
    REQUEST_TIMEOUT = 15  # seconds

    # Users can override this by setting COMICVINE_API_KEY environment variable
    # or by modifying the provider initialization
    DEFAULT_API_KEY = os.getenv(
        "COMICVINE_API_KEY", "57558043c53943d5d1e96a9ad425b0eb85532ee6"
    ).strip()

    HEADERS: ClassVar[dict[str, str]] = {"User-Agent": "Not Evil Browser"}

    def __init__(
        self,
        enabled: bool = True,
        timeout: int = REQUEST_TIMEOUT,
        api_key: str | None = None,
    ) -> None:
        """Initialize ComicVine provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled.
        timeout : int
            Request timeout in seconds.
        api_key : str | None
            ComicVine API key. If None, uses default key.
        """
        super().__init__(enabled)
        self.timeout = timeout
        self.api_key = api_key or self.DEFAULT_API_KEY

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about ComicVine source.

        Returns
        -------
        MetadataSourceInfo
            Source information.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url=self.BASE_URL,
        )

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for comic books using ComicVine API.

        Parameters
        ----------
        query : str
            Search query (title, series, etc.).
        locale : str
            Locale code (default: 'en', currently not used by ComicVine API).
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
            # Tokenize and build query
            title_tokens = list(self._get_title_tokens(query, strip_joiners=False))
            if not title_tokens:
                return []

            # URL encode tokens and join with %20
            encoded_tokens = [quote(token.encode("utf-8")) for token in title_tokens]
            search_query = "%20".join(encoded_tokens)

            # Build API request parameters
            params = {
                "api_key": self.api_key,
                "resources": "issue",
                "query": search_query,
                "sort": "name:desc",
                "format": "json",
            }

            # Make API request
            with httpx.Client(
                headers=self.HEADERS, timeout=self.timeout, follow_redirects=True
            ) as client:
                response = client.get(self.SEARCH_ENDPOINT, params=params)
                response.raise_for_status()

                # Parse response
                data = response.json()
                results = data.get("results", [])

                records = []
                for result in results[:max_results]:
                    try:
                        record = self._parse_search_result(result)
                        if record:
                            records.append(record)
                    except (KeyError, ValueError, TypeError, AttributeError) as e:
                        logger.warning("Failed to parse ComicVine result: %s", e)
                        continue

                return records

        except httpx.TimeoutException as e:
            msg = f"ComicVine API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"ComicVine API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (KeyError, ValueError, TypeError) as e:
            msg = f"Failed to parse ComicVine API response: {e}"
            raise MetadataProviderParseError(msg) from e

    def _get_title_tokens(self, title: str, strip_joiners: bool = True) -> list[str]:
        """Extract tokens from title for better search matching.

        This is a simplified version of calibre's title tokenization.
        It removes common patterns and special characters to improve
        search query matching.

        Parameters
        ----------
        title : str
            Title to tokenize.
        strip_joiners : bool
            Whether to remove common joiners like "a", "and", "the", "&".

        Returns
        -------
        list[str]
            List of cleaned title tokens.
        """
        title_patterns = [
            (re.compile(pat, re.IGNORECASE), repl)
            for pat, repl in [
                # Remove things like: (2010) (Omnibus) etc.
                (
                    r"(?i)[({\[](\d{4}|omnibus|anthology|hardcover|"
                    r"audiobook|audio\scd|paperback|turtleback|"
                    r"mass\s*market|edition|ed\.)[\])}]",
                    "",
                ),
                # Remove any strings that contain the substring edition inside
                # parentheses
                (r"(?i)[({\[].*?(edition|ed.).*?[\]})]", ""),
                # Remove commas used as separators in numbers
                (r"(\d+),(\d+)", r"\1\2"),
                # Remove hyphens only if they have whitespace before them
                (r"(\s-)", " "),
                # Replace other special chars with a space
                (r"""[:,;!@$%^&*(){}.`~"\s\[\]/]《》「」""", " "),
            ]
        ]

        for pat, repl in title_patterns:
            title = pat.sub(repl, title)

        tokens = title.split()
        result = []
        for token in tokens:
            token = token.strip().strip('"').strip("'")
            if token and (
                not strip_joiners or token.lower() not in ("a", "and", "the", "&")
            ):
                result.append(token)

        return result

    def _parse_search_result(self, result: dict) -> MetadataRecord | None:
        """Parse a single search result from ComicVine API.

        Parameters
        ----------
        result : dict
            Result data from API response.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            issue_id = result.get("id")
            if not issue_id:
                return None

            series = self._extract_series(result)
            issue_number = result.get("issue_number", 0)
            issue_name = result.get("name", "")
            title = self._build_title(series, issue_number, issue_name)

            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=issue_id,
                title=title,
                authors=self._extract_authors(result),
                url=result.get("site_detail_url", ""),
                cover_url=self._extract_cover_url(result),
                description=result.get("description", ""),
                series=series if series else None,
                series_index=self._parse_series_index(issue_number),
                identifiers={"comicvine": str(issue_id)},
                publisher=None,  # ComicVine API doesn't provide publisher
                published_date=result.get("store_date") or result.get("date_added"),
                rating=None,  # ComicVine API doesn't provide rating
                languages=[],
                tags=self._build_tags(series),
            )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.warning("Error parsing ComicVine result: %s", e)
            return None

    def _extract_series(self, result: dict) -> str:
        """Extract series name from result.

        Parameters
        ----------
        result : dict
            Result data from API response.

        Returns
        -------
        str
            Series name, or empty string if not found.
        """
        volume = result.get("volume", {})
        if isinstance(volume, dict):
            return volume.get("name", "")
        return ""

    def _build_title(self, series: str, issue_number: float, issue_name: str) -> str:
        """Build title from series, issue number, and issue name.

        Parameters
        ----------
        series : str
            Series name.
        issue_number : int | float
            Issue number.
        issue_name : str
            Issue name.

        Returns
        -------
        str
            Formatted title.
        """
        if series and issue_number:
            return f"{series}#{issue_number} - {issue_name}"
        if series:
            return f"{series} - {issue_name}" if issue_name else series
        return issue_name or "Unknown"

    def _extract_authors(self, result: dict) -> list[str]:
        """Extract authors from result.

        Parameters
        ----------
        result : dict
            Result data from API response.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors = result.get("authors", [])
        if not isinstance(authors, list):
            return []

        author_list = []
        for author in authors:
            if isinstance(author, dict):
                author_name = author.get("name", "")
                if author_name:
                    author_list.append(author_name)
            elif isinstance(author, str):
                author_list.append(author)

        return author_list

    def _extract_cover_url(self, result: dict) -> str | None:
        """Extract cover image URL from result.

        Parameters
        ----------
        result : dict
            Result data from API response.

        Returns
        -------
        str | None
            Cover URL, or None if not found.
        """
        image = result.get("image", {})
        if isinstance(image, dict):
            return image.get("original_url") or image.get("super_url")
        return None

    def _parse_series_index(self, issue_number: float | None) -> float | None:
        """Parse issue number to series index.

        Parameters
        ----------
        issue_number : int | float | None
            Issue number from API.

        Returns
        -------
        float | None
            Series index as float, or None if invalid.
        """
        if not issue_number:
            return None
        try:
            return float(issue_number)
        except (ValueError, TypeError):
            return None

    def _build_tags(self, series: str) -> list[str]:
        """Build tags list from series.

        Parameters
        ----------
        series : str
            Series name.

        Returns
        -------
        list[str]
            List of tags.
        """
        tags = ["Comics"]
        if series:
            tags.append(series)
        return tags

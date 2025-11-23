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

"""OpenLibrary API metadata provider.

This provider fetches book metadata from the OpenLibrary API.
Documentation: https://openlibrary.org/developers/api
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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


class OpenLibraryProvider(MetadataProvider):
    """Metadata provider for OpenLibrary API.

    This provider uses the OpenLibrary API to search for books
    and retrieve metadata. It handles clean JSON API responses.
    """

    API_BASE_URL = "https://openlibrary.org"
    SEARCH_ENDPOINT = f"{API_BASE_URL}/search.json"
    WORK_URL_BASE = "https://openlibrary.org/works/"
    COVERS_BASE_URL = "https://covers.openlibrary.org"
    SOURCE_ID = "openlibrary"
    SOURCE_NAME = "OpenLibrary"
    SOURCE_DESCRIPTION = "OpenLibrary API"
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RESULTS_LIMIT = 100  # OpenLibrary API limit

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize OpenLibrary provider.

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
        """Get information about OpenLibrary source.

        Returns
        -------
        MetadataSourceInfo
            Source information.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url=self.API_BASE_URL,
        )

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books using OpenLibrary API.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en'). Note: OpenLibrary uses language codes
            like 'eng', but this parameter is kept for API consistency.
            Currently unused but reserved for future locale filtering.
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
                "limit": min(max_results, self.MAX_RESULTS_LIMIT),
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
            docs = data.get("docs", [])

            records = []
            for doc in docs[:max_results]:
                try:
                    record = self._parse_search_doc(doc)
                    if record:
                        records.append(record)
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    logger.warning("Failed to parse OpenLibrary search doc: %s", e)
                    continue
        except httpx.TimeoutException as e:
            msg = f"OpenLibrary API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"OpenLibrary API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (KeyError, ValueError, TypeError) as e:
            msg = f"Failed to parse OpenLibrary API response: {e}"
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
            Cleaned search query string.
        """
        # Let the HTTP client handle URL encoding via params
        return query.strip()

    def _parse_search_doc(self, doc: dict) -> MetadataRecord | None:
        """Parse a single document from OpenLibrary search response.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            # Extract work key
            work_key = doc.get("key", "")
            if not work_key:
                return None

            # Normalize key (remove /works/ or /books/ prefix)
            normalized_key = work_key.replace("/works/", "").replace("/books/", "")
            if not normalized_key:
                return None

            # Extract basic info
            title = doc.get("title", "")

            # Require at least a title to create a meaningful record
            if not title:
                return None

            # Extract authors
            authors = self._extract_authors(doc)

            # Extract description (may be in subtitle or abstract)
            description = doc.get("first_sentence")
            if isinstance(description, list) and description:
                description = (
                    description[0].get("value", "")
                    if isinstance(description[0], dict)
                    else str(description[0])
                )
            elif isinstance(description, dict):
                description = description.get("value", "")
            elif not isinstance(description, str):
                description = None

            # Extract cover image
            cover_url = self._extract_cover_url(doc)

            # Extract identifiers (ISBN, etc.)
            identifiers = self._extract_identifiers(doc)

            # Extract series info
            series, series_index = self._extract_series_info(doc)

            # Extract other metadata
            publisher = self._extract_publisher(doc)
            published_date = doc.get("first_publish_year")
            if published_date:
                published_date = str(published_date)

            # Extract languages
            languages = self._extract_languages(doc)

            # Extract tags/subjects
            tags = self._extract_tags(doc)

            # Build record
            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=normalized_key,
                title=title,
                authors=authors,
                url=f"{self.WORK_URL_BASE}{normalized_key}",
                cover_url=cover_url,
                description=description,
                series=series,
                series_index=series_index,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=None,  # OpenLibrary search doesn't provide ratings
                languages=languages,
                tags=tags,
            )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.warning("Error parsing OpenLibrary search doc: %s", e)
            return None

    def _extract_authors(self, doc: dict) -> list[str]:
        """Extract author names from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors = doc.get("author_name", [])
        if isinstance(authors, list):
            return [str(author) for author in authors if author]
        return []

    def _extract_cover_url(self, doc: dict) -> str | None:
        """Extract cover image URL from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        str | None
            Cover URL or None if not available.
        """
        cover_id = doc.get("cover_i")
        if cover_id and isinstance(cover_id, int):
            return f"{self.COVERS_BASE_URL}/b/id/{cover_id}-L.jpg"
        return None

    def _extract_identifiers(self, doc: dict) -> dict[str, str]:
        """Extract identifiers (ISBN, etc.) from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type -> value.
        """
        identifiers: dict[str, str] = {}

        # Extract ISBNs
        isbns = doc.get("isbn", [])
        if isinstance(isbns, list):
            for isbn in isbns:
                if isbn:
                    isbn_str = str(isbn).strip()
                    # Determine ISBN type by length
                    if len(isbn_str) == 10:
                        identifiers["isbn"] = isbn_str
                    elif len(isbn_str) == 13:
                        identifiers["isbn13"] = isbn_str
                    # Use first valid ISBN if type unclear
                    elif "isbn" not in identifiers:
                        identifiers["isbn"] = isbn_str

        # Extract other identifiers
        oclc = doc.get("oclc", [])
        if isinstance(oclc, list) and oclc:
            identifiers["oclc"] = str(oclc[0])

        lccn = doc.get("lccn", [])
        if isinstance(lccn, list) and lccn:
            identifiers["lccn"] = str(lccn[0])

        return identifiers

    def _extract_series_info(self, _doc: dict) -> tuple[str | None, float | None]:
        """Extract series information from document.

        Parameters
        ----------
        _doc : dict
            Document data from API response (unused, reserved for future use).

        Returns
        -------
        tuple[str | None, float | None]
            Tuple of (series name, series index).
        """
        # OpenLibrary search API doesn't directly provide series info
        # This would need to be extracted from title or fetched from work details
        # For now, return None values
        return None, None

    def _extract_publisher(self, doc: dict) -> str | None:
        """Extract publisher name from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        str | None
            Publisher name or None if not available.
        """
        publishers = doc.get("publisher", [])
        if isinstance(publishers, list) and publishers:
            return str(publishers[0])
        return None

    def _extract_languages(self, doc: dict) -> list[str]:
        """Extract language codes from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        list[str]
            List of language codes.
        """
        languages = doc.get("language", [])
        if isinstance(languages, list):
            return [str(lang) for lang in languages if lang]
        return []

    def _extract_tags(self, doc: dict) -> list[str]:
        """Extract tags/subjects from document.

        Parameters
        ----------
        doc : dict
            Document data from API response.

        Returns
        -------
        list[str]
            List of tags/subjects.
        """
        subjects = doc.get("subject", [])
        if isinstance(subjects, list):
            return [str(subject) for subject in subjects if subject]
        return []

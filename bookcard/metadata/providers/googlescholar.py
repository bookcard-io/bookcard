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

"""Google Scholar metadata provider.

This provider fetches academic publication metadata from Google Scholar
using the scholarly library. It searches for publications, papers, and books.
"""

from __future__ import annotations

import itertools
import logging
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote

try:
    from scholarly import scholarly  # type: ignore[import-untyped, import-not-found]
except ImportError:
    scholarly = None

from bookcard.metadata.base import (
    MetadataProvider,
    MetadataProviderError,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class GoogleScholarProvider(MetadataProvider):
    """Metadata provider for Google Scholar.

    This provider uses the scholarly library to search Google Scholar
    for academic publications, papers, and books. It extracts metadata
    from search results including title, authors, abstract, venue, and more.
    """

    BASE_URL = "https://scholar.google.com/"
    SOURCE_ID = "googlescholar"
    SOURCE_NAME = "Google Scholar"
    SOURCE_DESCRIPTION = "Google Scholar - Academic publications"
    REQUEST_TIMEOUT = 20  # seconds
    MAX_RETRIES = 2

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize Google Scholar provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled.
        timeout : int
            Request timeout in seconds.
        """
        super().__init__(enabled)
        self.timeout = timeout
        if scholarly is None:
            logger.warning(
                "scholarly library not available. Google Scholar provider will be disabled."
            )
            self.enabled = False

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about Google Scholar source.

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

    def is_enabled(self) -> bool:
        """Check if this provider is enabled.

        Returns
        -------
        bool
            True if provider is enabled and scholarly library is available.
        """
        return self.enabled and scholarly is not None

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for publications on Google Scholar.

        Parameters
        ----------
        query : str
            Search query (title, author, keywords, etc.).
        locale : str
            Locale code (not used by Google Scholar, kept for interface compatibility).
        max_results : int
            Maximum number of results (default: 10).

        Returns
        -------
        Sequence[MetadataRecord]
            Sequence of metadata records.

        Raises
        ------
        MetadataProviderError
            If scholarly library is not available.
        MetadataProviderNetworkError
            If network request fails.
        MetadataProviderParseError
            If response cannot be parsed.
        """
        if not self.is_enabled():
            return []

        if not query or not query.strip():
            return []

        if scholarly is None:
            msg = "scholarly library is not available"
            raise MetadataProviderError(msg)

        try:
            records = self._perform_search(query, max_results)
        except Exception as e:
            # scholarly library can raise various exceptions
            if isinstance(e, (TimeoutError, ConnectionError)):
                msg = f"Google Scholar search request failed: {e}"
                raise MetadataProviderNetworkError(msg) from e
            msg = f"Failed to parse Google Scholar search results: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return records

    def _perform_search(self, query: str, max_results: int) -> list[MetadataRecord]:
        """Perform the actual search and parse results.

        Parameters
        ----------
        query : str
            Search query.
        max_results : int
            Maximum number of results.

        Returns
        -------
        list[MetadataRecord]
            List of parsed metadata records.
        """
        # Prepare search query
        search_query = self._prepare_query(query)
        if not search_query:
            return []

        # At this point, scholarly is guaranteed to be not None
        # because search() checks this before calling _perform_search
        if scholarly is None:
            msg = "scholarly library is not available"
            raise MetadataProviderError(msg)

        # Configure scholarly
        scholarly.set_timeout(self.timeout)
        scholarly.set_retries(self.MAX_RETRIES)

        # Search publications
        scholar_gen = scholarly.search_pubs(search_query)
        results = itertools.islice(scholar_gen, max_results)

        records = []
        for result in results:
            try:
                record = self._parse_search_result(result)
                if record:
                    records.append(record)
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning("Failed to parse Google Scholar result: %s", e)
                continue

        return records

    def _prepare_query(self, query: str) -> str:
        """Prepare search query by tokenizing and URL-encoding.

        Parameters
        ----------
        query : str
            Raw search query.

        Returns
        -------
        str
            Prepared query string with tokens URL-encoded and joined.
        """
        # Simple tokenization - split on whitespace and filter short tokens
        title_tokens = [t for t in query.split() if len(t) > 1]

        if not title_tokens:
            return ""

        # URL-encode tokens and join with spaces
        tokens = [quote(t.encode("utf-8")) for t in title_tokens]
        return " ".join(tokens)

    def _parse_search_result(self, result: dict) -> MetadataRecord | None:
        """Parse a single search result from scholarly library.

        Parameters
        ----------
        result : dict
            Result dictionary from scholarly.search_pubs().

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            # Extract bib (bibliographic) information
            bib = result.get("bib", {})
            if not bib:
                return None

            title = bib.get("title")
            if not title:
                return None

            # Extract basic fields
            authors = self._extract_authors(bib)
            url, external_id = self._extract_urls(result)
            cover_url = self._extract_cover_url(result)
            description = self._extract_description(bib)
            publisher = bib.get("venue", "")
            published_date = self._extract_published_date(bib)
            identifiers = self._build_identifiers(external_id)
            tags = self._extract_tags(result)

            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=external_id or "unknown",
                title=title,
                authors=authors,
                url=url or self.BASE_URL,
                cover_url=cover_url,
                description=description,
                series=None,
                series_index=None,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=None,
                languages=[],
                tags=tags,
            )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.warning("Error parsing Google Scholar result: %s", e)
            return None

    def _extract_authors(self, bib: dict) -> list[str]:
        """Extract authors from bibliographic data.

        Parameters
        ----------
        bib : dict
            Bibliographic data dictionary.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors = bib.get("author", [])
        if isinstance(authors, str):
            # If author is a single string, split by comma or "and"
            authors = [
                a.strip()
                for a in authors.replace(" and ", ", ").split(",")
                if a.strip()
            ]
        return authors if isinstance(authors, list) else []

    def _extract_urls(self, result: dict) -> tuple[str, str]:
        """Extract URL and external ID from result.

        Parameters
        ----------
        result : dict
            Result dictionary.

        Returns
        -------
        tuple[str, str]
            Tuple of (url, external_id).
        """
        url = result.get("pub_url") or result.get("eprint_url") or ""
        if not url:
            # Generate a URL from the publication ID if available
            pub_id = result.get("pub_id")
            if pub_id:
                url = f"{self.BASE_URL}citations?view_op=view_citation&hl=en&user={pub_id}"

        external_id = url or result.get("pub_id", "")
        return url, external_id

    def _extract_cover_url(self, result: dict) -> str | None:
        """Extract cover image URL from result.

        Parameters
        ----------
        result : dict
            Result dictionary.

        Returns
        -------
        str | None
            Cover image URL, or None if not found.
        """
        image_data = result.get("image", {})
        if isinstance(image_data, dict):
            return image_data.get("original_url")
        return None

    def _extract_description(self, bib: dict) -> str:
        """Extract description (abstract) from bibliographic data.

        Parameters
        ----------
        bib : dict
            Bibliographic data dictionary.

        Returns
        -------
        str
            Description text.
        """
        description = bib.get("abstract", "")
        if description:
            # Unquote URL-encoded abstract
            description = unquote(description)
        return description

    def _extract_published_date(self, bib: dict) -> str | None:
        """Extract published date from bibliographic data.

        Parameters
        ----------
        bib : dict
            Bibliographic data dictionary.

        Returns
        -------
        str | None
            Published date string (YYYY-01-01 format), or None.
        """
        pub_year = bib.get("pub_year")
        if pub_year:
            # Format as YYYY-01-01 since we only have the year
            return f"{pub_year}-01-01"
        return None

    def _build_identifiers(self, external_id: str) -> dict[str, str]:
        """Build identifiers dictionary.

        Parameters
        ----------
        external_id : str
            External identifier.

        Returns
        -------
        dict[str, str]
            Identifiers dictionary.
        """
        identifiers: dict[str, str] = {}
        if external_id:
            identifiers["scholar"] = external_id
        return identifiers

    def _extract_tags(self, result: dict) -> list[str]:
        """Extract tags from result (citation count).

        Parameters
        ----------
        result : dict
            Result dictionary.

        Returns
        -------
        list[str]
            List of tags.
        """
        citation_count = result.get("num_citations", 0)
        if citation_count and citation_count > 0:
            return [f"Citations: {citation_count}"]
        return []

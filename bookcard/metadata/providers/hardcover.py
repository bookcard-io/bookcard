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

"""Hardcover API metadata provider.

This provider fetches book metadata from the Hardcover GraphQL API.
Documentation: https://docs.hardcover.app/api/graphql/
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

from bookcard.metadata.base import (
    MetadataProvider,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.metadata.providers._hardcover.client import (
    HardcoverGraphQLClient,
    HttpClient,
)
from bookcard.metadata.providers._hardcover.enrichment import (
    HardcoverEnrichment,
)
from bookcard.metadata.providers._hardcover.mapper import HardcoverBookMapper
from bookcard.metadata.providers._hardcover.parser import (
    HardcoverResponseParser,
)
from bookcard.metadata.providers._hardcover.queries import (
    EDITION_OPERATION_NAME,
    EDITION_QUERY,
    SEARCH_OPERATION_NAME,
    SEARCH_QUERY,
)
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class HardcoverProvider(MetadataProvider):
    """Metadata provider for Hardcover GraphQL API.

    This provider orchestrates the search, enrichment, and mapping
    of book metadata from the Hardcover GraphQL API.
    """

    API_BASE_URL = "https://api.hardcover.app/v1"
    GRAPHQL_ENDPOINT = f"{API_BASE_URL}/graphql"
    SOURCE_ID = "hardcover"
    SOURCE_NAME = "Hardcover"
    SOURCE_DESCRIPTION = "Hardcover GraphQL API"
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RESULTS_LIMIT = 50  # Reasonable limit for GraphQL queries

    # Users can override this by setting HARDCOVER_API_TOKEN environment variable
    # or by modifying the provider initialization
    DEFAULT_BEARER_TOKEN = os.getenv("HARDCOVER_API_TOKEN", "").strip()

    def __init__(
        self,
        enabled: bool = True,
        timeout: int = REQUEST_TIMEOUT,
        bearer_token: str | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize Hardcover provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled. Will be automatically
            set to False if no bearer token is available.
        timeout : int
            Request timeout in seconds.
        bearer_token : str | None
            Hardcover API bearer token. If None, uses token from
            HARDCOVER_API_TOKEN environment variable.
        http_client : HttpClient | None
            HTTP client to use. If None, uses httpx directly.
        """
        self.timeout = timeout
        self.bearer_token = bearer_token or self.DEFAULT_BEARER_TOKEN

        # Automatically disable if no bearer token is provided
        if not self.bearer_token:
            if enabled:
                logger.warning(
                    "Hardcover provider disabled: HARDCOVER_API_TOKEN environment variable not set"
                )
            enabled = False

        super().__init__(enabled)

        # Initialize components with dependency injection
        self._client = HardcoverGraphQLClient(
            endpoint=self.GRAPHQL_ENDPOINT,
            bearer_token=self.bearer_token,
            timeout=self.timeout,
            http_client=http_client,
        )
        self._parser = HardcoverResponseParser()
        self._mapper = HardcoverBookMapper()
        self._enrichment = HardcoverEnrichment()

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about Hardcover source.

        Returns
        -------
        MetadataSourceInfo
            Source information.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url="https://hardcover.app",
        )

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books using Hardcover GraphQL API.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en'). Currently unused but reserved
            for future locale filtering.
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
            # Execute search query
            data = self._client.execute_query(
                query=SEARCH_QUERY,
                variables={"query": query},
                operation_name=SEARCH_OPERATION_NAME,
            )

            # Parse search results
            results_data = self._parser.extract_search_data(data)
            books_data = self._parser.parse_search_results(results_data)

            if not books_data:
                return []

            # Enrich with edition details
            enriched_books_data = self._enrich_books_with_editions(
                books_data[:max_results]
            )

            # Map to MetadataRecord objects
            result = self._map_books_to_records(enriched_books_data)
        except httpx.TimeoutException as e:
            msg = f"Hardcover API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"Hardcover API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (KeyError, ValueError, TypeError) as e:
            msg = f"Failed to parse Hardcover API response: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return result

    def _enrich_books_with_editions(self, books_data: list[dict]) -> list[dict]:
        """Enrich book data with detailed edition information.

        Parameters
        ----------
        books_data : list[dict]
            List of book data from search results.

        Returns
        -------
        list[dict]
            List of enriched book data.
        """
        enriched_books_data = []
        for book_data in books_data:
            book_id = book_data.get("id")
            if book_id:
                edition_data = self._fetch_edition_details(book_id)
                if edition_data:
                    enriched_book = self._enrichment.merge_book_with_editions(
                        book_data, edition_data
                    )
                    enriched_books_data.append(enriched_book)
                else:
                    enriched_books_data.append(book_data)
            else:
                enriched_books_data.append(book_data)
        return enriched_books_data

    def _fetch_edition_details(self, book_id: int | str) -> dict | None:
        """Fetch detailed edition information for a book.

        Parameters
        ----------
        book_id : int | str
            Hardcover book ID.

        Returns
        -------
        dict | None
            Book data with edition details, or None if fetch fails.
        """
        try:
            book_id_int = int(book_id)
            data = self._client.execute_query(
                query=EDITION_QUERY,
                variables={"bookId": book_id_int},
                operation_name=EDITION_OPERATION_NAME,
            )
            return self._parser.extract_edition_data(data)
        except (
            ValueError,
            TypeError,
            KeyError,
            MetadataProviderParseError,
            MetadataProviderNetworkError,
        ) as e:
            logger.warning(
                "Failed to fetch edition details for book ID %s: %s", book_id, e
            )
        return None

    def _map_books_to_records(self, books_data: list[dict]) -> list[MetadataRecord]:
        """Map list of book data to MetadataRecord objects.

        Parameters
        ----------
        books_data : list[dict]
            List of book data dictionaries.

        Returns
        -------
        list[MetadataRecord]
            List of parsed metadata records.
        """
        records = []
        for book_data in books_data:
            record = self._mapper.map_to_record(book_data)
            if record:
                records.append(record)
        return records

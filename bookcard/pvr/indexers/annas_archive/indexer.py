# Copyright (C) 2026 knguyen and others
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

"""Anna's Archive indexer implementation."""

import logging
from collections.abc import Sequence

import httpx

from bookcard.pvr.base import BaseIndexer, IndexerSettings
from bookcard.pvr.exceptions import PVRProviderNetworkError
from bookcard.pvr.indexers.annas_archive.builders import (
    AnnasArchiveUrlBuilder,
    SearchParametersBuilder,
    SearchQueryBuilder,
)
from bookcard.pvr.indexers.annas_archive.cache import SearchCache
from bookcard.pvr.indexers.annas_archive.exceptions import AnnasArchiveSearchError
from bookcard.pvr.indexers.annas_archive.network import (
    HttpClient,
    HttpxClientAdapter,
    RetryStrategy,
)
from bookcard.pvr.indexers.annas_archive.parser import AnnasArchiveHtmlParser
from bookcard.pvr.indexers.annas_archive.settings import AnnasArchiveSettings
from bookcard.pvr.indexers.annas_archive.validators import SearchValidator
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class AnnasArchiveIndexer(BaseIndexer):
    """Indexer for Anna's Archive."""

    def __init__(
        self,
        settings: AnnasArchiveSettings | IndexerSettings,
        http_client: HttpClient | None = None,
        html_parser: AnnasArchiveHtmlParser | None = None,
        query_builder: SearchQueryBuilder | None = None,
        params_builder: SearchParametersBuilder | None = None,
        url_builder: AnnasArchiveUrlBuilder | None = None,
        validator: SearchValidator | None = None,
        cache: SearchCache | None = None,
        retry_strategy: RetryStrategy | None = None,
    ) -> None:
        """Initialize Anna's Archive indexer."""
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, AnnasArchiveSettings
        ):
            # Convert generic settings to specific settings
            settings = AnnasArchiveSettings(
                base_url=settings.base_url or "https://annas-archive.org",
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
            )

        super().__init__(settings)
        self.settings: AnnasArchiveSettings = settings

        self._http_client = http_client or HttpxClientAdapter(
            timeout=settings.timeout_seconds
        )
        self._html_parser = html_parser or AnnasArchiveHtmlParser()
        self._query_builder = query_builder or SearchQueryBuilder()
        self._params_builder = params_builder or SearchParametersBuilder()
        self._url_builder = url_builder or AnnasArchiveUrlBuilder(settings.base_url)
        self._validator = validator or SearchValidator()
        self._cache = cache or SearchCache()
        self._retry_strategy = retry_strategy or RetryStrategy(
            max_retries=settings.retry_count
        )

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
        page: int = 1,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases matching the query."""
        # Validate inputs
        max_results = self._validator.validate_max_results(max_results)
        if isbn:
            isbn = self._validator.validate_isbn(isbn)

        # Build search term
        search_term = self._query_builder.build(query, title, author, isbn)
        if not search_term:
            logger.info("No search term provided, returning empty results")
            return []

        self._validator.validate_query_length(search_term)

        # Check cache
        cache_key = SearchCache.make_cache_key(
            query, title, author, isbn, max_results, page
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for search: %s", cache_key[:16])
            return cached

        # Execute search with retry
        try:
            results = self._retry_strategy.execute(
                lambda: self._execute_search(search_term, max_results, page),
                retryable_exceptions=(
                    PVRProviderNetworkError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.ReadTimeout,
                ),
            )

            # Cache results
            self._cache.set(cache_key, list(results))
        except PVRProviderNetworkError:
            # Network errors are already wrapped/typed, re-raise
            raise
        except Exception as e:
            # Wrap other unexpected errors
            logger.exception("Search failed for %s", search_term)
            msg = f"Search failed for '{search_term}': {e}"
            raise AnnasArchiveSearchError(msg) from e
        else:
            return results

    def _execute_search(
        self, search_term: str, max_results: int, page: int
    ) -> list[ReleaseInfo]:
        """Execute the actual search request."""
        params = self._params_builder.build(search_term, page=page)
        url = self._url_builder.search_url()

        try:
            response = self._http_client.get(url, params=params.to_dict())
        except Exception as e:
            # If http_client raises something other than PVRProviderNetworkError (e.g. mock),
            # we might want to catch it, but HttpClient protocol implies it handles its own.
            # However, HttpxClientAdapter raises PVRProviderNetworkError.
            # If raw httpx error escapes:
            if isinstance(e, httpx.HTTPError):
                msg = f"HTTP Error: {e}"
                raise PVRProviderNetworkError(msg) from e
            raise

        return self._html_parser.parse_search_results(
            response.text,
            max_results,
            self.settings.base_url,
        )

    def search_all_pages(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
        max_pages: int = 10,
    ) -> Sequence[ReleaseInfo]:
        """Search multiple pages until max_results reached."""
        all_releases: list[ReleaseInfo] = []
        page = 1

        while len(all_releases) < max_results and page <= max_pages:
            page_results = self.search(
                query=query,
                title=title,
                author=author,
                isbn=isbn,
                max_results=max_results - len(all_releases),
                page=page,
            )

            if not page_results:
                break

            all_releases.extend(page_results)
            page += 1

        return all_releases[:max_results]

    def test_connection(self) -> bool:
        """Test connectivity and search functionality."""
        try:
            # Test 1: Base URL accessible
            self._http_client.get(self.settings.base_url)

            # Test 2: Search functionality works
            # We use a simple query that should return results or at least a valid page
            test_params = self._params_builder.build("test")
            url = self._url_builder.search_url()
            response = self._http_client.get(url, params=test_params.to_dict())

            # Test 3: Can parse results (even if empty)
            self._html_parser.parse_search_results(
                response.text,
                max_results=1,
                base_url=self.settings.base_url,
            )
        except Exception:
            logger.exception("Connection test failed")
            return False
        else:
            return True

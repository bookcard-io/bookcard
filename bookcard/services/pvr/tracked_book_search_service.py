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

"""Service for tracked book search operations.

Orchestrates search, result caching, and download initiation for tracked books.
"""

import logging
from datetime import UTC, datetime
from typing import NoReturn

from sqlmodel import Session

from bookcard.api.schemas.pvr_search import (
    PVRDownloadResponse,
    PVRSearchResponse,
    PVRSearchResultsResponse,
    ReleaseInfoRead,
    SearchResultRead,
)
from bookcard.models.pvr import (
    DownloadClientDefinition,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.services.download.repository import SQLModelDownloadItemRepository
from bookcard.services.download_client_service import DownloadClientService
from bookcard.services.download_service import DownloadService
from bookcard.services.pvr.exceptions import (
    DownloadInitiationError,
    TrackedBookSearchError,
)
from bookcard.services.pvr.search.cache import SearchResultsCache
from bookcard.services.pvr.search.matcher import DownloadItemMatcher
from bookcard.services.pvr.search.models import IndexerSearchResult
from bookcard.services.pvr.search.service import IndexerSearchService
from bookcard.services.tracked_book_service import TrackedBookService

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS_PER_INDEXER = 100

# Global cache instance to maintain state across service instances
_GLOBAL_SEARCH_CACHE = SearchResultsCache()


class TrackedBookSearchService:
    """Service for tracked book search operations."""

    def __init__(
        self,
        session: Session,
        tracked_book_service: TrackedBookService,
        indexer_search_service: IndexerSearchService,
        download_service: DownloadService,
        download_client_service: DownloadClientService,
        results_cache: SearchResultsCache = _GLOBAL_SEARCH_CACHE,
        matcher: DownloadItemMatcher | None = None,
    ) -> None:
        """Initialize service.

        Parameters
        ----------
        session : Session
            Database session.
        tracked_book_service : TrackedBookService
            Tracked book service.
        indexer_search_service : IndexerSearchService
            Indexer search service.
        download_service : DownloadService
            Download service.
        download_client_service : DownloadClientService
            Download client service.
        results_cache : SearchResultsCache
            Search results cache.
        matcher : DownloadItemMatcher | None
            Download item matcher.
        """
        self._session = session
        self._tracked_book_service = tracked_book_service
        self._indexer_search_service = indexer_search_service
        self._download_service = download_service
        self._download_client_service = download_client_service
        self._results_cache = results_cache
        self._matcher = matcher or DownloadItemMatcher()

    def search_tracked_book(
        self,
        tracked_book_id: int,
        max_results_per_indexer: int = DEFAULT_MAX_RESULTS_PER_INDEXER,
        indexer_ids: list[int] | None = None,
    ) -> PVRSearchResponse:
        """Initiate search for a tracked book.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        max_results_per_indexer : int
            Maximum results per indexer.
        indexer_ids : list[int] | None
            Specific indexer IDs to search.

        Returns
        -------
        PVRSearchResponse
            Search initiation response.

        Raises
        ------
        ValueError
            If tracked book not found or query is empty.
        TrackedBookSearchError
            If search fails.
        """
        book = self._get_tracked_book_or_raise(tracked_book_id)

        query = f"{book.title} {book.author}".strip()
        if not query:
            msg = "Tracked book must have title or author"
            raise ValueError(msg)

        try:
            results = self._indexer_search_service.search_all_indexers(
                query=query,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                max_results_per_indexer=max_results_per_indexer,
                indexer_ids=indexer_ids,
            )

            # Store results in cache
            self._results_cache.store(tracked_book_id, results)

            # Update tracked book
            self._tracked_book_service.update_search_status(
                tracked_book_id, datetime.now(UTC), TrackedBookStatus.SEARCHING
            )

            logger.info(
                "Search initiated",
                extra={
                    "tracked_book_id": tracked_book_id,
                    "book_title": book.title,
                    "results_count": len(results),
                    "indexer_count": len(indexer_ids) if indexer_ids else "all",
                },
            )

            return PVRSearchResponse(
                tracked_book_id=tracked_book_id,
                search_initiated=True,
                message=f"Search completed: {len(results)} results found",
            )

        except Exception as e:
            logger.exception("Failed to search for tracked book %d", tracked_book_id)
            msg = f"Search failed: {e}"
            raise TrackedBookSearchError(msg) from e

    def get_search_results(self, tracked_book_id: int) -> PVRSearchResultsResponse:
        """Get cached search results for a tracked book.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.

        Returns
        -------
        PVRSearchResultsResponse
            Search results response.

        Raises
        ------
        ValueError
            If tracked book not found.
        SearchResultsNotFoundError
            If no results in cache.
        """
        self._get_tracked_book_or_raise(tracked_book_id)

        results = self._get_cached_results_or_raise(tracked_book_id)

        # Fetch existing downloads for this book to populate download status
        download_item_repo = SQLModelDownloadItemRepository(self._session)
        existing_downloads = download_item_repo.get_by_tracked_book(tracked_book_id)

        maps = self._matcher.build_lookup_maps(existing_downloads)

        search_results = []
        for result in results:
            download_item = self._matcher.find_match(result, maps)

            search_results.append(
                SearchResultRead(
                    release=ReleaseInfoRead.from_release_info(result.release),
                    score=result.score,
                    indexer_name=result.indexer_name,
                    indexer_priority=result.indexer_priority,
                    indexer_protocol=result.indexer_protocol,
                    download_status=download_item.status if download_item else None,
                    download_item_id=download_item.id if download_item else None,
                )
            )

        return PVRSearchResultsResponse(
            tracked_book_id=tracked_book_id,
            results=search_results,
            total=len(search_results),
        )

    def trigger_download(
        self,
        tracked_book_id: int,
        release_index: int,
        download_client_id: int | None = None,
    ) -> PVRDownloadResponse:
        """Trigger download for a specific release from search results.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        release_index : int
            Index of the release in cached results.
        download_client_id : int | None
            Optional download client ID.

        Returns
        -------
        PVRDownloadResponse
            Download initiation response.

        Raises
        ------
        ValueError
            If tracked book not found, results not found, index invalid,
            or download client not found.
        DownloadInitiationError
            If download initiation fails.
        """
        book = self._get_tracked_book_or_raise(tracked_book_id)

        results = self._get_cached_results_or_raise(tracked_book_id)

        if release_index >= len(results):
            msg = (
                f"Invalid release index {release_index}. "
                f"Only {len(results)} results available."
            )
            raise ValueError(msg)

        selected_result = results[release_index]
        release = selected_result.release

        try:
            download_client = self._get_download_client_or_none(
                download_client_id, self._download_client_service
            )

            download_item = self._download_service.initiate_download(
                release=release,
                tracked_book=book,
                client=download_client,
            )

            logger.info(
                "Download initiated",
                extra={
                    "tracked_book_id": tracked_book_id,
                    "release_title": release.title,
                    "download_item_id": download_item.id,
                },
            )

            return PVRDownloadResponse(
                tracked_book_id=tracked_book_id,
                download_item_id=download_item.id or 0,
                release_title=release.title,
                message=f"Download initiated for '{release.title}'",
            )

        except ValueError:
            raise
        except PVRProviderError as e:
            msg = f"Download failed: {e}"
            raise DownloadInitiationError(msg) from e
        except Exception as e:
            logger.exception(
                "Failed to initiate download for tracked book %d", tracked_book_id
            )
            msg = f"Download failed: {e}"
            raise DownloadInitiationError(msg) from e

    def _get_tracked_book_or_raise(self, tracked_book_id: int) -> TrackedBook:
        book = self._tracked_book_service.get_tracked_book(tracked_book_id)
        if book is None:
            msg = f"Tracked book {tracked_book_id} not found"
            raise ValueError(msg)
        return book

    def _get_cached_results_or_raise(
        self, tracked_book_id: int
    ) -> list[IndexerSearchResult]:
        results = self._results_cache.get(tracked_book_id)

        if results is None:
            msg = (
                f"No search results available for tracked book {tracked_book_id}. "
                "Please initiate a search first."
            )
            raise ValueError(msg)

        return results

    def _get_download_client_or_none(
        self,
        download_client_id: int | None,
        download_client_service: DownloadClientService | None,
    ) -> DownloadClientDefinition | None:
        if not download_client_id:
            return None

        if not download_client_service:
            # Should not happen if injected correctly
            msg = "DownloadClientService required when download_client_id provided"
            raise ValueError(msg)

        client = download_client_service.get_decrypted_download_client(
            download_client_id
        )
        if client is None:
            self._raise_client_not_found(download_client_id)

        return client

    def _raise_client_not_found(self, client_id: int) -> NoReturn:
        msg = f"Download client {client_id} not found"
        raise ValueError(msg)

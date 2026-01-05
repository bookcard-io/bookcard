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

"""Tests for TrackedBookSearchService."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from sqlmodel import Session

from bookcard.api.schemas.pvr_search import (
    PVRDownloadResponse,
    PVRSearchResponse,
    PVRSearchResultsResponse,
)
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.cache import SearchResultsCache
from bookcard.services.pvr.search.models import IndexerSearchResult
from bookcard.services.pvr.tracked_book_search_service import (
    TrackedBookSearchService,
)


@pytest.fixture
def tracked_book() -> TrackedBook:
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        library_id=1,
        metadata_source_id="google",
        metadata_external_id="123",
        status=TrackedBookStatus.WANTED,
        auto_search_enabled=True,
        auto_download_enabled=False,
        preferred_formats=["epub"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def release_info() -> ReleaseInfo:
    return ReleaseInfo(
        indexer_id=1,
        title="Test Book - EPUB",
        download_url="magnet:?xt=urn:btih:test123",
        size_bytes=1024000,
        publish_date=datetime.now(UTC),
        seeders=10,
        leechers=2,
        quality="epub",
        author="Test Author",
        isbn="1234567890",
        description="Test book release",
        category="Books",
    )


@pytest.fixture
def indexer_search_result(release_info: ReleaseInfo) -> IndexerSearchResult:
    return IndexerSearchResult(
        release=release_info,
        score=0.95,
        indexer_name="Test Indexer",
        indexer_priority=0,
    )


@pytest.fixture
def download_item() -> DownloadItem:
    return DownloadItem(
        id=1,
        tracked_book_id=1,
        download_client_id=1,
        indexer_id=1,
        client_item_id="client-123",
        guid="test-guid-123",
        title="Test Book - EPUB",
        download_url="magnet:?xt=urn:btih:test123",
        status=DownloadItemStatus.QUEUED,
        progress=0.0,
        size_bytes=1024000,
        quality="epub",
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def download_client() -> DownloadClientDefinition:
    from bookcard.models.pvr import DownloadClientType

    return DownloadClientDefinition(
        id=1,
        name="Test qBittorrent",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        username="admin",
        password="password",
        use_ssl=False,
        enabled=True,
        priority=0,
    )


class TestTrackedBookSearchService:
    @pytest.fixture
    def service(self, session: Session) -> TrackedBookSearchService:
        tracked_book_service = MagicMock()
        indexer_search_service = MagicMock()
        download_service = MagicMock()
        download_client_service = MagicMock()
        results_cache = SearchResultsCache()

        return TrackedBookSearchService(
            session=session,
            tracked_book_service=tracked_book_service,
            indexer_search_service=indexer_search_service,
            download_service=download_service,
            download_client_service=download_client_service,
            results_cache=results_cache,
        )

    def test_search_tracked_book_success(
        self,
        service: TrackedBookSearchService,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
    ) -> None:
        mock_tracked_service = cast("MagicMock", service._tracked_book_service)
        mock_tracked_service.get_tracked_book.return_value = tracked_book

        mock_indexer_service = cast("MagicMock", service._indexer_search_service)
        mock_indexer_service.search_all_indexers.return_value = [indexer_search_result]

        result = service.search_tracked_book(
            tracked_book_id=1,
            max_results_per_indexer=100,
        )

        assert isinstance(result, PVRSearchResponse)
        assert result.tracked_book_id == 1
        assert result.search_initiated is True
        mock_tracked_service.get_tracked_book.assert_called_once_with(1)
        mock_indexer_service.search_all_indexers.assert_called_once()

        # Verify cache
        assert service._results_cache.get(1) == [indexer_search_result]

    def test_search_tracked_book_not_found(
        self,
        service: TrackedBookSearchService,
    ) -> None:
        mock_tracked_service = cast("MagicMock", service._tracked_book_service)
        mock_tracked_service.get_tracked_book.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.search_tracked_book(tracked_book_id=999)

    def test_get_search_results_success(
        self,
        service: TrackedBookSearchService,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        download_item: DownloadItem,
    ) -> None:
        mock_tracked_service = cast("MagicMock", service._tracked_book_service)
        mock_tracked_service.get_tracked_book.return_value = tracked_book

        # Mock download item repo
        mock_repo = MagicMock()
        mock_repo.get_by_tracked_book.return_value = [download_item]

        # Populate cache
        service._results_cache.store(1, [indexer_search_result])

        # Patch SQLModelDownloadItemRepository
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "bookcard.services.pvr.tracked_book_search_service.SQLModelDownloadItemRepository",
                lambda s: mock_repo,
            )

            result = service.get_search_results(tracked_book_id=1)

        assert isinstance(result, PVRSearchResultsResponse)
        assert len(result.results) == 1
        assert result.results[0].download_item_id == download_item.id

    def test_trigger_download_success(
        self,
        service: TrackedBookSearchService,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        download_item: DownloadItem,
    ) -> None:
        mock_tracked_service = cast("MagicMock", service._tracked_book_service)
        mock_tracked_service.get_tracked_book.return_value = tracked_book

        mock_download_service = cast("MagicMock", service._download_service)
        mock_download_service.initiate_download.return_value = download_item

        # Populate cache
        service._results_cache.store(1, [indexer_search_result])

        result = service.trigger_download(
            tracked_book_id=1,
            release_index=0,
        )

        assert isinstance(result, PVRDownloadResponse)
        assert result.download_item_id == download_item.id
        mock_download_service.initiate_download.assert_called_once()

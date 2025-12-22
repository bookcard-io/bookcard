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

"""Shared fixtures for PVR tests."""

from typing import TYPE_CHECKING

import pytest

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientType,
    IndexerDefinition,
    IndexerProtocol,
    IndexerType,
)
from bookcard.pvr.base import (
    BaseDownloadClient,
    BaseIndexer,
    DownloadClientSettings,
    IndexerSettings,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bookcard.pvr.models import ReleaseInfo


# ============================================================================
# Settings Fixtures
# ============================================================================


@pytest.fixture
def indexer_settings() -> IndexerSettings:
    """Create basic indexer settings."""
    return IndexerSettings(
        base_url="https://indexer.example.com",
        api_key="test-api-key",
        timeout_seconds=30,
        retry_count=3,
        categories=[1000, 2000],
    )


@pytest.fixture
def indexer_settings_minimal() -> IndexerSettings:
    """Create minimal indexer settings."""
    return IndexerSettings(base_url="https://indexer.example.com")


@pytest.fixture
def download_client_settings() -> DownloadClientSettings:
    """Create basic download client settings."""
    return DownloadClientSettings(
        host="localhost",
        port=8080,
        username="admin",
        password="secret",
        use_ssl=False,
        timeout_seconds=30,
        category="bookcard",
        download_path="/downloads",
    )


@pytest.fixture
def download_client_settings_minimal() -> DownloadClientSettings:
    """Create minimal download client settings."""
    return DownloadClientSettings(host="localhost", port=8080)


# ============================================================================
# Mock Provider Fixtures
# ============================================================================


class MockIndexer(BaseIndexer):
    """Mock indexer implementation for testing."""

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> "Sequence[ReleaseInfo]":
        """Mock search implementation."""
        from bookcard.pvr.models import ReleaseInfo

        return [
            ReleaseInfo(
                title=f"Result for {query}",
                download_url="https://example.com/torrent.torrent",
            )
        ]

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True


class MockDownloadClient(BaseDownloadClient):
    """Mock download client implementation for testing."""

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Mock add download implementation."""
        return "mock-item-id-123"

    def get_items(self) -> "Sequence[dict[str, str | int | float | None]]":
        """Mock get items implementation."""
        return [
            {
                "client_item_id": "item-1",
                "title": "Test Download",
                "status": "downloading",
                "progress": 0.5,
                "size_bytes": 1000000,
                "downloaded_bytes": 500000,
                "download_speed_bytes_per_sec": 100000.0,
                "eta_seconds": 5,
                "file_path": None,
            }
        ]

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Mock remove item implementation."""
        return True

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True


@pytest.fixture
def mock_indexer(indexer_settings: IndexerSettings) -> MockIndexer:
    """Create a mock indexer instance."""
    return MockIndexer(settings=indexer_settings, enabled=True)


@pytest.fixture
def mock_download_client(
    download_client_settings: DownloadClientSettings,
) -> MockDownloadClient:
    """Create a mock download client instance."""
    return MockDownloadClient(settings=download_client_settings, enabled=True)


# ============================================================================
# Database Model Fixtures
# ============================================================================


@pytest.fixture
def indexer_definition() -> IndexerDefinition:
    """Create an indexer definition for testing."""
    return IndexerDefinition(
        id=1,
        name="Test Indexer",
        indexer_type=IndexerType.TORZNAB,
        protocol=IndexerProtocol.TORRENT,
        base_url="https://indexer.example.com",
        api_key="test-api-key",
        enabled=True,
        priority=0,
        timeout_seconds=30,
        retry_count=3,
        categories=[1000, 2000],
    )


@pytest.fixture
def download_client_definition() -> DownloadClientDefinition:
    """Create a download client definition for testing."""
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        username="admin",
        password="secret",
        enabled=True,
        priority=0,
    )


# ============================================================================
# Parametrized Fixtures
# ============================================================================


@pytest.fixture(
    params=[
        (IndexerType.TORZNAB, IndexerProtocol.TORRENT),
        (IndexerType.NEWZNAB, IndexerProtocol.USENET),
        (IndexerType.TORRENT_RSS, IndexerProtocol.TORRENT),
        (IndexerType.USENET_RSS, IndexerProtocol.USENET),
        (IndexerType.CUSTOM, IndexerProtocol.TORRENT),
    ]
)
def indexer_type_and_protocol(
    request: pytest.FixtureRequest,
) -> tuple[IndexerType, IndexerProtocol]:
    """Parametrized fixture for indexer types and protocols."""
    return request.param


@pytest.fixture(
    params=[
        DownloadClientType.QBITTORRENT,
        DownloadClientType.TRANSMISSION,
        DownloadClientType.DELUGE,
        DownloadClientType.RTORRENT,
        DownloadClientType.SABNZBD,
        DownloadClientType.NZBGET,
    ]
)
def download_client_type(request: pytest.FixtureRequest) -> DownloadClientType:
    """Parametrized fixture for download client types."""
    return request.param

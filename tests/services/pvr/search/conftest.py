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

"""Shared fixtures for indexer search tests."""

from datetime import UTC, datetime

import pytest

from bookcard.models.pvr import IndexerDefinition, IndexerProtocol, IndexerType
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.models import IndexerSearchResult


@pytest.fixture
def sample_release() -> ReleaseInfo:
    """Create a sample release for testing.

    Returns
    -------
    ReleaseInfo
        Sample release instance.
    """
    return ReleaseInfo(
        indexer_id=1,
        title="Test Book Title",
        download_url="https://example.com/torrent.torrent",
        size_bytes=1024000,
        publish_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        seeders=100,
        leechers=10,
        quality="epub",
        author="Test Author",
        isbn="9781234567890",
        description="A test book description",
        category="Books",
    )


@pytest.fixture
def sample_release_minimal() -> ReleaseInfo:
    """Create a minimal release for testing.

    Returns
    -------
    ReleaseInfo
        Minimal release instance.
    """
    return ReleaseInfo(
        title="Minimal Book",
        download_url="https://example.com/book.torrent",
    )


@pytest.fixture
def sample_indexer() -> IndexerDefinition:
    """Create a sample indexer definition for testing.

    Returns
    -------
    IndexerDefinition
        Sample indexer definition.
    """
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
def sample_indexer_high_priority() -> IndexerDefinition:
    """Create a high priority indexer for testing.

    Returns
    -------
    IndexerDefinition
        High priority indexer definition.
    """
    return IndexerDefinition(
        id=2,
        name="High Priority Indexer",
        indexer_type=IndexerType.TORZNAB,
        protocol=IndexerProtocol.TORRENT,
        base_url="https://priority.example.com",
        api_key="priority-key",
        enabled=True,
        priority=0,  # Lower number = higher priority
        timeout_seconds=30,
        retry_count=3,
    )


@pytest.fixture
def sample_indexer_low_priority() -> IndexerDefinition:
    """Create a low priority indexer for testing.

    Returns
    -------
    IndexerDefinition
        Low priority indexer definition.
    """
    return IndexerDefinition(
        id=3,
        name="Low Priority Indexer",
        indexer_type=IndexerType.NEWZNAB,
        protocol=IndexerProtocol.USENET,
        base_url="https://lowpri.example.com",
        api_key="lowpri-key",
        enabled=True,
        priority=100,  # Higher number = lower priority
        timeout_seconds=30,
        retry_count=3,
    )


@pytest.fixture
def sample_search_result(
    sample_release: ReleaseInfo, sample_indexer: IndexerDefinition
) -> IndexerSearchResult:
    """Create a sample search result for testing.

    Parameters
    ----------
    sample_release : ReleaseInfo
        Sample release.
    sample_indexer : IndexerDefinition
        Sample indexer.

    Returns
    -------
    IndexerSearchResult
        Sample search result.
    """
    return IndexerSearchResult(
        release=sample_release,
        score=0.85,
        indexer_name=sample_indexer.name,
        indexer_priority=sample_indexer.priority,
    )


@pytest.fixture
def sample_search_results(
    sample_release: ReleaseInfo,
    sample_indexer: IndexerDefinition,
    sample_indexer_high_priority: IndexerDefinition,
) -> list[IndexerSearchResult]:
    """Create multiple sample search results for testing.

    Parameters
    ----------
    sample_release : ReleaseInfo
        Sample release.
    sample_indexer : IndexerDefinition
        Sample indexer.
    sample_indexer_high_priority : IndexerDefinition
        High priority indexer.

    Returns
    -------
    list[IndexerSearchResult]
        List of sample search results.
    """
    release1 = ReleaseInfo(
        title="Book 1",
        download_url="https://example.com/book1.torrent",
        indexer_id=1,
    )
    release2 = ReleaseInfo(
        title="Book 2",
        download_url="https://example.com/book2.torrent",
        indexer_id=2,
    )
    release3 = ReleaseInfo(
        title="Book 1",  # Duplicate URL
        download_url="https://example.com/book1.torrent",
        indexer_id=2,
    )

    return [
        IndexerSearchResult(
            release=release1,
            score=0.8,
            indexer_name=sample_indexer.name,
            indexer_priority=sample_indexer.priority,
        ),
        IndexerSearchResult(
            release=release2,
            score=0.9,
            indexer_name=sample_indexer_high_priority.name,
            indexer_priority=sample_indexer_high_priority.priority,
        ),
        IndexerSearchResult(
            release=release3,
            score=0.7,  # Lower score, should be deduplicated
            indexer_name=sample_indexer_high_priority.name,
            indexer_priority=sample_indexer_high_priority.priority,
        ),
    ]

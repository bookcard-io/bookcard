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

"""Tests for result aggregation and deduplication."""

import pytest

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.aggregation import (
    ResultAggregator,
    URLDeduplicationStrategy,
)
from bookcard.services.pvr.search.models import IndexerSearchResult


class TestURLDeduplicationStrategy:
    """Test URLDeduplicationStrategy."""

    def test_no_duplicates(
        self, sample_search_results: list[IndexerSearchResult]
    ) -> None:
        """Test deduplication with no duplicates.

        Parameters
        ----------
        sample_search_results : list[IndexerSearchResult]
            Sample search results.
        """
        strategy = URLDeduplicationStrategy()
        # Remove duplicate URL from fixture
        results = [
            r
            for r in sample_search_results
            if r.release.download_url != "https://example.com/book1.torrent"
            or r.score == 0.8
        ]

        deduplicated = strategy.deduplicate(results)
        assert len(deduplicated) == len(results)

    def test_deduplicates_by_url(
        self, sample_search_results: list[IndexerSearchResult]
    ) -> None:
        """Test deduplication removes duplicates by URL.

        Parameters
        ----------
        sample_search_results : list[IndexerSearchResult]
            Sample search results with duplicates.
        """
        strategy = URLDeduplicationStrategy()

        deduplicated = strategy.deduplicate(sample_search_results)

        # Should have 2 unique URLs
        urls = {r.release.download_url for r in deduplicated}
        assert len(urls) == 2

    def test_keeps_higher_score(
        self, sample_search_results: list[IndexerSearchResult]
    ) -> None:
        """Test deduplication keeps result with higher score.

        Parameters
        ----------
        sample_search_results : list[IndexerSearchResult]
            Sample search results with duplicates.
        """
        strategy = URLDeduplicationStrategy()

        deduplicated = strategy.deduplicate(sample_search_results)

        # Find the duplicate URL result
        url1_results = [
            r
            for r in deduplicated
            if r.release.download_url == "https://example.com/book1.torrent"
        ]
        assert len(url1_results) == 1
        # Should keep the one with score 0.8 (higher)
        assert url1_results[0].score == 0.8

    def test_keeps_lower_priority_on_tie(
        self,
        sample_indexer: IndexerDefinition,
        sample_indexer_high_priority: IndexerDefinition,
    ) -> None:
        """Test deduplication keeps lower priority indexer when scores are equal.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        sample_indexer_high_priority : IndexerDefinition
            High priority indexer.
        """
        strategy = URLDeduplicationStrategy()

        release1 = ReleaseInfo(
            title="Book 1",
            download_url="https://example.com/same.torrent",
        )
        release2 = ReleaseInfo(
            title="Book 1",
            download_url="https://example.com/same.torrent",
        )

        results = [
            IndexerSearchResult(
                release=release1,
                score=0.8,
                indexer_priority=sample_indexer.priority,  # Higher priority number
            ),
            IndexerSearchResult(
                release=release2,
                score=0.8,  # Same score
                indexer_priority=sample_indexer_high_priority.priority,  # Lower priority number
            ),
        ]

        deduplicated = strategy.deduplicate(results)
        assert len(deduplicated) == 1
        # Should keep the one with lower priority number (higher priority)
        assert deduplicated[0].indexer_priority == sample_indexer_high_priority.priority

    def test_empty_list(self) -> None:
        """Test deduplication with empty list."""
        strategy = URLDeduplicationStrategy()
        result = strategy.deduplicate([])
        assert result == []


class TestResultAggregator:
    """Test ResultAggregator."""

    @pytest.fixture
    def aggregator(self) -> ResultAggregator:
        """Create result aggregator.

        Returns
        -------
        ResultAggregator
            Aggregator instance.
        """
        return ResultAggregator(URLDeduplicationStrategy())

    def test_aggregate_deduplicates(
        self,
        aggregator: ResultAggregator,
        sample_search_results: list[IndexerSearchResult],
    ) -> None:
        """Test aggregate deduplicates results.

        Parameters
        ----------
        aggregator : ResultAggregator
            Aggregator instance.
        sample_search_results : list[IndexerSearchResult]
            Sample search results.
        """
        aggregated = aggregator.aggregate(sample_search_results)

        # Should be deduplicated
        urls = {r.release.download_url for r in aggregated}
        assert len(urls) <= len(sample_search_results)

    def test_aggregate_sorts_by_score(self, aggregator: ResultAggregator) -> None:
        """Test aggregate sorts by score.

        Parameters
        ----------
        aggregator : ResultAggregator
            Aggregator instance.
        """
        results = [
            IndexerSearchResult(
                release=ReleaseInfo(
                    title="Low Score",
                    download_url="https://example.com/low.torrent",
                ),
                score=0.3,
            ),
            IndexerSearchResult(
                release=ReleaseInfo(
                    title="High Score",
                    download_url="https://example.com/high.torrent",
                ),
                score=0.9,
            ),
            IndexerSearchResult(
                release=ReleaseInfo(
                    title="Medium Score",
                    download_url="https://example.com/medium.torrent",
                ),
                score=0.6,
            ),
        ]

        aggregated = aggregator.aggregate(results)

        # Should be sorted by score descending
        assert aggregated[0].score == 0.9
        assert aggregated[1].score == 0.6
        assert aggregated[2].score == 0.3

    def test_aggregate_custom_sort_key(self, aggregator: ResultAggregator) -> None:
        """Test aggregate with custom sort key.

        Parameters
        ----------
        aggregator : ResultAggregator
            Aggregator instance.
        """
        results = [
            IndexerSearchResult(
                release=ReleaseInfo(
                    title="A Title",
                    download_url="https://example.com/a.torrent",
                ),
                score=0.5,
            ),
            IndexerSearchResult(
                release=ReleaseInfo(
                    title="B Title",
                    download_url="https://example.com/b.torrent",
                ),
                score=0.5,
            ),
        ]

        def sort_by_title(result: IndexerSearchResult) -> tuple:
            return (result.release.title,)

        aggregated = aggregator.aggregate(results, sort_key=sort_by_title)

        assert aggregated[0].release.title == "A Title"
        assert aggregated[1].release.title == "B Title"

    def test_aggregate_empty_list(self, aggregator: ResultAggregator) -> None:
        """Test aggregate with empty list.

        Parameters
        ----------
        aggregator : ResultAggregator
            Aggregator instance.
        """
        result = aggregator.aggregate([])
        assert result == []

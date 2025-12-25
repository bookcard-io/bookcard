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

"""Result aggregation and deduplication strategies.

Implements strategy pattern for extensible deduplication approaches.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from bookcard.services.pvr.search.models import IndexerSearchResult


class DeduplicationStrategy(ABC):
    """Abstract base class for deduplication strategies.

    Follows strategy pattern to allow different deduplication approaches.
    """

    @abstractmethod
    def deduplicate(
        self, results: list[IndexerSearchResult]
    ) -> list[IndexerSearchResult]:
        """Deduplicate search results.

        Parameters
        ----------
        results : list[IndexerSearchResult]
            List of results to deduplicate.

        Returns
        -------
        list[IndexerSearchResult]
            Deduplicated results.
        """
        raise NotImplementedError


class URLDeduplicationStrategy(DeduplicationStrategy):
    """Deduplicate results by download URL.

    When duplicates are found, keeps the result with the highest score.
    If scores are equal, keeps the one from the higher priority indexer.
    """

    def deduplicate(
        self, results: list[IndexerSearchResult]
    ) -> list[IndexerSearchResult]:
        """Deduplicate by download URL.

        Parameters
        ----------
        results : list[IndexerSearchResult]
            List of results to deduplicate.

        Returns
        -------
        list[IndexerSearchResult]
            Deduplicated results.
        """
        url_to_result: dict[str, IndexerSearchResult] = {}

        for result in results:
            url = result.release.download_url
            if url not in url_to_result:
                url_to_result[url] = result
            else:
                existing = url_to_result[url]
                # Keep the one with higher score, or lower priority if scores equal
                if result.score > existing.score or (
                    result.score == existing.score
                    and result.indexer_priority < existing.indexer_priority
                ):
                    url_to_result[url] = result

        return list(url_to_result.values())


class ResultAggregator:
    """Handles deduplication and ranking of search results.

    Delegates to a deduplication strategy, following SRP and DIP.
    """

    def __init__(self, dedup_strategy: DeduplicationStrategy) -> None:
        """Initialize result aggregator.

        Parameters
        ----------
        dedup_strategy : DeduplicationStrategy
            Deduplication strategy to use.
        """
        self.dedup_strategy = dedup_strategy

    def aggregate(
        self,
        results: list[IndexerSearchResult],
        sort_key: Callable[[IndexerSearchResult], tuple] | None = None,
    ) -> list[IndexerSearchResult]:
        """Aggregate, deduplicate, and sort results.

        Parameters
        ----------
        results : list[IndexerSearchResult]
            List of results to aggregate.
        sort_key : Callable[[IndexerSearchResult], tuple] | None
            Optional custom sort key function. If None, sorts by score
            (highest first), then by indexer priority, then by title.

        Returns
        -------
        list[IndexerSearchResult]
            Aggregated, deduplicated, and sorted results.
        """
        deduplicated = self.dedup_strategy.deduplicate(results)

        if sort_key is None:
            # Default: sort by score (highest first), then priority, then title
            def sort_key(x: IndexerSearchResult) -> tuple:
                return (
                    -x.score,
                    x.indexer_priority,
                    x.release.title,
                )

        deduplicated.sort(key=sort_key)
        return deduplicated

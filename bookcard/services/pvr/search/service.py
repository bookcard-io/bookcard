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

"""Main indexer search service.

Facade that coordinates search components following SRP and DIP.
"""

import logging
import threading
from functools import partial

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.factory import create_indexer
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.indexer_service import IndexerService
from bookcard.services.pvr.search.aggregation import (
    ResultAggregator,
    URLDeduplicationStrategy,
)
from bookcard.services.pvr.search.filtering import IndexerSearchFilter
from bookcard.services.pvr.search.models import IndexerSearchResult
from bookcard.services.pvr.search.orchestration import SearchOrchestrator
from bookcard.services.pvr.search.scoring import (
    DefaultScoringStrategy,
    ReleaseScorer,
)

logger = logging.getLogger(__name__)


class IndexerSearchService:
    """Service for searching indexers and aggregating results.

    Facade that coordinates search orchestration, scoring, filtering,
    and aggregation components.

    Parameters
    ----------
    indexer_service : IndexerService
        Service for managing indexers.
    scorer : ReleaseScorer | None
        Release scorer. If None, creates default scorer.
    aggregator : ResultAggregator | None
        Result aggregator. If None, creates default aggregator.
    orchestrator : SearchOrchestrator | None
        Search orchestrator. If None, creates default orchestrator.
    """

    def __init__(
        self,
        indexer_service: IndexerService,
        scorer: ReleaseScorer | None = None,
        aggregator: ResultAggregator | None = None,
        orchestrator: SearchOrchestrator | None = None,
    ) -> None:
        """Initialize indexer search service.

        Parameters
        ----------
        indexer_service : IndexerService
            Service for managing indexers.
        scorer : ReleaseScorer | None
            Release scorer. If None, creates default.
        aggregator : ResultAggregator | None
            Result aggregator. If None, creates default.
        orchestrator : SearchOrchestrator | None
            Search orchestrator. If None, creates default.
        """
        self._indexer_service = indexer_service
        self._scorer = scorer or ReleaseScorer(DefaultScoringStrategy())
        self._aggregator = aggregator or ResultAggregator(URLDeduplicationStrategy())
        self._orchestrator = orchestrator or SearchOrchestrator()

    def search_all_indexers(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results_per_indexer: int = 100,
        indexer_ids: list[int] | None = None,
        filter_criteria: IndexerSearchFilter | None = None,
        cancellation_event: threading.Event | None = None,
    ) -> list[IndexerSearchResult]:
        """Search across all enabled indexers.

        Searches multiple indexers concurrently, aggregates results,
        applies filtering, ranks by score, and deduplicates.

        Parameters
        ----------
        query : str
            General search query.
        title : str | None
            Optional specific title.
        author : str | None
            Optional specific author.
        isbn : str | None
            Optional ISBN.
        max_results_per_indexer : int
            Maximum results per indexer (default: 100).
        indexer_ids : list[int] | None
            Specific indexer IDs to search. None = all enabled.
        filter_criteria : IndexerSearchFilter | None
            Optional filter criteria.
        cancellation_event : threading.Event | None
            Event to signal cancellation.

        Returns
        -------
        list[IndexerSearchResult]
            List of search results, sorted by score (highest first).
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        # Get indexers to search
        indexers = self._get_indexers_to_search(indexer_ids)
        if not indexers:
            logger.warning("No enabled indexers available for search")
            return []

        logger.info(
            "Searching %d indexers for query: %s",
            len(indexers),
            query,
        )

        # Build search tasks using partial to avoid closure issues
        search_tasks = [
            (
                indexer,
                partial(
                    self._search_indexer,
                    indexer,
                    query,
                    title,
                    author,
                    isbn,
                    max_results_per_indexer,
                    cancellation_event,
                ),
            )
            for indexer in indexers
        ]

        # Execute searches concurrently
        indexer_results = self._orchestrator.execute_searches(
            search_tasks, cancellation_event
        )

        # Score and transform results
        all_results: list[IndexerSearchResult] = []
        for indexer, releases in indexer_results:
            for release in releases:
                release.indexer_id = indexer.id
                score = self._scorer.score_release(
                    release, query, title, author, isbn, indexer
                )
                result = IndexerSearchResult(
                    release=release,
                    score=score,
                    indexer_name=indexer.name,
                    indexer_priority=indexer.priority,
                )
                all_results.append(result)

        # Apply filters
        if filter_criteria is not None:
            all_results = [
                result
                for result in all_results
                if filter_criteria.matches(result.release)
            ]

        all_results = self._aggregator.aggregate(all_results)

        logger.info(
            "Search completed: %d results from %d indexers",
            len(all_results),
            len(indexer_results),
        )

        return all_results

    def search_indexer(
        self,
        indexer_id: int,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
        filter_criteria: IndexerSearchFilter | None = None,
        cancellation_event: threading.Event | None = None,
    ) -> list[IndexerSearchResult]:
        """Search a single indexer.

        Parameters
        ----------
        indexer_id : int
            Indexer ID to search.
        query : str
            General search query.
        title : str | None
            Optional specific title.
        author : str | None
            Optional specific author.
        isbn : str | None
            Optional ISBN.
        max_results : int
            Maximum results to return.
        filter_criteria : IndexerSearchFilter | None
            Optional filter criteria.
        cancellation_event : threading.Event | None
            Event to signal cancellation.

        Returns
        -------
        list[IndexerSearchResult]
            List of search results from this indexer.

        Raises
        ------
        ValueError
            If indexer not found.
        """
        indexer = self._indexer_service.get_indexer(indexer_id)
        if indexer is None:
            msg = f"Indexer {indexer_id} not found"
            raise ValueError(msg)

        if not indexer.enabled:
            logger.warning("Indexer %s (id=%s) is disabled", indexer.name, indexer_id)
            return []

        releases = self._search_indexer(
            indexer, query, title, author, isbn, max_results, cancellation_event
        )

        # Score results
        results: list[IndexerSearchResult] = []
        for release in releases:
            release.indexer_id = indexer.id
            score = self._scorer.score_release(
                release, query, title, author, isbn, indexer
            )
            result = IndexerSearchResult(
                release=release,
                score=score,
                indexer_name=indexer.name,
                indexer_priority=indexer.priority,
            )
            results.append(result)

        # Apply filters
        if filter_criteria is not None:
            results = [
                result for result in results if filter_criteria.matches(result.release)
            ]

        # Sort by score
        return self._aggregator.aggregate(results)

    def _get_indexers_to_search(
        self, indexer_ids: list[int] | None
    ) -> list[IndexerDefinition]:
        """Get list of indexers to search.

        Parameters
        ----------
        indexer_ids : list[int] | None
            Specific indexer IDs, or None for all enabled.

        Returns
        -------
        list[IndexerDefinition]
            List of enabled indexers, sorted by priority.
        """
        if indexer_ids is not None:
            indexers = [
                self._indexer_service.get_indexer(idx_id)
                for idx_id in indexer_ids
                if self._indexer_service.get_indexer(idx_id) is not None
            ]
            indexers = [idx for idx in indexers if idx is not None and idx.enabled]
        else:
            indexers = self._indexer_service.list_indexers(enabled_only=True)

        # Sort by priority (lower = higher priority)
        indexers.sort(key=lambda x: (x.priority, x.id or 0))
        return indexers

    def _search_indexer(
        self,
        indexer: IndexerDefinition,
        query: str,
        title: str | None,
        author: str | None,
        isbn: str | None,
        max_results: int,
        cancellation_event: threading.Event | None,
    ) -> list[ReleaseInfo]:
        """Search a single indexer instance.

        Parameters
        ----------
        indexer : IndexerDefinition
            Indexer definition.
        query : str
            Search query.
        title : str | None
            Optional title.
        author : str | None
            Optional author.
        isbn : str | None
            Optional ISBN.
        max_results : int
            Maximum results.
        cancellation_event : threading.Event | None
            Cancellation event.

        Returns
        -------
        list[ReleaseInfo]
            List of releases.

        Raises
        ------
        PVRProviderError
            If search fails.
        """
        if cancellation_event and cancellation_event.is_set():
            return []

        try:
            indexer_instance = create_indexer(indexer)
            releases = indexer_instance.search(
                query=query,
                title=title,
                author=author,
                isbn=isbn,
                max_results=max_results,
            )
            return list(releases)
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error searching indexer {indexer.name}: {e}"
            raise PVRProviderError(msg) from e

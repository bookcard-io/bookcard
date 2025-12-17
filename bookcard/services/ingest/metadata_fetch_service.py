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

"""Metadata fetch service for ingest.

Orchestrates metadata fetching from multiple providers.
Follows SRP by delegating scoring and merging to specialized classes.
Follows IoC/DIP by requiring explicit dependency injection.
"""

from __future__ import annotations

import logging

from bookcard.models.metadata import MetadataRecord  # noqa: TC001
from bookcard.services.ingest.metadata_merger import (
    MergeStrategy,
    MetadataMerger,
    ScoredMetadataRecord,
)
from bookcard.services.ingest.metadata_query import MetadataQuery  # noqa: TC001
from bookcard.services.ingest.metadata_scorer import MetadataScorer, ScoringConfig
from bookcard.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)


class MetadataFetchService:
    """Service for orchestrating metadata fetching and processing.

    Delegates scoring to MetadataScorer and merging to MetadataMerger.
    Follows SRP by focusing solely on orchestration.
    Follows IoC/DIP by requiring explicit dependency injection.

    Parameters
    ----------
    metadata_service : MetadataService
        Metadata service for provider searches (required).
    scorer : MetadataScorer | None
        Optional metadata scorer (creates default if None).
    merger : MetadataMerger | None
        Optional metadata merger (creates default if None).
    enabled_providers : list[str] | None
        List of enabled provider IDs. If None, uses all available.
    """

    def __init__(
        self,
        metadata_service: MetadataService,
        scorer: MetadataScorer | None = None,
        merger: MetadataMerger | None = None,
        enabled_providers: list[str] | None = None,
    ) -> None:
        """Initialize metadata fetch service.

        Parameters
        ----------
        metadata_service : MetadataService
            Metadata service (required, no default).
        scorer : MetadataScorer | None
            Optional metadata scorer.
        merger : MetadataMerger | None
            Optional metadata merger.
        enabled_providers : list[str] | None
            List of enabled provider IDs.
        """
        self._metadata_service = metadata_service
        self._scorer = scorer or MetadataScorer()
        self._merger = merger or MetadataMerger()
        self._enabled_providers = enabled_providers

    @classmethod
    def create_default(
        cls,
        enabled_providers: list[str] | None = None,
        provider_weights: dict[str, float] | None = None,
        scoring_config: ScoringConfig | None = None,
        merge_strategy: MergeStrategy | str | None = None,
    ) -> MetadataFetchService:
        """Create service with default dependencies.

        Factory method for convenience while maintaining IoC.
        Useful for cases where full dependency injection isn't needed.

        Parameters
        ----------
        enabled_providers : list[str] | None
            List of enabled provider IDs.
        provider_weights : dict[str, float] | None
            Optional provider weights for scoring.
        scoring_config : ScoringConfig | None
            Optional scoring configuration.
        merge_strategy : MergeStrategy | str | None
            Optional merge strategy (default: MERGE_BEST).

        Returns
        -------
        MetadataFetchService
            Service instance with default dependencies.
        """
        metadata_service = MetadataService()
        scorer = MetadataScorer(
            config=scoring_config, provider_weights=provider_weights
        )
        merger = MetadataMerger(strategy=merge_strategy or MergeStrategy.MERGE_BEST)
        return cls(
            metadata_service=metadata_service,
            scorer=scorer,
            merger=merger,
            enabled_providers=enabled_providers,
        )

    def fetch_metadata(self, query: MetadataQuery) -> MetadataRecord | None:
        """Fetch and merge metadata using a MetadataQuery object.

        Fetches from all enabled providers, scores each result,
        and merges the best fields.

        Parameters
        ----------
        query : MetadataQuery
            Metadata query object.

        Returns
        -------
        MetadataRecord | None
            Merged metadata record, or None if no results found.
        """
        if not query.is_valid():
            logger.warning("No search query provided (title, authors, or ISBN)")
            return None

        search_string = query.build_search_string()
        if not search_string:
            logger.warning("Empty search string generated from query")
            return None

        # Fetch from all enabled providers
        all_results: list[MetadataRecord] = []
        try:
            results = self._metadata_service.search(
                query=search_string,
                locale=query.locale,
                max_results_per_provider=query.max_results_per_provider,
                provider_ids=self._enabled_providers,
            )
            all_results = list(results)
        except (ValueError, RuntimeError, ConnectionError, TimeoutError) as e:
            logger.warning("Error fetching metadata: %s", e)
            return None

        if not all_results:
            logger.info("No metadata results found for query: %s", search_string)
            return None

        # Score and merge results
        return self._score_and_merge(all_results, query)

    def _score_and_merge(
        self, records: list[MetadataRecord], query: MetadataQuery
    ) -> MetadataRecord:
        """Score records and merge them.

        Parameters
        ----------
        records : list[MetadataRecord]
            List of metadata records to score and merge.
        query : MetadataQuery
            Original query for scoring context.

        Returns
        -------
        MetadataRecord
            Merged metadata record.
        """
        # Score all records
        scored_records: list[ScoredMetadataRecord] = []
        for record in records:
            score = self._scorer.score(
                record=record,
                query_title=query.title,
                query_authors=query.authors,
                query_isbn=query.isbn,
            )
            scored_records.append(ScoredMetadataRecord(record=record, score=score))

        # Sort by score (highest first)
        scored_records.sort(key=lambda x: x.score, reverse=True)

        # Merge using merger
        return self._merger.merge(scored_records)

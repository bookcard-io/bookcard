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

"""Indexer search service module.

This package provides components for searching indexers, scoring results,
filtering, and aggregating search results.
"""

from bookcard.services.pvr.search.aggregation import (
    ResultAggregator,
    URLDeduplicationStrategy,
)
from bookcard.services.pvr.search.exceptions import (
    IndexerSearchError,
    IndexerTimeoutError,
    IndexerUnavailableError,
)
from bookcard.services.pvr.search.filtering import (
    CompositeFilter,
    FilterCriterion,
    FormatFilter,
    IndexerSearchFilter,
    KeywordFilter,
    SeederLeecherFilter,
    SizeRangeFilter,
)
from bookcard.services.pvr.search.models import IndexerSearchResult
from bookcard.services.pvr.search.orchestration import SearchOrchestrator
from bookcard.services.pvr.search.scoring import (
    DefaultScoringStrategy,
    ReleaseScorer,
    ScoringStrategy,
    ScoringWeights,
)
from bookcard.services.pvr.search.service import IndexerSearchService

__all__ = [
    "CompositeFilter",
    "DefaultScoringStrategy",
    "FilterCriterion",
    "FormatFilter",
    "IndexerSearchError",
    "IndexerSearchFilter",
    "IndexerSearchResult",
    "IndexerSearchService",
    "IndexerTimeoutError",
    "IndexerUnavailableError",
    "KeywordFilter",
    "ReleaseScorer",
    "ResultAggregator",
    "ScoringStrategy",
    "ScoringWeights",
    "SearchOrchestrator",
    "SeederLeecherFilter",
    "SizeRangeFilter",
    "URLDeduplicationStrategy",
]

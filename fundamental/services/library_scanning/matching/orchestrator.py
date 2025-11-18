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

"""Matching orchestrator for coordinating multiple matching strategies."""

import logging

from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.exact import (
    ExactNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.fuzzy import (
    FuzzyNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.identifier import (
    IdentifierMatchingStrategy,
)
from fundamental.services.library_scanning.matching.types import MatchResult

logger = logging.getLogger(__name__)


class MatchingOrchestrator:
    """Orchestrates multiple matching strategies in priority order.

    Executes strategies in priority order and stops at first match
    above the configured threshold. Configurable confidence thresholds
    per strategy.
    """

    def __init__(
        self,
        strategies: list[BaseMatchingStrategy] | None = None,
        min_confidence: float = 0.5,
    ) -> None:
        """Initialize matching orchestrator.

        Parameters
        ----------
        strategies : list[BaseMatchingStrategy] | None
            List of matching strategies in priority order.
            If None, uses default strategies (identifier, exact, fuzzy).
        min_confidence : float
            Minimum confidence score to accept a match (default: 0.5).
        """
        if strategies is None:
            strategies = [
                IdentifierMatchingStrategy(),
                ExactNameMatchingStrategy(),
                FuzzyNameMatchingStrategy(),
            ]

        self.strategies = strategies
        self.min_confidence = min_confidence

    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match entity using all strategies in priority order.

        Parameters
        ----------
        entity : Author
            Calibre author entity to match.
        data_source : BaseDataSource
            External data source to search.

        Returns
        -------
        MatchResult | None
            Match result if found above threshold, None otherwise.
        """
        for strategy in self.strategies:
            try:
                result = strategy.match(entity, data_source)
                if result and result.confidence_score >= self.min_confidence:
                    return result
            except (DataSourceNetworkError, DataSourceRateLimitError):
                # Log error but continue to next strategy
                logger.debug("Strategy %s failed, trying next", strategy.name)
                continue

        return None

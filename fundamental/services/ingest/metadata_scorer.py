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

"""Metadata scoring service.

Scores metadata records for quality and relevance.
Follows SRP by focusing solely on scoring logic.
Follows OCP by making scoring weights configurable.
"""

from dataclasses import dataclass, field

from fundamental.models.metadata import MetadataRecord
from fundamental.services.ingest.metadata_utils import (
    StringNormalizer,
    StringSimilarityCalculator,
)


@dataclass
class ScoringConfig:
    """Configuration for metadata scoring.

    Makes scoring weights configurable, following Open/Closed Principle.

    Attributes
    ----------
    field_weights : dict[str, float]
        Weights for field completeness (default: 0.1 per field).
    title_match_weight : float
        Weight for title match quality (default: 0.2).
    author_match_weight : float
        Weight for author match quality (default: 0.2).
    isbn_match_weight : float
        Weight for ISBN exact match (default: 0.1).
    """

    field_weights: dict[str, float] = field(
        default_factory=lambda: {
            "title": 0.1,
            "authors": 0.1,
            "description": 0.1,
            "cover_url": 0.1,
            "identifiers": 0.1,
        }
    )
    title_match_weight: float = 0.2
    author_match_weight: float = 0.2
    isbn_match_weight: float = 0.1


class MetadataScorer:
    """Scores metadata records for quality and relevance.

    Separates scoring concerns from fetching/merging logic.
    Follows SRP by focusing solely on scoring.
    """

    def __init__(
        self,
        config: ScoringConfig | None = None,
        provider_weights: dict[str, float] | None = None,
    ) -> None:
        """Initialize metadata scorer.

        Parameters
        ----------
        config : ScoringConfig | None
            Optional scoring configuration (uses default if None).
        provider_weights : dict[str, float] | None
            Optional provider weights for score multiplier.
        """
        self._config = config or ScoringConfig()
        self._provider_weights = provider_weights or {}
        self._similarity_calculator = StringSimilarityCalculator()
        self._normalizer = StringNormalizer()

    def score(
        self,
        record: MetadataRecord,
        query_title: str | None = None,
        query_authors: list[str] | None = None,
        query_isbn: str | None = None,
    ) -> float:
        """Score a metadata record for quality.

        Scores based on completeness and match quality, then applies
        provider weight multiplier.

        Parameters
        ----------
        record : MetadataRecord
            Metadata record to score.
        query_title : str | None
            Original search title.
        query_authors : list[str] | None
            Original search authors.
        query_isbn : str | None
            Original search ISBN.

        Returns
        -------
        float
            Quality score (0.0-1.0).
        """
        completeness = self._calculate_completeness_score(record)
        match_quality = self._calculate_match_quality(
            record, query_title, query_authors, query_isbn
        )
        score = completeness + match_quality

        # Apply provider weight (multiplier)
        provider_weight = self._provider_weights.get(record.source_id, 1.0)
        score *= provider_weight

        # Clamp to 0.0-1.0
        return min(1.0, max(0.0, score))

    def _calculate_completeness_score(self, record: MetadataRecord) -> float:
        """Calculate completeness score for a metadata record.

        Uses configurable field weights from ScoringConfig.

        Parameters
        ----------
        record : MetadataRecord
            Metadata record to score.

        Returns
        -------
        float
            Completeness score (0.0-0.5 typically).
        """
        score = 0.0
        for field_name, weight in self._config.field_weights.items():
            value = getattr(record, field_name, None)
            # Handle both single values and collections
            if value and (
                (isinstance(value, (list, dict)) and value)
                or (not isinstance(value, (list, dict)) and value)
            ):
                score += weight
        return score

    def _calculate_match_quality(
        self,
        record: MetadataRecord,
        query_title: str | None,
        query_authors: list[str] | None,
        query_isbn: str | None,
    ) -> float:
        """Calculate match quality score.

        Parameters
        ----------
        record : MetadataRecord
            Metadata record to score.
        query_title : str | None
            Original search title.
        query_authors : list[str] | None
            Original search authors.
        query_isbn : str | None
            Original search ISBN.

        Returns
        -------
        float
            Match quality score (0.0-0.5 typically).
        """
        match_quality = 0.0

        # Title match
        if query_title and record.title:
            title_similarity = self._similarity_calculator.similarity(
                query_title.lower(), record.title.lower()
            )
            match_quality += title_similarity * self._config.title_match_weight

        # Author match
        if query_authors and record.authors:
            author_match = self._similarity_calculator.authors_match(
                query_authors, record.authors
            )
            if author_match:
                match_quality += self._config.author_match_weight

        # ISBN match (exact match is very strong)
        if query_isbn and record.identifiers:
            record_isbn = record.identifiers.get("isbn", "")
            if record_isbn:
                norm_query = self._normalizer.normalize_isbn(query_isbn)
                norm_record = self._normalizer.normalize_isbn(record_isbn)
                if norm_query == norm_record:
                    match_quality += self._config.isbn_match_weight

        return match_quality

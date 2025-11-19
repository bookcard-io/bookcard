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

"""Duplicate detection service for author records.

Separates duplicate detection logic from pipeline orchestration.
Uses Strategy pattern for different detection algorithms.
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

from fundamental.models.author_metadata import AuthorMetadata
from fundamental.services.library_scanning.matching.exact import normalize_name
from fundamental.services.library_scanning.matching.fuzzy import (
    levenshtein_distance,
)

logger = logging.getLogger(__name__)


@dataclass
class DuplicatePair:
    """Represents a pair of duplicate authors.

    Attributes
    ----------
    keep : AuthorMetadata
        Author record to keep (higher quality).
    merge : AuthorMetadata
        Author record to merge (lower quality).
    keep_score : float
        Quality score of the keep record.
    merge_score : float
        Quality score of the merge record.
    """

    keep: AuthorMetadata
    merge: AuthorMetadata
    keep_score: float
    merge_score: float


class DuplicateDetector:
    """Service for detecting duplicate authors.

    Uses ONLY persisted data from the database (no API calls).
    Detects duplicates using name similarity with Levenshtein distance.
    """

    def __init__(
        self,
        min_similarity: float = 0.85,
        quality_scorer: "QualityScorer | None" = None,
    ) -> None:
        """Initialize duplicate detector.

        Parameters
        ----------
        min_similarity : float
            Minimum name similarity to consider duplicates (default: 0.85).
        quality_scorer : QualityScorer | None
            Quality scorer instance. If None, creates default.
        """
        self._min_similarity = min_similarity
        self._quality_scorer = quality_scorer or QualityScorer()

    def find_duplicates(self, authors: list[AuthorMetadata]) -> Iterator[DuplicatePair]:
        """Find all duplicate pairs in author list.

        Parameters
        ----------
        authors : list[AuthorMetadata]
            List of authors to check for duplicates.

        Yields
        ------
        DuplicatePair
            Pairs of duplicate authors.
        """
        seen: set[int] = set()

        for i, author1 in enumerate(authors):
            if author1.id is None or author1.id in seen:
                continue

            for author2 in authors[i + 1 :]:
                if author2.id is None or author2.id in seen:
                    continue

                if self.are_duplicates(author1, author2):
                    pair = self.score_and_pair(author1, author2)
                    if pair.merge.id:
                        seen.add(pair.merge.id)
                    yield pair

    def are_duplicates(self, author1: AuthorMetadata, author2: AuthorMetadata) -> bool:
        """Check if two author records are duplicates.

        Uses ONLY persisted data from the database (no API calls).
        Uses Levenshtein distance on normalized names.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author record.
        author2 : AuthorMetadata
            Second author record.

        Returns
        -------
        bool
            True if records are duplicates, False otherwise.
        """
        # Skip if same record
        if author1.id == author2.id:
            return False

        # Normalize names from persisted data
        name1 = normalize_name(author1.name)
        name2 = normalize_name(author2.name)

        # Calculate Levenshtein distance-based similarity
        max_len = max(len(name1), len(name2))
        if max_len == 0:
            return True  # Both empty, consider duplicates

        distance = levenshtein_distance(name1, name2)
        similarity = 1.0 - (distance / max_len)

        # Check if similarity meets threshold
        if similarity >= self._min_similarity:
            logger.debug(
                "Duplicate detected: '%s' (ID: %s) and '%s' (ID: %s) - "
                "Levenshtein similarity: %.3f (distance: %d, max_len: %d)",
                author1.name,
                author1.id,
                author2.name,
                author2.id,
                similarity,
                distance,
                max_len,
            )
            return True

        # Also check alternate names if available
        if author1.alternate_names and author2.alternate_names:
            for alt1 in author1.alternate_names:
                norm_alt1 = normalize_name(alt1.name)
                for alt2 in author2.alternate_names:
                    norm_alt2 = normalize_name(alt2.name)
                    alt_distance = levenshtein_distance(norm_alt1, norm_alt2)
                    alt_max_len = max(len(norm_alt1), len(norm_alt2))
                    if alt_max_len > 0:
                        alt_similarity = 1.0 - (alt_distance / alt_max_len)
                        if alt_similarity >= self._min_similarity:
                            logger.debug(
                                "Duplicate detected via alternate names: '%s' and '%s' - "
                                "Similarity: %.3f",
                                alt1.name,
                                alt2.name,
                                alt_similarity,
                            )
                            return True

        return False

    def score_and_pair(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> DuplicatePair:
        """Score authors and create duplicate pair.

        Determines which record to keep based on quality score.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author record.
        author2 : AuthorMetadata
            Second author record.

        Returns
        -------
        DuplicatePair
            Pair with keep/merge determined by quality scores.
        """
        score1 = self._quality_scorer.calculate(author1)
        score2 = self._quality_scorer.calculate(author2)

        if score1 >= score2:
            return DuplicatePair(
                keep=author1, merge=author2, keep_score=score1, merge_score=score2
            )
        return DuplicatePair(
            keep=author2, merge=author1, keep_score=score2, merge_score=score1
        )


class QualityScorer:
    """Service for calculating author record quality scores.

    Higher score = better record to keep.
    """

    def calculate(self, author: AuthorMetadata) -> float:
        """Calculate quality score for an author record.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        float
            Quality score (higher is better).
        """
        score = 0.0
        score += self._calculate_work_count_score(author)
        score += self._calculate_ratings_score(author)
        score += self._calculate_completeness_score(author)
        score += self._calculate_recency_score(author)
        return score

    def _calculate_work_count_score(self, author: AuthorMetadata) -> float:
        """Calculate score based on work count.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        float
            Work count score (0-40 points, max at 100 works).
        """
        if author.work_count is None:
            return 0.0
        return min(40.0, author.work_count * 0.4)

    def _calculate_ratings_score(self, author: AuthorMetadata) -> float:
        """Calculate score based on ratings count.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        float
            Ratings score (0-30 points, max at 10000 ratings).
        """
        if author.ratings_count is None:
            return 0.0
        return min(30.0, author.ratings_count / 10000.0 * 30.0)

    def _calculate_completeness_score(self, author: AuthorMetadata) -> float:
        """Calculate score based on record completeness.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        float
            Completeness score (0-20 points).
        """
        # Field weights: field_name -> points
        field_weights = {
            "biography": 3,
            "birth_date": 2,
            "death_date": 2,
            "location": 2,
            "photo_url": 2,
            "personal_name": 1,
            "fuller_name": 1,
            "title": 1,
            "top_work": 1,
        }

        completeness = sum(
            weight
            for field, weight in field_weights.items()
            if getattr(author, field, None)
        )

        # Add ratings_average if present
        if author.ratings_average is not None:
            completeness += 1

        return min(20.0, completeness * 2.0)

    def _calculate_recency_score(self, author: AuthorMetadata) -> float:
        """Calculate score based on record recency.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        float
            Recency score (0-10 points, more recent = better).
        """
        if not author.last_synced_at:
            # No sync date = older record, lower score
            return 2.0

        # Normalize last_synced_at to timezone-aware (UTC) if it's naive
        last_synced = author.last_synced_at
        if last_synced.tzinfo is None:
            last_synced = last_synced.replace(tzinfo=UTC)

        days_since_sync = (datetime.now(UTC) - last_synced).total_seconds() / 86400
        # More recent = higher score (max 10 points for < 1 day old)
        return max(0.0, 10.0 - (days_since_sync / 365.0 * 10.0))

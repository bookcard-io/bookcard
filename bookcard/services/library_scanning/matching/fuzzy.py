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

"""Fuzzy name matching strategy.

Matches authors using fuzzy string matching (Levenshtein, token-based).
Confidence: 0.5-0.85.
"""

from bookcard.models.core import Author
from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.matching.base import BaseMatchingStrategy
from bookcard.services.library_scanning.matching.exact import normalize_name
from bookcard.services.library_scanning.matching.types import MatchResult


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.

    Parameters
    ----------
    s1 : str
        First string.
    s2 : str
        Second string.

    Returns
    -------
    int
        Levenshtein distance.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings (0.0 to 1.0).

    Parameters
    ----------
    s1 : str
        First string.
    s2 : str
        Second string.

    Returns
    -------
    float
        Similarity score (1.0 = identical, 0.0 = completely different).
    """
    if not s1 or not s2:
        return 0.0

    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0

    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


class FuzzyNameMatchingStrategy(BaseMatchingStrategy):
    """Matching strategy that uses fuzzy string matching.

    Priority 3: Matches using Levenshtein distance and token-based similarity.
    Confidence: 0.5-0.85.
    """

    def __init__(self, min_similarity: float = 0.7) -> None:
        """Initialize fuzzy matching strategy.

        Parameters
        ----------
        min_similarity : float
            Minimum similarity score to consider a match (default: 0.7).
        """
        self.min_similarity = min_similarity

    @property
    def name(self) -> str:
        """Get the name of this matching strategy.

        Returns
        -------
        str
            Strategy name.
        """
        return "fuzzy"

    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match author using fuzzy string matching.

        Parameters
        ----------
        entity : Author
            Calibre author entity to match.
        data_source : BaseDataSource
            External data source to search.

        Returns
        -------
        MatchResult | None
            Match result if found, None otherwise.
        """
        normalized_calibre_name = normalize_name(entity.name)

        # Search external data source
        search_results = data_source.search_author(entity.name)

        if not search_results:
            return None

        best_match: MatchResult | None = None
        best_score = 0.0

        # Find best fuzzy match
        for result in search_results:
            normalized_result_name = normalize_name(result.name)
            score = similarity_score(normalized_calibre_name, normalized_result_name)

            if score >= self.min_similarity and score > best_score:
                # Map similarity score (0.7-1.0) to confidence (0.5-0.85)
                confidence = 0.5 + (score - self.min_similarity) * (
                    (0.85 - 0.5) / (1.0 - self.min_similarity)
                )

                best_match = MatchResult(
                    confidence_score=confidence,
                    matched_entity=result,
                    match_method="fuzzy",
                )
                best_score = score

            # Also check alternate names
            for alt_name in result.alternate_names:
                normalized_alt_name = normalize_name(alt_name)
                alt_score = similarity_score(
                    normalized_calibre_name, normalized_alt_name
                )

                if alt_score >= self.min_similarity and alt_score > best_score:
                    confidence = 0.5 + (alt_score - self.min_similarity) * (
                        (0.85 - 0.5) / (1.0 - self.min_similarity)
                    )

                    best_match = MatchResult(
                        confidence_score=confidence,
                        matched_entity=result,
                        match_method="fuzzy_alternate",
                    )
                    best_score = alt_score

        return best_match

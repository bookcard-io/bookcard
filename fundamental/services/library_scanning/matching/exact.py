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

"""Exact name matching strategy.

Matches authors by exact name with normalization.
Confidence: 0.85-0.95.
"""

import unicodedata

from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.types import MatchResult


def normalize_name(name: str) -> str:
    """Normalize author name for comparison.

    Parameters
    ----------
    name : str
        Author name to normalize.

    Returns
    -------
    str
        Normalized name (lowercase, stripped, unicode normalized).
    """
    # Unicode normalization
    normalized = unicodedata.normalize("NFKD", name)
    # Convert to lowercase and strip whitespace
    normalized = normalized.lower().strip()
    # Remove extra whitespace
    return " ".join(normalized.split())


class ExactNameMatchingStrategy(BaseMatchingStrategy):
    """Matching strategy that uses exact name matching.

    Priority 2: Matches by exact name with normalization.
    Confidence: 0.85-0.95.
    """

    @property
    def name(self) -> str:
        """Get the name of this matching strategy.

        Returns
        -------
        str
            Strategy name.
        """
        return "exact"

    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match author by exact name.

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

        # Find exact match (case-insensitive, normalized)
        for result in search_results:
            normalized_result_name = normalize_name(result.name)

            if normalized_calibre_name == normalized_result_name:
                # Exact match found
                return MatchResult(
                    confidence_score=0.90,
                    matched_entity=result,
                    match_method="exact",
                )

            # Also check alternate names
            for alt_name in result.alternate_names:
                normalized_alt_name = normalize_name(alt_name)
                if normalized_calibre_name == normalized_alt_name:
                    return MatchResult(
                        confidence_score=0.88,
                        matched_entity=result,
                        match_method="exact_alternate",
                    )

        return None

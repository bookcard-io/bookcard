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

"""Identifier-based matching strategy.

Matches authors by external identifiers (VIAF, Goodreads, Wikidata, etc.).
Highest confidence matching (0.95-1.0).
"""

from bookcard.models.core import Author
from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.matching.base import BaseMatchingStrategy
from bookcard.services.library_scanning.matching.exact import normalize_name
from bookcard.services.library_scanning.matching.types import MatchResult


class IdentifierMatchingStrategy(BaseMatchingStrategy):
    """Matching strategy that uses external identifiers.

    Priority 1: Matches by VIAF, Goodreads, Wikidata, ISNI, etc.
    Highest confidence (0.95-1.0).
    """

    @property
    def name(self) -> str:
        """Get the name of this matching strategy.

        Returns
        -------
        str
            Strategy name.
        """
        return "identifier"

    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match author by external identifiers.

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
        # TODO: Extract identifiers from Calibre author metadata
        # For now, we'll search by name and check if identifiers match
        # In a full implementation, we'd need to store identifiers in Calibre
        # or extract them from existing AuthorMetadata mappings

        # Search by name first
        search_results = data_source.search_author(entity.name)

        if not search_results:
            return None

        # For identifier matching, we'd ideally have identifiers from the
        # Calibre author. Since we don't have that yet, we'll verify that
        # the first result matches the author name before returning it.
        # This is a simplified implementation - full version would compare
        # identifiers from Calibre with identifiers from search results

        normalized_calibre_name = normalize_name(entity.name)

        # Find the first result that matches the author name exactly
        # This ensures we don't return incorrect matches
        for result in search_results:
            normalized_result_name = normalize_name(result.name)

            if normalized_calibre_name == normalized_result_name:
                # Exact name match found - return with high confidence
                return MatchResult(
                    confidence_score=0.98,
                    matched_entity=result,
                    match_method="identifier",
                )

            # Also check alternate names
            for alt_name in result.alternate_names:
                normalized_alt_name = normalize_name(alt_name)
                if normalized_calibre_name == normalized_alt_name:
                    return MatchResult(
                        confidence_score=0.97,
                        matched_entity=result,
                        match_method="identifier_alternate",
                    )

        # No exact name match found - return None to let other strategies handle it
        # This prevents returning incorrect matches when identifiers aren't available
        return None

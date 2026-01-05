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

"""Book matching service for PVR import."""

import logging
from difflib import SequenceMatcher

from bookcard.services.pvr.importing.models import BookMetadata, MatchScore

logger = logging.getLogger(__name__)


class BookMatchingService:
    """Calculates similarity scores and finds best matches."""

    def find_best_match(
        self,
        target_metadata: BookMetadata,
        candidates: list[tuple[int, BookMetadata]],
    ) -> int | None:
        """Find the best matching book ID from candidates.

        Parameters
        ----------
        target_metadata : BookMetadata
            Target book metadata.
        candidates : list[tuple[int, BookMetadata]]
            List of (book_id, metadata) candidates.

        Returns
        -------
        int | None
            Best matching book ID or None.
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0][0]

        best_match_id = None
        best_score = MatchScore(0.0)

        for book_id, candidate_meta in candidates:
            score = self._calculate_score(target_metadata, candidate_meta)
            if score.value > best_score.value:
                best_score = score
                best_match_id = book_id

        # If reasonable match found, return it
        if best_match_id and best_score.is_acceptable_match():
            return best_match_id

        # Fallback to first one if no strong match?
        # Original logic fell back to first one.
        logger.warning(
            "No strong match found for '%s' among candidates. Linking first one.",
            target_metadata.title,
        )
        return candidates[0][0]

    def _calculate_score(
        self, target: BookMetadata, candidate: BookMetadata
    ) -> MatchScore:
        """Calculate similarity score."""
        # Title similarity
        title_score = SequenceMatcher(
            None, target.normalized_title, candidate.normalized_title
        ).ratio()

        # Author similarity
        author_score = SequenceMatcher(
            None, target.normalized_author, candidate.normalized_author
        ).ratio()

        # Weighted average
        weighted_value = (title_score * 0.7) + (author_score * 0.3)
        return MatchScore(weighted_value)

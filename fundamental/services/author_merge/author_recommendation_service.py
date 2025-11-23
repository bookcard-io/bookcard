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

"""Service for author recommendation and scoring.

Follows SRP by focusing solely on recommendation and scoring logic,
separating this concern from merge orchestration.
"""

import logging
from collections.abc import Callable

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from fundamental.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from fundamental.services.author_merge.value_objects import AuthorScore

logger = logging.getLogger(__name__)


class AuthorRecommendationService:
    """Service for author recommendation and scoring.

    Handles the logic for determining which author to keep when merging,
    including scoring and metadata evaluation.
    """

    def __init__(
        self,
        relationship_repo: AuthorRelationshipRepository,
        calibre_author_service: CalibreAuthorService | None = None,
    ) -> None:
        """Initialize recommendation service.

        Parameters
        ----------
        relationship_repo : AuthorRelationshipRepository
            Repository for relationship operations.
        calibre_author_service : CalibreAuthorService | None
            Optional Calibre author service for book counts.
        """
        self._relationship_repo = relationship_repo
        self._calibre_author_service = calibre_author_service

    def determine_best_author(
        self,
        authors: list[AuthorMetadata],
        library_id: int,
        get_mapping: Callable[[int | None, int], AuthorMapping | None],
        get_book_count: Callable[[AuthorMetadata, int], int],
    ) -> AuthorMetadata:
        """Determine the best author to keep based on multiple criteria.

        Parameters
        ----------
        authors : list[AuthorMetadata]
            List of authors to evaluate.
        library_id : int
            Library ID.
        get_mapping : callable
            Function to get AuthorMapping for an author.
        get_book_count : callable
            Function to get book count for an author.

        Returns
        -------
        AuthorMetadata
            Best author to keep.
        """
        best_author = authors[0]
        best_score = -1

        for author in authors:
            score = self._calculate_score(
                author, library_id, get_mapping, get_book_count
            )

            if score.total > best_score:
                best_score = score.total
                best_author = author

        return best_author

    def calculate_metadata_score(self, author: AuthorMetadata) -> int:
        """Calculate metadata completeness score for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author to score.

        Returns
        -------
        int
            Metadata score (higher is better).
        """
        score = 0

        # Count populated fields
        if author.biography:
            score += 10
        if author.birth_date:
            score += 5
        if author.death_date:
            score += 5
        if author.location:
            score += 5
        if author.photo_url:
            score += 10
        if author.work_count and author.work_count > 0:
            score += 5
        if author.ratings_count and author.ratings_count > 0:
            score += 5
        if author.top_work:
            score += 5

        return score

    def _calculate_score(
        self,
        author: AuthorMetadata,
        library_id: int,
        get_mapping: Callable[[int | None, int], AuthorMapping | None],
        get_book_count: Callable[[AuthorMetadata, int], int],
    ) -> AuthorScore:
        """Calculate total score for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author to score.
        library_id : int
            Library ID.
        get_mapping : callable
            Function to get AuthorMapping for an author.
        get_book_count : callable
            Function to get book count for an author.

        Returns
        -------
        AuthorScore
            Author score object.
        """
        score = 0

        # Prefer author with more books
        book_count = get_book_count(author, library_id)
        score += book_count * 100  # Books are weighted heavily

        # Prefer author with verified mapping
        mapping = get_mapping(author.id, library_id)
        is_verified = mapping.is_verified if mapping else False
        if is_verified:
            score += 50

        # Prefer author with better metadata
        metadata_score = self.calculate_metadata_score(author)
        score += metadata_score

        # Prefer author with user-uploaded photos (custom photos are valuable)
        user_photos_count = 0
        if author.id:
            relationship_counts = self._relationship_repo.get_relationship_counts(
                author.id
            )
            user_photos_count = relationship_counts.user_photos
            # Each user photo adds to the score (user effort is valuable)
            score += user_photos_count * 15

        return AuthorScore(
            book_count=book_count,
            is_verified=is_verified,
            metadata_completeness=metadata_score,
            user_photos_count=user_photos_count,
            total=score,
        )

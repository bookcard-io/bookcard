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

"""Score stage for calculating author similarity scores."""

import logging

from sqlmodel import select

from fundamental.models.author_metadata import (
    AuthorMetadata,
    AuthorSimilarity,
    AuthorSubject,
)
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class ScoreStage(PipelineStage):
    """Stage that calculates similarity scores between authors.

    Creates AuthorSimilarity records using genre overlap, collaboration
    detection, and work similarity.
    """

    def __init__(self, min_similarity: float = 0.3) -> None:
        """Initialize score stage.

        Parameters
        ----------
        min_similarity : float
            Minimum similarity score to store (default: 0.3).
        """
        self._progress = 0.0
        self._min_similarity = min_similarity

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "score"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def _calculate_genre_similarity(
        self,
        author1_subjects: set[str],
        author2_subjects: set[str],
    ) -> float:
        """Calculate similarity based on genre/subject overlap.

        Parameters
        ----------
        author1_subjects : set[str]
            Subjects for first author.
        author2_subjects : set[str]
            Subjects for second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if not author1_subjects or not author2_subjects:
            return 0.0

        intersection = author1_subjects & author2_subjects
        union = author1_subjects | author2_subjects

        if not union:
            return 0.0

        # Jaccard similarity
        return len(intersection) / len(union)

    def _calculate_similarity(
        self,
        context: PipelineContext,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate overall similarity between two authors.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        # Get subjects for both authors
        stmt1 = select(AuthorSubject).where(
            AuthorSubject.author_metadata_id == author1.id,
        )
        subjects1 = {s.subject_name for s in context.session.exec(stmt1).all()}

        stmt2 = select(AuthorSubject).where(
            AuthorSubject.author_metadata_id == author2.id,
        )
        subjects2 = {s.subject_name for s in context.session.exec(stmt2).all()}

        # Calculate genre similarity
        # Could add more factors here:
        # - Work count similarity
        # - Ratings similarity
        # - Collaboration detection (would need book data)

        return self._calculate_genre_similarity(subjects1, subjects2)

    def _create_similarity_if_needed(
        self,
        context: PipelineContext,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
        similarity: float,
    ) -> bool:
        """Create similarity record if it doesn't already exist.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.
        similarity : float
            Similarity score.

        Returns
        -------
        bool
            True if similarity was created, False if it already existed.
        """
        # Check if similarity already exists
        stmt = select(AuthorSimilarity).where(
            (
                (AuthorSimilarity.author1_id == author1.id)
                & (AuthorSimilarity.author2_id == author2.id)
            )
            | (
                (AuthorSimilarity.author1_id == author2.id)
                & (AuthorSimilarity.author2_id == author1.id)
            ),
        )
        existing = context.session.exec(stmt).first()

        if existing:
            return False

        # Create similarity record (always store with lower ID first)
        # Both IDs should be non-None at this point (from database)
        if (
            author1.id is not None
            and author2.id is not None
            and author1.id < author2.id
        ):
            similarity_record = AuthorSimilarity(
                author1_id=author1.id,
                author2_id=author2.id,
                similarity_score=similarity,
                similarity_source="genre_overlap",
            )
        else:
            similarity_record = AuthorSimilarity(
                author1_id=author2.id,
                author2_id=author1.id,
                similarity_score=similarity,
                similarity_source="genre_overlap",
            )
        context.session.add(similarity_record)
        return True

    def _get_all_authors(self, context: PipelineContext) -> list[AuthorMetadata]:
        """Get all AuthorMetadata records.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.

        Returns
        -------
        list[AuthorMetadata]
            List of all author metadata records.
        """
        stmt = select(AuthorMetadata)
        return list(context.session.exec(stmt).all())

    def _process_author_pair(
        self,
        context: PipelineContext,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> bool:
        """Process a single author pair and create similarity if needed.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        bool
            True if similarity was created, False otherwise.
        """
        # Skip if same author
        if author1.id == author2.id:
            return False

        # Calculate similarity
        similarity = self._calculate_similarity(context, author1, author2)

        # Create similarity if above threshold
        return similarity >= self._min_similarity and self._create_similarity_if_needed(
            context,
            author1,
            author2,
            similarity,
        )

    def _process_all_author_pairs(
        self,
        context: PipelineContext,
        all_authors: list[AuthorMetadata],
        total_pairs: int,
    ) -> int:
        """Process all author pairs and create similarities.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        all_authors : list[AuthorMetadata]
            List of all authors to compare.
        total_pairs : int
            Total number of pairs to process.

        Returns
        -------
        int
            Number of similarities created.
        """
        similarities_created = 0
        pairs_processed = 0

        for i, author1 in enumerate(all_authors):
            if context.check_cancelled():
                break

            for _j, author2 in enumerate(all_authors[i + 1 :], start=i + 1):
                if context.check_cancelled():
                    break

                if self._process_author_pair(context, author1, author2):
                    similarities_created += 1

                pairs_processed += 1

                # Update progress with metadata
                if total_pairs > 0:
                    self._progress = pairs_processed / total_pairs
                    metadata = {
                        "current_index": pairs_processed,
                        "total_items": total_pairs,
                        "similarities_created": similarities_created,
                    }
                    context.update_progress(self._progress, metadata)

        return similarities_created

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the score stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with ingested authors.

        Returns
        -------
        StageResult
            Result with similarity scores created.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Score cancelled")

        try:
            all_authors = self._get_all_authors(context)
            total_pairs = len(all_authors) * (len(all_authors) - 1) // 2

            if total_pairs == 0:
                return StageResult(
                    success=True,
                    message="No authors to score",
                    stats={"similarities_created": 0},
                )

            similarities_created = self._process_all_author_pairs(
                context,
                all_authors,
                total_pairs,
            )

            # Commit similarities
            context.session.commit()

            stats = {
                "similarities_created": similarities_created,
                "pairs_processed": total_pairs,
            }

            logger.info(
                "Created %d author similarities for library %d",
                similarities_created,
                context.library_id,
            )

            return StageResult(
                success=True,
                message=f"Created {similarities_created} author similarities",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in score stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Score failed: {e}",
            )

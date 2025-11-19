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

"""Match stage for matching crawled entities to external data sources."""

import logging
from datetime import UTC, datetime

from fundamental.models.core import Author
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
)

logger = logging.getLogger(__name__)


class MatchStage(PipelineStage):
    """Stage that matches crawled entities to external data sources.

    Uses MatchingOrchestrator with configured strategies to match authors.
    Creates AuthorMapping records with confidence scores.
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        author_limit: int | None = None,
        stale_data_max_age_days: int | None = None,
    ) -> None:
        """Initialize match stage.

        Parameters
        ----------
        min_confidence : float
            Minimum confidence score to accept a match (default: 0.5).
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit API calls.
        stale_data_max_age_days : int | None
            Maximum age in days for existing mappings to be considered fresh.
            If an author has a mapping within this age, matching will be skipped.
            None means always match (no staleness check).
        """
        self._progress = 0.0
        self._min_confidence = min_confidence
        self._author_limit = author_limit
        self._stale_data_max_age_days = stale_data_max_age_days
        self._matching_orchestrator = MatchingOrchestrator(
            min_confidence=min_confidence,
        )

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "match"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def _should_skip_match(
        self,
        context: PipelineContext,
        calibre_author_id: int,
    ) -> bool:
        """Check if author matching should be skipped due to existing fresh mapping.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        calibre_author_id : int
            Calibre author ID to check.

        Returns
        -------
        bool
            True if matching should be skipped, False otherwise.
        """
        # If no stale data settings, always match
        if self._stale_data_max_age_days is None:
            return False

        # Check if author has an existing mapping
        mapping_repo = AuthorMappingRepository(context.session)
        existing_mapping = mapping_repo.find_by_calibre_author_id_and_library(
            calibre_author_id,
            context.library_id,
        )

        if not existing_mapping:
            # No mapping exists, should match
            return False

        # Check if mapping is still fresh
        now = datetime.now(UTC)
        # Use updated_at if available, otherwise created_at
        mapping_date = existing_mapping.updated_at or existing_mapping.created_at
        # Normalize to timezone-aware if needed
        if mapping_date.tzinfo is None:
            mapping_date = mapping_date.replace(tzinfo=UTC)

        days_since_mapping = (now - mapping_date).days

        # If mapping is older than max_age, should re-match
        # Mapping is fresh if it's within max_age, so skip matching
        return days_since_mapping < self._stale_data_max_age_days

    def _update_progress_metadata(
        self,
        context: PipelineContext,
        idx: int,
        total_authors: int,
        author_name: str,
        matched_count: int,
        unmatched_count: int,
        skipped_count: int,
    ) -> None:
        """Update progress with metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        idx : int
            Current index (0-based).
        total_authors : int
            Total number of authors.
        author_name : str
            Current author name.
        matched_count : int
            Number of matched authors.
        unmatched_count : int
            Number of unmatched authors.
        skipped_count : int
            Number of skipped authors.
        """
        self._progress = (idx + 1) / total_authors
        metadata = {
            "current_stage": {
                "name": "match",
                "status": "in_progress",
                "current_item": author_name,
                "current_index": idx + 1,
                "total_items": total_authors,
                "matched": matched_count,
                "unmatched": unmatched_count,
                "skipped": skipped_count,
            },
        }
        context.update_progress(self._progress, metadata)

    def _process_author_match(
        self,
        context: PipelineContext,
        author: Author,
    ) -> tuple[int, int, int]:
        """Process a single author match.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        author : Author
            Author to match.

        Returns
        -------
        tuple[int, int, int]
            Tuple of (matched_count, unmatched_count, skipped_count).
        """
        matched_count = 0
        unmatched_count = 0
        skipped_count = 0

        # Skip if author has no ID (shouldn't happen, but be safe)
        if author.id is None:
            unmatched_count += 1
            logger.warning("Author '%s' has no ID, skipping match", author.name)
            return matched_count, unmatched_count, skipped_count

        # Check if author should be skipped due to existing fresh mapping
        if self._should_skip_match(context, author.id):
            skipped_count += 1
            logger.debug(
                "Skipping match for author '%s' (ID: %d) - existing mapping is fresh",
                author.name,
                author.id,
            )
            return matched_count, unmatched_count, skipped_count

        # Attempt to match author
        match_result = self._matching_orchestrator.match(
            author,
            context.data_source,
        )

        if match_result:
            # Store the Calibre author ID for tracking
            match_result.calibre_author_id = author.id
            context.match_results.append(match_result)
            matched_count += 1
            logger.debug(
                "Matched author '%s' (ID: %d) via %s (confidence: %.2f)",
                author.name,
                author.id,
                match_result.match_method,
                match_result.confidence_score,
            )
        else:
            context.unmatched_authors.append(author)
            unmatched_count += 1
            logger.debug(
                "No match found for author '%s' (ID: %d)",
                author.name,
                author.id,
            )

        return matched_count, unmatched_count, skipped_count

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the match stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with crawled authors and data source.

        Returns
        -------
        StageResult
            Result with match results and unmatched authors.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Match cancelled")

        authors = context.crawled_authors
        total_authors = len(authors)

        logger.info(
            "Starting match stage for library %d (%d authors to match)",
            context.library_id,
            total_authors,
        )

        if total_authors == 0:
            logger.warning("No authors to match in library %d", context.library_id)
            return StageResult(
                success=True,
                message="No authors to match",
                stats={"matched": 0, "unmatched": 0},
            )

        try:
            matched_count = 0
            unmatched_count = 0
            skipped_count = 0

            # Apply author limit if set (for testing)
            if self._author_limit is not None and self._author_limit > 0:
                authors = authors[: self._author_limit]
                total_authors = len(authors)
                logger.info(
                    "Author limit applied: processing %d authors (limited from original count)",
                    total_authors,
                )

            # Log progress every 10% or every 25 authors, whichever is more frequent
            log_interval = max(1, min(25, total_authors // 10))

            for idx, author in enumerate(authors):
                if context.check_cancelled():
                    return StageResult(success=False, message="Match cancelled")

                # Process author match
                m, u, s = self._process_author_match(context, author)
                matched_count += m
                unmatched_count += u
                skipped_count += s

                # Log progress periodically
                if (idx + 1) % log_interval == 0 or (idx + 1) == total_authors:
                    logger.info(
                        "Match progress: %d/%d authors processed (%d matched, %d unmatched, %d skipped)",
                        idx + 1,
                        total_authors,
                        matched_count,
                        unmatched_count,
                        skipped_count,
                    )

                # Update progress with metadata
                self._update_progress_metadata(
                    context,
                    idx,
                    total_authors,
                    author.name,
                    matched_count,
                    unmatched_count,
                    skipped_count,
                )

            stats = {
                "matched": matched_count,
                "unmatched": unmatched_count,
                "skipped": skipped_count,
                "total": total_authors,
            }

            logger.info(
                "Matched %d/%d authors in library %d (%d skipped due to fresh mappings)",
                matched_count,
                total_authors,
                context.library_id,
                skipped_count,
            )

            return StageResult(
                success=True,
                message=f"Matched {matched_count}/{total_authors} authors",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in match stage")
            return StageResult(
                success=False,
                message=f"Match failed: {e}",
            )

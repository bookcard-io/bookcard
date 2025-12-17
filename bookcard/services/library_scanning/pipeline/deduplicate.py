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

"""Deduplication stage for merging duplicate AuthorMetadata records.

Detects and merges duplicate author records that represent the same person
but have different OpenLibrary keys (e.g., "Fyodor Dostoevsky" vs "Fyodor DOSTOYEVSKY").
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import selectinload
from sqlmodel import select

from bookcard.models.author_metadata import AuthorMetadata, AuthorWork
from bookcard.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from bookcard.services.library_scanning.pipeline.duplicate_detector import (
    DuplicateDetector,
)
from bookcard.services.library_scanning.pipeline.merge_commands import (
    AuthorMerger,
    MergeStats,
)

if TYPE_CHECKING:
    from bookcard.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class DeduplicateStage(PipelineStage):
    """Stage that deduplicates and merges duplicate AuthorMetadata records.

    Uses ONLY persisted data from the database (no API calls).
    Detects duplicates using:
    - Name similarity using Levenshtein distance on persisted names only

    Chooses the best record based on:
    - Work count (more works = more complete)
    - Ratings count (more popular)
    - Record completeness (more fields filled)
    - Last synced date (more recent = fresher)

    Merges duplicates by:
    - Keeping the best record
    - Merging alternate names, photos, links, subjects, remote IDs
    - Updating all AuthorMapping records
    - Deleting duplicate records
    """

    def __init__(
        self,
        min_name_similarity: float = 0.85,
        author_limit: int | None = None,
    ) -> None:
        """Initialize deduplication stage.

        Uses ONLY persisted data and Levenshtein distance on names.

        Parameters
        ----------
        min_name_similarity : float
            Minimum name similarity (Levenshtein-based) to consider duplicates (default: 0.85).
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit processing.
        """
        self._progress = 0.0
        self._min_name_similarity = min_name_similarity
        self._author_limit = author_limit
        self._detector = DuplicateDetector(min_similarity=min_name_similarity)
        self._merger = AuthorMerger()

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "deduplicate"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def _load_authors(self, context: "PipelineContext") -> list[AuthorMetadata]:
        """Load all authors with relationships.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.

        Returns
        -------
        list[AuthorMetadata]
            List of authors with relationships loaded.
        """
        stmt = select(AuthorMetadata).options(
            selectinload(AuthorMetadata.remote_ids),
            selectinload(AuthorMetadata.photos),
            selectinload(AuthorMetadata.alternate_names),
            selectinload(AuthorMetadata.links),
            selectinload(AuthorMetadata.works).selectinload(AuthorWork.subjects),
        )
        all_authors = list(context.session.exec(stmt).all())

        # Apply author limit if set (for testing)
        if self._author_limit is not None and self._author_limit > 0:
            all_authors = all_authors[: self._author_limit]
            logger.info(
                "Author limit applied: processing %d authors (limited from original count)",
                len(all_authors),
            )

        return all_authors

    def _update_progress(
        self,
        context: "PipelineContext",
        pairs_checked: int,
        total_pairs: int,
        duplicates_found: int,
        merged_count: int,
    ) -> None:
        """Update progress tracking.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        pairs_checked : int
            Number of pairs checked so far.
        total_pairs : int
            Total number of pairs to check.
        duplicates_found : int
            Number of duplicates found.
        merged_count : int
            Number of merges completed.
        """
        if total_pairs > 0:
            self._progress = pairs_checked / total_pairs
            metadata = {
                "current_stage": {
                    "name": "deduplicate",
                    "status": "in_progress",
                    "current_index": pairs_checked,
                    "total_items": total_pairs,
                    "duplicates_found": duplicates_found,
                    "merged": merged_count,
                },
            }
            context.update_progress(self._progress, metadata)

    def _merge_author_records(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge duplicate author records.

        Delegates to AuthorMerger which uses Command pattern for separation of concerns.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep (higher quality).
        merge : AuthorMetadata
            Record to merge into keep (will be deleted).
        """
        self._merger.merge(context, keep, merge)

    def execute(self, context: "PipelineContext") -> StageResult:
        """Execute the deduplication stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.

        Returns
        -------
        StageResult
            Result with deduplication statistics.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Deduplicate cancelled")

        logger.info("Starting deduplicate stage for library %d", context.library_id)

        # Report initial status
        self._progress = 0.0
        context.update_progress(
            0.0,
            {
                "current_stage": {
                    "name": "deduplicate",
                    "status": "starting",
                    "current_index": 0,
                    "total_items": 0,
                    "duplicates_found": 0,
                    "merged": 0,
                },
            },
        )

        try:
            # Load authors
            authors = self._load_authors(context)

            logger.info(
                "Checking %d author records for duplicates",
                len(authors),
            )

            if len(authors) < 2:
                # Report completion status
                self._progress = 1.0
                context.update_progress(
                    1.0,
                    {
                        "current_stage": {
                            "name": "deduplicate",
                            "status": "completed",
                            "current_index": 0,
                            "total_items": 0,
                            "duplicates_found": 0,
                            "merged": 0,
                        },
                    },
                )
                return StageResult(
                    success=True,
                    message="No duplicates to check (less than 2 authors)",
                    stats={"duplicates_found": 0, "merged": 0, "total_checked": 0},
                )

            # Report detection phase start
            total_pairs = len(authors) * (len(authors) - 1) // 2
            context.update_progress(
                0.0,
                {
                    "current_stage": {
                        "name": "deduplicate",
                        "status": "detecting",
                        "current_index": 0,
                        "total_items": total_pairs,
                        "duplicates_found": 0,
                        "merged": 0,
                    },
                },
            )

            # Find duplicates using detector service
            duplicate_pairs = list(self._detector.find_duplicates(authors))

            # Update progress after detection
            self._update_progress(
                context, total_pairs, total_pairs, len(duplicate_pairs), 0
            )

            # Report merge phase start
            if duplicate_pairs:
                context.update_progress(
                    self._progress,
                    {
                        "current_stage": {
                            "name": "deduplicate",
                            "status": "merging",
                            "current_index": 0,
                            "total_items": len(duplicate_pairs),
                            "duplicates_found": len(duplicate_pairs),
                            "merged": 0,
                        },
                    },
                )

            # Merge duplicates with progress reporting
            merge_stats = MergeStats(duplicates_found=len(duplicate_pairs))
            merge_stats.total_checked = total_pairs

            # Merge pairs with progress reporting
            for idx, pair in enumerate(duplicate_pairs):
                if context.check_cancelled():
                    return StageResult(success=False, message="Deduplicate cancelled")

                try:
                    self._merger.merge_pair(context, pair)
                    merge_stats.merged += 1
                except Exception:
                    logger.exception("Failed to merge pair")
                    merge_stats.failed += 1

                # Update progress periodically (every merge or every 10%)
                if (idx + 1) % max(1, len(duplicate_pairs) // 10) == 0 or (
                    idx + 1
                ) == len(duplicate_pairs):
                    # Progress is split: 50% for detection, 50% for merging
                    detection_progress = 0.5
                    merge_progress = 0.5 * ((idx + 1) / len(duplicate_pairs))
                    self._progress = detection_progress + merge_progress

                    context.update_progress(
                        self._progress,
                        {
                            "current_stage": {
                                "name": "deduplicate",
                                "status": "merging",
                                "current_index": idx + 1,
                                "total_items": len(duplicate_pairs),
                                "duplicates_found": len(duplicate_pairs),
                                "merged": merge_stats.merged,
                            },
                        },
                    )

            # Commit all changes
            context.session.commit()

            # Report final completion status
            self._progress = 1.0
            context.update_progress(
                1.0,
                {
                    "current_stage": {
                        "name": "deduplicate",
                        "status": "completed",
                        "current_index": len(duplicate_pairs),
                        "total_items": len(duplicate_pairs),
                        "duplicates_found": merge_stats.duplicates_found,
                        "merged": merge_stats.merged,
                    },
                },
            )

            logger.info(
                "Deduplication complete: found %d duplicates, merged %d records",
                merge_stats.duplicates_found,
                merge_stats.merged,
            )

            return StageResult(
                success=True,
                message=f"Found {merge_stats.duplicates_found} duplicates, merged {merge_stats.merged} records",
                stats=merge_stats.to_dict(),
            )

        except Exception as e:
            logger.exception("Error in deduplicate stage")
            context.session.rollback()
            # Report error status
            context.update_progress(
                self._progress,
                {
                    "current_stage": {
                        "name": "deduplicate",
                        "status": "error",
                        "error": str(e),
                    },
                },
            )
            return StageResult(
                success=False,
                message=f"Deduplicate failed: {e}",
            )

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

"""Components for the link stage pipeline.

Separates concerns following SOLID principles:
- Repositories (data access)
- Services (business logic)
- Progress tracking
- Statistics collection
- Batch processing
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bookcard.models.author_metadata import AuthorMapping
from bookcard.services.library_scanning.matching.types import MatchResult
from bookcard.services.library_scanning.repositories import (
    AuthorMappingRepository,
    AuthorMetadataRepository,
    MappingData,
)
from bookcard.services.progress import (
    BaseProgressTracker,
    calculate_log_interval,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Service Layer
# ============================================================================


class MappingService:
    """Handle the business logic for creating/updating author mappings."""

    def __init__(
        self,
        mapping_repo: AuthorMappingRepository,
        metadata_repo: AuthorMetadataRepository,
    ) -> None:
        """Initialize mapping service.

        Parameters
        ----------
        mapping_repo : AuthorMappingRepository
            Mapping repository.
        metadata_repo : AuthorMetadataRepository
            Author metadata repository.
        """
        self.mapping_repo = mapping_repo
        self.metadata_repo = metadata_repo

    def create_or_update_mapping(
        self,
        match_result: MatchResult,
        library_id: int,
    ) -> tuple[AuthorMapping, bool] | None:
        """Create or update a mapping for a match result.

        Parameters
        ----------
        match_result : MatchResult
            Match result containing author information.
        library_id : int
            Library identifier.

        Returns
        -------
        tuple[AuthorMapping, bool] | None
            Tuple of (mapping, was_created) or None if metadata not found.
            was_created is True if mapping was created, False if updated.
        """
        if match_result.calibre_author_id is None:
            return None

        # Normalize key to OpenLibrary convention: ensure /authors/ prefix
        raw_key = match_result.matched_entity.key
        if not raw_key.startswith("/authors/"):
            lookup_key = f"/authors/{raw_key.replace('authors/', '')}"
        else:
            lookup_key = raw_key

        # Find the metadata
        metadata = self.metadata_repo.find_by_openlibrary_key(lookup_key)

        if not metadata or not metadata.id:
            logger.warning(
                "AuthorMetadata not found for key: %s (normalized: %s) (Calibre author ID: %d)",
                match_result.matched_entity.key,
                lookup_key,
                match_result.calibre_author_id,
            )
            # Log available keys for debugging
            logger.debug(
                "Searching for AuthorMetadata with key: %s (tried normalized: %s)",
                match_result.matched_entity.key,
                lookup_key,
            )
            return None

        # Prepare mapping data
        mapping_data = MappingData(
            library_id=library_id,
            calibre_author_id=match_result.calibre_author_id,
            author_metadata_id=metadata.id,
            confidence_score=match_result.confidence_score,
            matched_by=match_result.match_method,
        )

        # Clean up old mappings for this metadata (force rematch case)
        # If we are linking this Calibre author to this metadata, we should remove any
        # OTHER mappings that point to this metadata but are NOT this Calibre author.
        # However, multiple Calibre authors *could* legitimately map to the same OpenLibrary author
        # (e.g. "J.K. Rowling" and "Joanne Rowling").

        # BUT, the requirement is: "on successful rematch, it should delete the `author_mappings` table and remove all previous mappings belonging to the target `author_metadata.id`"
        # This implies we want to reset mappings for this METADATA record.
        # But we must be careful not to delete the mapping we are about to create/update.
        # So we delete all mappings for this metadata_id EXCEPT the one for the current calibre_author_id.

        # Actually, re-reading the requirement: "it should delete the `author_mappings` table and remove all previous mappings belonging to the target `author_metadata.id`"
        # The user example shows two mappings for the SAME author_metadata_id (663).
        # One is for calibre_author_id 256, one for 75.
        # The user says "in this case, it should delete row 483" (the one for 256).
        # This implies that when we map author 75 to metadata 663, we should remove other mappings to 663?
        # That seems dangerous if multiple valid Calibre authors map to one real author.

        # However, "rematch" usually implies fixing a bad match. If author 256 was wrongly mapped to 663,
        # and now we map 75 to 663, maybe 256 should be unmapped?
        # But maybe 256 IS also 663?

        # Let's assume the user knows what they want: "remove all previous mappings belonging to the target `author_metadata.id`".
        # I will implement: Delete all mappings for `metadata.id` where `calibre_author_id` != `match_result.calibre_author_id`.

        deleted_count = self.mapping_repo.delete_mappings_for_metadata_exclude_author(
            metadata.id, match_result.calibre_author_id
        )
        if deleted_count > 0:
            logger.info(
                "Deleted %d previous mappings for AuthorMetadata ID %d",
                deleted_count,
                metadata.id,
            )

        # Check for existing mapping
        existing = self.mapping_repo.find_by_calibre_author_id_and_library(
            match_result.calibre_author_id,
            library_id,
        )

        if existing:
            mapping = self.mapping_repo.update(existing, mapping_data)
            logger.debug(
                "Updated mapping for Calibre author ID %d -> AuthorMetadata ID %d",
                match_result.calibre_author_id,
                metadata.id,
            )
            return mapping, False
        mapping = self.mapping_repo.create(mapping_data)
        logger.debug(
            "Created mapping for Calibre author ID %d -> AuthorMetadata ID %d",
            match_result.calibre_author_id,
            metadata.id,
        )
        return mapping, True


# ============================================================================
# Progress Tracking
# ============================================================================


class ProgressReporter(BaseProgressTracker):
    """Handle progress tracking and reporting.

    Uses shared base class for common functionality,
    following DRY principles and improving code cohesion.
    """

    def __init__(self, total_items: int, log_interval: int | None = None) -> None:
        """Initialize progress reporter.

        Parameters
        ----------
        total_items : int
            Total number of items to process.
        log_interval : int | None
            Interval for logging progress. If None, calculated automatically.
        """
        # Calculate log interval using shared utility
        if log_interval is None:
            log_interval = calculate_log_interval(total_items)
        super().__init__(total_items, log_interval)

    def update(self, current_index: int) -> float:
        """Update progress and return progress value.

        Parameters
        ----------
        current_index : int
            Current item index (1-based).

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._update_progress(current_index)

    def should_log(self, current_index: int) -> bool:
        """Check if we should log progress at this index.

        Parameters
        ----------
        current_index : int
            Current item index (1-based).

        Returns
        -------
        bool
            True if should log, False otherwise.
        """
        return self.should_log_at(current_index)


# ============================================================================
# Statistics Collection
# ============================================================================


@dataclass
class LinkingStatistics:
    """Statistics for the linking process."""

    mappings_created: int = 0
    mappings_updated: int = 0
    mappings_failed: int = 0
    total_processed: int = 0

    def record_creation(self) -> None:
        """Record a mapping creation."""
        self.mappings_created += 1
        self.total_processed += 1

    def record_update(self) -> None:
        """Record a mapping update."""
        self.mappings_updated += 1
        self.total_processed += 1

    def record_failure(self) -> None:
        """Record a mapping failure."""
        self.mappings_failed += 1
        self.total_processed += 1

    def to_dict(self) -> dict[str, int]:
        """Convert statistics to dictionary.

        Returns
        -------
        dict[str, int]
            Statistics dictionary.
        """
        return {
            "mappings_created": self.mappings_created,
            "mappings_updated": self.mappings_updated,
            "mappings_failed": self.mappings_failed,
            "total_processed": self.total_processed,
        }


# ============================================================================
# Batch Processing
# ============================================================================


class MappingBatchProcessor:
    """Processor for creating/updating author mappings."""

    def __init__(
        self,
        mapping_service: MappingService,
        statistics: LinkingStatistics,
    ) -> None:
        """Initialize batch processor.

        Parameters
        ----------
        mapping_service : MappingService
            Mapping service for creating/updating mappings.
        statistics : LinkingStatistics
            Statistics collector.
        """
        self.mapping_service = mapping_service
        self.statistics = statistics

    def process_item(self, item: MatchResult, context: dict[str, Any]) -> bool:
        """Process a single match result.

        Parameters
        ----------
        item : MatchResult
            Match result to process.
        context : dict[str, Any]
            Context dictionary with library_id.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        result = self.mapping_service.create_or_update_mapping(
            item,
            context["library_id"],
        )

        if result:
            _mapping, was_created = result
            if was_created:
                self.statistics.record_creation()
            else:
                self.statistics.record_update()
            return True
        self.statistics.record_failure()
        return False

    def process_batch(
        self,
        items: list[MatchResult],
        context: dict[str, Any],
        progress_callback: Callable[[int, int], None] | None = None,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> int:
        """Process a batch of items.

        Parameters
        ----------
        items : list[MatchResult]
            List of match results to process.
        context : dict[str, Any]
            Context dictionary with library_id.
        progress_callback : Callable[[int, int], None] | None
            Optional callback for progress updates (current, total).
        cancellation_check : Callable[[], bool] | None
            Optional function to check if processing should be cancelled.

        Returns
        -------
        int
            Number of successfully processed items.
        """
        successful = 0

        for idx, item in enumerate(items, 1):
            if cancellation_check and cancellation_check():
                logger.info("Batch processing cancelled at item %d/%d", idx, len(items))
                break

            if self.process_item(item, context):
                successful += 1

            if progress_callback:
                progress_callback(idx, len(items))

        return successful

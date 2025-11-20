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
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.progress import (
    BaseProgressTracker,
    calculate_log_interval,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Value Objects
# ============================================================================


@dataclass
class MappingData:
    """Value object for mapping data.

    Parameters
    ----------
    library_id : int
        Library identifier.
    calibre_author_id : int
        Calibre author ID.
    author_metadata_id : int
        Author metadata ID.
    confidence_score : float | None
        Matching confidence score.
    matched_by : str | None
        How the match was made.
    """

    library_id: int
    calibre_author_id: int
    author_metadata_id: int
    confidence_score: float | None
    matched_by: str | None


# ============================================================================
# Repository Layer
# ============================================================================


class AuthorMappingRepository:
    """Repository for AuthorMapping operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_calibre_author_id(self, calibre_author_id: int) -> AuthorMapping | None:
        """Find mapping by Calibre author ID.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID.

        Returns
        -------
        AuthorMapping | None
            Mapping if found, None otherwise.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.calibre_author_id == calibre_author_id
        )
        return self.session.exec(stmt).first()

    def find_by_calibre_author_id_and_library(
        self, calibre_author_id: int, library_id: int
    ) -> AuthorMapping | None:
        """Find mapping by Calibre author ID and library ID.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID.
        library_id : int
            Library ID.

        Returns
        -------
        AuthorMapping | None
            Mapping if found, None otherwise.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.calibre_author_id == calibre_author_id,
            AuthorMapping.library_id == library_id,
        )
        return self.session.exec(stmt).first()

    def create(self, mapping_data: MappingData) -> AuthorMapping:
        """Create new mapping.

        Parameters
        ----------
        mapping_data : MappingData
            Mapping data.

        Returns
        -------
        AuthorMapping
            Created mapping record.
        """
        mapping = AuthorMapping(
            library_id=mapping_data.library_id,
            calibre_author_id=mapping_data.calibre_author_id,
            author_metadata_id=mapping_data.author_metadata_id,
            confidence_score=mapping_data.confidence_score,
            matched_by=mapping_data.matched_by,
        )
        self.session.add(mapping)
        return mapping

    def update(
        self, existing: AuthorMapping, mapping_data: MappingData
    ) -> AuthorMapping:
        """Update existing mapping.

        Parameters
        ----------
        existing : AuthorMapping
            Existing mapping record.
        mapping_data : MappingData
            Updated mapping data.

        Returns
        -------
        AuthorMapping
            Updated mapping record.
        """
        existing.author_metadata_id = mapping_data.author_metadata_id
        existing.confidence_score = mapping_data.confidence_score
        existing.matched_by = mapping_data.matched_by
        existing.updated_at = datetime.now(UTC)
        return existing


class AuthorMetadataRepository:
    """Repository for AuthorMetadata operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_openlibrary_key(self, key: str) -> AuthorMetadata | None:
        """Find author metadata by OpenLibrary key.

        Parameters
        ----------
        key : str
            OpenLibrary author key.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        stmt = select(AuthorMetadata).where(AuthorMetadata.openlibrary_key == key)
        return self.session.exec(stmt).first()


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

        # Find the metadata
        metadata = self.metadata_repo.find_by_openlibrary_key(
            match_result.matched_entity.key
        )

        if not metadata or not metadata.id:
            logger.warning(
                "AuthorMetadata not found for key: %s (Calibre author ID: %d)",
                match_result.matched_entity.key,
                match_result.calibre_author_id,
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

        # Check for existing mapping
        existing = self.mapping_repo.find_by_calibre_author_id(
            match_result.calibre_author_id
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

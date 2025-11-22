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

"""Matching orchestrator for coordinating multiple matching strategies."""

import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.exact import (
    ExactNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.fuzzy import (
    FuzzyNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.identifier import (
    IdentifierMatchingStrategy,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.repositories import (
    AuthorMappingRepository,
    MappingData,
)

logger = logging.getLogger(__name__)


class MatchingOrchestrator:
    """Orchestrates multiple matching strategies in priority order.

    Executes strategies in priority order and stops at first match
    above the configured threshold. Configurable confidence thresholds
    per strategy.

    Also handles the full matching lifecycle including checking for
    existing mappings and handling unmatched authors.
    """

    def __init__(
        self,
        strategies: list[BaseMatchingStrategy] | None = None,
        min_confidence: float = 0.5,
    ) -> None:
        """Initialize matching orchestrator.

        Parameters
        ----------
        strategies : list[BaseMatchingStrategy] | None
            List of matching strategies in priority order.
            If None, uses default strategies (identifier, exact, fuzzy).
        min_confidence : float
            Minimum confidence score to accept a match (default: 0.5).
        """
        if strategies is None:
            strategies = [
                IdentifierMatchingStrategy(),
                ExactNameMatchingStrategy(),
                FuzzyNameMatchingStrategy(),
            ]

        self.strategies = strategies
        self.min_confidence = min_confidence

    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match entity using all strategies in priority order.

        Parameters
        ----------
        entity : Author
            Calibre author entity to match.
        data_source : BaseDataSource
            External data source to search.

        Returns
        -------
        MatchResult | None
            Match result if found above threshold, None otherwise.
        """
        for strategy in self.strategies:
            try:
                result = strategy.match(entity, data_source)
                if result and result.confidence_score >= self.min_confidence:
                    return result
            except (DataSourceNetworkError, DataSourceRateLimitError):
                # Log error but continue to next strategy
                logger.debug("Strategy %s failed, trying next", strategy.name)
                continue

        return None

    def _should_skip_match(
        self,
        session: Session,
        calibre_author_id: int,
        library_id: int,
        stale_data_max_age_days: int | None,
    ) -> bool:
        """Check if match should be skipped.

        Checks both for existing valid matches and stale data age.
        """
        # First check if author already has a valid match
        # Query mapping with join to check metadata
        stmt = (
            select(AuthorMapping, AuthorMetadata)
            .join(
                AuthorMetadata,
                AuthorMapping.author_metadata_id == AuthorMetadata.id,
            )
            .where(
                AuthorMapping.calibre_author_id == calibre_author_id,
                AuthorMapping.library_id == library_id,
            )
        )
        result = session.exec(stmt).first()

        if result:
            mapping, metadata = result
            # Valid match means: matched_by != "unmatched" AND openlibrary_key is not None
            if (
                mapping.matched_by != "unmatched"
                and metadata.openlibrary_key is not None
            ):
                return True

        # Then check staleness if configured
        if stale_data_max_age_days is None:
            return False

        mapping_repo = AuthorMappingRepository(session)
        existing_mapping = mapping_repo.find_by_calibre_author_id_and_library(
            calibre_author_id,
            library_id,
        )

        if not existing_mapping:
            return False

        now = datetime.now(UTC)
        mapping_date = existing_mapping.updated_at or existing_mapping.created_at
        if mapping_date.tzinfo is None:
            mapping_date = mapping_date.replace(tzinfo=UTC)

        days_since = (now - mapping_date).days
        return days_since < stale_data_max_age_days

    def _handle_unmatched(
        self,
        session: Session,
        author: Author,
        library_id: int,
    ) -> int:
        """Handle case where no match is found for an author.

        Creates/updates an AuthorMetadata record with openlibrary_key=None and links it.

        Returns
        -------
        int
            The author_metadata_id of the created/updated unmatched record.
        """
        if author.id is None:
            msg = "Author ID cannot be None for unmatched handling"
            raise ValueError(msg)

        logger.info("No match found for %s - creating unmatched record", author.name)

        # Check for existing mapping to reuse metadata
        mapping_repo = AuthorMappingRepository(session)
        existing_mapping = mapping_repo.find_by_calibre_author_id_and_library(
            author.id, library_id
        )

        unmatched_metadata = None
        if existing_mapping:
            # Check if we can reuse the metadata from the existing mapping
            # We only reuse if it is also an unmatched record (key is None)
            existing_metadata = session.get(
                AuthorMetadata, existing_mapping.author_metadata_id
            )
            if existing_metadata and existing_metadata.openlibrary_key is None:
                unmatched_metadata = existing_metadata
                # Update name if changed
                if unmatched_metadata.name != author.name:
                    unmatched_metadata.name = author.name
                    session.add(unmatched_metadata)

        if not unmatched_metadata:
            # Create unmatched metadata
            unmatched_metadata = AuthorMetadata(
                name=author.name,
                openlibrary_key=None,
            )
            session.add(unmatched_metadata)

        session.flush()

        if unmatched_metadata.id is None:
            msg = "Failed to generate ID for unmatched metadata"
            raise ValueError(msg)

        # Create or update mapping
        mapping_data = MappingData(
            library_id=library_id,
            calibre_author_id=author.id,
            author_metadata_id=unmatched_metadata.id,
            confidence_score=0.0,
            matched_by="unmatched",
        )

        if existing_mapping:
            mapping_repo.update(existing_mapping, mapping_data)
        else:
            mapping_repo.create(mapping_data)

        session.commit()

        return unmatched_metadata.id

    def process_match_request(
        self,
        session: Session,
        author: Author,
        library_id: int,
        data_source: BaseDataSource,
        force_rematch: bool = False,
        openlibrary_key: str | None = None,
        stale_data_max_age_days: int | None = None,
    ) -> MatchResult | None:
        """Process a match request with full lifecycle handling.

        Parameters
        ----------
        session : Session
            Database session.
        author : Author
            Calibre author to match.
        library_id : int
            Library ID.
        data_source : BaseDataSource
            External data source.
        force_rematch : bool
            Whether to force rematching even if fresh mapping exists.
        openlibrary_key : str | None
            Specific key to match against if force_rematch is True.
        stale_data_max_age_days : int | None
            Max age of existing mappings before re-matching.

        Returns
        -------
        MatchResult | None
            Match result if a new match was found and should be linked.
            None if skipped (existing match) or handled as unmatched.
        """
        if author.id is None:
            logger.warning("Author has no ID: %s", author.name)
            return None

        # Check if author already has a match or should be skipped (unless force_rematch)
        if not force_rematch and self._should_skip_match(
            session, author.id, library_id, stale_data_max_age_days
        ):
            logger.info(
                "Skipping match for author %s (ID: %s) - already matched or fresh",
                author.name,
                author.id,
            )
            return None

        # Perform match
        match_result = None
        # If openlibrary_key is provided, match directly by key
        if openlibrary_key and force_rematch:
            logger.info(
                "Force rematching author %s to OLID %s",
                author.name,
                openlibrary_key,
            )
            # Get author directly by key
            author_data = data_source.get_author(openlibrary_key)
            if not author_data:
                logger.warning(
                    "Author not found in data source for key: %s", openlibrary_key
                )
            else:
                match_result = MatchResult(
                    confidence_score=1.0,
                    matched_entity=author_data,
                    match_method="direct_key",
                )
        else:
            # Use normal matching flow
            match_result = self.match(author, data_source)

        if match_result:
            # Add calibre ID to result for tracking
            match_result.calibre_author_id = author.id

            logger.info(
                "Matched author %s -> %s (confidence: %.2f)",
                author.name,
                match_result.matched_entity.name,
                match_result.confidence_score,
            )
            return match_result

        # No match found - handle unmatched
        self._handle_unmatched(session, author, library_id)
        # Return None to indicate no match
        # The caller can look up the author_metadata_id from the mapping if needed
        return None

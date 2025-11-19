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

"""Link stage for creating library-aware work-author linkages."""

import logging
from typing import Any

from sqlmodel import Session

from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
    AuthorMetadataRepository,
    LinkingStatistics,
    MappingBatchProcessor,
    MappingService,
    ProgressReporter,
)

logger = logging.getLogger(__name__)


class LinkStage(PipelineStage):
    """Stage that creates library-aware linkages between works and authors.

    Links books to AuthorMetadata via AuthorMapping + library context.
    Tracks which library each work belongs to.

    Refactored to follow SOLID principles with separated concerns:
    - Data access delegated to repositories
    - Business logic in service layer
    - Progress tracking and statistics collection separated
    - Batch processing for extensibility

    Supports both dependency injection (for testing) and lazy initialization
    (for backward compatibility).
    """

    def __init__(
        self,
        mapping_service: MappingService | None = None,
        author_limit: int | None = None,
    ) -> None:
        """Initialize link stage.

        Parameters
        ----------
        mapping_service : MappingService | None
            Mapping service. If None, will be created from context.
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit processing.
        """
        self._mapping_service = mapping_service
        self.author_limit = author_limit
        self._progress_reporter: ProgressReporter | None = None
        self._initialized = mapping_service is not None

    def _initialize_from_context(self, context: PipelineContext) -> None:
        """Initialize components from pipeline context.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with session.
        """
        if self._initialized:
            return

        # Create components directly (factory moved here to avoid circular import)
        components = LinkStageFactory.create_components(
            session=context.session,
            author_limit=self.author_limit,
        )

        self._mapping_service = components["mapping_service"]
        self._initialized = True

    @property
    def mapping_service(self) -> MappingService:
        """Get mapping service.

        Returns
        -------
        MappingService
            Mapping service instance.
        """
        if self._mapping_service is None:
            msg = (
                "Mapping service not initialized. Call _initialize_from_context first."
            )
            raise RuntimeError(msg)
        return self._mapping_service

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "link"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress_reporter.progress if self._progress_reporter else 0.0

    def _prepare_match_results(self, match_results: list) -> list:
        """Apply limits and filtering to match results.

        Parameters
        ----------
        match_results : list
            List of match results.

        Returns
        -------
        list
            Prepared match results.
        """
        if self.author_limit is not None and self.author_limit > 0:
            limited = match_results[: self.author_limit]
            logger.info(
                "Author limit applied: processing %d authors (limited from original count)",
                len(limited),
            )
            return limited
        return match_results

    def _process_mappings(
        self,
        context: PipelineContext,
        match_results: list,
    ) -> LinkingStatistics:
        """Process all match results and create/update mappings.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        match_results : list
            List of match results to process.

        Returns
        -------
        LinkingStatistics
            Statistics for the linking process.
        """
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(self.mapping_service, statistics)
        self._progress_reporter = ProgressReporter(len(match_results))

        def progress_callback(current: int, total: int) -> None:
            """Update progress and report to context.

            Parameters
            ----------
            current : int
                Current item index (1-based).
            total : int
                Total number of items.
            """
            if self._progress_reporter is None:
                msg = "Progress reporter not initialized"
                raise RuntimeError(msg)
            progress = self._progress_reporter.update(current)

            if self._progress_reporter.should_log(current):
                logger.info(
                    "Link progress: %d/%d match results processed (%s)",
                    current,
                    total,
                    statistics.to_dict(),
                )

            # Update pipeline context
            metadata = {
                "current_stage": {
                    "name": "link",
                    "status": "in_progress",
                    "current_index": current,
                    "total_items": total,
                    **statistics.to_dict(),
                },
            }
            context.update_progress(progress, metadata)

        # Process batch
        processor.process_batch(
            match_results,
            {"library_id": context.library_id},
            progress_callback,
            context.check_cancelled,
        )

        return statistics

    def _create_empty_result(self) -> StageResult:
        """Create result for empty input.

        Returns
        -------
        StageResult
            Empty result stage result.
        """
        logger.warning("No match results to link")
        return StageResult(
            success=True,
            message="No matches to link",
            stats={"mappings_created": 0},
        )

    def _create_success_result(self, statistics: LinkingStatistics) -> StageResult:
        """Create success result from statistics.

        Parameters
        ----------
        statistics : LinkingStatistics
            Linking statistics.

        Returns
        -------
        StageResult
            Success stage result.
        """
        logger.info("Linking complete: %s", statistics.to_dict())
        stats_dict = statistics.to_dict()
        return StageResult(
            success=True,
            message=f"Created {statistics.mappings_created} mappings, updated {statistics.mappings_updated}",
            stats={
                k: float(v) if isinstance(v, int) else v for k, v in stats_dict.items()
            },
        )

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the link stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with match results and crawled data.

        Returns
        -------
        StageResult
            Result with linked mappings count.
        """
        # Initialize from context if not already initialized
        if not self._initialized:
            self._initialize_from_context(context)

        if context.check_cancelled():
            return StageResult(success=False, message="Link cancelled")

        # Apply limit and validate
        match_results = self._prepare_match_results(context.match_results)

        total_matches = len(match_results)

        logger.info(
            "Starting link stage for library %d (%d match results to process)",
            context.library_id,
            total_matches,
        )

        if total_matches == 0:
            return self._create_empty_result()

        try:
            # Process mappings
            statistics = self._process_mappings(context, match_results)

            # Commit mappings
            context.session.commit()

            return self._create_success_result(statistics)

        except Exception as e:
            logger.exception("Error in link stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Link failed: {e}",
            )


# ============================================================================
# Factory for Stage Creation
# ============================================================================


class LinkStageFactory:
    """Factory for creating fully configured LinkStage instances."""

    @staticmethod
    def create_components(
        session: Session,
        author_limit: int | None = None,  # noqa: ARG004
    ) -> dict[str, Any]:
        """Create components for LinkStage.

        Parameters
        ----------
        session : Session
            Database session.
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Not used in this method but kept for API consistency.

        Returns
        -------
        dict[str, Any]
            Dictionary with components: mapping_service.
        """
        # Create repositories
        mapping_repo = AuthorMappingRepository(session)
        metadata_repo = AuthorMetadataRepository(session)

        # Create service
        mapping_service = MappingService(mapping_repo, metadata_repo)

        return {
            "mapping_service": mapping_service,
        }

    @staticmethod
    def create(
        session: Session,
        author_limit: int | None = None,
    ) -> LinkStage:
        """Create a fully configured LinkStage.

        Parameters
        ----------
        session : Session
            Database session.
        author_limit : int | None
            Maximum number of authors to process (None = no limit).

        Returns
        -------
        LinkStage
            Fully configured link stage instance.
        """
        components = LinkStageFactory.create_components(
            session=session,
            author_limit=author_limit,
        )

        # Create stage (no import needed - we're in the same module)
        return LinkStage(
            mapping_service=components["mapping_service"],
            author_limit=author_limit,
        )

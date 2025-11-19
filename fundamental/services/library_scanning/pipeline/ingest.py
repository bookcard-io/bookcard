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

"""Ingest stage for fetching and storing external metadata."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from fundamental.models.author_metadata import AuthorMetadata
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.ingest_components import (
    AlternateNameService,
    AuthorAlternateNameRepository,
    AuthorDataFetcher,
    AuthorIngestionUnitOfWork,
    AuthorLinkRepository,
    AuthorLinkService,
    AuthorMetadataRepository,
    AuthorMetadataService,
    AuthorPhotoRepository,
    AuthorPhotoService,
    AuthorRemoteIdRepository,
    AuthorWorkRepository,
    AuthorWorkService,
    DirectAuthorSubjectStrategy,
    HybridSubjectStrategy,
    MatchResultDeduplicator,
    PhotoUrlBuilder,
    ProgressTracker,
    RemoteIdService,
    WorkBasedSubjectStrategy,
    WorkSubjectRepository,
)

logger = logging.getLogger(__name__)


class IngestStage(PipelineStage):
    """Stage that fetches full metadata from external sources.

    Creates/updates AuthorMetadata, AuthorRemoteId, AuthorPhoto, etc.
    Handles incremental updates (only fetch if stale).
    Fetches subjects from author's works if not available from author data.

    Refactored to follow SOLID principles with separated concerns:
    - Data fetching delegated to AuthorDataFetcher
    - Business logic in service layer
    - Database operations in repositories
    - Subject fetching via strategy pattern

    Supports both dependency injection (for testing) and lazy initialization
    (for backward compatibility).
    """

    def __init__(
        self,
        author_fetcher: AuthorDataFetcher | None = None,
        ingestion_uow: AuthorIngestionUnitOfWork | None = None,
        deduplicator: MatchResultDeduplicator | None = None,
        progress_tracker: ProgressTracker | None = None,
        author_limit: int | None = None,
        stale_data_max_age_days: int | None = None,
        stale_data_refresh_interval_days: int | None = None,
        max_works_per_author: int | None = None,
    ) -> None:
        """Initialize ingest stage.

        Parameters
        ----------
        author_fetcher : AuthorDataFetcher | None
            Component for fetching author data. If None, will be created from context.
        ingestion_uow : AuthorIngestionUnitOfWork | None
            Unit of work for author ingestion. If None, will be created from context.
        deduplicator : MatchResultDeduplicator | None
            Component for deduplicating match results. If None, will be created.
        progress_tracker : ProgressTracker | None
            Optional progress tracker (creates new one if None).
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit API calls.
        stale_data_max_age_days : int | None
            Maximum age of cached data in days before considering it stale
            (None = always refresh).
        stale_data_refresh_interval_days : int | None
            Minimum interval between refreshes in days (None = no minimum).
        max_works_per_author : int | None
            Maximum number of works to fetch per author (None = no limit).
            This limits both work keys fetched and work metadata fetched for subjects.
        """
        self._author_fetcher = author_fetcher
        self._ingestion_uow = ingestion_uow
        self._deduplicator = deduplicator
        self._progress_tracker = progress_tracker
        self.author_limit = author_limit
        self._stale_data_max_age_days = stale_data_max_age_days
        self._stale_data_refresh_interval_days = stale_data_refresh_interval_days
        self._max_works_per_author = max_works_per_author
        self._initialized = (
            author_fetcher is not None
            and ingestion_uow is not None
            and deduplicator is not None
        )

    def _initialize_from_context(self, context: PipelineContext) -> None:
        """Initialize components from pipeline context.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with session and data source.
        """
        if self._initialized:
            return

        components = IngestStageFactory.create_components(
            session=context.session,
            data_source=context.data_source,
            author_limit=self.author_limit,
            max_works_per_author=self._max_works_per_author,
        )

        self._author_fetcher = components["author_fetcher"]
        self._ingestion_uow = components["ingestion_uow"]
        self._deduplicator = components["deduplicator"]
        self._progress_tracker = components["progress_tracker"]
        self._initialized = True

    @property
    def author_fetcher(self) -> AuthorDataFetcher:
        """Get author data fetcher.

        Returns
        -------
        AuthorDataFetcher
            Author data fetcher instance.
        """
        if self._author_fetcher is None:
            msg = "Author fetcher not initialized. Call _initialize_from_context first."
            raise RuntimeError(msg)
        return self._author_fetcher

    @property
    def ingestion_uow(self) -> AuthorIngestionUnitOfWork:
        """Get ingestion unit of work.

        Returns
        -------
        AuthorIngestionUnitOfWork
            Ingestion unit of work instance.
        """
        if self._ingestion_uow is None:
            msg = "Ingestion UOW not initialized. Call _initialize_from_context first."
            raise RuntimeError(msg)
        return self._ingestion_uow

    @property
    def deduplicator(self) -> MatchResultDeduplicator:
        """Get deduplicator.

        Returns
        -------
        MatchResultDeduplicator
            Deduplicator instance.
        """
        if self._deduplicator is None:
            self._deduplicator = MatchResultDeduplicator()
        return self._deduplicator

    @property
    def progress_tracker(self) -> ProgressTracker:
        """Get progress tracker.

        Returns
        -------
        ProgressTracker
            Progress tracker instance.
        """
        if self._progress_tracker is None:
            self._progress_tracker = ProgressTracker()
        return self._progress_tracker

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "ingest"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self.progress_tracker.progress

    def _should_skip_fetch(
        self,
        context: PipelineContext,
        author_key: str,
        author_name: str,  # noqa: ARG002
    ) -> bool:
        """Check if author fetch should be skipped due to stale data settings.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_key : str
            Author key identifier.
        author_name : str
            Author name for logging (unused but kept for API consistency).

        Returns
        -------
        bool
            True if fetch should be skipped, False otherwise.
        """
        # If no stale data settings, always fetch
        if (
            self._stale_data_max_age_days is None
            and self._stale_data_refresh_interval_days is None
        ):
            return False

        # Check if author exists in database
        stmt = select(AuthorMetadata).where(
            AuthorMetadata.openlibrary_key == author_key
        )
        existing = context.session.exec(stmt).first()

        if not existing or not existing.last_synced_at:
            # Author doesn't exist or has no sync date, fetch it
            return False

        now = datetime.now(UTC)
        # Normalize last_synced_at to timezone-aware if needed
        last_synced = existing.last_synced_at
        if last_synced.tzinfo is None:
            last_synced = last_synced.replace(tzinfo=UTC)

        days_since_sync = (now - last_synced).days

        # Check max age: if data is older than max_age, fetch it
        if (
            self._stale_data_max_age_days is not None
            and days_since_sync >= self._stale_data_max_age_days
        ):
            return False

        # Check refresh interval: if less than interval has passed, skip
        if (
            self._stale_data_refresh_interval_days is not None
            and days_since_sync < self._stale_data_refresh_interval_days
        ):
            return True

        # If we have max_age but data is fresh, skip
        return (
            self._stale_data_max_age_days is not None
            and days_since_sync < self._stale_data_max_age_days
        )

    def _apply_limit(self, match_results: list) -> list:
        """Apply author limit if set.

        Parameters
        ----------
        match_results : list
            List of match results.

        Returns
        -------
        list
            Limited match results if limit is set, otherwise original list.
        """
        if self.author_limit is not None and self.author_limit > 0:
            limited = match_results[: self.author_limit]
            logger.info(
                "Author limit applied: processing %d authors (limited from original count)",
                len(limited),
            )
            return limited
        return match_results

    def _process_authors(
        self,
        context: PipelineContext,
        unique_results: list,
    ) -> dict[str, int]:
        """Process all authors and return statistics.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        unique_results : list
            List of unique match results.

        Returns
        -------
        dict[str, int]
            Statistics dictionary with ingested, failed, and total counts.
        """
        ingested_count = 0
        failed_count = 0

        self.progress_tracker.reset(len(unique_results))

        for idx, match_result in enumerate(unique_results):
            if context.check_cancelled():
                break

            author_key = match_result.matched_entity.key
            author_name = match_result.matched_entity.name

            try:
                logger.info(
                    "Processing author '%s' (key: %s) %d/%d",
                    author_name,
                    author_key,
                    idx + 1,
                    len(unique_results),
                )

                # Check if we should skip fetching due to stale data settings
                should_skip = self._should_skip_fetch(context, author_key, author_name)
                if should_skip:
                    logger.debug(
                        "Skipping fetch for '%s' (key: %s) - data is fresh",
                        author_name,
                        author_key,
                    )
                    ingested_count += 1
                    self.progress_tracker.update()
                    self._report_progress(
                        context, idx, unique_results, ingested_count, failed_count
                    )
                    continue

                # Fetch author data
                author_data = self.author_fetcher.fetch_author(author_key)

                if author_data:
                    # Ingest using unit of work
                    self.ingestion_uow.ingest_author(match_result, author_data)
                    # Commit after each author to preserve progress if interrupted
                    context.session.commit()
                    ingested_count += 1
                    logger.info(
                        "Successfully ingested author '%s' (%d/%d)",
                        author_name,
                        idx + 1,
                        len(unique_results),
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        "Could not fetch full author data for '%s' (key: %s) (%d/%d)",
                        author_name,
                        author_key,
                        idx + 1,
                        len(unique_results),
                    )

            except (DataSourceNetworkError, DataSourceRateLimitError) as e:
                logger.warning(
                    "Network error ingesting author '%s' (key: %s) (%d/%d): %s",
                    author_name,
                    author_key,
                    idx + 1,
                    len(unique_results),
                    e,
                )
                failed_count += 1
            except Exception:
                logger.exception(
                    "Unexpected error ingesting author '%s' (key: %s) (%d/%d)",
                    author_name,
                    author_key,
                    idx + 1,
                    len(unique_results),
                )
                failed_count += 1

            # Update progress
            self.progress_tracker.update()
            self._report_progress(
                context, idx, unique_results, ingested_count, failed_count
            )

        return {
            "ingested": ingested_count,
            "failed": failed_count,
            "total": len(unique_results),
        }

    def _report_progress(
        self,
        context: PipelineContext,
        idx: int,
        unique_results: list,
        ingested_count: int,
        failed_count: int,
    ) -> None:
        """Report progress to context.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        idx : int
            Current index.
        unique_results : list
            List of unique match results.
        ingested_count : int
            Number of ingested authors.
        failed_count : int
            Number of failed authors.
        """
        if unique_results:
            match_result = unique_results[idx]
            metadata = {
                "current_stage": {
                    "name": "ingest",
                    "status": "in_progress",
                    "current_item": match_result.matched_entity.name,
                    "current_index": idx + 1,
                    "total_items": len(unique_results),
                    "ingested": ingested_count,
                    "failed": failed_count,
                },
            }
            context.update_progress(self.progress_tracker.progress, metadata)

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the ingest stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with match results.

        Returns
        -------
        StageResult
            Result with ingested metadata counts.
        """
        # Initialize from context if not already initialized
        if not self._initialized:
            self._initialize_from_context(context)

        if context.check_cancelled():
            return StageResult(success=False, message="Ingest cancelled")

        # Apply author limit if set (for testing)
        match_results = self._apply_limit(context.match_results)

        total_matches = len(match_results)

        logger.info(
            "Starting ingest stage for library %d (%d matched authors to ingest)",
            context.library_id,
            total_matches,
        )

        if total_matches == 0:
            logger.warning("No matches to ingest in library %d", context.library_id)
            return StageResult(
                success=True,
                message="No matches to ingest",
                stats={"ingested": 0},
            )

        try:
            # Deduplicate match results by author key
            unique_results, duplicate_count = self.deduplicator.deduplicate_by_key(
                match_results
            )

            if not unique_results:
                return StageResult(
                    success=True,
                    message="No unique matches to ingest",
                    stats={"ingested": 0},
                )

            # Process each author (commits after each author)
            stats = self._process_authors(context, unique_results)
            stats["deduplicated"] = duplicate_count

            # Final commit as safety measure (authors already committed incrementally)
            context.session.commit()

            logger.info(
                "Ingested %d/%d unique authors in library %d (deduplicated from %d match results)",
                stats["ingested"],
                len(unique_results),
                context.library_id,
                len(match_results),
            )

            result = StageResult(
                success=True,
                message=f"Ingested {stats['ingested']}/{len(unique_results)} unique authors",
                stats={
                    k: float(v) if isinstance(v, int) else v for k, v in stats.items()
                },
            )

        except Exception as e:
            logger.exception("Error in ingest stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Ingest failed: {e}",
            )
        else:
            return result


# ============================================================================
# Factory for Stage Creation
# ============================================================================


class IngestStageFactory:
    """Factory for creating fully configured IngestStage instances."""

    @staticmethod
    def create_components(
        session: Session,
        data_source: BaseDataSource,
        author_limit: int | None = None,  # noqa: ARG004
        max_works_per_author: int | None = None,
    ) -> dict[str, Any]:
        """Create components for IngestStage.

        Parameters
        ----------
        session : Session
            Database session.
        data_source : BaseDataSource
            External data source for fetching author data.
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Not used in this method but kept for API consistency with create().
        max_works_per_author : int | None
            Maximum number of works to fetch per author (None = no limit).
            This limits both work keys fetched and work metadata fetched for subjects.

        Returns
        -------
        dict[str, Any]
            Dictionary with components: author_fetcher, ingestion_uow,
            deduplicator, progress_tracker.
        """
        # Create repositories
        author_repo = AuthorMetadataRepository(session)
        photo_repo = AuthorPhotoRepository(session)
        remote_id_repo = AuthorRemoteIdRepository(session)
        alt_name_repo = AuthorAlternateNameRepository(session)
        link_repo = AuthorLinkRepository(session)
        work_repo = AuthorWorkRepository(session)
        subject_repo = WorkSubjectRepository(session)

        # Create URL builder
        url_builder = PhotoUrlBuilder()

        # Create services
        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alternate_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            author_repo,
            photo_service,
            remote_id_service,
            alternate_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        # Create data fetcher
        data_fetcher = AuthorDataFetcher(data_source)

        # Create subject fetching strategies
        direct_strategy = DirectAuthorSubjectStrategy(data_fetcher)
        work_strategy = WorkBasedSubjectStrategy(
            data_fetcher,
            work_service,
            work_repo,
            subject_repo,
            max_works_per_author=max_works_per_author,
        )
        subject_strategy = HybridSubjectStrategy(direct_strategy, work_strategy)

        # Create unit of work
        uow = AuthorIngestionUnitOfWork(
            session,
            author_service,
            work_service,
            subject_strategy=subject_strategy,
            data_fetcher=data_fetcher,
            max_works_per_author=max_works_per_author,
        )

        # Create deduplicator and progress tracker
        deduplicator = MatchResultDeduplicator()
        progress_tracker = ProgressTracker()

        return {
            "author_fetcher": data_fetcher,
            "ingestion_uow": uow,
            "deduplicator": deduplicator,
            "progress_tracker": progress_tracker,
        }

    @staticmethod
    def create(
        session: Session,
        data_source: BaseDataSource,
        author_limit: int | None = None,
        max_works_per_author: int | None = None,
    ) -> IngestStage:
        """Create a fully configured IngestStage.

        Parameters
        ----------
        session : Session
            Database session.
        data_source : BaseDataSource
            External data source for fetching author data.
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
        max_works_per_author : int | None
            Maximum number of works to fetch per author (None = no limit).
            This limits both work keys fetched and work metadata fetched for subjects.

        Returns
        -------
        IngestStage
            Fully configured ingest stage instance.
        """
        components = IngestStageFactory.create_components(
            session=session,
            data_source=data_source,
            author_limit=author_limit,
            max_works_per_author=max_works_per_author,
        )

        return IngestStage(
            author_fetcher=components["author_fetcher"],
            ingestion_uow=components["ingestion_uow"],
            deduplicator=components["deduplicator"],
            progress_tracker=components["progress_tracker"],
            author_limit=author_limit,
        )

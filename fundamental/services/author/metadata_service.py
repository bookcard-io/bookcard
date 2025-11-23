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

"""Author metadata service for external data fetching.

Follows Single Responsibility Principle by focusing solely on metadata fetching.
"""

from sqlmodel import Session

from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.author.helpers import ensure_active_library
from fundamental.services.author_exceptions import AuthorMetadataFetchError
from fundamental.services.config_service import LibraryService
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.ingest import (
    IngestStage,
    IngestStageFactory,
)
from fundamental.services.library_scanning.pipeline.ingest_components import (
    AuthorDataFetcher,
)
from fundamental.services.library_scanning.scan_factories import (
    PipelineContextFactory,
)


class AuthorMetadataService:
    """Service for fetching author metadata from external sources.

    Handles fetching and updating metadata for authors.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library_service: LibraryService,
    ) -> None:
        """Initialize author metadata service.

        Parameters
        ----------
        session : Session
            Database session.
        library_service : LibraryService
            Library service for active library management.
        """
        self._session = session
        self._library_service = library_service

    def fetch_author_metadata(
        self,
        openlibrary_key: str,
    ) -> dict[str, object]:
        """Fetch and update metadata for a single author.

        Triggers the ingest stage of the pipeline for this author only.
        Fetches latest biography, metadata, subjects, etc. from OpenLibrary.

        Parameters
        ----------
        openlibrary_key : str
            OpenLibrary key (e.g., "OL23919A").

        Returns
        -------
        dict[str, object]
            Result dictionary with success status, message, and stats.

        Raises
        ------
        AuthorMetadataFetchError
            If fetch fails.
        NoActiveLibraryError
            If no active library exists.
        """
        active_library = ensure_active_library(self._library_service)

        # Create data source
        data_source = DataSourceRegistry.create_source("openlibrary")

        # Create pipeline context
        def noop_progress(
            _progress: float, _metadata: dict[str, object] | None = None
        ) -> None:
            """No-op progress callback."""

        library_repo = LibraryRepository(self._session)
        context_factory = PipelineContextFactory(library_repo)  # type: ignore[arg-type]
        # active_library.id is guaranteed to be int by ensure_active_library
        library_id: int = active_library.id  # type: ignore[assignment]
        context = context_factory.create_context(
            library_id=library_id,
            session=self._session,
            data_source=data_source,
            progress_callback=noop_progress,
        )

        # Fetch latest author data from OpenLibrary
        author_fetcher = AuthorDataFetcher(data_source)
        latest_author_data = author_fetcher.fetch_author(openlibrary_key)

        if not latest_author_data:
            msg = f"Could not fetch author data from OpenLibrary for key: {openlibrary_key}"
            raise AuthorMetadataFetchError(msg)

        # Create MatchResult for the author
        match_result = MatchResult(
            confidence_score=1.0,
            matched_entity=latest_author_data,
            match_method="manual_refresh",
            calibre_author_id=None,
        )

        # Create ingest stage components (configured for forced refresh - no restrictions)
        components = IngestStageFactory.create_components(
            session=self._session,
            data_source=data_source,
            max_works_per_author=None,  # No limit on works per author in forced refresh
        )
        # Create ingest stage with stale data settings set to None (always refresh)
        ingest_stage = IngestStage(
            author_fetcher=components["author_fetcher"],
            ingestion_uow=components["ingestion_uow"],
            deduplicator=components["deduplicator"],
            progress_tracker=components["progress_tracker"],
            stale_data_max_age_days=None,  # Always refresh
            stale_data_refresh_interval_days=None,  # Always refresh
        )

        # Set the match result in context
        context.match_results = [match_result]

        # Execute ingest stage
        result = ingest_stage.execute(context)

        if not result.success:
            msg = f"Ingest failed: {result.message}"
            raise AuthorMetadataFetchError(msg)

        return {
            "success": True,
            "message": result.message,
            "stats": result.stats,
        }

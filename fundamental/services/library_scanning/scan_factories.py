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

"""Factories for creating scan pipeline components.

Uses Factory pattern to create data sources, pipeline stages, and contexts.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fundamental.services.library_scanning.pipeline.crawl import CrawlStage
from fundamental.services.library_scanning.pipeline.ingest import IngestStage
from fundamental.services.library_scanning.pipeline.link import LinkStage
from fundamental.services.library_scanning.pipeline.match import MatchStage

if TYPE_CHECKING:
    from sqlmodel import Session

from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.executor import PipelineExecutor
from fundamental.services.library_scanning.pipeline.score import ScoreStage
from fundamental.services.library_scanning.scan_configuration import (
    ScanConfiguration,
)


class DataSourceFactory(ABC):
    """Abstract factory for creating data sources.

    Follows Factory pattern to allow different data source creation strategies.
    """

    @abstractmethod
    def create_data_source(self, config: ScanConfiguration) -> BaseDataSource:
        """Create a data source based on configuration.

        Parameters
        ----------
        config : ScanConfiguration
            Scan configuration containing data source settings.

        Returns
        -------
        BaseDataSource
            Configured data source instance.
        """


class RegistryDataSourceFactory(DataSourceFactory):
    """Create data sources using the registry.

    Uses DataSourceRegistry to create data sources with configuration.
    """

    def create_data_source(self, config: ScanConfiguration) -> BaseDataSource:
        """Create data source from registry.

        Parameters
        ----------
        config : ScanConfiguration
            Scan configuration containing data source name and settings.

        Returns
        -------
        BaseDataSource
            Configured data source instance.
        """
        kwargs: dict[str, Any] = {}
        if config.rate_limit_delay is not None:
            kwargs["rate_limit_delay"] = config.rate_limit_delay

        return DataSourceRegistry.create_source(
            config.data_source_name,
            **kwargs,
        )


class PipelineFactory(ABC):
    """Abstract factory for creating pipeline stages and executor.

    Follows Factory pattern to allow different pipeline configurations.
    """

    @abstractmethod
    def create_stages(
        self, config: ScanConfiguration
    ) -> list[Any]:  # list[PipelineStage] but avoiding circular import
        """Create pipeline stages based on configuration.

        Parameters
        ----------
        config : ScanConfiguration
            Scan configuration for stage setup.

        Returns
        -------
        list[PipelineStage]
            List of configured pipeline stages.
        """

    @abstractmethod
    def create_executor(
        self,
        stages: list[Any],  # list[PipelineStage]
        progress_callback: Callable[[float, dict[str, Any] | None], None] | None = None,
    ) -> PipelineExecutor:
        """Create pipeline executor.

        Parameters
        ----------
        stages : list[PipelineStage]
            List of pipeline stages.
        progress_callback : Callable
            Progress callback function.

        Returns
        -------
        PipelineExecutor
            Configured pipeline executor.
        """


class StandardPipelineFactory(PipelineFactory):
    """Standard implementation of pipeline factory.

    Creates the standard pipeline stages used for library scanning.
    """

    def create_stages(
        self, config: ScanConfiguration
    ) -> list[Any]:  # list[PipelineStage]
        """Create standard pipeline stages.

        Parameters
        ----------
        config : ScanConfiguration
            Scan configuration for stage setup.

        Returns
        -------
        list[PipelineStage]
            List of configured pipeline stages.
        """
        # Build ingest stage kwargs from config
        ingest_kwargs: dict[str, Any] = {}
        if config.stale_data_max_age_days is not None:
            ingest_kwargs["stale_data_max_age_days"] = config.stale_data_max_age_days
        if config.stale_data_refresh_interval_days is not None:
            ingest_kwargs["stale_data_refresh_interval_days"] = (
                config.stale_data_refresh_interval_days
            )
        if config.max_works_per_author is not None:
            ingest_kwargs["max_works_per_author"] = config.max_works_per_author

        # Build match stage kwargs from config
        match_kwargs: dict[str, Any] = {}
        if config.stale_data_max_age_days is not None:
            match_kwargs["stale_data_max_age_days"] = (
                None  # config.stale_data_max_age_days
            )

        # Build score stage kwargs from config
        score_kwargs: dict[str, Any] = {}
        if config.stale_data_max_age_days is not None:
            score_kwargs["stale_data_max_age_days"] = (
                None  # config.stale_data_max_age_days
            )

        # Note: MatchStage makes API calls via context.data_source.search_author()
        # The data source is already configured with rate limiting from provider config
        # in the orchestrator, so MatchStage will respect those limits automatically.
        return [
            CrawlStage(),  # Only reads from Calibre DB, no API calls
            MatchStage(
                **match_kwargs
            ),  # Makes API calls via data_source.search_author()
            IngestStage(
                **ingest_kwargs
            ),  # Makes API calls via data_source.get_author()
            LinkStage(),  # Only database operations, no API calls
            ScoreStage(**score_kwargs),  # Only database operations, no API calls
        ]

    def create_executor(
        self,
        stages: list[Any],  # list[PipelineStage]
        progress_callback: Callable[[float, dict[str, Any] | None], None] | None = None,
    ) -> PipelineExecutor:
        """Create pipeline executor with stages.

        Parameters
        ----------
        stages : list[PipelineStage]
            List of pipeline stages.
        progress_callback : Callable | None
            Progress callback function (accepts progress and optional metadata).

        Returns
        -------
        PipelineExecutor
            Configured pipeline executor.

        Note
        ----
        The PipelineExecutor expects Callable[[float], None] but actually
        calls it with two arguments. We create a wrapper to adapt the signature.
        """
        # Note: PipelineExecutor type annotation says Callable[[float], None]
        # but it actually calls the callback with (float, dict) in _create_progress_callback.
        # We pass the callback directly and let the executor handle it.
        # The type mismatch is in the executor's annotation, not our code.
        return PipelineExecutor(
            stages=stages,
            progress_callback=progress_callback,  # type: ignore[arg-type]
        )


class PipelineContextFactory:
    """Factory for creating pipeline contexts.

    Handles creation of PipelineContext with proper library loading.
    """

    def __init__(self, library_repo: LibraryRepository) -> None:
        """Initialize context factory.

        Parameters
        ----------
        library_repo : LibraryRepository
            Repository for loading library data.
        """
        self.library_repo = library_repo

    def create_context(
        self,
        library_id: int,
        session: "Session",
        data_source: BaseDataSource,
        progress_callback: Callable[[float, dict[str, Any] | None], None],
    ) -> PipelineContext:
        """Create pipeline context.

        Parameters
        ----------
        library_id : int
            Library ID to scan.
        session : Session
            Database session.
        data_source : BaseDataSource
            Data source for external API access.
        progress_callback : Callable
            Progress callback function.

        Returns
        -------
        PipelineContext
            Configured pipeline context.

        Raises
        ------
        ValueError
            If library is not found.
        """
        library = self.library_repo.get(library_id)
        if not library:
            error_msg = f"Library {library_id} not found"
            raise ValueError(error_msg)

        return PipelineContext(
            library_id=library_id,
            library=library,
            session=session,
            data_source=data_source,
            progress_callback=progress_callback,
        )

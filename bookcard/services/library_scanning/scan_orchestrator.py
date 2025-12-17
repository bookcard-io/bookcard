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

"""Library scan orchestrator.

Orchestrates the library scanning process by coordinating configuration,
data sources, pipeline creation, and execution.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlmodel import Session

from bookcard.services.library_scanning.scan_configuration import (
    ScanConfigurationProvider,
)
from bookcard.services.library_scanning.scan_factories import (
    DataSourceFactory,
    PipelineContextFactory,
    PipelineFactory,
)

logger = logging.getLogger(__name__)


class LibraryScanOrchestrator:
    """Orchestrate the library scanning process.

    Coordinates all components needed for a library scan:
    - Configuration loading
    - Data source creation
    - Pipeline creation
    - Context creation
    - Pipeline execution

    Follows Dependency Injection pattern - all dependencies are injected.
    """

    def __init__(
        self,
        config_provider: ScanConfigurationProvider,
        data_source_factory: DataSourceFactory,
        pipeline_factory: PipelineFactory,
        context_factory: PipelineContextFactory,
    ) -> None:
        """Initialize scan orchestrator.

        Parameters
        ----------
        config_provider : ScanConfigurationProvider
            Provider for scan configuration.
        data_source_factory : DataSourceFactory
            Factory for creating data sources.
        pipeline_factory : PipelineFactory
            Factory for creating pipeline stages and executor.
        context_factory : PipelineContextFactory
            Factory for creating pipeline contexts.
        """
        self.config_provider = config_provider
        self.data_source_factory = data_source_factory
        self.pipeline_factory = pipeline_factory
        self.context_factory = context_factory

    def scan_library(
        self,
        library_id: int,
        metadata: dict[str, Any],
        session: "Session",
        progress_callback: Callable[[float, dict[str, Any] | None], None] | None = None,
    ) -> dict[str, Any]:
        """Execute a library scan with the provided configuration.

        Parameters
        ----------
        library_id : int
            Library ID to scan.
        metadata : dict[str, Any]
            Task metadata containing optional data_source_config.
        session : Session
            Database session.
        progress_callback : Callable | None
            Optional progress callback function.

        Returns
        -------
        dict[str, Any]
            Scan result dictionary with success status and message.

        Raises
        ------
        ValueError
            If library is not found or provider is disabled.
        """
        # Get configuration
        config = self.config_provider.get_configuration(library_id, metadata)

        # Create data source
        data_source = self.data_source_factory.create_data_source(config)

        # Create pipeline context
        context = self.context_factory.create_context(
            library_id=config.library_id,
            session=session,
            data_source=data_source,
            progress_callback=progress_callback or (lambda _p, _m: None),
        )

        # Create and execute pipeline
        stages = self.pipeline_factory.create_stages(config)
        executor = self.pipeline_factory.create_executor(
            stages, progress_callback or (lambda _p, _m: None)
        )

        # Execute and return result
        result = executor.execute(context)

        # Log result
        if result["success"]:
            logger.info(
                "Library scan completed successfully for library %d", library_id
            )
        else:
            logger.warning(
                "Library scan completed with errors for library %d: %s",
                library_id,
                result.get("message", "Unknown error"),
            )

        return result

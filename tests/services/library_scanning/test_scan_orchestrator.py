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

"""Tests for scan orchestrator to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.executor import PipelineExecutor
from bookcard.services.library_scanning.scan_configuration import ScanConfiguration
from bookcard.services.library_scanning.scan_factories import (
    DataSourceFactory,
    PipelineContextFactory,
    PipelineFactory,
)
from bookcard.services.library_scanning.scan_orchestrator import (
    LibraryScanOrchestrator,
)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Create a mock configuration provider."""
    provider = MagicMock()
    provider.get_configuration.return_value = ScanConfiguration(
        library_id=1,
        data_source_name="openlibrary",
    )
    return provider


@pytest.fixture
def mock_data_source_factory() -> MagicMock:
    """Create a mock data source factory."""
    factory = MagicMock(spec=DataSourceFactory)
    mock_source = MagicMock(spec=BaseDataSource)
    factory.create_data_source.return_value = mock_source
    return factory


@pytest.fixture
def mock_pipeline_factory() -> MagicMock:
    """Create a mock pipeline factory."""
    factory = MagicMock(spec=PipelineFactory)
    factory.create_stages.return_value = []
    mock_executor = MagicMock(spec=PipelineExecutor)
    mock_executor.execute.return_value = {"success": True}
    factory.create_executor.return_value = mock_executor
    return factory


@pytest.fixture
def mock_context_factory() -> MagicMock:
    """Create a mock context factory."""
    factory = MagicMock(spec=PipelineContextFactory)
    mock_context = MagicMock(spec=PipelineContext)
    mock_context.library_id = 1
    factory.create_context.return_value = mock_context
    return factory


@pytest.fixture
def orchestrator(
    mock_config_provider: MagicMock,
    mock_data_source_factory: MagicMock,
    mock_pipeline_factory: MagicMock,
    mock_context_factory: MagicMock,
) -> LibraryScanOrchestrator:
    """Create a LibraryScanOrchestrator with mocked dependencies."""
    return LibraryScanOrchestrator(
        config_provider=mock_config_provider,
        data_source_factory=mock_data_source_factory,
        pipeline_factory=mock_pipeline_factory,
        context_factory=mock_context_factory,
    )


class TestLibraryScanOrchestrator:
    """Test LibraryScanOrchestrator."""

    def test_init_stores_dependencies(
        self,
        mock_config_provider: MagicMock,
        mock_data_source_factory: MagicMock,
        mock_pipeline_factory: MagicMock,
        mock_context_factory: MagicMock,
    ) -> None:
        """Test __init__ stores all dependencies."""
        orchestrator = LibraryScanOrchestrator(
            config_provider=mock_config_provider,
            data_source_factory=mock_data_source_factory,
            pipeline_factory=mock_pipeline_factory,
            context_factory=mock_context_factory,
        )

        assert orchestrator.config_provider == mock_config_provider
        assert orchestrator.data_source_factory == mock_data_source_factory
        assert orchestrator.pipeline_factory == mock_pipeline_factory
        assert orchestrator.context_factory == mock_context_factory

    def test_scan_library_success(
        self,
        orchestrator: LibraryScanOrchestrator,
        mock_config_provider: MagicMock,
        mock_data_source_factory: MagicMock,
        mock_pipeline_factory: MagicMock,
        mock_context_factory: MagicMock,
    ) -> None:
        """Test scan_library successfully executes scan."""
        mock_session = MagicMock()
        metadata = {}

        result = orchestrator.scan_library(
            library_id=1,
            metadata=metadata,
            session=mock_session,
        )

        assert result == {"success": True}
        mock_config_provider.get_configuration.assert_called_once_with(1, metadata)
        mock_data_source_factory.create_data_source.assert_called_once()
        mock_pipeline_factory.create_stages.assert_called_once()
        mock_pipeline_factory.create_executor.assert_called_once()
        mock_context_factory.create_context.assert_called_once()

    def test_scan_library_with_progress_callback(
        self,
        orchestrator: LibraryScanOrchestrator,
    ) -> None:
        """Test scan_library with progress callback."""
        mock_session = MagicMock()
        metadata = {}
        callback = MagicMock()

        result = orchestrator.scan_library(
            library_id=1,
            metadata=metadata,
            session=mock_session,
            progress_callback=callback,
        )

        assert result == {"success": True}
        # Verify callback was passed to context factory
        call_args = orchestrator.context_factory.create_context.call_args  # type: ignore[attr-defined]
        assert call_args[1]["progress_callback"] == callback

    def test_scan_library_without_progress_callback(
        self,
        orchestrator: LibraryScanOrchestrator,
    ) -> None:
        """Test scan_library without progress callback creates default."""
        mock_session = MagicMock()
        metadata = {}

        result = orchestrator.scan_library(
            library_id=1,
            metadata=metadata,
            session=mock_session,
            progress_callback=None,
        )

        assert result == {"success": True}
        # Verify default callback was created
        call_args = orchestrator.context_factory.create_context.call_args  # type: ignore[attr-defined]
        assert call_args[1]["progress_callback"] is not None

    def test_scan_library_with_failure_result(
        self,
        mock_config_provider: MagicMock,
        mock_data_source_factory: MagicMock,
        mock_pipeline_factory: MagicMock,
        mock_context_factory: MagicMock,
    ) -> None:
        """Test scan_library handles failure result."""
        mock_executor = MagicMock(spec=PipelineExecutor)
        mock_executor.execute.return_value = {
            "success": False,
            "message": "Test error",
        }
        mock_pipeline_factory.create_executor.return_value = mock_executor

        orchestrator = LibraryScanOrchestrator(
            config_provider=mock_config_provider,
            data_source_factory=mock_data_source_factory,
            pipeline_factory=mock_pipeline_factory,
            context_factory=mock_context_factory,
        )

        mock_session = MagicMock()
        result = orchestrator.scan_library(
            library_id=1,
            metadata={},
            session=mock_session,
        )

        assert result["success"] is False
        assert result["message"] == "Test error"

    def test_scan_library_with_unknown_error_message(
        self,
        mock_config_provider: MagicMock,
        mock_data_source_factory: MagicMock,
        mock_pipeline_factory: MagicMock,
        mock_context_factory: MagicMock,
    ) -> None:
        """Test scan_library handles result without message."""
        mock_executor = MagicMock(spec=PipelineExecutor)
        mock_executor.execute.return_value = {"success": False}
        mock_pipeline_factory.create_executor.return_value = mock_executor

        orchestrator = LibraryScanOrchestrator(
            config_provider=mock_config_provider,
            data_source_factory=mock_data_source_factory,
            pipeline_factory=mock_pipeline_factory,
            context_factory=mock_context_factory,
        )

        mock_session = MagicMock()
        result = orchestrator.scan_library(
            library_id=1,
            metadata={},
            session=mock_session,
        )

        assert result["success"] is False

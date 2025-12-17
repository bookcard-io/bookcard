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

"""Tests for scan factories to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.executor import PipelineExecutor
from bookcard.services.library_scanning.scan_configuration import ScanConfiguration
from bookcard.services.library_scanning.scan_factories import (
    PipelineContextFactory,
    RegistryDataSourceFactory,
    StandardPipelineFactory,
)


class TestRegistryDataSourceFactory:
    """Test RegistryDataSourceFactory."""

    @patch("bookcard.services.library_scanning.scan_factories.DataSourceRegistry")
    def test_create_data_source_with_rate_limit(self, mock_registry: MagicMock) -> None:
        """Test create_data_source with rate_limit_delay."""
        mock_source = MagicMock(spec=BaseDataSource)
        mock_registry.create_source.return_value = mock_source

        factory = RegistryDataSourceFactory()
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
            rate_limit_delay=1.5,
        )

        result = factory.create_data_source(config)

        assert result == mock_source
        mock_registry.create_source.assert_called_once_with(
            "openlibrary", rate_limit_delay=1.5
        )

    @patch("bookcard.services.library_scanning.scan_factories.DataSourceRegistry")
    def test_create_data_source_without_rate_limit(
        self, mock_registry: MagicMock
    ) -> None:
        """Test create_data_source without rate_limit_delay."""
        mock_source = MagicMock(spec=BaseDataSource)
        mock_registry.create_source.return_value = mock_source

        factory = RegistryDataSourceFactory()
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
            rate_limit_delay=None,
        )

        result = factory.create_data_source(config)

        assert result == mock_source
        mock_registry.create_source.assert_called_once_with("openlibrary")


class TestStandardPipelineFactory:
    """Test StandardPipelineFactory."""

    def test_create_stages_with_all_config(self) -> None:
        """Test create_stages with all configuration values."""
        factory = StandardPipelineFactory()
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
            stale_data_max_age_days=30,
            stale_data_refresh_interval_days=7,
            max_works_per_author=100,
        )

        stages = factory.create_stages(config)

        assert len(stages) == 6
        # Verify ingest stage has kwargs
        ingest_stage = stages[2]
        assert hasattr(ingest_stage, "_stale_data_max_age_days") or hasattr(
            ingest_stage, "stale_data_max_age_days"
        )

    def test_create_stages_with_partial_config(self) -> None:
        """Test create_stages with partial configuration."""
        factory = StandardPipelineFactory()
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
            stale_data_max_age_days=30,
        )

        stages = factory.create_stages(config)

        assert len(stages) == 6

    def test_create_stages_with_no_config(self) -> None:
        """Test create_stages with minimal configuration."""
        factory = StandardPipelineFactory()
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
        )

        stages = factory.create_stages(config)

        assert len(stages) == 6

    def test_create_executor_with_callback(self) -> None:
        """Test create_executor with progress callback."""
        factory = StandardPipelineFactory()
        stages = []
        callback = MagicMock()

        executor = factory.create_executor(stages, callback)

        assert isinstance(executor, PipelineExecutor)
        assert executor.stages == stages

    def test_create_executor_without_callback(self) -> None:
        """Test create_executor without progress callback."""
        factory = StandardPipelineFactory()
        stages = []

        executor = factory.create_executor(stages, None)

        assert isinstance(executor, PipelineExecutor)
        assert executor.stages == stages


class TestPipelineContextFactory:
    """Test PipelineContextFactory."""

    @pytest.fixture
    def mock_library_repo(self) -> MagicMock:
        """Create a mock library repository."""
        repo = MagicMock(spec=LibraryRepository)
        library = MagicMock(spec=Library)
        library.id = 1
        repo.get.return_value = library
        return repo

    @pytest.fixture
    def factory(self, mock_library_repo: MagicMock) -> PipelineContextFactory:
        """Create a PipelineContextFactory."""
        return PipelineContextFactory(mock_library_repo)

    def test_init_stores_repo(self, mock_library_repo: MagicMock) -> None:
        """Test __init__ stores library repository."""
        factory = PipelineContextFactory(mock_library_repo)
        assert factory.library_repo == mock_library_repo

    def test_create_context_success(
        self,
        factory: PipelineContextFactory,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test create_context successfully creates context."""
        mock_session = MagicMock()
        mock_data_source = MagicMock(spec=BaseDataSource)
        callback = MagicMock()

        context = factory.create_context(
            library_id=1,
            session=mock_session,
            data_source=mock_data_source,
            progress_callback=callback,
        )

        assert isinstance(context, PipelineContext)
        assert context.library_id == 1
        mock_library_repo.get.assert_called_once_with(1)

    def test_create_context_library_not_found(
        self,
        factory: PipelineContextFactory,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test create_context raises ValueError when library not found."""
        mock_library_repo.get.return_value = None
        mock_session = MagicMock()
        mock_data_source = MagicMock(spec=BaseDataSource)
        callback = MagicMock()

        with pytest.raises(ValueError, match=r"Library 1 not found"):
            factory.create_context(
                library_id=1,
                session=mock_session,
                data_source=mock_data_source,
                progress_callback=callback,
            )

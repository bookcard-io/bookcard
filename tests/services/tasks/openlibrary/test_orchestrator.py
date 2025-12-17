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

"""Tests for OpenLibraryDumpIngestOrchestrator to achieve 100% coverage."""

from __future__ import annotations

import gzip
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.services.tasks.openlibrary.config import IngestionConfig
from bookcard.services.tasks.openlibrary.orchestrator import (
    OpenLibraryDumpIngestOrchestrator,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock database repository.

    Returns
    -------
    MagicMock
        Mock repository object.
    """
    return MagicMock()


@pytest.fixture
def mock_progress_reporter() -> MagicMock:
    """Create a mock progress reporter.

    Returns
    -------
    MagicMock
        Mock progress reporter object.
    """
    return MagicMock()


@pytest.fixture
def mock_cancellation_checker() -> MagicMock:
    """Create a mock cancellation checker.

    Returns
    -------
    MagicMock
        Mock cancellation checker object.
    """
    checker = MagicMock()
    checker.is_cancelled.return_value = False
    return checker


@pytest.fixture
def base_config() -> IngestionConfig:
    """Create base ingestion config.

    Returns
    -------
    IngestionConfig
        Base configuration.
    """
    return IngestionConfig(
        data_directory="/test/data",
        batch_size=10000,
        process_authors=True,
        process_works=True,
        process_editions=True,
    )


@pytest.fixture
def orchestrator(
    base_config: IngestionConfig,
    mock_repository: MagicMock,
    mock_progress_reporter: MagicMock,
    mock_cancellation_checker: MagicMock,
) -> OpenLibraryDumpIngestOrchestrator:
    """Create orchestrator instance.

    Parameters
    ----------
    base_config : IngestionConfig
        Base configuration.
    mock_repository : MagicMock
        Mock repository.
    mock_progress_reporter : MagicMock
        Mock progress reporter.
    mock_cancellation_checker : MagicMock
        Mock cancellation checker.

    Returns
    -------
    OpenLibraryDumpIngestOrchestrator
        Orchestrator instance.
    """
    return OpenLibraryDumpIngestOrchestrator(
        config=base_config,
        repository=mock_repository,
        progress_reporter=mock_progress_reporter,
        cancellation_checker=mock_cancellation_checker,
    )


def create_gzip_dump_file(file_path: Path, lines: list[str]) -> None:
    """Create a gzipped dump file for testing.

    Parameters
    ----------
    file_path : Path
        Path to create the file.
    lines : list[str]
        Lines to write to the file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


class TestOpenLibraryDumpIngestOrchestratorInit:
    """Test OpenLibraryDumpIngestOrchestrator initialization."""

    def test_init(
        self,
        base_config: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
    ) -> None:
        """Test orchestrator initialization.

        Parameters
        ----------
        base_config : IngestionConfig
            Base configuration.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        """
        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=base_config,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        assert orchestrator.config == base_config
        assert orchestrator.repository == mock_repository
        assert orchestrator.progress_reporter == mock_progress_reporter
        assert orchestrator.cancellation_checker == mock_cancellation_checker
        assert orchestrator.base_dir == Path(base_config.data_directory) / "openlibrary"
        assert orchestrator.dump_dir == orchestrator.base_dir / "dump"


class TestOpenLibraryDumpIngestOrchestratorRun:
    """Test OpenLibraryDumpIngestOrchestrator run method."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory.

        Parameters
        ----------
        tmp_path : Path
            Pytest temporary path fixture.

        Returns
        -------
        Path
            Temporary directory path.
        """
        return tmp_path

    @pytest.fixture
    def config_with_temp_dir(self, temp_dir: Path) -> IngestionConfig:
        """Create config with temporary directory.

        Parameters
        ----------
        temp_dir : Path
            Temporary directory path.

        Returns
        -------
        IngestionConfig
            Configuration with temp directory.
        """
        return IngestionConfig(
            data_directory=str(temp_dir),
            batch_size=2,  # Small batch for testing
            process_authors=True,
            process_works=True,
            process_editions=True,
        )

    @patch("bookcard.services.tasks.openlibrary.orchestrator.FileProcessor")
    @patch("bookcard.services.tasks.openlibrary.orchestrator.OpenLibraryDumpParser")
    def test_run_success_all_files(
        self,
        mock_parser_class: Mock,
        mock_file_processor_class: Mock,
        config_with_temp_dir: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful run with all file types.

        Parameters
        ----------
        mock_parser_class : Mock
            Mock parser class.
        mock_file_processor_class : Mock
            Mock file processor class.
        config_with_temp_dir : IngestionConfig
            Configuration with temp directory.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        temp_dir : Path
            Temporary directory path.
        """
        mock_file_processor = MagicMock()
        mock_file_processor.process_file.side_effect = [
            {"records": 10},  # authors
            {"records": 20},  # works
            {"records": 30},  # editions
        ]
        mock_file_processor_class.return_value = mock_file_processor

        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config_with_temp_dir,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        # Create dump files
        authors_file = orchestrator.dump_dir / "ol_dump_authors_latest.txt.gz"
        works_file = orchestrator.dump_dir / "ol_dump_works_latest.txt.gz"
        editions_file = orchestrator.dump_dir / "ol_dump_editions_latest.txt.gz"
        create_gzip_dump_file(
            authors_file, ["author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{}"]
        )
        create_gzip_dump_file(
            works_file, ["work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{}"]
        )
        create_gzip_dump_file(
            editions_file, ["edition\t/editions/OL1E\t1\t2008-04-01T00:00:00\t{}"]
        )

        orchestrator.run()

        assert mock_file_processor.process_file.call_count == 3
        mock_progress_reporter.report.assert_called()
        final_call = mock_progress_reporter.report.call_args_list[-1]
        assert final_call[0][0] == 1.0
        assert "stats" in final_call[0][1]

    @patch("bookcard.services.tasks.openlibrary.orchestrator.FileProcessor")
    @patch("bookcard.services.tasks.openlibrary.orchestrator.OpenLibraryDumpParser")
    def test_run_authors_only(
        self,
        mock_parser_class: Mock,
        mock_file_processor_class: Mock,
        temp_dir: Path,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
    ) -> None:
        """Test run with authors only.

        Parameters
        ----------
        mock_parser_class : Mock
            Mock parser class.
        mock_file_processor_class : Mock
            Mock file processor class.
        temp_dir : Path
            Temporary directory path.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        """
        config = IngestionConfig(
            data_directory=str(temp_dir),
            batch_size=2,  # Small batch for testing
            process_authors=True,
            process_works=False,
            process_editions=False,
        )

        mock_file_processor = MagicMock()
        mock_file_processor.process_file.return_value = {"records": 10}
        mock_file_processor_class.return_value = mock_file_processor

        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        authors_file = orchestrator.dump_dir / "ol_dump_authors_latest.txt.gz"
        create_gzip_dump_file(
            authors_file, ["author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{}"]
        )

        orchestrator.run()

        assert mock_file_processor.process_file.call_count == 1

    @patch("bookcard.services.tasks.openlibrary.orchestrator.FileProcessor")
    @patch("bookcard.services.tasks.openlibrary.orchestrator.OpenLibraryDumpParser")
    def test_run_editions_file_missing(
        self,
        mock_parser_class: Mock,
        mock_file_processor_class: Mock,
        config_with_temp_dir: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test run when editions file is missing.

        Parameters
        ----------
        mock_parser_class : Mock
            Mock parser class.
        mock_file_processor_class : Mock
            Mock file processor class.
        config_with_temp_dir : IngestionConfig
            Configuration with temp directory.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        temp_dir : Path
            Temporary directory path.
        """
        mock_file_processor = MagicMock()
        mock_file_processor.process_file.side_effect = [
            {"records": 10},  # authors
            {"records": 20},  # works
        ]
        mock_file_processor_class.return_value = mock_file_processor

        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config_with_temp_dir,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        authors_file = orchestrator.dump_dir / "ol_dump_authors_latest.txt.gz"
        works_file = orchestrator.dump_dir / "ol_dump_works_latest.txt.gz"
        create_gzip_dump_file(
            authors_file, ["author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{}"]
        )
        create_gzip_dump_file(
            works_file, ["work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{}"]
        )
        # Don't create editions file

        orchestrator.run()

        # Should handle missing editions file gracefully
        assert mock_file_processor.process_file.call_count == 2


class TestOpenLibraryDumpIngestOrchestratorSetupDirectories:
    """Test OpenLibraryDumpIngestOrchestrator._setup_directories method."""

    def test_setup_directories(
        self,
        base_config: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test directory setup.

        Parameters
        ----------
        base_config : IngestionConfig
            Base configuration.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        tmp_path : Path
            Temporary directory path.
        """
        config = IngestionConfig(
            data_directory=str(tmp_path),
            batch_size=base_config.batch_size,
            process_authors=base_config.process_authors,
            process_works=base_config.process_works,
            process_editions=base_config.process_editions,
        )
        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        orchestrator._setup_directories()

        assert orchestrator.base_dir.exists()
        assert orchestrator.dump_dir.exists()


class TestOpenLibraryDumpIngestOrchestratorClearExistingData:
    """Test OpenLibraryDumpIngestOrchestrator._clear_existing_data method."""

    @pytest.mark.parametrize(
        ("process_authors", "process_works", "process_editions", "expected_tables"),
        [
            (
                True,
                True,
                True,
                [
                    "openlibrary_authors",
                    "openlibrary_works",
                    "openlibrary_author_works",
                    "openlibrary_editions",
                    "openlibrary_edition_isbns",
                ],
            ),
            (True, False, False, ["openlibrary_authors"]),
            (False, True, False, ["openlibrary_works", "openlibrary_author_works"]),
            (False, False, True, ["openlibrary_editions", "openlibrary_edition_isbns"]),
        ],
    )
    def test_clear_existing_data(
        self,
        base_config: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
        expected_tables: list[str],
    ) -> None:
        """Test clearing existing data.

        Parameters
        ----------
        base_config : IngestionConfig
            Base configuration.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        expected_tables : list[str]
            Expected tables to truncate.
        """
        config = IngestionConfig(
            data_directory=base_config.data_directory,
            batch_size=base_config.batch_size,
            process_authors=process_authors,
            process_works=process_works,
            process_editions=process_editions,
        )
        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        orchestrator._clear_existing_data()

        mock_progress_reporter.report.assert_called_with(
            0.0, {"status": "Clearing existing data..."}
        )
        if expected_tables:
            mock_repository.truncate_tables.assert_called_once()
            call_args = mock_repository.truncate_tables.call_args[0][0]
            assert set(call_args) == set(expected_tables)


class TestOpenLibraryDumpIngestOrchestratorValidateEnabledFileTypes:
    """Test OpenLibraryDumpIngestOrchestrator._validate_enabled_file_types method."""

    @pytest.mark.parametrize(
        ("process_authors", "process_works", "process_editions", "should_raise"),
        [
            (True, True, True, False),
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ],
    )
    def test_validate_enabled_file_types(
        self,
        base_config: IngestionConfig,
        mock_repository: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
        should_raise: bool,
    ) -> None:
        """Test validation of enabled file types.

        Parameters
        ----------
        base_config : IngestionConfig
            Base configuration.
        mock_repository : MagicMock
            Mock repository.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        should_raise : bool
            Whether ValueError should be raised.
        """
        config = IngestionConfig(
            data_directory=base_config.data_directory,
            batch_size=base_config.batch_size,
            process_authors=process_authors,
            process_works=process_works,
            process_editions=process_editions,
        )
        orchestrator = OpenLibraryDumpIngestOrchestrator(
            config=config,
            repository=mock_repository,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
        )

        if should_raise:
            with pytest.raises(
                ValueError, match="At least one file type must be enabled"
            ):
                orchestrator._validate_enabled_file_types()
        else:
            orchestrator._validate_enabled_file_types()  # Should not raise

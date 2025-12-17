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

"""Tests for FileProcessor to achieve 100% coverage."""

from __future__ import annotations

import gzip
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

from bookcard.models.openlibrary import OpenLibraryAuthor
from bookcard.services.tasks.openlibrary.batch import BatchProcessor
from bookcard.services.tasks.openlibrary.config import IngestionConfig
from bookcard.services.tasks.openlibrary.file_processor import FileProcessor
from bookcard.services.tasks.openlibrary.models import DumpRecord
from bookcard.services.tasks.openlibrary.parser import DumpFileParser
from bookcard.services.tasks.openlibrary.processors import RecordProcessor


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


class MockRecordProcessor(RecordProcessor[OpenLibraryAuthor]):
    """Mock record processor for testing."""

    def __init__(self, can_process_result: bool = True) -> None:
        """Initialize mock processor.

        Parameters
        ----------
        can_process_result : bool
            Whether can_process should return True.
        """
        self.can_process_result = can_process_result
        self.processed_records: list[DumpRecord] = []

    def can_process(self, record: DumpRecord) -> bool:
        """Check if this processor can handle the record.

        Parameters
        ----------
        record : DumpRecord
            Record to check.

        Returns
        -------
        bool
            True if this processor can handle the record.
        """
        return self.can_process_result

    def process_record(self, record: DumpRecord) -> list[OpenLibraryAuthor]:
        """Process a single record into model objects.

        Parameters
        ----------
        record : DumpRecord
            Record to process.

        Returns
        -------
        list[OpenLibraryAuthor]
            List of model objects created from the record.
        """
        self.processed_records.append(record)
        return [
            OpenLibraryAuthor(
                type=record.record_type,
                key=record.key,
                revision=record.revision,
                last_modified=record.last_modified,
                data=record.data,
            )
        ]


class MockParser(DumpFileParser):
    """Mock parser for testing."""

    def __init__(self, records: list[DumpRecord] | None = None) -> None:
        """Initialize mock parser.

        Parameters
        ----------
        records : list[DumpRecord] | None
            Records to yield when parsing.
        """
        self.records = records or []

    def parse_line(self, line: str) -> DumpRecord | None:
        """Parse a single line from dump file.

        Parameters
        ----------
        line : str
            Line from dump file.

        Returns
        -------
        DumpRecord | None
            Parsed record or None if line is invalid.
        """
        return None

    def parse_file(self, file_path: Path) -> Iterator[DumpRecord]:
        """Parse entire file and yield records.

        Parameters
        ----------
        file_path : Path
            Path to dump file.

        Yields
        ------
        DumpRecord
            Parsed records from the file.
        """
        yield from self.records


@pytest.fixture
def mock_parser() -> MockParser:
    """Create a mock parser.

    Returns
    -------
    MockParser
        Mock parser instance.
    """
    return MockParser()


@pytest.fixture
def mock_processor() -> MockRecordProcessor:
    """Create a mock processor.

    Returns
    -------
    MockRecordProcessor
        Mock processor instance.
    """
    return MockRecordProcessor()


@pytest.fixture
def mock_batch_processor() -> MagicMock:
    """Create a mock batch processor.

    Returns
    -------
    MagicMock
        Mock batch processor.
    """
    return MagicMock(spec=BatchProcessor)


@pytest.fixture
def mock_progress_reporter() -> MagicMock:
    """Create a mock progress reporter.

    Returns
    -------
    MagicMock
        Mock progress reporter.
    """
    return MagicMock()


@pytest.fixture
def mock_cancellation_checker() -> MagicMock:
    """Create a mock cancellation checker.

    Returns
    -------
    MagicMock
        Mock cancellation checker.
    """
    checker = MagicMock()
    checker.is_cancelled.return_value = False
    return checker


@pytest.fixture
def config() -> IngestionConfig:
    """Create ingestion config.

    Returns
    -------
    IngestionConfig
        Configuration instance.
    """
    return IngestionConfig(
        data_directory="/test/data",
        batch_size=10000,
        progress_update_interval=2,  # Small interval for testing
    )


@pytest.fixture
def file_processor(
    mock_parser: MockParser,
    mock_processor: MockRecordProcessor,
    mock_batch_processor: MagicMock,
    mock_progress_reporter: MagicMock,
    mock_cancellation_checker: MagicMock,
    config: IngestionConfig,
) -> FileProcessor:
    """Create file processor instance.

    Parameters
    ----------
    mock_parser : MockParser
        Mock parser.
    mock_processor : MockRecordProcessor
        Mock processor.
    mock_batch_processor : MagicMock
        Mock batch processor.
    mock_progress_reporter : MagicMock
        Mock progress reporter.
    mock_cancellation_checker : MagicMock
        Mock cancellation checker.
    config : IngestionConfig
        Configuration.

    Returns
    -------
    FileProcessor
        File processor instance.
    """
    batch_processors = {OpenLibraryAuthor: mock_batch_processor}
    return FileProcessor(
        parser=mock_parser,
        processors=[mock_processor],
        batch_processors=batch_processors,
        progress_reporter=mock_progress_reporter,
        cancellation_checker=mock_cancellation_checker,
        config=config,
    )


class TestFileProcessorInit:
    """Test FileProcessor initialization."""

    def test_init(
        self,
        mock_parser: MockParser,
        mock_processor: MockRecordProcessor,
        mock_batch_processor: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        config: IngestionConfig,
    ) -> None:
        """Test file processor initialization.

        Parameters
        ----------
        mock_parser : MockParser
            Mock parser.
        mock_processor : MockRecordProcessor
            Mock processor.
        mock_batch_processor : MagicMock
            Mock batch processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        config : IngestionConfig
            Configuration.
        """
        batch_processors = {OpenLibraryAuthor: mock_batch_processor}
        processor = FileProcessor(
            parser=mock_parser,
            processors=[mock_processor],
            batch_processors=batch_processors,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
            config=config,
        )

        assert processor.parser == mock_parser
        assert processor.processors == [mock_processor]
        assert processor.batch_processors == batch_processors
        assert processor.progress_reporter == mock_progress_reporter
        assert processor.cancellation_checker == mock_cancellation_checker
        assert processor.config == config


class TestFileProcessorRaiseCancelled:
    """Test FileProcessor._raise_cancelled method."""

    def test_raise_cancelled(
        self,
        file_processor: FileProcessor,
    ) -> None:
        """Test _raise_cancelled raises InterruptedError.

        Parameters
        ----------
        file_processor : FileProcessor
            File processor instance.
        """
        with pytest.raises(InterruptedError, match="Task cancelled"):
            file_processor._raise_cancelled()


class TestFileProcessorProcessFile:
    """Test FileProcessor.process_file method."""

    def test_process_file_success(
        self,
        file_processor: FileProcessor,
        mock_parser: MockParser,
        mock_processor: MockRecordProcessor,
        mock_batch_processor: MagicMock,
        mock_progress_reporter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful file processing.

        Parameters
        ----------
        file_processor : FileProcessor
            File processor instance.
        mock_parser : MockParser
            Mock parser.
        mock_processor : MockRecordProcessor
            Mock processor.
        mock_batch_processor : MagicMock
            Mock batch processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
            DumpRecord(
                record_type="author",
                key="/authors/OL2A",
                revision=2,
                last_modified=None,
                data={"name": "Author 2"},
            ),
        ]
        mock_parser.records = records

        stats = file_processor.process_file(file_path, "authors")

        assert stats["records"] == 2
        assert len(mock_processor.processed_records) == 2
        assert mock_batch_processor.add.call_count == 2
        mock_batch_processor.flush.assert_called_once()

    def test_process_file_with_progress_update(
        self,
        mock_parser: MockParser,
        mock_processor: MockRecordProcessor,
        mock_batch_processor: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test file processing with progress updates.

        Parameters
        ----------
        mock_parser : MockParser
            Mock parser.
        mock_processor : MockRecordProcessor
            Mock processor.
        mock_batch_processor : MagicMock
            Mock batch processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        tmp_path : Path
            Temporary directory path.
        """
        # Create config with small progress interval
        config = IngestionConfig(
            data_directory="/test/data",
            batch_size=10000,
            progress_update_interval=2,  # Small interval for testing
        )
        batch_processors = {OpenLibraryAuthor: mock_batch_processor}
        file_processor = FileProcessor(
            parser=mock_parser,
            processors=[mock_processor],
            batch_processors=batch_processors,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
            config=config,
        )

        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key=f"/authors/OL{i}A",
                revision=i,
                last_modified=None,
                data={"name": f"Author {i}"},
            )
            for i in range(1, 5)  # 4 records, should trigger progress at 2 and 4
        ]
        mock_parser.records = records

        stats = file_processor.process_file(file_path, "authors")

        assert stats["records"] == 4
        # Progress should be reported at 2 and 4 records
        assert mock_progress_reporter.report.call_count == 2

    def test_process_file_cancelled(
        self,
        file_processor: FileProcessor,
        mock_parser: MockParser,
        mock_cancellation_checker: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test file processing with cancellation.

        Parameters
        ----------
        file_processor : FileProcessor
            File processor instance.
        mock_parser : MockParser
            Mock parser.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
            DumpRecord(
                record_type="author",
                key="/authors/OL2A",
                revision=2,
                last_modified=None,
                data={"name": "Author 2"},
            ),
        ]
        mock_parser.records = records

        # Simulate cancellation during processing (after first record check)
        call_count = 0

        def is_cancelled() -> bool:
            nonlocal call_count
            call_count += 1
            # Return True on second call (during processing of first record)
            return call_count >= 2

        mock_cancellation_checker.is_cancelled.side_effect = is_cancelled

        with pytest.raises(InterruptedError, match="Task cancelled"):
            file_processor.process_file(file_path, "authors")

    def test_process_file_no_processor(
        self,
        mock_parser: MockParser,
        mock_batch_processor: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        config: IngestionConfig,
        tmp_path: Path,
    ) -> None:
        """Test file processing when no processor can handle record.

        Parameters
        ----------
        mock_parser : MockParser
            Mock parser.
        mock_batch_processor : MagicMock
            Mock batch processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        config : IngestionConfig
            Configuration.
        tmp_path : Path
            Temporary directory path.
        """
        processor = MockRecordProcessor(can_process_result=False)
        batch_processors = {OpenLibraryAuthor: mock_batch_processor}
        file_processor = FileProcessor(
            parser=mock_parser,
            processors=[processor],
            batch_processors=batch_processors,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
            config=config,
        )

        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
        ]
        mock_parser.records = records

        stats = file_processor.process_file(file_path, "authors")

        assert stats["records"] == 0
        mock_batch_processor.add.assert_not_called()

    def test_process_file_empty_models(
        self,
        mock_parser: MockParser,
        mock_batch_processor: MagicMock,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        config: IngestionConfig,
        tmp_path: Path,
    ) -> None:
        """Test file processing when processor returns empty models.

        Parameters
        ----------
        mock_parser : MockParser
            Mock parser.
        mock_batch_processor : MagicMock
            Mock batch processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        config : IngestionConfig
            Configuration.
        tmp_path : Path
            Temporary directory path.
        """

        class EmptyProcessor(MockRecordProcessor):
            """Processor that returns empty list."""

            def process_record(self, record: DumpRecord) -> list[OpenLibraryAuthor]:
                """Process record returning empty list.

                Parameters
                ----------
                record : DumpRecord
                    Record to process.

                Returns
                -------
                list[OpenLibraryAuthor]
                    Empty list.
                """
                return []

        processor = EmptyProcessor()
        batch_processors = {OpenLibraryAuthor: mock_batch_processor}
        file_processor = FileProcessor(
            parser=mock_parser,
            processors=[processor],
            batch_processors=batch_processors,
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
            config=config,
        )

        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
        ]
        mock_parser.records = records

        stats = file_processor.process_file(file_path, "authors")

        assert stats["records"] == 0
        # Should not try to add to batch when models is empty
        mock_batch_processor.add.assert_not_called()

    def test_process_file_model_type_not_in_batch_processors(
        self,
        mock_parser: MockParser,
        mock_processor: MockRecordProcessor,
        mock_progress_reporter: MagicMock,
        mock_cancellation_checker: MagicMock,
        config: IngestionConfig,
        tmp_path: Path,
    ) -> None:
        """Test file processing when model type not in batch processors.

        Parameters
        ----------
        mock_parser : MockParser
            Mock parser.
        mock_processor : MockRecordProcessor
            Mock processor.
        mock_progress_reporter : MagicMock
            Mock progress reporter.
        mock_cancellation_checker : MagicMock
            Mock cancellation checker.
        config : IngestionConfig
            Configuration.
        tmp_path : Path
            Temporary directory path.
        """
        # Use empty batch_processors dict
        file_processor = FileProcessor(
            parser=mock_parser,
            processors=[mock_processor],
            batch_processors={},
            progress_reporter=mock_progress_reporter,
            cancellation_checker=mock_cancellation_checker,
            config=config,
        )

        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
        ]
        mock_parser.records = records

        stats = file_processor.process_file(file_path, "authors")

        assert stats["records"] == 1
        # Should not add to batch when model type not in batch_processors

    def test_process_file_exception(
        self,
        file_processor: FileProcessor,
        mock_parser: MockParser,
        mock_batch_processor: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test file processing with exception.

        Parameters
        ----------
        file_processor : FileProcessor
            File processor instance.
        mock_parser : MockParser
            Mock parser.
        mock_batch_processor : MagicMock
            Mock batch processor.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        records = [
            DumpRecord(
                record_type="author",
                key="/authors/OL1A",
                revision=1,
                last_modified=None,
                data={"name": "Author 1"},
            ),
        ]
        mock_parser.records = records

        # Make batch processor raise exception
        mock_batch_processor.add.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            file_processor.process_file(file_path, "authors")

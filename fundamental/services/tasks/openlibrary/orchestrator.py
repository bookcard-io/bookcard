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

"""Orchestrator for OpenLibrary dump ingestion.

Coordinates the entire ingestion process following the Orchestrator pattern.
"""

import logging
from pathlib import Path

from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryEdition,
    OpenLibraryWork,
)
from fundamental.services.tasks.openlibrary.batch import (
    AuthorWorkBatchProcessor,
    BatchProcessor,
    IsbnBatchProcessor,
)
from fundamental.services.tasks.openlibrary.config import IngestionConfig
from fundamental.services.tasks.openlibrary.file_processor import FileProcessor
from fundamental.services.tasks.openlibrary.parser import OpenLibraryDumpParser
from fundamental.services.tasks.openlibrary.processors import (
    AuthorRecordProcessor,
    EditionRecordProcessor,
    WorkRecordProcessor,
)
from fundamental.services.tasks.openlibrary.protocols import DatabaseRepository
from fundamental.services.tasks.protocols import (
    CancellationChecker,
    ProgressReporter,
)

logger = logging.getLogger(__name__)


class OpenLibraryDumpIngestOrchestrator:
    """Orchestrates the entire ingestion process.

    Follows the Orchestrator pattern to coordinate all components
    of the ingestion process without implementing business logic itself.

    Parameters
    ----------
    config : IngestionConfig
        Ingestion configuration.
    repository : DatabaseRepository
        Database repository for operations.
    progress_reporter : ProgressReporter
        Progress reporter for updates.
    cancellation_checker : CancellationChecker
        Cancellation checker for task cancellation.
    """

    def __init__(
        self,
        config: IngestionConfig,
        repository: DatabaseRepository,
        progress_reporter: ProgressReporter,
        cancellation_checker: CancellationChecker,
    ) -> None:
        """Initialize orchestrator.

        Parameters
        ----------
        config : IngestionConfig
            Ingestion configuration.
        repository : DatabaseRepository
            Database repository for operations.
        progress_reporter : ProgressReporter
            Progress reporter for updates.
        cancellation_checker : CancellationChecker
            Cancellation checker for task cancellation.
        """
        self.config = config
        self.repository = repository
        self.progress_reporter = progress_reporter
        self.cancellation_checker = cancellation_checker

        # Setup file paths
        self.base_dir = Path(config.data_directory) / "openlibrary"
        self.dump_dir = self.base_dir / "dump"

    def run(self) -> None:
        """Execute the complete ingestion process.

        Raises
        ------
        ValueError
            If no file types are enabled for processing.
        Exception
            If ingestion fails.
        """
        self._setup_directories()
        self._clear_existing_data()
        self._validate_enabled_file_types()

        # Setup components
        parser = OpenLibraryDumpParser()

        # Create batch processors
        author_work_batch = AuthorWorkBatchProcessor(
            self.repository, self.config.batch_size
        )
        isbn_batch = IsbnBatchProcessor(self.repository, self.config.batch_size)

        batch_processors = {
            OpenLibraryAuthor: BatchProcessor(self.repository, self.config.batch_size),
            OpenLibraryWork: BatchProcessor(self.repository, self.config.batch_size),
            OpenLibraryEdition: BatchProcessor(self.repository, self.config.batch_size),
        }

        # Create record processors
        processors = []
        if self.config.process_authors:
            processors.append(AuthorRecordProcessor())
        if self.config.process_works:
            processors.append(WorkRecordProcessor(author_work_batch))
        if self.config.process_editions:
            processors.append(EditionRecordProcessor(isbn_batch))

        # Create file processor
        file_processor = FileProcessor(
            parser=parser,
            processors=processors,
            batch_processors=batch_processors,
            progress_reporter=self.progress_reporter,
            cancellation_checker=self.cancellation_checker,
            config=self.config,
        )

        # Process files
        total_stats = {}

        if self.config.process_authors:
            authors_file = self.dump_dir / "ol_dump_authors_latest.txt.gz"
            stats = file_processor.process_file(authors_file, "authors")
            total_stats["authors"] = stats["records"]

        if self.config.process_works:
            works_file = self.dump_dir / "ol_dump_works_latest.txt.gz"
            stats = file_processor.process_file(works_file, "works")
            total_stats["works"] = stats["records"]

        if self.config.process_editions:
            editions_file = self.dump_dir / "ol_dump_editions_latest.txt.gz"
            if editions_file.exists():
                stats = file_processor.process_file(editions_file, "editions")
                total_stats["editions"] = stats["records"]
            else:
                logger.warning("Editions file not found: %s", editions_file)

        # Final flush of relationship batches
        author_work_batch.flush()
        isbn_batch.flush()

        self.progress_reporter.report(
            1.0, {"status": "Completed", "stats": total_stats}
        )
        logger.info("Ingestion complete: %s", total_stats)

    def _setup_directories(self) -> None:
        """Create necessary directories."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.dump_dir.mkdir(parents=True, exist_ok=True)

    def _clear_existing_data(self) -> None:
        """Clear existing data for fresh ingestion."""
        self.progress_reporter.report(0.0, {"status": "Clearing existing data..."})

        tables_to_truncate = []
        if self.config.process_authors:
            tables_to_truncate.append("openlibrary_authors")
        if self.config.process_works:
            tables_to_truncate.extend(["openlibrary_works", "openlibrary_author_works"])
        if self.config.process_editions:
            tables_to_truncate.extend([
                "openlibrary_editions",
                "openlibrary_edition_isbns",
            ])

        if tables_to_truncate:
            self.repository.truncate_tables(tables_to_truncate)

    def _validate_enabled_file_types(self) -> None:
        """Validate that at least one file type is enabled.

        Raises
        ------
        ValueError
            If no file types are enabled.
        """
        enabled_count = sum([
            self.config.process_authors,
            self.config.process_works,
            self.config.process_editions,
        ])
        if enabled_count == 0:
            msg = "At least one file type must be enabled for processing"
            raise ValueError(msg)

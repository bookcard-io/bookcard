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

"""File processor for OpenLibrary dump ingestion.

Orchestrates processing of dump files using parsers and record processors.
"""

import logging
from pathlib import Path
from typing import Any

from fundamental.services.tasks.openlibrary.batch import BatchProcessor
from fundamental.services.tasks.openlibrary.config import IngestionConfig
from fundamental.services.tasks.openlibrary.parser import DumpFileParser
from fundamental.services.tasks.openlibrary.processors import RecordProcessor
from fundamental.services.tasks.protocols import (
    CancellationChecker,
    ProgressReporter,
)

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes a single dump file using appropriate record processors.

    Follows the Single Responsibility Principle by focusing solely on
    file processing orchestration.

    Parameters
    ----------
    parser : DumpFileParser
        Parser for dump files.
    processors : list[RecordProcessor[Any]]
        List of record processors to use.
    batch_processors : dict[type, BatchProcessor[Any]]
        Dictionary mapping model types to their batch processors.
    progress_reporter : ProgressReporter
        Progress reporter for updates.
    cancellation_checker : CancellationChecker
        Cancellation checker for task cancellation.
    config : IngestionConfig
        Ingestion configuration.
    """

    def __init__(
        self,
        parser: DumpFileParser,
        processors: list[RecordProcessor[Any]],
        batch_processors: dict[type, BatchProcessor[Any]],
        progress_reporter: ProgressReporter,
        cancellation_checker: CancellationChecker,
        config: IngestionConfig,
    ) -> None:
        """Initialize file processor.

        Parameters
        ----------
        parser : DumpFileParser
            Parser for dump files.
        processors : list[RecordProcessor[Any]]
            List of record processors to use.
        batch_processors : dict[type, BatchProcessor[Any]]
            Dictionary mapping model types to their batch processors.
        progress_reporter : ProgressReporter
            Progress reporter for updates.
        cancellation_checker : CancellationChecker
            Cancellation checker for task cancellation.
        config : IngestionConfig
            Ingestion configuration.
        """
        self.parser = parser
        self.processors = processors
        self.batch_processors = batch_processors
        self.progress_reporter = progress_reporter
        self.cancellation_checker = cancellation_checker
        self.config = config

    def _raise_cancelled(self) -> None:
        """Raise InterruptedError for cancelled task."""
        msg = "Task cancelled"
        raise InterruptedError(msg)

    def process_file(self, file_path: Path, file_type: str) -> dict[str, int]:
        """Process a dump file and return processing statistics.

        Parameters
        ----------
        file_path : Path
            Path to dump file.
        file_type : str
            Type of file being processed (e.g., 'authors', 'works', 'editions').

        Returns
        -------
        dict[str, int]
            Statistics about processing, including 'records' count.

        Raises
        ------
        InterruptedError
            If task is cancelled.
        Exception
            If file processing fails.
        """
        logger.info("Processing %s file: %s", file_type, file_path.name)

        stats = {"records": 0}

        try:
            for record in self.parser.parse_file(file_path):
                if self.cancellation_checker.is_cancelled():
                    self._raise_cancelled()

                # Find appropriate processor
                for processor in self.processors:
                    if processor.can_process(record):
                        models = processor.process_record(record)

                        # Add to appropriate batch
                        model_type = type(models[0]) if models else None
                        if model_type and model_type in self.batch_processors:
                            self.batch_processors[model_type].add(models)

                        stats["records"] += len(models)
                        break

                # Update progress periodically
                if stats["records"] % self.config.progress_update_interval == 0:
                    self.progress_reporter.report(
                        0.5,  # Placeholder progress
                        {
                            "current_file": file_path.name,
                            "processed_records": stats["records"],
                            "status": f"Processing {file_type}...",
                        },
                    )

            # Flush all batches
            for batch_processor in self.batch_processors.values():
                batch_processor.flush()

        except Exception:
            logger.exception("Error processing %s file %s", file_type, file_path)
            raise

        return stats

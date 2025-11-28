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

"""Ingest book task implementation.

Processes a single book file group during ingest.
Refactored to follow SOLID principles, SRP, IoC, SoC, and DRY.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_processor_service import IngestProcessorService
from fundamental.services.tasks.base import BaseTask
from fundamental.services.tasks.context import WorkerContext
from fundamental.services.tasks.exceptions import TaskCancelledError

if TYPE_CHECKING:
    from fundamental.models.ingest import IngestConfig

logger = logging.getLogger(__name__)


class IngestBookTask(BaseTask):
    """Task for processing a single book file group during ingest.

    Fetches metadata, adds books to library, and handles file cleanup.
    Follows SRP by focusing on orchestration, delegating persistence
    and business logic to services.
    """

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute ingest book task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, task_service, update_progress.
            Note: dict support is for backward compatibility; conversion
            should ideally happen at the caller level.
        """
        context = self._get_worker_context(worker_context)
        history_id = self._get_history_id()

        # Create services (dependency injection would be ideal, but
        # this maintains compatibility with existing task runner)
        processor_service = IngestProcessorService(context.session)
        config_service = IngestConfigService(context.session)
        config = config_service.get_config()

        try:
            self._check_cancellation()
            processor_service.update_history_status(history_id, IngestStatus.PROCESSING)
            context.update_progress(0.1, None)

            # Get history and extract file info
            history = processor_service.get_history(history_id)
            file_paths, metadata_hint = self._extract_file_info(history)

            # Fetch metadata
            fetched_metadata = self._fetch_metadata(
                processor_service, history_id, metadata_hint, context
            )

            # Process all files
            book_ids = self._process_files(
                processor_service,
                history_id,
                file_paths,
                fetched_metadata,
                metadata_hint,
                config,
                context,
            )

            # Check if any books were successfully processed
            if not book_ids:
                self._handle_no_books_processed(processor_service, history_id, context)

            # Finalize processing (delegates persistence to service)
            processor_service.finalize_history(history_id, book_ids)
            context.update_progress(1.0, {"book_ids": book_ids})

            logger.info(
                "Ingest book task completed: history_id=%d, book_ids=%s",
                history_id,
                book_ids,
            )

        except TaskCancelledError:
            self._handle_cancellation(processor_service, history_id)
        except Exception:
            logger.exception("Ingest book task %s failed", self.task_id)
            self._handle_error(processor_service, history_id)

    def _get_worker_context(
        self, worker_context: dict[str, Any] | WorkerContext
    ) -> WorkerContext:
        """Convert worker context to WorkerContext object.

        Note: This conversion should ideally happen at the task runner
        level to follow ISP/LSP, but is kept here for backward compatibility.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context to convert.

        Returns
        -------
        WorkerContext
            Typed worker context.
        """
        if isinstance(worker_context, dict):
            return WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        return worker_context

    def _get_history_id(self) -> int:
        """Get history_id from task metadata.

        Returns
        -------
        int
            Ingest history ID.

        Raises
        ------
        ValueError
            If history_id is missing from metadata.
        """
        history_id = self.metadata.get("history_id")
        if not history_id:
            msg = "history_id is required in task metadata"
            raise ValueError(msg)
        return history_id

    def _check_cancellation(self) -> None:
        """Check if task is cancelled and raise exception if so.

        Raises
        ------
        TaskCancelledError
            If task is cancelled.
        """
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def _extract_file_info(
        self, history: IngestHistory
    ) -> tuple[list[Path], dict[str, Any] | None]:
        """Extract file paths and metadata hint from history.

        Parameters
        ----------
        history : IngestHistory
            Ingest history record.

        Returns
        -------
        tuple[list[Path], dict[str, Any] | None]
            Tuple of (file_paths, metadata_hint).

        Raises
        ------
        ValueError
            If no files found in history.
        """
        ingest_metadata = history.ingest_metadata or {}
        files = ingest_metadata.get("files", [])
        if not files:
            msg = f"No files found in ingest history {history.id}"
            raise ValueError(msg)
        return [Path(f) for f in files], ingest_metadata.get("metadata_hint")

    def _fetch_metadata(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
        metadata_hint: dict[str, Any] | None,
        context: WorkerContext,
    ) -> dict[str, Any] | None:
        """Fetch metadata for the book.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for metadata operations.
        history_id : int
            Ingest history ID.
        metadata_hint : dict[str, Any] | None
            Optional metadata hint from file extraction.
        context : WorkerContext
            Worker context for progress updates.

        Returns
        -------
        dict[str, Any] | None
            Fetched metadata or None if not found.
        """
        context.update_progress(0.2, None)
        return processor_service.fetch_and_store_metadata(history_id, metadata_hint)

    def _process_files(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
        file_paths: list[Path],
        fetched_metadata: dict[str, Any] | None,
        metadata_hint: dict[str, Any] | None,
        config: "IngestConfig",
        context: WorkerContext,
    ) -> list[int]:
        """Process all files in the file group.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for book operations.
        history_id : int
            Ingest history ID.
        file_paths : list[Path]
            List of file paths to process.
        fetched_metadata : dict[str, Any] | None
            Fetched metadata from external sources.
        metadata_hint : dict[str, Any] | None
            Metadata hint from file extraction.
        config : IngestConfig
            Ingest configuration.
        context : WorkerContext
            Worker context for progress updates.

        Returns
        -------
        list[int]
            List of created book IDs.
        """
        context.update_progress(0.4, {"file_count": len(file_paths)})
        book_ids: list[int] = []

        for i, file_path in enumerate(file_paths):
            self._check_cancellation()

            if not file_path.exists():
                logger.warning("File not found: %s", file_path)
                continue

            try:
                book_id = self._process_single_file(
                    processor_service,
                    history_id,
                    file_path,
                    fetched_metadata,
                    metadata_hint,
                    config,
                )
                book_ids.append(book_id)
            except Exception:
                logger.exception("Failed to process file %s", file_path)
                # Continue with other files

            progress = 0.4 + (0.5 * (i + 1) / len(file_paths))
            context.update_progress(progress, {"processed": i + 1})

        return book_ids

    def _process_single_file(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
        file_path: Path,
        fetched_metadata: dict[str, Any] | None,
        metadata_hint: dict[str, Any] | None,
        config: "IngestConfig",
    ) -> int:
        """Process a single file.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for book operations.
        history_id : int
            Ingest history ID.
        file_path : Path
            Path to book file.
        fetched_metadata : dict[str, Any] | None
            Fetched metadata from external sources.
        metadata_hint : dict[str, Any] | None
            Metadata hint from file extraction.
        config : IngestConfig
            Ingest configuration.

        Returns
        -------
        int
            Created book ID.
        """
        # Extract file format (low-level detail, but needed for service call)
        file_format = file_path.suffix.lower().lstrip(".")

        # Extract title and author using DRY metadata merging
        title, author_name = self._extract_title_author(fetched_metadata, metadata_hint)

        # Add book to library (delegates to service)
        book_id = processor_service.add_book_to_library(
            history_id=history_id,
            file_path=file_path,
            file_format=file_format,
            title=title,
            author_name=author_name,
        )

        # Handle cover download if URL is available
        cover_url = None
        if fetched_metadata and fetched_metadata.get("cover_url"):
            cover_url = fetched_metadata["cover_url"]
        elif metadata_hint and metadata_hint.get("cover_url"):
            cover_url = metadata_hint["cover_url"]

        if cover_url:
            processor_service.set_book_cover(book_id, cover_url)

        # Handle file deletion if configured (separate concern)
        if config.auto_delete_after_ingest:
            self._delete_source_file(file_path)

        return book_id

    def _extract_title_author(
        self,
        fetched_metadata: dict[str, Any] | None,
        metadata_hint: dict[str, Any] | None,
    ) -> tuple[str | None, str | None]:
        """Extract title and author from metadata sources with fallback.

        Follows DRY principle by using generic metadata merging utility.

        Parameters
        ----------
        fetched_metadata : dict[str, Any] | None
            Fetched metadata from external sources (higher priority).
        metadata_hint : dict[str, Any] | None
            Metadata hint from file extraction (fallback).

        Returns
        -------
        tuple[str | None, str | None]
            Tuple of (title, author_name).
        """
        # Use generic metadata merge utility
        merged = self._merge_metadata(
            fetched_metadata, metadata_hint, keys=["title", "authors"]
        )

        title = merged.get("title")
        authors = merged.get("authors", [])
        author_name = authors[0] if authors else None

        return title, author_name

    def _merge_metadata(
        self,
        *sources: dict[str, Any] | None,
        keys: list[str],
    ) -> dict[str, Any]:
        """Merge metadata from multiple sources with fallback.

        Extracts values from multiple sources in priority order.
        First source with a non-empty value wins.

        Parameters
        ----------
        *sources : dict[str, Any] | None
            Variable number of metadata source dictionaries.
        keys : list[str]
            List of keys to extract from sources.

        Returns
        -------
        dict[str, Any]
            Merged metadata dictionary.
        """
        result: dict[str, Any] = {}

        for key in keys:
            for source in sources:
                if source and (value := source.get(key)):
                    # Handle both single values and lists
                    if (isinstance(value, list) and value) or (
                        not isinstance(value, list) and value
                    ):
                        result[key] = value
                    else:
                        continue
                    break

        return result

    def _delete_source_file(self, file_path: Path) -> None:
        """Delete source file after processing.

        Parameters
        ----------
        file_path : Path
            Path to file to delete.
        """
        try:
            file_path.unlink()
            logger.info("Deleted source file: %s", file_path)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to delete source file %s: %s", file_path, e)

    def _handle_no_books_processed(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
        context: WorkerContext,
    ) -> None:
        """Handle case where no books were successfully processed.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for status updates.
        history_id : int
            Ingest history ID.
        context : WorkerContext
            Worker context for progress updates.

        Raises
        ------
        RuntimeError
            Always raised to signal task failure.
        """
        error_msg = "No books were successfully processed. All files failed to ingest."
        logger.warning(
            "Ingest book task failed: history_id=%d, reason=%s",
            history_id,
            error_msg,
        )
        processor_service.update_history_status(
            history_id, IngestStatus.FAILED, error_msg
        )
        context.update_progress(1.0, {"book_ids": [], "error": error_msg})
        raise RuntimeError(error_msg)

    def _handle_cancellation(
        self, processor_service: IngestProcessorService, history_id: int
    ) -> None:
        """Handle task cancellation.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for status updates.
        history_id : int
            Ingest history ID.
        """
        logger.info("Ingest book task %s cancelled", self.task_id)
        processor_service.update_history_status(
            history_id, IngestStatus.FAILED, "Task cancelled"
        )

    def _handle_error(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
    ) -> None:
        """Handle task error.

        Parameters
        ----------
        processor_service : IngestProcessorService
            Processor service for status updates.
        history_id : int
            Ingest history ID.

        Note
        ----
        Exception logging should be done in the caller's exception handler.
        This method only updates the history status.
        """
        import sys

        error = sys.exc_info()[1]
        error_msg = (
            str(error)[:2000] if error else "Unknown error"
        )  # Truncate to max length
        processor_service.update_history_status(
            history_id, IngestStatus.FAILED, error_msg
        )
        raise

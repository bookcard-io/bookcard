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
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlmodel import Session

from bookcard.models.ingest import IngestHistory, IngestStatus
from bookcard.services.duplicate_detection import BookDuplicateHandler
from bookcard.services.ingest.ingest_config_service import IngestConfigService
from bookcard.services.ingest.ingest_processor_service import IngestProcessorService
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.exceptions import TaskCancelledError
from bookcard.services.tasks.post_processors import (
    ConversionPostIngestProcessor,
    EPUBPostIngestProcessor,
)

if TYPE_CHECKING:
    from bookcard.models.config import Library
    from bookcard.models.ingest import IngestConfig
    from bookcard.services.tasks.post_processors import PostIngestProcessor

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

            # Fetch metadata (only if enabled in config)
            fetched_metadata = self._fetch_metadata(
                processor_service, history_id, metadata_hint, config, context
            )

            # Process all files
            book_ids, skipped_duplicates = self._process_files(
                processor_service,
                history_id,
                file_paths,
                fetched_metadata,
                metadata_hint,
                config,
                context,
            )

            # Check if any books were successfully processed
            # If all files were skipped as duplicates (IGNORE mode), that's success
            # Only fail if there were actual processing errors
            if not book_ids and skipped_duplicates == 0:
                self._handle_no_books_processed(processor_service, history_id, context)
            elif not book_ids and skipped_duplicates > 0:
                # All files were skipped as duplicates - this is success in IGNORE mode
                logger.info(
                    "All files skipped as duplicates (IGNORE mode): history_id=%d, skipped=%d",
                    history_id,
                    skipped_duplicates,
                )

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
        config: "IngestConfig",
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
        config : IngestConfig
            Ingest configuration.
        context : WorkerContext
            Worker context for progress updates.

        Returns
        -------
        dict[str, Any] | None
            Fetched metadata or None if not found or disabled.
        """
        # Skip metadata fetch if disabled in configuration
        if not config.metadata_fetch_enabled:
            logger.info(
                "Metadata fetch is disabled in ingest configuration; "
                "skipping fetch for history %d",
                history_id,
            )
            return None

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
    ) -> tuple[list[int], int]:
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
        tuple[list[int], int]
            Tuple of (list of created book IDs, count of skipped duplicates).
        """
        context.update_progress(0.4, {"file_count": len(file_paths)})
        book_ids: list[int] = []
        skipped_duplicates = 0

        # Get library once for all files (used by post-processors)
        library = processor_service.get_active_library()

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
                    library,
                    context.session,
                )
                book_ids.append(book_id)
            except ValueError as exc:
                # Handle duplicate skip (IGNORE mode) - log, delete file, and continue
                if "skipping per library settings" in str(exc):
                    logger.info("Skipping duplicate file: %s", file_path)
                    skipped_duplicates += 1
                    # Delete skipped duplicate file to clean up ingest directory
                    self._delete_source_files_and_dirs(file_path)
                else:
                    logger.exception("Failed to process file %s", file_path)
                # Continue with other files
            except Exception:
                logger.exception("Failed to process file %s", file_path)
                # Continue with other files

            progress = 0.4 + (0.5 * (i + 1) / len(file_paths))
            context.update_progress(progress, {"processed": i + 1})

        return book_ids, skipped_duplicates

    def _check_and_handle_duplicate(
        self,
        library: "Library",
        processor_service: IngestProcessorService,
        file_path: Path,
        file_format: str,
        title: str | None,
        author_name: str | None,
    ) -> int | None:
        """Check for duplicate and handle according to library settings.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Active library configuration.
        processor_service : IngestProcessorService
            Processor service for book operations.
        file_path : Path
            Path to book file.
        file_format : str
            File format extension.
        title : str | None
            Book title.
        author_name : str | None
            Author name.

        Returns
        -------
        int | None
            Book ID if duplicate should be used (OVERWRITE mode), None otherwise.
            Returns None if IGNORE mode and duplicate found (caller should skip).

        Note
        ----
        For IGNORE mode, returns None to signal skip. For OVERWRITE mode,
        deletes existing book and returns its ID. For CREATE_NEW mode, returns None.
        """
        duplicate_handler = BookDuplicateHandler()
        result = duplicate_handler.check_duplicate(
            library=library,
            file_path=file_path,
            title=title,
            author_name=author_name,
            file_format=file_format,
        )

        if result.should_skip:
            # IGNORE mode: skip duplicate
            logger.info(
                "Duplicate book found (book_id=%d), skipping per library settings",
                result.duplicate_book_id,
            )
            return None  # Signal to caller to skip this file

        if result.should_overwrite and result.duplicate_book_id:
            # OVERWRITE mode: delete existing book
            logger.info(
                "Duplicate found (book_id=%d), overwriting per library settings",
                result.duplicate_book_id,
            )
            # Get book service to delete - access via public method if available
            # Otherwise use the factory directly (it's a public attribute in practice)
            book_service_factory = getattr(
                processor_service, "_book_service_factory", None
            )
            if book_service_factory:
                book_service = book_service_factory(library)
                book_service.delete_book(
                    book_id=result.duplicate_book_id,
                    delete_files_from_drive=True,
                )
            return result.duplicate_book_id

        # CREATE_NEW mode or no duplicate: proceed normally
        return None

    def _process_single_file(
        self,
        processor_service: IngestProcessorService,
        history_id: int,
        file_path: Path,
        fetched_metadata: dict[str, Any] | None,
        metadata_hint: dict[str, Any] | None,
        config: "IngestConfig",
        library: "Library",
        session: Session,
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
        library : Library
            Active library configuration.
        session : Session
            Database session.

        Returns
        -------
        int
            Created book ID.

        Raises
        ------
        ValueError
            If file should be skipped (duplicate in IGNORE mode).
        """
        # Extract file format (low-level detail, but needed for service call)
        file_format = file_path.suffix.lower().lstrip(".")

        # Extract title and author using DRY metadata merging
        title, author_name = self._extract_title_author(fetched_metadata, metadata_hint)

        # Check for duplicates and handle according to library settings
        # Returns None if IGNORE mode (should skip) or CREATE_NEW mode (proceed)
        # Returns book_id if OVERWRITE mode (existing book deleted)
        duplicate_result = self._check_and_handle_duplicate(
            library=library,
            processor_service=processor_service,
            file_path=file_path,
            file_format=file_format,
            title=title,
            author_name=author_name,
        )

        # If IGNORE mode and duplicate found, skip this file
        if duplicate_result is None and title:
            duplicate_handler = BookDuplicateHandler()
            result = duplicate_handler.check_duplicate(
                library=library,
                file_path=file_path,
                title=title,
                author_name=author_name,
                file_format=file_format,
            )
            if result.should_skip:
                msg = f"Duplicate book found (book_id={result.duplicate_book_id}), skipping per library settings"
                raise ValueError(msg)

        # Extract and convert published_date to pubdate
        pubdate = self._extract_pubdate(fetched_metadata, metadata_hint)
        book_id = processor_service.add_book_to_library(
            history_id=history_id,
            file_path=file_path,
            file_format=file_format,
            title=title,
            author_name=author_name,
            pubdate=pubdate,
        )

        # Handle cover download if URL is available
        cover_url = None
        if fetched_metadata and fetched_metadata.get("cover_url"):
            cover_url = fetched_metadata["cover_url"]
        elif metadata_hint and metadata_hint.get("cover_url"):
            cover_url = metadata_hint["cover_url"]

        if cover_url:
            processor_service.set_book_cover(book_id, cover_url)

        # Run post-processors (e.g., auto-conversion, EPUB fixing)
        self._run_post_processors(
            session,
            book_id,
            library,
            file_format,
        )

        # Handle file deletion if configured (separate concern)
        if config.auto_delete_after_ingest:
            self._delete_source_files_and_dirs(file_path)

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

    def _extract_pubdate(
        self,
        fetched_metadata: dict[str, Any] | None,
        metadata_hint: dict[str, Any] | None,
    ) -> datetime | None:
        """Extract and convert published_date to datetime pubdate.

        Parameters
        ----------
        fetched_metadata : dict[str, Any] | None
            Fetched metadata from external sources (higher priority).
        metadata_hint : dict[str, Any] | None
            Metadata hint from file extraction (fallback).

        Returns
        -------
        datetime | None
            Parsed datetime pubdate or None if not available.
        """
        # Use generic metadata merge utility to get published_date
        merged = self._merge_metadata(
            fetched_metadata, metadata_hint, keys=["published_date"]
        )

        published_date = merged.get("published_date")
        if not published_date:
            return None

        return self._parse_published_date(published_date)

    def _parse_published_date(self, date_str: str) -> datetime | None:
        """Parse published_date string to datetime.

        Parameters
        ----------
        date_str : str
            Published date string in various formats.

        Returns
        -------
        datetime | None
            Parsed datetime or None if invalid.
        """
        if not date_str:
            return None

        # Try common date formats in order of specificity
        # Each format tuple is (format_string, min_length)
        formats = [
            ("%Y-%m-%d", 10),  # YYYY-MM-DD
            ("%Y-%m", 7),  # YYYY-MM
            ("%Y", 4),  # YYYY
            ("%Y-%m-%dT%H:%M:%S", 19),  # YYYY-MM-DDTHH:MM:SS
            ("%Y-%m-%dT%H:%M:%SZ", 20),  # YYYY-MM-DDTHH:MM:SSZ
            ("%Y-%m-%dT%H:%M:%S%z", 25),  # YYYY-MM-DDTHH:MM:SS+HH:MM
        ]

        for fmt, min_length in formats:
            try:
                # Check if date string is long enough for this format
                if len(date_str) >= min_length:
                    # Parse date string - strptime returns naive datetime
                    parsed = datetime.strptime(date_str, fmt)  # noqa: DTZ007
                    # Ensure UTC timezone
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    return parsed
            except (ValueError, TypeError):
                continue

        logger.warning(
            "Failed to parse published_date: %s",
            date_str,
        )
        return None

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

    def _delete_source_files_and_dirs(self, file_path: Path) -> None:
        """Delete source book file, companion files, and empty parent directories.

        This method is intentionally conservative and only removes:

        - The main book file that was just processed.
        - Companion files that belong to the same logical book:
          all files in the same directory whose stem matches the main file,
          plus common companion files such as ``cover.*`` and ``metadata.opf``.
        - The immediate parent directory (``Book``) if it is empty after file
          deletion.
        - The parent of the parent directory (``Author``) if it is also empty.

        Parameters
        ----------
        file_path : Path
            Path to the primary book file that was ingested.
        """
        book_dir = file_path.parent
        author_dir = book_dir.parent

        self._delete_main_file(file_path)
        self._delete_companion_files(file_path, book_dir)
        self._try_delete_empty_directory(book_dir, "book")
        self._try_delete_empty_directory(author_dir, "author")

    def _delete_main_file(self, file_path: Path) -> None:
        """Delete the main book file.

        Parameters
        ----------
        file_path : Path
            Path to the main book file to delete.
        """
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                logger.info("Deleted source file: %s", file_path)
            except (OSError, PermissionError) as exc:
                logger.warning("Failed to delete source file %s: %s", file_path, exc)

    def _delete_companion_files(self, file_path: Path, book_dir: Path) -> None:
        """Delete companion files belonging to the same book.

        Parameters
        ----------
        file_path : Path
            Path to the main book file.
        book_dir : Path
            Directory containing the book files.
        """
        if not book_dir.exists() or not book_dir.is_dir():
            return

        main_stem = file_path.stem
        companion_suffixes = {".opf", ".jpg", ".jpeg", ".png", ".gif", ".webp"}

        for child in book_dir.iterdir():
            if not child.is_file():
                continue

            is_matching_stem = child.stem == main_stem
            is_cover = (
                child.stem == "cover" and child.suffix.lower() in companion_suffixes
            )
            is_metadata = child.name.lower() == "metadata.opf"

            if not (is_matching_stem or is_cover or is_metadata):
                continue

            try:
                child.unlink()
                logger.info("Deleted companion ingest file: %s", child)
            except (OSError, PermissionError) as exc:
                logger.warning("Failed to delete companion file %s: %s", child, exc)

    def _try_delete_empty_directory(self, directory: Path, dir_type: str) -> None:
        """Attempt to delete an empty directory.

        Parameters
        ----------
        directory : Path
            Directory to delete if empty.
        dir_type : str
            Type of directory (e.g., "book", "author") for logging.

        Note
        ----
        Will not delete the root ingest directory (named "books_ingest")
        even if it becomes empty, to preserve the ingest directory structure.
        """
        if not directory.exists() or not directory.is_dir():
            return

        # Never delete the root ingest directory (books_ingest)
        if directory.name == "books_ingest":
            return

        try:
            remaining_items = [
                item for item in directory.iterdir() if item.name not in (".", "..")
            ]
            if not remaining_items:
                directory.rmdir()
                logger.info(
                    "Deleted empty ingest %s directory: %s", dir_type, directory
                )
        except (OSError, PermissionError) as exc:
            logger.warning(
                "Failed to delete ingest %s directory %s: %s", dir_type, directory, exc
            )

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

    def _get_post_processors(
        self,
        session: Session,
        library: "Library",
    ) -> list["PostIngestProcessor"]:
        """Get post-ingest processors for auto-ingest.

        Parameters
        ----------
        session : Session
            Database session for creating processors.
        library : Library
            Library configuration.

        Returns
        -------
        list[PostIngestProcessor]
            List of post-ingest processors.
        """
        processors = [EPUBPostIngestProcessor(session)]
        # Add conversion processor using library-level settings
        processors.append(ConversionPostIngestProcessor(session, library=library))
        return processors

    def _run_post_processors(
        self,
        session: Session,
        book_id: int,
        library: "Library",
        file_format: str,
    ) -> None:
        """Run post-ingest processors for the ingested book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Library
            Library configuration.
        file_format : str
            File format that was ingested.
        """
        processors = self._get_post_processors(session, library)
        for processor in processors:
            if processor.supports_format(file_format):
                with suppress(Exception):
                    # Don't fail the ingest if post-processing fails
                    # Use None for user_id since this is library-level auto-ingest
                    processor.process(session, book_id, library, user_id=None)

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

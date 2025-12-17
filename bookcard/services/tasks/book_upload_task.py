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

"""Book upload task implementation.

Handles single file uploads with progress tracking and metadata extraction.
Refactored to follow SOLID principles, DRY, SRP, IoC, and SoC.
"""

import logging
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.repositories.book_metadata_service import BookMetadataService
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.duplicate_detection import BookDuplicateHandler
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import ProgressCallback, WorkerContext
from bookcard.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
)
from bookcard.services.tasks.post_processors import (
    ConversionPostIngestProcessor,
    EPUBPostIngestProcessor,
    PostIngestProcessor,
)

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """File information extracted from metadata.

    Follows Single Responsibility Principle by encapsulating file metadata.
    """

    file_path: Path
    filename: str
    file_format: str


class BookUploadTask(BaseTask):
    """Task for uploading a single book file.

    Handles file upload, metadata extraction, and database insertion
    with progress tracking. Refactored to follow SOLID principles.

    Attributes
    ----------
    file_info : FileInfo
        File information extracted from metadata.
    _post_processors : list[PostIngestProcessor]
        List of post-ingest processors to run after book addition.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
        post_processors: list[PostIngestProcessor] | None = None,  # type: ignore[type-arg]
    ) -> None:
        """Initialize book upload task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing file_path, filename, file_format.
        post_processors : list[PostIngestProcessor] | None
            Optional list of post-ingest processors. If None, will create
            default processors (e.g., EPUB) at runtime.
        """
        super().__init__(task_id, user_id, metadata)
        self.file_info = self._parse_file_info(metadata)
        self._post_processors = post_processors

    def _parse_file_info(self, metadata: dict[str, Any]) -> FileInfo:
        """Parse file information from metadata.

        Parameters
        ----------
        metadata : dict[str, Any]
            Task metadata.

        Returns
        -------
        FileInfo
            Parsed file information.

        Raises
        ------
        ValueError
            If required file_path is missing.
        """
        file_path_str = metadata.get("file_path", "")
        if not file_path_str:
            msg = "file_path is required in task metadata"
            raise ValueError(msg)
        return FileInfo(
            file_path=Path(file_path_str),
            filename=metadata.get("filename", "Unknown"),
            file_format=metadata.get("file_format", ""),
        )

    def _check_cancellation(self) -> None:
        """Check if task is cancelled and raise exception if so.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def _update_progress_or_cancel(
        self,
        progress: float,
        update_progress: ProgressCallback,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update progress and check for cancellation.

        Combines progress update and cancellation check to follow DRY.

        Parameters
        ----------
        progress : float
            Progress value (0.0 to 1.0).
        update_progress : ProgressCallback
            Progress update callback.
        metadata : dict[str, Any] | None
            Optional metadata to include with progress update.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        update_progress(progress, metadata)
        self._check_cancellation()

    def _validate_file(self) -> int:
        """Validate file path and return file size.

        Returns
        -------
        int
            File size in bytes.

        Raises
        ------
        FileNotFoundError
            If file does not exist.
        ValueError
            If file path is invalid.
        """
        if not self.file_info.file_path.exists():
            msg = f"File not found: {self.file_info.file_path}"
            raise FileNotFoundError(msg)
        if self.file_info.file_path.is_dir():
            msg = f"file_path is a directory, not a file: {self.file_info.file_path}"
            raise ValueError(msg)
        if not self.file_info.file_path.is_file():
            msg = f"file_path is not a valid file: {self.file_info.file_path}"
            raise ValueError(msg)
        return self.file_info.file_path.stat().st_size

    def _get_active_library(
        self,
        session: Session,  # type: ignore[type-arg]
    ) -> Library:  # type: ignore[name-defined]
        """Get active library configuration.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        Library
            Active library configuration.

        Raises
        ------
        ValueError
            If no active library is configured.
        """
        library_repo = LibraryRepository(session)
        library_service = LibraryService(session, library_repo)
        library = library_service.get_active_library()

        if library is None:
            raise LibraryNotConfiguredError

        return library

    def _extract_title(self) -> str:
        """Extract title from metadata or filename.

        Returns
        -------
        str
            Book title.
        """
        title = self.metadata.get("title")
        if not title:
            title = Path(self.file_info.filename).stem
        return title

    def _extract_author(self) -> str | None:
        """Extract author from file metadata.

        Extracts author from the book file using BookMetadataService.
        Falls back to None if extraction fails.

        Returns
        -------
        str | None
            Author name if found, None otherwise.
        """
        try:
            metadata_service = BookMetadataService()
            metadata, _ = metadata_service.extract_metadata(
                self.file_info.file_path, self.file_info.file_format
            )
            author = metadata.author
            # Handle case where author might be "Unknown" or empty
            if author and author != "Unknown":
                return author
        except (ValueError, ImportError, OSError, KeyError, AttributeError) as exc:
            logger.debug(
                "Failed to extract author from %s: %s",
                self.file_info.file_path,
                exc,
            )
        return None

    def _check_and_handle_duplicate(
        self,
        library: Library,  # type: ignore[name-defined]
        book_service: BookService,
        title: str,
        author_name: str | None,
    ) -> int | None:
        """Check for duplicate and handle according to library settings.

        Parameters
        ----------
        library : Library
            Active library configuration.
        book_service : BookService
            Book service instance.
        title : str
            Book title.
        author_name : str | None
            Author name extracted from file.

        Returns
        -------
        int | None
            Book ID if duplicate should be used (OVERWRITE mode), None otherwise.
            Raises exception if IGNORE mode and duplicate found.

        Raises
        ------
        ValueError
            If duplicate found and IGNORE mode is set.
        """
        duplicate_handler = BookDuplicateHandler()
        result = duplicate_handler.check_duplicate(
            library=library,
            file_path=self.file_info.file_path,
            title=title,
            author_name=author_name,
            file_format=self.file_info.file_format,
        )

        if result.should_skip:
            # IGNORE mode: skip duplicate
            msg = f"Duplicate book found (book_id={result.duplicate_book_id}), skipping per library settings"
            logger.info(msg)
            raise ValueError(msg)

        if result.should_overwrite and result.duplicate_book_id:
            # OVERWRITE mode: delete existing book
            logger.info(
                "Duplicate found (book_id=%d), overwriting per library settings",
                result.duplicate_book_id,
            )
            book_service.delete_book(
                book_id=result.duplicate_book_id,
                delete_files_from_drive=True,
            )
            return result.duplicate_book_id

        # CREATE_NEW mode or no duplicate: proceed normally
        return None

    def _add_book_to_library(
        self,
        session: Session,  # type: ignore[type-arg]
        library: Library,  # type: ignore[name-defined]
        update_progress: ProgressCallback,
    ) -> int:
        """Add book to library and return book ID.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Active library configuration.
        update_progress : ProgressCallback
            Progress update callback.

        Returns
        -------
        int
            Book ID.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        ValueError
            If duplicate found and IGNORE mode is set.
        """
        # Update progress: 0.2 - library found
        self._update_progress_or_cancel(0.2, update_progress)

        # Create book service
        book_service = BookService(library, session=session)

        # Extract title and author from file
        title = self._extract_title()
        author_name = self._extract_author()

        # Update progress: 0.25 - checking for duplicates
        self._update_progress_or_cancel(0.25, update_progress)

        # Check for duplicates and handle according to library settings
        self._check_and_handle_duplicate(library, book_service, title, author_name)

        # Update progress: 0.3 - ready to add book
        self._update_progress_or_cancel(0.3, update_progress)

        # Add book to library
        # This will save the file, extract metadata, and create database entry
        book_id = book_service.add_book(
            file_path=self.file_info.file_path,
            file_format=self.file_info.file_format,
            title=title,
            author_name=author_name,
        )

        # Store final metadata
        self.set_metadata("book_ids", [book_id])
        self.set_metadata("title", title)

        return book_id

    def _get_post_processors(
        self,
        session: Session,  # type: ignore[type-arg]
        library: Library,  # type: ignore[name-defined]
    ) -> list[PostIngestProcessor]:  # type: ignore[type-arg]
        """Get post-ingest processors, creating defaults if needed.

        Parameters
        ----------
        session : Session
            Database session for creating processors.
        library : Library
            Library configuration for library-level conversion settings.

        Returns
        -------
        list[PostIngestProcessor]
            List of post-ingest processors.
        """
        if self._post_processors is not None:
            return self._post_processors

        processors = [EPUBPostIngestProcessor(session)]
        # Add conversion processor using library-level config
        # User uploads now follow library-level auto-convert settings
        processors.append(ConversionPostIngestProcessor(session, library=library))
        return processors

    def _run_post_processors(
        self,
        session: Session,  # type: ignore[type-arg]
        book_id: int,
        library: Library,  # type: ignore[name-defined]
    ) -> None:
        """Run post-ingest processors for the uploaded book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Library
            Library configuration.
        """
        processors = self._get_post_processors(session, library)
        for processor in processors:
            if processor.supports_format(self.file_info.file_format):
                with suppress(Exception):
                    # Don't fail the upload if post-processing fails
                    processor.process(session, book_id, library, self.user_id)

    def _validate_metadata_before_completion(self) -> None:
        """Validate required metadata is present before task completion.

        Raises
        ------
        ValueError
            If required metadata fields are missing.
        """
        if "book_ids" not in self.metadata:
            msg = "Required metadata field 'book_ids' missing"
            raise ValueError(msg)

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute book upload task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, task_service, update_progress.
            Can be a dictionary (for backward compatibility) or WorkerContext.
        """
        # Convert dict to WorkerContext for type safety
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        else:
            context = worker_context

        try:
            self._check_cancellation()

            # Validate file and get file size
            file_size = self._validate_file()
            self.set_metadata("file_size", file_size)

            # Update progress: 0.1 - file validated
            self._update_progress_or_cancel(
                0.1, context.update_progress, {"file_size": file_size}
            )

            # Get active library
            library = self._get_active_library(context.session)

            # Add book to library
            book_id = self._add_book_to_library(
                context.session, library, context.update_progress
            )

            # Update progress: 0.9 - book added
            context.update_progress(0.9, {"book_ids": [book_id]})

            # Run post-processors (e.g., EPUB auto-fix)
            self._run_post_processors(context.session, book_id, library)

            # Validate metadata before completion
            self._validate_metadata_before_completion()

            # Update progress: 1.0 - complete
            context.update_progress(1.0, self.metadata)

            logger.info(
                "Task %s: Book %s uploaded successfully (%s, %s bytes)",
                self.task_id,
                book_id,
                self.file_info.filename,
                file_size,
            )

        except TaskCancelledError:
            logger.info("Task %s cancelled", self.task_id)
            # Don't re-raise - cancellation is expected
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

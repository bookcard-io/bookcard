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
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_service import BookService
from fundamental.services.config_service import LibraryService
from fundamental.services.tasks.base import BaseTask

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlmodel import Session

logger = logging.getLogger(__name__)


class BookUploadTask(BaseTask):
    """Task for uploading a single book file.

    Handles file upload, metadata extraction, and database insertion
    with progress tracking.

    Attributes
    ----------
    file_path : Path
        Path to the uploaded file (temporary location).
    filename : str
        Original filename.
    file_format : str
        File format extension.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
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
        """
        super().__init__(task_id, user_id, metadata)
        file_path_str = metadata.get("file_path", "")
        if not file_path_str:
            msg = "file_path is required in task metadata"
            raise ValueError(msg)
        self.file_path = Path(file_path_str)
        self.filename = metadata.get("filename", "Unknown")
        self.file_format = metadata.get("file_format", "")

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
        if not self.file_path.exists():
            msg = f"File not found: {self.file_path}"
            raise FileNotFoundError(msg)
        if self.file_path.is_dir():
            msg = f"file_path is a directory, not a file: {self.file_path}"
            raise ValueError(msg)
        if not self.file_path.is_file():
            msg = f"file_path is not a valid file: {self.file_path}"
            raise ValueError(msg)
        return self.file_path.stat().st_size

    def _add_book_to_library(
        self,
        session: Session,
        update_progress: Callable[..., None],  # type: ignore[type-arg]
    ) -> int:
        """Add book to library and return book ID.

        Parameters
        ----------
        session : Session
            Database session.
        update_progress : Any
            Progress update callback.

        Returns
        -------
        int
            Book ID.

        Raises
        ------
        ValueError
            If no active library is configured.
        """
        # Get active library
        library_repo = LibraryRepository(session)
        library_service = LibraryService(session, library_repo)
        library = library_service.get_active_library()

        if library is None:
            msg = "No active library configured"
            raise ValueError(msg)

        # Update progress: 0.2 - library found
        update_progress(0.2)

        # Check if cancelled
        if self.check_cancelled():
            return -1  # type: ignore[return-value]

        # Create book service
        book_service = BookService(library, session=session)

        # Extract title from filename if not provided
        title = self.metadata.get("title")
        if not title:
            title = Path(self.filename).stem

        # Update progress: 0.3 - ready to add book
        update_progress(0.3)

        # Check if cancelled
        if self.check_cancelled():
            return -1  # type: ignore[return-value]

        # Add book to library
        # This will save the file, extract metadata, and create database entry
        book_id = book_service.add_book(
            file_path=self.file_path,
            file_format=self.file_format,
            title=title,
            author_name=self.metadata.get("author_name"),
        )

        # Store final metadata - ensure book_ids is in self.metadata
        # This is critical because complete_task uses task_instance.metadata
        self.set_metadata("book_ids", [book_id])  # Array with single element
        self.set_metadata("title", title)

        return book_id

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute book upload task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Validate file and get file size
            file_size = self._validate_file()
            self.set_metadata("file_size", file_size)

            # Update progress: 0.1 - file validated
            update_progress(0.1, {"file_size": file_size})

            # Add book to library
            book_id = self._add_book_to_library(session, update_progress)
            if book_id == -1:  # Cancelled
                return

            # Update progress: 0.9 - book added
            # This saves book_ids to task_data in the database
            # For single book upload, book_ids is an array with one element
            update_progress(0.9, {"book_ids": [book_id]})

            # Log to verify book_ids is in metadata
            logger.info(
                "Task %s: Metadata before final update: %s",
                self.task_id,
                self.metadata,
            )

            # Update progress: 1.0 - complete
            # Pass self.metadata which should now include book_ids
            # This ensures book_ids is saved to task_data before complete_task is called
            update_progress(1.0, self.metadata)

            # Double-check that book_ids is in metadata before task completes
            if "book_ids" not in self.metadata:
                logger.error(
                    "Task %s: book_ids not found in metadata after update_progress(1.0). Metadata: %s",
                    self.task_id,
                    self.metadata,
                )
            else:
                logger.info(
                    "Task %s: book_ids %s confirmed in metadata before task completion",
                    self.task_id,
                    self.metadata.get("book_ids"),
                )

            logger.info(
                "Task %s: Book %s uploaded successfully (%s, %s bytes)",
                self.task_id,
                book_id,
                self.filename,
                file_size,
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

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

from sqlmodel import select

from fundamental.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_service import BookService
from fundamental.services.config_service import LibraryService
from fundamental.services.epub_fixer_service import EPUBFixerService
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

        # Auto-fix EPUB on ingest if enabled
        if self.file_format.lower() == "epub":
            self._auto_fix_epub_on_ingest(session, book_id, library)

        return book_id

    def _auto_fix_epub_on_ingest(
        self,
        session: Session,
        book_id: int,
        library: Library,
    ) -> None:
        """Auto-fix EPUB file on ingest if enabled.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID that was just added.
        library : Any
            Library configuration.
        """
        try:
            # Check if auto-fix on ingest is enabled
            stmt = select(ScheduledTasksConfig).limit(1)
            scheduled_config = session.exec(stmt).first()
            if (
                scheduled_config is None
                or not scheduled_config.epub_fixer_auto_fix_on_ingest
            ):
                logger.debug("EPUB auto-fix on ingest is disabled, skipping")
                return

            # Check if EPUB fixer is enabled
            stmt = select(EPUBFixerConfig).limit(1)
            epub_config = session.exec(stmt).first()
            if not epub_config or not epub_config.enabled:
                logger.debug("EPUB fixer is disabled, skipping auto-fix on ingest")
                return

            # Get book to find file path
            stmt = (
                select(Book, Data)
                .join(Data)
                .where(Book.id == book_id)
                .where(Data.format == "EPUB")
            )
            result = session.exec(stmt).first()
            if result is None:
                logger.debug("EPUB format not found for book %d", book_id)
                return

            book, data = result

            # Construct file path
            lib_root = getattr(library, "library_root", None)
            if lib_root:
                library_path = Path(lib_root)
            else:
                library_db_path = Path(library.calibre_db_path)
                library_path = (
                    library_db_path
                    if library_db_path.is_dir()
                    else library_db_path.parent
                )

            book_dir = library_path / book.path
            file_name = data.name or str(book.id)
            file_path = book_dir / f"{file_name}.{data.format.lower()}"

            if not file_path.exists():
                # Try alternative naming
                alt_file_name = f"{book.id}.{data.format.lower()}"
                alt_file_path = book_dir / alt_file_name
                if alt_file_path.exists():
                    file_path = alt_file_path
                else:
                    logger.warning(
                        "EPUB file not found at %s or %s", file_path, alt_file_path
                    )
                    return

            # Process EPUB file
            fixer_service = EPUBFixerService(session)

            fix_run = fixer_service.process_epub_file(
                file_path=file_path,
                book_id=book_id,
                book_title=book.title,
                user_id=self.user_id,
                library_id=library.id if library else None,
                manually_triggered=False,  # Automatic, not manual
            )

            # Get fixes for the run to log
            if fix_run.id is not None:
                fixes = fixer_service.get_fixes_for_run(fix_run.id)
                if fixes:
                    logger.info(
                        "Auto-fixed EPUB on ingest: book_id=%d, file=%s, fixes_applied=%d",
                        book_id,
                        file_path,
                        len(fixes),
                    )
                else:
                    logger.debug(
                        "No fixes needed for EPUB on ingest: book_id=%d", book_id
                    )

        except Exception:
            # Don't fail the upload if auto-fix fails
            logger.exception(
                "Failed to auto-fix EPUB on ingest for book_id=%d", book_id
            )

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

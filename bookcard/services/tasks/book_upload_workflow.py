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

"""Book upload workflow and supporting components."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import SQLAlchemyError

from bookcard.repositories.book_metadata_service import BookMetadataService
from bookcard.services.book_service import BookService
from bookcard.services.duplicate_detection import BookDuplicateHandler
from bookcard.services.tasks.exceptions import (
    TaskCancelledError,
)
from bookcard.services.tasks.post_processors import (
    ConversionPostIngestProcessor,
    EPUBPostIngestProcessor,
    PostIngestProcessor,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.config import Library
    from bookcard.services.book_metadata import BookMetadata

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, dict[str, Any] | None], None]
CancellationCheck = Callable[[], bool]


@dataclass(frozen=True)
class FileInfo:
    """File information extracted from task metadata."""

    file_path: Path
    filename: str
    file_format: str

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> FileInfo:
        """Create a FileInfo from task metadata.

        Parameters
        ----------
        metadata : dict[str, Any]
            Task metadata containing file_path, filename, and file_format.

        Returns
        -------
        FileInfo
            Parsed file information.

        Raises
        ------
        ValueError
            If file_path is missing.
        """
        file_path_str = metadata.get("file_path", "")
        if not file_path_str:
            msg = "file_path is required in task metadata"
            raise ValueError(msg)

        return cls(
            file_path=Path(file_path_str),
            filename=metadata.get("filename", "Unknown"),
            file_format=metadata.get("file_format", ""),
        )


@dataclass(frozen=True)
class UploadContext:
    """Runtime context for a book upload."""

    session: Session
    update_progress: ProgressCallback
    check_cancelled: CancellationCheck
    task_id: int
    user_id: int
    file_info: FileInfo
    task_metadata: dict[str, Any]
    post_processors: list[PostIngestProcessor] | None
    library_id: int | None = None


@dataclass(frozen=True)
class UploadResult:
    """Result of a successful book upload."""

    book_id: int
    title: str
    file_size: int


class ProgressTracker:
    """Progress tracker that enforces cancellation checks."""

    def __init__(
        self,
        update_progress: ProgressCallback,
        check_cancelled: CancellationCheck,
        task_id: int,
    ) -> None:
        """Initialize progress tracker.

        Parameters
        ----------
        update_progress : ProgressCallback
            Callback used to update task progress.
        check_cancelled : CancellationCheck
            Callback used to determine if task is cancelled.
        task_id : int
            Task ID for cancellation errors.
        """
        self._update_progress = update_progress
        self._check_cancelled = check_cancelled
        self._task_id = task_id

    def update(self, progress: float, metadata: dict[str, Any] | None = None) -> None:
        """Update progress and enforce cancellation.

        Parameters
        ----------
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict[str, Any] | None
            Optional metadata to include with progress update.

        Raises
        ------
        TaskCancelledError
            If task was cancelled.
        """
        self._update_progress(progress, metadata)
        if self._check_cancelled():
            raise TaskCancelledError(self._task_id)


class UploadFileValidator:
    """Validate uploaded file paths."""

    def validate(self, file_info: FileInfo) -> int:
        """Validate file path and return size.

        Parameters
        ----------
        file_info : FileInfo
            File information for the uploaded file.

        Returns
        -------
        int
            File size in bytes.

        Raises
        ------
        FileNotFoundError
            If file does not exist.
        ValueError
            If path is invalid or points to a directory.
        """
        if not file_info.file_path.exists():
            msg = f"File not found: {file_info.file_path}"
            raise FileNotFoundError(msg)
        if file_info.file_path.is_dir():
            msg = f"file_path is a directory, not a file: {file_info.file_path}"
            raise ValueError(msg)
        if not file_info.file_path.is_file():
            msg = f"file_path is not a valid file: {file_info.file_path}"
            raise ValueError(msg)
        return file_info.file_path.stat().st_size


class LibraryAccessor:
    """Fetch the active library configuration."""

    def get_active_library(
        self,
        session: Session,
        library_id: int | None = None,
        user_id: int | None = None,
    ) -> Library:
        """Return the target library configuration.

        Uses :func:`resolve_task_library` to resolve the library from
        an explicit *library_id*, then per-user active library, then
        global active library.

        Parameters
        ----------
        session : Session
            Database session.
        library_id : int | None
            Explicit library ID captured at enqueue time.
        user_id : int | None
            User identifier for per-user fallback.

        Returns
        -------
        Library
            Library configuration.

        Raises
        ------
        LibraryNotConfiguredError
            If no library could be resolved.
        """
        from bookcard.services.tasks.task_library_resolver import (
            resolve_task_library,
        )

        metadata: dict[str, Any] = {}
        if library_id is not None:
            metadata["library_id"] = library_id
        return resolve_task_library(session, metadata, user_id)


class FileMetadataProvider:
    """Extract file metadata with optional caching."""

    def __init__(
        self,
        metadata_service: BookMetadataService | None = None,
    ) -> None:
        """Initialize metadata provider.

        Parameters
        ----------
        metadata_service : BookMetadataService | None
            Optional metadata service dependency.
        """
        self._metadata_service = metadata_service or BookMetadataService()
        self._cached_metadata: BookMetadata | None = None

    def get(self, file_info: FileInfo) -> BookMetadata | None:
        """Return metadata for the uploaded file.

        Parameters
        ----------
        file_info : FileInfo
            File information for the uploaded file.

        Returns
        -------
        BookMetadata | None
            Extracted metadata if available.
        """
        if self._cached_metadata is not None:
            return self._cached_metadata

        try:
            metadata, _ = self._metadata_service.extract_metadata(
                file_info.file_path, file_info.file_format
            )
        except (ValueError, ImportError, OSError, KeyError, AttributeError) as exc:
            logger.debug(
                "Failed to extract metadata from %s: %s",
                file_info.file_path,
                exc,
            )
            return None

        self._cached_metadata = metadata
        return metadata


class TitleResolver:
    """Resolve upload title from metadata or filename."""

    def resolve(
        self,
        file_metadata: BookMetadata | None,
        task_metadata: dict[str, Any],
        file_info: FileInfo,
    ) -> str:
        """Resolve book title for upload.

        Parameters
        ----------
        file_metadata : BookMetadata | None
            Metadata extracted from the file.
        task_metadata : dict[str, Any]
            Task metadata provided at enqueue time.
        file_info : FileInfo
            File information for the uploaded file.

        Returns
        -------
        str
            Resolved title.
        """
        if file_metadata and file_metadata.title and file_metadata.title != "Unknown":
            return file_metadata.title

        title = task_metadata.get("title")
        if not title:
            title = Path(file_info.filename).stem
        return title


class AuthorResolver:
    """Resolve upload author from file metadata."""

    def resolve(self, file_metadata: BookMetadata | None) -> str | None:
        """Resolve author name for upload.

        Parameters
        ----------
        file_metadata : BookMetadata | None
            Metadata extracted from the file.

        Returns
        -------
        str | None
            Author name if available.
        """
        if file_metadata is None:
            return None

        author = file_metadata.author
        if author and author != "Unknown":
            return author
        return None


class DuplicateChecker:
    """Detect and handle duplicates based on library policy."""

    def __init__(self, handler: BookDuplicateHandler | None = None) -> None:
        """Initialize duplicate checker.

        Parameters
        ----------
        handler : BookDuplicateHandler | None
            Optional duplicate handler dependency.
        """
        self._handler = handler or BookDuplicateHandler()

    def check_and_handle(
        self,
        *,
        library: Library,
        book_service: BookService,
        file_info: FileInfo,
        title: str,
        author_name: str | None,
    ) -> None:
        """Handle duplicates based on library settings.

        Parameters
        ----------
        library : Library
            Active library configuration.
        book_service : BookService
            Book service instance.
        file_info : FileInfo
            File information for the uploaded file.
        title : str
            Book title.
        author_name : str | None
            Author name extracted from file.

        Raises
        ------
        ValueError
            If duplicate found and IGNORE mode is set.
        """
        result = self._handler.check_duplicate(
            library=library,
            file_path=file_info.file_path,
            title=title,
            author_name=author_name,
            file_format=file_info.file_format,
        )

        if result.should_skip:
            msg = (
                "Duplicate book found (book_id="
                f"{result.duplicate_book_id}), skipping per library settings"
            )
            logger.info(msg)
            raise ValueError(msg)

        if result.should_overwrite and result.duplicate_book_id:
            logger.info(
                "Duplicate found (book_id=%d), overwriting per library settings",
                result.duplicate_book_id,
            )
            book_service.delete_book(
                book_id=result.duplicate_book_id,
                delete_files_from_drive=True,
            )


class BookAdder:
    """Add a book to the library via the book service."""

    def add(
        self,
        *,
        book_service: BookService,
        file_info: FileInfo,
        title: str,
        author_name: str | None,
    ) -> int:
        """Add a book to the library.

        Parameters
        ----------
        book_service : BookService
            Book service instance.
        file_info : FileInfo
            File information for the uploaded file.
        title : str
            Book title.
        author_name : str | None
            Author name for the book.

        Returns
        -------
        int
            Newly created book ID.
        """
        return book_service.add_book(
            file_path=file_info.file_path,
            file_format=file_info.file_format,
            title=title,
            author_name=author_name,
        )


class PostProcessorFactory:
    """Build post-ingest processors for uploads."""

    def build(
        self,
        *,
        session: Session,
        library: Library,
        override: list[PostIngestProcessor] | None,
    ) -> list[PostIngestProcessor]:
        """Create post-ingest processors.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        override : list[PostIngestProcessor] | None
            Optional override list.

        Returns
        -------
        list[PostIngestProcessor]
            Post-ingest processors to run.
        """
        if override is not None:
            return override

        processors = [EPUBPostIngestProcessor(session)]
        processors.append(ConversionPostIngestProcessor(session, library=library))
        return processors


class PostProcessorRunner:
    """Run post-ingest processors safely."""

    _handled_errors = (
        ValueError,
        OSError,
        RuntimeError,
        SQLAlchemyError,
        KeyError,
        TypeError,
        AttributeError,
    )

    def run(
        self,
        *,
        session: Session,
        book_id: int,
        library: Library,
        user_id: int,
        processors: list[PostIngestProcessor],
        file_format: str,
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
        user_id : int
            User ID that triggered the upload.
        processors : list[PostIngestProcessor]
            Post-ingest processors to run.
        file_format : str
            Uploaded file format.
        """
        for processor in processors:
            if processor.supports_format(file_format):
                try:
                    with session.begin_nested():
                        processor.process(session, book_id, library, user_id)
                except self._handled_errors:
                    logger.exception(
                        "Post-processor %s failed for book %s",
                        processor.__class__.__name__,
                        book_id,
                    )


class BookUploadWorkflow:
    """Orchestrate the book upload process."""

    def __init__(
        self,
        *,
        file_validator: UploadFileValidator | None = None,
        library_accessor: LibraryAccessor | None = None,
        metadata_provider: FileMetadataProvider | None = None,
        title_resolver: TitleResolver | None = None,
        author_resolver: AuthorResolver | None = None,
        duplicate_checker: DuplicateChecker | None = None,
        book_adder: BookAdder | None = None,
        post_processor_factory: PostProcessorFactory | None = None,
        post_processor_runner: PostProcessorRunner | None = None,
    ) -> None:
        """Initialize workflow with dependencies.

        Parameters
        ----------
        file_validator : UploadFileValidator | None
            Validator for uploaded files.
        library_accessor : LibraryAccessor | None
            Library accessor dependency.
        metadata_provider : FileMetadataProvider | None
            Metadata provider dependency.
        title_resolver : TitleResolver | None
            Title resolver dependency.
        author_resolver : AuthorResolver | None
            Author resolver dependency.
        duplicate_checker : DuplicateChecker | None
            Duplicate checking dependency.
        book_adder : BookAdder | None
            Book adder dependency.
        post_processor_factory : PostProcessorFactory | None
            Post-processor factory dependency.
        post_processor_runner : PostProcessorRunner | None
            Post-processor runner dependency.
        """
        self._file_validator = file_validator or UploadFileValidator()
        self._library_accessor = library_accessor or LibraryAccessor()
        self._metadata_provider = metadata_provider or FileMetadataProvider()
        self._title_resolver = title_resolver or TitleResolver()
        self._author_resolver = author_resolver or AuthorResolver()
        self._duplicate_checker = duplicate_checker or DuplicateChecker()
        self._book_adder = book_adder or BookAdder()
        self._post_processor_factory = post_processor_factory or PostProcessorFactory()
        self._post_processor_runner = post_processor_runner or PostProcessorRunner()

    def execute(self, context: UploadContext) -> UploadResult:
        """Execute the upload workflow.

        Parameters
        ----------
        context : UploadContext
            Runtime context for the upload.

        Returns
        -------
        UploadResult
            Result of the upload operation.
        """
        progress = ProgressTracker(
            context.update_progress,
            context.check_cancelled,
            context.task_id,
        )

        file_size = self._file_validator.validate(context.file_info)
        progress.update(0.1, {"file_size": file_size})

        library = self._library_accessor.get_active_library(
            context.session,
            library_id=context.library_id,
            user_id=context.user_id,
        )
        progress.update(0.2)

        book_service = BookService(library, session=context.session)
        file_metadata = self._metadata_provider.get(context.file_info)
        title = self._title_resolver.resolve(
            file_metadata, context.task_metadata, context.file_info
        )
        author_name = self._author_resolver.resolve(file_metadata)

        progress.update(0.25)
        self._duplicate_checker.check_and_handle(
            library=library,
            book_service=book_service,
            file_info=context.file_info,
            title=title,
            author_name=author_name,
        )
        progress.update(0.3)

        book_id = self._book_adder.add(
            book_service=book_service,
            file_info=context.file_info,
            title=title,
            author_name=author_name,
        )
        progress.update(0.9, {"book_ids": [book_id]})

        processors = self._post_processor_factory.build(
            session=context.session,
            library=library,
            override=context.post_processors,
        )
        self._post_processor_runner.run(
            session=context.session,
            book_id=book_id,
            library=library,
            user_id=context.user_id,
            processors=processors,
            file_format=context.file_info.file_format,
        )

        return UploadResult(book_id=book_id, title=title, file_size=file_size)

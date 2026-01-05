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

"""PVR import workflow orchestration."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bookcard.models.pvr import (
    DownloadItem,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.services.duplicate_detection.book_duplicate_handler import (
    BookDuplicateHandler,
)
from bookcard.services.pvr.importing.book_matching import (
    BookMatchingService,
    BookMetadata,
)
from bookcard.services.pvr.importing.models import FileType
from bookcard.services.pvr.importing.results import (
    FileGroupImportResult,
    FormatAddDecision,
    FormatCheckResult,
    WorkflowResult,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.models.config import Library
    from bookcard.services.ingest.file_discovery_service import FileGroup
    from bookcard.services.pvr.importing.comparison import FileComparer
    from bookcard.services.pvr.importing.file_preparation import FilePreparationService
    from bookcard.services.pvr.importing.file_selection import FileSelectionStrategy
    from bookcard.services.pvr.importing.protocols import (
        BookServiceFactory,
        BookServiceProtocol,
        FileDiscoveryProtocol,
        IngestServiceProtocol,
    )
    from bookcard.services.pvr.importing.transaction import ImportTransaction

logger = logging.getLogger(__name__)


class BookIngestCommand:
    """Encapsulates book ingest workflow with guaranteed order."""

    def __init__(
        self,
        ingest_service: IngestServiceProtocol,
        book_service: BookServiceProtocol,
        download_item: DownloadItem,
    ) -> None:
        """Initialize command."""
        self._ingest = ingest_service
        self._book_service = book_service
        self._download_item = download_item
        self._history_id: int | None = None
        self._book_id: int | None = None

    def create_history(self, file_group: FileGroup) -> BookIngestCommand:
        """Step 1: Create ingest history."""
        self._history_id = self._ingest.process_file_group(file_group)

        tracked_book = self._download_item.tracked_book
        metadata_hint = {
            "title": tracked_book.title,
            "authors": [tracked_book.author],
        }
        if tracked_book.isbn:
            metadata_hint["isbn"] = tracked_book.isbn

        self._ingest.fetch_and_store_metadata(self._history_id, metadata_hint)
        return self

    def add_book(self, main_file: Path) -> BookIngestCommand:
        """Step 2: Add book to library."""
        if self._history_id is None:
            msg = "Must create history first"
            raise RuntimeError(msg)

        tracked_book = self._download_item.tracked_book
        file_format = main_file.suffix.lstrip(".").lower()

        # Prepare metadata from tracked book
        identifiers = []
        if tracked_book.isbn:
            identifiers.append({"type": "isbn", "val": tracked_book.isbn})
        if tracked_book.metadata_source_id and tracked_book.metadata_external_id:
            identifiers.append({
                "type": tracked_book.metadata_source_id,
                "val": tracked_book.metadata_external_id,
            })

        pubdate = None
        if tracked_book.published_date:
            try:
                # Remove Z if present for simple parsing
                date_str = tracked_book.published_date.replace("Z", "+00:00")
                pubdate = datetime.fromisoformat(date_str)
            except ValueError:
                logger.debug("Failed to parse pubdate: %s", tracked_book.published_date)

        rating = None
        if tracked_book.rating is not None:
            rating = int(max(0, min(5, tracked_book.rating)))

        self._book_id = self._ingest.add_book_to_library(
            history_id=self._history_id,
            file_path=main_file,
            file_format=file_format,
            title=tracked_book.title,
            author_name=tracked_book.author,
            description=tracked_book.description,
            publisher=tracked_book.publisher,
            identifiers=identifiers,
            tags=tracked_book.tags,
            rating=rating,
            cover_url=tracked_book.cover_url,
            pubdate=pubdate,
        )
        return self

    def add_formats(
        self,
        formats: list[Path],
        tx: ImportTransaction,  # noqa: ARG002
    ) -> BookIngestCommand:
        """Step 3: Add additional formats."""
        if self._book_id is None:
            msg = "Must add book first"
            raise RuntimeError(msg)

        # In a real implementation, we might want to decouple recording logic
        # But for now, we follow the pattern of IngestService actions
        for file_path in formats:
            file_format = file_path.suffix.lstrip(".").lower()
            try:
                self._ingest.add_format_to_book(
                    book_id=self._book_id,
                    file_path=file_path,
                    file_format=file_format,
                )
            except (ValueError, RuntimeError, OSError) as e:
                logger.warning(
                    "Failed to add format %s to book %d: %s",
                    file_format,
                    self._book_id,
                    e,
                )

        return self

    def finalize(self) -> int:
        """Step 4: Finalize and return book ID."""
        if self._book_id is None or self._history_id is None:
            msg = "Ingest workflow incomplete"
            raise RuntimeError(msg)

        self._ingest.finalize_history(self._history_id, [self._book_id])
        return self._book_id


class BookIngestionOrchestrator(Protocol):
    """Protocol for book ingestion orchestrator."""

    def ingest_all(
        self,
        file_groups: list[FileGroup],
        download_item: DownloadItem,
        tx: ImportTransaction,
    ) -> list[int]:
        """Ingest all file groups."""
        ...


class DefaultBookIngestionOrchestrator:
    """Default implementation of ingestion orchestrator."""

    def __init__(
        self,
        ingest_service: IngestServiceProtocol,
        book_service_factory: BookServiceFactory,
        library: Library,
        file_selector_factory: Callable[[list[str]], FileSelectionStrategy],
        file_comparer: FileComparer,
    ) -> None:
        """Initialize orchestrator."""
        self._ingest_service = ingest_service
        self._book_service_factory = book_service_factory
        self._library = library
        self._file_selector_factory = file_selector_factory
        self._file_comparer = file_comparer

    def ingest_all(
        self,
        file_groups: list[FileGroup],
        download_item: DownloadItem,
        tx: ImportTransaction,
    ) -> list[int]:
        """Ingest all file groups and return list of book IDs."""
        ingested_book_ids: list[int] = []

        for group in file_groups:
            try:
                result = self._ingest_file_group(group, download_item, tx)
                if result.book_id:
                    ingested_book_ids.append(result.book_id)
            except Exception:
                if download_item.id:
                    logger.exception(
                        "Failed to ingest file group %s for download %d",
                        group.book_key,
                        download_item.id,
                    )
                else:
                    logger.exception("Failed to ingest file group %s", group.book_key)

        return ingested_book_ids

    def _ingest_file_group(
        self,
        file_group: FileGroup,
        download_item: DownloadItem,
        tx: ImportTransaction,
    ) -> FileGroupImportResult:
        """Ingest a file group using template method pattern."""
        tracked_book = download_item.tracked_book
        result = FileGroupImportResult()

        book_service = self._book_service_factory.create(self._library)

        try:
            # Check for update scenario
            if (
                tracked_book.status == TrackedBookStatus.COMPLETED
                and tracked_book.matched_book_id
            ):
                book_id = self._update_existing_book_files(
                    file_group,
                    download_item,
                    tracked_book.matched_book_id,
                    book_service,
                    tx,
                )
                if book_id:
                    result.book_id = book_id
                    return result

                logger.warning(
                    "Tracked book %d is COMPLETED but matched book %d update failed. "
                    "Falling back to fresh ingest.",
                    tracked_book.id,
                    tracked_book.matched_book_id,
                )

            # Fresh ingest
            # Select file
            selector = self._file_selector_factory(tracked_book.preferred_formats or [])
            main_file = selector.select_best_file(file_group.files)

            if not main_file:
                logger.warning("No valid file found in group %s", file_group.book_key)
                return result

            # Check for duplicates
            file_format = main_file.suffix.lstrip(".").lower()
            duplicate_handler = BookDuplicateHandler()
            dup_result = duplicate_handler.check_duplicate(
                library=self._library,
                file_path=main_file,
                title=tracked_book.title,
                author_name=tracked_book.author,
                file_format=file_format,
            )

            if dup_result.should_skip:
                logger.info(
                    "Duplicate book found (book_id=%s) and mode is IGNORE. Skipping.",
                    dup_result.duplicate_book_id,
                )
                result.book_id = dup_result.duplicate_book_id
                return result

            if dup_result.should_overwrite and dup_result.duplicate_book_id:
                logger.info(
                    "Duplicate book found (book_id=%s) and mode is OVERWRITE. "
                    "Updating existing book.",
                    dup_result.duplicate_book_id,
                )
                book_id = self._update_existing_book_files(
                    file_group,
                    download_item,
                    dup_result.duplicate_book_id,
                    book_service,
                    tx,
                )
                if book_id:
                    result.book_id = book_id
                    return result

            other_files = [f for f in file_group.files if f != main_file]

            # Use Command Pattern
            book_id = (
                BookIngestCommand(self._ingest_service, book_service, download_item)
                .create_history(file_group)
                .add_book(main_file)
                .add_formats(other_files, tx)
                .finalize()
            )

            # Record main file (missing in Command for now, doing it here to keep Command focused on IngestService)
            # Ideally Command should handle this too if we pass tx and more context
            file_format = main_file.suffix.lstrip(".").lower()
            self._record_file_safely(
                download_item,
                book_service,
                book_id,
                file_format,
                FileType.MAIN,
                main_file,
                tx,
            )

            # Record formats
            for other_file in other_files:
                fmt = other_file.suffix.lstrip(".").lower()
                self._record_file_safely(
                    download_item,
                    book_service,
                    book_id,
                    fmt,
                    FileType.FORMAT,
                    other_file,
                    tx,
                )

            result.book_id = book_id
            result.main_file_added = True

        except Exception as e:
            result.errors.append(str(e))
            raise  # Propagate error to caller

        return result

    def _update_existing_book_files(
        self,
        file_group: FileGroup,
        download_item: DownloadItem,
        book_id: int,
        book_service: BookServiceProtocol,
        tx: ImportTransaction,
    ) -> int | None:
        """Update existing book with any new files from the group."""
        # Verify book exists
        book_rel = book_service.get_book(book_id)
        if not book_rel:
            logger.warning("Matched book %d not found in library", book_id)
            return None

        for file_path in file_group.files:
            file_format = file_path.suffix.lstrip(".").lower()

            check_result = self._check_format_addition(
                book_id, file_path, file_format, book_service
            )

            if check_result.decision == FormatAddDecision.SKIP_IDENTICAL:
                logger.info(
                    "Format %s for book %d exists and is identical.",
                    file_format,
                    book_id,
                )
                continue
            if check_result.decision == FormatAddDecision.UPDATE_DIFFERENT:
                logger.info(
                    "Format %s for book %d exists but differs.", file_format, book_id
                )

            if check_result.should_add:
                try:
                    self._ingest_service.add_format_to_book(
                        book_id=book_id,
                        file_path=file_path,
                        file_format=file_format,
                    )
                    self._record_file_safely(
                        download_item,
                        book_service,
                        book_id,
                        file_format,
                        FileType.FORMAT,
                        file_path,
                        tx,
                    )
                except (ValueError, RuntimeError, OSError) as e:
                    logger.warning(
                        "Failed to add/update format %s for book %d: %s",
                        file_format,
                        book_id,
                        e,
                    )

        return book_id

    def _check_format_addition(
        self,
        book_id: int,
        file_path: Path,
        file_format: str,
        book_service: BookServiceProtocol,
    ) -> FormatCheckResult:
        """Check if format should be added (no side effects)."""
        try:
            existing_path = book_service.get_format_file_path(book_id, file_format)

            if self._file_comparer.are_identical(file_path, existing_path):
                return FormatCheckResult(
                    FormatAddDecision.SKIP_IDENTICAL,
                )

            return FormatCheckResult(
                FormatAddDecision.UPDATE_DIFFERENT,
            )
        except (ValueError, RuntimeError, OSError):
            return FormatCheckResult(FormatAddDecision.ADD_NEW)

    def _record_file_safely(
        self,
        download_item: DownloadItem,
        book_service: BookServiceProtocol,
        book_id: int,
        file_format: str,
        file_type: FileType,
        original_file: Path,
        tx: ImportTransaction,
    ) -> None:
        """Record file with error handling."""
        try:
            path = book_service.get_format_file_path(book_id, file_format)

            from bookcard.models.pvr import TrackedBookFile

            tracked_file = TrackedBookFile(
                tracked_book_id=download_item.tracked_book.id,
                path=str(path),
                filename=original_file.name,
                size_bytes=original_file.stat().st_size,
                file_type=file_type.value,
            )
            tx.add(tracked_file)

        except (ValueError, RuntimeError, OSError) as e:
            logger.warning(
                "Failed to record %s file for book %d: %s", file_type, book_id, e
            )


class PVRImportWorkflow:
    """Encapsulates the entire import workflow."""

    def __init__(
        self,
        file_preparer: FilePreparationService,
        file_discoverer: FileDiscoveryProtocol,
        book_ingester: BookIngestionOrchestrator,
        book_matcher: BookMatchingService,
        book_service_factory: BookServiceFactory,
        library: Library,
    ) -> None:
        """Initialize workflow."""
        self._file_preparer = file_preparer
        self._file_discoverer = file_discoverer
        self._book_ingester = book_ingester
        self._book_matcher = book_matcher
        self._book_service_factory = book_service_factory
        self._library = library

    def execute(
        self,
        download_item: DownloadItem,
        download_path: Path,
        tx: ImportTransaction,
    ) -> WorkflowResult:
        """Execute complete import workflow."""
        with tempfile.TemporaryDirectory(prefix="pvr_import_") as temp_dir:
            temp_path = Path(temp_dir)

            # 1. Prepare files
            try:
                self._file_preparer.prepare_files(download_path, temp_path)
            except (OSError, ValueError) as e:
                msg = f"File preparation failed: {e}"
                raise RuntimeError(msg) from e

            # 2. Discover & Group files
            try:
                book_files = self._file_discoverer.discover_files(temp_path)
            except (FileNotFoundError, ValueError, OSError) as e:
                msg = f"File discovery failed: {e}"
                raise RuntimeError(msg) from e

            if not book_files:
                msg = "No book files discovered"
                raise RuntimeError(msg)

            file_groups = self._file_discoverer.group_files_by_directory(book_files)
            if not file_groups:
                msg = "Failed to group files"
                raise RuntimeError(msg)

            # 3. Ingest groups
            ingested_book_ids = self._book_ingester.ingest_all(
                file_groups, download_item, tx
            )
            if not ingested_book_ids:
                logger.warning(
                    "No files ingested for download %s (likely duplicates or skipped)",
                    download_item.id,
                )

            # 4. Link best match
            book_service = self._book_service_factory.create(self._library)
            best_match_id = self.find_best_match(
                ingested_book_ids, download_item.tracked_book, book_service
            )

            return WorkflowResult(book_id=best_match_id)

    def find_best_match(
        self,
        book_ids: list[int],
        tracked_book: TrackedBook,
        book_service: BookServiceProtocol,
    ) -> int | None:
        """Find best match among ingested books."""
        candidates = []
        for book_id in book_ids:
            try:
                book = book_service.get_book(book_id)
                if book:
                    authors = " & ".join(book.authors) if book.authors else ""
                    meta = BookMetadata(title=book.book.title, author=authors)
                    candidates.append((book_id, meta))
            except Exception:
                logger.exception("Failed to get book details for %d", book_id)
                continue

        target_meta = BookMetadata(title=tracked_book.title, author=tracked_book.author)
        return self._book_matcher.find_best_match(target_meta, candidates)

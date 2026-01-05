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

"""PVR import service.

Handles importing completed downloads into the library.
Refactored to follow SOLID principles:
- SRP: Responsibilities split into dedicated services and workflow.
- DIP: Dependencies depend on abstractions (Protocols).
- OCP: Strategies for file selection and matching.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.services.ingest.file_discovery_service import FileDiscoveryService
from bookcard.services.ingest.ingest_processor_service import IngestProcessorService
from bookcard.services.pvr.importing import (
    BookMatchingService,
    BookServiceFactory,
    FileDiscoveryProtocol,
    FilePreparationService,
    FileSelectionStrategy,
    IngestServiceProtocol,
    PathMappingService,
    PreferenceBasedSelector,
    TrackedBookServiceProtocol,
)
from bookcard.services.pvr.importing.comparison import FileComparer
from bookcard.services.pvr.importing.error_handler import (
    DefaultImportErrorHandler,
    ImportErrorHandler,
)
from bookcard.services.pvr.importing.factories import DefaultBookServiceFactory
from bookcard.services.pvr.importing.results import (
    ImportBatchResult,
    ImportResult,
    ImportStatus,
)
from bookcard.services.pvr.importing.transaction import import_transaction
from bookcard.services.pvr.importing.validation import (
    CompletionStatusValidator,
    CompositeValidator,
    DownloadItemValidator,
    FilePathValidator,
    TrackedBookStateValidator,
)
from bookcard.services.pvr.importing.workflow import (
    DefaultBookIngestionOrchestrator,
    PVRImportWorkflow,
)
from bookcard.services.tracked_book_service import TrackedBookService

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.models.config import Library
    from bookcard.services.pvr.importing.protocols import (
        MetricsRecorder,
        SessionFactory,
    )

logger = logging.getLogger(__name__)


class PVRImportService:
    """Service for importing completed PVR downloads.

    Orchestrates the process via PVRImportWorkflow.
    """

    def __init__(
        self,
        session: Session,
        session_factory: SessionFactory,
        target_library: Library,
        ingest_service: IngestServiceProtocol | None = None,
        tracked_book_service: TrackedBookServiceProtocol | None = None,
        file_discovery_service: FileDiscoveryProtocol | None = None,
        path_mapper: PathMappingService | None = None,
        file_preparer: FilePreparationService | None = None,
        book_matcher: BookMatchingService | None = None,
        file_selector_factory: Callable[[list[str]], FileSelectionStrategy]
        | None = None,
        book_service_factory: BookServiceFactory | None = None,
        file_comparer: FileComparer | None = None,
        validator: DownloadItemValidator | None = None,
        error_handler: ImportErrorHandler | None = None,
        metrics: MetricsRecorder | None = None,
        workflow: PVRImportWorkflow | None = None,
    ) -> None:
        """Initialize PVR import service."""
        self._session = session
        self._session_factory = session_factory
        self._target_library = target_library
        self._ingest_service = ingest_service or IngestProcessorService(session)
        self._tracked_book_service = tracked_book_service or TrackedBookService(session)
        self._file_discovery_service = file_discovery_service or FileDiscoveryService(
            supported_formats=["epub", "mobi", "pdf", "cbz", "cbr", "azw3"],
        )
        self._path_mapper = path_mapper or PathMappingService()
        self._file_preparer = file_preparer or FilePreparationService()
        self._book_matcher = book_matcher or BookMatchingService()
        self._file_selector_factory = file_selector_factory or PreferenceBasedSelector
        self._book_service_factory = book_service_factory or DefaultBookServiceFactory(
            self._ingest_service
        )
        self._file_comparer = file_comparer or FileComparer()
        self._validator = validator or CompositeValidator([
            CompletionStatusValidator(),
            FilePathValidator(),
            TrackedBookStateValidator(),
        ])
        self._error_handler = error_handler or DefaultImportErrorHandler(
            session_factory
        )
        self._metrics = metrics

        # Setup Workflow
        if workflow:
            self._workflow = workflow
        else:
            book_ingester = DefaultBookIngestionOrchestrator(
                ingest_service=self._ingest_service,
                book_service_factory=self._book_service_factory,
                library=self._target_library,
                file_selector_factory=self._file_selector_factory,
                file_comparer=self._file_comparer,
            )
            self._workflow = PVRImportWorkflow(
                file_preparer=self._file_preparer,
                file_discoverer=self._file_discovery_service,
                book_ingester=book_ingester,
                book_matcher=self._book_matcher,
                book_service_factory=self._book_service_factory,
                library=self._target_library,
            )

    def import_pending_downloads(self) -> ImportBatchResult:
        """Find and import all pending completed downloads.

        Returns
        -------
        ImportBatchResult
            Result of the batch import operation.
        """
        statement = (
            select(DownloadItem)
            .join(TrackedBook)
            .where(DownloadItem.status == DownloadItemStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.FAILED)
        )

        items = self._session.exec(statement).all()
        results = ImportBatchResult()

        for item in items:
            try:
                result = self.process_completed_download(item)
                results.add_result(result, item.id)
            except (OSError, ValueError, RuntimeError) as e:
                # Only catch expected errors, let critical ones propagate
                if item.id:
                    logger.exception("Error processing download item %d", item.id)
                    results.add_failed(item.id, str(e))
                else:
                    logger.exception("Error processing download item (no ID)")
                    # Can't add to results by ID if no ID, but count as failed
                    results.failed += 1

        return results

    def process_completed_download(self, download_item: DownloadItem) -> ImportResult:
        """Process a completed download item using the workflow.

        Parameters
        ----------
        download_item : DownloadItem
            The completed download item to process.

        Returns
        -------
        ImportResult
            Result of the import operation.
        """
        if download_item.id is None:
            return ImportResult(
                ImportStatus.FAILED, error_message="Download item has no ID"
            )
        item_id = download_item.id

        # Validate
        validation = self._validator.validate(download_item)
        if not validation.is_valid:
            return ImportResult(
                ImportStatus.FAILED, error_message=validation.error_message
            )

        download_path = self._path_mapper.resolve_download_path(download_item)
        if not download_path.exists():
            msg = f"Download path does not exist: {download_path}"
            self._error_handler.handle(RuntimeError(msg), download_item)
            return ImportResult(ImportStatus.FAILED, error_message=msg)

        logger.info("Processing completed download %d: %s", item_id, download_path)

        # Execute in transaction
        try:
            # Use session factory to ensure clean session handling
            with self._session_factory.create_session() as session:
                # We need to attach the item to the new session if it's detached?
                # Or re-fetch. Since we have item_id, it's safer to re-fetch to ensure
                # it's attached to the current session.
                # However, download_item passed in might be from self._session (the list loop).
                # If we use it in a new session, we might get errors if we try to modify it
                # without merging.
                # But workflow executes mainly on IDs or passed objects.
                # Workflow uses download_item.tracked_book.

                # Best practice: Fetch fresh in the new session.
                item = session.get(DownloadItem, item_id)
                if not item:
                    msg = f"Download item {item_id} not found in new session"
                    self._raise_runtime_error(msg)

                with import_transaction(session) as tx:
                    result = self._workflow.execute(item, download_path, tx)

                    # Update tracked book status if successful (even if no new book created)
                    if item.tracked_book:
                        item.tracked_book.status = TrackedBookStatus.COMPLETED
                        if result.book_id:
                            item.tracked_book.matched_book_id = result.book_id
                        tx.add(item.tracked_book)

                    if self._metrics:
                        self._metrics.increment(
                            "pvr.import.success",
                            tags={"library": self._target_library.name},
                        )

                    return ImportResult(ImportStatus.SUCCESS, book_id=result.book_id)

        except Exception as e:
            logger.exception("Import failed for item %d", item_id)
            self._error_handler.handle(e, download_item)

            if self._metrics:
                self._metrics.increment(
                    "pvr.import.failed", tags={"error_type": type(e).__name__}
                )

            return ImportResult(ImportStatus.FAILED, error_message=str(e))

    def _raise_runtime_error(self, message: str) -> None:
        """Raise RuntimeError with the given message."""
        raise RuntimeError(message)

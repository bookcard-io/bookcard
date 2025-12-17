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

"""Book format conversion task implementation.

Handles format conversion in the background with progress tracking.
Refactored to follow SOLID principles, DRY, SRP, IoC, and SoC.
"""

import logging
from typing import Any

from bookcard.models.config import Library
from bookcard.models.conversion import ConversionMethod, ConversionStatus
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.conversion import create_conversion_service
from bookcard.services.conversion_utils import raise_conversion_error
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import ProgressCallback, WorkerContext
from bookcard.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
)

logger = logging.getLogger(__name__)


class BookConvertTask(BaseTask):
    """Task for converting a book format.

    Handles format conversion in the background with progress tracking.
    Refactored to follow SOLID principles.

    Attributes
    ----------
    _book_id : int
        Calibre book ID to convert.
    _source_format : str
        Source format (e.g., "MOBI", "AZW3").
    _target_format : str
        Target format (e.g., "EPUB", "KEPUB").
    _conversion_method : ConversionMethod
        How conversion was triggered.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize book convert task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing book_id, source_format, target_format,
            conversion_method (optional).

        Raises
        ------
        ValueError
            If required metadata fields are missing or invalid.
        """
        super().__init__(task_id, user_id, metadata)
        self._book_id = self._require_int("book_id", metadata)
        self._source_format = self._require_str("source_format", metadata)
        self._target_format = self._require_str("target_format", metadata)
        self._conversion_method = ConversionMethod(
            metadata.get("conversion_method", ConversionMethod.MANUAL.value)
        )

    def _require_int(self, key: str, metadata: dict[str, Any]) -> int:
        """Require an integer value from metadata.

        Parameters
        ----------
        key : str
            Metadata key.
        metadata : dict[str, Any]
            Metadata dictionary.

        Returns
        -------
        int
            Integer value.

        Raises
        ------
        ValueError
            If key is missing.
        TypeError
            If value is not an integer.
        """
        value = metadata.get(key)
        if value is None:
            msg = f"Missing required metadata key: {key}"
            raise ValueError(msg)
        if not isinstance(value, int):
            msg = f"Metadata key {key} must be an integer, got {type(value).__name__}"
            raise TypeError(msg)
        return value

    def _require_str(self, key: str, metadata: dict[str, Any]) -> str:
        """Require a string value from metadata.

        Parameters
        ----------
        key : str
            Metadata key.
        metadata : dict[str, Any]
            Metadata dictionary.

        Returns
        -------
        str
            String value.

        Raises
        ------
        ValueError
            If key is missing.
        TypeError
            If value is not a string.
        """
        value = metadata.get(key)
        if value is None:
            msg = f"Missing required metadata key: {key}"
            raise ValueError(msg)
        if not isinstance(value, str):
            msg = f"Metadata key {key} must be a string, got {type(value).__name__}"
            raise TypeError(msg)
        return value

    def _check_cancellation(self) -> None:
        """Check if task has been cancelled.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def _get_active_library(self, context: WorkerContext) -> Library:  # type: ignore[name-defined]
        """Get active library configuration.

        Parameters
        ----------
        context : WorkerContext
            Worker context containing session.

        Returns
        -------
        Library
            Active library configuration.

        Raises
        ------
        LibraryNotConfiguredError
            If no active library is configured.
        TaskCancelledError
            If task has been cancelled.
        """
        self._check_cancellation()

        library_repo = LibraryRepository(context.session)
        library_service = LibraryService(context.session, library_repo)
        library = library_service.get_active_library()
        if library is None:
            raise LibraryNotConfiguredError

        return library

    def _update_progress_or_cancel(
        self,
        progress: float,
        update_progress: ProgressCallback,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update progress or check for cancellation.

        Parameters
        ----------
        progress : float
            Progress value (0.0 to 1.0).
        update_progress : ProgressCallback
            Progress update callback.
        metadata : dict[str, Any] | None
            Optional metadata to include.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        self._check_cancellation()
        update_progress(progress, metadata or {})

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute book conversion task.

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

            # Update progress: 0.1 - task started
            self._update_progress_or_cancel(0.1, context.update_progress)

            # Get active library
            library = self._get_active_library(context)

            # Update progress: 0.2 - library found
            self._update_progress_or_cancel(0.2, context.update_progress)

            # Check for existing conversion
            conversion_service = create_conversion_service(context.session, library)
            existing = conversion_service.check_existing_conversion(
                self._book_id, self._source_format, self._target_format
            )

            if existing:
                # Conversion already exists - update task metadata
                self.set_metadata("existing_conversion_id", existing.id)
                self.set_metadata(
                    "message",
                    f"Conversion from {self._source_format} to {self._target_format} already exists",
                )
                self._update_progress_or_cancel(1.0, context.update_progress)
                logger.info(
                    "Conversion already exists: book_id=%d, %s -> %s",
                    self._book_id,
                    self._source_format,
                    self._target_format,
                )
                return

            # Update progress: 0.3 - ready to convert
            self._update_progress_or_cancel(0.3, context.update_progress)

            # Get user setting for backup preference
            # For now, default to backing up
            # In the future, we could check user settings here
            backup_original = True

            # Perform conversion
            conversion = conversion_service.convert_book(
                book_id=self._book_id,
                original_format=self._source_format,
                target_format=self._target_format,
                user_id=self.user_id,
                conversion_method=self._conversion_method,
                backup_original=backup_original,
            )

            # Update progress: 0.9 - conversion complete
            self._update_progress_or_cancel(
                0.9,
                context.update_progress,
                {
                    "conversion_id": conversion.id,
                    "status": conversion.status.value,
                },
            )

            # Update progress: 1.0 - complete
            self._update_progress_or_cancel(1.0, context.update_progress)

            if conversion.status == ConversionStatus.COMPLETED:
                logger.info(
                    "Conversion completed: book_id=%d, %s -> %s",
                    self._book_id,
                    self._source_format,
                    self._target_format,
                )
            else:
                error_msg = conversion.error_message or "Unknown error"
                logger.error(
                    "Conversion failed: book_id=%d, %s -> %s, error=%s",
                    self._book_id,
                    self._source_format,
                    self._target_format,
                    error_msg,
                )

                msg = f"Conversion failed: {error_msg}"
                raise_conversion_error(msg)

        except TaskCancelledError:
            logger.info("Conversion task %d was cancelled", self.task_id)
            raise

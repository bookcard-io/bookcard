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

"""Book DRM stripping task implementation.

Runs DeDRM on an existing book format and, if it produces a different output,
adds the result as an additional format for the same book (without modifying
the original format).
"""

from __future__ import annotations

import hashlib
import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.dedrm_service import DeDRMService
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import ProgressCallback, WorkerContext
from bookcard.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.models.config import Library


class BookStripDrmTask(BaseTask):
    """Task for stripping DRM (if present) from a book format.

    Attributes
    ----------
    _book_id : int
        Calibre book ID to process.
    _source_format : str
        Existing format to attempt DeDRM on (e.g. "AZW3").
    _output_format : str
        Format name to store the DRM-free copy under (e.g. "AZW3_NODRM").
    """

    def __init__(self, task_id: int, user_id: int, metadata: dict[str, Any]) -> None:
        """Initialize book DRM stripping task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing book_id, source_format, output_format.

        Raises
        ------
        ValueError
            If required metadata keys are missing.
        TypeError
            If metadata values are of incorrect types.
        """
        super().__init__(task_id, user_id, metadata)
        self._book_id = self._require_int("book_id", metadata)
        self._source_format = self._require_str("source_format", metadata).upper()
        self._output_format = self._require_str("output_format", metadata).upper()
        self._dedrm_service = DeDRMService()

    @staticmethod
    def _require_int(key: str, metadata: dict[str, Any]) -> int:
        value = metadata.get(key)
        if value is None:
            msg = f"Missing required metadata key: {key}"
            raise ValueError(msg)
        if not isinstance(value, int):
            msg = f"Metadata key {key} must be an integer, got {type(value).__name__}"
            raise TypeError(msg)
        return value

    @staticmethod
    def _require_str(key: str, metadata: dict[str, Any]) -> str:
        value = metadata.get(key)
        if value is None:
            msg = f"Missing required metadata key: {key}"
            raise ValueError(msg)
        if not isinstance(value, str):
            msg = f"Metadata key {key} must be a string, got {type(value).__name__}"
            raise TypeError(msg)
        return value

    def _check_cancellation(self) -> None:
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def _get_active_library(self, context: WorkerContext) -> Library:
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
        self._check_cancellation()
        update_progress(progress, metadata or {})

    @staticmethod
    def _sha256_path(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute DRM stripping task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, update_progress, task_service.
        """
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        else:
            context = worker_context

        processed_path = None
        try:
            self._update_progress_or_cancel(0.1, context.update_progress)

            library = self._get_active_library(context)
            self._update_progress_or_cancel(0.2, context.update_progress)

            book_service = BookService(library, session=context.session)
            source_path = book_service.get_format_file_path(
                self._book_id, self._source_format
            )
            self.set_metadata("source_format", self._source_format)
            self.set_metadata("output_format", self._output_format)
            self._update_progress_or_cancel(
                0.35,
                context.update_progress,
                {"source_format": self._source_format},
            )

            processed_path = self._dedrm_service.strip_drm(source_path)
            self._update_progress_or_cancel(0.7, context.update_progress)

            original_hash = self._sha256_path(source_path)
            processed_hash = self._sha256_path(processed_path)
            did_strip = original_hash != processed_hash
            self.set_metadata("did_strip", did_strip)

            if did_strip:
                book_service.add_format(
                    book_id=self._book_id,
                    file_path=processed_path,
                    file_format=self._output_format,
                    replace=False,
                )
                self._update_progress_or_cancel(
                    0.95,
                    context.update_progress,
                    {"output_format": self._output_format},
                )

            self._update_progress_or_cancel(1.0, context.update_progress, self.metadata)
        except TaskCancelledError:
            logger.info("DeDRM task %d was cancelled", self.task_id)
            raise
        finally:
            if processed_path is not None:
                with suppress(OSError):
                    processed_path.unlink()

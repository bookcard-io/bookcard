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

"""Book DeDRM orchestration service.

Initiates DRM stripping tasks for existing Calibre books.
Follows SRP by focusing solely on task orchestration and format selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bookcard.models.tasks import TaskType

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.services.book_service import BookService
    from bookcard.services.tasks.base import TaskRunner


@dataclass
class DeDRMInitiationResult:
    """Result of initiating a DRM stripping task.

    Attributes
    ----------
    task_id : int
        Task ID if enqueued, 0 if request is a no-op.
    message : str | None
        Optional message describing the result.
    """

    task_id: int
    message: str | None = None


class BookDeDRMOrchestrationService:
    """Service for initiating book DRM stripping tasks.

    Parameters
    ----------
    session : Session
        Database session (used only for parity with other orchestration services).
    book_service : BookService
        Book service for retrieving book data and formats.
    task_runner : TaskRunner | None
        Task runner for enqueueing background tasks. Optional for read-only use.
    """

    _FORMAT_PREFERENCE: tuple[str, ...] = (
        # Prefer Kindle formats first
        "KFX",
        "AZW3",
        "AZW",
        "MOBI",
        # Then common ebook formats
        "EPUB",
        "PDF",
    )

    def __init__(
        self,
        session: Session,
        book_service: BookService,
        task_runner: TaskRunner | None = None,
    ) -> None:
        self._session = session
        self._book_service = book_service
        self._task_runner = task_runner

    def initiate_strip_drm(self, book_id: int, user_id: int) -> DeDRMInitiationResult:
        """Initiate a DRM stripping operation for a book.

        Chooses a source format from the book's available formats and enqueues
        a background task.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        user_id : int
            User ID initiating the operation.

        Returns
        -------
        DeDRMInitiationResult
            Result containing task ID and optional message.

        Raises
        ------
        ValueError
            If book not found or no formats are available.
        RuntimeError
            If task runner is unavailable.
        """
        existing_book = self._book_service.get_book_full(book_id)
        if existing_book is None:
            msg = "book_not_found"
            raise ValueError(msg)

        formats = existing_book.formats or []
        if not formats:
            return DeDRMInitiationResult(
                task_id=0, message="no_formats_available_for_dedrm"
            )

        source_format = self._choose_source_format(formats)
        if not source_format:
            return DeDRMInitiationResult(
                task_id=0, message="no_supported_formats_for_dedrm"
            )

        output_format = self._choose_unique_output_format(
            formats=formats, source_format=source_format
        )

        if self._task_runner is None:
            msg = "Task runner not available"
            raise RuntimeError(msg)

        task_id = self._task_runner.enqueue(
            task_type=TaskType.BOOK_STRIP_DRM,
            payload={
                "book_id": book_id,
                "source_format": source_format,
                "output_format": output_format,
            },
            user_id=user_id,
            metadata={
                "task_type": TaskType.BOOK_STRIP_DRM,
                "book_id": book_id,
                "source_format": source_format,
                "output_format": output_format,
            },
        )

        return DeDRMInitiationResult(
            task_id=task_id,
            message=f"DRM stripping queued for {source_format}",
        )

    def _choose_source_format(self, formats: list[dict]) -> str | None:
        existing = {str(f.get("format", "")).upper() for f in formats}
        for fmt in self._FORMAT_PREFERENCE:
            if fmt in existing:
                return fmt
        # Fallback to first listed format
        for f in formats:
            candidate = str(f.get("format", "")).upper()
            if candidate:
                return candidate
        return None

    @staticmethod
    def _choose_unique_output_format(*, formats: list[dict], source_format: str) -> str:
        existing = {str(f.get("format", "")).upper() for f in formats}
        base = f"{source_format.upper()}_NODRM"
        if base not in existing:
            return base
        for i in range(1, 100):
            candidate = f"{base}_{i}"
            if candidate not in existing:
                return candidate
        # Extremely unlikely; still provide a deterministic fallback
        return f"{base}_X"

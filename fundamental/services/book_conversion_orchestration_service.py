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

"""Book conversion orchestration service.

Handles the business logic for initiating book format conversions.
Follows SRP by focusing solely on conversion orchestration operations.
"""

import math
from dataclasses import dataclass

from sqlmodel import Session, desc, select

from fundamental.models.config import Library
from fundamental.models.conversion import BookConversion, ConversionStatus
from fundamental.models.tasks import TaskType
from fundamental.services.book_service import BookService
from fundamental.services.conversion import create_conversion_service
from fundamental.services.tasks.base import TaskRunner


@dataclass
class ConversionInitiationResult:
    """Result of initiating a book conversion.

    Attributes
    ----------
    task_id : int
        Task ID if conversion was enqueued, 0 if existing conversion found.
    existing_conversion : BookConversion | None
        Existing conversion if one was found.
    message : str | None
        Optional message about the result.
    """

    task_id: int
    existing_conversion: BookConversion | None = None
    message: str | None = None


@dataclass
class ConversionListResult:
    """Result of getting conversion list.

    Attributes
    ----------
    conversions : list[BookConversion]
        List of conversion records for the current page.
    total : int
        Total number of conversions.
    page : int
        Current page number.
    page_size : int
        Number of items per page.
    total_pages : int
        Total number of pages.
    """

    conversions: list[BookConversion]
    total: int
    page: int
    page_size: int
    total_pages: int


class BookConversionOrchestrationService:
    """Service for orchestrating book format conversions.

    Handles business logic for initiating conversions: checking existing
    conversions, validating formats, and enqueueing tasks.

    Parameters
    ----------
    session : Session
        Database session.
    book_service : BookService
        Book service for retrieving book data.
    library : Library
        Active library configuration.
    task_runner : TaskRunner
        Task runner for enqueueing conversion tasks.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        book_service: BookService,
        library: Library,
        task_runner: TaskRunner | None = None,
    ) -> None:
        """Initialize conversion orchestration service.

        Parameters
        ----------
        session : Session
            Database session.
        book_service : BookService
            Book service for retrieving book data.
        library : Library
            Active library configuration.
        task_runner : TaskRunner | None
            Task runner for enqueueing conversion tasks. Optional for read operations.
        """
        self._session = session
        self._book_service = book_service
        self._library = library
        self._task_runner = task_runner
        self._conversion_service = create_conversion_service(session, library)

    def initiate_conversion(
        self,
        book_id: int,
        source_format: str,
        target_format: str,
        user_id: int,
    ) -> ConversionInitiationResult:
        """Initiate a book format conversion.

        Checks for existing conversions, validates source format exists,
        and enqueues a conversion task if needed.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        source_format : str
            Source format to convert from.
        target_format : str
            Target format to convert to.
        user_id : int
            User ID initiating the conversion.

        Returns
        -------
        ConversionInitiationResult
            Result containing task ID, existing conversion info, and message.

        Raises
        ------
        ValueError
            If book not found, source format not found, or library not found.
        RuntimeError
            If task runner is unavailable.
        """
        # Verify book exists
        existing_book = self._book_service.get_book_full(book_id)
        if existing_book is None:
            error_msg = "book_not_found"
            raise ValueError(error_msg)

        # Check for existing conversion
        existing = self._conversion_service.check_existing_conversion(
            book_id,
            source_format,
            target_format,
        )

        if existing and existing.status == ConversionStatus.COMPLETED:
            # Return friendly message about existing conversion
            completed_date = (
                existing.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                if existing.completed_at
                else "previously"
            )
            message = (
                f"This book has already been converted from {source_format} "
                f"to {target_format} on {completed_date}"
            )
            return ConversionInitiationResult(
                task_id=0,
                existing_conversion=existing,
                message=message,
            )

        # Validate that source format exists
        formats = existing_book.formats or []
        source_format_upper = source_format.upper()
        target_format_upper = target_format.upper()
        format_found = any(
            str(f.get("format", "")).upper() == source_format_upper for f in formats
        )
        if not format_found:
            error_msg = f"source_format_not_found: {source_format}"
            raise ValueError(error_msg)

        # Check if target format already exists (duplicate detection)
        target_format_exists = any(
            str(f.get("format", "")).upper() == target_format_upper for f in formats
        )
        if target_format_exists:
            # Target format file already exists - no-op and report conversion exists
            message = (
                f"This book already has the {target_format} format. "
                f"No conversion needed."
            )
            return ConversionInitiationResult(
                task_id=0,
                existing_conversion=None,
                message=message,
            )

        # Check task runner is available
        if self._task_runner is None:
            error_msg = "Task runner not available"
            raise RuntimeError(error_msg)

        # Enqueue conversion task
        task_id = self._task_runner.enqueue(
            task_type=TaskType.BOOK_CONVERT,
            payload={
                "book_id": book_id,
                "source_format": source_format,
                "target_format": target_format,
            },
            user_id=user_id,
            metadata={
                "task_type": TaskType.BOOK_CONVERT,
                "book_id": book_id,
                "source_format": source_format,
                "target_format": target_format,
                "conversion_method": "manual",
            },
        )

        return ConversionInitiationResult(task_id=task_id)

    def get_conversions(
        self,
        book_id: int,
        page: int,
        page_size: int,
    ) -> ConversionListResult:
        """Get paginated conversion history for a book.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        ConversionListResult
            Paginated list of conversion records.

        Raises
        ------
        ValueError
            If book not found.
        """
        # Verify book exists
        existing_book = self._book_service.get_book_full(book_id)
        if existing_book is None:
            error_msg = "book_not_found"
            raise ValueError(error_msg)

        # Build query
        stmt = (
            select(BookConversion)
            .where(BookConversion.book_id == book_id)
            .order_by(desc(BookConversion.created_at))
        )

        # Get total count
        count_stmt = select(BookConversion).where(BookConversion.book_id == book_id)
        total = len(list(self._session.exec(count_stmt).all()))

        # Apply pagination
        offset = (page - 1) * page_size
        conversions = list(
            self._session.exec(stmt.offset(offset).limit(page_size)).all()
        )

        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return ConversionListResult(
            conversions=conversions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

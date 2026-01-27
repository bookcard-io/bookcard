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

"""Reading service for managing reading progress, sessions, and status.

Business logic for tracking reading progress, managing reading sessions,
and handling read status with automatic marking at 90% threshold.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bookcard.models.reading import (
    ReadingProgress,
    ReadingSession,
    ReadStatus,
    ReadStatusEnum,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.reading_repository import (
        AnnotationRepository,
        ReadingProgressRepository,
        ReadingSessionRepository,
        ReadStatusRepository,
    )

# Auto-mark threshold: 90%
AUTO_MARK_THRESHOLD = 0.90


class ReadingService:
    """Service for managing reading progress, sessions, and status.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    progress_repo : ReadingProgressRepository
        Repository for reading progress operations.
    session_repo : ReadingSessionRepository
        Repository for reading session operations.
    status_repo : ReadStatusRepository
        Repository for read status operations.
    annotation_repo : AnnotationRepository
        Repository for annotation operations.
    """

    def __init__(
        self,
        session: Session,
        progress_repo: ReadingProgressRepository,
        session_repo: ReadingSessionRepository,
        status_repo: ReadStatusRepository,
        annotation_repo: AnnotationRepository | None = None,
    ) -> None:
        """Initialize reading service.

        Parameters
        ----------
        session : Session
            Database session.
        progress_repo : ReadingProgressRepository
            Reading progress repository.
        session_repo : ReadingSessionRepository
            Reading session repository.
        status_repo : ReadStatusRepository
            Read status repository.
        annotation_repo : AnnotationRepository | None
            Annotation repository (optional).
        """
        self._session = session
        self._progress_repo = progress_repo
        self._session_repo = session_repo
        self._status_repo = status_repo
        self._annotation_repo = annotation_repo

    def update_progress(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        book_format: str,
        progress: float,
        cfi: str | None = None,
        page_number: int | None = None,
        device: str | None = None,
        spread_mode: bool | None = None,
        reading_direction: str | None = None,
    ) -> ReadingProgress:
        """Update reading progress for a book.

        Automatically marks book as read when progress reaches 90%.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        book_format : str
            Book format (EPUB, PDF, etc.).
        progress : float
            Reading progress (0.0 to 1.0).
        cfi : str | None
            Canonical Fragment Identifier for EPUB (optional).
        page_number : int | None
            Page number for PDF or comic formats (optional).
        device : str | None
            Device identifier (optional).
        spread_mode : bool | None
            Whether reading in spread mode for comics (optional).
        reading_direction : str | None
            Reading direction for comics: 'ltr', 'rtl', or 'vertical' (optional).

        Returns
        -------
        ReadingProgress
            Updated or created reading progress.

        Raises
        ------
        ValueError
            If progress is outside valid range (0.0 to 1.0).
        """
        if not 0.0 <= progress <= 1.0:
            msg = f"Progress must be between 0.0 and 1.0, got {progress}"
            raise ValueError(msg)

        # Get or create reading progress
        existing = self._progress_repo.get_by_user_book_format(
            user_id,
            library_id,
            book_id,
            book_format,
        )

        if existing is None:
            progress_obj = ReadingProgress(
                user_id=user_id,
                library_id=library_id,
                book_id=book_id,
                format=book_format,
                progress=progress,
                cfi=cfi,
                page_number=page_number,
                device=device,
                spread_mode=spread_mode,
                reading_direction=reading_direction,
                updated_at=datetime.now(UTC),
            )
            self._progress_repo.add(progress_obj)
        else:
            existing.progress = progress
            if cfi is not None:
                existing.cfi = cfi
            if page_number is not None:
                existing.page_number = page_number
            if device is not None:
                existing.device = device
            if spread_mode is not None:
                existing.spread_mode = spread_mode
            if reading_direction is not None:
                existing.reading_direction = reading_direction
            existing.updated_at = datetime.now(UTC)
            progress_obj = existing

        self._session.flush()

        # Update read status if progress >= threshold
        if progress >= AUTO_MARK_THRESHOLD:
            self._auto_mark_as_read(user_id, library_id, book_id, progress)

        # Update first_opened_at if not set and progress > 0
        if progress > 0:
            self._ensure_first_opened(user_id, library_id, book_id)

        return progress_obj

    def start_session(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        book_format: str,
        device: str | None = None,
    ) -> ReadingSession:
        """Start a reading session.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        book_format : str
            Book format (EPUB, PDF, etc.).
        device : str | None
            Device identifier (optional).

        Returns
        -------
        ReadingSession
            Created reading session.
        """
        # Get current progress (default to 0.0)
        progress = self.get_progress(user_id, library_id, book_id, book_format)
        progress_start = progress.progress if progress else 0.0

        session = ReadingSession(
            user_id=user_id,
            library_id=library_id,
            book_id=book_id,
            format=book_format,
            started_at=datetime.now(UTC),
            progress_start=progress_start,
            device=device,
        )
        self._session_repo.add(session)
        self._session.flush()

        # Update first_opened_at if not set
        self._ensure_first_opened(user_id, library_id, book_id)

        return session

    def end_session(
        self,
        session_id: int,
        progress_end: float,
    ) -> ReadingSession:
        """End a reading session.

        Parameters
        ----------
        session_id : int
            Session ID.
        progress_end : float
            Final reading progress (0.0 to 1.0).

        Returns
        -------
        ReadingSession
            Updated reading session.

        Raises
        ------
        ValueError
            If session not found, already ended, or progress invalid.
        """
        if not 0.0 <= progress_end <= 1.0:
            msg = f"Progress must be between 0.0 and 1.0, got {progress_end}"
            raise ValueError(msg)

        session = self._session_repo.get(session_id)
        if session is None:
            msg = f"Reading session {session_id} not found"
            raise ValueError(msg)

        if session.ended_at is not None:
            msg = f"Reading session {session_id} is already ended"
            raise ValueError(msg)

        session.ended_at = datetime.now(UTC)
        session.progress_end = progress_end
        self._session.flush()

        # Update reading progress table so it appears in recent reads
        # This ensures the progress is saved and will show up in the recent reads list
        # update_progress handles creating/updating the record and auto-marking as read
        self.update_progress(
            user_id=session.user_id,
            library_id=session.library_id,
            book_id=session.book_id,
            book_format=session.format,
            progress=progress_end,
            device=session.device,
        )

        return session

    def mark_as_read(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        manual: bool = True,
    ) -> ReadStatus:
        """Manually mark a book as read.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        manual : bool
            Whether this is a manual marking (default: True).

        Returns
        -------
        ReadStatus
            Updated or created read status.
        """
        # Get current progress to determine progress_when_marked
        progress = self.get_progress(user_id, library_id, book_id, "EPUB")
        progress_when_marked = progress.progress if progress else None

        status = self._status_repo.get_by_user_book(user_id, library_id, book_id)
        if status is None:
            status = ReadStatus(
                user_id=user_id,
                library_id=library_id,
                book_id=book_id,
                status=ReadStatusEnum.READ,
                marked_as_read_at=datetime.now(UTC),
                auto_marked=not manual,
                progress_when_marked=progress_when_marked,
            )
            self._status_repo.add(status)
        else:
            status.status = ReadStatusEnum.READ
            status.marked_as_read_at = datetime.now(UTC)
            status.auto_marked = not manual
            if progress_when_marked is not None:
                status.progress_when_marked = progress_when_marked

        self._session.flush()
        return status

    def mark_as_unread(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
    ) -> ReadStatus:
        """Mark a book as unread.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.

        Returns
        -------
        ReadStatus
            Updated or created read status.
        """
        status = self._status_repo.get_by_user_book(user_id, library_id, book_id)
        if status is None:
            status = ReadStatus(
                user_id=user_id,
                library_id=library_id,
                book_id=book_id,
                status=ReadStatusEnum.NOT_READ,
            )
            self._status_repo.add(status)
        else:
            status.status = ReadStatusEnum.NOT_READ
            status.marked_as_read_at = None
            status.auto_marked = False
            status.progress_when_marked = None

        self._session.flush()
        return status

    def get_progress(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        book_format: str,
    ) -> ReadingProgress | None:
        """Get current reading progress for a book.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        book_format : str
            Book format (EPUB, PDF, etc.).

        Returns
        -------
        ReadingProgress | None
            Reading progress if found, None otherwise.
        """
        return self._progress_repo.get_by_user_book_format(
            user_id,
            library_id,
            book_id,
            book_format,
        )

    def get_recent_reads(
        self,
        user_id: int,
        library_id: int,
        limit: int = 10,
    ) -> list[ReadingProgress]:
        """Get recent reads for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        limit : int
            Maximum number of records to return (default: 10).

        Returns
        -------
        list[ReadingProgress]
            List of recent reading progress records.
        """
        return self._progress_repo.get_recent_reads(user_id, library_id, limit)

    def get_reading_history(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        limit: int = 50,
    ) -> list[ReadingSession]:
        """Get reading history for a book.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        limit : int
            Maximum number of records to return (default: 50).

        Returns
        -------
        list[ReadingSession]
            List of reading sessions for the book.
        """
        return self._session_repo.get_sessions_by_book(
            user_id,
            library_id,
            book_id,
            limit,
        )

    def get_read_status(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
    ) -> ReadStatus | None:
        """Get read status for a book.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.

        Returns
        -------
        ReadStatus | None
            Read status if found, None otherwise.
        """
        return self._status_repo.get_by_user_book(user_id, library_id, book_id)

    def _auto_mark_as_read(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        progress: float,
    ) -> None:
        """Automatically mark book as read when progress reaches threshold.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        progress : float
            Current progress percentage.
        """
        status = self._status_repo.get_by_user_book(user_id, library_id, book_id)
        if status is None:
            status = ReadStatus(
                user_id=user_id,
                library_id=library_id,
                book_id=book_id,
                status=ReadStatusEnum.READ,
                marked_as_read_at=datetime.now(UTC),
                auto_marked=True,
                progress_when_marked=progress,
            )
            self._status_repo.add(status)
        elif status.status != ReadStatusEnum.READ:
            # Only auto-mark if not already manually marked as read
            status.status = ReadStatusEnum.READ
            status.marked_as_read_at = datetime.now(UTC)
            status.auto_marked = True
            status.progress_when_marked = progress

        self._session.flush()

    def _ensure_first_opened(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
    ) -> None:
        """Ensure first_opened_at is set for a book.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        """
        status = self._status_repo.get_by_user_book(user_id, library_id, book_id)
        if status is None:
            status = ReadStatus(
                user_id=user_id,
                library_id=library_id,
                book_id=book_id,
                status=ReadStatusEnum.READING,
                first_opened_at=datetime.now(UTC),
            )
            self._status_repo.add(status)
        elif status.first_opened_at is None:
            status.first_opened_at = datetime.now(UTC)
            if status.status == ReadStatusEnum.NOT_READ:
                status.status = ReadStatusEnum.READING

        self._session.flush()

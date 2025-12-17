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

"""Repository layer for reading-related persistence operations.

Provides data access for reading progress, sessions, read status, and annotations.
"""

from __future__ import annotations

from sqlalchemy import desc
from sqlmodel import Session, select

from bookcard.models.reading import (
    Annotation,
    ReadingProgress,
    ReadingSession,
    ReadStatus,
    ReadStatusEnum,
)
from bookcard.repositories.base import Repository


class ReadingProgressRepository(Repository[ReadingProgress]):
    """Repository for ReadingProgress entities.

    Provides CRUD operations and specialized queries for reading progress.
    """

    def __init__(self, session: Session) -> None:
        """Initialize reading progress repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, ReadingProgress)

    def get_by_user_book_format(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        book_format: str,
    ) -> ReadingProgress | None:
        """Get reading progress for a specific user/book/format combination.

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
        stmt = select(ReadingProgress).where(
            ReadingProgress.user_id == user_id,
            ReadingProgress.library_id == library_id,
            ReadingProgress.book_id == book_id,
            ReadingProgress.format == book_format,
        )
        return self._session.exec(stmt).first()

    def get_recent_reads(
        self,
        user_id: int,
        library_id: int,
        limit: int = 10,
    ) -> list[ReadingProgress]:
        """Get recent reads ordered by updated_at.

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
            List of recent reading progress records, ordered by updated_at descending.
        """
        stmt = (
            select(ReadingProgress)
            .where(
                ReadingProgress.user_id == user_id,
                ReadingProgress.library_id == library_id,
            )
            .order_by(desc(ReadingProgress.updated_at))
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())


class ReadingSessionRepository(Repository[ReadingSession]):
    """Repository for ReadingSession entities.

    Provides CRUD operations and specialized queries for reading sessions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize reading session repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, ReadingSession)

    def get_active_session(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        book_format: str,
    ) -> ReadingSession | None:
        """Get the current active reading session.

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
        ReadingSession | None
            Active session if found (ended_at is None), None otherwise.
        """
        stmt = select(ReadingSession).where(
            ReadingSession.user_id == user_id,
            ReadingSession.library_id == library_id,
            ReadingSession.book_id == book_id,
            ReadingSession.format == book_format,
            ReadingSession.ended_at.is_(None),  # type: ignore[attr-defined]
        )
        return self._session.exec(stmt).first()

    def get_sessions_by_book(
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
            List of reading sessions for the book, ordered by started_at descending.
        """
        stmt = (
            select(ReadingSession)
            .where(
                ReadingSession.user_id == user_id,
                ReadingSession.library_id == library_id,
                ReadingSession.book_id == book_id,
            )
            .order_by(desc(ReadingSession.started_at))
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())


class ReadStatusRepository(Repository[ReadStatus]):
    """Repository for ReadStatus entities.

    Provides CRUD operations and specialized queries for read status.
    """

    def __init__(self, session: Session) -> None:
        """Initialize read status repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, ReadStatus)

    def get_by_user_book(
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
        stmt = select(ReadStatus).where(
            ReadStatus.user_id == user_id,
            ReadStatus.library_id == library_id,
            ReadStatus.book_id == book_id,
        )
        return self._session.exec(stmt).first()

    def get_read_books(
        self,
        user_id: int,
        library_id: int,
    ) -> list[ReadStatus]:
        """Get all read books for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.

        Returns
        -------
        list[ReadStatus]
            List of read status records where status is READ.
        """
        stmt = select(ReadStatus).where(
            ReadStatus.user_id == user_id,
            ReadStatus.library_id == library_id,
            ReadStatus.status == ReadStatusEnum.READ,
        )
        return list(self._session.exec(stmt).all())


class AnnotationRepository(Repository[Annotation]):
    """Repository for Annotation entities.

    Provides CRUD operations and specialized queries for annotations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize annotation repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, Annotation)

    def get_by_user_book(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
    ) -> list[Annotation]:
        """Get annotations for a book.

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
        list[Annotation]
            List of annotations for the book.
        """
        stmt = select(Annotation).where(
            Annotation.user_id == user_id,
            Annotation.library_id == library_id,
            Annotation.book_id == book_id,
        )
        return list(self._session.exec(stmt).all())

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

"""Kobo repository.

Typed repositories for Kobo sync entities with convenience query methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from sqlmodel import Session, select

from fundamental.models.kobo import (
    KoboArchivedBook,
    KoboAuthToken,
    KoboBookmark,
    KoboReadingState,
    KoboStatistics,
    KoboSyncedBook,
)
from fundamental.repositories.base import Repository

if TYPE_CHECKING:
    from collections.abc import Iterable


class KoboAuthTokenRepository(Repository[KoboAuthToken]):
    """Repository for `KoboAuthToken` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboAuthToken)

    def find_by_token(self, token: str) -> KoboAuthToken | None:
        """Find auth token by token string.

        Parameters
        ----------
        token : str
            Authentication token string.

        Returns
        -------
        KoboAuthToken | None
            Auth token if found, None otherwise.
        """
        stmt = select(KoboAuthToken).where(KoboAuthToken.auth_token == token)
        return self._session.exec(stmt).first()

    def find_by_user_id(self, user_id: int) -> KoboAuthToken | None:
        """Find auth token by user ID.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        KoboAuthToken | None
            Auth token if found, None otherwise.
        """
        stmt = select(KoboAuthToken).where(KoboAuthToken.user_id == user_id)
        return self._session.exec(stmt).first()

    def delete_by_user_id(self, user_id: int) -> None:
        """Delete auth token for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        """
        stmt = select(KoboAuthToken).where(KoboAuthToken.user_id == user_id)
        token = self._session.exec(stmt).first()
        if token:
            self.delete(token)


class KoboReadingStateRepository(Repository[KoboReadingState]):
    """Repository for `KoboReadingState` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboReadingState)

    def find_by_user_and_book(
        self, user_id: int, book_id: int
    ) -> KoboReadingState | None:
        """Find reading state by user and book.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.

        Returns
        -------
        KoboReadingState | None
            Reading state if found, None otherwise.
        """
        stmt = (
            select(KoboReadingState)
            .where(KoboReadingState.user_id == user_id)
            .where(KoboReadingState.book_id == book_id)
        )
        return self._session.exec(stmt).first()

    def find_by_user(
        self, user_id: int, last_modified_after: datetime | None = None
    ) -> Iterable[KoboReadingState]:
        """Find all reading states for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        last_modified_after : datetime | None
            Optional filter for states modified after this time.

        Returns
        -------
        Iterable[KoboReadingState]
            Reading states for the user.
        """
        stmt = select(KoboReadingState).where(KoboReadingState.user_id == user_id)
        if last_modified_after:
            stmt = stmt.where(KoboReadingState.last_modified > last_modified_after)
        stmt = stmt.order_by(KoboReadingState.last_modified)
        return self._session.exec(stmt).all()

    def find_by_user_and_books(
        self, user_id: int, book_ids: list[int]
    ) -> Iterable[KoboReadingState]:
        """Find reading states for a user and multiple books.

        Parameters
        ----------
        user_id : int
            User ID.
        book_ids : list[int]
            List of book IDs.

        Returns
        -------
        Iterable[KoboReadingState]
            Reading states matching the criteria.
        """
        if not book_ids:
            return []
        stmt = (
            select(KoboReadingState)
            .where(KoboReadingState.user_id == user_id)
            .where(KoboReadingState.book_id.in_(book_ids))  # type: ignore[attr-defined]
        )
        return self._session.exec(stmt).all()


class KoboBookmarkRepository(Repository[KoboBookmark]):
    """Repository for `KoboBookmark` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboBookmark)

    def find_by_reading_state_id(self, reading_state_id: int) -> KoboBookmark | None:
        """Find bookmark by reading state ID.

        Parameters
        ----------
        reading_state_id : int
            Reading state ID.

        Returns
        -------
        KoboBookmark | None
            Bookmark if found, None otherwise.
        """
        stmt = select(KoboBookmark).where(
            KoboBookmark.reading_state_id == reading_state_id
        )
        return self._session.exec(stmt).first()


class KoboStatisticsRepository(Repository[KoboStatistics]):
    """Repository for `KoboStatistics` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboStatistics)

    def find_by_reading_state_id(self, reading_state_id: int) -> KoboStatistics | None:
        """Find statistics by reading state ID.

        Parameters
        ----------
        reading_state_id : int
            Reading state ID.

        Returns
        -------
        KoboStatistics | None
            Statistics if found, None otherwise.
        """
        stmt = select(KoboStatistics).where(
            KoboStatistics.reading_state_id == reading_state_id
        )
        return self._session.exec(stmt).first()


class KoboSyncedBookRepository(Repository[KoboSyncedBook]):
    """Repository for `KoboSyncedBook` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboSyncedBook)

    def find_by_user_and_book(
        self, user_id: int, book_id: int
    ) -> KoboSyncedBook | None:
        """Find synced book by user and book.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.

        Returns
        -------
        KoboSyncedBook | None
            Synced book if found, None otherwise.
        """
        stmt = (
            select(KoboSyncedBook)
            .where(KoboSyncedBook.user_id == user_id)
            .where(KoboSyncedBook.book_id == book_id)
        )
        return self._session.exec(stmt).first()

    def find_by_user(self, user_id: int) -> Iterable[KoboSyncedBook]:
        """Find all synced books for a user.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        Iterable[KoboSyncedBook]
            Synced books for the user.
        """
        stmt = select(KoboSyncedBook).where(KoboSyncedBook.user_id == user_id)
        return self._session.exec(stmt).all()

    def find_book_ids_by_user(self, user_id: int) -> set[int]:
        """Get set of book IDs that have been synced for a user.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        set[int]
            Set of book IDs.
        """
        stmt = select(KoboSyncedBook.book_id).where(KoboSyncedBook.user_id == user_id)
        return set(self._session.exec(stmt).all())

    def delete_by_user_and_book(self, user_id: int, book_id: int) -> None:
        """Delete synced book record.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.
        """
        synced_book = self.find_by_user_and_book(user_id, book_id)
        if synced_book:
            self.delete(synced_book)


class KoboArchivedBookRepository(Repository[KoboArchivedBook]):
    """Repository for `KoboArchivedBook` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KoboArchivedBook)

    def find_by_user_and_book(
        self, user_id: int, book_id: int
    ) -> KoboArchivedBook | None:
        """Find archived book by user and book.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.

        Returns
        -------
        KoboArchivedBook | None
            Archived book if found, None otherwise.
        """
        stmt = (
            select(KoboArchivedBook)
            .where(KoboArchivedBook.user_id == user_id)
            .where(KoboArchivedBook.book_id == book_id)
        )
        return self._session.exec(stmt).first()

    def find_archived_by_user(
        self, user_id: int, last_modified_after: datetime | None = None
    ) -> Iterable[KoboArchivedBook]:
        """Find archived books for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        last_modified_after : datetime | None
            Optional filter for books archived after this time.

        Returns
        -------
        Iterable[KoboArchivedBook]
            Archived books for the user.
        """
        stmt = (
            select(KoboArchivedBook)
            .where(KoboArchivedBook.user_id == user_id)
            .where(KoboArchivedBook.is_archived == True)  # noqa: E712
        )
        if last_modified_after:
            stmt = stmt.where(KoboArchivedBook.last_modified > last_modified_after)
        # Use desc() method on the column to avoid type checker issues
        from sqlalchemy import desc

        stmt = stmt.order_by(desc(KoboArchivedBook.last_modified))
        return self._session.exec(stmt).all()

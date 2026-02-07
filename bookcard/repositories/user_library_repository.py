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

"""User-library association repository.

Persistence layer for managing user-library assignments, visibility, and
active-library state.
"""

from __future__ import annotations

from sqlmodel import Session, select

from bookcard.models.config import Library
from bookcard.models.user_library import UserLibrary
from bookcard.repositories.base import Repository


class UserLibraryRepository(Repository[UserLibrary]):
    """Repository for ``UserLibrary`` association entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, UserLibrary)

    def find_by_user_and_library(
        self, user_id: int, library_id: int
    ) -> UserLibrary | None:
        """Find the association for a specific user and library.

        Parameters
        ----------
        user_id : int
            User identifier.
        library_id : int
            Library identifier.

        Returns
        -------
        UserLibrary | None
            The association if it exists, None otherwise.
        """
        stmt = select(UserLibrary).where(
            UserLibrary.user_id == user_id,
            UserLibrary.library_id == library_id,
        )
        return self._session.exec(stmt).first()

    def find_active_for_user(self, user_id: int) -> UserLibrary | None:
        """Find the active library association for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        UserLibrary | None
            The active association if one exists, None otherwise.
        """
        stmt = select(UserLibrary).where(
            UserLibrary.user_id == user_id,
            UserLibrary.is_active == True,  # noqa: E712
        )
        return self._session.exec(stmt).first()

    def list_visible_for_user(self, user_id: int) -> list[UserLibrary]:
        """List all visible library associations for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[UserLibrary]
            Visible associations ordered by creation date.
        """
        stmt = (
            select(UserLibrary)
            .where(
                UserLibrary.user_id == user_id,
                UserLibrary.is_visible == True,  # noqa: E712
            )
            .order_by(UserLibrary.created_at)  # type: ignore[arg-type]
        )
        return list(self._session.exec(stmt).all())

    def list_for_user(self, user_id: int) -> list[UserLibrary]:
        """List all library associations for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[UserLibrary]
            All associations ordered by creation date.
        """
        stmt = (
            select(UserLibrary)
            .where(UserLibrary.user_id == user_id)
            .order_by(UserLibrary.created_at)  # type: ignore[arg-type]
        )
        return list(self._session.exec(stmt).all())

    def list_for_library(self, library_id: int) -> list[UserLibrary]:
        """List all user associations for a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        list[UserLibrary]
            All associations ordered by creation date.
        """
        stmt = (
            select(UserLibrary)
            .where(UserLibrary.library_id == library_id)
            .order_by(UserLibrary.created_at)  # type: ignore[arg-type]
        )
        return list(self._session.exec(stmt).all())

    def deactivate_all_for_user(self, user_id: int) -> None:
        """Set ``is_active=False`` on all associations for a user.

        Parameters
        ----------
        user_id : int
            User identifier.
        """
        stmt = select(UserLibrary).where(
            UserLibrary.user_id == user_id,
            UserLibrary.is_active == True,  # noqa: E712
        )
        for ul in self._session.exec(stmt).all():
            ul.is_active = False
            self._session.add(ul)

    def get_active_library_for_user(self, user_id: int) -> Library | None:
        """Get the active ``Library`` entity for a user.

        Joins through the association to return the full Library object.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        Library | None
            The active library if one exists, None otherwise.
        """
        stmt = (
            select(Library)
            .join(UserLibrary, UserLibrary.library_id == Library.id)  # type: ignore[invalid-argument-type]
            .where(
                UserLibrary.user_id == user_id,
                UserLibrary.is_active == True,  # noqa: E712
            )
        )
        return self._session.exec(stmt).first()

    def get_visible_libraries_for_user(self, user_id: int) -> list[Library]:
        """Get all visible ``Library`` entities for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[Library]
            Visible libraries ordered by creation date.
        """
        stmt = (
            select(Library)
            .join(UserLibrary, UserLibrary.library_id == Library.id)  # type: ignore[invalid-argument-type]
            .where(
                UserLibrary.user_id == user_id,
                UserLibrary.is_visible == True,  # noqa: E712
            )
            .order_by(Library.created_at)  # type: ignore[arg-type]
        )
        return list(self._session.exec(stmt).all())

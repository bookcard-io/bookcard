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

"""User-library management service.

Business logic for managing per-user library assignments, visibility, and
active-library selection.  Follows IOC by accepting repositories as
constructor parameters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bookcard.models.user_library import UserLibrary

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.config import Library
    from bookcard.repositories.config_repository import LibraryRepository
    from bookcard.repositories.user_library_repository import UserLibraryRepository

logger = logging.getLogger(__name__)


class UserLibraryService:
    """Operations for managing user-library associations.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    user_library_repo : UserLibraryRepository
        Repository for user-library persistence.
    library_repo : LibraryRepository
        Repository for library persistence.
    """

    def __init__(
        self,
        session: Session,
        user_library_repo: UserLibraryRepository,
        library_repo: LibraryRepository,
    ) -> None:
        self._session = session
        self._user_library_repo = user_library_repo
        self._library_repo = library_repo

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_active_library_for_user(self, user_id: int) -> Library | None:
        """Get the active library for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        Library | None
            The user's active library, or None if none is set.
        """
        return self._user_library_repo.get_active_library_for_user(user_id)

    def get_visible_libraries_for_user(self, user_id: int) -> list[Library]:
        """Get all visible libraries for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[Library]
            Libraries the user has marked as visible.
        """
        return self._user_library_repo.get_visible_libraries_for_user(user_id)

    def get_visible_library_ids_for_user(self, user_id: int) -> list[int]:
        """Get IDs of all visible libraries for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[int]
            Library IDs the user has marked as visible.
        """
        libs = self._user_library_repo.list_visible_for_user(user_id)
        return [ul.library_id for ul in libs]

    def list_assignments_for_user(self, user_id: int) -> list[UserLibrary]:
        """List all library assignments for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[UserLibrary]
            All user-library associations.
        """
        return self._user_library_repo.list_for_user(user_id)

    def list_assignments_for_library(self, library_id: int) -> list[UserLibrary]:
        """List all user assignments for a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        list[UserLibrary]
            All user-library associations for the library.
        """
        return self._user_library_repo.list_for_library(library_id)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def assign_library_to_user(
        self,
        user_id: int,
        library_id: int,
        *,
        is_visible: bool = True,
        is_active: bool = False,
    ) -> UserLibrary:
        """Assign a library to a user.

        If the assignment already exists, it is returned unchanged.
        If ``is_active`` is True, any previously active library for the user
        is deactivated first.

        Parameters
        ----------
        user_id : int
            User identifier.
        library_id : int
            Library identifier.
        is_visible : bool
            Whether the library should be visible (default: True).
        is_active : bool
            Whether this should be the user's active library (default: False).

        Returns
        -------
        UserLibrary
            The created or existing association.

        Raises
        ------
        ValueError
            If the library does not exist.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = f"Library {library_id} does not exist"
            raise ValueError(msg)

        existing = self._user_library_repo.find_by_user_and_library(user_id, library_id)
        if existing is not None:
            return existing

        if is_active:
            self._user_library_repo.deactivate_all_for_user(user_id)

        ul = UserLibrary(
            user_id=user_id,
            library_id=library_id,
            is_visible=is_visible,
            is_active=is_active,
        )
        self._user_library_repo.add(ul)
        self._session.flush()
        self._session.refresh(ul)
        logger.info(
            "Assigned library %d to user %d (visible=%s, active=%s)",
            library_id,
            user_id,
            is_visible,
            is_active,
        )
        return ul

    def unassign_library_from_user(self, user_id: int, library_id: int) -> None:
        """Remove a library assignment from a user.

        Parameters
        ----------
        user_id : int
            User identifier.
        library_id : int
            Library identifier.

        Raises
        ------
        ValueError
            If the assignment does not exist.
        """
        ul = self._user_library_repo.find_by_user_and_library(user_id, library_id)
        if ul is None:
            msg = f"No assignment found for user {user_id} and library {library_id}"
            raise ValueError(msg)

        self._user_library_repo.delete(ul)
        self._session.flush()
        logger.info("Unassigned library %d from user %d", library_id, user_id)

    def set_active_library_for_user(self, user_id: int, library_id: int) -> UserLibrary:
        """Set a library as the user's active library.

        Deactivates any previously active library for the user, then
        activates the specified one.  The library must already be assigned
        to the user.

        Parameters
        ----------
        user_id : int
            User identifier.
        library_id : int
            Library identifier.

        Returns
        -------
        UserLibrary
            The updated association.

        Raises
        ------
        ValueError
            If the assignment does not exist.
        """
        ul = self._user_library_repo.find_by_user_and_library(user_id, library_id)
        if ul is None:
            msg = f"No assignment found for user {user_id} and library {library_id}"
            raise ValueError(msg)

        self._user_library_repo.deactivate_all_for_user(user_id)
        ul.is_active = True
        self._session.add(ul)
        self._session.flush()
        self._session.refresh(ul)
        logger.info("Set library %d as active for user %d", library_id, user_id)
        return ul

    def set_visibility_for_user(
        self, user_id: int, library_id: int, *, is_visible: bool
    ) -> UserLibrary:
        """Update visibility of a library for a user.

        Parameters
        ----------
        user_id : int
            User identifier.
        library_id : int
            Library identifier.
        is_visible : bool
            Whether the library should be visible.

        Returns
        -------
        UserLibrary
            The updated association.

        Raises
        ------
        ValueError
            If the assignment does not exist.
        """
        ul = self._user_library_repo.find_by_user_and_library(user_id, library_id)
        if ul is None:
            msg = f"No assignment found for user {user_id} and library {library_id}"
            raise ValueError(msg)

        ul.is_visible = is_visible
        self._session.add(ul)
        self._session.flush()
        self._session.refresh(ul)
        logger.info(
            "Set library %d visibility=%s for user %d",
            library_id,
            is_visible,
            user_id,
        )
        return ul

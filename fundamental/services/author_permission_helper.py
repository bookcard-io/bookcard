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

"""Permission helper for author operations.

Centralizes permission checking logic following DRY principle.
Separates authorization concerns from business logic.
"""

from typing import Any

from sqlmodel import Session

from fundamental.models.auth import User
from fundamental.services.permission_service import PermissionService


class AuthorPermissionHelper:
    """Helper for author permission operations.

    Centralizes permission checking to avoid duplication.
    Follows SRP by handling only permission concerns.
    """

    def __init__(self, session: Session) -> None:
        """Initialize permission helper.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._permission_service = PermissionService(session)

    @staticmethod
    def build_permission_context(author_data: dict[str, Any]) -> dict[str, Any]:
        """Build permission context from author data.

        Parameters
        ----------
        author_data : dict[str, Any]
            Author data dictionary.

        Returns
        -------
        dict[str, Any]
            Permission context dictionary with authors list.
        """
        author_name = author_data.get("name")
        if author_name:
            return {"authors": [author_name]}
        return {"authors": []}

    def check_write_permission(
        self,
        user: User,
        author_data: dict[str, Any],
    ) -> None:
        """Check write permission for author operations.

        Parameters
        ----------
        user : User
            Current authenticated user.
        author_data : dict[str, Any]
            Author data dictionary.

        Raises
        ------
        PermissionError
            If user does not have write permission.
        """
        context = self.build_permission_context(author_data)
        self._permission_service.check_permission(user, "books", "write", context)

    def check_read_permission(
        self,
        user: User,
        author_data: dict[str, Any],
    ) -> None:
        """Check read permission for author operations.

        Parameters
        ----------
        user : User
            Current authenticated user.
        author_data : dict[str, Any]
            Author data dictionary.

        Raises
        ------
        PermissionError
            If user does not have read permission.
        """
        context = self.build_permission_context(author_data)
        self._permission_service.check_permission(user, "books", "read", context)

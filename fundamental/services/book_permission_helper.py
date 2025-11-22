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

"""Permission helper for book operations.

Centralizes permission checking logic following DRY principle.
Separates authorization concerns from business logic.
"""

from sqlmodel import Session

from fundamental.models.auth import User
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.services.permission_service import PermissionService


class BookPermissionHelper:
    """Helper for book permission operations.

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
    def build_permission_context(
        book_with_rels: BookWithRelations | BookWithFullRelations,
    ) -> dict[str, object]:
        """Build permission context from book metadata.

        Parameters
        ----------
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with related metadata.
        _book_id : int
            Book ID (unused, kept for API compatibility).
        _session : Session
            Database session (unused, kept for API compatibility).

        Returns
        -------
        dict[str, object]
            Permission context dictionary with authors, tags, series_id, etc.
        """
        context: dict[str, object] = {
            "authors": book_with_rels.authors,
        }

        # Add series_id if available
        if (
            isinstance(book_with_rels, BookWithFullRelations)
            and book_with_rels.series_id
        ):
            context["series_id"] = book_with_rels.series_id

        # Add tags if available
        if isinstance(book_with_rels, BookWithFullRelations) and book_with_rels.tags:
            context["tags"] = book_with_rels.tags

        return context

    def check_read_permission(
        self,
        user: User,
        book_with_rels: BookWithRelations | BookWithFullRelations | None = None,
    ) -> None:
        """Check read permission for book operations.

        Parameters
        ----------
        user : User
            Current authenticated user.
        book_with_rels : BookWithRelations | BookWithFullRelations | None
            Optional book with relations for context-based permission.
        book_id : int | None
            Optional book ID (required if book_with_rels is None).
        session : Session | None
            Optional session (required if book_with_rels is None).

        Raises
        ------
        PermissionError
            If user does not have read permission.
        """
        if book_with_rels is not None:
            context = BookPermissionHelper.build_permission_context(book_with_rels)
            self._permission_service.check_permission(user, "books", "read", context)
        else:
            self._permission_service.check_permission(user, "books", "read")

    def check_write_permission(
        self,
        user: User,
        book_with_rels: BookWithRelations | BookWithFullRelations,
    ) -> None:
        """Check write permission for book operations.

        Parameters
        ----------
        user : User
            Current authenticated user.
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with relations for context-based permission.
        book_id : int
            Book ID.
        session : Session
            Database session.

        Raises
        ------
        PermissionError
            If user does not have write permission.
        """
        context = BookPermissionHelper.build_permission_context(book_with_rels)
        self._permission_service.check_permission(user, "books", "write", context)

    def check_create_permission(self, user: User) -> None:
        """Check create permission for book operations.

        Parameters
        ----------
        user : User
            Current authenticated user.

        Raises
        ------
        PermissionError
            If user does not have create permission.
        """
        self._permission_service.check_permission(user, "books", "create")

    def check_send_permission(
        self,
        user: User,
        book_with_rels: BookWithRelations | BookWithFullRelations,
    ) -> None:
        """Check send permission for book operations.

        Parameters
        ----------
        user : User
            Current authenticated user.
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with relations for context-based permission.
        book_id : int
            Book ID.
        session : Session
            Database session.

        Raises
        ------
        PermissionError
            If user does not have send permission.
        """
        context = BookPermissionHelper.build_permission_context(
            book_with_rels,
        )
        self._permission_service.check_permission(user, "books", "send", context)

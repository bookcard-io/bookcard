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

"""Repository layer for metadata enforcement persistence operations.

Provides data access for metadata enforcement operations tracking.
"""

from sqlalchemy import desc
from sqlmodel import Session, select

from bookcard.models.metadata_enforcement import (
    EnforcementStatus,
    MetadataEnforcementOperation,
)
from bookcard.repositories.base import Repository


class MetadataEnforcementRepository(Repository[MetadataEnforcementOperation]):
    """Repository for MetadataEnforcementOperation entities.

    Provides CRUD operations and specialized queries for enforcement operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize metadata enforcement repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, MetadataEnforcementOperation)

    def get_by_book(
        self,
        book_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MetadataEnforcementOperation]:
        """Get enforcement operations for a specific book.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        limit : int
            Maximum number of records to return (default: 50).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[MetadataEnforcementOperation]
            List of enforcement operations for the book, ordered by created_at descending.
        """
        stmt = (
            select(MetadataEnforcementOperation)
            .where(MetadataEnforcementOperation.book_id == book_id)
            .order_by(desc(MetadataEnforcementOperation.created_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

    def get_by_library(
        self,
        library_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MetadataEnforcementOperation]:
        """Get enforcement operations for a specific library.

        Parameters
        ----------
        library_id : int
            Library ID.
        limit : int
            Maximum number of records to return (default: 50).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[MetadataEnforcementOperation]
            List of enforcement operations for the library, ordered by created_at descending.
        """
        stmt = (
            select(MetadataEnforcementOperation)
            .where(MetadataEnforcementOperation.library_id == library_id)
            .order_by(desc(MetadataEnforcementOperation.created_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

    def get_by_status(
        self,
        status: EnforcementStatus,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MetadataEnforcementOperation]:
        """Get enforcement operations by status.

        Parameters
        ----------
        status : EnforcementStatus
            Status to filter by.
        limit : int
            Maximum number of records to return (default: 50).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[MetadataEnforcementOperation]
            List of enforcement operations with the specified status,
            ordered by created_at descending.
        """
        stmt = (
            select(MetadataEnforcementOperation)
            .where(MetadataEnforcementOperation.status == status)
            .order_by(desc(MetadataEnforcementOperation.created_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

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

"""E-reader device repository.

Typed repository for EReaderDevice entities with convenience query methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.auth import EReaderDevice
from bookcard.repositories.base import Repository

if TYPE_CHECKING:
    from collections.abc import Iterable


class EReaderRepository(Repository[EReaderDevice]):
    """Repository for `EReaderDevice` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, EReaderDevice)

    def find_by_user(self, user_id: int) -> Iterable[EReaderDevice]:
        """Return all e-reader devices for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        Iterable[EReaderDevice]
            E-reader device entities for the user.
        """
        stmt = select(EReaderDevice).where(EReaderDevice.user_id == user_id)
        return self._session.exec(stmt).all()

    def find_default(self, user_id: int) -> EReaderDevice | None:
        """Return the default e-reader device for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        EReaderDevice | None
            Default e-reader device if found, None otherwise.
        """
        stmt = select(EReaderDevice).where(
            EReaderDevice.user_id == user_id,
            EReaderDevice.is_default == True,  # noqa: E712
        )
        return self._session.exec(stmt).first()

    def find_by_email(self, user_id: int, email: str) -> EReaderDevice | None:
        """Return an e-reader device by user and email if it exists.

        Parameters
        ----------
        user_id : int
            User identifier.
        email : str
            E-reader email address.

        Returns
        -------
        EReaderDevice | None
            E-reader device entity if found, None otherwise.
        """
        stmt = select(EReaderDevice).where(
            EReaderDevice.user_id == user_id, EReaderDevice.email == email
        )
        return self._session.exec(stmt).first()

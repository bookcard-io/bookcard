# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING WITHOUT LIMITATION THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""E-reader device repository.

Typed repository for EReaderDevice entities with convenience query methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.auth import EReaderDevice
from fundamental.repositories.base import Repository

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

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
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""User repository.

Typed repository for `User` entities with convenience query methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.auth import User
from fundamental.repositories.base import Repository

if TYPE_CHECKING:
    from collections.abc import Iterable


class UserRepository(Repository[User]):
    """Repository for `User` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def find_by_email(self, email: str) -> User | None:
        """Return a user by email if it exists."""
        stmt = select(User).where(User.email == email)
        return self._session.exec(stmt).first()

    def find_by_username(self, username: str) -> User | None:
        """Return a user by username if it exists."""
        stmt = select(User).where(User.username == username)
        return self._session.exec(stmt).first()

    def list_admins(self) -> Iterable[User]:
        """Return all users with administrative privileges."""
        stmt = select(User).where(User.is_admin == True)  # noqa: E712
        return self._session.exec(stmt).all()

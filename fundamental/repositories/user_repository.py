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

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.auth import TokenBlacklist, User
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


class TokenBlacklistRepository(Repository[TokenBlacklist]):
    """Repository for `TokenBlacklist` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, TokenBlacklist)

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a JWT ID is blacklisted.

        Parameters
        ----------
        jti : str
            JWT ID to check.

        Returns
        -------
        bool
            True if the token is blacklisted, False otherwise.
        """
        stmt = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        return self._session.exec(stmt).first() is not None

    def add_to_blacklist(self, jti: str, expires_at: datetime) -> TokenBlacklist:
        """Add a JWT ID to the blacklist.

        Parameters
        ----------
        jti : str
            JWT ID to blacklist.
        expires_at : datetime
            Token expiration timestamp.

        Returns
        -------
        TokenBlacklist
            Created blacklist entry.
        """
        blacklist_entry = TokenBlacklist(
            jti=jti,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        self._session.add(blacklist_entry)
        return blacklist_entry

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

    def find_by_oidc_sub(self, oidc_sub: str) -> User | None:
        """Return a user by OIDC subject identifier if it exists.

        Parameters
        ----------
        oidc_sub : str
            OIDC subject identifier (``sub`` claim).

        Returns
        -------
        User | None
            Matching user if found, otherwise None.
        """
        stmt = select(User).where(User.oidc_sub == oidc_sub)
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

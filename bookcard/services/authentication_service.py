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

"""Authentication business logic.

This module contains the application-level service for registration, login,
and invite validation. It is decoupled from the web layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from bookcard.models.auth import User

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.admin_repositories import InviteRepository
    from bookcard.repositories.user_repository import UserRepository
    from bookcard.services.security import JWTManager, PasswordHasher


class AuthError(StrEnum):
    """Authentication error message constants."""

    USERNAME_EXISTS = "username_already_exists"
    EMAIL_EXISTS = "email_already_exists"
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_PASSWORD = "invalid_password"  # noqa: S105
    INVALID_INVITE = "invalid_invite"
    INVITE_EXPIRED = "invite_expired"
    INVITE_ALREADY_USED = "invite_already_used"


class AuthenticationService:
    """Handle authentication operations (registration/login/invite checks)."""

    def __init__(
        self,
        session: Session,
        user_repo: UserRepository,
        invite_repo: InviteRepository,
        hasher: PasswordHasher,
        jwt: JWTManager,
    ) -> None:
        self._session = session
        self._users = user_repo
        self._invites = invite_repo
        self._hasher = hasher
        self._jwt = jwt

    def register_user(
        self, username: str, email: str, password: str
    ) -> tuple[User, str]:
        """Register a new user and return an access token.

        Parameters
        ----------
        username : str
            Desired username.
        email : str
            User email.
        password : str
            Plaintext password to hash.

        Returns
        -------
        tuple[User, str]
            The created user and access token.

        Raises
        ------
        ValueError
            If username or email already exists.
        """
        if self._users.find_by_username(username) is not None:
            raise ValueError(AuthError.USERNAME_EXISTS)
        if self._users.find_by_email(email) is not None:
            raise ValueError(AuthError.EMAIL_EXISTS)

        user = User(
            username=username,
            email=email,
            password_hash=self._hasher.hash(password),
        )
        self._session.add(user)
        self._session.flush()
        token = self._jwt.create_access_token(
            str(user.id), {"username": user.username, "is_admin": user.is_admin}
        )
        return user, token

    def login_user(self, identifier: str, password: str) -> tuple[User, str]:
        """Authenticate a user by username or email and return an access token.

        Parameters
        ----------
        identifier : str
            Username or email.
        password : str
            Plaintext password to verify.

        Returns
        -------
        tuple[User, str]
            The authenticated user and access token.

        Raises
        ------
        ValueError
            If credentials are invalid.
        """
        user = self._users.find_by_username(identifier) or self._users.find_by_email(
            identifier
        )
        if user is None:
            raise ValueError(AuthError.INVALID_CREDENTIALS)
        if not self._hasher.verify(password, user.password_hash):
            raise ValueError(AuthError.INVALID_CREDENTIALS)

        user.last_login = datetime.now(UTC)
        self._session.flush()
        token = self._jwt.create_access_token(
            str(user.id), {"username": user.username, "is_admin": user.is_admin}
        )
        return user, token

    def validate_invite_token(self, token: str) -> bool:
        """Validate an invite token.

        Parameters
        ----------
        token : str
            Invite token to validate.

        Returns
        -------
        bool
            True when the token is valid and unused.

        Raises
        ------
        ValueError
            If the token is invalid, expired, or already used.
        """
        invite = self._invites.get_by_token(token)
        if invite is None:
            raise ValueError(AuthError.INVALID_INVITE)

        now = datetime.now(UTC)
        if invite.expires_at < now:
            raise ValueError(AuthError.INVITE_EXPIRED)

        if invite.used_by is not None:
            raise ValueError(AuthError.INVITE_ALREADY_USED)

        return True

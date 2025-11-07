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

"""Authentication service.

Handles user registration and login, separate from web layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from rainbow.models.auth import User

if TYPE_CHECKING:
    from sqlmodel import Session

    from rainbow.repositories.user_repository import UserRepository
    from rainbow.services.security import JWTManager, PasswordHasher


class AuthError(StrEnum):
    """Authentication error message constants."""

    USERNAME_EXISTS = "username_already_exists"
    EMAIL_EXISTS = "email_already_exists"
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_PASSWORD = "invalid_password"  # noqa: S105
    INVALID_INVITE = "invalid_invite"
    INVITE_EXPIRED = "invite_expired"
    INVITE_ALREADY_USED = "invite_already_used"


class AuthService:
    """Application-level authentication operations."""

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        user_repo: UserRepository,  # type: ignore[type-arg]
        hasher: PasswordHasher,  # type: ignore[type-arg]
        jwt: JWTManager,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._users = user_repo
        self._hasher = hasher
        self._jwt = jwt

    def register_user(
        self, username: str, email: str, password: str
    ) -> tuple[User, str]:
        """Create a new user and return (user, access_token)."""
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
        """Authenticate a user by username or email and return (user, access_token)."""
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

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> None:
        """Change a user's password.

        Parameters
        ----------
        user_id : int
            User identifier.
        current_password : str
            Current password for verification.
        new_password : str
            New password to set.

        Raises
        ------
        ValueError
            If user not found, current password is incorrect, or new password
            is the same as current password.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        if not self._hasher.verify(current_password, user.password_hash):
            raise ValueError(AuthError.INVALID_PASSWORD)

        user.password_hash = self._hasher.hash(new_password)
        user.updated_at = datetime.now(UTC)
        self._session.flush()

    def update_profile_picture(self, user_id: int, picture_path: str) -> User:
        """Update a user's profile picture path.

        Parameters
        ----------
        user_id : int
            User identifier.
        picture_path : str
            Path to the profile picture file.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If user not found.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.profile_picture = picture_path
        user.updated_at = datetime.now(UTC)
        self._session.flush()
        return user

    def delete_profile_picture(self, user_id: int) -> User:
        """Remove a user's profile picture.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If user not found.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.profile_picture = None
        user.updated_at = datetime.now(UTC)
        self._session.flush()
        return user

    def validate_invite_token(self, token: str) -> bool:
        """Validate an invite token.

        Parameters
        ----------
        token : str
            Invite token to validate.

        Returns
        -------
        bool
            True if token is valid and unused, False otherwise.

        Raises
        ------
        ValueError
            If token is invalid, expired, or already used.
        """
        from rainbow.repositories.admin_repositories import InviteRepository

        invite_repo = InviteRepository(self._session)
        invite = invite_repo.get_by_token(token)
        if invite is None:
            raise ValueError(AuthError.INVALID_INVITE)

        now = datetime.now(UTC)
        if invite.expires_at < now:
            raise ValueError(AuthError.INVITE_EXPIRED)

        if invite.used_by is not None:
            raise ValueError(AuthError.INVITE_ALREADY_USED)

        return True

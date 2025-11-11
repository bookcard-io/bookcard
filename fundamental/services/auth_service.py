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

from contextlib import suppress
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.auth import User

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.user_repository import UserRepository
    from fundamental.services.security import JWTManager, PasswordHasher


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
        data_directory: str = "/data",
    ) -> None:
        self._session = session
        self._users = user_repo
        self._hasher = hasher
        self._jwt = jwt
        self._data_directory = Path(data_directory)
        self._ensure_data_directory_exists()

    def _ensure_data_directory_exists(self) -> None:
        """Ensure the data directory exists, creating it if necessary."""
        self._data_directory.mkdir(parents=True, exist_ok=True)

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

    def _get_user_assets_dir(self, user_id: int) -> Path:
        """Get the assets directory path for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        Path
            Path to user's assets directory.
        """
        return self._data_directory / str(user_id) / "assets"

    def _delete_profile_picture_file(self, picture_path: str | None) -> None:
        """Delete profile picture file from disk.

        Parameters
        ----------
        picture_path : str | None
            Path to the profile picture file to delete.
        """
        if picture_path:
            file_path = Path(picture_path)
            if file_path.is_absolute() and file_path.exists():
                with suppress(OSError):
                    file_path.unlink()

    def upload_profile_picture(
        self, user_id: int, file_content: bytes, filename: str
    ) -> User:
        """Upload and save a user's profile picture.

        Saves the file to {data_directory}/{user_id}/assets/profile_picture.{ext}
        and updates the user's profile_picture field. Deletes any existing profile
        picture file before saving the new one.

        Parameters
        ----------
        user_id : int
            User identifier.
        file_content : bytes
            File content to save.
        filename : str
            Original filename (used to determine extension).

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If user not found, invalid file extension, or file save fails.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if not file_ext or file_ext not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
        }:
            msg = "invalid_file_type"
            raise ValueError(msg)

        # Delete old profile picture if exists
        if user.profile_picture:
            old_path = Path(user.profile_picture)
            if old_path.is_absolute():
                # Absolute path - delete directly
                with suppress(OSError):
                    old_path.unlink()
            else:
                # Relative path - construct full path
                full_old_path = self._data_directory / user.profile_picture
                with suppress(OSError):
                    full_old_path.unlink()

        # Create user assets directory
        assets_dir = self._get_user_assets_dir(user_id)
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Save new file
        picture_filename = f"profile_picture{file_ext}"
        picture_path = assets_dir / picture_filename
        try:
            picture_path.write_bytes(file_content)
        except OSError as exc:
            msg = f"failed_to_save_file: {exc!s}"
            raise ValueError(msg) from exc

        # Update user record with relative path from data_directory
        # Store as relative path so it works if data_directory changes
        relative_path = picture_path.relative_to(self._data_directory)
        user.profile_picture = str(relative_path)
        user.updated_at = datetime.now(UTC)
        self._session.flush()
        return user

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

        Deletes both the file from disk and clears the database field.

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

        # Delete file from disk
        if user.profile_picture:
            # Handle both relative and absolute paths
            if Path(user.profile_picture).is_absolute():
                self._delete_profile_picture_file(user.profile_picture)
            else:
                # Relative path - construct full path
                full_path = self._data_directory / user.profile_picture
                if full_path.exists():
                    with suppress(OSError):
                        full_path.unlink()

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
        from fundamental.repositories.admin_repositories import InviteRepository

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

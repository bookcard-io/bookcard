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

"""User profile operations (password, profile fields, profile pictures)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.auth import User
    from bookcard.repositories.user_repository import UserRepository
    from bookcard.services.file_storage_service import FileStorageService
    from bookcard.services.security import PasswordHasher


class ProfileError(StrEnum):
    """Profile error message constants."""

    USER_NOT_FOUND = "user_not_found"
    INVALID_PASSWORD = "invalid_password"  # noqa: S105
    USERNAME_EXISTS = "username_already_exists"
    EMAIL_EXISTS = "email_already_exists"
    INVALID_FILE_TYPE = "invalid_file_type"


class UserProfileService:
    """Handles user profile operations."""

    def __init__(
        self,
        session: Session,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        file_storage: FileStorageService,
    ) -> None:
        self._session = session
        self._users = user_repo
        self._hasher = hasher
        self._storage = file_storage

    def _get_user_or_raise(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(ProfileError.USER_NOT_FOUND)
        return user

    def _save_and_flush(self, user: User) -> None:
        user.updated_at = datetime.now(UTC)
        self._session.flush()

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> None:
        """Change a user's password.

        Parameters
        ----------
        user_id : int
            User identifier.
        current_password : str
            Current password to verify.
        new_password : str
            New password to set.

        Raises
        ------
        ValueError
            If the user does not exist or the current password is invalid.
        """
        user = self._get_user_or_raise(user_id)

        if not self._hasher.verify(current_password, user.password_hash):
            raise ValueError(ProfileError.INVALID_PASSWORD)

        user.password_hash = self._hasher.hash(new_password)
        self._save_and_flush(user)

    def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
    ) -> User:
        """Update a user's profile fields.

        Parameters
        ----------
        user_id : int
            User identifier.
        username : str | None
            New username (optional).
        email : str | None
            New email (optional).
        full_name : str | None
            New full name (optional).

        Returns
        -------
        User
            Updated user.

        Raises
        ------
        ValueError
            If the user does not exist or uniqueness constraints fail.
        """
        user = self._get_user_or_raise(user_id)

        if username is not None and username != user.username:
            existing = self._users.find_by_username(username)
            if existing and existing.id != user_id:
                raise ValueError(ProfileError.USERNAME_EXISTS)

        if email is not None and email != user.email:
            existing = self._users.find_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError(ProfileError.EMAIL_EXISTS)

        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name

        self._save_and_flush(user)
        return user

    def upload_profile_picture(
        self, user_id: int, file_content: bytes, filename: str
    ) -> User:
        """Upload a profile picture and store it on disk.

        Parameters
        ----------
        user_id : int
            User identifier.
        file_content : bytes
            Raw file bytes.
        filename : str
            Original filename (used for extension validation).

        Returns
        -------
        User
            Updated user with `profile_picture` set to the stored path.

        Raises
        ------
        ValueError
            If user does not exist, file extension is invalid, or storage fails.
        """
        user = self._get_user_or_raise(user_id)

        file_ext = Path(filename).suffix.lower()
        if not file_ext or file_ext not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
        }:
            raise ValueError(ProfileError.INVALID_FILE_TYPE)

        # Delete old picture
        if user.profile_picture:
            self._storage.delete_profile_picture(user.profile_picture)

        # Save new picture
        relative_path = self._storage.save_profile_picture(
            user_id, file_content, filename
        )

        user.profile_picture = relative_path
        self._save_and_flush(user)
        return user

    def delete_profile_picture(self, user_id: int) -> User:
        """Delete a user's profile picture (file + DB field).

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        User
            Updated user with `profile_picture` cleared.
        """
        user = self._get_user_or_raise(user_id)

        if user.profile_picture:
            self._storage.delete_profile_picture(user.profile_picture)

        user.profile_picture = None
        self._save_and_flush(user)
        return user

    def update_profile_picture_path(self, user_id: int, picture_path: str) -> User:
        """Update the stored profile picture path without uploading a file.

        Parameters
        ----------
        user_id : int
            User identifier.
        picture_path : str
            New profile picture path.

        Returns
        -------
        User
            Updated user.
        """
        user = self._get_user_or_raise(user_id)
        user.profile_picture = picture_path
        self._save_and_flush(user)
        return user

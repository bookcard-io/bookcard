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

"""Authentication service.

Handles user registration and login, separate from web layer.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from sqlmodel import select

from fundamental.models.auth import User, UserSetting
from fundamental.models.config import (
    EmailServerConfig,
    EmailServerType,
    OpenLibraryDumpConfig,
)
from fundamental.repositories.admin_repositories import (
    InviteRepository,
    SettingRepository,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.user_repository import UserRepository
    from fundamental.services.security import DataEncryptor, JWTManager, PasswordHasher


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
        encryptor: DataEncryptor | None = None,  # type: ignore[type-arg]
        data_directory: str = "/data",
    ) -> None:
        self._session = session
        self._users = user_repo
        self._hasher = hasher
        self._jwt = jwt
        self._encryptor = encryptor
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

    def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
    ) -> User:
        """Update a user's profile information.

        Parameters
        ----------
        user_id : int
            User identifier.
        username : str | None
            New username (optional).
        email : str | None
            New email address (optional).
        full_name : str | None
            New full name (optional).

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If user not found, username already exists, or email already exists.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        # Check for username conflicts if username is being changed
        if username is not None and username != user.username:
            existing_user = self._users.find_by_username(username)
            if existing_user is not None and existing_user.id != user_id:
                raise ValueError(AuthError.USERNAME_EXISTS)

        # Check for email conflicts if email is being changed
        if email is not None and email != user.email:
            existing_user = self._users.find_by_email(email)
            if existing_user is not None and existing_user.id != user_id:
                raise ValueError(AuthError.EMAIL_EXISTS)

        # Update fields if provided
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name

        user.updated_at = datetime.now(UTC)
        self._session.flush()
        return user

    def upsert_setting(
        self, user_id: int, key: str, value: str, description: str | None = None
    ) -> UserSetting:
        """Create or update a user setting.

        Parameters
        ----------
        user_id : int
            User identifier.
        key : str
            Setting key.
        value : str
            Setting value.
        description : str | None
            Optional setting description.

        Returns
        -------
        UserSetting
            Created or updated user setting entity.

        Raises
        ------
        ValueError
            If user not found.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        # Query for existing setting directly
        stmt = select(UserSetting).where(
            UserSetting.user_id == user_id, UserSetting.key == key
        )
        existing_setting = self._session.exec(stmt).first()

        if existing_setting is not None:
            # Update existing setting
            existing_setting.value = value
            if description is not None:
                existing_setting.description = description
            existing_setting.updated_at = datetime.now(UTC)
            self._session.flush()
            return existing_setting

        # Create new setting
        new_setting = UserSetting(
            user_id=user_id,
            key=key,
            value=value,
            description=description,
        )
        self._session.add(new_setting)
        self._session.flush()
        return new_setting

    def get_setting(self, user_id: int, key: str) -> UserSetting | None:
        """Get a user setting by key.

        Parameters
        ----------
        user_id : int
            User identifier.
        key : str
            Setting key.

        Returns
        -------
        UserSetting | None
            User setting entity if found, None otherwise.
        """
        setting_repo = SettingRepository(self._session)
        return setting_repo.get_by_key(user_id, key)

    def get_all_settings(self, user_id: int) -> list[UserSetting]:
        """Get all settings for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[UserSetting]
            List of user setting entities.
        """
        stmt = select(UserSetting).where(UserSetting.user_id == user_id)
        return list(self._session.exec(stmt).all())

    def get_email_server_config(
        self, decrypt: bool = False
    ) -> EmailServerConfig | None:
        """Get the singleton email server configuration.

        Parameters
        ----------
        decrypt : bool, optional
            Whether to decrypt passwords and tokens. Defaults to False.
            Set to True when returning config to API (for reading).

        Returns
        -------
        EmailServerConfig | None
            The configuration if it exists, otherwise None.
        """
        stmt = select(EmailServerConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None or not decrypt or self._encryptor is None:
            return config

        # Detach from session to avoid modifying the database object
        self._session.expunge(config)

        # Decrypt password if it exists
        if config.smtp_password:
            config.smtp_password = self._encryptor.decrypt(config.smtp_password)

        # Decrypt Gmail token if it exists
        # gmail_token is stored as an encrypted string in the database
        if config.gmail_token and isinstance(config.gmail_token, str):
            config.gmail_token = self._encryptor.decrypt_dict(config.gmail_token)

        return config

    def _apply_smtp_config(
        self,
        config: EmailServerConfig,
        *,
        smtp_host: str | None,
        smtp_port: int | None,
        smtp_username: str | None,
        smtp_password: str | None,
        smtp_use_tls: bool | None,
        smtp_use_ssl: bool | None,
        smtp_from_email: str | None,
        smtp_from_name: str | None,
    ) -> None:
        """Apply SMTP-specific configuration fields.

        Parameters
        ----------
        config : EmailServerConfig
            Configuration object to update.
        smtp_host, smtp_port, smtp_username, smtp_password : Optional
            SMTP connection settings.
        smtp_use_tls, smtp_use_ssl : Optional
            SMTP encryption flags.
        smtp_from_email, smtp_from_name : Optional
            SMTP sender details.
        """
        if smtp_host is not None:
            config.smtp_host = smtp_host
        if smtp_port is not None:
            config.smtp_port = smtp_port
        if smtp_username is not None:
            config.smtp_username = smtp_username
        if smtp_password is not None:
            # Encrypt password before storing
            if self._encryptor is not None:
                config.smtp_password = self._encryptor.encrypt(smtp_password)
            else:
                config.smtp_password = smtp_password
        if smtp_use_tls is not None:
            config.smtp_use_tls = smtp_use_tls
        if smtp_use_ssl is not None:
            config.smtp_use_ssl = smtp_use_ssl
        if smtp_from_email is not None:
            config.smtp_from_email = smtp_from_email
        if smtp_from_name is not None:
            config.smtp_from_name = smtp_from_name
        # Clear Gmail-specific fields
        config.gmail_token = None

    def _apply_gmail_config(
        self,
        config: EmailServerConfig,
        *,
        gmail_token: dict[str, object] | None,
        smtp_host: str | None,
        smtp_port: int | None,
        smtp_username: str | None,
        smtp_use_tls: bool | None,
        smtp_use_ssl: bool | None,
        smtp_from_email: str | None,
        smtp_from_name: str | None,
    ) -> None:
        """Apply Gmail-specific configuration fields.

        Parameters
        ----------
        config : EmailServerConfig
            Configuration object to update.
        gmail_token : dict[str, object] | None
            Gmail OAuth token JSON.
        smtp_host, smtp_port, smtp_username : Optional
            SMTP connection settings (optional for Gmail).
        smtp_use_tls, smtp_use_ssl : Optional
            SMTP encryption flags.
        smtp_from_email, smtp_from_name : Optional
            SMTP sender details.
        """
        # Encrypt Gmail token before storing
        if gmail_token is not None:
            if self._encryptor is not None:
                config.gmail_token = self._encryptor.encrypt_dict(gmail_token)
            else:
                config.gmail_token = gmail_token
        else:
            config.gmail_token = None
        config.smtp_password = None
        if smtp_host is not None:
            config.smtp_host = smtp_host
        if smtp_port is not None:
            config.smtp_port = smtp_port
        if smtp_username is not None:
            config.smtp_username = smtp_username
        if smtp_use_tls is not None:
            config.smtp_use_tls = smtp_use_tls
        if smtp_use_ssl is not None:
            config.smtp_use_ssl = smtp_use_ssl
        if smtp_from_email is not None:
            config.smtp_from_email = smtp_from_email
        if smtp_from_name is not None:
            config.smtp_from_name = smtp_from_name

    def upsert_email_server_config(
        self,
        *,
        server_type: EmailServerType,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_use_tls: bool | None = None,
        smtp_use_ssl: bool | None = None,
        smtp_from_email: str | None = None,
        smtp_from_name: str | None = None,
        max_email_size_mb: int | None = None,
        gmail_token: dict[str, object] | None = None,
        enabled: bool | None = None,
    ) -> EmailServerConfig:
        """Create or update the email server configuration.

        Parameters
        ----------
        server_type : EmailServerType
            Email server type to use.
        smtp_host, smtp_port, smtp_username, smtp_password : Optional
            SMTP settings (used when server_type is SMTP).
        smtp_use_tls, smtp_use_ssl : Optional
            SMTP encryption flags (at most one should be True).
        smtp_from_email, smtp_from_name : Optional
            SMTP sender details.
        max_email_size_mb : int | None
            Maximum email size in MB.
        gmail_token : dict[str, object] | None
            Gmail OAuth token JSON (used when server_type is GMAIL).
        enabled : bool | None
            Whether email sending is enabled.

        Returns
        -------
        EmailServerConfig
            The created or updated configuration.

        Raises
        ------
        ValueError
            If both smtp_use_tls and smtp_use_ssl are True.
        """
        # Validate TLS/SSL flags if provided
        if smtp_use_tls is True and smtp_use_ssl is True:
            msg = "invalid_smtp_encryption"
            raise ValueError(msg)

        config = self.get_email_server_config()
        if config is None:
            config = EmailServerConfig()
            self._session.add(config)

        # Apply common fields
        config.server_type = server_type  # type: ignore[assignment]
        if max_email_size_mb is not None:
            config.max_email_size_mb = max_email_size_mb
        if enabled is not None:
            config.enabled = enabled

        # Apply server-type-specific fields
        if server_type == EmailServerType.SMTP:
            self._apply_smtp_config(
                config,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_use_tls=smtp_use_tls,
                smtp_use_ssl=smtp_use_ssl,
                smtp_from_email=smtp_from_email,
                smtp_from_name=smtp_from_name,
            )
        else:
            self._apply_gmail_config(
                config,
                gmail_token=gmail_token,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_use_tls=smtp_use_tls,
                smtp_use_ssl=smtp_use_ssl,
                smtp_from_email=smtp_from_email,
                smtp_from_name=smtp_from_name,
            )

        config.updated_at = datetime.now(UTC)
        self._session.flush()
        return config

    def get_openlibrary_dump_config(
        self,
    ) -> OpenLibraryDumpConfig | None:
        """Get the singleton OpenLibrary dump configuration.

        Returns
        -------
        OpenLibraryDumpConfig | None
            The configuration if it exists, otherwise None.
        """
        stmt = select(OpenLibraryDumpConfig).limit(1)
        return self._session.exec(stmt).first()

    def _apply_openlibrary_dump_config(
        self,
        config: OpenLibraryDumpConfig,
        *,
        authors_url: str | None = None,
        works_url: str | None = None,
        editions_url: str | None = None,
        default_process_authors: bool | None = None,
        default_process_works: bool | None = None,
        default_process_editions: bool | None = None,
        staleness_threshold_days: int | None = None,
        enable_auto_download: bool | None = None,
        enable_auto_process: bool | None = None,
        auto_check_interval_hours: int | None = None,
    ) -> None:
        """Apply OpenLibrary dump configuration fields.

        Parameters
        ----------
        config : OpenLibraryDumpConfig
            Configuration object to update.
        authors_url, works_url, editions_url : str | None
            URLs for dump files.
        default_process_authors, default_process_works, default_process_editions : bool | None
            Default processing flags.
        staleness_threshold_days : int | None
            Days before data is considered stale.
        enable_auto_download, enable_auto_process : bool | None
            Automation flags.
        auto_check_interval_hours : int | None
            Hours between automatic checks.
        """
        field_mapping = {
            "authors_url": authors_url,
            "works_url": works_url,
            "editions_url": editions_url,
            "default_process_authors": default_process_authors,
            "default_process_works": default_process_works,
            "default_process_editions": default_process_editions,
            "staleness_threshold_days": staleness_threshold_days,
            "enable_auto_download": enable_auto_download,
            "enable_auto_process": enable_auto_process,
            "auto_check_interval_hours": auto_check_interval_hours,
        }
        for field_name, value in field_mapping.items():
            if value is not None:
                setattr(config, field_name, value)

    def upsert_openlibrary_dump_config(
        self,
        *,
        authors_url: str | None = None,
        works_url: str | None = None,
        editions_url: str | None = None,
        default_process_authors: bool | None = None,
        default_process_works: bool | None = None,
        default_process_editions: bool | None = None,
        staleness_threshold_days: int | None = None,
        enable_auto_download: bool | None = None,
        enable_auto_process: bool | None = None,
        auto_check_interval_hours: int | None = None,
    ) -> OpenLibraryDumpConfig:
        """Create or update the OpenLibrary dump configuration.

        Parameters
        ----------
        authors_url, works_url, editions_url : str | None
            URLs for dump files.
        default_process_authors, default_process_works, default_process_editions : bool | None
            Default processing flags.
        staleness_threshold_days : int | None
            Days before data is considered stale.
        enable_auto_download, enable_auto_process : bool | None
            Automation flags.
        auto_check_interval_hours : int | None
            Hours between automatic checks.

        Returns
        -------
        OpenLibraryDumpConfig
            The created or updated configuration.
        """
        config = self.get_openlibrary_dump_config()
        if config is None:
            config = OpenLibraryDumpConfig()
            self._session.add(config)

        self._apply_openlibrary_dump_config(
            config,
            authors_url=authors_url,
            works_url=works_url,
            editions_url=editions_url,
            default_process_authors=default_process_authors,
            default_process_works=default_process_works,
            default_process_editions=default_process_editions,
            staleness_threshold_days=staleness_threshold_days,
            enable_auto_download=enable_auto_download,
            enable_auto_process=enable_auto_process,
            auto_check_interval_hours=auto_check_interval_hours,
        )

        config.updated_at = datetime.now(UTC)
        self._session.flush()
        return config

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

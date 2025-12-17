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

"""User service.

Encapsulates user profile operations and validations.
"""

from __future__ import annotations

import json
import re
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from bookcard.models.auth import (
    EBookFormat,
    User,
    UserRole,
    UserSetting,
)
from bookcard.repositories.command_executor import CommandExecutor
from bookcard.repositories.delete_commands import (
    DeleteRefreshTokensCommand,
    DeleteUserCommand,
    DeleteUserDataDirectoryCommand,
    DeleteUserDevicesCommand,
    DeleteUserRolesCommand,
    DeleteUserSettingsCommand,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from bookcard.repositories.ereader_repository import EReaderRepository
    from bookcard.repositories.role_repository import UserRoleRepository
    from bookcard.repositories.user_repository import UserRepository
    from bookcard.services.ereader_service import EReaderService
    from bookcard.services.role_service import RoleService
    from bookcard.services.security import PasswordHasher


# Default user settings to initialize for new users.
# Values can be strings, booleans, or lists (which will be JSON-encoded).
# Only settings with non-None values will be created.
DEFAULT_USER_SETTINGS: dict[str, str | bool | list[str]] = {
    "theme_preference": "dark",
    "books_grid_display": "infinite-scroll",
    "default_view_mode": "grid",
    "default_page_size": "20",
    "preferred_language": "en",
    "default_sort_field": "timestamp",
    "default_sort_order": "desc",
    "enabled_metadata_providers": [
        "Hardcover",
        "Google Books",
        "Amazon",
        "ComicVine",
    ],
    "preferred_metadata_providers": ["Hardcover", "Google Books", "Amazon"],
    "replace_cover_on_metadata_selection": True,
    "metadata_download_format": "opf",
    "auto_dismiss_book_edit_modal": True,
    "book_details_open_mode": "modal",
    "always_warn_on_delete": True,
    "default_delete_files_from_drive": False,
    "auto_convert_on_import": False,
    "auto_convert_target_format": "epub",
    "auto_convert_ignored_formats": ["epub", "pdf"],
    "auto_convert_backup_originals": True,
    "comic_reading_mode": "paged",
    "comic_reading_direction": "ltr",
    "comic_spread_mode": True,
    "comic_zoom_level": "1.0",
}


class UserService:
    """Operations for retrieving and updating user profiles.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    users : UserRepository
        Repository providing user persistence operations.
    """

    def __init__(self, session: Session, users: UserRepository) -> None:  # type: ignore[type-arg]
        self._session = session
        self._users = users

    def get(self, user_id: int) -> User | None:
        """Return a user by id or ``None`` if missing."""
        return self._users.get(user_id)

    def create_admin_user(
        self,
        username: str,
        email: str,
        password: str,
        *,
        full_name: str | None = None,
        is_admin: bool = False,
        is_active: bool = True,
        role_ids: list[int] | None = None,
        default_device_email: str | None = None,
        default_device_name: str | None = None,
        default_device_type: str | None = None,
        default_device_format: str | None = None,
        password_hasher: PasswordHasher,
        role_service: RoleService | None = None,
        device_service: EReaderService | None = None,
    ) -> User:
        """Create a new user with optional role and device assignment.

        Parameters
        ----------
        username : str
            Username for the new user.
        email : str
            Email address for the new user.
        password : str
            Plain text password (will be hashed before storage).
        full_name : str | None
            Optional full name.
        is_admin : bool
            Whether the user is an admin (default: False).
        is_active : bool
            Whether the user is active (default: True).
        role_ids : list[int] | None
            Optional list of role IDs to assign.
        default_device_email : str | None
            Optional e-reader email for default device.
        default_device_name : str | None
            Optional device name (used when creating device).
        default_device_type : str | None
            Optional device type (defaults to "generic" if creating).
        default_device_format : str | None
            Optional preferred format string (defaults to EPUB if creating).
        password_hasher : PasswordHasher
            Password hasher for hashing passwords (IOC).
        role_service : RoleService | None
            Role service for managing role assignments (IOC).
        device_service : EReaderService | None
            E-reader service for device operations (IOC).

        Returns
        -------
        User
            Created user with relationships loaded.

        Raises
        ------
        ValueError
            If username or email already exists.
        """
        # Check if username/email exists
        if self._users.find_by_username(username) is not None:
            msg = "username_already_exists"
            raise ValueError(msg)
        if self._users.find_by_email(email) is not None:
            msg = "email_already_exists"
            raise ValueError(msg)

        # Create user
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=password_hasher.hash(password),
            is_admin=is_admin,
            is_active=is_active,
        )
        self._users.add(user)
        self._session.flush()

        # Assign roles if provided
        if role_ids and role_service is not None:
            for role_id in role_ids:
                with suppress(ValueError):
                    # Role doesn't exist or already assigned, skip
                    role_service.assign_role_to_user(user.id, role_id)  # type: ignore[arg-type]

        # Create default device if email provided
        if default_device_email and device_service is not None:
            # Use payload values if provided, otherwise default to hardcoded values
            preferred_format = EBookFormat.EPUB
            if default_device_format:
                with suppress(ValueError):
                    # Invalid format, use default
                    preferred_format = EBookFormat(default_device_format.lower())
            device_name = default_device_name or "My eReader"
            device_type = default_device_type or "generic"
            with suppress(ValueError):
                # Device email already exists, skip
                device_service.create_device(
                    user.id,  # type: ignore[arg-type]
                    default_device_email,
                    device_name=device_name,
                    device_type=device_type,
                    preferred_format=preferred_format,
                    is_default=True,
                )

        # Initialize default user settings
        self._initialize_default_settings(user.id)  # type: ignore[arg-type]

        self._session.commit()

        # Reload with relationships for response
        user_with_rels = self.get_with_relationships(user.id)  # type: ignore[arg-type]
        if user_with_rels is None:
            msg = "user_not_found"
            raise ValueError(msg)
        return user_with_rels

    def update_profile(
        self, user_id: int, *, username: str | None = None, email: str | None = None
    ) -> User:
        """Update username and/or email ensuring uniqueness.

        Raises
        ------
        ValueError
            If the desired username or email is already in use by another user.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        if username is not None and username != user.username:
            exists = self._users.find_by_username(username)
            if exists is not None and exists.id != user.id:
                msg = "username_already_exists"
                raise ValueError(msg)
            user.username = username

        if email is not None and email != user.email:
            exists = self._users.find_by_email(email)
            if exists is not None and exists.id != user.id:
                msg = "email_already_exists"
                raise ValueError(msg)
            user.email = email

        self._session.flush()
        return user

    def list_users(self, limit: int | None = None, offset: int = 0) -> Iterable[User]:
        """List users with pagination.

        Parameters
        ----------
        limit : int | None
            Maximum number of users to return.
        offset : int
            Number of users to skip.

        Returns
        -------
        Iterable[User]
            User entities.
        """
        return self._users.list(limit=limit, offset=offset)

    def get_with_relationships(self, user_id: int) -> User | None:
        """Get user by ID with eager-loaded relationships.

        Loads user with ereader_devices and roles (including nested role data).

        Uses `selectinload()` which executes separate SELECT queries with IN clauses
        to avoid cartesian product issues when loading multiple one-to-many relationships.

        Alternative: `joinedload()` would use LEFT OUTER JOINs in a single query,
        but can cause row multiplication (cartesian product) with multiple one-to-many
        relationships (e.g., user with 3 devices and 2 roles = 6 rows returned).

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        User | None
            User with relationships loaded, or None if not found.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                # selectinload: Executes separate SELECT with IN clause
                # SELECT * FROM ereader_devices WHERE user_id IN (1)
                # SELECT * FROM user_roles WHERE user_id IN (1)
                # SELECT * FROM roles WHERE id IN (role_ids)
                selectinload(User.ereader_devices),
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        return self._session.exec(stmt).first()

    def list_users_with_relationships(
        self, limit: int | None = None, offset: int = 0
    ) -> list[User]:
        """List users with eager-loaded relationships.

        Loads users with ereader_devices and roles (including nested role data).

        Uses `selectinload()` which executes separate SELECT queries with IN clauses
        to avoid cartesian product issues when loading multiple one-to-many relationships.

        Example queries executed:
        1. SELECT * FROM users LIMIT 10 OFFSET 0
        2. SELECT * FROM ereader_devices WHERE user_id IN (1, 2, 3, ...)
        3. SELECT * FROM user_roles WHERE user_id IN (1, 2, 3, ...)
        4. SELECT * FROM roles WHERE id IN (role_ids)

        Alternative: `joinedload()` would use LEFT OUTER JOINs in a single query,
        but can cause row multiplication (cartesian product) with multiple one-to-many
        relationships (e.g., 10 users with avg 3 devices and 2 roles = 60 rows returned).

        Parameters
        ----------
        limit : int | None
            Maximum number of users to return.
        offset : int
            Number of users to skip.

        Returns
        -------
        list[User]
            Users with relationships loaded.
        """
        stmt = (
            select(User)
            .offset(offset)
            .options(
                # selectinload: Executes separate SELECT with IN clause
                # Avoids cartesian product issues with multiple one-to-many relationships
                selectinload(User.ereader_devices),
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._session.exec(stmt).all())

    def update_admin_status(self, user_id: int, is_admin: bool) -> User:
        """Update user admin status.

        Parameters
        ----------
        user_id : int
            User identifier.
        is_admin : bool
            New admin status.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.is_admin = is_admin
        self._session.flush()
        return user

    def update_active_status(self, user_id: int, is_active: bool) -> User:
        """Update user active status.

        Parameters
        ----------
        user_id : int
            User identifier.
        is_active : bool
            New active status.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.is_active = is_active
        self._session.flush()
        return user

    def update_user(
        self,
        user_id: int,
        *,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        is_admin: bool | None = None,
        is_active: bool | None = None,
        role_ids: list[int] | None = None,
        default_device_email: str | None = None,
        default_device_name: str | None = None,
        default_device_type: str | None = None,
        default_device_format: str | None = None,
        role_service: RoleService | None = None,
        user_role_repo: UserRoleRepository | None = None,
        password_hasher: PasswordHasher | None = None,
        device_service: EReaderService | None = None,
        device_repo: EReaderRepository | None = None,
    ) -> User:
        """Update user properties with role and device synchronization.

        Orchestrates updates to user profile, password, admin status, active status,
        role assignments, and default device. Follows SRP by delegating to specialized
        methods and uses IOC for service dependencies.

        Parameters
        ----------
        user_id : int
            User identifier.
        username : str | None
            Optional new username.
        email : str | None
            Optional new email.
        password : str | None
            Optional new password (will be hashed before storage).
        is_admin : bool | None
            Optional new admin status.
        is_active : bool | None
            Optional new active status.
        role_ids : list[int] | None
            Optional list of role IDs to assign. If provided, synchronizes
            user roles to match this list (adds missing, removes extra).
        default_device_email : str | None
            Optional e-reader email for default device. If provided, creates
            or updates the device.
        default_device_name : str | None
            Optional device name (used when creating device).
        default_device_type : str | None
            Optional device type (used when creating device).
        default_device_format : str | None
            Optional preferred format (used when creating device).
        role_service : RoleService | None
            Role service for managing role assignments (IOC).
        user_role_repo : UserRoleRepository | None
            User role repository for querying current roles (IOC).
        password_hasher : PasswordHasher | None
            Password hasher for hashing new passwords (IOC).
        device_service : EReaderService | None
            E-reader service for device operations (IOC).
        device_repo : EReaderRepository | None
            E-reader repository for querying devices (IOC).

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If user not found, username/email conflict, or role/device operation fails.
        """
        # Verify user exists
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        # Update profile if username/email provided
        if username is not None or email is not None:
            self.update_profile(user_id, username=username, email=email)

        # Update password if provided
        if password is not None:
            if password_hasher is None:
                msg = "password_hasher_required"
                raise ValueError(msg)
            user.password_hash = password_hasher.hash(password)

        # Update admin status if provided
        if is_admin is not None:
            self.update_admin_status(user_id, is_admin)

        # Update active status if provided
        if is_active is not None:
            self.update_active_status(user_id, is_active)

        # Synchronize roles if provided
        if (
            role_ids is not None
            and role_service is not None
            and user_role_repo is not None
        ):
            self._sync_user_roles(user_id, role_ids, role_service, user_role_repo)

        # Create or update default device if email provided
        if (
            default_device_email is not None
            and device_service is not None
            and device_repo is not None
        ):
            self._sync_default_device(
                user_id,
                default_device_email,
                device_name=default_device_name,
                device_type=default_device_type,
                device_format=default_device_format,
                device_service=device_service,
                device_repo=device_repo,
            )

        self._session.flush()
        return user

    def _sync_user_roles(
        self,
        user_id: int,
        new_role_ids: list[int],
        role_service: RoleService,
        user_role_repo: UserRoleRepository,
    ) -> None:
        """Synchronize user roles to match the provided list.

        Adds missing roles and removes roles not in the list.
        Uses suppress to handle cases where roles don't exist or are already assigned.

        Parameters
        ----------
        user_id : int
            User identifier.
        new_role_ids : list[int]
            Desired role IDs.
        role_service : RoleService
            Role service for assignment operations.
        user_role_repo : UserRoleRepository
            Repository for querying current user roles.

        Notes
        -----
        Silently skips invalid role assignments (non-existent roles, already assigned).
        """
        # Get current user roles
        current_user_roles = list(user_role_repo.list_by_user(user_id))
        current_role_ids = {ur.role_id for ur in current_user_roles}
        new_role_ids_set = set(new_role_ids)

        # Remove roles that are no longer assigned
        roles_to_remove = current_role_ids - new_role_ids_set
        for role_id in roles_to_remove:
            with suppress(ValueError):
                # Role association doesn't exist, skip
                role_service.remove_role_from_user(user_id, role_id)

        # Add new roles
        roles_to_add = new_role_ids_set - current_role_ids
        for role_id in roles_to_add:
            with suppress(ValueError):
                # Role doesn't exist or already assigned, skip
                role_service.assign_role_to_user(user_id, role_id)

    def _sync_default_device(
        self,
        user_id: int,
        device_email: str,
        *,
        device_name: str | None = None,
        device_type: str | None = None,
        device_format: str | None = None,
        device_service: EReaderService,
        device_repo: EReaderRepository,
    ) -> None:
        """Create or update default device for user.

        If a device with the email already exists, updates it to be default.
        Otherwise, creates a new device. Uses suppress to handle conflicts gracefully.

        Parameters
        ----------
        user_id : int
            User identifier.
        device_email : str
            E-reader email address.
        device_name : str | None
            Optional device name (defaults to "My eReader" if creating).
        device_type : str | None
            Optional device type (defaults to "generic" if creating).
        device_format : str | None
            Optional preferred format string (defaults to EPUB if creating).
        device_service : EReaderService
            E-reader service for device operations.
        device_repo : EReaderRepository
            E-reader repository for querying devices.

        Notes
        -----
        Silently skips if device email already exists for another user.
        """
        # Check if device with this email already exists for this user
        existing_device = device_repo.find_by_email(user_id, device_email)

        if existing_device is not None:
            # Update existing device to be default and update properties
            update_kwargs: dict[str, object] = {"is_default": True}
            if device_name is not None:
                update_kwargs["device_name"] = device_name
            if device_type is not None:
                update_kwargs["device_type"] = device_type
            if device_format is not None:
                with suppress(ValueError):
                    # Invalid format, skip
                    update_kwargs["preferred_format"] = EBookFormat(
                        device_format.lower()
                    )
            device_service.update_device(existing_device.id, **update_kwargs)  # type: ignore[arg-type]
        else:
            # Create new device - always use increment system for naming
            preferred_format = EBookFormat.EPUB
            if device_format:
                with suppress(ValueError):
                    # Invalid format, use default
                    preferred_format = EBookFormat(device_format.lower())
            device_type_final = device_type or "generic"

            # Always generate incremented device name for new devices
            device_name_final = self._generate_incremented_device_name(
                user_id, device_repo
            )

            with suppress(ValueError):
                # Device email already exists for another user, skip
                device_service.create_device(
                    user_id,
                    device_email,
                    device_name=device_name_final,
                    device_type=device_type_final,
                    preferred_format=preferred_format,
                    is_default=True,
                )

    def _generate_incremented_device_name(
        self, user_id: int, device_repo: EReaderRepository
    ) -> str:
        """Generate incremented device name based on existing devices.

        Checks existing device names for pattern "My eReader (N)" and returns
        the next available number. If a device exists with just "My eReader"
        (no number), starts with "(1)".

        Parameters
        ----------
        user_id : int
            User identifier.
        device_repo : EReaderRepository
            E-reader repository for querying devices.

        Returns
        -------
        str
            Incremented device name (e.g., "My eReader (1)", "My eReader (2)").
        """
        base_name = "My eReader"
        numbered_pattern = re.compile(rf"^{re.escape(base_name)}\s*\((\d+)\)$")
        base_pattern = re.compile(rf"^{re.escape(base_name)}$")

        # Get all existing devices for the user
        existing_devices = list(device_repo.find_by_user(user_id))

        # Check if base name exists (without number)
        has_base_name = any(
            device.device_name and base_pattern.match(device.device_name)
            for device in existing_devices
        )

        # Find the highest number in existing device names
        max_number = 0
        for device in existing_devices:
            if device.device_name:
                match = numbered_pattern.match(device.device_name)
                if match:
                    number = int(match.group(1))
                    max_number = max(max_number, number)

        # If base name exists or we found numbered devices, increment
        if has_base_name or max_number > 0:
            next_number = max_number + 1
            return f"{base_name} ({next_number})"

        # No existing devices with this pattern, return base name
        return base_name

    def delete_user(
        self,
        user_id: int,
        *,
        data_directory: str | Path | None = None,
        device_repo: EReaderRepository | None = None,
        user_role_repo: UserRoleRepository | None = None,
    ) -> None:
        """Delete a user and all related data.

        Uses command pattern with compensating undos for atomic deletion.
        If any command fails, all previous commands are automatically undone.
        Follows SRP by delegating to command classes.

        Parameters
        ----------
        user_id : int
            User identifier.
        data_directory : str | Path | None
            Optional data directory path for filesystem cleanup.
        device_repo : EReaderRepository | None
            Optional e-reader repository (for dependency injection).
        user_role_repo : UserRoleRepository | None
            Optional user role repository (for dependency injection).

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        executor = CommandExecutor()

        # Execute deletion commands in order
        # If any fails, all previous commands are automatically undone

        # 1. Delete e-reader devices
        if device_repo is not None:
            executor.execute(
                DeleteUserDevicesCommand(self._session, user_id, device_repo)
            )

        # 2. Delete user roles
        if user_role_repo is not None:
            executor.execute(
                DeleteUserRolesCommand(self._session, user_id, user_role_repo)
            )

        # 3. Delete user settings
        executor.execute(DeleteUserSettingsCommand(self._session, user_id))

        # 4. Delete refresh tokens
        executor.execute(DeleteRefreshTokensCommand(self._session, user_id))

        # 5. Delete user's data directory (if provided)
        if data_directory is not None:
            user_data_dir = Path(data_directory) / str(user_id)
            executor.execute(DeleteUserDataDirectoryCommand(user_data_dir))

        # 6. Delete the user record itself (must be last for database integrity)
        executor.execute(DeleteUserCommand(self._session, user))

        # Clear executor after successful execution
        executor.clear()
        self._session.flush()

    def _initialize_default_settings(self, user_id: int) -> None:
        """Initialize default user settings for a newly created user.

        Creates UserSetting records for all settings defined in DEFAULT_USER_SETTINGS.
        Handles different value types:
        - Strings: stored as-is
        - Booleans: converted to "true"/"false" strings
        - Lists: JSON-encoded to strings

        Parameters
        ----------
        user_id : int
            User identifier for which to create default settings.

        Notes
        -----
        Follows SRP by handling only default settings initialization.
        Follows DRY by centralizing default values in DEFAULT_USER_SETTINGS constant.
        """
        for key, value in DEFAULT_USER_SETTINGS.items():
            # Convert value to string representation
            if isinstance(value, bool):
                setting_value = "true" if value else "false"
            elif isinstance(value, list):
                # JSON-encode lists (e.g., metadata providers)
                setting_value = json.dumps(value)
            else:
                # String or other types - convert to string
                setting_value = str(value)

            # Create setting record
            setting = UserSetting(
                user_id=user_id,
                key=key,
                value=setting_value,
            )
            self._session.add(setting)

        self._session.flush()

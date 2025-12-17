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

"""User authentication and authorization API schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from bookcard.models.auth import User  # noqa: TC001
from bookcard.models.config import EmailServerType


class UserRead(BaseModel):
    """Public-facing user representation.

    Attributes
    ----------
    id : int
        Primary identifier.
    username : str
        Unique username.
    email : EmailStr
        Email address.
    full_name : str | None
        User's full name.
    profile_picture : str | None
        Optional path to user's profile picture.
    is_admin : bool
        Whether the user has admin privileges.
    default_ereader_email : str | None
        Email address of the default e-reader device, if any.
    ereader_devices : list[EReaderDeviceRead]
        List of e-reader devices for the user.
    roles : list[RoleRead]
        List of roles assigned to the user.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    profile_picture: str | None = None
    is_admin: bool
    default_ereader_email: str | None = None
    ereader_devices: list[EReaderDeviceRead] = Field(default_factory=list)
    roles: list[RoleRead] = Field(default_factory=list)

    @classmethod
    def from_user(cls, user: User) -> UserRead:
        """Create UserRead from User model with relationships.

        Parameters
        ----------
        user : User
            User model instance with relationships loaded.

        Returns
        -------
        UserRead
            UserRead instance with populated relationships.
        """
        # Find default e-reader device
        default_email = None
        if user.ereader_devices:
            default_device = next(
                (d for d in user.ereader_devices if d.is_default), None
            )
            if default_device:
                default_email = default_device.email

        # Extract roles from UserRole relationships
        roles = []
        if user.roles:
            roles = [RoleRead.model_validate(ur.role) for ur in user.roles if ur.role]

        # Extract e-reader devices
        ereader_devices = []
        if user.ereader_devices:
            ereader_devices = [
                EReaderDeviceRead.model_validate(device)
                for device in user.ereader_devices
            ]

        return cls(
            id=user.id,  # type: ignore[arg-type]
            username=user.username,
            email=user.email,  # type: ignore[arg-type]
            full_name=user.full_name,
            profile_picture=user.profile_picture,
            is_admin=user.is_admin,
            default_ereader_email=default_email,
            ereader_devices=ereader_devices,
            roles=roles,
        )


class UserCreate(BaseModel):
    """Payload to create a new user account."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Login by username or email and password."""

    identifier: str
    password: str


class TokenResponse(BaseModel):
    """Bearer token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 OAuth token type identifier, not a password


class LoginResponse(BaseModel):
    """Login response containing access token and user data."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 OAuth token type identifier, not a password
    user: UserRead


class AuthConfigResponse(BaseModel):
    """Authentication configuration exposed to clients.

    Attributes
    ----------
    oidc_enabled : bool
        Whether OIDC authentication is enabled.
    oidc_issuer : str
        Configured OIDC issuer URL (may be empty if disabled).
    local_login_enabled : bool
        Whether local username/password login should be offered to users.
    """

    oidc_enabled: bool
    oidc_issuer: str
    local_login_enabled: bool


class OIDCCallbackRequest(BaseModel):
    """OIDC callback payload forwarded by frontend/API client.

    Parameters
    ----------
    code : str
        Authorization code from the OIDC provider.
    state : str
        Signed state token returned from the authorization request.
    redirect_uri : str
        Redirect URI used for the authorization request (must match the state).
    """

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1, max_length=2048)


class PasswordChangeRequest(BaseModel):
    """Request to change user password."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ProfilePictureUpdateRequest(BaseModel):
    """Request to update profile picture."""

    picture_path: str = Field(min_length=1, max_length=500)


class ProfileRead(BaseModel):
    """Extended user profile with profile picture."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    profile_picture: str | None
    is_admin: bool


class ProfileUpdate(BaseModel):
    """Payload to update user profile information."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)


class InviteValidationResponse(BaseModel):
    """Response for invite token validation."""

    valid: bool
    token: str


class SettingUpdate(BaseModel):
    """Payload to update a user setting."""

    value: str = Field(max_length=1000)
    description: str | None = Field(default=None, max_length=500)


class SettingRead(BaseModel):
    """User setting representation."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    description: str | None = None
    updated_at: datetime


class SettingsRead(BaseModel):
    """Collection of user settings."""

    settings: dict[str, SettingRead] = Field(default_factory=dict)


class AdminUserCreate(BaseModel):
    """Payload to create a new user with optional role and device assignment."""

    username: str = Field(min_length=3, max_length=50)
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False
    is_active: bool = True
    role_ids: list[int] = Field(default_factory=list)
    default_device_email: str | None = Field(
        default=None, description="E-reader email for default device"
    )
    default_device_name: str | None = Field(
        default=None, description="Optional device name"
    )
    default_device_type: str = Field(default="kindle", description="Device type")
    default_device_format: str | None = Field(
        default=None, description="Preferred format (e.g., 'epub', 'mobi')"
    )


class AdminUserUpdate(BaseModel):
    """Payload to update user properties."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_admin: bool | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = Field(default=None)
    default_device_email: str | None = Field(
        default=None, description="E-reader email for default device"
    )
    default_device_name: str | None = Field(
        default=None, description="Optional device name"
    )
    default_device_type: str | None = Field(default=None, description="Device type")
    default_device_format: str | None = Field(
        default=None, description="Preferred format (e.g., 'epub', 'mobi')"
    )


class RoleCreate(BaseModel):
    """Payload to create a new role."""

    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[PermissionAssignment] = Field(
        default_factory=list,
        description="List of permissions to assign to the role.",
    )


class RoleUpdate(BaseModel):
    """Payload to update a role."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[PermissionAssignment] | None = Field(
        default=None,
        description="List of permissions to assign to the role. If provided, replaces all existing permissions.",
    )
    removed_permission_ids: list[int] = Field(
        default_factory=list,
        description="List of role_permission IDs to remove (for granular updates).",
    )


class RolePermissionRead(BaseModel):
    """Role-permission association representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    permission: PermissionRead
    condition: dict[str, object] | None = None
    assigned_at: datetime


class RoleRead(BaseModel):
    """Role representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    permissions: list[RolePermissionRead] = Field(default_factory=list)


class PermissionRead(BaseModel):
    """Permission representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    resource: str
    action: str


class PermissionCreate(BaseModel):
    """Payload to create a new permission."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    resource: str = Field(min_length=1, max_length=50)
    action: str = Field(min_length=1, max_length=50)
    condition: dict[str, object] | None = Field(
        default=None,
        description="Optional condition for resource-specific permissions (must be valid JSON).",
    )


class PermissionUpdate(BaseModel):
    """Payload to update a permission."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    resource: str | None = Field(default=None, min_length=1, max_length=50)
    action: str | None = Field(default=None, min_length=1, max_length=50)


class RolePermissionUpdate(BaseModel):
    """Payload to update a role-permission association."""

    condition: dict[str, object] | None = Field(
        default=None,
        description="Optional condition for resource-specific permissions (must be valid JSON).",
    )


class PermissionAssignment(BaseModel):
    """Permission assignment for role creation/update."""

    permission_id: int | None = Field(
        default=None,
        description="Existing permission ID. If None, permission_name must be provided.",
    )
    permission_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Permission name. If permission_id is None, this will be used to find or create the permission.",
    )
    # For new permissions
    resource: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Resource name (required if creating new permission).",
    )
    action: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Action name (required if creating new permission).",
    )
    permission_description: str | None = Field(
        default=None,
        max_length=255,
        description="Permission description (for new permissions).",
    )
    condition: dict[str, object] | None = Field(
        default=None,
        description="Optional condition for resource-specific permissions (must be valid JSON).",
    )


class RolePermissionGrant(BaseModel):
    """Payload to grant a permission to a role."""

    permission_id: int
    condition: dict[str, object] | None = Field(
        default=None, description="Optional condition for resource-specific permissions"
    )


class UserRoleAssign(BaseModel):
    """Payload to assign a role to a user."""

    role_id: int


class EReaderDeviceCreate(BaseModel):
    """Payload to create an e-reader device."""

    email: str = Field(description="E-reader email address")
    device_name: str | None = Field(
        default=None, description="User-friendly device name"
    )
    device_type: str = Field(default="kindle", description="Device type")
    preferred_format: str | None = Field(
        default=None, description="Preferred format (e.g., 'epub', 'mobi')"
    )
    is_default: bool = Field(default=False, description="Set as default device")
    serial_number: str | None = Field(
        default=None, description="Device serial number for DRM removal"
    )


class EReaderDeviceUpdate(BaseModel):
    """Payload to update an e-reader device."""

    email: str | None = Field(default=None, description="E-reader email address")
    device_name: str | None = Field(
        default=None, description="User-friendly device name"
    )
    device_type: str | None = Field(default=None, description="Device type")
    preferred_format: str | None = Field(
        default=None, description="Preferred format (e.g., 'epub', 'mobi')"
    )
    is_default: bool | None = Field(default=None, description="Set as default device")
    serial_number: str | None = Field(
        default=None, description="Device serial number for DRM removal"
    )


class EReaderDeviceRead(BaseModel):
    """E-reader device representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    device_name: str | None = None
    device_type: str
    is_default: bool
    preferred_format: str | None = None
    serial_number: str | None = None


class EmailServerConfigRead(BaseModel):
    """Email server configuration representation (read).

    Notes
    -----
    The SMTP password is intentionally omitted from the read model
    for security reasons. The password may be set via the update model.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    server_type: EmailServerType
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_from_email: str | None = None
    smtp_from_name: str | None = None
    max_email_size_mb: int = 25
    gmail_token: dict[str, object] | None = None
    enabled: bool = False
    # timestamps
    updated_at: datetime | None = None
    created_at: datetime | None = None


class EmailServerConfigUpdate(BaseModel):
    """Payload to create or update email server configuration."""

    server_type: EmailServerType = EmailServerType.SMTP
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = None
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=500)
    smtp_use_tls: bool | None = None
    smtp_use_ssl: bool | None = None
    smtp_from_email: str | None = Field(default=None, max_length=255)
    smtp_from_name: str | None = Field(default=None, max_length=255)
    max_email_size_mb: int | None = None
    gmail_token: dict[str, object] | None = None
    enabled: bool | None = None


class OpenLibraryDumpConfigRead(BaseModel):
    """OpenLibrary dump configuration representation (read)."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    authors_url: str | None = None
    works_url: str | None = None
    editions_url: str | None = None
    default_process_authors: bool = True
    default_process_works: bool = True
    default_process_editions: bool = False
    staleness_threshold_days: int = 30
    enable_auto_download: bool = False
    enable_auto_process: bool = False
    auto_check_interval_hours: int = 24
    # timestamps
    updated_at: datetime | None = None
    created_at: datetime | None = None


class OpenLibraryDumpConfigUpdate(BaseModel):
    """Payload to create or update OpenLibrary dump configuration."""

    authors_url: str | None = Field(default=None, max_length=1000)
    works_url: str | None = Field(default=None, max_length=1000)
    editions_url: str | None = Field(default=None, max_length=1000)
    default_process_authors: bool | None = None
    default_process_works: bool | None = None
    default_process_editions: bool | None = None
    staleness_threshold_days: int | None = Field(default=None, ge=1)
    enable_auto_download: bool | None = None
    enable_auto_process: bool | None = None
    auto_check_interval_hours: int | None = Field(default=None, ge=1, le=168)


class ScheduledTasksConfigRead(BaseModel):
    """Scheduled tasks configuration representation (read)."""

    id: int | None = None
    start_time_hour: int
    duration_hours: int
    generate_book_covers: bool
    generate_series_covers: bool
    reconnect_database: bool
    metadata_backup: bool
    epub_fixer_daily_scan: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScheduledTasksConfigUpdate(BaseModel):
    """Payload to create or update scheduled tasks configuration."""

    start_time_hour: int | None = Field(default=None, ge=0, le=23)
    duration_hours: int | None = Field(default=None, ge=1, le=24)
    generate_book_covers: bool | None = None
    generate_series_covers: bool | None = None
    reconnect_database: bool | None = None
    metadata_backup: bool | None = None
    epub_fixer_daily_scan: bool | None = None

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

from fundamental.models.auth import User  # noqa: TC001


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

        return cls(
            id=user.id,  # type: ignore[arg-type]
            username=user.username,
            email=user.email,  # type: ignore[arg-type]
            full_name=user.full_name,
            profile_picture=user.profile_picture,
            is_admin=user.is_admin,
            default_ereader_email=default_email,
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
    is_admin: bool | None = None
    is_active: bool | None = None


class RoleCreate(BaseModel):
    """Payload to create a new role."""

    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)


class RoleRead(BaseModel):
    """Role representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class PermissionRead(BaseModel):
    """Permission representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    resource: str
    action: str


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

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
# IMPLIED, INCLUDING WITHOUT LIMITATION THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Authentication and user database models for Fundamental."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import ConfigDict
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel


class EBookFormat(StrEnum):
    """E-book file format enumeration.

    Supported formats for e-reader devices.
    """

    EPUB = "epub"
    MOBI = "mobi"
    AZW = "azw"
    AZW3 = "azw3"
    PDF = "pdf"
    TXT = "txt"
    RTF = "rtf"
    FB2 = "fb2"
    LIT = "lit"
    LRF = "lrf"
    OEB = "oeb"
    PDB = "pdb"
    RB = "rb"
    SNB = "snb"
    TCR = "tcr"


class User(SQLModel, table=True):
    """User model for authentication and user management.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    username : str
        Unique username for login.
    email : str
        Unique email address.
    hashed_password : str
        Bcrypt hashed password.
    full_name : str | None
        User's full name.
    is_active : bool
        Whether user account is active (default True).
    is_superuser : bool
        Whether user has superuser/admin privileges (default False).
    created_at : datetime
        Account creation timestamp.
    updated_at : datetime
        Last update timestamp.
    last_login : datetime | None
        Last login timestamp.
    """

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=64)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    profile_picture: str | None = Field(default=None, max_length=500)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
    last_login: datetime | None = None

    # Relationships
    settings: list["UserSetting"] = Relationship(back_populates="user")
    roles: list["UserRole"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")
    ereader_devices: list["EReaderDevice"] = Relationship(back_populates="user")


class UserSetting(SQLModel, table=True):
    """User setting model for key-value user preferences.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    key : str
        Setting key (max 100 chars).
    value : str
        Setting value (max 1000 chars, can store JSON).
    description : str | None
        Optional description of the setting.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "user_settings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    key: str = Field(max_length=100, index=True)
    value: str = Field(max_length=1000)
    description: str | None = Field(default=None, max_length=500)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        index=True,
    )

    # Relationships
    user: User = Relationship(back_populates="settings")

    model_config = ConfigDict()
    indexes: ClassVar[list[tuple[str, ...]]] = [
        ("user_id", "key"),  # Composite unique index
    ]


class Role(SQLModel, table=True):
    """Role model for role-based access control.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    name : str
        Unique role name (e.g., 'admin', 'user', 'viewer').
    description : str | None
        Role description.
    created_at : datetime
        Role creation timestamp.
    """

    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    users: list["UserRole"] = Relationship(back_populates="role")
    permissions: list["RolePermission"] = Relationship(back_populates="role")


class Permission(SQLModel, table=True):
    """Permission model for fine-grained access control.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    name : str
        Unique permission name (e.g., 'books:read', 'books:delete').
    description : str | None
        Permission description.
    resource : str
        Resource name (e.g., 'books', 'users').
    action : str
        Action name (e.g., 'read', 'write', 'delete').
    created_at : datetime
        Permission creation timestamp.
    """

    __tablename__ = "permissions"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    resource: str = Field(max_length=50, index=True)
    action: str = Field(max_length=50, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    roles: list["RolePermission"] = Relationship(back_populates="permission")


class UserRole(SQLModel, table=True):
    """User-role association table.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    role_id : int
        Foreign key to role.
    assigned_at : datetime
        Assignment timestamp.
    """

    __tablename__ = "user_roles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    user: User = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="users")

    model_config = ConfigDict()
    indexes: ClassVar[list[tuple[str, ...]]] = [
        ("user_id", "role_id"),  # Composite unique index
    ]


class RolePermission(SQLModel, table=True):
    """Role-permission association table with optional resource conditions.

    Supports resource-specific permissions through the `condition` field.
    When `condition` is None, the permission applies globally.
    When `condition` is set, the permission only applies when the condition matches.

    Condition examples:
    - Tag-based: `{"tag": "kids"}` or `{"tags": ["kids", "young-adult"]}`
    - Author-based: `{"author_id": 123}` or `{"author_ids": [1, 2, 3]}`
    - Genre-based: `{"genre": "fiction"}`
    - Series-based: `{"series_id": 456}`
    - Multiple: `{"tags": ["kids"], "author_id": 123}`

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    role_id : int
        Foreign key to role.
    permission_id : int
        Foreign key to permission.
    condition : dict[str, Any] | None
        Optional JSON condition that specifies when this permission applies.
        None means the permission applies globally to all resources.
    assigned_at : datetime
        Assignment timestamp.
    """

    __tablename__ = "role_permissions"

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    permission_id: int = Field(foreign_key="permissions.id", index=True)
    condition: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    role: Role = Relationship(back_populates="permissions")
    permission: Permission = Relationship(back_populates="roles")

    model_config = ConfigDict()
    indexes: ClassVar[list[tuple[str, ...]]] = [
        ("role_id", "permission_id"),  # Composite unique index
    ]


class RefreshToken(SQLModel, table=True):
    """Refresh token model for JWT token refresh.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    token_hash : str
        Hashed refresh token (for security).
    expires_at : datetime
        Token expiration timestamp.
    revoked : bool
        Whether token has been revoked.
    device_info : str | None
        Optional device/browser information.
    created_at : datetime
        Token creation timestamp.
    last_used_at : datetime | None
        Last time token was used.
    """

    __tablename__ = "refresh_tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True, max_length=255)
    expires_at: datetime = Field(index=True)
    revoked: bool = False
    device_info: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    last_used_at: datetime | None = None

    # Relationships
    user: User = Relationship(back_populates="refresh_tokens")


class Invite(SQLModel, table=True):
    """Invitation token for user registration.

    Supports invite-only registration by requiring a valid invitation
    token to create new user accounts. Tokens can be created by admins
    or existing users and have expiration dates.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    token : str
        Unique invitation token (UUID format).
    created_by : int
        Foreign key reference to the user who created this invite.
    used_by : int | None
        Foreign key reference to the user who used this invite, if any.
    created_at : datetime
        Timestamp when the invite was created.
    expires_at : datetime
        Timestamp when the invite expires.
    used_at : datetime | None
        Timestamp when the invite was used, if any.
    """

    __tablename__ = "invites"

    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(
        default_factory=lambda: str(uuid4()),
        unique=True,
        index=True,
        max_length=255,
    )
    created_by: int = Field(foreign_key="users.id", index=True)
    used_by: int | None = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    expires_at: datetime = Field(index=True)
    used_at: datetime | None = Field(default=None)


class TokenBlacklist(SQLModel, table=True):
    """Blacklisted JWT token IDs.

    Stores JWT IDs (jti) of tokens that have been revoked/logged out.
    Tokens are checked against this blacklist during validation.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    jti : str
        JWT ID (jti claim) of the blacklisted token.
    expires_at : datetime
        Token expiration timestamp (for cleanup purposes).
    created_at : datetime
        When the token was blacklisted.
    """

    __tablename__ = "token_blacklist"

    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(unique=True, index=True, max_length=255)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )


class EReaderDevice(SQLModel, table=True):
    """E-reader device email configuration.

    Stores e-reader email addresses and preferences for sending books
    to devices like Kindle, Kobo, and other e-readers.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    email : str
        E-reader email address (e.g., Kindle send-to-email).
    device_name : str | None
        User-friendly device name (e.g., "My Kindle", "Kobo Clara").
    device_type : str
        Device type: 'kindle', 'kobo', 'generic', etc.
    is_default : bool
        Whether this is the default device for sending.
    preferred_format : EBookFormat | None
        Preferred format for this device (e.g., EPUB, MOBI, AZW3).
    created_at : datetime
        Device creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "ereader_devices"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    email: str = Field(max_length=255, index=True)
    device_name: str | None = Field(default=None, max_length=100)
    device_type: str = Field(default="kindle", max_length=50)
    is_default: bool = Field(default=False)
    preferred_format: EBookFormat | None = Field(
        default=None,
        sa_column=Column(SQLEnum(EBookFormat, native_enum=False)),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    user: User = Relationship(back_populates="ereader_devices")

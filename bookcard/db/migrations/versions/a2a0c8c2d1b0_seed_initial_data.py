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

"""Seed initial admin user, roles, and permissions (one-time, idempotent).

Revision ID: a2a0c8c2d1b0
Revises: ce04c7de48d9
Create Date: 2025-11-02 00:00:00.000000

"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from alembic import op
from passlib.context import CryptContext
from sqlalchemy import text

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a2a0c8c2d1b0"
down_revision: str | Sequence[str] | None = "ce04c7de48d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # noqa: C901
    """Insert initial admin user, roles, and permissions (one-time, idempotent).

    Uses environment variables provided by the runtime (e.g., docker-compose):
    - ADMIN_USERNAME
    - ADMIN_EMAIL
    - ADMIN_PASSWORD

    The insertion is guarded to be idempotent:
    - If any row exists in users, roles, or permissions, it skips seeding.
    """
    conn = op.get_bind()

    # Quick exit if any users already exist
    total_users = conn.execute(text("SELECT COUNT(1) FROM users")).scalar_one()
    if int(total_users or 0) > 0:
        return

    # Quick exit if any roles already exist
    total_roles = conn.execute(text("SELECT COUNT(1) FROM roles")).scalar_one()
    if int(total_roles or 0) > 0:
        return

    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip()
    password = os.getenv("ADMIN_PASSWORD", "admin123").strip()

    # Idempotency on username/email too (paranoid check)
    exists = conn.execute(
        text("SELECT 1 FROM users WHERE username = :u OR email = :e LIMIT 1"),
        {"u": username, "e": email},
    ).first()
    if exists is not None:
        return

    # Hash the password with bcrypt via passlib to match application behavior
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_ctx.hash(password)

    now = datetime.now(UTC)

    # Insert admin user
    conn.execute(
        text(
            """
            INSERT INTO users (
                username, email, password_hash, profile_picture, is_active, is_admin,
                created_at, updated_at, last_login
            ) VALUES (
                :username, :email, :password_hash, NULL, TRUE, TRUE,
                :created_at, :updated_at, NULL
            )
            """
        ),
        {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        },
    )
    # Get the inserted user ID
    user_result = conn.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": username},
    )
    user_id = user_result.scalar_one()

    # Insert default user settings for the admin user
    default_settings = {
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

    for key, value in default_settings.items():
        # Convert value to string representation
        if isinstance(value, bool):
            setting_value = "true" if value else "false"
        elif isinstance(value, list):
            # JSON-encode lists (e.g., metadata providers)
            setting_value = json.dumps(value)
        else:
            # String or other types - convert to string
            setting_value = str(value)

        conn.execute(
            text(
                """
                INSERT INTO user_settings (user_id, key, value, updated_at)
                VALUES (:user_id, :key, :value, :updated_at)
                """
            ),
            {
                "user_id": user_id,
                "key": key,
                "value": setting_value,
                "updated_at": now,
            },
        )

    # Seed roles
    roles_data = [
        ("admin", "Administrator with full system access"),
        ("user", "Standard user with basic access"),
        ("viewer", "Read-only user with viewing permissions"),
    ]

    role_ids = {}
    for role_name, role_description in roles_data:
        conn.execute(
            text(
                """
                INSERT INTO roles (name, description, created_at)
                VALUES (:name, :description, :created_at)
                """
            ),
            {
                "name": role_name,
                "description": role_description,
                "created_at": now,
            },
        )
        # Get the inserted role ID
        role_result = conn.execute(
            text("SELECT id FROM roles WHERE name = :name"),
            {"name": role_name},
        )
        role_ids[role_name] = role_result.scalar_one()

    # Seed permissions
    permissions_data = [
        # User management permissions
        ("users:create", "Create users", "users", "create"),
        ("users:read", "Read user information", "users", "read"),
        ("users:write", "Create and update users", "users", "write"),
        ("users:delete", "Delete users", "users", "delete"),
        # Book management permissions
        ("books:create", "Create (upload) books", "books", "create"),
        ("books:read", "Read book information", "books", "read"),
        ("books:write", "Create and update books", "books", "write"),
        ("books:delete", "Delete books", "books", "delete"),
        ("books:send", "Send books via email", "books", "send"),
        # Shelf management permissions
        ("shelves:create", "Create shelves", "shelves", "create"),
        ("shelves:read", "Read shelf information", "shelves", "read"),
        ("shelves:edit", "Edit any shelf", "shelves", "edit"),
        ("shelves:delete", "Delete shelves", "shelves", "delete"),
        # Role management permissions
        ("roles:read", "Read role information", "roles", "read"),
        ("roles:write", "Create and update roles", "roles", "write"),
        ("roles:delete", "Delete roles", "roles", "delete"),
        # Permission management permissions
        ("permissions:create", "Create permissions", "permissions", "create"),
        ("permissions:read", "Read permission information", "permissions", "read"),
        ("permissions:write", "Create and update permissions", "permissions", "write"),
        ("permissions:delete", "Delete permissions", "permissions", "delete"),
        # System permissions
        ("system:admin", "Full system administration access", "system", "admin"),
    ]

    permission_ids = {}
    for perm_name, perm_description, resource, action in permissions_data:
        conn.execute(
            text(
                """
                INSERT INTO permissions (name, description, resource, action, created_at)
                VALUES (:name, :description, :resource, :action, :created_at)
                """
            ),
            {
                "name": perm_name,
                "description": perm_description,
                "resource": resource,
                "action": action,
                "created_at": now,
            },
        )
        # Get the inserted permission ID
        perm_result = conn.execute(
            text("SELECT id FROM permissions WHERE name = :name"),
            {"name": perm_name},
        )
        permission_ids[perm_name] = perm_result.scalar_one()

    # Assign all permissions to admin role
    admin_role_id = role_ids["admin"]
    for perm_id in permission_ids.values():
        conn.execute(
            text(
                """
                INSERT INTO role_permissions (role_id, permission_id, assigned_at)
                VALUES (:role_id, :permission_id, :assigned_at)
                """
            ),
            {
                "role_id": admin_role_id,
                "permission_id": perm_id,
                "assigned_at": now,
            },
        )

    # Assign basic permissions to user role
    user_role_id = role_ids["user"]
    user_permissions = [
        permission_ids["users:read"],
        permission_ids["books:create"],
        permission_ids["books:read"],
        permission_ids["books:write"],
        permission_ids["books:send"],
        permission_ids["shelves:create"],
        permission_ids["shelves:read"],
    ]
    for perm_id in user_permissions:
        conn.execute(
            text(
                """
                INSERT INTO role_permissions (role_id, permission_id, assigned_at)
                VALUES (:role_id, :permission_id, :assigned_at)
                """
            ),
            {
                "role_id": user_role_id,
                "permission_id": perm_id,
                "assigned_at": now,
            },
        )

    # Assign read-only permissions to viewer role
    viewer_role_id = role_ids["viewer"]
    viewer_permissions = [
        permission_ids["users:read"],
        permission_ids["books:read"],
        permission_ids["shelves:read"],
    ]
    for perm_id in viewer_permissions:
        conn.execute(
            text(
                """
                INSERT INTO role_permissions (role_id, permission_id, assigned_at)
                VALUES (:role_id, :permission_id, :assigned_at)
                """
            ),
            {
                "role_id": viewer_role_id,
                "permission_id": perm_id,
                "assigned_at": now,
            },
        )

    # Assign admin role to the seeded admin user
    conn.execute(
        text(
            """
            INSERT INTO user_roles (user_id, role_id, assigned_at)
            VALUES (:user_id, :role_id, :assigned_at)
            """
        ),
        {
            "user_id": user_id,
            "role_id": admin_role_id,
            "assigned_at": now,
        },
    )


def downgrade() -> None:
    """Remove seeded data: admin user, roles, permissions, and associations.

    This keeps downgrade safe: it won't touch data created later with
    different credentials or names.
    """
    conn = op.get_bind()
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip()

    # Remove user settings for the admin user
    conn.execute(
        text(
            """
            DELETE FROM user_settings
            WHERE user_id IN (
                SELECT id FROM users WHERE username = :u OR email = :e
            )
            """
        ),
        {"u": username, "e": email},
    )

    # Remove user-role associations for the admin user
    conn.execute(
        text(
            """
            DELETE FROM user_roles
            WHERE user_id IN (
                SELECT id FROM users WHERE username = :u OR email = :e
            )
            """
        ),
        {"u": username, "e": email},
    )

    # Remove role-permission associations for seeded roles
    conn.execute(
        text(
            """
            DELETE FROM role_permissions
            WHERE role_id IN (
                SELECT id FROM roles WHERE name IN ('admin', 'user', 'viewer')
            )
            """
        ),
    )

    # Remove seeded permissions
    conn.execute(
        text(
            """
            DELETE FROM permissions
            WHERE name IN (
                'users:create', 'users:read', 'users:write', 'users:delete',
                'books:create', 'books:read', 'books:write', 'books:delete', 'books:send',
                'shelves:create', 'shelves:read', 'shelves:edit', 'shelves:delete',
                'roles:read', 'roles:write', 'roles:delete',
                'permissions:create', 'permissions:read', 'permissions:write', 'permissions:delete',
                'system:admin'
            )
            """
        ),
    )

    # Remove seeded roles
    conn.execute(
        text(
            """
            DELETE FROM roles
            WHERE name IN ('admin', 'user', 'viewer')
            """
        ),
    )

    # Remove the seeded admin user
    conn.execute(
        text("DELETE FROM users WHERE username = :u OR email = :e"),
        {"u": username, "e": email},
    )

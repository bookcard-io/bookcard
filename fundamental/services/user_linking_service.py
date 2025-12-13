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

"""User linking service for external identity providers.

This service contains the domain logic for mapping an external identity
(Keycloak userinfo) to a local `User` row while preserving local RBAC state.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import func
from sqlmodel import select

from fundamental.models.auth import User
from fundamental.repositories.role_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from fundamental.services.role_service import RoleService

if TYPE_CHECKING:
    from sqlmodel import Session


class _UserLookup(Protocol):
    def find_by_keycloak_sub(self, keycloak_sub: str) -> User | None:
        """Find a user by Keycloak subject identifier."""

    def find_by_email(self, email: str) -> User | None:
        """Find a user by email address."""

    def find_by_username(self, username: str) -> User | None:
        """Find a user by username."""


class _PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Hash a password string."""


class UserLinkingService:
    """Link external (Keycloak) identities to local users.

    Parameters
    ----------
    user_repo : UserRepository
        Repository for user lookup and persistence.
    password_hasher : PasswordHasher
        Password hasher used to create a non-usable password hash for new
        externally-authenticated users.
    """

    def __init__(
        self, user_repo: _UserLookup, password_hasher: _PasswordHasher
    ) -> None:
        self._users = user_repo
        self._hasher = password_hasher

    def find_or_create_keycloak_user(
        self, *, userinfo: dict[str, object], session: Session
    ) -> User:
        """Find or create a local user record for a Keycloak-authenticated identity.

        Lookup strategy (in order):
        1) `keycloak_sub` (userinfo ``sub``)
        2) email (userinfo ``email``)
        3) username (userinfo ``preferred_username``)

        If this is the first user in the system, they are automatically
        granted admin privileges (is_admin=True and admin role).

        Parameters
        ----------
        userinfo : dict[str, object]
            OIDC userinfo payload from Keycloak.
        session : Session
            Active database session for persistence.

        Returns
        -------
        User
            The linked or newly created user.

        Raises
        ------
        ValueError
            If userinfo does not contain a subject (``sub``).
        """
        sub = userinfo.get("sub")
        if not isinstance(sub, str) or not sub:
            msg = "keycloak_userinfo_missing_sub"
            raise ValueError(msg)

        email = userinfo.get("email")
        email_str = email if isinstance(email, str) and email else None

        preferred_username = userinfo.get("preferred_username")
        username_str = (
            preferred_username
            if isinstance(preferred_username, str) and preferred_username
            else None
        )

        user = self._users.find_by_keycloak_sub(sub)
        if user is None and email_str:
            user = self._users.find_by_email(email_str)
        if user is None and username_str:
            user = self._users.find_by_username(username_str)

        if user is not None:
            if user.keycloak_sub is None:
                user.keycloak_sub = sub
            user.last_login = datetime.now(UTC)
            session.flush()
            return user

        # Check if this is the first user in the system
        user_count_stmt = select(func.count(User.id))
        user_count = session.exec(user_count_stmt).one() or 0
        is_first_user = user_count == 0

        username = self._derive_available_username(username_str, email_str)
        password = secrets.token_urlsafe(48)
        user = User(
            username=username,
            email=email_str or f"{sub}@keycloak.local",
            password_hash=self._hasher.hash(password),
            keycloak_sub=sub,
            full_name=userinfo.get("name")
            if isinstance(userinfo.get("name"), str)
            else None,
            is_admin=is_first_user,
            last_login=datetime.now(UTC),
        )
        session.add(user)
        session.flush()

        # If first user, assign admin role
        if is_first_user:
            role_repo = RoleRepository(session)
            admin_role = role_repo.find_by_name("admin")
            if admin_role is not None and admin_role.id is not None:
                role_service = RoleService(
                    session,
                    role_repo,
                    PermissionRepository(session),
                    UserRoleRepository(session),
                    RolePermissionRepository(session),
                )
                role_service.assign_role_to_user(user.id, admin_role.id)  # type: ignore[arg-type]

        return user

    def _derive_available_username(
        self, preferred: str | None, email: str | None
    ) -> str:
        base = preferred or (email.split("@", 1)[0] if email else None) or "user"
        base = base.strip()[:64] or "user"
        if self._users.find_by_username(base) is None:
            return base

        for i in range(2, 1000):
            candidate = f"{base}-{i}"
            if len(candidate) > 64:
                candidate = candidate[:64]
            if self._users.find_by_username(candidate) is None:
                return candidate

        # Extremely unlikely; fallback to a random suffix.
        suffix = secrets.token_hex(4)
        candidate = f"{base[:55]}-{suffix}"
        return candidate[:64]

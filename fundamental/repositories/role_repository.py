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

"""Role and permission repositories.

Typed repositories for Role, Permission, UserRole, and RolePermission entities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.auth import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from fundamental.repositories.base import Repository

if TYPE_CHECKING:
    from collections.abc import Iterable


class RoleRepository(Repository[Role]):
    """Repository for `Role` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Role)

    def find_by_name(self, name: str) -> Role | None:
        """Return a role by name if it exists.

        Parameters
        ----------
        name : str
            Role name.

        Returns
        -------
        Role | None
            Role entity if found, None otherwise.
        """
        stmt = select(Role).where(Role.name == name)
        return self._session.exec(stmt).first()

    def list_all(self) -> Iterable[Role]:
        """Return all roles ordered by name.

        Returns
        -------
        Iterable[Role]
            All role entities.
        """
        stmt = select(Role).order_by(Role.name)
        return self._session.exec(stmt).all()


class PermissionRepository(Repository[Permission]):
    """Repository for `Permission` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Permission)

    def find_by_name(self, name: str) -> Permission | None:
        """Return a permission by name if it exists.

        Parameters
        ----------
        name : str
            Permission name.

        Returns
        -------
        Permission | None
            Permission entity if found, None otherwise.
        """
        stmt = select(Permission).where(Permission.name == name)
        return self._session.exec(stmt).first()

    def find_by_resource_action(self, resource: str, action: str) -> Permission | None:
        """Return a permission by resource and action if it exists.

        Parameters
        ----------
        resource : str
            Resource name (e.g., 'books', 'users').
        action : str
            Action name (e.g., 'read', 'write', 'delete').

        Returns
        -------
        Permission | None
            Permission entity if found, None otherwise.
        """
        stmt = select(Permission).where(
            Permission.resource == resource, Permission.action == action
        )
        return self._session.exec(stmt).first()

    def list(self, limit: int | None = None, offset: int = 0) -> Iterable[Permission]:
        """List permissions with simple pagination, ordered by name.

        Parameters
        ----------
        limit : int | None
            Maximum number of records to return.
        offset : int
            Number of records to skip.

        Returns
        -------
        Iterable[Permission]
            Permission entities ordered by name.
        """
        stmt = select(Permission).order_by(Permission.name).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return self._session.exec(stmt).all()

    def list_by_resource(self, resource: str) -> Iterable[Permission]:
        """Return all permissions for a resource, ordered by name.

        Parameters
        ----------
        resource : str
            Resource name.

        Returns
        -------
        Iterable[Permission]
            Permission entities for the resource, ordered by name.
        """
        stmt = (
            select(Permission)
            .where(Permission.resource == resource)
            .order_by(Permission.name)
        )
        return self._session.exec(stmt).all()


class UserRoleRepository(Repository[UserRole]):
    """Repository for `UserRole` association entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, UserRole)

    def find_by_user_role(self, user_id: int, role_id: int) -> UserRole | None:
        """Return a user-role association if it exists.

        Parameters
        ----------
        user_id : int
            User identifier.
        role_id : int
            Role identifier.

        Returns
        -------
        UserRole | None
            UserRole entity if found, None otherwise.
        """
        stmt = select(UserRole).where(
            UserRole.user_id == user_id, UserRole.role_id == role_id
        )
        return self._session.exec(stmt).first()

    def list_by_user(self, user_id: int) -> Iterable[UserRole]:
        """Return all roles for a user.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        Iterable[UserRole]
            UserRole entities for the user.
        """
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        return self._session.exec(stmt).all()

    def list_by_role(self, role_id: int) -> Iterable[UserRole]:
        """Return all users with a role.

        Parameters
        ----------
        role_id : int
            Role identifier.

        Returns
        -------
        Iterable[UserRole]
            UserRole entities for the role.
        """
        stmt = select(UserRole).where(UserRole.role_id == role_id)
        return self._session.exec(stmt).all()


class RolePermissionRepository(Repository[RolePermission]):
    """Repository for `RolePermission` association entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, RolePermission)

    def find_by_role_permission(
        self, role_id: int, permission_id: int
    ) -> RolePermission | None:
        """Return a role-permission association if it exists.

        Parameters
        ----------
        role_id : int
            Role identifier.
        permission_id : int
            Permission identifier.

        Returns
        -------
        RolePermission | None
            RolePermission entity if found, None otherwise.
        """
        stmt = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        return self._session.exec(stmt).first()

    def list_by_role(self, role_id: int) -> Iterable[RolePermission]:
        """Return all permissions for a role.

        Parameters
        ----------
        role_id : int
            Role identifier.

        Returns
        -------
        Iterable[RolePermission]
            RolePermission entities for the role.
        """
        stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        return self._session.exec(stmt).all()

    def list_by_permission(self, permission_id: int) -> Iterable[RolePermission]:
        """Return all roles with a permission.

        Parameters
        ----------
        permission_id : int
            Permission identifier.

        Returns
        -------
        Iterable[RolePermission]
            RolePermission entities for the permission.
        """
        stmt = select(RolePermission).where(
            RolePermission.permission_id == permission_id
        )
        return self._session.exec(stmt).all()

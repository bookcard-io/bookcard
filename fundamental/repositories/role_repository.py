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

    def list_by_resource(self, resource: str) -> Iterable[Permission]:
        """Return all permissions for a resource.

        Parameters
        ----------
        resource : str
            Resource name.

        Returns
        -------
        Iterable[Permission]
            Permission entities for the resource.
        """
        stmt = select(Permission).where(Permission.resource == resource)
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

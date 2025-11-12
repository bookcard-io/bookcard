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

"""Role and permission service.

Encapsulates role and permission management operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fundamental.models.auth import Role, RolePermission, UserRole

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.role_repository import (
        PermissionRepository,
        RolePermissionRepository,
        RoleRepository,
        UserRoleRepository,
    )


class RoleService:
    """Operations for managing roles and permissions.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    roles : RoleRepository
        Repository providing role persistence operations.
    permissions : PermissionRepository
        Repository providing permission persistence operations.
    user_roles : UserRoleRepository
        Repository providing user-role association operations.
    role_permissions : RolePermissionRepository
        Repository providing role-permission association operations.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        roles: RoleRepository,  # type: ignore[type-arg]
        permissions: PermissionRepository,  # type: ignore[type-arg]
        user_roles: UserRoleRepository,  # type: ignore[type-arg]
        role_permissions: RolePermissionRepository,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._roles = roles
        self._permissions = permissions
        self._user_roles = user_roles
        self._role_permissions = role_permissions

    def create_role(self, name: str, description: str | None = None) -> Role:
        """Create a new role.

        Parameters
        ----------
        name : str
            Role name (must be unique).
        description : str | None
            Optional role description.

        Returns
        -------
        Role
            Created role entity.

        Raises
        ------
        ValueError
            If a role with the given name already exists.
        """
        existing = self._roles.find_by_name(name)
        if existing is not None:
            msg = "role_already_exists"
            raise ValueError(msg)

        role = Role(name=name, description=description)
        self._roles.add(role)
        self._session.flush()
        return role

    def assign_role_to_user(self, user_id: int, role_id: int) -> UserRole:
        """Assign a role to a user.

        Parameters
        ----------
        user_id : int
            User identifier.
        role_id : int
            Role identifier.

        Returns
        -------
        UserRole
            Created user-role association.

        Raises
        ------
        ValueError
            If the association already exists.
        """
        existing = self._user_roles.find_by_user_role(user_id, role_id)
        if existing is not None:
            msg = "user_already_has_role"
            raise ValueError(msg)

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_at=datetime.now(UTC),
        )
        self._user_roles.add(user_role)
        self._session.flush()
        return user_role

    def remove_role_from_user(self, user_id: int, role_id: int) -> None:
        """Remove a role from a user.

        Parameters
        ----------
        user_id : int
            User identifier.
        role_id : int
            Role identifier.

        Raises
        ------
        ValueError
            If the association does not exist.
        """
        user_role = self._user_roles.find_by_user_role(user_id, role_id)
        if user_role is None:
            msg = "user_role_not_found"
            raise ValueError(msg)

        self._user_roles.delete(user_role)
        self._session.flush()

    def grant_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        condition: dict[str, object] | None = None,
    ) -> RolePermission:
        """Grant a permission to a role.

        Parameters
        ----------
        role_id : int
            Role identifier.
        permission_id : int
            Permission identifier.
        condition : dict[str, object] | None
            Optional condition for resource-specific permissions.

        Returns
        -------
        RolePermission
            Created role-permission association.

        Raises
        ------
        ValueError
            If the association already exists.
        """
        existing = self._role_permissions.find_by_role_permission(
            role_id, permission_id
        )
        if existing is not None:
            msg = "role_already_has_permission"
            raise ValueError(msg)

        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            condition=condition,
        )
        self._role_permissions.add(role_permission)
        self._session.flush()
        return role_permission

    def revoke_permission_from_role(self, role_id: int, permission_id: int) -> None:
        """Revoke a permission from a role.

        Parameters
        ----------
        role_id : int
            Role identifier.
        permission_id : int
            Permission identifier.

        Raises
        ------
        ValueError
            If the association does not exist.
        """
        role_permission = self._role_permissions.find_by_role_permission(
            role_id, permission_id
        )
        if role_permission is None:
            msg = "role_permission_not_found"
            raise ValueError(msg)

        self._role_permissions.delete(role_permission)
        self._session.flush()

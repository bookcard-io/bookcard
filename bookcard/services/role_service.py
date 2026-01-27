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

from bookcard.models.auth import Permission, Role, RolePermission, UserRole

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.api.schemas.auth import (
        PermissionAssignment,
        PermissionUpdate,
        RoleCreate,
        RoleUpdate,
    )
    from bookcard.repositories.role_repository import (
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
        session: Session,
        roles: RoleRepository,
        permissions: PermissionRepository,
        user_roles: UserRoleRepository,
        role_permissions: RolePermissionRepository,
    ) -> None:
        self._session = session
        self._roles = roles
        self._permissions = permissions
        self._user_roles = user_roles
        self._role_permissions = role_permissions

    def create_role(
        self,
        name: str,
        description: str | None = None,
        permission_assignments: list[dict] | None = None,
    ) -> Role:
        """Create a new role with optional permissions.

        Parameters
        ----------
        name : str
            Role name (must be unique).
        description : str | None
            Optional role description.
        permission_assignments : list[dict] | None
            List of permission assignments. Each dict should have:
            - permission_id (int | None): Existing permission ID
            - permission_name (str | None): Permission name to find or create
            - resource (str | None): Resource name (for new permissions)
            - action (str | None): Action name (for new permissions)
            - permission_description (str | None): Description (for new permissions)
            - condition (dict[str, object] | None): Optional condition

        Returns
        -------
        Role
            Created role entity.

        Raises
        ------
        ValueError
            If a role with the given name already exists or if permission data is invalid.
        """
        existing = self._roles.find_by_name(name)
        if existing is not None:
            msg = "role_already_exists"
            raise ValueError(msg)

        role = Role(name=name, description=description)
        self._roles.add(role)
        self._session.flush()

        # Assign permissions if provided
        if permission_assignments:
            for assignment in permission_assignments:
                permission_id = assignment.get("permission_id")
                permission_name = assignment.get("permission_name")
                resource = assignment.get("resource")
                action = assignment.get("action")
                permission_description = assignment.get("permission_description")
                condition = assignment.get("condition")

                # Determine which permission to use
                if permission_id is not None:
                    # Use existing permission by ID
                    permission = self._permissions.get(permission_id)
                    if permission is None:
                        msg = "permission_not_found"
                        raise ValueError(msg)
                elif permission_name is not None:
                    # Find or create permission by name
                    if resource is None or action is None:
                        msg = "resource_and_action_required_for_new_permission"
                        raise ValueError(msg)
                    permission = self.get_or_create_permission(
                        permission_name,
                        resource,
                        action,
                        permission_description,
                    )
                else:
                    msg = "permission_id_or_permission_name_required"
                    raise ValueError(msg)

                # Grant permission to role
                if permission.id is None:
                    msg = "permission_id_is_none"
                    raise ValueError(msg)
                if role.id is None:
                    msg = "role_id_is_none"
                    raise ValueError(msg)
                # Type narrowing: both IDs are guaranteed to be int here
                permission_id: int = permission.id
                role_id_int: int = role.id
                self.grant_permission_to_role(
                    role_id_int,
                    permission_id,
                    condition,
                )

        return role

    def _update_role_name(
        self,
        role: Role,
        name: str | None,
        is_locked: bool,
        role_id: int,
    ) -> None:
        """Update role name with validation.

        Parameters
        ----------
        role : Role
            Role entity to update.
        name : str | None
            New role name.
        is_locked : bool
            Whether the role is locked.
        role_id : int
            Role identifier.

        Raises
        ------
        ValueError
            If trying to modify locked role name or if name already exists.
        """
        if name is None or name == role.name:
            return

        # Admin role protection (id == 1)
        if is_locked and role_id == 1:
            msg = "cannot_modify_locked_role_name"
            raise ValueError(msg)

        # Check if new name already exists
        existing = self._roles.find_by_name(name)
        if existing is not None:
            msg = "role_already_exists"
            raise ValueError(msg)

        role.name = name

    def _remove_role_permissions(
        self,
        role_id: int,
        removed_permission_ids: list[int],
        is_locked: bool,
    ) -> None:
        """Remove permissions from a role.

        Parameters
        ----------
        role_id : int
            Role identifier.
        removed_permission_ids : list[int]
            List of role_permission IDs to remove.
        is_locked : bool
            Whether the role is locked.

        Raises
        ------
        ValueError
            If trying to remove permissions from locked role or if permission not found.
        """
        if not removed_permission_ids:
            return

        if is_locked and role_id == 1:
            msg = "cannot_remove_permissions_from_locked_role"
            raise ValueError(msg)

        for role_permission_id in removed_permission_ids:
            role_permission = self._role_permissions.get(role_permission_id)
            if role_permission is None:
                msg = "role_permission_not_found"
                raise ValueError(msg)
            if role_permission.role_id != role_id:
                msg = "role_permission_belongs_to_different_role"
                raise ValueError(msg)
            self._role_permissions.delete(role_permission)

    def _add_role_permissions(
        self,
        role_id: int,
        permission_assignments: list[dict],
    ) -> None:
        """Add permissions to a role.

        Parameters
        ----------
        role_id : int
            Role identifier.
        permission_assignments : list[dict]
            List of permission assignments to add.

        Raises
        ------
        ValueError
            If permission data is invalid.
        """
        if not permission_assignments:
            return

        for assignment in permission_assignments:
            permission_id = assignment.get("permission_id")
            permission_name = assignment.get("permission_name")
            resource = assignment.get("resource")
            action = assignment.get("action")
            permission_description = assignment.get("permission_description")
            condition = assignment.get("condition")

            # Determine which permission to use
            if permission_id is not None:
                # Use existing permission by ID
                permission = self._permissions.get(permission_id)
                if permission is None:
                    msg = "permission_not_found"
                    raise ValueError(msg)
            elif permission_name is not None:
                # Find or create permission by name
                if resource is None or action is None:
                    msg = "resource_and_action_required_for_new_permission"
                    raise ValueError(msg)
                permission = self.get_or_create_permission(
                    permission_name,
                    resource,
                    action,
                    permission_description,
                )
            else:
                msg = "permission_id_or_permission_name_required"
                raise ValueError(msg)

            # Grant permission to role (will raise if already exists)
            if permission.id is None:
                msg = "permission_id_is_none"
                raise ValueError(msg)
            # Type narrowing: permission.id is guaranteed to be int here
            permission_id_int: int = permission.id
            try:
                self.grant_permission_to_role(
                    role_id,
                    permission_id_int,
                    condition,
                )
            except ValueError as exc:
                if str(exc) != "role_already_has_permission":
                    raise
                # Ignore if permission already granted

    def update_role(
        self,
        role_id: int,
        name: str | None = None,
        description: str | None = None,
        permission_assignments: list[dict] | None = None,
        removed_permission_ids: list[int] | None = None,
        is_locked: bool = False,
    ) -> Role:
        """Update an existing role with optional permission changes.

        Parameters
        ----------
        role_id : int
            Role identifier.
        name : str | None
            New role name (must be unique if provided).
        description : str | None
            New role description.
        permission_assignments : list[dict] | None
            List of permission assignments to add. Each dict should have:
            - permission_id (int | None): Existing permission ID
            - permission_name (str | None): Permission name to find or create
            - resource (str | None): Resource name (for new permissions)
            - action (str | None): Action name (for new permissions)
            - permission_description (str | None): Description (for new permissions)
            - condition (dict[str, object] | None): Optional condition
        removed_permission_ids : list[int] | None
            List of role_permission IDs to remove.
        is_locked : bool
            Whether the role is locked (admin protection).

        Returns
        -------
        Role
            Updated role entity.

        Raises
        ------
        ValueError
            If role not found, if a role with the given name already exists,
            if trying to modify locked role, or if permission data is invalid.
        """
        role = self._roles.get(role_id)
        if role is None:
            msg = "role_not_found"
            raise ValueError(msg)

        # Update role name
        self._update_role_name(role, name, is_locked, role_id)

        # Update description
        if description is not None:
            role.description = description

        # Handle permission removals
        self._remove_role_permissions(role_id, removed_permission_ids or [], is_locked)

        # Handle permission additions
        if permission_assignments:
            self._add_role_permissions(role_id, permission_assignments)

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

    def can_delete_role(self, role_id: int) -> tuple[bool, str | None]:
        """Check if a role can be deleted.

        Parameters
        ----------
        role_id : int
            Role identifier.

        Returns
        -------
        tuple[bool, str | None]
            (can_delete, error_message)
            - can_delete: True if role can be deleted, False otherwise
            - error_message: Error message if role cannot be deleted, None otherwise
        """
        role = self._roles.get(role_id)
        if role is None:
            return (False, "role_not_found")

        # Check if role is locked (admin role id == 1)
        if role_id == 1:
            return (False, "cannot_delete_locked_role")

        # Check if role is assigned to any users
        user_roles = list(self._user_roles.list_by_role(role_id))
        if user_roles:
            user_count = len(user_roles)
            return (
                False,
                f"role_assigned_to_users_{user_count}",
            )

        return (True, None)

    def delete_role(self, role_id: int) -> None:
        """Delete a role.

        Parameters
        ----------
        role_id : int
            Role identifier.

        Raises
        ------
        ValueError
            If role not found, if role is locked, or if role is assigned to users.
        """
        can_delete, error_message = self.can_delete_role(role_id)
        if not can_delete:
            if error_message:
                msg = error_message
                raise ValueError(msg)
            msg = "cannot_delete_role"
            raise ValueError(msg)

        role = self._roles.get(role_id)
        if role is None:
            msg = "role_not_found"
            raise ValueError(msg)

        # Delete all role-permission associations first to avoid NOT NULL constraint violation
        role_permissions = list(self._role_permissions.list_by_role(role_id))
        for role_permission in role_permissions:
            self._role_permissions.delete(role_permission)

        # Now delete the role
        self._roles.delete(role)
        self._session.flush()

    def can_delete_permission(self, permission_id: int) -> tuple[bool, str | None]:
        """Check if a permission can be deleted.

        A permission can only be deleted if it has no role associations
        (i.e., it is orphaned).

        Parameters
        ----------
        permission_id : int
            Permission identifier.

        Returns
        -------
        tuple[bool, str | None]
            (can_delete, error_message)
            - can_delete: True if permission can be deleted, False otherwise
            - error_message: Error message if permission cannot be deleted, None otherwise
        """
        permission = self._permissions.get(permission_id)
        if permission is None:
            return (False, "permission_not_found")

        # Check if permission is associated with any roles
        role_permissions = list(
            self._role_permissions.list_by_permission(permission_id),
        )
        if role_permissions:
            role_count = len({rp.role_id for rp in role_permissions})
            return (
                False,
                f"permission_assigned_to_roles_{role_count}",
            )

        return (True, None)

    def delete_permission(self, permission_id: int) -> None:
        """Delete a permission.

        Only allows deletion of orphaned permissions (permissions with no role associations).

        Parameters
        ----------
        permission_id : int
            Permission identifier.

        Raises
        ------
        ValueError
            If permission not found or if permission is associated with roles.
        """
        can_delete, error_message = self.can_delete_permission(permission_id)
        if not can_delete:
            if error_message:
                msg = error_message
                raise ValueError(msg)
            msg = "cannot_delete_permission"
            raise ValueError(msg)

        permission = self._permissions.get(permission_id)
        if permission is None:
            msg = "permission_not_found"
            raise ValueError(msg)

        # Delete the permission (no associations exist, so safe to delete)
        self._permissions.delete(permission)
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

    def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: str | None = None,
    ) -> Permission:
        """Create a new permission.

        Parameters
        ----------
        name : str
            Permission name (must be unique).
        resource : str
            Resource name (e.g., 'books', 'users').
        action : str
            Action name (e.g., 'read', 'write', 'delete').
        description : str | None
            Optional permission description.

        Returns
        -------
        Permission
            Created permission entity.

        Raises
        ------
        ValueError
            If a permission with the given name already exists.
        """
        existing = self._permissions.find_by_name(name)
        if existing is not None:
            msg = "permission_already_exists"
            raise ValueError(msg)

        # Also check by resource+action for integrity
        existing_by_resource_action = self._permissions.find_by_resource_action(
            resource, action
        )
        if existing_by_resource_action is not None:
            msg = "permission_with_resource_action_already_exists"
            raise ValueError(msg)

        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
        self._permissions.add(permission)
        self._session.flush()
        return permission

    def get_or_create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: str | None = None,
    ) -> Permission:
        """Get an existing permission or create a new one.

        Parameters
        ----------
        name : str
            Permission name.
        resource : str
            Resource name.
        action : str
            Action name.
        description : str | None
            Optional permission description (only used if creating).

        Returns
        -------
        Permission
            Existing or newly created permission entity.
        """
        # Try to find by name first
        existing = self._permissions.find_by_name(name)
        if existing is not None:
            # Verify resource and action match
            if existing.resource != resource or existing.action != action:
                msg = "permission_name_exists_with_different_resource_action"
                raise ValueError(msg)
            return existing

        # Try to find by resource+action
        existing_by_resource_action = self._permissions.find_by_resource_action(
            resource, action
        )
        if existing_by_resource_action is not None:
            # Verify name matches
            if existing_by_resource_action.name != name:
                msg = "permission_resource_action_exists_with_different_name"
                raise ValueError(msg)
            return existing_by_resource_action

        # Create new permission
        return self.create_permission(name, resource, action, description)

    def update_permission(
        self,
        permission_id: int,
        name: str | None = None,
        description: str | None = None,
        resource: str | None = None,
        action: str | None = None,
    ) -> Permission:
        """Update an existing permission.

        Parameters
        ----------
        permission_id : int
            Permission identifier.
        name : str | None
            New permission name (must be unique if provided).
        description : str | None
            New permission description.
        resource : str | None
            New resource name.
        action : str | None
            New action name.

        Returns
        -------
        Permission
            Updated permission entity.

        Raises
        ------
        ValueError
            If permission not found or if a permission with the given name already exists.
        """
        permission = self._permissions.get(permission_id)
        if permission is None:
            msg = "permission_not_found"
            raise ValueError(msg)

        if name is not None and name != permission.name:
            # Check if name is being changed and if new name already exists
            existing = self._permissions.find_by_name(name)
            if existing is not None:
                msg = "permission_already_exists"
                raise ValueError(msg)
            permission.name = name

        if description is not None:
            permission.description = description

        if resource is not None and resource != permission.resource:
            # Check if resource+action combination already exists
            existing_by_resource_action = self._permissions.find_by_resource_action(
                resource, action or permission.action
            )
            if existing_by_resource_action is not None:
                msg = "permission_with_resource_action_already_exists"
                raise ValueError(msg)
            permission.resource = resource

        if action is not None and action != permission.action:
            # Check if resource+action combination already exists
            existing_by_resource_action = self._permissions.find_by_resource_action(
                resource or permission.resource, action
            )
            if existing_by_resource_action is not None:
                msg = "permission_with_resource_action_already_exists"
                raise ValueError(msg)
            permission.action = action

        self._session.flush()
        return permission

    def update_role_permission_condition(
        self,
        role_permission_id: int,
        condition: dict[str, object] | None,
    ) -> RolePermission:
        """Update the condition on a role-permission association.

        Parameters
        ----------
        role_permission_id : int
            Role-permission association identifier.
        condition : dict[str, object] | None
            New condition (None to remove condition).

        Returns
        -------
        RolePermission
            Updated role-permission association.

        Raises
        ------
        ValueError
            If role-permission association not found.
        """
        role_permission = self._role_permissions.get(role_permission_id)
        if role_permission is None:
            msg = "role_permission_not_found"
            raise ValueError(msg)

        role_permission.condition = condition
        self._session.flush()
        return role_permission

    def update_permission_from_schema(
        self,
        permission_id: int,
        payload: PermissionUpdate,
    ) -> Permission:
        """Update a permission from API schema payload.

        Parameters
        ----------
        permission_id : int
            Permission identifier.
        payload : PermissionUpdate
            Permission update payload from API.

        Returns
        -------
        Permission
            Updated permission entity.

        Raises
        ------
        ValueError
            If permission not found, if inputs are invalid, or if permission name/resource+action already exists.
        """
        # Validate and trim inputs
        name = None
        if payload.name is not None:
            name = payload.name.strip()
            if not name:
                msg = "name_cannot_be_blank"
                raise ValueError(msg)

        description = None
        if payload.description is not None:
            description = payload.description.strip()
            if description == "":
                description = None

        resource = None
        if payload.resource is not None:
            resource = payload.resource.strip()
            if not resource:
                msg = "resource_cannot_be_blank"
                raise ValueError(msg)

        action = None
        if payload.action is not None:
            action = payload.action.strip()
            if not action:
                msg = "action_cannot_be_blank"
                raise ValueError(msg)

        return self.update_permission(
            permission_id,
            name=name,
            description=description,
            resource=resource,
            action=action,
        )

    def _process_permission_assignments(
        self,
        permission_assignments: list[PermissionAssignment],
    ) -> list[dict]:
        """Process permission assignments from schema into service format.

        Parameters
        ----------
        permission_assignments : list[PermissionAssignment]
            Permission assignments from API schema.

        Returns
        -------
        list[dict]
            Processed permission assignments in service format.

        Raises
        ------
        ValueError
            If permission assignment data is invalid.
        """
        processed = []
        for perm in permission_assignments:
            assignment: dict = {}

            # Handle existing permission by ID
            if perm.permission_id is not None:
                assignment["permission_id"] = perm.permission_id
            # Handle permission by name (existing or new)
            elif perm.permission_name:
                perm_name = perm.permission_name.strip()
                if not perm_name:
                    msg = "permission_name_cannot_be_blank"
                    raise ValueError(msg)
                assignment["permission_name"] = perm_name

                # For new permissions, validate required fields
                if perm.permission_id is None:
                    resource = perm.resource.strip() if perm.resource else ""
                    action = perm.action.strip() if perm.action else ""
                    if not resource:
                        msg = "resource_cannot_be_blank"
                        raise ValueError(msg)
                    if not action:
                        msg = "action_cannot_be_blank"
                        raise ValueError(msg)
                    assignment["resource"] = resource
                    assignment["action"] = action
                    assignment["permission_description"] = (
                        perm.permission_description.strip()
                        if perm.permission_description
                        else None
                    )
                    if assignment["permission_description"] == "":
                        assignment["permission_description"] = None
            else:
                msg = "permission_id_or_permission_name_required"
                raise ValueError(msg)

            # Condition is already validated as dict by Pydantic
            assignment["condition"] = perm.condition

            processed.append(assignment)
        return processed

    def create_role_from_schema(self, payload: RoleCreate) -> Role:
        """Create a new role from API schema payload.

        Parameters
        ----------
        payload : RoleCreate
            Role creation payload from API.

        Returns
        -------
        Role
            Created role entity.

        Raises
        ------
        ValueError
            If role name already exists, if inputs are invalid, or if permission data is invalid.
        """
        # Validate and trim inputs
        name = payload.name.strip() if payload.name else ""
        if not name:
            msg = "name_cannot_be_blank"
            raise ValueError(msg)
        description = payload.description.strip() if payload.description else None
        if description == "":
            description = None

        # Process permission assignments
        permission_assignments = None
        if payload.permissions:
            permission_assignments = self._process_permission_assignments(
                payload.permissions
            )

        return self.create_role(name, description, permission_assignments)

    def update_role_from_schema(
        self,
        role_id: int,
        payload: RoleUpdate,
        is_locked: bool = False,
    ) -> Role:
        """Update an existing role from API schema payload.

        Parameters
        ----------
        role_id : int
            Role identifier.
        payload : RoleUpdate
            Role update payload from API.
        is_locked : bool
            Whether the role is locked (admin protection).

        Returns
        -------
        Role
            Updated role entity.

        Raises
        ------
        ValueError
            If role not found, if inputs are invalid, if trying to modify locked role,
            or if permission data is invalid.
        """
        # Validate and trim inputs
        name = None
        if payload.name is not None:
            name = payload.name.strip()
            if not name:
                msg = "name_cannot_be_blank"
                raise ValueError(msg)

        description = None
        if payload.description is not None:
            description = payload.description.strip()
            if description == "":
                description = None

        # Process permission assignments
        permission_assignments = None
        if payload.permissions is not None:
            permission_assignments = self._process_permission_assignments(
                payload.permissions
            )

        return self.update_role(
            role_id,
            name=name,
            description=description,
            permission_assignments=permission_assignments,
            removed_permission_ids=payload.removed_permission_ids
            if payload.removed_permission_ids
            else None,
            is_locked=is_locked,
        )

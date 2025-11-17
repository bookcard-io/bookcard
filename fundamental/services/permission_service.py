# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Permission service for checking user permissions with condition evaluation.

Provides permission checking functionality with support for conditional permissions
based on resource metadata (e.g., restrict by author, tags, series).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlmodel import select

from fundamental.models.auth import Permission, RolePermission, UserRole

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlmodel import Session

    from fundamental.models.auth import User


class PermissionService:
    """Service for checking user permissions with condition evaluation.

    Supports conditional permissions that apply only when resource metadata
    matches specified conditions (e.g., author, tags, series).

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        self._session = session

    def has_permission(
        self,
        user: User,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if user has permission for resource:action.

        Checks all roles assigned to the user and evaluates any conditions
        against the provided context. Returns True if any role has the
        permission without conditions, or if any role has the permission
        with conditions that match the context.

        Parameters
        ----------
        user : User
            User to check permissions for.
        resource : str
            Resource name (e.g., 'books', 'shelves').
        action : str
            Action name (e.g., 'read', 'write', 'delete').
        context : dict[str, Any] | None
            Optional resource context for condition evaluation.
            For books, should include: authors, author_ids, tags, series_id, etc.
            For shelves, should include: owner_id, etc.

        Returns
        -------
        bool
            True if user has permission, False otherwise.
        """
        if user.id is None:
            return False

        # Admin users have all permissions
        if user.is_admin:
            return True

        # Get all permissions for the user's roles
        user_permissions = self.get_user_permissions(user)

        # Find matching permission
        for perm_data in user_permissions:
            perm = perm_data["permission"]
            condition = perm_data["condition"]

            # Check if permission matches resource:action
            if perm.resource != resource or perm.action != action:
                continue

            # If no condition, permission applies globally
            if condition is None:
                return True

            # Evaluate condition against context
            if context is not None and self.evaluate_condition(
                condition, context, user
            ):
                return True

        return False

    def check_permission(
        self,
        user: User,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Check permission and raise exception if denied.

        Parameters
        ----------
        user : User
            User to check permissions for.
        resource : str
            Resource name (e.g., 'books', 'shelves').
        action : str
            Action name (e.g., 'read', 'write', 'delete').
        context : dict[str, Any] | None
            Optional resource context for condition evaluation.

        Raises
        ------
        PermissionError
            If user does not have the required permission.
        """
        if not self.has_permission(user, resource, action, context):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"permission_denied: {resource}:{action}",
            )

    def _normalize_list(self, value: object) -> list[object]:
        """Normalize value to a list.

        Parameters
        ----------
        value : object
            Value to normalize.

        Returns
        -------
        list[object]
            List containing the value, or empty list if value is None/empty.
        """
        if not value:
            return []
        if isinstance(value, list):
            return list(value)  # Ensure it's a list[object]
        return [value]

    def _check_author_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check author name condition.

        Parameters
        ----------
        expected_value : Any
            Expected author name.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        authors = self._normalize_list(resource_data.get("authors", []))
        return expected_value in authors

    def _check_author_id_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check author ID condition.

        Parameters
        ----------
        expected_value : Any
            Expected author ID.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        author_ids = self._normalize_list(resource_data.get("author_ids", []))
        return expected_value in author_ids

    def _check_author_ids_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check author IDs list condition.

        Parameters
        ----------
        expected_value : Any
            Expected list of author IDs.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        if not isinstance(expected_value, list):
            return False
        author_ids = self._normalize_list(resource_data.get("author_ids", []))
        return any(aid in author_ids for aid in expected_value)

    def _check_tag_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check single tag condition.

        Parameters
        ----------
        expected_value : Any
            Expected tag name.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        tags = self._normalize_list(resource_data.get("tags", []))
        return expected_value in tags

    def _check_tags_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check tags list condition.

        Parameters
        ----------
        expected_value : Any
            Expected list of tags.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        if not isinstance(expected_value, list):
            return False
        tags = self._normalize_list(resource_data.get("tags", []))
        return any(tag in tags for tag in expected_value)

    def _check_series_id_condition(
        self, expected_value: object, resource_data: dict[str, Any]
    ) -> bool:
        """Check series ID condition.

        Parameters
        ----------
        expected_value : Any
            Expected series ID.
        resource_data : dict[str, Any]
            Resource metadata.

        Returns
        -------
        bool
            True if condition matches.
        """
        series_id = resource_data.get("series_id")
        return series_id == expected_value

    def _check_owner_id_condition(
        self, expected_value: object, resource_data: dict[str, Any], user: User | None
    ) -> bool:
        """Check owner ID condition.

        Parameters
        ----------
        expected_value : Any
            Expected owner ID (supports "user.id" for current user).
        resource_data : dict[str, Any]
            Resource metadata.
        user : User | None
            Optional user for evaluating "user.id".

        Returns
        -------
        bool
            True if condition matches.
        """
        owner_id = resource_data.get("owner_id")
        if expected_value == "user.id":
            if user is None or user.id is None:
                return False
            return owner_id == user.id
        return owner_id == expected_value

    def evaluate_condition(
        self,
        condition: dict[str, Any],
        resource_data: dict[str, Any],
        user: User | None = None,
    ) -> bool:
        """Evaluate condition against resource metadata.

        Supports the following condition keys:
        - author: Exact author name match
        - author_id: Author ID match
        - author_ids: List of author IDs (matches if any in list)
        - tag: Single tag match
        - tags: List of tags (matches if any tag in list)
        - series_id: Series ID match
        - owner_id: Owner ID match (supports "user.id" for current user)

        Multiple conditions are combined with AND logic (all must match).

        Parameters
        ----------
        condition : dict[str, Any]
            Condition dictionary to evaluate.
        resource_data : dict[str, Any]
            Resource metadata to match against.
        user : User | None
            Optional user for evaluating "user.id" in owner_id conditions.

        Returns
        -------
        bool
            True if condition matches, False otherwise.
        """
        # Condition handlers mapping
        handlers: dict[str, Callable[[Any, dict[str, Any], User | None], bool]] = {
            "author": lambda v, d, _u: self._check_author_condition(v, d),
            "author_id": lambda v, d, _u: self._check_author_id_condition(v, d),
            "author_ids": lambda v, d, _u: self._check_author_ids_condition(v, d),
            "tag": lambda v, d, _u: self._check_tag_condition(v, d),
            "tags": lambda v, d, _u: self._check_tags_condition(v, d),
            "series_id": lambda v, d, _u: self._check_series_id_condition(v, d),
            "owner_id": lambda v, d, u: self._check_owner_id_condition(v, d, u),
        }

        # Evaluate each condition key
        for key, expected_value in condition.items():
            handler = handlers.get(key)
            if handler is None:
                # Unknown condition key - fail safe by denying
                return False
            if not handler(expected_value, resource_data, user):
                return False

        # All conditions matched
        return True

    def get_user_permissions(self, user: User) -> list[dict[str, Any]]:
        """Get all permissions with conditions for user.

        Loads all roles assigned to the user and their associated permissions
        with conditions. Optimizes queries to avoid N+1 problems.

        Parameters
        ----------
        user : User
            User to get permissions for.

        Returns
        -------
        list[dict[str, Any]]
            List of permission dictionaries, each containing:
            - permission: Permission object
            - condition: dict[str, Any] | None condition
        """
        if user.id is None:
            return []

        # Load user roles with role-permission relationships
        stmt = (
            select(UserRole, RolePermission, Permission)
            .join(RolePermission, UserRole.role_id == RolePermission.role_id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(UserRole.user_id == user.id)
        )

        results = self._session.exec(stmt).all()

        permissions = []
        for result in results:
            # Unpack result tuple
            _user_role, role_permission, permission = result
            permissions.append({
                "permission": permission,
                "condition": role_permission.condition,
            })

        return permissions

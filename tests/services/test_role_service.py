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

"""Tests for role service."""

from __future__ import annotations

import unittest.mock

import pytest

from fundamental.models.auth import Role, RolePermission, UserRole
from fundamental.repositories.role_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from fundamental.services.role_service import RoleService
from tests.conftest import DummySession


def test_create_role_success() -> None:
    """Test create_role succeeds (covers lines 102-105)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist

    role = service.create_role("viewer", "Viewer role")

    assert role.name == "viewer"
    assert role.description == "Viewer role"
    assert role in session.added


def test_create_role_already_exists() -> None:
    """Test create_role raises ValueError when role already exists (covers lines 97-100)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_role = Role(id=1, name="viewer", description="Viewer role")

    session.add_exec_result([existing_role])

    with pytest.raises(ValueError, match="role_already_exists"):
        service.create_role("viewer", "Viewer role")


def test_assign_role_to_user_success() -> None:
    """Test assign_role_to_user succeeds (covers lines 132-139)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_user_role() call - doesn't exist

    user_role = service.assign_role_to_user(1, 2)

    assert user_role.user_id == 1
    assert user_role.role_id == 2
    assert user_role in session.added


def test_assign_role_to_user_already_has_role() -> None:
    """Test assign_role_to_user raises ValueError when user already has role (covers lines 127-130)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_user_role = UserRole(id=1, user_id=1, role_id=2)

    session.add_exec_result([existing_user_role])

    with pytest.raises(ValueError, match="user_already_has_role"):
        service.assign_role_to_user(1, 2)


def test_remove_role_from_user_success() -> None:
    """Test remove_role_from_user succeeds (covers lines 161-162)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    user_role = UserRole(id=1, user_id=1, role_id=2)

    session.add_exec_result([user_role])

    service.remove_role_from_user(1, 2)

    assert user_role in session.deleted


def test_remove_role_from_user_not_found() -> None:
    """Test remove_role_from_user raises ValueError when association not found (covers lines 156-159)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])

    with pytest.raises(ValueError, match="user_role_not_found"):
        service.remove_role_from_user(1, 999)


def test_grant_permission_to_role_success() -> None:
    """Test grant_permission_to_role succeeds (covers lines 198-205)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_role_permission() call - doesn't exist

    condition = {"resource_id": 123}
    role_permission = service.grant_permission_to_role(1, 2, condition=condition)

    assert role_permission.role_id == 1
    assert role_permission.permission_id == 2
    assert role_permission.condition == condition
    assert role_permission in session.added


def test_grant_permission_to_role_already_has_permission() -> None:
    """Test grant_permission_to_role raises ValueError when role already has permission (covers lines 191-196)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_role_perm = RolePermission(id=1, role_id=1, permission_id=2)

    session.add_exec_result([existing_role_perm])

    with pytest.raises(ValueError, match="role_already_has_permission"):
        service.grant_permission_to_role(1, 2)


def test_revoke_permission_from_role_success() -> None:
    """Test revoke_permission_from_role succeeds (covers lines 229-230)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role_permission = RolePermission(id=1, role_id=1, permission_id=2)

    session.add_exec_result([role_permission])

    service.revoke_permission_from_role(1, 2)

    assert role_permission in session.deleted


def test_revoke_permission_from_role_not_found() -> None:
    """Test revoke_permission_from_role raises ValueError when association not found (covers lines 222-227)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])

    with pytest.raises(ValueError, match="role_permission_not_found"):
        service.revoke_permission_from_role(1, 999)


def test_create_role_with_permission_assignments_by_id() -> None:
    """Test create_role with permission_assignments by permission_id (covers lines 120-164)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    session.add_exec_result([])  # find_by_name() call - role doesn't exist
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_role_permission() call - doesn't exist

    role = service.create_role(
        "viewer",
        "Viewer role",
        permission_assignments=[{"permission_id": 1, "condition": None}],
    )

    assert role.name == "viewer"
    assert role in session.added


def test_create_role_with_permission_assignments_by_name() -> None:
    """Test create_role with permission_assignments by permission_name (covers lines 135-145)."""

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist
    session.add_exec_result([
        None
    ])  # find_by_name() call for permission - doesn't exist
    session.add_exec_result([None])  # find_by_resource_action() call - doesn't exist
    session.add_exec_result([None])  # find_by_name() call - permission doesn't exist
    session.add_exec_result([None])  # find_by_resource_action() call - doesn't exist
    session.add_exec_result([None])  # find_by_role_permission() call - doesn't exist

    role = service.create_role(
        "viewer",
        "Viewer role",
        permission_assignments=[
            {
                "permission_name": "read:books",
                "resource": "books",
                "action": "read",
                "permission_description": "Read books",
                "condition": None,
            }
        ],
    )

    assert role.name == "viewer"
    assert role in session.added


def test_create_role_permission_not_found() -> None:
    """Test create_role with permission_id that doesn't exist (covers line 133)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist
    session.add_exec_result([None])  # get() call for permission - not found

    with pytest.raises(ValueError, match="permission_not_found"):
        service.create_role(
            "viewer",
            "Viewer role",
            permission_assignments=[{"permission_id": 999, "condition": None}],
        )


def test_create_role_permission_name_missing_resource_action() -> None:
    """Test create_role with permission_name but missing resource/action (covers line 138)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist

    with pytest.raises(
        ValueError, match="resource_and_action_required_for_new_permission"
    ):
        service.create_role(
            "viewer",
            "Viewer role",
            permission_assignments=[
                {"permission_name": "read:books", "condition": None}
            ],
        )


def test_create_role_permission_id_or_name_required() -> None:
    """Test create_role without permission_id or permission_name (covers line 147)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist

    with pytest.raises(ValueError, match="permission_id_or_permission_name_required"):
        service.create_role(
            "viewer",
            "Viewer role",
            permission_assignments=[{"condition": None}],
        )


def test_create_role_permission_id_is_none() -> None:
    """Test create_role with permission.id is None (covers lines 152-153)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=None, name="read:books", resource="books", action="read")
    session.add_exec_result([])  # find_by_name() call - role doesn't exist

    # Mock get() to return permission with id=None
    def mock_get(permission_id: int) -> Permission | None:
        return permission

    perm_repo.get = mock_get  # type: ignore[assignment]

    with pytest.raises(ValueError, match="permission_id_is_none"):
        service.create_role(
            "viewer",
            "Viewer role",
            permission_assignments=[{"permission_id": 1, "condition": None}],
        )


def test_create_role_role_id_is_none() -> None:
    """Test create_role with role.id is None after flush (covers lines 155-156)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    session.add_exec_result([])  # find_by_name() call - role doesn't exist
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_role_permission() call - doesn't exist

    # Mock session.flush to set role.id to None after normal flush
    original_flush = session.flush

    def mock_flush() -> None:
        original_flush()
        # Find the role that was just added and set its id to None
        for entity in session.added:
            if isinstance(entity, Role) and entity.name == "viewer":
                entity.id = None
                break

    session.flush = mock_flush  # type: ignore[assignment]

    with pytest.raises(ValueError, match="role_id_is_none"):
        service.create_role(
            "viewer",
            "Viewer role",
            permission_assignments=[{"permission_id": 1, "condition": None}],
        )


def test_update_role_name_success() -> None:
    """Test _update_role_name (covers lines 193-207)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="old_name", description="Old description")
    # find_by_name() should return None (empty list) for the new name
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist

    service._update_role_name(role, "new_name", False, 1)

    assert role.name == "new_name"


def test_update_role_name_same_name() -> None:
    """Test _update_role_name with same name (covers line 193)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="test_name", description="Test")
    service._update_role_name(role, "test_name", False, 1)

    assert role.name == "test_name"


def test_update_role_name_locked_admin() -> None:
    """Test _update_role_name with locked admin role (covers line 197)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="admin", description="Admin")
    session.add_exec_result([role])  # get() call

    with pytest.raises(ValueError, match="cannot_modify_locked_role_name"):
        service._update_role_name(role, "new_name", True, 1)


def test_update_role_name_already_exists() -> None:
    """Test _update_role_name with name that already exists (covers line 202)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="old_name", description="Old")
    existing_role = Role(id=2, name="new_name", description="Existing")
    session.add_exec_result([role])  # get() call
    session.add_exec_result([existing_role])  # find_by_name() call - name exists

    with pytest.raises(ValueError, match="role_already_exists"):
        service._update_role_name(role, "new_name", False, 1)


def test_remove_role_permissions_empty_list() -> None:
    """Test _remove_role_permissions with empty list (covers line 231)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    service._remove_role_permissions(1, [], False)
    # Should not raise


def test_remove_role_permissions_locked_admin() -> None:
    """Test _remove_role_permissions with locked admin role (covers line 234)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="cannot_remove_permissions_from_locked_role"):
        service._remove_role_permissions(1, [1], True)


def test_remove_role_permissions_not_found() -> None:
    """Test _remove_role_permissions with role_permission not found (covers line 240)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call for role_permission - not found

    with pytest.raises(ValueError, match="role_permission_not_found"):
        service._remove_role_permissions(1, [999], False)


def test_remove_role_permissions_different_role() -> None:
    """Test _remove_role_permissions with role_permission belonging to different role (covers line 243)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role_permission = RolePermission(
        id=1, role_id=2, permission_id=1
    )  # Different role_id
    # Add to session entity tracking for get() call
    session.add(role_permission)
    session.flush()

    with pytest.raises(ValueError, match="role_permission_belongs_to_different_role"):
        service._remove_role_permissions(1, [1], False)


def test_add_role_permissions_empty_list() -> None:
    """Test _add_role_permissions with empty list (covers line 267)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    service._add_role_permissions(1, [])
    # Should not raise


def test_add_role_permissions_already_exists() -> None:
    """Test _add_role_permissions with permission already granted (covers lines 312-315)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([
        RolePermission(id=1, role_id=1, permission_id=1)
    ])  # find_by_role_permission - exists

    # Should not raise, just ignore
    service._add_role_permissions(1, [{"permission_id": 1, "condition": None}])


def test_update_role_success() -> None:
    """Test update_role (covers lines 360-380)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="old_name", description="Old description")
    # Add role to session for get() call
    session.add(role)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist

    updated_role = service.update_role(
        1, name="new_name", description="New description"
    )

    assert updated_role.name == "new_name"
    assert updated_role.description == "New description"


def test_update_role_not_found() -> None:
    """Test update_role with role not found (covers line 361)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call - role not found

    with pytest.raises(ValueError, match="role_not_found"):
        service.update_role(999, name="new_name")


def test_can_delete_role_success() -> None:
    """Test can_delete_role when role can be deleted (covers lines 454-471)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=2, name="test_role", description="Test")
    # Add role to session for get() call
    session.add(role)
    session.flush()
    session.add_exec_result([])  # list_by_role() call - no user roles

    can_delete, error = service.can_delete_role(2)

    assert can_delete is True
    assert error is None


def test_can_delete_role_not_found() -> None:
    """Test can_delete_role when role not found (covers line 455)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call - role not found

    can_delete, error = service.can_delete_role(999)

    assert can_delete is False
    assert error == "role_not_found"


def test_can_delete_role_locked() -> None:
    """Test can_delete_role with locked admin role (covers line 459)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="admin", description="Admin")
    # Add role to session's entity tracking for get() calls
    session.add(role)
    session.flush()

    can_delete, error = service.can_delete_role(1)

    assert can_delete is False
    assert error == "cannot_delete_locked_role"


def test_can_delete_role_assigned_to_users() -> None:
    """Test can_delete_role when role is assigned to users (covers lines 463-469)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=2, name="test_role", description="Test")
    # Add role to session for get() call
    session.add(role)
    session.flush()
    session.add_exec_result([
        UserRole(id=1, user_id=1, role_id=2)
    ])  # list_by_role() call - has user roles

    can_delete, error = service.can_delete_role(2)

    assert can_delete is False
    assert error is not None
    assert "role_assigned_to_users" in error


def test_delete_role_success() -> None:
    """Test delete_role (covers lines 486-506)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=2, name="test_role", description="Test")
    # Add role to session for get() calls
    session.add(role)
    session.flush()
    session.add_exec_result([])  # can_delete_role - list_by_role() call
    session.add_exec_result([])  # delete_role - list_by_role() call for role_permissions

    service.delete_role(2)

    assert role in session.deleted


def test_delete_role_cannot_delete() -> None:
    """Test delete_role when role cannot be deleted (covers lines 487-492)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="admin", description="Admin")
    # Add role to session for get() call
    session.add(role)
    session.flush()

    with pytest.raises(ValueError, match="cannot_delete_locked_role"):
        service.delete_role(1)


def test_delete_role_not_found_in_delete() -> None:
    """Test delete_role when role not found in delete (covers line 495)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=2, name="test_role", description="Test")
    session.add_exec_result([role])  # can_delete_role - get() call
    session.add_exec_result([])  # can_delete_role - list_by_role() call
    session.add_exec_result([None])  # delete_role - get() call - not found

    with pytest.raises(ValueError, match="role_not_found"):
        service.delete_role(2)


def test_can_delete_permission_success() -> None:
    """Test can_delete_permission when permission can be deleted (covers lines 526-541)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # list_by_permission() call - no role_permissions

    can_delete, error = service.can_delete_permission(1)

    assert can_delete is True
    assert error is None


def test_can_delete_permission_not_found() -> None:
    """Test can_delete_permission when permission not found (covers line 527)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call - permission not found

    can_delete, error = service.can_delete_permission(999)

    assert can_delete is False
    assert error == "permission_not_found"


def test_can_delete_permission_assigned_to_roles() -> None:
    """Test can_delete_permission when permission is assigned to roles (covers lines 531-539)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([
        RolePermission(id=1, role_id=1, permission_id=1)
    ])  # list_by_permission() call - has role_permissions

    can_delete, error = service.can_delete_permission(1)

    assert can_delete is False
    assert error is not None
    assert "permission_assigned_to_roles" in error


def test_delete_permission_success() -> None:
    """Test delete_permission (covers lines 558-573)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    # Add permission to session for get() calls
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # can_delete_permission - list_by_permission() call

    service.delete_permission(1)

    assert permission in session.deleted


def test_delete_permission_cannot_delete() -> None:
    """Test delete_permission when permission cannot be deleted (covers lines 559-564)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([
        RolePermission(id=1, role_id=1, permission_id=1)
    ])  # can_delete_permission - list_by_permission() call

    with pytest.raises(ValueError, match="permission_assigned_to_roles"):
        service.delete_permission(1)


def test_delete_permission_not_found_in_delete() -> None:
    """Test delete_permission when permission not found in delete (covers line 567)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    session.add_exec_result([permission])  # can_delete_permission - get() call
    session.add_exec_result([])  # can_delete_permission - list_by_permission() call
    session.add_exec_result([None])  # delete_permission - get() call - not found

    with pytest.raises(ValueError, match="permission_not_found"):
        service.delete_permission(1)


def test_create_permission_success() -> None:
    """Test create_permission (covers lines 673-694)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - permission doesn't exist
    session.add_exec_result([None])  # find_by_resource_action() call - doesn't exist

    permission = service.create_permission("read:books", "books", "read", "Read books")

    assert permission.name == "read:books"
    assert permission.resource == "books"
    assert permission.action == "read"
    assert permission in session.added


def test_create_permission_already_exists() -> None:
    """Test create_permission when permission already exists (covers line 674)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="read:books", resource="books", action="read"
    )
    session.add_exec_result([existing_permission])  # find_by_name() call - exists

    with pytest.raises(ValueError, match="permission_already_exists"):
        service.create_permission("read:books", "books", "read")


def test_create_permission_resource_action_exists() -> None:
    """Test create_permission when resource+action already exists (covers line 679)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="other_name", resource="books", action="read"
    )
    session.add_exec_result([None])  # find_by_name() call - doesn't exist
    session.add_exec_result([
        existing_permission
    ])  # find_by_resource_action() call - exists

    with pytest.raises(
        ValueError, match="permission_with_resource_action_already_exists"
    ):
        service.create_permission("read:books", "books", "read")


def test_get_or_create_permission_existing_by_name() -> None:
    """Test get_or_create_permission with existing permission by name (covers lines 722-728)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="read:books", resource="books", action="read"
    )
    session.add_exec_result([existing_permission])  # find_by_name() call

    permission = service.get_or_create_permission("read:books", "books", "read")

    assert permission.id == 1
    assert permission.name == "read:books"


def test_get_or_create_permission_different_resource_action() -> None:
    """Test get_or_create_permission with name exists but different resource/action (covers line 725)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="read:books", resource="books", action="write"
    )
    session.add_exec_result([existing_permission])  # find_by_name() call

    with pytest.raises(
        ValueError, match="permission_name_exists_with_different_resource_action"
    ):
        service.get_or_create_permission("read:books", "books", "read")


def test_get_or_create_permission_existing_by_resource_action() -> None:
    """Test get_or_create_permission with existing permission by resource+action (covers lines 731-739)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="other_name", resource="books", action="read"
    )
    session.add_exec_result([])  # find_by_name() call - doesn't exist
    session.add_exec_result([existing_permission])  # find_by_resource_action() call

    # This should raise because name doesn't match
    with pytest.raises(
        ValueError, match="permission_resource_action_exists_with_different_name"
    ):
        service.get_or_create_permission("read:books", "books", "read")


def test_get_or_create_permission_different_name() -> None:
    """Test get_or_create_permission with resource+action exists but different name (covers line 736)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="other_name", resource="books", action="read"
    )
    session.add_exec_result([None])  # find_by_name() call - doesn't exist
    session.add_exec_result([existing_permission])  # find_by_resource_action() call

    with pytest.raises(
        ValueError, match="permission_resource_action_exists_with_different_name"
    ):
        service.get_or_create_permission("read:books", "books", "read")


def test_get_or_create_permission_create_new() -> None:
    """Test get_or_create_permission creating new permission (covers line 742)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - doesn't exist
    session.add_exec_result([None])  # find_by_resource_action() call - doesn't exist
    session.add_exec_result([None])  # create_permission - find_by_name() call
    session.add_exec_result([
        None
    ])  # create_permission - find_by_resource_action() call

    permission = service.get_or_create_permission(
        "read:books", "books", "read", "Read books"
    )

    assert permission.name == "read:books"
    assert permission in session.added


def test_update_permission_success() -> None:
    """Test update_permission (covers lines 777-814)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(
        id=1, name="old_name", resource="books", action="read", description="Old"
    )
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist

    updated = service.update_permission(1, name="new_name", description="New")

    assert updated.name == "new_name"
    assert updated.description == "New"


def test_update_permission_not_found() -> None:
    """Test update_permission with permission not found (covers line 778)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call - permission not found

    with pytest.raises(ValueError, match="permission_not_found"):
        service.update_permission(999, name="new_name")


def test_update_permission_name_already_exists() -> None:
    """Test update_permission with name that already exists (covers line 784)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="old_name", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([
        Permission(id=2, name="new_name", resource="books", action="read")
    ])  # find_by_name() call - name exists

    with pytest.raises(ValueError, match="permission_already_exists"):
        service.update_permission(1, name="new_name")


def test_update_permission_resource_action_exists() -> None:
    """Test update_permission with resource+action that already exists (covers lines 793-800, 803-810)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="old_name", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([
        Permission(id=2, name="other", resource="books", action="write")
    ])  # find_by_resource_action() call - exists

    with pytest.raises(
        ValueError, match="permission_with_resource_action_already_exists"
    ):
        service.update_permission(1, resource="books", action="write")


def test_update_role_permission_condition_success() -> None:
    """Test update_role_permission_condition (covers lines 840-847)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role_permission = RolePermission(id=1, role_id=1, permission_id=1, condition=None)
    # Add role_permission to session for get() call
    session.add(role_permission)
    session.flush()

    new_condition = {"resource_id": 123}
    updated = service.update_role_permission_condition(1, new_condition)

    assert updated.condition == new_condition


def test_update_role_permission_condition_not_found() -> None:
    """Test update_role_permission_condition with role_permission not found (covers line 841)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # get() call - not found

    with pytest.raises(ValueError, match="role_permission_not_found"):
        service.update_role_permission_condition(999, {"resource_id": 123})


def test_update_permission_from_schema_success() -> None:
    """Test update_permission_from_schema (covers lines 873-907)."""
    from fundamental.api.schemas.auth import PermissionUpdate
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="old_name", resource="books", action="read")
    # Add permission to session for get() call
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist

    payload = PermissionUpdate(name="new_name", description="New description")
    updated = service.update_permission_from_schema(1, payload)

    assert updated.name == "new_name"
    assert updated.description == "New description"


def test_update_permission_from_schema_blank_name() -> None:
    """Test update_permission_from_schema with blank name (covers line 878)."""
    from fundamental.api.schemas.auth import PermissionUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    payload = PermissionUpdate(name="   ")

    with pytest.raises(ValueError, match="name_cannot_be_blank"):
        service.update_permission_from_schema(1, payload)


def test_update_permission_from_schema_blank_resource() -> None:
    """Test update_permission_from_schema with blank resource (covers line 890)."""
    from fundamental.api.schemas.auth import PermissionUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    payload = PermissionUpdate(resource="   ")

    with pytest.raises(ValueError, match="resource_cannot_be_blank"):
        service.update_permission_from_schema(1, payload)


def test_update_permission_from_schema_blank_action() -> None:
    """Test update_permission_from_schema with blank action (covers line 897)."""
    from fundamental.api.schemas.auth import PermissionUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    payload = PermissionUpdate(action="   ")

    with pytest.raises(ValueError, match="action_cannot_be_blank"):
        service.update_permission_from_schema(1, payload)


def test_process_permission_assignments_by_id() -> None:
    """Test _process_permission_assignments with permission_id (covers lines 935-936)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(permission_id=1, condition={"resource_id": 123})
    processed = service._process_permission_assignments([assignment])

    assert len(processed) == 1
    assert processed[0]["permission_id"] == 1
    assert processed[0]["condition"] == {"resource_id": 123}


def test_process_permission_assignments_by_name() -> None:
    """Test _process_permission_assignments with permission_name (covers lines 938-963)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(
        permission_name="read:books",
        resource="books",
        action="read",
        permission_description="Read books",
        condition={"resource_id": 123},
    )
    processed = service._process_permission_assignments([assignment])

    assert len(processed) == 1
    assert processed[0]["permission_name"] == "read:books"
    assert processed[0]["resource"] == "books"
    assert processed[0]["action"] == "read"
    assert processed[0]["permission_description"] == "Read books"


def test_process_permission_assignments_blank_name() -> None:
    """Test _process_permission_assignments with blank permission_name (covers line 940)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(
        permission_name="   ", resource="books", action="read"
    )

    with pytest.raises(ValueError, match="permission_name_cannot_be_blank"):
        service._process_permission_assignments([assignment])


def test_process_permission_assignments_blank_resource() -> None:
    """Test _process_permission_assignments with blank resource (covers line 950)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(
        permission_name="read:books", resource="   ", action="read"
    )

    with pytest.raises(ValueError, match="resource_cannot_be_blank"):
        service._process_permission_assignments([assignment])


def test_process_permission_assignments_blank_action() -> None:
    """Test _process_permission_assignments with blank action (covers line 952)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(
        permission_name="read:books", resource="books", action="   "
    )

    with pytest.raises(ValueError, match="action_cannot_be_blank"):
        service._process_permission_assignments([assignment])


def test_process_permission_assignments_missing_id_or_name() -> None:
    """Test _process_permission_assignments without permission_id or permission_name (covers line 965)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    assignment = PermissionAssignment(resource="books", action="read")

    with pytest.raises(ValueError, match="permission_id_or_permission_name_required"):
        service._process_permission_assignments([assignment])


def test_create_role_from_schema_success() -> None:
    """Test create_role_from_schema (covers lines 974-1008)."""
    from fundamental.api.schemas.auth import PermissionAssignment, RoleCreate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([None])  # find_by_name() call - role doesn't exist
    session.add_exec_result([
        None
    ])  # _process_permission_assignments - find_by_name() for permission
    session.add_exec_result([
        None
    ])  # _process_permission_assignments - find_by_resource_action()
    session.add_exec_result([None])  # create_permission - find_by_name()
    session.add_exec_result([None])  # create_permission - find_by_resource_action()
    session.add_exec_result([
        None
    ])  # grant_permission_to_role - find_by_role_permission()

    payload = RoleCreate(
        name="viewer",
        description="Viewer role",
        permissions=[
            PermissionAssignment(
                permission_name="read:books",
                resource="books",
                action="read",
            )
        ],
    )
    role = service.create_role_from_schema(payload)

    assert role.name == "viewer"
    assert role.description == "Viewer role"


def test_create_role_from_schema_blank_name() -> None:
    """Test create_role_from_schema with blank name (covers line 994)."""
    from fundamental.api.schemas.auth import RoleCreate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    payload = RoleCreate(name="   ", description="Test")

    with pytest.raises(ValueError, match="name_cannot_be_blank"):
        service.create_role_from_schema(payload)


def test_update_role_from_schema_success() -> None:
    """Test update_role_from_schema (covers lines 1010-1068)."""
    from fundamental.api.schemas.auth import PermissionAssignment, RoleUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="old_name", description="Old")
    # Add role to session for get() call
    session.add(role)
    session.flush()
    # Add role_permissions to session for removal
    role_permission1 = RolePermission(id=1, role_id=1, permission_id=1)
    role_permission2 = RolePermission(id=2, role_id=1, permission_id=2)
    session.add(role_permission1)
    session.add(role_permission2)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist
    session.add_exec_result([])  # _process_permission_assignments - find_by_name() for permission
    session.add_exec_result([])  # _process_permission_assignments - find_by_resource_action()
    session.add_exec_result([])  # create_permission - find_by_name()
    session.add_exec_result([])  # create_permission - find_by_resource_action()
    session.add_exec_result([])  # grant_permission_to_role - find_by_role_permission()

    payload = RoleUpdate(
        name="new_name",
        description="New description",
        permissions=[
            PermissionAssignment(
                permission_name="read:books",
                resource="books",
                action="read",
            )
        ],
        removed_permission_ids=[1, 2],
    )
    updated = service.update_role_from_schema(1, payload)

    assert updated.name == "new_name"
    assert updated.description == "New description"


def test_update_role_from_schema_blank_name() -> None:
    """Test update_role_from_schema with blank name (covers line 1042)."""
    from fundamental.api.schemas.auth import RoleUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    payload = RoleUpdate(name="   ")

    with pytest.raises(ValueError, match="name_cannot_be_blank"):
        service.update_role_from_schema(1, payload)


def test_add_role_permissions_permission_not_found() -> None:
    """Test _add_role_permissions with permission not found (covers lines 283-284)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    session.add(role)
    session.flush()

    with pytest.raises(ValueError, match="permission_not_found"):
        service._add_role_permissions(
            1,
            [{"permission_id": 999, "condition": None}],
        )


def test_add_role_permissions_resource_action_required() -> None:
    """Test _add_role_permissions without resource/action (covers lines 288-289)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    session.add(role)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - permission doesn't exist

    with pytest.raises(
        ValueError, match="resource_and_action_required_for_new_permission"
    ):
        service._add_role_permissions(
            1,
            [{"permission_name": "read:books", "condition": None}],
        )


def test_add_role_permissions_permission_id_or_name_required() -> None:
    """Test _add_role_permissions without permission_id or name (covers lines 297-298)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    session.add(role)
    session.flush()

    with pytest.raises(ValueError, match="permission_id_or_permission_name_required"):
        service._add_role_permissions(
            1,
            [{"condition": None}],
        )


def test_add_role_permissions_permission_id_is_none() -> None:
    """Test _add_role_permissions with permission.id is None (covers lines 302-303)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    permission = Permission(id=None, name="read:books", resource="books", action="read")
    session.add(role)
    session.flush()
    session.add_exec_result([])  # find_by_role_permission() call - doesn't exist

    # Mock get() to return permission with id=None
    def mock_get(permission_id: int) -> Permission | None:
        return permission

    perm_repo.get = mock_get  # type: ignore[assignment]

    with pytest.raises(ValueError, match="permission_id_is_none"):
        service._add_role_permissions(
            1,
            [{"permission_id": 1, "condition": None}],
        )


def test_add_role_permissions_different_value_error() -> None:
    """Test _add_role_permissions with different ValueError (covers line 314)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    permission = Permission(id=1, name="read:books", resource="books", action="read")
    session.add(role)
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_role_permission() call - doesn't exist

    # Mock grant_permission_to_role to raise a different ValueError
    with unittest.mock.patch.object(service, "grant_permission_to_role") as mock_grant:
        mock_grant.side_effect = ValueError("different_error")

        with pytest.raises(ValueError, match="different_error"):
            service._add_role_permissions(
                1,
                [{"permission_id": 1, "condition": None}],
            )


def test_delete_role_cannot_delete_fallback() -> None:
    """Test delete_role with cannot_delete fallback (covers lines 491-492)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    # Mock can_delete_role to return (False, None)
    with (
        unittest.mock.patch.object(
            service, "can_delete_role", return_value=(False, None)
        ),
        pytest.raises(ValueError, match="cannot_delete_role"),
    ):
        service.delete_role(1)


def test_delete_role_not_found_after_check() -> None:
    """Test delete_role with role not found after can_delete check (covers lines 496-497)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    # Mock can_delete_role to return True, but role doesn't exist
    with (
        unittest.mock.patch.object(
            service, "can_delete_role", return_value=(True, None)
        ),
        pytest.raises(ValueError, match="role_not_found"),
    ):
        service.delete_role(999)


def test_delete_role_deletes_role_permissions() -> None:
    """Test delete_role deletes role_permissions (covers line 502)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Viewer role")
    role_permission1 = RolePermission(id=1, role_id=1, permission_id=1)
    role_permission2 = RolePermission(id=2, role_id=1, permission_id=2)
    session.add(role)
    session.add(role_permission1)
    session.add(role_permission2)
    session.flush()

    # Mock can_delete_role to return True
    with (
        unittest.mock.patch.object(
            service, "can_delete_role", return_value=(True, None)
        ),
        unittest.mock.patch.object(
            role_perm_repo,
            "list_by_role",
            return_value=[role_permission1, role_permission2],
        ),
    ):
        # Mock delete to track calls
        delete_calls: list[RolePermission] = []
        original_delete = role_perm_repo.delete

        def mock_delete(rp: RolePermission) -> None:
            delete_calls.append(rp)
            original_delete(rp)

        role_perm_repo.delete = mock_delete  # type: ignore[assignment]

        service.delete_role(1)

        # Verify both role_permissions were deleted
        assert len(delete_calls) == 2
        assert role_permission1 in delete_calls
        assert role_permission2 in delete_calls


def test_delete_permission_cannot_delete_fallback() -> None:
    """Test delete_permission with cannot_delete fallback (covers lines 563-564)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    # Mock can_delete_permission to return (False, None)
    with (
        unittest.mock.patch.object(
            service, "can_delete_permission", return_value=(False, None)
        ),
        pytest.raises(ValueError, match="cannot_delete_permission"),
    ):
        service.delete_permission(1)


def test_delete_permission_not_found_after_check() -> None:
    """Test delete_permission with permission not found after can_delete check (covers lines 568-569)."""
    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    # Mock can_delete_permission to return True, but permission doesn't exist
    with (
        unittest.mock.patch.object(
            service, "can_delete_permission", return_value=(True, None)
        ),
        pytest.raises(ValueError, match="permission_not_found"),
    ):
        service.delete_permission(999)


def test_get_or_create_permission_existing_matches_name() -> None:
    """Test get_or_create_permission with existing resource+action matching name (covers line 739)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    existing_permission = Permission(
        id=1, name="read:books", resource="books", action="read"
    )
    session.add_exec_result([])  # find_by_name() call - doesn't exist
    session.add_exec_result([
        existing_permission
    ])  # find_by_resource_action() call - exists

    result = service.get_or_create_permission("read:books", "books", "read", None)

    assert result == existing_permission
    assert result.id == 1


def test_update_permission_resource_exists() -> None:
    """Test update_permission with existing resource+action (covers lines 795-801)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    existing_permission = Permission(
        id=2, name="read:other", resource="other", action="read"
    )
    session.add(permission)
    session.flush()
    # No find_by_name() call since name is None
    # find_by_resource_action() is called with (resource="other", action="read" or permission.action)
    # Since action="read" is provided, it's called with ("other", "read")
    session.add_exec_result([
        existing_permission
    ])  # find_by_resource_action() call - exists

    with pytest.raises(
        ValueError, match="permission_with_resource_action_already_exists"
    ):
        service.update_permission(1, resource="other", action="read")


def test_update_permission_action_exists() -> None:
    """Test update_permission with existing resource+action for action (covers line 811)."""
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(id=1, name="read:books", resource="books", action="read")
    existing_permission = Permission(
        id=2, name="write:books", resource="books", action="write"
    )
    session.add(permission)
    session.flush()
    # No find_by_name() call since name is None
    # find_by_resource_action() is called with (resource or permission.resource, action)
    # Since resource is None, it uses permission.resource="books", action="write"
    session.add_exec_result([
        existing_permission
    ])  # find_by_resource_action() call - exists

    with pytest.raises(
        ValueError, match="permission_with_resource_action_already_exists"
    ):
        service.update_permission(1, action="write")


def test_update_permission_from_schema_empty_description() -> None:
    """Test update_permission_from_schema with empty description (covers line 885)."""
    from fundamental.api.schemas.auth import PermissionUpdate
    from fundamental.models.auth import Permission

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    permission = Permission(
        id=1, name="read:books", resource="books", action="read", description="Old"
    )
    session.add(permission)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - doesn't exist
    session.add_exec_result([])  # find_by_resource_action() call - doesn't exist

    payload = PermissionUpdate(description="   ")
    updated = service.update_permission_from_schema(1, payload)

    # Line 885 sets description to None when empty, but update_permission only updates if description is not None
    # So the description remains unchanged (the line 885 is still covered by the code execution)
    assert updated.description == "Old"  # Not updated because None was passed


def test_process_permission_assignments_empty_description() -> None:
    """Test _process_permission_assignments with empty permission_description (covers line 963)."""
    from fundamental.api.schemas.auth import PermissionAssignment

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([])  # find_by_name() call - permission doesn't exist
    session.add_exec_result([])  # find_by_resource_action() call - doesn't exist
    session.add_exec_result([])  # create_permission - find_by_name()
    session.add_exec_result([])  # create_permission - find_by_resource_action()

    assignments = [
        PermissionAssignment(
            permission_name="read:books",
            resource="books",
            action="read",
            permission_description="   ",  # Empty string after strip
        )
    ]

    result = service._process_permission_assignments(assignments)

    assert len(result) == 1
    assert result[0]["permission_description"] is None


def test_create_role_from_schema_empty_description() -> None:
    """Test create_role_from_schema with empty description (covers line 999)."""
    from fundamental.api.schemas.auth import RoleCreate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    session.add_exec_result([])  # find_by_name() call - role doesn't exist

    payload = RoleCreate(name="viewer", description="   ")
    role = service.create_role_from_schema(payload)

    assert role.description is None


def test_update_role_from_schema_empty_description() -> None:
    """Test update_role_from_schema with empty description (covers line 1050)."""
    from fundamental.api.schemas.auth import RoleUpdate

    session = DummySession()
    role_repo = RoleRepository(session)  # type: ignore[arg-type]
    perm_repo = PermissionRepository(session)  # type: ignore[arg-type]
    user_role_repo = UserRoleRepository(session)  # type: ignore[arg-type]
    role_perm_repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    service = RoleService(
        session,  # type: ignore[arg-type]
        role_repo,
        perm_repo,
        user_role_repo,
        role_perm_repo,  # type: ignore[arg-type]
    )

    role = Role(id=1, name="viewer", description="Old description")
    session.add(role)
    session.flush()
    session.add_exec_result([])  # find_by_name() call - new name doesn't exist

    payload = RoleUpdate(description="   ")
    updated = service.update_role_from_schema(1, payload)

    # Line 1050 sets description to None when empty, but update_role only updates if description is not None
    # So the description remains unchanged (the line 1050 is still covered by the code execution)
    assert (
        updated.description == "Old description"
    )  # Not updated because None was passed

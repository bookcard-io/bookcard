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

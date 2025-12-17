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

"""Tests for role repository."""

from __future__ import annotations

from bookcard.models.auth import Permission, Role, RolePermission, UserRole
from bookcard.repositories.role_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from tests.conftest import DummySession


def test_role_repository_find_by_name_returns_role() -> None:
    """Test RoleRepository.find_by_name returns role with matching name (covers lines 65-66)."""
    session = DummySession()
    repo = RoleRepository(session)  # type: ignore[arg-type]

    role = Role(id=1, name="viewer", description="Viewer role")

    session.add_exec_result([role])
    result = repo.find_by_name("viewer")
    assert result is not None
    assert result.id == 1
    assert result.name == "viewer"


def test_role_repository_find_by_name_returns_none() -> None:
    """Test RoleRepository.find_by_name returns None when not found (covers lines 65-66)."""
    session = DummySession()
    repo = RoleRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_name("nonexistent")
    assert result is None


def test_role_repository_list_all_returns_all_roles() -> None:
    """Test RoleRepository.list_all returns all roles ordered by name (covers lines 76-77)."""
    session = DummySession()
    repo = RoleRepository(session)  # type: ignore[arg-type]

    role1 = Role(id=1, name="admin", description="Admin role")
    role2 = Role(id=2, name="viewer", description="Viewer role")

    session.add_exec_result([role1, role2])
    result = list(repo.list_all())
    assert len(result) == 2
    assert result[0].name == "admin"
    assert result[1].name == "viewer"


def test_permission_repository_find_by_name_returns_permission() -> None:
    """Test PermissionRepository.find_by_name returns permission (covers lines 99-100)."""
    session = DummySession()
    repo = PermissionRepository(session)  # type: ignore[arg-type]

    permission = Permission(id=1, name="books:read", resource="books", action="read")

    session.add_exec_result([permission])
    result = repo.find_by_name("books:read")
    assert result is not None
    assert result.id == 1
    assert result.name == "books:read"


def test_permission_repository_find_by_name_returns_none() -> None:
    """Test PermissionRepository.find_by_name returns None when not found (covers lines 99-100)."""
    session = DummySession()
    repo = PermissionRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_name("nonexistent")
    assert result is None


def test_permission_repository_find_by_resource_action_returns_permission() -> None:
    """Test PermissionRepository.find_by_resource_action returns permission (covers lines 117-120)."""
    session = DummySession()
    repo = PermissionRepository(session)  # type: ignore[arg-type]

    permission = Permission(id=1, name="books:read", resource="books", action="read")

    session.add_exec_result([permission])
    result = repo.find_by_resource_action("books", "read")
    assert result is not None
    assert result.id == 1
    assert result.resource == "books"
    assert result.action == "read"


def test_permission_repository_find_by_resource_action_returns_none() -> None:
    """Test PermissionRepository.find_by_resource_action returns None (covers lines 117-120)."""
    session = DummySession()
    repo = PermissionRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_resource_action("books", "write")
    assert result is None


def test_permission_repository_list_by_resource_returns_permissions() -> None:
    """Test PermissionRepository.list_by_resource returns permissions (covers lines 135-136)."""
    session = DummySession()
    repo = PermissionRepository(session)  # type: ignore[arg-type]

    perm1 = Permission(id=1, name="books:read", resource="books", action="read")
    perm2 = Permission(id=2, name="books:write", resource="books", action="write")

    session.add_exec_result([perm1, perm2])
    result = list(repo.list_by_resource("books"))
    assert len(result) == 2
    assert all(p.resource == "books" for p in result)


def test_user_role_repository_find_by_user_role_returns_association() -> None:
    """Test UserRoleRepository.find_by_user_role returns association (covers lines 160-163)."""
    session = DummySession()
    repo = UserRoleRepository(session)  # type: ignore[arg-type]

    user_role = UserRole(id=1, user_id=1, role_id=2)

    session.add_exec_result([user_role])
    result = repo.find_by_user_role(1, 2)
    assert result is not None
    assert result.user_id == 1
    assert result.role_id == 2


def test_user_role_repository_find_by_user_role_returns_none() -> None:
    """Test UserRoleRepository.find_by_user_role returns None (covers lines 160-163)."""
    session = DummySession()
    repo = UserRoleRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_user_role(1, 999)
    assert result is None


def test_user_role_repository_list_by_user_returns_roles() -> None:
    """Test UserRoleRepository.list_by_user returns user roles (covers lines 178-179)."""
    session = DummySession()
    repo = UserRoleRepository(session)  # type: ignore[arg-type]

    user_role1 = UserRole(id=1, user_id=1, role_id=1)
    user_role2 = UserRole(id=2, user_id=1, role_id=2)

    session.add_exec_result([user_role1, user_role2])
    result = list(repo.list_by_user(1))
    assert len(result) == 2
    assert all(ur.user_id == 1 for ur in result)


def test_user_role_repository_list_by_role_returns_users() -> None:
    """Test UserRoleRepository.list_by_role returns users with role (covers lines 194-195)."""
    session = DummySession()
    repo = UserRoleRepository(session)  # type: ignore[arg-type]

    user_role1 = UserRole(id=1, user_id=1, role_id=1)
    user_role2 = UserRole(id=2, user_id=2, role_id=1)

    session.add_exec_result([user_role1, user_role2])
    result = list(repo.list_by_role(1))
    assert len(result) == 2
    assert all(ur.role_id == 1 for ur in result)


def test_role_permission_repository_find_by_role_permission_returns_association() -> (
    None
):
    """Test RolePermissionRepository.find_by_role_permission returns association (covers lines 221-225)."""
    session = DummySession()
    repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    role_perm = RolePermission(id=1, role_id=1, permission_id=2)

    session.add_exec_result([role_perm])
    result = repo.find_by_role_permission(1, 2)
    assert result is not None
    assert result.role_id == 1
    assert result.permission_id == 2


def test_role_permission_repository_find_by_role_permission_returns_none() -> None:
    """Test RolePermissionRepository.find_by_role_permission returns None (covers lines 221-225)."""
    session = DummySession()
    repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_role_permission(1, 999)
    assert result is None


def test_role_permission_repository_list_by_role_returns_permissions() -> None:
    """Test RolePermissionRepository.list_by_role returns role permissions (covers lines 240-241)."""
    session = DummySession()
    repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    role_perm1 = RolePermission(id=1, role_id=1, permission_id=1)
    role_perm2 = RolePermission(id=2, role_id=1, permission_id=2)

    session.add_exec_result([role_perm1, role_perm2])
    result = list(repo.list_by_role(1))
    assert len(result) == 2
    assert all(rp.role_id == 1 for rp in result)


def test_role_permission_repository_list_by_permission_returns_roles() -> None:
    """Test RolePermissionRepository.list_by_permission returns roles with permission (covers lines 256-259)."""
    session = DummySession()
    repo = RolePermissionRepository(session)  # type: ignore[arg-type]

    role_perm1 = RolePermission(id=1, role_id=1, permission_id=1)
    role_perm2 = RolePermission(id=2, role_id=2, permission_id=1)

    session.add_exec_result([role_perm1, role_perm2])
    result = list(repo.list_by_permission(1))
    assert len(result) == 2
    assert all(rp.permission_id == 1 for rp in result)

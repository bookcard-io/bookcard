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

"""Tests for PermissionService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from fastapi import HTTPException, status

from bookcard.models.auth import Permission, RolePermission, User, UserRole
from bookcard.services.permission_service import PermissionService

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def permission_service(session: DummySession) -> PermissionService:
    """Create PermissionService instance."""
    return PermissionService(session)  # type: ignore[arg-type]


@pytest.fixture
def user() -> User:
    """Create a test user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_admin=False,
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin user."""
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def permission() -> Permission:
    """Create a test permission."""
    return Permission(
        id=1,
        name="books:read",
        resource="books",
        action="read",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def role_permission(permission: Permission) -> RolePermission:
    """Create a test role permission."""
    return RolePermission(
        id=1,
        role_id=1,
        permission_id=1,
        condition=None,
        assigned_at=datetime.now(UTC),
    )


@pytest.fixture
def user_role() -> UserRole:
    """Create a test user role."""
    return UserRole(
        id=1,
        user_id=1,
        role_id=1,
        assigned_at=datetime.now(UTC),
    )


class TestPermissionServiceInit:
    """Test PermissionService initialization."""

    def test_init_stores_session(self, session: DummySession) -> None:
        """Test __init__ stores session."""
        service = PermissionService(session)  # type: ignore[arg-type]
        assert service._session == session


class TestNormalizeList:
    """Test _normalize_list method."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, []),
            ([], []),
            ("", []),
            (0, []),
            (False, []),
            ([1, 2, 3], [1, 2, 3]),
            ("single", ["single"]),
            (123, [123]),
        ],
    )
    def test_normalize_list(
        self,
        permission_service: PermissionService,
        value: object,
        expected: list[object],
    ) -> None:
        """Test _normalize_list normalizes various inputs."""
        result = permission_service._normalize_list(value)
        assert result == expected


class TestHasPermission:
    """Test has_permission method."""

    def test_has_permission_user_id_none(
        self, permission_service: PermissionService, user: User
    ) -> None:
        """Test has_permission returns False when user.id is None."""
        user.id = None
        assert permission_service.has_permission(user, "books", "read") is False

    def test_has_permission_admin_user(
        self, permission_service: PermissionService, admin_user: User
    ) -> None:
        """Test has_permission returns True for admin users."""
        assert permission_service.has_permission(admin_user, "books", "read") is True
        assert permission_service.has_permission(admin_user, "books", "write") is True
        assert permission_service.has_permission(admin_user, "any", "action") is True

    def test_has_permission_no_matching_permission(
        self,
        permission_service: PermissionService,
        user: User,
        session: DummySession,
    ) -> None:
        """Test has_permission returns False when no matching permission."""
        session.set_exec_result([])
        assert permission_service.has_permission(user, "books", "read") is False

    def test_has_permission_global_permission(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns True for global permission (no condition)."""
        session.set_exec_result([(user_role, role_permission, permission)])
        assert permission_service.has_permission(user, "books", "read") is True

    def test_has_permission_wrong_resource(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns False for wrong resource."""
        session.set_exec_result([(user_role, role_permission, permission)])
        assert permission_service.has_permission(user, "shelves", "read") is False

    def test_has_permission_wrong_action(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns False for wrong action."""
        session.set_exec_result([(user_role, role_permission, permission)])
        assert permission_service.has_permission(user, "books", "write") is False

    def test_has_permission_with_condition_matches(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns True when condition matches."""
        role_permission.condition = {"author_id": 123}
        session.set_exec_result([(user_role, role_permission, permission)])
        context = {"author_ids": [123, 456]}
        assert permission_service.has_permission(user, "books", "read", context) is True

    def test_has_permission_with_condition_no_match(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns False when condition doesn't match."""
        role_permission.condition = {"author_id": 123}
        session.set_exec_result([(user_role, role_permission, permission)])
        context = {"author_ids": [456, 789]}
        assert (
            permission_service.has_permission(user, "books", "read", context) is False
        )

    def test_has_permission_with_condition_no_context(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test has_permission returns False when condition exists but no context."""
        role_permission.condition = {"author_id": 123}
        session.set_exec_result([(user_role, role_permission, permission)])
        assert permission_service.has_permission(user, "books", "read") is False


class TestCheckPermission:
    """Test check_permission method."""

    def test_check_permission_allowed(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test check_permission doesn't raise when permission granted."""
        session.set_exec_result([(user_role, role_permission, permission)])
        # Should not raise
        permission_service.check_permission(user, "books", "read")

    def test_check_permission_denied(
        self, permission_service: PermissionService, user: User, session: DummySession
    ) -> None:
        """Test check_permission raises HTTPException when permission denied."""
        session.set_exec_result([])
        with pytest.raises(HTTPException) as exc_info:
            permission_service.check_permission(user, "books", "read")
        exception = exc_info.value
        assert isinstance(exception, HTTPException)
        assert exception.status_code == status.HTTP_403_FORBIDDEN
        assert "permission_denied: books:read" in exception.detail


class TestConditionCheckers:
    """Test condition checker methods."""

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            ("Author Name", {"authors": ["Author Name", "Other"]}, True),
            ("Author Name", {"authors": ["Other Author"]}, False),
            ("Author Name", {"authors": []}, False),
            ("Author Name", {}, False),
        ],
    )
    def test_check_author_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_author_condition."""
        result = permission_service._check_author_condition(
            expected_value, resource_data
        )
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            (123, {"author_ids": [123, 456]}, True),
            (123, {"author_ids": [456, 789]}, False),
            (123, {"author_ids": []}, False),
            (123, {}, False),
        ],
    )
    def test_check_author_id_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_author_id_condition."""
        result = permission_service._check_author_id_condition(
            expected_value, resource_data
        )
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            ([123, 456], {"author_ids": [123, 456, 789]}, True),
            ([123, 999], {"author_ids": [123, 456]}, True),
            ([999, 888], {"author_ids": [123, 456]}, False),
            ("not-list", {"author_ids": [123]}, False),
            ([], {"author_ids": [123]}, False),
        ],
    )
    def test_check_author_ids_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_author_ids_condition."""
        result = permission_service._check_author_ids_condition(
            expected_value, resource_data
        )
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            ("tag1", {"tags": ["tag1", "tag2"]}, True),
            ("tag1", {"tags": ["tag2", "tag3"]}, False),
            ("tag1", {"tags": []}, False),
            ("tag1", {}, False),
        ],
    )
    def test_check_tag_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_tag_condition."""
        result = permission_service._check_tag_condition(expected_value, resource_data)
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            (["tag1", "tag2"], {"tags": ["tag1", "tag2", "tag3"]}, True),
            (["tag1", "tag4"], {"tags": ["tag1", "tag2"]}, True),
            (["tag4", "tag5"], {"tags": ["tag1", "tag2"]}, False),
            ("not-list", {"tags": ["tag1"]}, False),
            ([], {"tags": ["tag1"]}, False),
        ],
    )
    def test_check_tags_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_tags_condition."""
        result = permission_service._check_tags_condition(expected_value, resource_data)
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "expected"),
        [
            (123, {"series_id": 123}, True),
            (123, {"series_id": 456}, False),
            (123, {}, False),
            (None, {"series_id": None}, True),
        ],
    )
    def test_check_series_id_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        expected: bool,
    ) -> None:
        """Test _check_series_id_condition."""
        result = permission_service._check_series_id_condition(
            expected_value, resource_data
        )
        assert result == expected

    @pytest.mark.parametrize(
        ("expected_value", "resource_data", "user", "expected"),
        [
            (123, {"owner_id": 123}, None, True),
            (123, {"owner_id": 456}, None, False),
            (
                "user.id",
                {"owner_id": 1},
                User(id=1, username="u", email="e", password_hash="h"),
                True,
            ),
            (
                "user.id",
                {"owner_id": 1},
                User(id=2, username="u", email="e", password_hash="h"),
                False,
            ),
            (
                "user.id",
                {"owner_id": 1},
                User(id=None, username="u", email="e", password_hash="h"),
                False,
            ),
            ("user.id", {"owner_id": 1}, None, False),
        ],
    )
    def test_check_owner_id_condition(
        self,
        permission_service: PermissionService,
        expected_value: object,
        resource_data: dict[str, object],
        user: User | None,
        expected: bool,
    ) -> None:
        """Test _check_owner_id_condition."""
        result = permission_service._check_owner_id_condition(
            expected_value, resource_data, user
        )
        assert result == expected


class TestEvaluateCondition:
    """Test evaluate_condition method."""

    def test_evaluate_condition_all_match(
        self,
        permission_service: PermissionService,
        user: User,
    ) -> None:
        """Test evaluate_condition returns True when all conditions match."""
        condition = {
            "author_id": 123,
            "tag": "fiction",
            "series_id": 456,
        }
        resource_data = {
            "author_ids": [123],
            "tags": ["fiction"],
            "series_id": 456,
        }
        assert (
            permission_service.evaluate_condition(condition, resource_data, user)
            is True
        )

    def test_evaluate_condition_one_fails(
        self,
        permission_service: PermissionService,
        user: User,
    ) -> None:
        """Test evaluate_condition returns False when one condition fails."""
        condition = {
            "author_id": 123,
            "tag": "fiction",
        }
        resource_data = {
            "author_ids": [123],
            "tags": ["non-fiction"],
        }
        assert (
            permission_service.evaluate_condition(condition, resource_data, user)
            is False
        )

    def test_evaluate_condition_unknown_key(
        self,
        permission_service: PermissionService,
        user: User,
    ) -> None:
        """Test evaluate_condition returns False for unknown condition key."""
        condition = {"unknown_key": "value"}
        resource_data = {}
        assert (
            permission_service.evaluate_condition(condition, resource_data, user)
            is False
        )

    def test_evaluate_condition_empty(
        self,
        permission_service: PermissionService,
        user: User,
    ) -> None:
        """Test evaluate_condition returns True for empty condition."""
        condition = {}
        resource_data = {}
        assert (
            permission_service.evaluate_condition(condition, resource_data, user)
            is True
        )

    @pytest.mark.parametrize(
        ("condition", "resource_data", "user", "expected"),
        [
            ({"author": "Author Name"}, {"authors": ["Author Name"]}, None, True),
            ({"author_ids": [1, 2]}, {"author_ids": [1, 3]}, None, True),
            ({"tags": ["tag1"]}, {"tags": ["tag1", "tag2"]}, None, True),
            (
                {"owner_id": "user.id"},
                {"owner_id": 1},
                User(id=1, username="u", email="e", password_hash="h"),
                True,
            ),
        ],
    )
    def test_evaluate_condition_various_types(
        self,
        permission_service: PermissionService,
        condition: dict[str, object],
        resource_data: dict[str, object],
        user: User | None,
        expected: bool,
    ) -> None:
        """Test evaluate_condition with various condition types."""
        result = permission_service.evaluate_condition(condition, resource_data, user)
        assert result == expected


class TestGetUserPermissions:
    """Test get_user_permissions method."""

    def test_get_user_permissions_user_id_none(
        self, permission_service: PermissionService, user: User
    ) -> None:
        """Test get_user_permissions returns empty list when user.id is None."""
        user.id = None
        result = permission_service.get_user_permissions(user)
        assert result == []

    def test_get_user_permissions_no_roles(
        self,
        permission_service: PermissionService,
        user: User,
        session: DummySession,
    ) -> None:
        """Test get_user_permissions returns empty list when user has no roles."""
        session.set_exec_result([])
        result = permission_service.get_user_permissions(user)
        assert result == []

    def test_get_user_permissions_single_permission(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test get_user_permissions returns single permission."""
        session.set_exec_result([(user_role, role_permission, permission)])
        result = permission_service.get_user_permissions(user)
        assert len(result) == 1
        assert result[0]["permission"] == permission
        assert result[0]["condition"] is None

    def test_get_user_permissions_with_condition(
        self,
        permission_service: PermissionService,
        user: User,
        permission: Permission,
        role_permission: RolePermission,
        user_role: UserRole,
        session: DummySession,
    ) -> None:
        """Test get_user_permissions includes condition."""
        role_permission.condition = {"author_id": 123}
        session.set_exec_result([(user_role, role_permission, permission)])
        result = permission_service.get_user_permissions(user)
        assert len(result) == 1
        assert result[0]["condition"] == {"author_id": 123}

    def test_get_user_permissions_multiple(
        self,
        permission_service: PermissionService,
        user: User,
        session: DummySession,
    ) -> None:
        """Test get_user_permissions returns multiple permissions."""
        perm1 = Permission(
            id=1,
            name="books:read",
            resource="books",
            action="read",
            created_at=datetime.now(UTC),
        )
        perm2 = Permission(
            id=2,
            name="books:write",
            resource="books",
            action="write",
            created_at=datetime.now(UTC),
        )
        role_perm1 = RolePermission(
            id=1,
            role_id=1,
            permission_id=1,
            condition=None,
            assigned_at=datetime.now(UTC),
        )
        role_perm2 = RolePermission(
            id=2,
            role_id=1,
            permission_id=2,
            condition={"tag": "fiction"},
            assigned_at=datetime.now(UTC),
        )
        user_role = UserRole(id=1, user_id=1, role_id=1, assigned_at=datetime.now(UTC))

        session.set_exec_result([
            (user_role, role_perm1, perm1),
            (user_role, role_perm2, perm2),
        ])
        result = permission_service.get_user_permissions(user)
        assert len(result) == 2
        assert result[0]["permission"] == perm1
        assert result[1]["permission"] == perm2
        assert result[1]["condition"] == {"tag": "fiction"}

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

"""Tests for admin routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import bookcard.api.routes.admin as admin
from bookcard.models.auth import EBookFormat, EReaderDevice, Role, User
from bookcard.models.config import Library
from tests.conftest import DummySession


def test_create_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_user succeeds with valid payload."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        is_admin=False,
        is_active=True,
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_admin=False,
        is_active=True,
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.create_admin_user.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        assert result.username == "testuser"
        mock_service.create_admin_user.assert_called_once()


def test_create_user_username_exists() -> None:
    """Test create_user raises 409 when username already exists."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="existing",
        email="test@example.com",
        password="password123",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.create_admin_user.side_effect = ValueError(
            "username_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_user(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "username_already_exists"


def test_create_user_email_exists() -> None:
    """Test create_user raises 409 when email already exists."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="newuser",
        email="existing@example.com",
        password="password123",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.create_admin_user.side_effect = ValueError("email_already_exists")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_user(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "email_already_exists"


def test_create_user_with_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_user assigns roles when role_ids provided."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        role_ids=[1, 2],
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.create_admin_user.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Verify create_admin_user was called with role_ids
        call_args = mock_service.create_admin_user.call_args
        assert call_args is not None
        assert call_args.kwargs.get("role_ids") == [1, 2]


def test_create_user_with_device(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_user creates default device when default_device_email provided."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        default_device_email="device@example.com",
        default_device_name="My Kindle",
        default_device_type="kindle",
        default_device_format="epub",
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_device_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_device_service = MagicMock()
        mock_device_service.create_device.return_value = MagicMock()
        mock_device_service_class.return_value = mock_device_service

        mock_service = MagicMock()
        mock_service.create_admin_user.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Verify create_admin_user was called with device parameters
        call_args = mock_service.create_admin_user.call_args
        assert call_args is not None
        assert call_args.kwargs.get("default_device_email") == "device@example.com"


def test_create_user_with_roles_suppresses_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_user suppresses ValueError when assigning roles (covers suppress block lines 137-139)."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        role_ids=[1, 2],
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo_class.return_value = mock_user_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_role_service = MagicMock()
        # First role assignment succeeds, second raises ValueError (should be suppressed)
        mock_role_service.assign_role_to_user.side_effect = [
            None,
            ValueError("role_not_found"),
        ]
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.create_admin_user.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Verify create_admin_user was called (role assignment happens inside service)
        mock_service.create_admin_user.assert_called_once()


def test_create_user_with_device_suppresses_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_user suppresses ValueError when creating device (covers suppress block lines 147-159)."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
        default_device_email="existing@example.com",
        default_device_format="invalid_format",  # Invalid format should be suppressed
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_device_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo_class.return_value = mock_user_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_device_service = MagicMock()
        # Device creation raises ValueError (should be suppressed)
        mock_device_service.create_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_device_service_class.return_value = mock_device_service

        mock_service = MagicMock()
        mock_service.create_admin_user.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Verify create_admin_user was called (device creation happens inside service)
        mock_service.create_admin_user.assert_called_once()


def test_create_user_user_not_found_after_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_user raises 404 when user not found after creation."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.create_admin_user.side_effect = ValueError("user_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_user(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_list_users(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_users returns paginated users."""
    session = DummySession()
    user1 = User(
        id=1,
        username="user1",
        email="user1@example.com",
        password_hash="hash",
    )
    user1.ereader_devices = []
    user1.roles = []

    user2 = User(
        id=2,
        username="user2",
        email="user2@example.com",
        password_hash="hash",
    )
    user2.ereader_devices = []
    user2.roles = []

    with patch("bookcard.api.routes.admin.UserService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.list_users_with_relationships.return_value = [user1, user2]
        mock_service_class.return_value = mock_service

        result = admin.list_users(session, limit=10, offset=0)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


def test_get_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_user returns user when found."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with patch("bookcard.api.routes.admin.UserService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.get_user(session, user_id=1)
        assert result.id == 1
        assert result.username == "testuser"


def test_get_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_user raises 404 when user not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.UserService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.get_user(session, user_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_update_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user succeeds with valid payload."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="newname", email="newemail@example.com")

    user = User(
        id=1,
        username="newname",
        email="newemail@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        assert result.username == "newname"


def test_update_user_not_found() -> None:
    """Test update_user raises 404 when user not found."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="newname")

    with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.update_user(session, user_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_update_user_username_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user raises 409 when username already exists."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="existing")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.side_effect = ValueError("username_already_exists")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "username_already_exists"


def test_update_user_admin_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user updates admin status."""
    session = DummySession()
    payload = admin.AdminUserUpdate(is_admin=True)

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_admin=True,
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        mock_service.update_user.assert_called_once()
        # Verify is_admin was passed to update_user
        call_args = mock_service.update_user.call_args
        assert call_args[0][0] == 1  # user_id
        assert call_args[1]["is_admin"] is True


def test_update_user_active_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user updates active status."""
    session = DummySession()
    payload = admin.AdminUserUpdate(is_active=False)

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_active=False,
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        mock_service.update_user.assert_called_once()
        # Verify is_active was passed to update_user
        call_args = mock_service.update_user.call_args
        assert call_args[0][0] == 1  # user_id
        assert call_args[1]["is_active"] is False


def test_update_user_not_found_after_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user raises 404 when user not found after update."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="newname")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_update_user_profile_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user re-raises ValueError for unexpected profile update errors (covers line 295)."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="newname")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        # Raise ValueError with unexpected message (not username_already_exists or email_already_exists)
        mock_service.update_user.side_effect = ValueError("unexpected_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="unexpected_error"):
            admin.update_user(session, user_id=1, payload=payload)


@pytest.mark.parametrize(
    ("payload", "method_name", "line_cover"),
    [
        (admin.AdminUserUpdate(is_admin=True), "update_admin_status", "301-302"),
        (admin.AdminUserUpdate(is_active=False), "update_active_status", "308-309"),
    ],
)
def test_update_user_status_value_error(
    monkeypatch: pytest.MonkeyPatch,
    payload: admin.AdminUserUpdate,
    method_name: str,
    line_cover: str,
) -> None:
    """Test update_user raises 404 when status update methods raise ValueError (covers lines {line_cover})."""
    session = DummySession()

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        # update_user now handles all updates internally, so we mock it to raise ValueError
        mock_service.update_user.side_effect = ValueError("user_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_assign_role_to_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test assign_role_to_user succeeds."""
    session = DummySession()
    payload = admin.UserRoleAssign(role_id=1)

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.assign_role_to_user(session, user_id=1, payload=payload)
        assert result.id == 1
        mock_role_service.assign_role_to_user.assert_called_once_with(1, 1)


def test_assign_role_to_user_already_has_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test assign_role_to_user raises 409 when user already has role."""
    session = DummySession()
    payload = admin.UserRoleAssign(role_id=1)

    with patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class:
        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.side_effect = ValueError(
            "user_already_has_role"
        )
        mock_role_service_class.return_value = mock_role_service

        with pytest.raises(HTTPException) as exc_info:
            admin.assign_role_to_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "user_already_has_role"


def test_assign_role_to_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test assign_role_to_user raises 404 when user or role not found."""
    session = DummySession()
    payload = admin.UserRoleAssign(role_id=1)

    with patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class:
        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.side_effect = ValueError("user_not_found")
        mock_role_service_class.return_value = mock_role_service

        with pytest.raises(HTTPException) as exc_info:
            admin.assign_role_to_user(session, user_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_or_role_not_found"


def test_assign_role_to_user_not_found_after_assign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test assign_role_to_user raises 404 when user not found after assignment."""
    session = DummySession()
    payload = admin.UserRoleAssign(role_id=1)

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.assign_role_to_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_remove_role_from_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test remove_role_from_user succeeds."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_role_service = MagicMock()
        mock_role_service.remove_role_from_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.remove_role_from_user(session, user_id=1, role_id=1)
        assert result.id == 1


def test_remove_role_from_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test remove_role_from_user raises 404 when user or role not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class:
        mock_role_service = MagicMock()
        mock_role_service.remove_role_from_user.side_effect = ValueError(
            "user_role_not_found"
        )
        mock_role_service_class.return_value = mock_role_service

        with pytest.raises(HTTPException) as exc_info:
            admin.remove_role_from_user(session, user_id=999, role_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_role_not_found"


def test_remove_role_from_user_not_found_after_remove(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test remove_role_from_user raises 404 when user not found after removal."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_role_service = MagicMock()
        mock_role_service.remove_role_from_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.remove_role_from_user(session, user_id=1, role_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_create_role_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_role succeeds."""
    session = DummySession()
    payload = admin.RoleCreate(name="viewer", description="Viewer role")

    role = Role(id=1, name="viewer", description="Viewer role")
    role.permissions = []

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role_from_schema.return_value = role
        mock_service_class.return_value = mock_service

        result = admin.create_role(session, payload)
        assert result.id == 1
        assert result.name == "viewer"


def test_create_role_already_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_role raises 409 when role already exists."""
    session = DummySession()
    payload = admin.RoleCreate(name="existing", description="Existing role")

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role_from_schema.side_effect = ValueError(
            "role_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_role(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "role_already_exists"


@pytest.mark.parametrize(
    (
        "route_func",
        "payload",
        "service_class_path",
        "service_method",
        "line_cover",
        "call_kwargs",
    ),
    [
        (
            admin.create_role,
            admin.RoleCreate(name="testrole", description="Test role"),
            "bookcard.api.routes.admin.RoleService",
            "create_role_from_schema",
            "488",
            {"payload": admin.RoleCreate(name="testrole", description="Test role")},
        ),
        (
            admin.create_device,
            admin.EReaderDeviceCreate(email="device@example.com"),
            "bookcard.api.routes.admin.EReaderService",
            "create_device",
            "768",
            {
                "user_id": 1,
                "payload": admin.EReaderDeviceCreate(email="device@example.com"),
            },
        ),
        (
            admin.update_device,
            admin.EReaderDeviceUpdate(email="device@example.com"),
            "bookcard.api.routes.admin.EReaderService",
            "update_device",
            "860",
            {
                "device_id": 1,
                "payload": admin.EReaderDeviceUpdate(email="device@example.com"),
            },
        ),
        (
            admin.create_library,
            admin.LibraryCreate(
                name="Test Library",
                calibre_db_path="/path/to/library",
                calibre_db_file="metadata.db",
            ),
            "bookcard.api.routes.admin.LibraryService",
            "create_library",
            "1003",
            {
                "payload": admin.LibraryCreate(
                    name="Test Library",
                    calibre_db_path="/path/to/library",
                    calibre_db_file="metadata.db",
                )
            },
        ),
        (
            admin.update_library,
            admin.LibraryUpdate(name="Updated Library"),
            "bookcard.api.routes.admin.LibraryService",
            "update_library",
            "1060",
            {"library_id": 1, "payload": admin.LibraryUpdate(name="Updated Library")},
        ),
        (
            admin.delete_library,
            None,
            "bookcard.api.routes.admin.LibraryService",
            "delete_library",
            "1096",
            {"library_id": 1},
        ),
    ],
)
def test_unexpected_value_error_re_raised(
    monkeypatch: pytest.MonkeyPatch,
    route_func: callable,  # type: ignore[type-arg]
    payload: object | None,
    service_class_path: str,
    service_method: str,
    line_cover: str,
    call_kwargs: dict[str, object],
) -> None:
    """Test that ValueError with unexpected messages are re-raised (covers line {line_cover})."""
    session = DummySession()

    # Setup for create_device which needs a user
    if route_func == admin.create_device:
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hash",
        )
        with (
            patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
            patch(service_class_path) as mock_service_class,
        ):
            mock_user_repo = MagicMock()
            mock_user_repo.get.return_value = user
            mock_user_repo_class.return_value = mock_user_repo

            mock_service = MagicMock()
            setattr(
                mock_service,
                service_method,
                MagicMock(side_effect=ValueError("unexpected_error")),
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(ValueError, match="unexpected_error"):
                route_func(session, **call_kwargs)
    # Setup for other routes
    else:
        with patch(service_class_path) as mock_service_class:
            mock_service = MagicMock()
            setattr(
                mock_service,
                service_method,
                MagicMock(side_effect=ValueError("unexpected_error")),
            )
            mock_service_class.return_value = mock_service

            # For create_library, unexpected ValueErrors are re-raised as ValueError
            # For other routes, check if they re-raise or convert to HTTPException
            if route_func == admin.create_library:
                with pytest.raises(ValueError, match="unexpected_error"):
                    route_func(session, **call_kwargs)
            else:
                with pytest.raises(ValueError, match="unexpected_error"):
                    route_func(session, **call_kwargs)


def test_list_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_roles returns all roles."""
    session = DummySession()
    role1 = Role(id=1, name="viewer", description="Viewer role")
    role2 = Role(id=2, name="editor", description="Editor role")

    with patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [role1, role2]
        mock_repo_class.return_value = mock_repo

        result = admin.list_roles(session)
        assert len(result) == 2
        assert result[0].name == "viewer"
        assert result[1].name == "editor"


def test_delete_role_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_role succeeds."""
    session = DummySession()
    role = Role(id=2, name="viewer", description="Viewer role")

    with patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.delete_role(session, role_id=2)
        assert result is None
        mock_repo.delete.assert_called_once_with(role)


def test_delete_role_not_found() -> None:
    """Test delete_role raises 404 when role not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_role(session, role_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_not_found"


def test_grant_permission_to_role_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test grant_permission_to_role succeeds."""
    session = DummySession()
    payload = admin.RolePermissionGrant(permission_id=1, condition=None)

    role = Role(id=1, name="viewer", description="Viewer role")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.grant_permission_to_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.grant_permission_to_role(session, role_id=1, payload=payload)
        assert result.id == 1
        mock_service.grant_permission_to_role.assert_called_once_with(1, 1, None)


def test_grant_permission_to_role_already_has_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test grant_permission_to_role raises 409 when role already has permission."""
    session = DummySession()
    payload = admin.RolePermissionGrant(permission_id=1, condition=None)

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.grant_permission_to_role.side_effect = ValueError(
            "role_already_has_permission"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.grant_permission_to_role(session, role_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "role_already_has_permission"


def test_grant_permission_to_role_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test grant_permission_to_role raises 404 when role or permission not found."""
    session = DummySession()
    payload = admin.RolePermissionGrant(permission_id=1, condition=None)

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.grant_permission_to_role.side_effect = ValueError("role_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.grant_permission_to_role(session, role_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_or_permission_not_found"


def test_grant_permission_to_role_not_found_after_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test grant_permission_to_role raises 404 when role not found after grant."""
    session = DummySession()
    payload = admin.RolePermissionGrant(permission_id=1, condition=None)

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.grant_permission_to_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.grant_permission_to_role(session, role_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_not_found"


def test_revoke_permission_from_role_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test revoke_permission_from_role succeeds."""
    session = DummySession()
    role = Role(id=1, name="viewer", description="Viewer role")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.revoke_permission_from_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.revoke_permission_from_role(session, role_id=1, permission_id=1)
        assert result.id == 1


def test_revoke_permission_from_role_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test revoke_permission_from_role raises 404 when role permission not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.revoke_permission_from_role.side_effect = ValueError(
            "role_permission_not_found"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.revoke_permission_from_role(session, role_id=1, permission_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_permission_not_found"


def test_revoke_permission_from_role_not_found_after_revoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test revoke_permission_from_role raises 404 when role not found after revoke."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.revoke_permission_from_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.revoke_permission_from_role(session, role_id=1, permission_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_not_found"


def test_list_permissions_with_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_permissions filters by resource when provided."""
    from bookcard.models.auth import Permission

    session = DummySession()
    perm1 = Permission(id=1, name="read", resource="books", action="read")
    perm2 = Permission(id=2, name="write", resource="books", action="write")

    with patch("bookcard.api.routes.admin.PermissionRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_by_resource.return_value = [perm1, perm2]
        mock_repo_class.return_value = mock_repo

        result = admin.list_permissions(session, resource="books")
        assert len(result) == 2
        mock_repo.list_by_resource.assert_called_once_with("books")


def test_delete_permission_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_permission succeeds when permission is orphaned."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PermissionRepository") as mock_perm_repo_class,
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch(
            "bookcard.api.routes.admin.RolePermissionRepository"
        ) as mock_rp_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.delete_permission.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_perm_repo = MagicMock()
        mock_perm_repo_class.return_value = mock_perm_repo

        mock_rp_repo = MagicMock()
        mock_rp_repo_class.return_value = mock_rp_repo

        result = admin.delete_permission(session, permission_id=1)
        assert result is None
        mock_service.delete_permission.assert_called_once_with(1)
        session.commit()


def test_delete_permission_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_permission raises 404 when permission not found."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PermissionRepository") as mock_perm_repo_class,
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch(
            "bookcard.api.routes.admin.RolePermissionRepository"
        ) as mock_rp_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.delete_permission.side_effect = ValueError("permission_not_found")
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_perm_repo = MagicMock()
        mock_perm_repo_class.return_value = mock_perm_repo

        mock_rp_repo = MagicMock()
        mock_rp_repo_class.return_value = mock_rp_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_permission(session, permission_id=999)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "permission_not_found"


def test_delete_permission_assigned_to_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_permission raises 400 when permission is associated with roles."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PermissionRepository") as mock_perm_repo_class,
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch(
            "bookcard.api.routes.admin.RolePermissionRepository"
        ) as mock_rp_repo_class,
    ):
        mock_service = MagicMock()
        mock_service.delete_permission.side_effect = ValueError(
            "permission_assigned_to_roles_2",
        )
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_perm_repo = MagicMock()
        mock_perm_repo_class.return_value = mock_perm_repo

        mock_rp_repo = MagicMock()
        mock_rp_repo_class.return_value = mock_rp_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_permission(session, permission_id=1)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "permission_assigned_to_roles_2"


def test_list_permissions_without_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_permissions returns all permissions when resource not provided."""
    from bookcard.models.auth import Permission

    session = DummySession()
    perm1 = Permission(id=1, name="read", resource="books", action="read")
    perm2 = Permission(id=2, name="write", resource="authors", action="write")

    with patch("bookcard.api.routes.admin.PermissionRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list.return_value = [perm1, perm2]
        mock_repo_class.return_value = mock_repo

        result = admin.list_permissions(session, resource=None)
        assert len(result) == 2
        mock_repo.list.assert_called_once()


def test_create_device_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_device succeeds."""
    session = DummySession()
    payload = admin.EReaderDeviceCreate(
        email="device@example.com",
        device_name="My Kindle",
        device_type="kindle",
        preferred_format="epub",
        is_default=True,
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="My Kindle",
        device_type="kindle",
        preferred_format=EBookFormat.EPUB,
        is_default=True,
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.get.return_value = user
        mock_user_repo_class.return_value = mock_user_repo

        mock_service = MagicMock()
        mock_service.create_device.return_value = device
        mock_service_class.return_value = mock_service

        result = admin.create_device(session, user_id=1, payload=payload)
        assert result.id == 1
        assert result.email == "device@example.com"


def test_create_device_user_not_found() -> None:
    """Test create_device raises 404 when user not found."""
    session = DummySession()
    payload = admin.EReaderDeviceCreate(email="device@example.com")

    with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.create_device(session, user_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_create_device_email_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_device raises 409 when device email already exists."""
    session = DummySession()
    payload = admin.EReaderDeviceCreate(email="existing@example.com")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.get.return_value = user
        mock_user_repo_class.return_value = mock_user_repo

        mock_service = MagicMock()
        mock_service.create_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_device(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "device_email_already_exists"


def test_create_device_invalid_format_suppressed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_device suppresses ValueError for invalid format (covers suppress block lines 749-751)."""
    session = DummySession()
    payload = admin.EReaderDeviceCreate(
        email="device@example.com",
        preferred_format="invalid_format",  # Invalid format should be suppressed
    )

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        preferred_format=None,  # Should be None when format is invalid
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.get.return_value = user
        mock_user_repo_class.return_value = mock_user_repo

        mock_service = MagicMock()
        mock_service.create_device.return_value = device
        mock_service_class.return_value = mock_service

        result = admin.create_device(session, user_id=1, payload=payload)
        assert result.id == 1
        # Should create device with None format when invalid format provided
        mock_service.create_device.assert_called_once()


def test_list_user_devices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_user_devices returns all devices for a user."""
    session = DummySession()
    device1 = EReaderDevice(
        id=1,
        user_id=1,
        email="device1@example.com",
        device_type="kindle",
        is_default=True,
    )
    device2 = EReaderDevice(
        id=2,
        user_id=1,
        email="device2@example.com",
        device_type="kobo",
        is_default=False,
    )

    with patch("bookcard.api.routes.admin.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_user.return_value = [device1, device2]
        mock_repo_class.return_value = mock_repo

        result = admin.list_user_devices(session, user_id=1)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


def test_update_device_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_device succeeds."""
    session = DummySession()
    payload = admin.EReaderDeviceUpdate(
        email="newemail@example.com",
        device_name="Updated Device",
        preferred_format="mobi",
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="newemail@example.com",
        device_name="Updated Device",
        device_type="kindle",
        preferred_format=EBookFormat.MOBI,
        is_default=True,
    )

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_device.return_value = device
        mock_service_class.return_value = mock_service

        result = admin.update_device(session, device_id=1, payload=payload)
        assert result.id == 1
        assert result.email == "newemail@example.com"


def test_update_device_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_device raises 404 when device not found."""
    session = DummySession()
    payload = admin.EReaderDeviceUpdate(email="newemail@example.com")

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_device.side_effect = ValueError("device_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_device(session, device_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_update_device_email_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_device raises 409 when device email already exists."""
    session = DummySession()
    payload = admin.EReaderDeviceUpdate(email="existing@example.com")

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_device(session, device_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "device_email_already_exists"


def test_update_device_invalid_format_suppressed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_device suppresses ValueError for invalid format (covers suppress block lines 839-841)."""
    session = DummySession()
    payload = admin.EReaderDeviceUpdate(
        preferred_format="invalid_format",  # Invalid format should be suppressed
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        preferred_format=None,  # Should be None when format is invalid
    )

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_device.return_value = device
        mock_service_class.return_value = mock_service

        result = admin.update_device(session, device_id=1, payload=payload)
        assert result.id == 1
        # Should update device with None format when invalid format provided
        mock_service.update_device.assert_called_once()


def test_delete_device_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_device succeeds."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_device.return_value = None
        mock_service_class.return_value = mock_service

        result = admin.delete_device(session, device_id=1)
        assert result is None
        mock_service.delete_device.assert_called_once_with(1)


def test_delete_device_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_device raises 404 when device not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_device.side_effect = ValueError("device_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_device(session, device_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_list_libraries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_libraries returns all libraries."""
    session = DummySession()
    library1 = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
    )
    library2 = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.list_libraries.return_value = [library1, library2]
        mock_service_class.return_value = mock_service

        result = admin.list_libraries(session)
        assert len(result) == 2
        assert result[0].name == "Library 1"
        assert result[1].name == "Library 2"


def test_get_active_library_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_active_library returns active library when found."""
    session = DummySession()
    library = Library(
        id=1,
        name="Active Library",
        calibre_db_path="/path",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_service_class.return_value = mock_service

        result = admin.get_active_library(session)
        assert result is not None
        assert result.name == "Active Library"


def test_get_active_library_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_active_library returns None when no active library."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = None
        mock_service_class.return_value = mock_service

        result = admin.get_active_library(session)
        assert result is None


def test_create_library_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_library succeeds."""
    session = DummySession()
    payload = admin.LibraryCreate(
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
    )

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_library.return_value = library
        mock_service_class.return_value = mock_service

        result = admin.create_library(session, payload=payload)
        assert result.id == 1
        assert result.name == "Test Library"


def test_create_library_path_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_library raises 409 when library path already exists."""
    session = DummySession()
    payload = admin.LibraryCreate(
        name="Test Library",
        calibre_db_path="/existing/path",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_library.side_effect = ValueError(
            "library_path_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_library(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "library_path_already_exists"


def test_update_library_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_library succeeds."""
    session = DummySession()
    payload = admin.LibraryUpdate(
        name="Updated Library",
        calibre_db_path="/new/path",
    )

    library = Library(
        id=1,
        name="Updated Library",
        calibre_db_path="/new/path",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_library.return_value = library
        mock_service_class.return_value = mock_service

        result = admin.update_library(session, library_id=1, payload=payload)
        assert result.id == 1
        assert result.name == "Updated Library"


def test_update_library_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_library raises 404 when library not found."""
    session = DummySession()
    payload = admin.LibraryUpdate(name="Updated Library")

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_library.side_effect = ValueError("library_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_library(session, library_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"


def test_update_library_path_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_library raises 409 when library path already exists."""
    session = DummySession()
    payload = admin.LibraryUpdate(calibre_db_path="/existing/path")

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_library.side_effect = ValueError(
            "library_path_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_library(session, library_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "library_path_already_exists"


def test_delete_library_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_library succeeds."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_library.return_value = None
        mock_service_class.return_value = mock_service

        result = admin.delete_library(session, library_id=1)
        assert result is None
        mock_service.delete_library.assert_called_once_with(1)


def test_delete_library_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_library raises 404 when library not found."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_library.side_effect = ValueError("library_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_library(session, library_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"


def test_get_library_stats_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_library_stats returns statistics (covers lines 1128-1133)."""
    session = DummySession()

    mock_stats = {
        "total_books": 100,
        "total_series": 20,
        "total_authors": 50,
        "total_tags": 30,
        "total_ratings": 10,
        "total_content_size": 1024000,
    }

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_library_stats.return_value = mock_stats
        mock_service_class.return_value = mock_service

        result = admin.get_library_stats(session, library_id=1)
        assert result.total_books == 100
        assert result.total_series == 20


def test_get_library_stats_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_library_stats raises 404 when library not found (covers lines 1134-1138)."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_library_stats.side_effect = ValueError("library_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.get_library_stats(session, library_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"


def test_get_library_stats_other_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_library_stats re-raises other ValueError (covers line 1138)."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_library_stats.side_effect = ValueError("other_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="other_error"):
            admin.get_library_stats(session, library_id=1)


def test_get_library_stats_file_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_library_stats raises 404 when database file not found (covers lines 1139-1142)."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_library_stats.side_effect = FileNotFoundError(
            "Database not found"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.get_library_stats(session, library_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "calibre_database_not_found"


def test_get_user_profile_picture_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_user_profile_picture raises 404 when user not found (covers line 282-283)."""

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin.get_user_profile_picture(request, session, user_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_get_user_profile_picture_no_picture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_user_profile_picture returns 404 when user has no profile picture (covers line 285-286)."""
    from fastapi import Response

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        profile_picture=None,
    )

    with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        result = admin.get_user_profile_picture(request, session, user_id=1)
        assert isinstance(result, Response)
        assert result.status_code == 404


def test_get_user_profile_picture_absolute_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_user_profile_picture with absolute path (covers lines 290-291)."""
    import tempfile
    from pathlib import Path

    from fastapi.responses import FileResponse

    class DummyRequest:
        def __init__(self, temp_dir: str) -> None:
            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    with tempfile.TemporaryDirectory() as tmpdir:
        pic_file = Path(tmpdir) / "pic.jpg"
        pic_file.write_bytes(b"fake image")

        session = DummySession()
        request = DummyRequest(tmpdir)
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            profile_picture=str(pic_file),
        )

        with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo

            result = admin.get_user_profile_picture(request, session, user_id=1)
            assert isinstance(result, FileResponse)
            assert result.path == str(pic_file)
            assert result.media_type == "image/jpeg"


def test_get_user_profile_picture_relative_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_user_profile_picture with relative path (covers lines 292-294)."""
    import tempfile
    from pathlib import Path

    from fastapi.responses import FileResponse

    class DummyRequest:
        def __init__(self, temp_dir: str) -> None:
            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    with tempfile.TemporaryDirectory() as tmpdir:
        pic_file = Path(tmpdir) / "pictures" / "pic.png"
        pic_file.parent.mkdir()
        pic_file.write_bytes(b"fake image")

        session = DummySession()
        request = DummyRequest(tmpdir)
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            profile_picture="pictures/pic.png",
        )

        with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo

            result = admin.get_user_profile_picture(request, session, user_id=1)
            assert isinstance(result, FileResponse)
            assert result.path == str(pic_file)
            assert result.media_type == "image/png"


def test_get_user_profile_picture_file_not_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_user_profile_picture returns 404 when file doesn't exist (covers lines 296-297)."""
    from fastapi import Response

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        profile_picture="nonexistent.jpg",
    )

    with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        result = admin.get_user_profile_picture(request, session, user_id=1)
        assert isinstance(result, Response)
        assert result.status_code == 404


@pytest.mark.parametrize(
    ("ext", "expected_media_type"),
    [
        (".jpg", "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".png", "image/png"),
        (".gif", "image/gif"),
        (".webp", "image/webp"),
        (".svg", "image/svg+xml"),
        (".unknown", "image/jpeg"),  # Default fallback
    ],
)
def test_get_user_profile_picture_media_types(
    monkeypatch: pytest.MonkeyPatch, ext: str, expected_media_type: str
) -> None:
    """Test get_user_profile_picture determines correct media type (covers lines 299-309)."""
    import tempfile
    from pathlib import Path

    from fastapi.responses import FileResponse

    class DummyRequest:
        def __init__(self, temp_dir: str) -> None:
            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    with tempfile.TemporaryDirectory() as tmpdir:
        pic_file = Path(tmpdir) / f"pic{ext}"
        pic_file.write_bytes(b"fake image")

        session = DummySession()
        request = DummyRequest(tmpdir)
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            profile_picture=str(pic_file),
        )

        with patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo

            result = admin.get_user_profile_picture(request, session, user_id=1)
            assert isinstance(result, FileResponse)
            assert result.media_type == expected_media_type


def test_update_user_with_role_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user with role_ids creates role service (covers lines 353-362)."""
    session = DummySession()
    payload = admin.AdminUserUpdate(role_ids=[1, 2])

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_role_repo_class,
        patch(
            "bookcard.api.routes.admin.UserRoleRepository"
        ) as mock_user_role_repo_class,
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
        patch("bookcard.api.routes.admin.RoleService") as mock_role_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        # Verify role service was created
        mock_role_repo_class.assert_called_once()
        mock_user_role_repo_class.assert_called_once()
        mock_role_service_class.assert_called_once()


def test_update_user_with_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user with password creates password hasher (covers line 367)."""
    session = DummySession()
    payload = admin.AdminUserUpdate(password="newpassword123")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        # Verify password hasher was created
        mock_hasher_class.assert_called_once()


def test_update_user_with_device_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user with default_device_email creates device service (covers lines 372-374)."""
    session = DummySession()
    payload = admin.AdminUserUpdate(default_device_email="device@example.com")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []
    user.roles = []

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
        patch("bookcard.api.routes.admin.EReaderRepository") as mock_device_repo_class,
        patch("bookcard.api.routes.admin.EReaderService") as mock_device_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.return_value = user
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        # Verify device service was created
        mock_device_repo_class.assert_called_once()
        mock_device_service_class.assert_called_once()


def test_update_user_password_hasher_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_user raises 500 when password_hasher_required (covers lines 403-406)."""
    session = DummySession()
    payload = admin.AdminUserUpdate(password="newpassword123")

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_user.side_effect = ValueError("password_hasher_required")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_user(session, user_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "password_update_failed"


def test_delete_user_cannot_delete_self(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_user raises 403 when admin tries to delete themselves (covers lines 444-445)."""

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    with patch("bookcard.api.routes.admin.get_admin_user") as mock_get_admin:
        mock_get_admin.return_value = admin_user

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_user(request, session, admin_user, user_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "cannot_delete_self"


def test_delete_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_user succeeds (covers lines 447-461)."""

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )
    target_user = User(
        id=2,
        username="target",
        email="target@example.com",
        password_hash="hash",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.EReaderRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.get.return_value = target_user
        mock_repo_class.return_value = mock_user_repo

        mock_service = MagicMock()
        mock_service.delete_user.return_value = None
        mock_service_class.return_value = mock_service

        admin.delete_user(request, session, admin_user, user_id=2)
        mock_service.delete_user.assert_called_once()
        session.commit()


def test_delete_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_user raises 404 when user not found (covers lines 462-466)."""

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.EReaderRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.get.return_value = None
        mock_repo_class.return_value = mock_user_repo

        mock_service = MagicMock()
        mock_service.delete_user.side_effect = ValueError("user_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_user(request, session, admin_user, user_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "user_not_found"


def test_delete_user_other_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_user re-raises ValueError with other messages (covers line 466)."""
    from unittest.mock import MagicMock, patch

    class DummyRequest:
        def __init__(self) -> None:
            import tempfile

            temp_dir = tempfile.mkdtemp()

            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.EReaderRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.delete_user.side_effect = ValueError("other_error")
        mock_service_class.return_value = mock_service

        from bookcard.api.routes import admin

        with pytest.raises(ValueError, match="other_error"):
            admin.delete_user(request, session, admin_user, user_id=999)


def test_create_user_generic_value_error() -> None:
    """Test create_user raises 400 for generic ValueError (covers line 264)."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="testuser",
        email="test@example.com",
        password="password123",
    )

    with (
        patch("bookcard.api.routes.admin.UserRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.create_admin_user.side_effect = ValueError("generic_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_user(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic_error"


def test_auth_service_function(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _system_config_service function creates SystemConfigurationService."""
    from unittest.mock import MagicMock

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with (
        patch("bookcard.api.routes.admin.DataEncryptor") as mock_encryptor_class,
        patch(
            "bookcard.api.routes.admin.SystemConfigurationService"
        ) as mock_service_class,
    ):
        mock_encryptor = MagicMock()
        mock_encryptor_class.return_value = mock_encryptor
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = admin._system_config_service(request, session)  # type: ignore[arg-type]

        assert result is not None
        mock_encryptor_class.assert_called_once()
        mock_service_class.assert_called_once_with(
            session=session, encryptor=mock_encryptor
        )


def test_ensure_role_exists_role_not_found() -> None:
    """Test _ensure_role_exists raises 404 when role not found (covers lines 715-717)."""
    with patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            admin._ensure_role_exists(mock_repo, 999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_not_found"


def test_get_role_with_permissions_success() -> None:
    """Test _get_role_with_permissions returns role (covers line 753)."""
    session = DummySession()
    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = role

    with patch.object(session, "exec", return_value=mock_result):
        result = admin._get_role_with_permissions(session, 1)  # type: ignore[invalid-argument-type]
        assert result.id == 1
        assert result.name == "test"


def test_create_role_id_is_none() -> None:
    """Test create_role raises 500 when role.id is None (covers lines 802-803)."""
    session = DummySession()
    payload = admin.RoleCreate(name="testrole", description="Test role")

    role = Role(id=None, name="testrole", description="Test role")
    role.permissions = []

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role_from_schema.return_value = role
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_role(session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "role_id_is_none"


def test_create_role_reload_fails() -> None:
    """Test create_role handles reload failure (covers line 810)."""
    session = DummySession()
    payload = admin.RoleCreate(name="testrole", description="Test role")

    role = Role(id=1, name="testrole", description="Test role")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = None  # Simulate reload failure

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_service = MagicMock()
        mock_service.create_role_from_schema.return_value = role
        mock_service_class.return_value = mock_service

        result = admin.create_role(session, payload)
        assert result.id == 1
        assert result.name == "testrole"


def test_create_role_generic_value_error() -> None:
    """Test create_role re-raises unexpected ValueError (covers line 829)."""
    session = DummySession()
    payload = admin.RoleCreate(name="testrole", description="Test role")

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role_from_schema.side_effect = ValueError(
            "unexpected_error"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="unexpected_error"):
            admin.create_role(session, payload)


def test_update_role_ensure_role_not_found() -> None:
    """Test update_role calls _ensure_role_exists (covers line 919)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="updated")

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = None  # Role not found
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role(session, role_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404


@pytest.mark.parametrize(
    ("error_msg", "expected_status"),
    [
        ("name_cannot_be_blank", 400),
        ("permission_name_cannot_be_blank", 400),
        ("resource_cannot_be_blank", 400),
        ("action_cannot_be_blank", 400),
        ("cannot_modify_locked_role_name", 400),
        ("cannot_remove_permissions_from_locked_role", 400),
        ("permission_not_found", 400),
        ("permission_already_exists", 400),
        ("permission_with_resource_action_already_exists", 400),
        ("permission_name_exists_with_different_resource_action", 400),
        ("permission_resource_action_exists_with_different_name", 400),
        ("resource_and_action_required_for_new_permission", 400),
        ("permission_id_or_permission_name_required", 400),
        ("permission_id_is_none", 400),
        ("role_permission_not_found", 400),
        ("role_permission_belongs_to_different_role", 400),
    ],
)
def test_update_role_value_error_handlers(error_msg: str, expected_status: int) -> None:
    """Test update_role handles various ValueError messages (covers lines 933-951)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="updated")

    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = role

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_role_from_schema.side_effect = ValueError(error_msg)
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role(session, role_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == error_msg


def test_update_role_unexpected_value_error() -> None:
    """Test update_role re-raises unexpected ValueError (covers line 953)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="updated")

    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = role

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_role_from_schema.side_effect = ValueError("unexpected")
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="unexpected"):
            admin.update_role(session, role_id=1, payload=payload)


def test_delete_role_assigned_to_users() -> None:
    """Test delete_role raises 409 when role assigned to users (covers lines 999-1003)."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = Role(id=2, name="test", description="test")
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.delete_role.side_effect = ValueError("role_assigned_to_users_5")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_role(session, role_id=2)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "role_assigned_to_users"


def test_delete_role_generic_value_error() -> None:
    """Test delete_role raises 400 for generic ValueError (covers line 1004)."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = Role(id=2, name="test", description="test")
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.delete_role.side_effect = ValueError("generic_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_role(session, role_id=2)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic_error"


def test_grant_permission_to_role_reload_fails() -> None:
    """Test grant_permission_to_role handles reload failure (covers line 1074)."""
    session = DummySession()
    payload = admin.RolePermissionGrant(permission_id=1, condition=None)

    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = None  # Simulate reload failure

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_service = MagicMock()
        mock_service.grant_permission_to_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.grant_permission_to_role(session, role_id=1, payload=payload)
        assert result.id == 1


def test_revoke_permission_from_role_reload_fails() -> None:
    """Test revoke_permission_from_role handles reload failure (covers line 1139)."""
    session = DummySession()
    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = None  # Simulate reload failure

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_service = MagicMock()
        mock_service.revoke_permission_from_role.return_value = None
        mock_service_class.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.revoke_permission_from_role(session, role_id=1, permission_id=1)
        assert result.id == 1


def test_update_permission_id_is_none() -> None:
    """Test update_permission raises 500 when permission.id is None (covers lines 1188-1190)."""
    from bookcard.models.auth import Permission

    session = DummySession()
    payload = admin.PermissionUpdate(name="updated")

    permission = Permission(
        id=None,
        name="updated",
        resource="books",
        action="read",
    )

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.update_permission_from_schema.return_value = permission
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_permission(session, permission_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "permission_id_is_none"


def test_update_permission_already_exists() -> None:
    """Test update_permission raises 409 when permission already exists (covers lines 1205-1208)."""
    session = DummySession()
    payload = admin.PermissionUpdate(name="existing")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.update_permission_from_schema.side_effect = ValueError(
            "permission_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_permission(session, permission_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "permission_already_exists"


def test_update_permission_generic_value_error() -> None:
    """Test update_permission raises 400 for generic ValueError (covers line 1209)."""
    session = DummySession()
    payload = admin.PermissionUpdate(name="updated")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.update_permission_from_schema.side_effect = ValueError("generic")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_permission(session, permission_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic"


def test_delete_permission_cannot_delete() -> None:
    """Test delete_permission raises 400 when cannot_delete_permission (covers line 1258)."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.delete_permission.side_effect = ValueError(
            "cannot_delete_permission"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_permission(session, permission_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "cannot_delete_permission"


def test_delete_permission_generic_value_error() -> None:
    """Test delete_permission raises 400 for generic ValueError (covers line 1259)."""
    session = DummySession()

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.delete_permission.side_effect = ValueError("generic")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_permission(session, permission_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic"


def test_update_role_permission_generic_value_error() -> None:
    """Test update_role_permission raises 400 for generic ValueError (covers line 1322)."""
    session = DummySession()
    payload = admin.RolePermissionUpdate(condition={"key": "value"})

    role = Role(id=1, name="test", description="test")
    role.permissions = []

    mock_result = MagicMock()
    mock_result.first.return_value = role

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
        patch.object(session, "exec", return_value=mock_result),
    ):
        mock_service = MagicMock()
        mock_service.update_role_permission_condition.side_effect = ValueError(
            "generic"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role_permission(
                session, role_id=1, role_permission_id=1, payload=payload
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic"


def test_create_permission_id_is_none() -> None:
    """Test create_permission raises 500 when permission.id is None (covers lines 1374-1376)."""
    from bookcard.models.auth import Permission

    session = DummySession()
    payload = admin.PermissionCreate(name="new", resource="books", action="read")

    permission = Permission(
        id=None,
        name="new",
        resource="books",
        action="read",
    )

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.create_permission.return_value = permission
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_permission(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "permission_id_is_none"


@pytest.mark.parametrize(
    ("error_msg", "expected_status"),
    [
        ("name_cannot_be_blank", 400),
        ("permission_name_cannot_be_blank", 400),
        ("resource_cannot_be_blank", 400),
        ("action_cannot_be_blank", 400),
    ],
)
def test_create_permission_value_error_handlers(
    error_msg: str, expected_status: int
) -> None:
    """Test create_permission handles various ValueError messages (covers lines 1393-1399)."""
    session = DummySession()
    payload = admin.PermissionCreate(name="new", resource="books", action="read")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.create_permission.side_effect = ValueError(error_msg)
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_permission(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == error_msg


def test_create_permission_generic_value_error() -> None:
    """Test create_permission raises 400 for generic ValueError (covers line 1400)."""
    session = DummySession()
    payload = admin.PermissionCreate(name="new", resource="books", action="read")

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin.RoleRepository"),
        patch("bookcard.api.routes.admin.PermissionRepository"),
        patch("bookcard.api.routes.admin.UserRoleRepository"),
        patch("bookcard.api.routes.admin.RolePermissionRepository"),
    ):
        mock_service = MagicMock()
        mock_service.create_permission.side_effect = ValueError("generic")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_permission(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "generic"


def test_create_library_invalid_database() -> None:
    """Test create_library raises 400 for invalid_calibre_database (covers line 1743)."""
    session = DummySession()
    payload = admin.LibraryCreate(
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_library.side_effect = ValueError("invalid_calibre_database")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_library(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "invalid_calibre_database"


def test_create_library_permission_error() -> None:
    """Test create_library raises 403 for PermissionError (covers lines 1746-1748)."""
    session = DummySession()
    payload = admin.LibraryCreate(
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_library.side_effect = PermissionError("Access denied")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_library(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.detail


def test_create_library_file_not_found() -> None:
    """Test create_library raises 404 for FileNotFoundError (covers lines 1749-1750)."""
    session = DummySession()
    payload = admin.LibraryCreate(
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch("bookcard.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_library.side_effect = FileNotFoundError("File not found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_library(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404


def test_download_openlibrary_dumps_task_runner_unavailable() -> None:
    """Test download_openlibrary_dumps raises 503 when task runner unavailable (covers lines 1974-1981)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )
    payload = admin.DownloadFilesRequest(urls=["https://example.com/file.txt"])

    with pytest.raises(HTTPException) as exc_info:
        admin.download_openlibrary_dumps(request, current_user, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_download_openlibrary_dumps_value_error() -> None:
    """Test download_openlibrary_dumps raises 400 for ValueError (covers lines 1993-1997)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            class DummyTaskRunner:
                pass

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"config": DummyConfig(), "task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )
    payload = admin.DownloadFilesRequest(urls=[])

    with (
        patch("bookcard.api.routes.admin.OpenLibraryService") as mock_service_class,
    ):
        mock_service = MagicMock()
        mock_service.create_download_task.side_effect = ValueError("No URLs provided")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.download_openlibrary_dumps(request, current_user, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No URLs provided"


def test_ingest_openlibrary_dumps_no_file_types() -> None:
    """Test ingest_openlibrary_dumps raises 400 when no file types selected (covers lines 2075-2083)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            class DummyTaskRunner:
                pass

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"config": DummyConfig(), "task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )
    payload = admin.IngestFilesRequest(
        process_authors=False, process_works=False, process_editions=False
    )

    with pytest.raises(HTTPException) as exc_info:
        admin.ingest_openlibrary_dumps(request, current_user, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert "At least one file type" in exc_info.value.detail


def test_ingest_openlibrary_dumps_task_runner_unavailable() -> None:
    """Test ingest_openlibrary_dumps raises 503 when task runner unavailable (covers lines 2086-2093)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )
    payload = admin.IngestFilesRequest(process_authors=True)

    with pytest.raises(HTTPException) as exc_info:
        admin.ingest_openlibrary_dumps(request, current_user, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_get_openlibrary_dump_config_none() -> None:
    """Test get_openlibrary_dump_config returns defaults when config is None (covers lines 2139-2155)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with (
        patch("bookcard.api.routes.admin._auth_service") as mock_auth_service,
        patch("bookcard.api.routes.admin.get_current_user"),
    ):
        mock_service = MagicMock()
        mock_service.get_openlibrary_dump_config.return_value = None
        mock_auth_service.return_value = mock_service

        result = admin.get_openlibrary_dump_config(request, session)

        assert result.id is None
        assert (
            result.authors_url
            == "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
        )
        assert result.default_process_authors is True


def test_upsert_openlibrary_dump_config_not_admin() -> None:
    """Test upsert_openlibrary_dump_config raises 403 when user not admin (covers lines 2187-2188)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    payload = admin.OpenLibraryDumpConfigUpdate(
        authors_url="https://example.com/authors.txt"
    )

    non_admin_user = User(
        id=1,
        username="user",
        email="user@test.com",
        password_hash="hash",
        is_admin=False,
    )

    with (
        patch("bookcard.api.routes.admin._auth_service") as mock_auth_service,
        patch(
            "bookcard.api.routes.admin.get_current_user", return_value=non_admin_user
        ),
    ):
        mock_service = MagicMock()
        mock_auth_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.upsert_openlibrary_dump_config(request, session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "forbidden"


def test_upsert_openlibrary_dump_config_value_error() -> None:
    """Test upsert_openlibrary_dump_config raises 400 for ValueError (covers lines 2196-2198)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    payload = admin.OpenLibraryDumpConfigUpdate(authors_url="invalid")

    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )

    with (
        patch("bookcard.api.routes.admin._auth_service") as mock_auth_service,
        patch("bookcard.api.routes.admin.get_current_user", return_value=admin_user),
    ):
        mock_service = MagicMock()
        mock_service.upsert_openlibrary_dump_config.side_effect = ValueError(
            "Invalid URL"
        )
        mock_auth_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.upsert_openlibrary_dump_config(request, session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid URL"


def test_get_scheduled_tasks_config() -> None:
    """Test get_scheduled_tasks_config returns config (covers lines 2225-2227)."""
    from datetime import UTC, datetime

    from bookcard.models.config import ScheduledTasksConfig

    session = DummySession()
    config = ScheduledTasksConfig(
        id=1,
        start_time_hour=2,
        duration_hours=4,
        generate_book_covers=True,
        generate_series_covers=False,
        reconnect_database=True,
        metadata_backup=False,
        epub_fixer_daily_scan=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with patch(
        "bookcard.api.routes.admin.ScheduledTasksConfigService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_scheduled_tasks_config.return_value = config
        mock_service_class.return_value = mock_service

        result = admin.get_scheduled_tasks_config(session)

        assert result.id == 1
        assert result.start_time_hour == 2
        assert result.generate_book_covers is True


def test_upsert_scheduled_tasks_config_not_admin() -> None:
    """Test upsert_scheduled_tasks_config raises 403 when user not admin (covers lines 2257-2258)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    request = DummyRequest()
    payload = admin.ScheduledTasksConfigUpdate(generate_book_covers=True)

    non_admin_user = User(
        id=1,
        username="user",
        email="user@test.com",
        password_hash="hash",
        is_admin=False,
    )

    with patch(
        "bookcard.api.routes.admin.get_current_user", return_value=non_admin_user
    ):
        with pytest.raises(HTTPException) as exc_info:
            admin.upsert_scheduled_tasks_config(request, session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "forbidden"


def test_upsert_scheduled_tasks_config_value_error() -> None:
    """Test upsert_scheduled_tasks_config raises 400 for ValueError (covers lines 2267-2269)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    request = DummyRequest()
    payload = admin.ScheduledTasksConfigUpdate(generate_book_covers=True)

    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )

    with (
        patch("bookcard.api.routes.admin.get_current_user", return_value=admin_user),
        patch(
            "bookcard.api.routes.admin.ScheduledTasksConfigService"
        ) as mock_service_class,
    ):
        mock_service = MagicMock()
        mock_service.update_scheduled_tasks_config.side_effect = ValueError(
            "Invalid config"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.upsert_scheduled_tasks_config(request, session, payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid config"


def test_update_role_locked_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_role with locked role (covers lines 923-926)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="updated")

    role = Role(id=1, name="admin", description="Admin role")
    role.permissions = []

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock _get_role_with_permissions
        with patch(
            "bookcard.api.routes.admin._get_role_with_permissions"
        ) as mock_get_role:
            mock_get_role.return_value = role

            result = admin.update_role(session, role_id=1, payload=payload)
            assert result.id == 1
            # Verify is_locked was passed (role_id == 1)
            mock_service.update_role_from_schema.assert_called_once()
            call_args = mock_service.update_role_from_schema.call_args
            assert call_args[0][0] == 1  # role_id
            assert call_args[0][2] is True  # is_locked (role_id == 1)


def test_update_role_already_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_role raises 409 when role name already exists (covers line 930)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="existing")

    role = Role(id=1, name="test", description="Test role")

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_role_from_schema.side_effect = ValueError(
            "role_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role(session, role_id=1, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "role_already_exists"


def test_update_role_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_role raises 404 when role not found (covers line 932)."""
    session = DummySession()
    payload = admin.RoleUpdate(name="updated")

    with (
        patch("bookcard.api.routes.admin.RoleRepository") as mock_repo_class,
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = None  # Role not found
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_role_from_schema.side_effect = ValueError("role_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role(session, role_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_not_found"


def test_delete_role_cannot_delete_locked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_role raises 403 when trying to delete locked role (covers line 998)."""
    session = DummySession()

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_role.side_effect = ValueError("cannot_delete_locked_role")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_role(session, role_id=1)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "cannot_delete_locked_role"


def test_update_permission_not_found() -> None:
    """Test update_permission raises 404 when permission not found (covers line 1203)."""
    session = DummySession()
    payload = admin.PermissionUpdate(name="updated")

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.update_permission_from_schema.side_effect = ValueError(
            "permission_not_found"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.update_permission(session, permission_id=999, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "permission_not_found"


def test_update_role_permission_http_exception() -> None:
    """Test update_role_permission handles HTTPException (covers lines 1312-1317)."""
    session = DummySession()
    payload = admin.RolePermissionUpdate(condition={"tag": "fiction"})

    role = Role(id=1, name="test", description="Test role")
    role.permissions = []

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin._get_role_with_permissions") as mock_get_role,
    ):
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_get_role.side_effect = HTTPException(status_code=404, detail="not_found")

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role_permission(
                session, role_id=1, role_permission_id=1, payload=payload
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404


def test_update_role_permission_not_found() -> None:
    """Test update_role_permission raises 404 when not found (covers line 1321)."""
    session = DummySession()
    payload = admin.RolePermissionUpdate(condition={"tag": "fiction"})

    role = Role(id=1, name="test", description="Test role")
    role.permissions = []

    with (
        patch("bookcard.api.routes.admin.RoleService") as mock_service_class,
        patch("bookcard.api.routes.admin._get_role_with_permissions") as mock_get_role,
    ):
        mock_service = MagicMock()
        mock_service.update_role_permission_condition.side_effect = ValueError(
            "role_permission_not_found"
        )
        mock_service_class.return_value = mock_service

        mock_get_role.return_value = role

        with pytest.raises(HTTPException) as exc_info:
            admin.update_role_permission(
                session, role_id=1, role_permission_id=999, payload=payload
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "role_permission_not_found"


def test_create_permission_already_exists() -> None:
    """Test create_permission raises 409 when permission already exists (covers line 1392)."""
    session = DummySession()
    payload = admin.PermissionCreate(
        name="test", resource="books", action="read", description="Test permission"
    )

    with patch("bookcard.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_permission.side_effect = ValueError(
            "permission_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.create_permission(session, payload=payload)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "permission_already_exists"


def test_download_openlibrary_dumps_success() -> None:
    """Test download_openlibrary_dumps succeeds (covers line 1999)."""
    from bookcard.api.routes.admin import DownloadFilesRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "task_runner": DummyTaskRunner(),
                            "config": DummyConfig(),
                        },
                    )()
                },
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )

    payload = DownloadFilesRequest(urls=["https://example.com/file.txt"])

    with patch("bookcard.api.routes.admin.OpenLibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_download_task.return_value = 1
        mock_service_class.return_value = mock_service

        result = admin.download_openlibrary_dumps(
            request=request,
            current_user=current_user,
            payload=payload,
        )
        assert result.task_id == 1
        assert result.message == "Download task created"


def test_ingest_openlibrary_dumps_success() -> None:
    """Test ingest_openlibrary_dumps succeeds (covers lines 2094-2106)."""
    from bookcard.api.routes.admin import IngestFilesRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "task_runner": DummyTaskRunner(),
                            "config": DummyConfig(),
                        },
                    )()
                },
            )()

    request = DummyRequest()
    current_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )

    payload = IngestFilesRequest(
        process_authors=True, process_works=True, process_editions=True
    )

    with patch("bookcard.api.routes.admin.OpenLibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_ingest_task.return_value = 1
        mock_service_class.return_value = mock_service

        result = admin.ingest_openlibrary_dumps(
            request=request,
            current_user=current_user,
            payload=payload,
        )
        assert result.task_id == 1
        assert result.message == "Ingest task created"


def test_get_openlibrary_dump_config_returns_defaults() -> None:
    """Test get_openlibrary_dump_config returns defaults when config is None (covers line 2156)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"
                encryption_key = b"test_key"

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "config": DummyConfig(),
                        },
                    )()
                },
            )()

    session = DummySession()
    request = DummyRequest()

    with patch("bookcard.api.routes.admin._auth_service") as mock_auth_service:
        mock_service = MagicMock()
        mock_service.get_openlibrary_dump_config.return_value = None
        mock_auth_service.return_value = mock_service

        result = admin.get_openlibrary_dump_config(
            request=request,
            session=session,
        )
        assert result.id is None
        assert (
            result.authors_url
            == "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
        )
        assert (
            result.works_url
            == "https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
        )
        assert (
            result.editions_url
            == "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz"
        )


def test_upsert_scheduled_tasks_config_success() -> None:
    """Test upsert_scheduled_tasks_config succeeds (covers lines 2265-2271)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    request = DummyRequest()
    payload = admin.ScheduledTasksConfigUpdate(generate_book_covers=True)

    admin_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        is_admin=True,
    )

    from bookcard.models.config import ScheduledTasksConfig

    config = ScheduledTasksConfig(
        id=1,
        generate_book_covers=True,
        generate_book_covers_interval_hours=24,
    )

    with (
        patch("bookcard.api.routes.admin.get_current_user", return_value=admin_user),
        patch(
            "bookcard.api.routes.admin.ScheduledTasksConfigService"
        ) as mock_service_class,
    ):
        mock_service = MagicMock()
        mock_service.update_scheduled_tasks_config.return_value = config
        mock_service_class.return_value = mock_service

        result = admin.upsert_scheduled_tasks_config(
            request=request,
            session=session,
            payload=payload,
        )
        assert result.generate_book_covers is True

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
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for admin routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import fundamental.api.routes.admin as admin
from fundamental.models.auth import EBookFormat, EReaderDevice, Role, User
from fundamental.models.config import Library
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = None
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        assert result.username == "testuser"
        mock_repo.add.assert_called_once()
        session.flush()


def test_create_user_username_exists() -> None:
    """Test create_user raises 409 when username already exists."""
    session = DummySession()
    payload = admin.AdminUserCreate(
        username="existing",
        email="test@example.com",
        password="password123",
    )

    existing_user = User(
        id=1,
        username="existing",
        email="existing@example.com",
        password_hash="hash",
    )

    with patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = existing_user
        mock_repo_class.return_value = mock_repo

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

    existing_user = User(
        id=1,
        username="existing",
        email="existing@example.com",
        password_hash="hash",
    )

    with patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = None
        mock_repo.find_by_email.return_value = existing_user
        mock_repo_class.return_value = mock_repo

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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = None
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_role_service = MagicMock()
        mock_role_service.assign_role_to_user.return_value = None
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Should attempt to assign roles
        assert mock_role_service.assign_role_to_user.call_count == 2


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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch(
            "fundamental.api.routes.admin.EReaderService"
        ) as mock_device_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = None
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_device_service = MagicMock()
        mock_device_service.create_device.return_value = MagicMock()
        mock_device_service_class.return_value = mock_device_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Should create device
        mock_device_service.create_device.assert_called_once()


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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_username.return_value = None
        mock_user_repo.find_by_email.return_value = None
        mock_user_repo_class.return_value = mock_user_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_role_service = MagicMock()
        # First role assignment succeeds, second raises ValueError (should be suppressed)
        mock_role_service.assign_role_to_user.side_effect = [
            None,
            ValueError("role_not_found"),
        ]
        mock_role_service_class.return_value = mock_role_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Should attempt to assign both roles, second one suppressed
        assert mock_role_service.assign_role_to_user.call_count == 2


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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch(
            "fundamental.api.routes.admin.EReaderService"
        ) as mock_device_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_username.return_value = None
        mock_user_repo.find_by_email.return_value = None
        mock_user_repo_class.return_value = mock_user_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_device_service = MagicMock()
        # Device creation raises ValueError (should be suppressed)
        mock_device_service.create_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_device_service_class.return_value = mock_device_service

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.create_user(session, payload)
        assert result.id == 1
        # Device creation should be attempted but error suppressed
        mock_device_service.create_device.assert_called_once()


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
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.PasswordHasher") as mock_hasher_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_username.return_value = None
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"
        mock_hasher_class.return_value = mock_hasher

        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = None
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
    user1.ereader_devices = []  # type: ignore[attr-defined]
    user1.roles = []  # type: ignore[attr-defined]

    user2 = User(
        id=2,
        username="user2",
        email="user2@example.com",
        password_hash="hash",
    )
    user2.ereader_devices = []  # type: ignore[attr-defined]
    user2.roles = []  # type: ignore[attr-defined]

    with patch("fundamental.api.routes.admin.UserService") as mock_service_class:
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with patch("fundamental.api.routes.admin.UserService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.get_user(session, user_id=1)
        assert result.id == 1
        assert result.username == "testuser"


def test_get_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_user raises 404 when user not found."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.UserService") as mock_service_class:
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_profile.return_value = None
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        assert result.username == "newname"


def test_update_user_not_found() -> None:
    """Test update_user raises 404 when user not found."""
    session = DummySession()
    payload = admin.AdminUserUpdate(username="newname")

    with patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class:
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

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_profile.side_effect = ValueError("username_already_exists")
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_admin_status.return_value = None
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        mock_service.update_admin_status.assert_called_once_with(1, True)


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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_active_status.return_value = None
        mock_service.get_with_relationships.return_value = user
        mock_service_class.return_value = mock_service

        result = admin.update_user(session, user_id=1, payload=payload)
        assert result.id == 1
        mock_service.update_active_status.assert_called_once_with(1, False)


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

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_profile.return_value = None
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

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        # Raise ValueError with unexpected message (not username_already_exists or email_already_exists)
        mock_service.update_profile.side_effect = ValueError("unexpected_error")
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

    with (
        patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = user
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        setattr(
            mock_service,
            method_name,
            MagicMock(side_effect=ValueError("user_not_found")),
        )
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class:
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class:
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
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
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
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    with (
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class:
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
        patch("fundamental.api.routes.admin.RoleService") as mock_role_service_class,
        patch("fundamental.api.routes.admin.UserService") as mock_service_class,
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role.return_value = role
        mock_service_class.return_value = mock_service

        result = admin.create_role(session, payload)
        assert result.id == 1
        assert result.name == "viewer"


def test_create_role_already_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create_role raises 409 when role already exists."""
    session = DummySession()
    payload = admin.RoleCreate(name="existing", description="Existing role")

    with patch("fundamental.api.routes.admin.RoleService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_role.side_effect = ValueError("role_already_exists")
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
            "fundamental.api.routes.admin.RoleService",
            "create_role",
            "488",
            {"payload": admin.RoleCreate(name="testrole", description="Test role")},
        ),
        (
            admin.create_device,
            admin.EReaderDeviceCreate(email="device@example.com"),
            "fundamental.api.routes.admin.EReaderService",
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
            "fundamental.api.routes.admin.EReaderService",
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
            "fundamental.api.routes.admin.LibraryService",
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
            "fundamental.api.routes.admin.LibraryService",
            "update_library",
            "1060",
            {"library_id": 1, "payload": admin.LibraryUpdate(name="Updated Library")},
        ),
        (
            admin.delete_library,
            None,
            "fundamental.api.routes.admin.LibraryService",
            "delete_library",
            "1096",
            {"library_id": 1},
        ),
        (
            admin.activate_library,
            None,
            "fundamental.api.routes.admin.LibraryService",
            "set_active_library",
            "1138",
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
            patch(
                "fundamental.api.routes.admin.UserRepository"
            ) as mock_user_repo_class,
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
                route_func(session, **call_kwargs)  # type: ignore[call-arg]
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

            with pytest.raises(ValueError, match="unexpected_error"):
                route_func(session, **call_kwargs)  # type: ignore[call-arg]


def test_list_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_roles returns all roles."""
    session = DummySession()
    role1 = Role(id=1, name="viewer", description="Viewer role")
    role2 = Role(id=2, name="editor", description="Editor role")

    with patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class:
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
    role = Role(id=1, name="viewer", description="Viewer role")

    with patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = role
        mock_repo_class.return_value = mock_repo

        result = admin.delete_role(session, role_id=1)
        assert result is None
        mock_repo.delete.assert_called_once_with(role)


def test_delete_role_not_found() -> None:
    """Test delete_role raises 404 when role not found."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class:
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
        patch("fundamental.api.routes.admin.RoleService") as mock_service_class,
        patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class,
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_service_class:
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
        patch("fundamental.api.routes.admin.RoleService") as mock_service_class,
        patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class,
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
        patch("fundamental.api.routes.admin.RoleService") as mock_service_class,
        patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class,
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

    with patch("fundamental.api.routes.admin.RoleService") as mock_service_class:
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
        patch("fundamental.api.routes.admin.RoleService") as mock_service_class,
        patch("fundamental.api.routes.admin.RoleRepository") as mock_repo_class,
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
    from fundamental.models.auth import Permission

    session = DummySession()
    perm1 = Permission(id=1, name="read", resource="books", action="read")
    perm2 = Permission(id=2, name="write", resource="books", action="write")

    with patch("fundamental.api.routes.admin.PermissionRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_by_resource.return_value = [perm1, perm2]
        mock_repo_class.return_value = mock_repo

        result = admin.list_permissions(session, resource="books")
        assert len(result) == 2
        mock_repo.list_by_resource.assert_called_once_with("books")


def test_list_permissions_without_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_permissions returns all permissions when resource not provided."""
    from fundamental.models.auth import Permission

    session = DummySession()
    perm1 = Permission(id=1, name="read", resource="books", action="read")
    perm2 = Permission(id=2, name="write", resource="authors", action="write")

    with patch("fundamental.api.routes.admin.PermissionRepository") as mock_repo_class:
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
        patch("fundamental.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("fundamental.api.routes.admin.EReaderService") as mock_service_class,
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

    with patch("fundamental.api.routes.admin.UserRepository") as mock_repo_class:
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
        patch("fundamental.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("fundamental.api.routes.admin.EReaderService") as mock_service_class,
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
        patch("fundamental.api.routes.admin.UserRepository") as mock_user_repo_class,
        patch("fundamental.api.routes.admin.EReaderService") as mock_service_class,
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

    with patch("fundamental.api.routes.admin.EReaderRepository") as mock_repo_class:
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

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_device.return_value = None
        mock_service_class.return_value = mock_service

        result = admin.delete_device(session, device_id=1)
        assert result is None
        mock_service.delete_device.assert_called_once_with(1)


def test_delete_device_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_device raises 404 when device not found."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.EReaderService") as mock_service_class:
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
        is_active=True,
    )
    library2 = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
        is_active=False,
    )

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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
        is_active=True,
    )

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_service_class.return_value = mock_service

        result = admin.get_active_library(session)
        assert result is not None
        assert result.name == "Active Library"


def test_get_active_library_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_active_library returns None when no active library."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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
        is_active=False,
    )

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
        is_active=False,
    )

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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
        is_active=True,
    )

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
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

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_library.return_value = None
        mock_service_class.return_value = mock_service

        result = admin.delete_library(session, library_id=1)
        assert result is None
        mock_service.delete_library.assert_called_once_with(1)


def test_delete_library_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_library raises 404 when library not found."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.delete_library.side_effect = ValueError("library_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.delete_library(session, library_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"


def test_activate_library_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test activate_library succeeds."""
    session = DummySession()
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.set_active_library.return_value = library
        mock_service_class.return_value = mock_service

        result = admin.activate_library(session, library_id=1)
        assert result.id == 1
        assert result.is_active is True


def test_activate_library_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test activate_library raises 404 when library not found."""
    session = DummySession()

    with patch("fundamental.api.routes.admin.LibraryService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.set_active_library.side_effect = ValueError("library_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            admin.activate_library(session, library_id=999)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"

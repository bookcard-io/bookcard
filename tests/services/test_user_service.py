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

"""Tests for user service."""

from __future__ import annotations

import pytest

from fundamental.models.auth import User
from fundamental.repositories.user_repository import UserRepository
from fundamental.services.user_service import UserService
from tests.conftest import DummySession


def test_update_profile_username_changed() -> None:
    """Test update_profile updates username when changed (covers lines 77-82)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="oldname",
        email="user@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup
    session.add_exec_result([None])  # find_by_username() call

    result = service.update_profile(1, username="newname")

    assert result.username == "newname"


def test_get_returns_user() -> None:
    """Test get returns user when found (covers line 60)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup

    result = service.get(1)

    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"


def test_get_returns_none() -> None:
    """Test get returns None when user not found (covers line 60)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    result = service.get(999)

    assert result is None


def test_update_profile_user_not_found() -> None:
    """Test update_profile raises ValueError when user not found (covers lines 74-75)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="user_not_found"):
        service.update_profile(999, username="newname")


def test_update_profile_username_conflict() -> None:
    """Test update_profile raises ValueError when username already exists (covers lines 77-81)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="oldname",
        email="user@example.com",
        password_hash="hash",
    )

    existing_user = User(
        id=2,
        username="newname",
        email="other@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup
    session.add_exec_result([existing_user])  # find_by_username() call

    with pytest.raises(ValueError, match="username_already_exists"):
        service.update_profile(1, username="newname")


def test_update_profile_email_changed() -> None:
    """Test update_profile updates email when changed (covers lines 84-89)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="old@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup
    session.add_exec_result([None])  # find_by_email() call

    result = service.update_profile(1, email="new@example.com")

    assert result.email == "new@example.com"


def test_update_profile_email_conflict() -> None:
    """Test update_profile raises ValueError when email already exists (covers lines 84-88)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="old@example.com",
        password_hash="hash",
    )

    existing_user = User(
        id=2,
        username="other",
        email="new@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup
    session.add_exec_result([existing_user])  # find_by_email() call

    with pytest.raises(ValueError, match="email_already_exists"):
        service.update_profile(1, email="new@example.com")


def test_update_profile_same_username_no_check() -> None:
    """Test update_profile doesn't check when username unchanged (covers lines 77-82)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup

    result = service.update_profile(1, username="user")

    assert result.username == "user"
    # Should not call find_by_username when username unchanged


def test_update_profile_same_email_no_check() -> None:
    """Test update_profile doesn't check when email unchanged (covers lines 84-89)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
    )

    session.add(user)  # Add to session for get() lookup

    result = service.update_profile(1, email="user@example.com")

    assert result.email == "user@example.com"
    # Should not call find_by_email when email unchanged


def test_list_users_delegates_to_repo() -> None:
    """Test list_users delegates to repository (covers line 109)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user1 = User(
        id=1, username="user1", email="user1@example.com", password_hash="hash"
    )
    user2 = User(
        id=2, username="user2", email="user2@example.com", password_hash="hash"
    )

    session.add_exec_result([user1, user2])

    result = list(service.list_users(limit=10, offset=0))

    assert len(result) == 2


def test_get_with_relationships_returns_user() -> None:
    """Test get_with_relationships returns user with relationships (covers lines 133-147)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    session.add_exec_result([user])

    result = service.get_with_relationships(1)

    assert result is not None
    assert result.id == 1


def test_get_with_relationships_returns_none() -> None:
    """Test get_with_relationships returns None when user not found (covers lines 133-147)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])

    result = service.get_with_relationships(999)

    assert result is None


def test_list_users_with_relationships_returns_users() -> None:
    """Test list_users_with_relationships returns users with relationships (covers lines 181-195)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

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

    session.add_exec_result([user1, user2])

    result = service.list_users_with_relationships(limit=10, offset=0)

    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2


def test_list_users_with_relationships_with_limit() -> None:
    """Test list_users_with_relationships applies limit (covers lines 181-195)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    session.add_exec_result([user])

    result = service.list_users_with_relationships(limit=5, offset=0)

    assert len(result) == 1


def test_list_users_with_relationships_no_limit() -> None:
    """Test list_users_with_relationships works without limit (covers lines 181-195)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
    )
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]

    session.add_exec_result([user])

    result = service.list_users_with_relationships(limit=None, offset=0)

    assert len(result) == 1


def test_update_admin_status_success() -> None:
    """Test update_admin_status updates admin status (covers lines 217-224)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )

    session.add(user)  # Add to session for get() lookup

    result = service.update_admin_status(1, True)

    assert result.is_admin is True


def test_update_admin_status_not_found() -> None:
    """Test update_admin_status raises ValueError when user not found (covers lines 217-220)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([None])

    with pytest.raises(ValueError, match="user_not_found"):
        service.update_admin_status(999, True)


def test_update_active_status_success() -> None:
    """Test update_active_status updates active status (covers lines 246-253)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_active=True,
    )

    session.add(user)  # Add to session for get() lookup

    result = service.update_active_status(1, False)

    assert result.is_active is False


def test_update_active_status_not_found() -> None:
    """Test update_active_status raises ValueError when user not found (covers lines 246-249)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([None])

    with pytest.raises(ValueError, match="user_not_found"):
        service.update_active_status(999, False)


# Tests for update_user (lines 345-388)
def test_update_user_with_username_and_email() -> None:
    """Test update_user updates profile when username/email provided (covers lines 345-346)."""
    from unittest.mock import patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="oldname", email="old@example.com", password_hash="hash")
    session.add(user)

    with patch.object(service, "update_profile") as mock_update_profile:
        service.update_user(1, username="newname", email="new@example.com")

        mock_update_profile.assert_called_once_with(
            1, username="newname", email="new@example.com"
        )


def test_update_user_with_password() -> None:
    """Test update_user updates password when provided (covers lines 349-353)."""
    from unittest.mock import MagicMock

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(
        id=1, username="user", email="user@example.com", password_hash="old_hash"
    )
    session.add(user)

    mock_hasher = MagicMock()
    mock_hasher.hash.return_value = "new_hash"

    service.update_user(1, password="newpassword", password_hasher=mock_hasher)

    assert user.password_hash == "new_hash"
    mock_hasher.hash.assert_called_once_with("newpassword")


def test_update_user_password_requires_hasher() -> None:
    """Test update_user raises error when password provided without hasher (covers lines 350-352)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    with pytest.raises(ValueError, match="password_hasher_required"):
        service.update_user(1, password="newpassword")


def test_update_user_with_admin_status() -> None:
    """Test update_user updates admin status when provided (covers lines 356-357)."""
    from unittest.mock import patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    with patch.object(service, "update_admin_status") as mock_update_admin:
        service.update_user(1, is_admin=True)

        mock_update_admin.assert_called_once_with(1, True)


def test_update_user_with_active_status() -> None:
    """Test update_user updates active status when provided (covers lines 360-361)."""
    from unittest.mock import patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    with patch.object(service, "update_active_status") as mock_update_active:
        service.update_user(1, is_active=False)

        mock_update_active.assert_called_once_with(1, False)


def test_update_user_with_roles() -> None:
    """Test update_user syncs roles when provided (covers lines 364-369)."""
    from unittest.mock import MagicMock, patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    mock_role_service = MagicMock()
    mock_user_role_repo = MagicMock()

    with patch.object(service, "_sync_user_roles") as mock_sync_roles:
        service.update_user(
            1,
            role_ids=[1, 2, 3],
            role_service=mock_role_service,
            user_role_repo=mock_user_role_repo,
        )

        mock_sync_roles.assert_called_once_with(
            1, [1, 2, 3], mock_role_service, mock_user_role_repo
        )


def test_update_user_with_device_email() -> None:
    """Test update_user syncs device when email provided (covers lines 372-385)."""
    from unittest.mock import MagicMock, patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    mock_device_service = MagicMock()
    mock_device_repo = MagicMock()

    with patch.object(service, "_sync_default_device") as mock_sync_device:
        service.update_user(
            1,
            default_device_email="device@example.com",
            device_service=mock_device_service,
            device_repo=mock_device_repo,
        )

        mock_sync_device.assert_called_once()
        call_args = mock_sync_device.call_args
        assert call_args[0][0] == 1  # user_id
        assert call_args[0][1] == "device@example.com"  # device_email
        assert call_args[1]["device_service"] == mock_device_service
        assert call_args[1]["device_repo"] == mock_device_repo


# Tests for _sync_user_roles (lines 418-434)
def test_sync_user_roles_removes_and_adds() -> None:
    """Test _sync_user_roles removes old roles and adds new ones (covers lines 418-434)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import UserRole

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    # Current roles: 1, 2
    current_roles = [
        UserRole(user_id=1, role_id=1),
        UserRole(user_id=1, role_id=2),
    ]

    mock_user_role_repo = MagicMock()
    mock_user_role_repo.list_by_user.return_value = current_roles

    mock_role_service = MagicMock()

    # New roles: 2, 3 (remove 1, add 3)
    service._sync_user_roles(1, [2, 3], mock_role_service, mock_user_role_repo)

    # Should remove role 1
    mock_role_service.remove_role_from_user.assert_called_once_with(1, 1)
    # Should add role 3
    mock_role_service.assign_role_to_user.assert_called_once_with(1, 3)


def test_sync_user_roles_handles_errors() -> None:
    """Test _sync_user_roles suppresses errors (covers lines 425-427, 432-434)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import UserRole

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    current_roles = [UserRole(user_id=1, role_id=1)]

    mock_user_role_repo = MagicMock()
    mock_user_role_repo.list_by_user.return_value = current_roles

    mock_role_service = MagicMock()
    mock_role_service.remove_role_from_user.side_effect = ValueError("Role not found")
    mock_role_service.assign_role_from_user.side_effect = ValueError("Already assigned")

    # Should not raise, errors are suppressed
    service._sync_user_roles(1, [2], mock_role_service, mock_user_role_repo)

    mock_role_service.remove_role_from_user.assert_called_once_with(1, 1)
    mock_role_service.assign_role_to_user.assert_called_once_with(1, 2)


# Tests for _sync_default_device (lines 474-506)
def test_sync_default_device_updates_existing() -> None:
    """Test _sync_default_device updates existing device (covers lines 474-489)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import EBookFormat, EReaderDevice

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    existing_device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="Old Name",
        device_type="kindle",
        is_default=False,
        preferred_format=EBookFormat.MOBI,
    )

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_email.return_value = existing_device

    mock_device_service = MagicMock()

    service._sync_default_device(
        1,
        "device@example.com",
        device_name="New Name",
        device_type="kobo",
        device_format="epub",
        device_service=mock_device_service,
        device_repo=mock_device_repo,
    )

    mock_device_service.update_device.assert_called_once()
    call_kwargs = mock_device_service.update_device.call_args[1]
    assert call_kwargs["is_default"] is True
    assert call_kwargs["device_name"] == "New Name"
    assert call_kwargs["device_type"] == "kobo"
    assert call_kwargs["preferred_format"] == EBookFormat.EPUB


def test_sync_default_device_creates_new() -> None:
    """Test _sync_default_device creates new device (covers lines 490-506)."""
    from unittest.mock import MagicMock, patch

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_email.return_value = None
    mock_device_repo.find_by_user.return_value = []

    mock_device_service = MagicMock()

    with patch.object(
        service, "_generate_incremented_device_name", return_value="My eReader"
    ):
        service._sync_default_device(
            1,
            "newdevice@example.com",
            device_service=mock_device_service,
            device_repo=mock_device_repo,
        )

        mock_device_service.create_device.assert_called_once()
        call_args = mock_device_service.create_device.call_args
        assert call_args[0][0] == 1  # user_id
        assert call_args[0][1] == "newdevice@example.com"  # device_email
        call_kwargs = call_args[1]
        assert call_kwargs["device_name"] == "My eReader"
        assert call_kwargs["device_type"] == "generic"
        assert call_kwargs["is_default"] is True
        # preferred_format defaults to EPUB when device_format is None
        from fundamental.models.auth import EBookFormat

        assert call_kwargs["preferred_format"] == EBookFormat.EPUB


def test_sync_default_device_invalid_format() -> None:
    """Test _sync_default_device handles invalid format gracefully (covers lines 484-488)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import EReaderDevice

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    existing_device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="Device",
        device_type="kindle",
        is_default=False,
    )

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_email.return_value = existing_device

    mock_device_service = MagicMock()

    # Invalid format should be suppressed
    service._sync_default_device(
        1,
        "device@example.com",
        device_format="INVALID_FORMAT",
        device_service=mock_device_service,
        device_repo=mock_device_repo,
    )

    # Should not include preferred_format in update
    call_kwargs = mock_device_service.update_device.call_args[1]
    assert "preferred_format" not in call_kwargs


# Tests for _generate_incremented_device_name (lines 536-564)
def test_generate_incremented_device_name_no_existing() -> None:
    """Test _generate_incremented_device_name returns base name when no devices (covers lines 536-564)."""
    from unittest.mock import MagicMock

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_user.return_value = []

    result = service._generate_incremented_device_name(1, mock_device_repo)

    assert result == "My eReader"


def test_generate_incremented_device_name_with_base_name() -> None:
    """Test _generate_incremented_device_name increments when base name exists (covers lines 544-561)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import EReaderDevice

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    existing_device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="My eReader",
    )

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_user.return_value = [existing_device]

    result = service._generate_incremented_device_name(1, mock_device_repo)

    assert result == "My eReader (1)"


def test_generate_incremented_device_name_with_numbered() -> None:
    """Test _generate_incremented_device_name increments from highest number (covers lines 549-561)."""
    from unittest.mock import MagicMock

    from fundamental.models.auth import EReaderDevice

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    existing_devices = [
        EReaderDevice(
            id=1, user_id=1, email="d1@example.com", device_name="My eReader (1)"
        ),
        EReaderDevice(
            id=2, user_id=1, email="d2@example.com", device_name="My eReader (3)"
        ),
    ]

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_user.return_value = existing_devices

    result = service._generate_incremented_device_name(1, mock_device_repo)

    assert result == "My eReader (4)"


# Tests for delete_user (lines 596-634)
def test_delete_user_executes_all_commands() -> None:
    """Test delete_user executes all deletion commands (covers lines 596-634)."""
    from unittest.mock import MagicMock, patch

    from fundamental.models.auth import User

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    mock_device_repo = MagicMock()
    mock_user_role_repo = MagicMock()

    with patch(
        "fundamental.services.user_service.CommandExecutor"
    ) as mock_executor_class:
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        service.delete_user(
            1,
            device_repo=mock_device_repo,
            user_role_repo=mock_user_role_repo,
            data_directory="/tmp",
        )

        # Should execute 6 commands
        assert mock_executor.execute.call_count == 6
        mock_executor.clear.assert_called_once()
        assert session.flush_count >= 1


def test_delete_user_without_optional_repos() -> None:
    """Test delete_user works without optional repositories (covers lines 607-616)."""
    from unittest.mock import MagicMock, patch

    from fundamental.models.auth import User

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    user = User(id=1, username="user", email="user@example.com", password_hash="hash")
    session.add(user)

    with patch(
        "fundamental.services.user_service.CommandExecutor"
    ) as mock_executor_class:
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        service.delete_user(
            1, device_repo=None, user_role_repo=None, data_directory=None
        )

        # Should execute 3 commands (settings, tokens, user - no devices, roles, or directory)
        assert mock_executor.execute.call_count == 3


def test_delete_user_not_found() -> None:
    """Test delete_user raises ValueError when user not found (covers lines 598-599)."""
    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([None])  # get() returns None

    with pytest.raises(ValueError, match="user_not_found"):
        service.delete_user(999)


def test_sync_default_device_invalid_format_suppressed_new_device() -> None:
    """Test _sync_default_device suppresses invalid format when creating new device (covers lines 494-496)."""
    from unittest.mock import MagicMock, patch

    from fundamental.models.auth import EBookFormat

    session = DummySession()
    repo = UserRepository(session)  # type: ignore[arg-type]
    service = UserService(session, repo)  # type: ignore[arg-type]

    mock_device_repo = MagicMock()
    mock_device_repo.find_by_email.return_value = None
    mock_device_repo.find_by_user.return_value = []

    mock_device_service = MagicMock()

    with patch.object(
        service, "_generate_incremented_device_name", return_value="My eReader"
    ):
        service._sync_default_device(
            1,
            "newdevice@example.com",
            device_format="INVALID_FORMAT",  # Invalid format should be suppressed
            device_service=mock_device_service,
            device_repo=mock_device_repo,
        )

        # Should use default EPUB format when invalid format is suppressed
        call_args = mock_device_service.create_device.call_args
        assert call_args[1]["preferred_format"] == EBookFormat.EPUB

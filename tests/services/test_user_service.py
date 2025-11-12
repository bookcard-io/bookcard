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

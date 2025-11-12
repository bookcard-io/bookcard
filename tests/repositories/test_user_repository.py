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

"""Tests for UserRepository query logic."""

from datetime import UTC, datetime

from tests.conftest import DummySession


def test_find_by_email_delegates_to_session(session: DummySession) -> None:
    """Test find_by_email queries by exact email match."""
    from fundamental.models.auth import User
    from fundamental.repositories.user_repository import UserRepository

    # Test actual repository to ensure coverage
    user_repo = UserRepository(session)  # type: ignore[arg-type]
    user = User(id=1, username="alice", email="alice@example.com", password_hash="hash")
    session.add_exec_result([user])

    found = user_repo.find_by_email("alice@example.com")
    assert found is not None
    assert found.email == "alice@example.com"
    session.add_exec_result([])
    assert user_repo.find_by_email("nonexistent@example.com") is None


def test_find_by_username_delegates_to_session(session: DummySession) -> None:
    """Test find_by_username queries by exact username match."""
    from fundamental.models.auth import User
    from fundamental.repositories.user_repository import UserRepository

    # Test actual repository to ensure coverage
    user_repo = UserRepository(session)  # type: ignore[arg-type]
    user = User(id=2, username="bob", email="bob@example.com", password_hash="hash")
    session.add_exec_result([user])

    found = user_repo.find_by_username("bob")
    assert found is not None
    assert found.username == "bob"
    session.add_exec_result([])
    assert user_repo.find_by_username("nonexistent") is None


def test_list_admins_filters_by_is_admin(session: DummySession) -> None:
    """Test list_admins returns only users with is_admin=True."""
    from fundamental.models.auth import User
    from fundamental.repositories.user_repository import UserRepository

    # Test actual repository to ensure coverage
    user_repo = UserRepository(session)  # type: ignore[arg-type]
    admin = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )
    session.add_exec_result([admin])

    result = list(user_repo.list_admins())
    assert len(result) == 1
    assert result[0].is_admin is True


def test_token_blacklist_is_blacklisted_true(session: DummySession) -> None:
    """Test is_blacklisted returns True when token is blacklisted (covers lines 83-84)."""
    from fundamental.models.auth import TokenBlacklist

    # Import the actual repository to ensure coverage
    from fundamental.repositories.user_repository import TokenBlacklistRepository

    repo = TokenBlacklistRepository(session)  # type: ignore[arg-type]

    blacklist_entry = TokenBlacklist(
        id=1,
        jti="test-jti-123",
        expires_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    session.add_exec_result([blacklist_entry])

    result = repo.is_blacklisted("test-jti-123")
    assert result is True


def test_token_blacklist_is_blacklisted_false(session: DummySession) -> None:
    """Test is_blacklisted returns False when token is not blacklisted (covers lines 83-84)."""
    from fundamental.repositories.user_repository import TokenBlacklistRepository

    repo = TokenBlacklistRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])  # No matching entry

    result = repo.is_blacklisted("non-existent-jti")
    assert result is False


def test_token_blacklist_add_to_blacklist(session: DummySession) -> None:
    """Test add_to_blacklist creates and returns blacklist entry (covers lines 101-107)."""
    from fundamental.repositories.user_repository import TokenBlacklistRepository

    repo = TokenBlacklistRepository(session)  # type: ignore[arg-type]

    expires_at = datetime.now(UTC)
    result = repo.add_to_blacklist("test-jti-456", expires_at)

    assert result.jti == "test-jti-456"
    assert result.expires_at == expires_at
    assert result.created_at is not None
    assert result in session.added

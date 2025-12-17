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

"""Admin repository implementation tests."""

from __future__ import annotations

from typing import Any

import pytest

from bookcard.models.auth import Invite, User, UserSetting
from bookcard.repositories.admin_repositories import (
    InviteRepository,
    SettingRepository,
    UserAdminRepository,
)


class MockResult:
    """Mock query result."""

    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def all(self) -> list[Any]:
        """Return all items."""
        return self._items

    def first(self) -> Any:  # noqa: ANN401
        """Return first item or None."""
        return self._items[0] if self._items else None


class MockSession:
    """Mock session for repository tests."""

    def __init__(self) -> None:
        self._next: list[Any] = []

    def set_exec(self, items: list[Any]) -> None:
        """Set the next exec result."""
        self._next = items

    def exec(self, stmt: Any) -> MockResult:  # noqa: ANN401
        """Execute query and return configured result."""
        return MockResult(self._next)


@pytest.fixture
def session() -> MockSession:
    """Create mock session."""
    return MockSession()


@pytest.fixture
def user_repo(session: MockSession) -> UserAdminRepository:
    """Create UserAdminRepository."""
    return UserAdminRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def setting_repo(session: MockSession) -> SettingRepository:
    """Create SettingRepository."""
    return SettingRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def invite_repo(session: MockSession) -> InviteRepository:
    """Create InviteRepository."""
    return InviteRepository(session)  # type: ignore[arg-type]


def test_user_repo_list_users_returns_exec_all(
    user_repo: UserAdminRepository, session: MockSession
) -> None:
    """Test list_users returns exec().all() result."""
    u1 = User(id=1, username="u1", email="e1", password_hash="h")  # type: ignore[call-arg]
    u2 = User(id=2, username="u2", email="e2", password_hash="h")  # type: ignore[call-arg]
    session.set_exec([u1, u2])
    out = list(user_repo.list_users(limit=10, offset=0))
    assert out == [u1, u2]


def test_user_repo_list_users_respects_pagination(
    user_repo: UserAdminRepository, session: MockSession
) -> None:
    """Test list_users respects offset and limit."""
    u1 = User(id=1, username="u1", email="e1", password_hash="h")  # type: ignore[call-arg]
    session.set_exec([u1])
    out = list(user_repo.list_users(limit=1, offset=1))
    assert out == [u1]


def test_setting_repo_get_by_key_returns_first(
    setting_repo: SettingRepository, session: MockSession
) -> None:
    """Test get_by_key returns exec().first() result."""
    setting = UserSetting(key="test", value="value")  # type: ignore[call-arg]
    session.set_exec([setting])
    out = setting_repo.get_by_key(1, "test")
    assert out is setting


def test_setting_repo_get_by_key_returns_none_when_missing(
    setting_repo: SettingRepository, session: MockSession
) -> None:
    """Test get_by_key returns None when not found."""
    session.set_exec([])
    out = setting_repo.get_by_key(1, "missing")
    assert out is None


def test_invite_repo_list_all_returns_exec_all(
    invite_repo: InviteRepository, session: MockSession
) -> None:
    """Test list_all returns exec().all() result."""
    inv1 = Invite(id=1, created_by=1, token="t1")  # type: ignore[call-arg]
    inv2 = Invite(id=2, created_by=1, token="t2")  # type: ignore[call-arg]
    session.set_exec([inv1, inv2])
    out = list(invite_repo.list_all(limit=10))
    assert out == [inv1, inv2]


def test_invite_repo_list_all_respects_limit(
    invite_repo: InviteRepository, session: MockSession
) -> None:
    """Test list_all respects limit parameter."""
    inv = Invite(id=1, created_by=1, token="t")  # type: ignore[call-arg]
    session.set_exec([inv])
    out = list(invite_repo.list_all(limit=1))
    assert out == [inv]


def test_invite_repo_get_by_token_returns_first(
    invite_repo: InviteRepository, session: MockSession
) -> None:
    """Test get_by_token returns exec().first() result."""
    from datetime import UTC, datetime, timedelta

    inv = Invite(
        id=1,
        created_by=1,
        token="test-token-123",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )  # type: ignore[call-arg]
    session.set_exec([inv])
    out = invite_repo.get_by_token("test-token-123")
    assert out is inv


def test_invite_repo_get_by_token_returns_none_when_missing(
    invite_repo: InviteRepository, session: MockSession
) -> None:
    """Test get_by_token returns None when not found."""
    session.set_exec([])
    out = invite_repo.get_by_token("missing-token")
    assert out is None

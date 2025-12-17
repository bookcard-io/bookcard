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

from __future__ import annotations

from typing import Any

import pytest

from bookcard.models.auth import User
from bookcard.repositories.user_repository import UserRepository


class MockResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def first(self) -> Any | None:  # noqa: ANN401
        return self._items[0] if self._items else None

    def all(self) -> list[Any]:
        return self._items


class MockSession:
    def __init__(self) -> None:
        self._next_exec_result: list[Any] = []

    def set_exec_result(self, items: list[Any]) -> None:
        self._next_exec_result = items

    def exec(self, stmt: Any) -> MockResult:  # noqa: ANN401
        return MockResult(self._next_exec_result)


@pytest.fixture
def session() -> MockSession:
    return MockSession()


@pytest.fixture
def repo(session: MockSession) -> UserRepository:
    return UserRepository(session)  # type: ignore[arg-type]


def test_find_by_email_uses_first(repo: UserRepository, session: MockSession) -> None:
    user = User(username="alice", email="alice@example.com", password_hash="x")
    session.set_exec_result([user])
    found = repo.find_by_email("alice@example.com")
    assert found is user


def test_find_by_username_uses_first(
    repo: UserRepository, session: MockSession
) -> None:
    user = User(username="bob", email="b@example.com", password_hash="x")
    session.set_exec_result([user])
    found = repo.find_by_username("bob")
    assert found is user


def test_list_admins_uses_all(repo: UserRepository, session: MockSession) -> None:
    admin = User(
        username="root", email="root@example.com", password_hash="x", is_admin=True
    )
    session.set_exec_result([admin])
    results = list(repo.list_admins())
    assert results == [admin]

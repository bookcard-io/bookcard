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

from __future__ import annotations

from typing import Any

import pytest

from fundamental.models.auth import User
from fundamental.repositories.user_repository import UserRepository


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

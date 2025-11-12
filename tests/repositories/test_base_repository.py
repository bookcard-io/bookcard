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

from typing import Any, TypeVar

import pytest
from sqlmodel import Field, SQLModel

from fundamental.repositories.base import Repository


class MockResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def all(self) -> list[Any]:
        return self._items


T = TypeVar("T")


class MockSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.refreshed: list[Any] = []
        self.flush_count: int = 0
        self._get_map: dict[tuple[type[object], int], object] = {}
        self._next_exec_result: list[Any] = []

    def add(self, entity: Any) -> None:  # noqa: ANN401
        self.added.append(entity)

    def delete(self, entity: Any) -> None:  # noqa: ANN401
        self.deleted.append(entity)

    def refresh(self, entity: Any) -> None:  # noqa: ANN401
        self.refreshed.append(entity)

    def flush(self) -> None:
        self.flush_count += 1

    def get(self, model_type: type[T], entity_id: int) -> T | None:
        value = self._get_map.get((model_type, entity_id))
        return value if isinstance(value, model_type) else None

    def set_get(self, model_type: type[T], entity_id: int, value: T) -> None:
        self._get_map[model_type, entity_id] = value

    def set_exec_result(self, items: list[Any]) -> None:
        self._next_exec_result = items

    def exec(self, stmt: Any) -> MockResult:  # noqa: ANN401
        return MockResult(self._next_exec_result)


class Thing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, index=True)


@pytest.fixture
def session() -> MockSession:
    return MockSession()


@pytest.fixture
def repo(session: MockSession) -> Repository[Thing]:
    return Repository(session, Thing)  # type: ignore[type-arg]


def test_add_returns_entity_and_calls_session_add(
    repo: Repository[Thing], session: MockSession
) -> None:
    entity = Thing(id=1, name="t1")
    returned = repo.add(entity)
    assert returned is entity
    assert entity in session.added


def test_get_returns_value_from_session(
    repo: Repository[Thing], session: MockSession
) -> None:
    entity = Thing(id=2, name="t2")
    session.set_get(Thing, 2, entity)
    assert repo.get(2) is entity
    assert repo.get(999) is None


def test_list_without_limit_executes_query_and_returns_all(
    repo: Repository[Thing], session: MockSession
) -> None:
    items = [Thing(id=1, name="a"), Thing(id=2, name="b")]
    session.set_exec_result(items)
    results = list(repo.list())
    assert results == items


def test_list_with_limit_executes_query_and_returns_all(
    repo: Repository[Thing], session: MockSession
) -> None:
    items = [Thing(id=3, name="c"), Thing(id=4, name="d")]
    session.set_exec_result(items)
    results = list(repo.list(limit=1, offset=0))
    assert results == items


def test_delete_calls_session_delete(
    repo: Repository[Thing], session: MockSession
) -> None:
    entity = Thing(id=10, name="z")
    repo.delete(entity)
    assert entity in session.deleted


def test_flush_calls_session_flush(
    repo: Repository[Thing], session: MockSession
) -> None:
    repo.flush()
    assert session.flush_count == 1


def test_refresh_calls_session_refresh_and_returns_entity(
    repo: Repository[Thing], session: MockSession
) -> None:
    entity = Thing(id=20, name="y")
    returned = repo.refresh(entity)
    assert returned is entity
    assert entity in session.refreshed

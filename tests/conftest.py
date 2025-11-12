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

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest

# Ensure required application environment variables are available during test import
os.environ.setdefault("FUNDAMENTAL_JWT_SECRET", "test-secret")
os.environ.setdefault("FUNDAMENTAL_JWT_ALG", "HS256")
os.environ.setdefault("FUNDAMENTAL_JWT_EXPIRES_MIN", "15")
os.environ.setdefault("FUNDAMENTAL_DATABASE_URL", "sqlite:///fundamental.db")
os.environ.setdefault("FUNDAMENTAL_ALEMBIC_ENABLED", "false")
os.environ.setdefault("FUNDAMENTAL_ECHO_SQL", "false")


class MockResult:
    """Mock query result for session.exec()."""

    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def all(self) -> list[Any]:
        """Return all items."""
        return self._items

    def first(self) -> Any | None:  # noqa: ANN401
        """Return first item or None if empty."""
        return self._items[0] if self._items else None

    def one(self) -> Any:  # noqa: ANN401
        """Return single item, raise if not exactly one.

        Unwraps single-element tuples (common in SQL count queries).
        """
        if len(self._items) != 1:
            msg = f"Expected exactly one result, got {len(self._items)}"
            raise ValueError(msg)
        item = self._items[0]
        # Unwrap single-element tuples (e.g., (42,) -> 42)
        if isinstance(item, tuple) and len(item) == 1:
            return item[0]
        return item


class DummySession:
    """In-memory stand-in for `sqlmodel.Session` used by services.

    Tracks calls to `add`, `flush`, `delete`, `refresh` without touching a DB.
    Auto-assigns incremental integer `id` on `flush()` for added entities that
    expose an `id` attribute set to a falsey value.
    Supports `exec()` for SQL query mocking.
    Supports `get(model_class, id)` for entity lookups.
    """

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.refreshed: list[Any] = []
        self.flush_count: int = 0
        self._next_id: int = 1
        self._exec_results: list[list[Any]] = []
        # Track entities by model class and id for get() lookups
        self._entities_by_class_and_id: dict[type[Any], dict[int, Any]] = {}

    def add(self, entity: Any) -> None:  # noqa: ANN401
        """Record entity addition to the session."""
        self.added.append(entity)
        # Track entity for get() lookups
        if hasattr(entity, "id") and entity.id is not None:
            entity_type = type(entity)
            if entity_type not in self._entities_by_class_and_id:
                self._entities_by_class_and_id[entity_type] = {}
            self._entities_by_class_and_id[entity_type][entity.id] = entity

    def delete(self, entity: Any) -> None:  # noqa: ANN401
        """Record entity deletion from the session."""
        self.deleted.append(entity)

    def refresh(self, entity: Any) -> None:  # noqa: ANN401
        """Record entity refresh from the session."""
        self.refreshed.append(entity)

    def flush(self) -> None:
        """Simulate a flush assigning auto-increment ids."""
        self.flush_count += 1
        for entity in self.added:
            # Assign an auto-increment id if missing
            if hasattr(entity, "id") and not entity.id:
                entity.id = self._next_id
                self._next_id += 1
                # Track entity for get() lookups after id assignment
                entity_type = type(entity)
                if entity_type not in self._entities_by_class_and_id:
                    self._entities_by_class_and_id[entity_type] = {}
                self._entities_by_class_and_id[entity_type][entity.id] = entity

    def commit(self) -> None:
        """No-op commit to mimic real Session behavior in tests."""
        # Intentionally do nothing
        return

    def rollback(self) -> None:
        """No-op rollback to mimic real Session behavior in tests."""
        # Intentionally do nothing
        return

    def get(self, model_class: type[Any], entity_id: int) -> Any | None:  # noqa: ANN401
        """Get entity by model class and id.

        Parameters
        ----------
        model_class : type
            Model class to look up.
        entity_id : int
            Entity id.

        Returns
        -------
        Any | None
            Entity if found, None otherwise.
        """
        if model_class in self._entities_by_class_and_id:
            return self._entities_by_class_and_id[model_class].get(entity_id)
        return None

    def set_exec_result(self, result: list[Any]) -> None:
        """Configure the next result for exec() calls."""
        self._exec_results = [result]

    def add_exec_result(self, result: list[Any]) -> None:
        """Add a result that will be returned on the next exec() call."""
        self._exec_results.append(result)

    def exec(self, stmt: Any) -> MockResult:  # noqa: ANN401
        """Execute a query and return configured result."""
        if not self._exec_results:
            return MockResult([])
        return MockResult(self._exec_results.pop(0))

    def close(self) -> None:
        """Simulate closing the session."""


@dataclass
class InMemoryUser:
    """Simple user record used by in-memory repositories."""

    id: int | None = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_admin: bool = False
    last_login: datetime | None = None
    profile_picture: str | None = None


class InMemoryUserRepository:
    """Minimal user repository stub used to simulate persistence logic."""

    def __init__(self) -> None:
        self._by_id: dict[int, InMemoryUser] = {}
        self._by_username: dict[str, InMemoryUser] = {}
        self._by_email: dict[str, InMemoryUser] = {}

    def seed(self, user: InMemoryUser) -> None:
        """Insert or replace a user into the in-memory store."""
        if user.id is None:
            raise ValueError("seeded user must have an id")
        self._by_id[user.id] = user
        self._by_username[user.username] = user
        self._by_email[user.email] = user

    # Service-facing API
    def get(self, user_id: int) -> InMemoryUser | None:
        """Return user by id if present."""
        return self._by_id.get(user_id)

    def find_by_username(self, username: str) -> InMemoryUser | None:
        """Return user by username if present."""
        return self._by_username.get(username)

    def find_by_email(self, email: str) -> InMemoryUser | None:
        """Return user by email if present."""
        return self._by_email.get(email)


class FakeHasher:
    """Deterministic password hasher for unit tests."""

    def hash(self, password: str) -> str:
        """Return a predictable hash string for assertions."""
        return f"hash({password})"

    def verify(self, password: str, password_hash: str) -> bool:
        """Verify by recomputing the predictable hash string."""
        return password_hash == f"hash({password})"


class FakeJWTManager:
    """Non-cryptographic token builder for tests."""

    def create_access_token(
        self, subject: str, extra_claims: dict | None = None
    ) -> str:
        """Return a stable token string composed from inputs."""
        claims_part = (
            ""
            if not extra_claims
            else ",".join(f"{k}={v}" for k, v in sorted(extra_claims.items()))
        )
        return f"token(sub={subject};{claims_part})"


@pytest.fixture
def session() -> DummySession:
    return DummySession()


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def fake_hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def fake_jwt() -> FakeJWTManager:
    return FakeJWTManager()


@pytest.fixture
def user_factory() -> Callable[..., InMemoryUser]:
    def _make(
        *,
        user_id: int | None = None,
        username: str = "user",
        email: str = "user@example.com",
        password_hash: str = "",
        is_admin: bool = False,
    ) -> InMemoryUser:
        return InMemoryUser(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
        )

    return _make

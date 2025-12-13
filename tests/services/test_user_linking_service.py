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

"""Tests for UserLinkingService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.auth import User
from fundamental.services.user_linking_service import UserLinkingService
from tests.conftest import DummySession


class _StubUserRepo:
    def __init__(self) -> None:
        self.by_sub: dict[str, User] = {}
        self.by_email: dict[str, User] = {}
        self.by_username: dict[str, User] = {}

    def find_by_keycloak_sub(self, keycloak_sub: str) -> User | None:
        return self.by_sub.get(keycloak_sub)

    def find_by_email(self, email: str) -> User | None:
        return self.by_email.get(email)

    def find_by_username(self, username: str) -> User | None:
        return self.by_username.get(username)


def test_find_or_create_keycloak_user_missing_sub_raises() -> None:
    """Missing `sub` should raise a ValueError."""
    repo = _StubUserRepo()
    hasher = MagicMock()
    service = UserLinkingService(repo, hasher)  # type: ignore[arg-type]
    session = DummySession()

    with pytest.raises(ValueError, match="keycloak_userinfo_missing_sub"):
        service.find_or_create_keycloak_user(userinfo={}, session=session)  # type: ignore[arg-type]


def test_find_or_create_keycloak_user_links_existing_user_by_email() -> None:
    """Existing user found by email should be linked with keycloak_sub."""
    repo = _StubUserRepo()
    hasher = MagicMock()
    service = UserLinkingService(repo, hasher)  # type: ignore[arg-type]
    session = DummySession()

    user = User(
        id=1,
        username="alice",
        email="alice@example.com",
        password_hash="hash",
        keycloak_sub=None,
    )
    repo.by_email[user.email] = user

    linked = service.find_or_create_keycloak_user(
        userinfo={"sub": "kc-sub-1", "email": "alice@example.com"},
        session=session,  # type: ignore[arg-type]
    )

    assert linked is user
    assert linked.keycloak_sub == "kc-sub-1"
    assert session.flush_count > 0


def test_find_or_create_keycloak_user_creates_new_user() -> None:
    """New Keycloak user should create a local user with keycloak_sub."""
    repo = _StubUserRepo()

    hasher = MagicMock()
    hasher.hash.return_value = "hashed"
    service = UserLinkingService(repo, hasher)  # type: ignore[arg-type]
    session = DummySession()
    # Configure count query result: 0 users in system
    # SQLAlchemy count queries return tuples, e.g., (0,)
    session.set_exec_result([(0,)])

    created = service.find_or_create_keycloak_user(
        userinfo={
            "sub": "kc-sub-2",
            "email": "bob@example.com",
            "preferred_username": "bob",
            "name": "Bob Builder",
        },
        session=session,  # type: ignore[arg-type]
    )

    assert created.keycloak_sub == "kc-sub-2"
    assert created.email == "bob@example.com"
    assert created.username.startswith("bob")
    assert created.password_hash == "hashed"
    assert created.full_name == "Bob Builder"
    assert session.added
    assert session.flush_count > 0


def test_find_or_create_keycloak_user_username_collision_adds_suffix() -> None:
    """Username collision should append a numeric suffix."""
    repo = _StubUserRepo()
    repo.by_username["chris"] = User(
        id=1, username="chris", email="c1@example.com", password_hash="hash"
    )

    hasher = MagicMock()
    hasher.hash.return_value = "hashed"
    service = UserLinkingService(repo, hasher)  # type: ignore[arg-type]
    session = DummySession()
    # Configure count query result: 0 users in system (repo user doesn't count)
    # SQLAlchemy count queries return tuples, e.g., (0,)
    session.set_exec_result([(0,)])

    created = service.find_or_create_keycloak_user(
        # Avoid linking by username by omitting preferred_username, while still
        # forcing a collision via the email local-part.
        userinfo={"sub": "kc-sub-3", "email": "chris@example.com"},
        session=session,  # type: ignore[arg-type]
    )

    assert created.username.startswith("chris-")
    assert created.keycloak_sub == "kc-sub-3"

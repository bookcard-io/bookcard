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

"""Tests for authentication service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from bookcard.models.auth import Invite, User
from bookcard.services.authentication_service import AuthenticationService, AuthError
from tests.conftest import DummySession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session() -> DummySession:
    """Return a fresh DummySession for each test."""
    return DummySession()


@pytest.fixture
def user_repo() -> MagicMock:
    """Return a mock UserRepository."""
    return MagicMock(spec=["find_by_username", "find_by_email", "get"])


@pytest.fixture
def invite_repo() -> MagicMock:
    """Return a mock InviteRepository."""
    return MagicMock(spec=["get_by_token"])


@pytest.fixture
def hasher() -> MagicMock:
    """Return a mock PasswordHasher."""
    mock = MagicMock(spec=["hash", "verify"])
    mock.hash.return_value = "hashed_password"
    mock.verify.return_value = True
    return mock


@pytest.fixture
def jwt() -> MagicMock:
    """Return a mock JWTManager."""
    mock = MagicMock(spec=["create_access_token"])
    mock.create_access_token.return_value = "test_token"
    return mock


@pytest.fixture
def service(
    session: DummySession,
    user_repo: MagicMock,
    invite_repo: MagicMock,
    hasher: MagicMock,
    jwt: MagicMock,
) -> AuthenticationService:
    """Return an AuthenticationService with mocked dependencies."""
    return AuthenticationService(
        session=session,  # type: ignore[arg-type]
        user_repo=user_repo,
        invite_repo=invite_repo,
        hasher=hasher,
        jwt=jwt,
    )


@pytest.fixture
def existing_user() -> User:
    """Return a sample user for tests."""
    return User(
        id=1,
        username="existinguser",
        email="existing@example.com",
        password_hash="hashed",
        is_admin=False,
    )


# ---------------------------------------------------------------------------
# register_user tests
# ---------------------------------------------------------------------------


class TestRegisterUser:
    """Tests for AuthenticationService.register_user."""

    def test_register_user_success(
        self,
        service: AuthenticationService,
        session: DummySession,
        user_repo: MagicMock,
        hasher: MagicMock,
        jwt: MagicMock,
    ) -> None:
        """Register succeeds when username and email are available."""
        user_repo.find_by_username.return_value = None
        user_repo.find_by_email.return_value = None

        user, token = service.register_user("newuser", "new@example.com", "password123")

        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.password_hash == "hashed_password"
        assert token == "test_token"
        assert user in session.added
        assert session.flush_count == 1
        hasher.hash.assert_called_once_with("password123")
        jwt.create_access_token.assert_called_once()

    def test_register_user_username_exists(
        self,
        service: AuthenticationService,
        user_repo: MagicMock,
        existing_user: User,
    ) -> None:
        """Register fails when username already exists."""
        user_repo.find_by_username.return_value = existing_user

        with pytest.raises(ValueError, match=AuthError.USERNAME_EXISTS):
            service.register_user("existinguser", "new@example.com", "password123")

    def test_register_user_email_exists(
        self,
        service: AuthenticationService,
        user_repo: MagicMock,
        existing_user: User,
    ) -> None:
        """Register fails when email already exists."""
        user_repo.find_by_username.return_value = None
        user_repo.find_by_email.return_value = existing_user

        with pytest.raises(ValueError, match=AuthError.EMAIL_EXISTS):
            service.register_user("newuser", "existing@example.com", "password123")


# ---------------------------------------------------------------------------
# login_user tests
# ---------------------------------------------------------------------------


class TestLoginUser:
    """Tests for AuthenticationService.login_user."""

    def test_login_by_username_success(
        self,
        service: AuthenticationService,
        session: DummySession,
        user_repo: MagicMock,
        hasher: MagicMock,
        jwt: MagicMock,
        existing_user: User,
    ) -> None:
        """Login succeeds with valid username and password."""
        user_repo.find_by_username.return_value = existing_user
        hasher.verify.return_value = True

        user, token = service.login_user("existinguser", "correct_password")

        assert user.id == 1
        assert token == "test_token"
        assert user.last_login is not None
        assert session.flush_count == 1
        hasher.verify.assert_called_once_with("correct_password", "hashed")

    def test_login_by_email_success(
        self,
        service: AuthenticationService,
        user_repo: MagicMock,
        hasher: MagicMock,
        existing_user: User,
    ) -> None:
        """Login succeeds with valid email and password."""
        user_repo.find_by_username.return_value = None
        user_repo.find_by_email.return_value = existing_user
        hasher.verify.return_value = True

        user, token = service.login_user("existing@example.com", "correct_password")

        assert user.id == 1
        assert token == "test_token"

    def test_login_user_not_found(
        self,
        service: AuthenticationService,
        user_repo: MagicMock,
    ) -> None:
        """Login fails when user not found by username or email."""
        user_repo.find_by_username.return_value = None
        user_repo.find_by_email.return_value = None

        with pytest.raises(ValueError, match=AuthError.INVALID_CREDENTIALS):
            service.login_user("unknown", "password")

    def test_login_invalid_password(
        self,
        service: AuthenticationService,
        user_repo: MagicMock,
        hasher: MagicMock,
        existing_user: User,
    ) -> None:
        """Login fails when password is incorrect."""
        user_repo.find_by_username.return_value = existing_user
        hasher.verify.return_value = False

        with pytest.raises(ValueError, match=AuthError.INVALID_CREDENTIALS):
            service.login_user("existinguser", "wrong_password")


# ---------------------------------------------------------------------------
# validate_invite_token tests
# ---------------------------------------------------------------------------


class TestValidateInviteToken:
    """Tests for AuthenticationService.validate_invite_token."""

    def test_validate_invite_token_success(
        self,
        service: AuthenticationService,
        invite_repo: MagicMock,
    ) -> None:
        """Validation succeeds for valid, unexpired, unused invite."""
        invite = MagicMock(spec=Invite)
        invite.expires_at = datetime.now(UTC) + timedelta(days=1)
        invite.used_by = None
        invite_repo.get_by_token.return_value = invite

        result = service.validate_invite_token("valid_token")

        assert result is True
        invite_repo.get_by_token.assert_called_once_with("valid_token")

    def test_validate_invite_token_not_found(
        self,
        service: AuthenticationService,
        invite_repo: MagicMock,
    ) -> None:
        """Validation fails when invite token not found."""
        invite_repo.get_by_token.return_value = None

        with pytest.raises(ValueError, match=AuthError.INVALID_INVITE):
            service.validate_invite_token("unknown_token")

    def test_validate_invite_token_expired(
        self,
        service: AuthenticationService,
        invite_repo: MagicMock,
    ) -> None:
        """Validation fails when invite token is expired."""
        invite = MagicMock(spec=Invite)
        invite.expires_at = datetime.now(UTC) - timedelta(days=1)
        invite.used_by = None
        invite_repo.get_by_token.return_value = invite

        with pytest.raises(ValueError, match=AuthError.INVITE_EXPIRED):
            service.validate_invite_token("expired_token")

    def test_validate_invite_token_already_used(
        self,
        service: AuthenticationService,
        invite_repo: MagicMock,
    ) -> None:
        """Validation fails when invite token is already used."""
        invite = MagicMock(spec=Invite)
        invite.expires_at = datetime.now(UTC) + timedelta(days=1)
        invite.used_by = 42  # Already used
        invite_repo.get_by_token.return_value = invite

        with pytest.raises(ValueError, match=AuthError.INVITE_ALREADY_USED):
            service.validate_invite_token("used_token")

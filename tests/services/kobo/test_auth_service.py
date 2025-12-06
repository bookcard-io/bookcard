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

"""Tests for KoboAuthService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from fundamental.models.auth import User
from fundamental.models.kobo import KoboAuthToken
from fundamental.services.kobo.auth_service import KoboAuthService

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_auth_token_repo() -> MagicMock:
    """Create a mock KoboAuthTokenRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_id = MagicMock(return_value=None)
    repo.find_by_token = MagicMock(return_value=None)
    repo.delete_by_user_id = MagicMock()
    repo.add = MagicMock()
    return repo


@pytest.fixture
def mock_user_repo() -> MagicMock:
    """Create a mock UserRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.get = MagicMock(return_value=None)
    return repo


@pytest.fixture
def user() -> User:
    """Create a test user.

    Returns
    -------
    User
        User instance.
    """
    return User(id=1, username="testuser", email="test@example.com")


@pytest.fixture
def auth_service(
    session: DummySession,
    mock_auth_token_repo: MagicMock,
    mock_user_repo: MagicMock,
) -> KoboAuthService:
    """Create KoboAuthService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    mock_user_repo : MagicMock
        Mock user repository.

    Returns
    -------
    KoboAuthService
        Service instance.
    """
    return KoboAuthService(
        session,  # type: ignore[arg-type]
        mock_auth_token_repo,
        mock_user_repo,
    )


# ============================================================================
# Tests for KoboAuthService.__init__
# ============================================================================


def test_init(
    session: DummySession,
    mock_auth_token_repo: MagicMock,
    mock_user_repo: MagicMock,
) -> None:
    """Test KoboAuthService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    mock_user_repo : MagicMock
        Mock user repository.
    """
    service = KoboAuthService(
        session,  # type: ignore[arg-type]
        mock_auth_token_repo,
        mock_user_repo,
    )
    assert service._session == session
    assert service._auth_token_repo == mock_auth_token_repo
    assert service._user_repo == mock_user_repo


# ============================================================================
# Tests for KoboAuthService.generate_auth_token
# ============================================================================


def test_generate_auth_token_new_token(
    auth_service: KoboAuthService,
    mock_user_repo: MagicMock,
    mock_auth_token_repo: MagicMock,
    user: User,
    session: DummySession,
) -> None:
    """Test generating a new auth token when none exists.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_user_repo : MagicMock
        Mock user repository.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    user : User
        Test user.
    session : DummySession
        Dummy session instance.
    """
    mock_user_repo.get.return_value = user
    mock_auth_token_repo.find_by_user_id.return_value = None

    token = auth_service.generate_auth_token(user_id=1)

    assert token is not None
    assert len(token) == 64  # 32 bytes = 64 hex characters
    mock_user_repo.get.assert_called_once_with(1)
    mock_auth_token_repo.find_by_user_id.assert_called_once_with(1)
    mock_auth_token_repo.add.assert_called_once()
    assert session.flush_count == 1


def test_generate_auth_token_existing_token(
    auth_service: KoboAuthService,
    mock_user_repo: MagicMock,
    mock_auth_token_repo: MagicMock,
    user: User,
) -> None:
    """Test returning existing auth token when one exists.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_user_repo : MagicMock
        Mock user repository.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    user : User
        Test user.
    """
    existing_token = KoboAuthToken(
        id=1,
        user_id=1,
        auth_token="existing_token_hex_string_64_chars_long_12345678901234567890",
    )
    mock_user_repo.get.return_value = user
    mock_auth_token_repo.find_by_user_id.return_value = existing_token

    token = auth_service.generate_auth_token(user_id=1)

    assert token == existing_token.auth_token
    mock_user_repo.get.assert_called_once_with(1)
    mock_auth_token_repo.find_by_user_id.assert_called_once_with(1)
    mock_auth_token_repo.add.assert_not_called()


def test_generate_auth_token_user_not_found(
    auth_service: KoboAuthService,
    mock_user_repo: MagicMock,
) -> None:
    """Test generating token when user does not exist.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_user_repo : MagicMock
        Mock user repository.
    """
    mock_user_repo.get.return_value = None

    with pytest.raises(ValueError, match="User 1 not found"):
        auth_service.generate_auth_token(user_id=1)

    mock_user_repo.get.assert_called_once_with(1)


# ============================================================================
# Tests for KoboAuthService.validate_auth_token
# ============================================================================


def test_validate_auth_token_valid(
    auth_service: KoboAuthService,
    mock_auth_token_repo: MagicMock,
    mock_user_repo: MagicMock,
    user: User,
) -> None:
    """Test validating a valid auth token.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    mock_user_repo : MagicMock
        Mock user repository.
    user : User
        Test user.
    """
    auth_token = KoboAuthToken(id=1, user_id=1, auth_token="test_token")
    mock_auth_token_repo.find_by_token.return_value = auth_token
    mock_user_repo.get.return_value = user

    result = auth_service.validate_auth_token("test_token")

    assert result == user
    mock_auth_token_repo.find_by_token.assert_called_once_with("test_token")
    mock_user_repo.get.assert_called_once_with(1)


def test_validate_auth_token_invalid(
    auth_service: KoboAuthService,
    mock_auth_token_repo: MagicMock,
) -> None:
    """Test validating an invalid auth token.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    """
    mock_auth_token_repo.find_by_token.return_value = None

    result = auth_service.validate_auth_token("invalid_token")

    assert result is None
    mock_auth_token_repo.find_by_token.assert_called_once_with("invalid_token")


def test_validate_auth_token_user_not_found(
    auth_service: KoboAuthService,
    mock_auth_token_repo: MagicMock,
    mock_user_repo: MagicMock,
) -> None:
    """Test validating token when user does not exist.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    mock_user_repo : MagicMock
        Mock user repository.
    """
    auth_token = KoboAuthToken(id=1, user_id=1, auth_token="test_token")
    mock_auth_token_repo.find_by_token.return_value = auth_token
    mock_user_repo.get.return_value = None

    result = auth_service.validate_auth_token("test_token")

    assert result is None
    mock_auth_token_repo.find_by_token.assert_called_once_with("test_token")
    mock_user_repo.get.assert_called_once_with(1)


# ============================================================================
# Tests for KoboAuthService.revoke_auth_token
# ============================================================================


def test_revoke_auth_token(
    auth_service: KoboAuthService,
    mock_auth_token_repo: MagicMock,
    session: DummySession,
) -> None:
    """Test revoking an auth token.

    Parameters
    ----------
    auth_service : KoboAuthService
        Service instance.
    mock_auth_token_repo : MagicMock
        Mock auth token repository.
    session : DummySession
        Dummy session instance.
    """
    auth_service.revoke_auth_token(user_id=1)

    mock_auth_token_repo.delete_by_user_id.assert_called_once_with(1)
    assert session.flush_count == 1

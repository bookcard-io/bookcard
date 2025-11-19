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

"""Tests for FastAPI dependency providers."""

from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from sqlmodel import Session

from fundamental.api.deps import (
    get_current_user,
    get_db_session,
    require_permission,
)
from fundamental.config import AppConfig
from fundamental.database import create_db_engine
from fundamental.models.auth import User
from fundamental.services.security import SecurityTokenError
from tests.conftest import TEST_ENCRYPTION_KEY, DummySession


def test_get_db_session() -> None:
    """Test database session dependency."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    engine = create_db_engine(config)
    request = MagicMock(spec=Request)
    request.app.state.engine = engine
    session_gen = get_db_session(request)
    session = next(session_gen)
    assert isinstance(session, Session)
    # Cleanup
    with suppress(StopIteration):
        next(session_gen)


@pytest.mark.parametrize(
    ("auth_header", "expected_error"),
    [
        ("", "missing_token"),
        ("Invalid", "missing_token"),
        ("Basic token123", "missing_token"),
    ],
)
def test_get_current_user_missing_token(auth_header: str, expected_error: str) -> None:
    """Test get_current_user with missing or invalid authorization header."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": auth_header}
    session = DummySession()
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request, session)  # type: ignore[arg-type]
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.detail == expected_error


def test_get_current_user_invalid_token() -> None:
    """Test get_current_user with invalid JWT token."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer invalid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    with patch("fundamental.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.side_effect = SecurityTokenError()
        mock_jwt_class.return_value = mock_jwt
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request, session)  # type: ignore[arg-type]
        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "invalid_token"


def test_get_current_user_user_not_found() -> None:
    """Test get_current_user when user doesn't exist."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    with patch("fundamental.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "999"}
        mock_jwt_class.return_value = mock_jwt
        with patch("fundamental.api.deps.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = None
            mock_repo_class.return_value = mock_repo
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(request, session)  # type: ignore[arg-type]
            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.detail == "user_not_found"


def test_get_current_user_success() -> None:
    """Test successful get_current_user."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    with patch("fundamental.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "1"}
        mock_jwt_class.return_value = mock_jwt
        with patch("fundamental.api.deps.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo
            result = get_current_user(request, session)  # type: ignore[arg-type]
            assert result == user
            assert result.id == 1
            assert result.username == "testuser"


def test_get_admin_user_success() -> None:
    """Test successful get_admin_user with admin user."""
    from fundamental.api.deps import get_admin_user

    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )
    result = get_admin_user(admin_user)
    assert result == admin_user
    assert result.is_admin is True


def test_get_admin_user_not_admin() -> None:
    """Test get_admin_user raises 403 when user is not admin."""
    from fundamental.api.deps import get_admin_user

    regular_user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )
    with pytest.raises(HTTPException) as exc_info:
        get_admin_user(regular_user)
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.detail == "admin_required"


def test_require_permission_no_context() -> None:
    """Test require_permission with no context."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    permission_checker = require_permission("books", "read")

    with patch("fundamental.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise
        permission_checker(user, session)  # type: ignore[arg-type]

        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", None
        )


def test_require_permission_with_dict_context() -> None:
    """Test require_permission with dict context."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    context = {"book_id": 123}
    permission_checker = require_permission("books", "read", context=context)

    with patch("fundamental.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise
        permission_checker(user, session)  # type: ignore[arg-type]

        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", context
        )


def test_require_permission_with_callable_context() -> None:
    """Test require_permission with callable context (resolves to None)."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    # Test the callable context path by using a callable and type: ignore
    # The implementation checks isinstance(context, dict) first, then callable
    def context_provider() -> dict[str, object]:
        return {"book_id": 123}

    # Use type: ignore to bypass type checker since we're testing the callable path
    permission_checker = require_permission(
        "books",
        "read",
        context=context_provider,  # type: ignore[arg-type]
    )

    with patch("fundamental.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise, but callable context resolves to None
        permission_checker(user, session)  # type: ignore[arg-type]

        # Callable context is not supported, so resolved_context should be None
        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", None
        )


def test_require_permission_denied() -> None:
    """Test require_permission raises HTTPException when permission denied."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    permission_checker = require_permission("books", "write")

    with patch("fundamental.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied: books:write",
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            permission_checker(user, session)  # type: ignore[arg-type]
        exc = exc_info.value
        assert exc.status_code == status.HTTP_403_FORBIDDEN  # type: ignore[attr-defined]
        assert "permission_denied" in exc.detail  # type: ignore[attr-defined]

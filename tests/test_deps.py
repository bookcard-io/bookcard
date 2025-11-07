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

"""Tests for FastAPI dependency providers."""

from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from sqlmodel import Session

from rainbow.api.deps import get_current_user, get_db_session
from rainbow.config import AppConfig
from rainbow.database import create_db_engine
from rainbow.models.auth import User
from rainbow.services.security import SecurityTokenError
from tests.conftest import DummySession


def test_get_db_session() -> None:
    """Test database session dependency."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
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
    )
    session = DummySession()
    with patch("rainbow.api.deps.JWTManager") as mock_jwt_class:
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
    )
    session = DummySession()
    with patch("rainbow.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "999"}
        mock_jwt_class.return_value = mock_jwt
        with patch("rainbow.api.deps.UserRepository") as mock_repo_class:
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
    )
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    with patch("rainbow.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "1"}
        mock_jwt_class.return_value = mock_jwt
        with patch("rainbow.api.deps.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo
            result = get_current_user(request, session)  # type: ignore[arg-type]
            assert result == user
            assert result.id == 1
            assert result.username == "testuser"

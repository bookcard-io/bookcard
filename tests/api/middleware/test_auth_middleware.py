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

"""Tests for authentication middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fundamental.api.middleware.auth_middleware import AuthMiddleware
from fundamental.config import AppConfig
from fundamental.services.security import SecurityTokenError
from tests.conftest import TEST_ENCRYPTION_KEY


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("auth_header", "should_set_claims"),
    [
        ("", False),
        ("Bearer valid_token", True),
        ("Invalid token", False),
        ("Basic token123", False),
    ],
)
async def test_auth_middleware_dispatch(
    auth_header: str, should_set_claims: bool
) -> None:
    """Test middleware dispatch with various authorization headers."""
    request = MagicMock()
    request.headers = {"Authorization": auth_header}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    request.state.user = None
    request.state.user_claims = None
    call_next = AsyncMock(return_value=MagicMock())
    middleware = AuthMiddleware(MagicMock())
    if should_set_claims:
        with patch("fundamental.api.middleware.auth_middleware.JWTManager") as mock_jwt:
            mock_jwt_instance = MagicMock()
            mock_jwt_instance.decode_token.return_value = {
                "sub": "1",
                "username": "test",
            }
            mock_jwt.return_value = mock_jwt_instance
            response = await middleware.dispatch(request, call_next)
            assert request.state.user_claims == {"sub": "1", "username": "test"}
    else:
        response = await middleware.dispatch(request, call_next)
        assert request.state.user is None
        if not auth_header.startswith("Bearer "):
            assert request.state.user_claims is None
    call_next.assert_called_once_with(request)
    assert response is not None


@pytest.mark.asyncio
async def test_auth_middleware_invalid_token() -> None:
    """Test middleware handles invalid token gracefully."""
    request = MagicMock()
    request.headers = {"Authorization": "Bearer invalid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    request.state.user = None
    request.state.user_claims = None
    call_next = AsyncMock(return_value=MagicMock())
    middleware = AuthMiddleware(MagicMock())
    with patch("fundamental.api.middleware.auth_middleware.JWTManager") as mock_jwt:
        mock_jwt_instance = MagicMock()
        mock_jwt_instance.decode_token.side_effect = SecurityTokenError()
        mock_jwt.return_value = mock_jwt_instance
        response = await middleware.dispatch(request, call_next)
        # Should continue without setting claims
        assert request.state.user_claims is None
        call_next.assert_called_once_with(request)
        assert response is not None


@pytest.mark.asyncio
async def test_auth_middleware_no_header() -> None:
    """Test middleware with no authorization header."""
    request = MagicMock()
    request.headers = {}
    request.state.user = None
    request.state.user_claims = None
    call_next = AsyncMock(return_value=MagicMock())
    middleware = AuthMiddleware(MagicMock())
    response = await middleware.dispatch(request, call_next)
    assert request.state.user is None
    assert request.state.user_claims is None
    call_next.assert_called_once_with(request)
    assert response is not None

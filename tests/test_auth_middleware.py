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

"""Tests for authentication middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rainbow.api.middleware.auth_middleware import AuthMiddleware
from rainbow.config import AppConfig
from rainbow.services.security import SecurityTokenError


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
    )
    request.state.user = None
    request.state.user_claims = None
    call_next = AsyncMock(return_value=MagicMock())
    middleware = AuthMiddleware(MagicMock())
    if should_set_claims:
        with patch("rainbow.api.middleware.auth_middleware.JWTManager") as mock_jwt:
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
    )
    request.state.user = None
    request.state.user_claims = None
    call_next = AsyncMock(return_value=MagicMock())
    middleware = AuthMiddleware(MagicMock())
    with patch("rainbow.api.middleware.auth_middleware.JWTManager") as mock_jwt:
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

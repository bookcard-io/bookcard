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

"""Tests for KoboDeviceAuthService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from fundamental.api.schemas.kobo import KoboAuthTokenResponse
from fundamental.services.kobo.device_auth_service import KoboDeviceAuthService
from fundamental.services.kobo.store_proxy_service import KoboStoreProxyService
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session for testing.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


@pytest.fixture
def mock_proxy_service() -> MagicMock:
    """Create a mock KoboStoreProxyService.

    Returns
    -------
    MagicMock
        Mock proxy service instance.
    """
    service = MagicMock(spec=KoboStoreProxyService)
    service.should_proxy = MagicMock(return_value=False)
    service.proxy_request = AsyncMock()
    return service


@pytest.fixture
def device_auth_service(
    session: DummySession,
    mock_proxy_service: MagicMock,
) -> KoboDeviceAuthService:
    """Create KoboDeviceAuthService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_proxy_service : MagicMock
        Mock proxy service.

    Returns
    -------
    KoboDeviceAuthService
        Service instance.
    """
    return KoboDeviceAuthService(
        session,  # type: ignore[arg-type]
        mock_proxy_service,
    )


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock FastAPI Request.

    Returns
    -------
    MagicMock
        Mock request instance.
    """
    request = MagicMock()
    request.path_params = {"auth_token": "test_token"}
    request.url.path = "/kobo/test_token/v1/library/sync"
    request.method = "POST"
    request.headers = {"Content-Type": "application/json"}
    request.body = AsyncMock(return_value=b'{"user_key": "test_key"}')
    return request


# ============================================================================
# Tests for KoboDeviceAuthService.__init__
# ============================================================================


def test_init(session: DummySession, mock_proxy_service: MagicMock) -> None:
    """Test KoboDeviceAuthService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    service = KoboDeviceAuthService(
        session,  # type: ignore[arg-type]
        mock_proxy_service,
    )
    assert service._session == session
    assert service._proxy_service == mock_proxy_service


# ============================================================================
# Tests for KoboDeviceAuthService.authenticate_device
# ============================================================================


@pytest.mark.asyncio
async def test_authenticate_device_proxy_success(
    device_auth_service: KoboDeviceAuthService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test device authentication with successful proxy.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    mock_response = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "AccessToken": "proxy_token",
            "RefreshToken": "proxy_refresh",
            "TokenType": "Bearer",
            "TrackingId": "track123",
            "UserKey": "user_key",
        }
    )
    mock_proxy_service.should_proxy.return_value = True
    mock_proxy_service.proxy_request = AsyncMock(return_value=mock_response)

    result = await device_auth_service.authenticate_device(
        request=mock_request, user_key="test_key"
    )

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.AccessToken == "proxy_token"
    assert result.RefreshToken == "proxy_refresh"
    mock_proxy_service.proxy_request.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_device_proxy_failure_fallback(
    device_auth_service: KoboDeviceAuthService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test device authentication when proxy fails and falls back to local.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    mock_proxy_service.should_proxy.return_value = True
    mock_proxy_service.proxy_request = AsyncMock(side_effect=httpx.HTTPError("Error"))

    result = await device_auth_service.authenticate_device(
        request=mock_request, user_key="test_key"
    )

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.AccessToken is not None
    assert result.RefreshToken is not None
    assert result.TokenType == "Bearer"
    assert result.UserKey == "test_key"


@pytest.mark.asyncio
async def test_authenticate_device_proxy_json_error_fallback(
    device_auth_service: KoboDeviceAuthService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test device authentication when proxy returns invalid JSON.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    import json

    mock_response = MagicMock()
    mock_response.json = MagicMock(
        side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
    )
    mock_proxy_service.should_proxy.return_value = True
    mock_proxy_service.proxy_request = AsyncMock(return_value=mock_response)

    result = await device_auth_service.authenticate_device(
        request=mock_request, user_key="test_key"
    )

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.UserKey == "test_key"


@pytest.mark.asyncio
async def test_authenticate_device_local(
    device_auth_service: KoboDeviceAuthService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test device authentication with local token generation.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    mock_proxy_service.should_proxy.return_value = False

    result = await device_auth_service.authenticate_device(
        request=mock_request, user_key="test_key"
    )

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.AccessToken is not None
    assert result.RefreshToken is not None
    assert result.TokenType == "Bearer"
    assert result.TrackingId is not None
    assert result.UserKey == "test_key"
    assert len(result.AccessToken) > 0
    assert len(result.RefreshToken) > 0


# ============================================================================
# Tests for KoboDeviceAuthService._proxy_authentication
# ============================================================================


@pytest.mark.asyncio
async def test_proxy_authentication_success(
    device_auth_service: KoboDeviceAuthService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test successful proxy authentication.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    mock_response = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "AccessToken": "token",
            "RefreshToken": "refresh",
            "TokenType": "Bearer",
            "TrackingId": "track",
            "UserKey": "key",
        }
    )
    mock_proxy_service.proxy_request = AsyncMock(return_value=mock_response)

    result = await device_auth_service._proxy_authentication(mock_request)

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.AccessToken == "token"
    mock_proxy_service.proxy_request.assert_called_once()


# ============================================================================
# Tests for KoboDeviceAuthService._generate_local_tokens
# ============================================================================


def test_generate_local_tokens(
    device_auth_service: KoboDeviceAuthService,
) -> None:
    """Test local token generation.

    Parameters
    ----------
    device_auth_service : KoboDeviceAuthService
        Service instance.
    """
    result = device_auth_service._generate_local_tokens(user_key="test_key")

    assert isinstance(result, KoboAuthTokenResponse)
    assert result.AccessToken is not None
    assert result.RefreshToken is not None
    assert result.TokenType == "Bearer"
    assert result.TrackingId is not None
    assert result.UserKey == "test_key"
    assert len(result.AccessToken) > 0
    assert len(result.RefreshToken) > 0

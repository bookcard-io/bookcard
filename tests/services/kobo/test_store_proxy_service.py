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

"""Tests for KoboStoreProxyService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bookcard.models.config import IntegrationConfig
from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService
from bookcard.services.kobo.sync_token_service import SyncToken

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def integration_config_enabled() -> IntegrationConfig:
    """Create integration config with proxy enabled.

    Returns
    -------
    IntegrationConfig
        Config instance with proxy enabled.
    """
    config = MagicMock(spec=IntegrationConfig)
    config.kobo_proxy_enabled = True
    return config


@pytest.fixture
def integration_config_disabled() -> IntegrationConfig:
    """Create integration config with proxy disabled.

    Returns
    -------
    IntegrationConfig
        Config instance with proxy disabled.
    """
    config = MagicMock(spec=IntegrationConfig)
    config.kobo_proxy_enabled = False
    return config


@pytest.fixture
def proxy_service_enabled(
    integration_config_enabled: IntegrationConfig,
) -> KoboStoreProxyService:
    """Create proxy service with proxy enabled.

    Parameters
    ----------
    integration_config_enabled : IntegrationConfig
        Config with proxy enabled.

    Returns
    -------
    KoboStoreProxyService
        Service instance.
    """
    return KoboStoreProxyService(integration_config_enabled)


@pytest.fixture
def proxy_service_disabled(
    integration_config_disabled: IntegrationConfig,
) -> KoboStoreProxyService:
    """Create proxy service with proxy disabled.

    Parameters
    ----------
    integration_config_disabled : IntegrationConfig
        Config with proxy disabled.

    Returns
    -------
    KoboStoreProxyService
        Service instance.
    """
    return KoboStoreProxyService(integration_config_disabled)


@pytest.fixture
def proxy_service_none() -> KoboStoreProxyService:
    """Create proxy service with no config.

    Returns
    -------
    KoboStoreProxyService
        Service instance.
    """
    return KoboStoreProxyService(None)


# ============================================================================
# Tests for KoboStoreProxyService.__init__
# ============================================================================


def test_init_with_config(integration_config_enabled: IntegrationConfig) -> None:
    """Test initialization with config.

    Parameters
    ----------
    integration_config_enabled : IntegrationConfig
        Config instance.
    """
    service = KoboStoreProxyService(integration_config_enabled)
    assert service._integration_config == integration_config_enabled


def test_init_without_config() -> None:
    """Test initialization without config."""
    service = KoboStoreProxyService(None)
    assert service._integration_config is None


# ============================================================================
# Tests for KoboStoreProxyService.should_proxy
# ============================================================================


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (None, False),
        ("enabled", True),
        ("disabled", False),
    ],
)
def test_should_proxy(
    config: IntegrationConfig | None,
    expected: bool,
    integration_config_enabled: IntegrationConfig,
    integration_config_disabled: IntegrationConfig,
) -> None:
    """Test should_proxy method.

    Parameters
    ----------
    config : IntegrationConfig | None
        Config instance or None.
    expected : bool
        Expected result.
    integration_config_enabled : IntegrationConfig
        Config with proxy enabled.
    integration_config_disabled : IntegrationConfig
        Config with proxy disabled.
    """
    if config == "enabled":
        config = integration_config_enabled
    elif config == "disabled":
        config = integration_config_disabled

    service = KoboStoreProxyService(config)
    assert service.should_proxy() == expected


# ============================================================================
# Tests for KoboStoreProxyService.proxy_request
# ============================================================================


@pytest.mark.asyncio
async def test_proxy_request_success(
    proxy_service_enabled: KoboStoreProxyService,
) -> None:
    """Test successful proxy request.

    Parameters
    ----------
    proxy_service_enabled : KoboStoreProxyService
        Service instance.
    """
    mock_response = httpx.Response(
        status_code=200,
        content=b'{"result": "success"}',
        headers={"Content-Type": "application/json"},
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        response = await proxy_service_enabled.proxy_request(
            path="/v1/library/sync",
            method="GET",
            headers={"Host": "localhost", "Authorization": "Bearer token"},
            data=None,
        )

        assert response.status_code == 200
        assert "Host" not in mock_client_instance.request.call_args[1]["headers"]


@pytest.mark.asyncio
async def test_proxy_request_with_sync_token(
    proxy_service_enabled: KoboStoreProxyService,
) -> None:
    """Test proxy request with sync token.

    Parameters
    ----------
    proxy_service_enabled : KoboStoreProxyService
        Service instance.
    """
    from datetime import UTC, datetime

    mock_response = httpx.Response(
        status_code=200,
        content=b'{"result": "success"}',
    )
    sync_token = SyncToken(
        books_last_modified=datetime.now(UTC),
        books_last_created=datetime.now(UTC),
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        response = await proxy_service_enabled.proxy_request(
            path="/v1/library/sync",
            method="GET",
            headers={},
            data=None,
            sync_token=sync_token,
        )

        assert response.status_code == 200
        call_kwargs = mock_client_instance.request.call_args[1]
        assert "x-kobo-sync" in call_kwargs["headers"]


@pytest.mark.asyncio
async def test_proxy_request_with_data(
    proxy_service_enabled: KoboStoreProxyService,
) -> None:
    """Test proxy request with data.

    Parameters
    ----------
    proxy_service_enabled : KoboStoreProxyService
        Service instance.
    """
    mock_response = httpx.Response(
        status_code=200,
        content=b'{"result": "success"}',
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        response = await proxy_service_enabled.proxy_request(
            path="/v1/library/sync",
            method="POST",
            headers={},
            data=b'{"key": "value"}',
        )

        assert response.status_code == 200
        call_kwargs = mock_client_instance.request.call_args[1]
        assert call_kwargs["content"] == b'{"key": "value"}'


# ============================================================================
# Tests for KoboStoreProxyService.merge_sync_responses
# ============================================================================


@pytest.mark.parametrize(
    ("local_results", "store_results", "expected_length"),
    [
        ([], [], 0),
        ([{"id": 1}], [], 1),
        ([], [{"id": 2}], 1),
        ([{"id": 1}], [{"id": 2}], 2),
        ([{"id": 1}, {"id": 2}], [{"id": 3}], 3),
    ],
)
def test_merge_sync_responses(
    proxy_service_enabled: KoboStoreProxyService,
    local_results: list[dict[str, object]],
    store_results: list[dict[str, object]],
    expected_length: int,
) -> None:
    """Test merging sync responses.

    Parameters
    ----------
    proxy_service_enabled : KoboStoreProxyService
        Service instance.
    local_results : list[dict[str, object]]
        Local sync results.
    store_results : list[dict[str, object]]
        Store sync results.
    expected_length : int
        Expected merged length.
    """
    merged = proxy_service_enabled.merge_sync_responses(local_results, store_results)
    assert len(merged) == expected_length
    assert merged == local_results + store_results

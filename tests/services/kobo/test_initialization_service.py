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

"""Tests for KoboInitializationService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.api.schemas.kobo import KoboInitializationResponse
from bookcard.services.kobo.initialization_service import (
    NATIVE_KOBO_RESOURCES,
    KoboInitializationService,
)
from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService

# ============================================================================
# Fixtures
# ============================================================================


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
    return service


@pytest.fixture
def initialization_service(
    mock_proxy_service: MagicMock,
) -> KoboInitializationService:
    """Create KoboInitializationService instance for testing.

    Parameters
    ----------
    mock_proxy_service : MagicMock
        Mock proxy service.

    Returns
    -------
    KoboInitializationService
        Service instance.
    """
    return KoboInitializationService(mock_proxy_service)


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock FastAPI Request.

    Returns
    -------
    MagicMock
        Mock request instance.
    """
    request = MagicMock()
    request.base_url = Mock()
    request.base_url.__str__ = Mock(return_value="https://example.com/")
    return request


# ============================================================================
# Tests for KoboInitializationService.__init__
# ============================================================================


def test_init(mock_proxy_service: MagicMock) -> None:
    """Test KoboInitializationService initialization.

    Parameters
    ----------
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    service = KoboInitializationService(mock_proxy_service)
    assert service._proxy_service == mock_proxy_service


# ============================================================================
# Tests for KoboInitializationService.get_initialization_resources
# ============================================================================


def test_get_initialization_resources_with_store_resources(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test getting initialization resources from store.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    store_resources = {
        "library_sync": "/kobo/{auth_token}/v1/library/sync",
        "image_host": "https://cdn.kobo.com/book-images/",
    }
    with patch.object(
        initialization_service,
        "_fetch_resources_from_store",
        return_value=store_resources,
    ):
        result = initialization_service.get_initialization_resources(
            request=mock_request, auth_token="test_token"
        )

        assert isinstance(result, KoboInitializationResponse)
        assert "image_host" in result.Resources
        assert result.Resources["image_host"] == "https://example.com"


def test_get_initialization_resources_with_native_resources(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test getting initialization resources using native resources.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    with patch.object(
        initialization_service, "_fetch_resources_from_store", return_value=None
    ):
        result = initialization_service.get_initialization_resources(
            request=mock_request, auth_token="test_token"
        )

        assert isinstance(result, KoboInitializationResponse)
        assert "library_sync" in result.Resources
        assert result.Resources["image_host"] == "https://example.com"


# ============================================================================
# Tests for KoboInitializationService._fetch_resources_from_store
# ============================================================================


def test_fetch_resources_from_store_proxy_disabled(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
) -> None:
    """Test fetching resources when proxy is disabled.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_proxy_service.should_proxy.return_value = False
    result = initialization_service._fetch_resources_from_store()
    assert result is None


def test_fetch_resources_from_store_success(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
) -> None:
    """Test successfully fetching resources from store.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_proxy_service.should_proxy.return_value = True
    store_resources = {
        "library_sync": "/v1/library/sync",
        "image_host": "https://cdn.kobo.com",
    }

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"Resources": store_resources})
        mock_get.return_value = mock_response

        result = initialization_service._fetch_resources_from_store()

        assert result == store_resources
        mock_get.assert_called_once()


def test_fetch_resources_from_store_http_error(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
) -> None:
    """Test fetching resources when HTTP error occurs.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_proxy_service.should_proxy.return_value = True

    with patch("httpx.get", side_effect=httpx.HTTPError("Error")):
        result = initialization_service._fetch_resources_from_store()
        assert result is None


def test_fetch_resources_from_store_no_resources_key(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
) -> None:
    """Test fetching resources when response has no Resources key.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_proxy_service.should_proxy.return_value = True

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={})
        mock_get.return_value = mock_response

        result = initialization_service._fetch_resources_from_store()
        assert result is None


def test_fetch_resources_from_store_non_200_status(
    initialization_service: KoboInitializationService,
    mock_proxy_service: MagicMock,
) -> None:
    """Test fetching resources when status code is not 200.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_proxy_service.should_proxy.return_value = True

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = initialization_service._fetch_resources_from_store()
        assert result is None


# ============================================================================
# Tests for KoboInitializationService._transform_resource_urls
# ============================================================================


def test_transform_resource_urls(
    initialization_service: KoboInitializationService,
) -> None:
    """Test transforming resource URLs.

    Parameters
    ----------
    initialization_service : KoboInitializationService
        Service instance.
    """
    resources = NATIVE_KOBO_RESOURCES.copy()
    result = initialization_service._transform_resource_urls(
        resources=resources, base_url="https://example.com", auth_token="test_token"
    )

    assert result["image_host"] == "https://example.com"
    assert "test_token" in str(result["image_url_template"])
    assert "test_token" in str(result["image_url_quality_template"])

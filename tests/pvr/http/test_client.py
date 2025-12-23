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

"""Tests for HTTP client implementations."""

from types import TracebackType
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.http.client import HttpClient, HttpxClient

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Create a mock httpx.Client instance."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get = Mock(return_value=MagicMock(spec=httpx.Response))
    mock_client.post = Mock(return_value=MagicMock(spec=httpx.Response))
    mock_client.close = Mock()
    return mock_client


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock httpx.Response instance."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.text = "OK"
    response.content = b"OK"
    return response


@pytest.fixture(
    params=[
        (30, True, True),
        (10, False, False),
        (60, True, False),
        (45, False, True),
    ]
)
def client_params(
    request: pytest.FixtureRequest,
) -> tuple[int, bool, bool]:
    """Parametrized fixture for client initialization parameters."""
    return request.param


# ============================================================================
# HttpxClient Initialization Tests
# ============================================================================


class TestHttpxClientInit:
    """Test HttpxClient initialization."""

    def test_init_defaults(self) -> None:
        """Test initialization with default parameters."""
        client = HttpxClient(timeout=30)

        assert isinstance(client._client, httpx.Client)
        assert client._client.timeout.connect == 30
        assert client._client.timeout.read == 30
        assert client._client.timeout.write == 30
        assert client._client.timeout.pool == 30

    @pytest.mark.parametrize(
        ("timeout", "verify", "follow_redirects"),
        [
            (10, True, True),
            (30, False, False),
            (60, True, False),
            (45, False, True),
        ],
    )
    def test_init_parameters(
        self,
        timeout: int,
        verify: bool,
        follow_redirects: bool,
    ) -> None:
        """Test initialization with various parameters."""
        client = HttpxClient(
            timeout=timeout, verify=verify, follow_redirects=follow_redirects
        )

        assert isinstance(client._client, httpx.Client)
        assert client._client.timeout.connect == timeout

    def test_init_with_fixture(
        self,
        client_params: tuple[int, bool, bool],
    ) -> None:
        """Test initialization using parametrized fixture."""
        timeout, verify, follow_redirects = client_params
        client = HttpxClient(
            timeout=timeout, verify=verify, follow_redirects=follow_redirects
        )

        assert isinstance(client._client, httpx.Client)
        assert client._client.timeout.connect == timeout


# ============================================================================
# HttpxClient.get Tests
# ============================================================================


class TestHttpxClientGet:
    """Test HttpxClient.get method."""

    def test_get_basic(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test basic GET request."""
        mock_httpx_client.get.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        result = client.get("https://example.com")

        mock_httpx_client.get.assert_called_once_with("https://example.com")
        assert result == mock_response

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://localhost:8080",
            "https://api.example.com/v1/endpoint",
        ],
    )
    def test_get_various_urls(
        self,
        mock_httpx_client: MagicMock,
        mock_response: MagicMock,
        url: str,
    ) -> None:
        """Test GET request with various URLs."""
        mock_httpx_client.get.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        result = client.get(url)

        mock_httpx_client.get.assert_called_once_with(url)
        assert result == mock_response

    def test_get_with_kwargs(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test GET request with additional kwargs."""
        mock_httpx_client.get.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        result = client.get("https://example.com", headers=headers, params=params)

        mock_httpx_client.get.assert_called_once_with(
            "https://example.com", headers=headers, params=params
        )
        assert result == mock_response

    @pytest.mark.parametrize(
        ("headers", "params", "cookies"),
        [
            ({"X-Custom": "value"}, None, None),
            (None, {"q": "search"}, None),
            (None, None, {"session": "abc123"}),
            ({"Auth": "token"}, {"page": "1"}, {"lang": "en"}),
        ],
    )
    def test_get_with_various_kwargs(
        self,
        mock_httpx_client: MagicMock,
        mock_response: MagicMock,
        headers: dict[str, str] | None,
        params: dict[str, str] | None,
        cookies: dict[str, str] | None,
    ) -> None:
        """Test GET request with various kwargs combinations."""
        mock_httpx_client.get.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        kwargs: dict[str, Any] = {}
        if headers:
            kwargs["headers"] = headers
        if params:
            kwargs["params"] = params
        if cookies:
            kwargs["cookies"] = cookies

        result = client.get("https://example.com", **kwargs)

        mock_httpx_client.get.assert_called_once_with("https://example.com", **kwargs)
        assert result == mock_response


# ============================================================================
# HttpxClient.post Tests
# ============================================================================


class TestHttpxClientPost:
    """Test HttpxClient.post method."""

    def test_post_basic(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test basic POST request."""
        mock_httpx_client.post.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        result = client.post("https://example.com")

        mock_httpx_client.post.assert_called_once_with("https://example.com")
        assert result == mock_response

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://localhost:8080/api",
            "https://api.example.com/v1/endpoint",
        ],
    )
    def test_post_various_urls(
        self,
        mock_httpx_client: MagicMock,
        mock_response: MagicMock,
        url: str,
    ) -> None:
        """Test POST request with various URLs."""
        mock_httpx_client.post.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        result = client.post(url)

        mock_httpx_client.post.assert_called_once_with(url)
        assert result == mock_response

    def test_post_with_data(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test POST request with data."""
        mock_httpx_client.post.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        data = {"key": "value"}
        result = client.post("https://example.com", data=data)

        mock_httpx_client.post.assert_called_once_with("https://example.com", data=data)
        assert result == mock_response

    def test_post_with_json(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test POST request with JSON data."""
        mock_httpx_client.post.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        json_data = {"name": "test", "value": 123}
        result = client.post("https://example.com", json=json_data)

        mock_httpx_client.post.assert_called_once_with(
            "https://example.com", json=json_data
        )
        assert result == mock_response

    @pytest.mark.parametrize(
        ("data", "json", "headers", "files"),
        [
            ({"key": "value"}, None, None, None),
            (None, {"name": "test"}, None, None),
            (None, None, {"Content-Type": "application/json"}, None),
            ({"form": "data"}, None, {"Auth": "token"}, None),
            (None, {"json": "data"}, {"X-Custom": "header"}, None),
        ],
    )
    def test_post_with_various_kwargs(
        self,
        mock_httpx_client: MagicMock,
        mock_response: MagicMock,
        data: dict[str, str] | None,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
        files: dict[str, Any] | None,
    ) -> None:
        """Test POST request with various kwargs combinations."""
        mock_httpx_client.post.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        kwargs: dict[str, Any] = {}
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = headers
        if files:
            kwargs["files"] = files

        result = client.post("https://example.com", **kwargs)

        mock_httpx_client.post.assert_called_once_with("https://example.com", **kwargs)
        assert result == mock_response


# ============================================================================
# HttpxClient Context Manager Tests
# ============================================================================


class TestHttpxClientContextManager:
    """Test HttpxClient context manager methods."""

    def test_enter(self) -> None:
        """Test __enter__ method."""
        client = HttpxClient(timeout=30)

        result = client.__enter__()

        assert result is client
        assert result == client

    @pytest.mark.parametrize(
        ("exc_type", "exc_val", "exc_tb"),
        [
            (None, None, None),
            (ValueError, ValueError("test"), None),
            (Exception, Exception("error"), None),
        ],
    )
    def test_exit(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Test __exit__ method."""
        client = HttpxClient(timeout=30)
        with patch.object(client._client, "close") as mock_close:
            result = client.__exit__(exc_type, exc_val, exc_tb)

            mock_close.assert_called_once()
            assert result is None

    def test_context_manager_usage(
        self, mock_httpx_client: MagicMock, mock_response: MagicMock
    ) -> None:
        """Test using HttpxClient as context manager."""
        mock_httpx_client.get.return_value = mock_response
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        with client as ctx:
            result = ctx.get("https://example.com")

        assert result == mock_response
        mock_httpx_client.get.assert_called_once_with("https://example.com")
        mock_httpx_client.close.assert_called_once()

    def test_context_manager_with_exception(self, mock_httpx_client: MagicMock) -> None:
        """Test context manager closes client even when exception occurs."""
        mock_httpx_client.get.side_effect = ValueError("Test error")
        client = HttpxClient(timeout=30)
        client._client = mock_httpx_client

        with pytest.raises(ValueError, match="Test error"), client:
            client.get("https://example.com")

        mock_httpx_client.close.assert_called_once()


# ============================================================================
# HttpClient Type Alias Tests
# ============================================================================


class TestHttpClientAlias:
    """Test HttpClient type alias."""

    def test_http_client_is_httpx_client(self) -> None:
        """Test that HttpClient is an alias for HttpxClient."""
        assert HttpClient is HttpxClient

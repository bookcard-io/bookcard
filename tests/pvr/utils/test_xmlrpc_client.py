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

"""Tests for XML-RPC client."""

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.xmlrpc_client import XmlRpcClient

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def xmlrpc_client() -> XmlRpcClient:
    """Create XmlRpcClient instance with default settings."""
    return XmlRpcClient(url="http://localhost:8080/RPC2")


@pytest.fixture
def xmlrpc_client_with_auth() -> XmlRpcClient:
    """Create XmlRpcClient instance with authentication."""
    return XmlRpcClient(
        url="http://localhost:8080/RPC2",
        auth=("username", "password"),
    )


@pytest.fixture
def xmlrpc_client_with_token() -> XmlRpcClient:
    """Create XmlRpcClient instance with RPC token."""
    return XmlRpcClient(
        url="http://localhost:8080/RPC2",
        rpc_token="token123",
    )


@pytest.fixture
def xmlrpc_client_custom_timeout() -> XmlRpcClient:
    """Create XmlRpcClient instance with custom timeout."""
    return XmlRpcClient(
        url="http://localhost:8080/RPC2",
        timeout_seconds=60,
    )


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.text = """<?xml version="1.0"?>
    <methodResponse>
        <params>
            <param>
                <value><string>success</string></value>
            </param>
        </params>
    </methodResponse>"""
    return response


@pytest.fixture
def mock_httpx_client(mock_httpx_response: MagicMock) -> MagicMock:
    """Create a mock httpx.Client."""
    client = MagicMock(spec=httpx.Client)
    client.post.return_value = mock_httpx_response
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    return client


# ============================================================================
# XmlRpcClient Tests
# ============================================================================


class TestXmlRpcClientInit:
    """Test XmlRpcClient initialization."""

    def test_init_default(self) -> None:
        """Test XmlRpcClient initialization with default parameters."""
        client = XmlRpcClient(url="http://localhost:8080/RPC2")
        assert client.url == "http://localhost:8080/RPC2"
        assert client.timeout_seconds == 30
        assert client.auth is None
        assert client.rpc_token is None
        assert client.builder is not None
        assert client.parser is not None

    @pytest.mark.parametrize(
        ("url", "timeout", "auth", "rpc_token"),
        [
            ("http://example.com/RPC2", 10, None, None),
            ("https://example.com/RPC2", 60, ("user", "pass"), None),
            ("http://localhost:8080/RPC2", 30, None, "token123"),
            ("http://test.com/RPC2", 45, ("user", "pass"), "token456"),
        ],
    )
    def test_init_parameters(
        self,
        url: str,
        timeout: int,
        auth: tuple[str, str] | None,
        rpc_token: str | None,
    ) -> None:
        """Test XmlRpcClient initialization with various parameters."""
        client = XmlRpcClient(
            url=url,
            timeout_seconds=timeout,
            auth=auth,
            rpc_token=rpc_token,
        )
        assert client.url == url
        assert client.timeout_seconds == timeout
        assert client.auth == auth
        assert client.rpc_token == rpc_token


class TestXmlRpcClientGetClient:
    """Test XmlRpcClient._get_client method."""

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_get_client(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _get_client method."""
        mock_create_client.return_value = mock_httpx_client
        client = xmlrpc_client._get_client()
        assert client == mock_httpx_client
        mock_create_client.assert_called_once_with(
            timeout=30,
            verify=True,
            follow_redirects=True,
        )

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_get_client_custom_timeout(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client_custom_timeout: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _get_client method with custom timeout."""
        mock_create_client.return_value = mock_httpx_client
        client = xmlrpc_client_custom_timeout._get_client()
        assert client == mock_httpx_client
        mock_create_client.assert_called_once_with(
            timeout=60,
            verify=True,
            follow_redirects=True,
        )


class TestXmlRpcClientCall:
    """Test XmlRpcClient.call method."""

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_success(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test successful XML-RPC call."""
        mock_create_client.return_value = mock_httpx_client
        result = xmlrpc_client.call("test.method", "param1", 42)
        assert result == "success"
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["headers"]["Content-Type"] == "text/xml"
        assert call_args[1]["auth"] is None

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_auth(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client_with_auth: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with authentication."""
        mock_create_client.return_value = mock_httpx_client
        result = xmlrpc_client_with_auth.call("test.method")
        assert result == "success"
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["auth"] == ("username", "password")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_rpc_token(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client_with_token: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with RPC token."""
        mock_create_client.return_value = mock_httpx_client
        result = xmlrpc_client_with_token.call("test.method", "param1")
        assert result == "success"
        # Verify the request XML contains the token
        call_args = mock_httpx_client.post.call_args
        xml_content = call_args[1]["content"]
        assert "token123" in xml_content

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_multiple_params(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with multiple parameters."""
        mock_create_client.return_value = mock_httpx_client
        result = xmlrpc_client.call("test.method", "param1", 42, ["list"])
        assert result == "success"

    @pytest.mark.parametrize(
        ("status_code", "response_text", "expected_exception"),
        [
            (400, "Bad Request", PVRProviderError),
            (401, "", PVRProviderError),
            (403, "", PVRProviderError),
            (404, "Not Found", PVRProviderError),
            (500, "Internal Server Error", PVRProviderError),
        ],
    )
    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_http_error(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
        status_code: int,
        response_text: str,
        expected_exception: type[Exception],
    ) -> None:
        """Test XML-RPC call with HTTP error response."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.text = response_text
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        with pytest.raises(expected_exception):
            xmlrpc_client.call("test.method")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_http_error_long_response(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with HTTP error and long response text."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "A" * 300  # Longer than 200 chars
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        with pytest.raises(PVRProviderError):
            xmlrpc_client.call("test.method")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_http_error_response_text_exception(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with HTTP error when response.text raises exception."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = PropertyError()
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        with pytest.raises(PVRProviderError):
            xmlrpc_client.call("test.method")

    @pytest.mark.parametrize(
        "httpx_error",
        [
            httpx.TimeoutException("Request timed out"),
            httpx.ConnectError("Connection refused"),
            httpx.RequestError("Request failed"),
            httpx.HTTPError("HTTP error"),
        ],
    )
    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    @patch("bookcard.pvr.utils.xmlrpc_client.handle_httpx_exception")
    def test_call_httpx_error(
        self,
        mock_handle_exception: MagicMock,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
        httpx_error: httpx.HTTPError,
    ) -> None:
        """Test XML-RPC call with httpx.HTTPError."""
        mock_httpx_client.post.side_effect = httpx_error
        mock_create_client.return_value = mock_httpx_client
        mock_handle_exception.side_effect = PVRProviderError("Network error")

        with pytest.raises(PVRProviderError):
            xmlrpc_client.call("test.method")
        mock_handle_exception.assert_called_once_with(
            httpx_error, "XML-RPC call to test.method"
        )

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    @patch("bookcard.pvr.utils.xmlrpc_client.handle_httpx_exception")
    def test_call_httpx_error_returns_without_raising(
        self,
        mock_handle_exception: MagicMock,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with httpx.HTTPError when handle_httpx_exception returns."""
        mock_httpx_client.post.side_effect = httpx.HTTPError("HTTP error")
        mock_create_client.return_value = mock_httpx_client
        # Mock handle_httpx_exception to return without raising (unlikely but possible)
        mock_handle_exception.return_value = None

        # The raise statement on line 156 should execute
        with pytest.raises(httpx.HTTPError):
            xmlrpc_client.call("test.method")
        mock_handle_exception.assert_called_once()

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_pvr_provider_error(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call that raises PVRProviderError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0"?>
        <methodResponse>
            <fault>
                <value>
                    <struct>
                        <member>
                            <name>faultString</name>
                            <value><string>Test error</string></value>
                        </member>
                    </struct>
                </value>
            </fault>
        </methodResponse>"""
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        with pytest.raises(PVRProviderError, match="XML-RPC fault: Test error"):
            xmlrpc_client.call("test.method")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    @patch("bookcard.pvr.utils.xmlrpc_client.handle_http_error_response")
    def test_call_pvr_provider_error_from_http_handler(
        self,
        mock_handle_error: MagicMock,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call where handle_http_error_response raises PVRProviderError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client
        # handle_http_error_response raises PVRProviderError which is caught and re-raised
        mock_handle_error.side_effect = PVRProviderError("HTTP 500: Server Error")

        with pytest.raises(PVRProviderError, match="HTTP 500: Server Error"):
            xmlrpc_client.call("test.method")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_unexpected_exception(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call with unexpected exception."""
        mock_httpx_client.post.side_effect = ValueError("Unexpected error")
        mock_create_client.return_value = mock_httpx_client

        with pytest.raises(
            PVRProviderError, match=r"Unexpected error during XML-RPC call test\.method"
        ):
            xmlrpc_client.call("test.method")

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_int_response(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call returning integer."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value><int>42</int></value>
                </param>
            </params>
        </methodResponse>"""
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        result = xmlrpc_client.call("test.method")
        assert result == 42

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_array_response(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call returning array."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value>
                        <array>
                            <data>
                                <value><string>item1</string></value>
                                <value><string>item2</string></value>
                            </data>
                        </array>
                    </value>
                </param>
            </params>
        </methodResponse>"""
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        result = xmlrpc_client.call("test.method")
        assert result == ["item1", "item2"]

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_struct_response(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call returning struct."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>key</name>
                                <value><string>value</string></value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        </methodResponse>"""
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        result = xmlrpc_client.call("test.method")
        assert result == {"key": "value"}

    @patch("bookcard.pvr.utils.xmlrpc_client.create_httpx_client")
    def test_call_with_none_response(
        self,
        mock_create_client: MagicMock,
        xmlrpc_client: XmlRpcClient,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test XML-RPC call returning None."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0"?>
        <methodResponse>
            <params>
            </params>
        </methodResponse>"""
        mock_httpx_client.post.return_value = mock_response
        mock_create_client.return_value = mock_httpx_client

        result = xmlrpc_client.call("test.method")
        assert result is None


# ============================================================================
# Helper Classes
# ============================================================================


class PropertyError:
    """Helper class that raises exception when accessing text property."""

    def __getattr__(self, name: str) -> None:
        """Raise exception when accessing any attribute."""
        if name == "text":
            raise RuntimeError("Cannot access text")
        msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
        raise AttributeError(msg)

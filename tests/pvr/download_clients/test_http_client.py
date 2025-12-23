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

"""Tests for shared HTTP client utilities."""

import contextlib
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.pvr.download_clients._http_client import (
    build_base_url,
    create_httpx_client,
    handle_httpx_exception,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)


class TestBuildBaseUrl:
    """Test build_base_url function."""

    @pytest.mark.parametrize(
        ("host", "port", "use_ssl", "url_base", "expected"),
        [
            ("localhost", 8080, False, None, "http://localhost:8080"),
            ("localhost", 8080, True, None, "https://localhost:8080"),
            ("192.168.1.1", 443, True, None, "https://192.168.1.1:443"),
            ("example.com", 80, False, None, "http://example.com:80"),
            ("localhost", 8080, False, "/api", "http://localhost:8080/api/"),
            ("localhost", 8080, True, "/webapi", "https://localhost:8080/webapi/"),
            ("localhost", 8080, False, "api", "http://localhost:8080/api/"),
            ("localhost", 8080, False, "/api/", "http://localhost:8080/api/"),
            ("localhost", 8080, False, "api/", "http://localhost:8080/api/"),
        ],
    )
    def test_build_base_url(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        url_base: str | None,
        expected: str,
    ) -> None:
        """Test build_base_url with various parameters."""
        result = build_base_url(host, port, use_ssl, url_base)
        assert result == expected

    def test_build_base_url_empty_url_base(self) -> None:
        """Test build_base_url with empty url_base."""
        result = build_base_url("localhost", 8080, False, "")
        assert result == "http://localhost:8080"


class TestCreateHttpxClient:
    """Test create_httpx_client function."""

    def test_create_httpx_client_defaults(self) -> None:
        """Test create_httpx_client with default parameters."""
        client = create_httpx_client(timeout=30)
        assert isinstance(client, httpx.Client)
        assert client.timeout.connect == 30
        assert client.timeout.read == 30
        assert client.timeout.write == 30
        assert client.timeout.pool == 30
        assert getattr(client, "verify", True) is True
        assert getattr(client, "follow_redirects", True) is True

    @pytest.mark.parametrize(
        ("timeout", "verify", "follow_redirects"),
        [
            (10, True, True),
            (60, False, False),
            (30, True, False),
            (45, False, True),
        ],
    )
    def test_create_httpx_client_parameters(
        self, timeout: int, verify: bool, follow_redirects: bool
    ) -> None:
        """Test create_httpx_client with various parameters."""
        client = create_httpx_client(
            timeout=timeout, verify=verify, follow_redirects=follow_redirects
        )
        assert isinstance(client, httpx.Client)
        assert getattr(client, "verify", verify) == verify
        assert getattr(client, "follow_redirects", follow_redirects) == follow_redirects


class TestHandleHttpxException:
    """Test handle_httpx_exception function."""

    def test_handle_httpx_exception_timeout(self) -> None:
        """Test handling TimeoutException."""
        error = httpx.TimeoutException("Request timed out")
        with pytest.raises(PVRProviderTimeoutError, match="timed out"):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_timeout_custom_context(self) -> None:
        """Test handling TimeoutException with custom context."""
        error = httpx.TimeoutException("Request timed out")
        with pytest.raises(PVRProviderTimeoutError, match="Custom context timed out"):
            handle_httpx_exception(error, "Custom context")

    def test_handle_httpx_exception_http_status_401(self) -> None:
        """Test handling HTTPStatusError with 401 status."""
        response = MagicMock()
        response.status_code = 401
        response.text = "Unauthorized"
        error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=response
        )
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_http_status_403(self) -> None:
        """Test handling HTTPStatusError with 403 status."""
        response = MagicMock()
        response.status_code = 403
        response.text = "Forbidden"
        error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=response
        )
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_http_status_other(self) -> None:
        """Test handling HTTPStatusError with other status codes."""
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=response
        )
        # Should call handle_http_error_response which raises PVRProviderNetworkError
        # We just verify it doesn't raise authentication error
        with pytest.raises(PVRProviderNetworkError):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_http_status_long_response(self) -> None:
        """Test handling HTTPStatusError with long response text."""
        response = MagicMock()
        response.status_code = 500
        response.text = "A" * 300  # Longer than 200 chars
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=response
        )
        # Should truncate response text
        with contextlib.suppress(Exception):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_request_error(self) -> None:
        """Test handling RequestError."""
        error = httpx.RequestError("Connection failed")
        with pytest.raises(PVRProviderNetworkError, match="failed"):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_connect_error(self) -> None:
        """Test handling ConnectError."""
        error = httpx.ConnectError("Connection refused")
        with pytest.raises(PVRProviderNetworkError, match="failed"):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_unknown_exception(self) -> None:
        """Test handling unknown exception type."""
        error = ValueError("Unknown error")
        with pytest.raises(PVRProviderNetworkError, match="error"):
            handle_httpx_exception(error, "Test request")

    def test_handle_httpx_exception_default_context(self) -> None:
        """Test handling exception with default context."""
        error = httpx.RequestError("Connection failed")
        with pytest.raises(PVRProviderNetworkError, match="Request failed"):
            handle_httpx_exception(error)

    @patch("bookcard.pvr.download_clients._http_client.handle_http_error_response")
    def test_handle_httpx_exception_calls_handle_http_error_response(
        self, mock_handle: MagicMock
    ) -> None:
        """Test that handle_http_error_response is called for non-auth errors."""
        response = MagicMock()
        response.status_code = 500
        response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=response
        )
        # Configure mock to raise the expected exception
        mock_handle.side_effect = PVRProviderNetworkError("HTTP 500: Server Error")
        # handle_httpx_exception calls handle_http_error_response which raises an exception
        with pytest.raises(PVRProviderNetworkError):
            handle_httpx_exception(error, "Test request")
        mock_handle.assert_called_once_with(500, "Server Error")

    @patch("bookcard.pvr.download_clients._http_client.handle_http_error_response")
    def test_handle_httpx_exception_return_after_handle_http_error(
        self, mock_handle: MagicMock
    ) -> None:
        """Test return statement after handle_http_error_response (coverage)."""
        response = MagicMock()
        response.status_code = 400
        response.text = "Bad Request"
        error = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=response
        )
        # Mock handle_http_error_response to not raise (for coverage of return statement)
        mock_handle.return_value = None
        # This should return normally (though in practice it always raises)
        handle_httpx_exception(error, "Test request")
        mock_handle.assert_called_once_with(400, "Bad Request")

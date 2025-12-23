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

"""Tests for Freebox Download client."""

import base64
import hashlib
import hmac
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.freebox_download import (
    FreeboxDownloadClient,
    FreeboxDownloadProxy,
    FreeboxDownloadSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.utils.status import DownloadStatus


class TestFreeboxDownloadProxy:
    """Test FreeboxDownloadProxy."""

    def test_init(self, freebox_download_settings: FreeboxDownloadSettings) -> None:
        """Test proxy initialization."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        assert proxy.settings == freebox_download_settings
        assert proxy.api_url.endswith("/api/v1/")
        assert proxy._session_token is None

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_success(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {"challenge": "test-challenge"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        challenge = proxy._get_challenge()

        assert challenge == "test-challenge"

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_failure(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge with failure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderError, match="Failed to get Freebox challenge"):
            proxy._get_challenge()

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_http_error(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge with HTTP error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderNetworkError, match="HTTP 500"):
            proxy._get_challenge()

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_timeout(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge with timeout."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderTimeoutError):
            proxy._get_challenge()

    def test_compute_password(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test _compute_password."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        challenge = "test-challenge"
        password = proxy._compute_password(challenge)

        # Verify it's a hex string
        assert isinstance(password, str)
        assert len(password) == 40  # SHA1 hex digest length

        # Verify it matches expected HMAC-SHA1
        assert freebox_download_settings.app_token is not None
        expected = hmac.new(
            freebox_download_settings.app_token.encode("ascii"),
            challenge.encode("ascii"),
            hashlib.sha1,
        ).hexdigest()
        assert password == expected

    def test_compute_password_no_token(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test _compute_password without app token."""
        freebox_download_settings.app_token = None
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="App Token is required"
        ):
            proxy._compute_password("challenge")

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_success(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test successful authentication."""
        mock_get_challenge.return_value = "test-challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {"session_token": "test-session-token"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy.authenticate()

        assert proxy._session_token == "test-session-token"

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_success_no_token(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication success but no token returned."""
        mock_get_challenge.return_value = "test-challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {},  # No session_token
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return session token"
        ):
            proxy.authenticate()

    def test_authenticate_already_authenticated(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test authenticate when already authenticated."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._session_token = "existing-token"
        with patch(
            "bookcard.pvr.download_clients.freebox_download.create_httpx_client"
        ) as mock_create:
            proxy.authenticate()
            mock_create.assert_not_called()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_no_credentials(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication without credentials."""
        freebox_download_settings.app_id = None
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="App ID and App Token are required"
        ):
            proxy.authenticate()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_failure_status(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication with failure status."""
        mock_get_challenge.return_value = "challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderAuthenticationError):
            proxy.authenticate()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_server_error(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication with 500 server error."""
        mock_get_challenge.return_value = "challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        # handle_httpx_exception raises PVRProviderNetworkError
        with pytest.raises(PVRProviderNetworkError, match="HTTP 500"):
            proxy.authenticate()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_http_error_raised(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication where client raises HTTPStatusError(401)."""
        mock_get_challenge.return_value = "challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="Freebox authentication failed"
        ):
            proxy.authenticate()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_network_error(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication with network error."""
        mock_get_challenge.return_value = "challenge"
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Network Error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy.authenticate()

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_api_error(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test authentication with API error response."""
        mock_get_challenge.return_value = "challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False, "error_code": "auth_error"}
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError,
            match="Freebox authentication failed: auth_error",
        ):
            proxy.authenticate()

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_execute_http_method(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _execute_http_method."""
        mock_client = MagicMock()
        proxy = FreeboxDownloadProxy(freebox_download_settings)

        proxy._execute_http_method(mock_client, "GET", "url", {})
        mock_client.get.assert_called_once()

        proxy._execute_http_method(mock_client, "POST", "url", {})
        mock_client.post.assert_called_once()

        proxy._execute_http_method(mock_client, "PUT", "url", {})
        mock_client.put.assert_called_once()

        proxy._execute_http_method(mock_client, "DELETE", "url", {})
        mock_client.delete.assert_called_once()

        with pytest.raises(PVRProviderError, match="Unsupported HTTP method"):
            proxy._execute_http_method(mock_client, "HEAD", "url", {})

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": {"id": 123}}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._session_token = "test-session"
        result = proxy._request("GET", "/downloads")

        # _request returns data.get("result", {}) - check if it's a dict with id
        if isinstance(result, dict):
            assert result.get("id") == 123
        else:
            assert result == 123

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_api_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request with API error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error_code": "unknown_error",
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderError, match="Freebox API error: unknown_error"):
            proxy._request("GET", "endpoint")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_server_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request with server error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderNetworkError, match="HTTP 500"):
            proxy._request("GET", "endpoint")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_network_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request with network error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network Error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy._request("GET", "endpoint")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request session expired retry."""
        mock_client = MagicMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True, "result": {}}

        mock_client.get.side_effect = [mock_response_403, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._request("GET", "endpoint")

        assert mock_authenticate.call_count == 2  # Initial + Retry

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_session_expired_retry_fails(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request session expired retry fails."""
        mock_client = MagicMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403

        # Second response also 403
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 403
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Auth Failed", request=MagicMock(), response=mock_response_fail
        )

        mock_client.get.side_effect = [mock_response_403, mock_response_fail]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)

        with pytest.raises(
            PVRProviderAuthenticationError, match="Freebox authentication failed"
        ):
            proxy._request("GET", "endpoint")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": {"id": 123}}
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.add_task_from_file(b"content", "test.torrent", directory="/path")
        assert result == "123"

        # Verify call args
        call_kwargs = mock_client.post.call_args[1]
        assert "files" in call_kwargs
        assert call_kwargs["data"]["download_dir"] == "/path"

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_api_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file with API error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False, "error_code": "error"}
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderError, match="Freebox API error: error"):
            proxy.add_task_from_file(b"content", "test.torrent")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_server_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file with server error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderNetworkError, match="HTTP 500"):
            proxy.add_task_from_file(b"content", "test.torrent")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file with expired session."""
        mock_client = MagicMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True, "result": {"id": 123}}

        mock_client.post.side_effect = [mock_response_403, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.add_task_from_file(b"content", "test.torrent")
        assert result == "123"
        assert mock_authenticate.call_count == 2  # Initial + Retry

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_expired_retry_fails(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file with expired session retry failure."""
        mock_client = MagicMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403

        # Second response also 403
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 403
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Auth Failed", request=MagicMock(), response=mock_response_fail
        )

        mock_client.post.side_effect = [mock_response_403, mock_response_fail]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)

        with pytest.raises(
            PVRProviderAuthenticationError, match="Freebox authentication failed"
        ):
            proxy.add_task_from_file(b"content", "test.torrent")

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_network_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file with network error."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Network Error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)

        with pytest.raises(PVRProviderNetworkError):
            proxy.add_task_from_file(b"content", "test.torrent")

    @patch.object(FreeboxDownloadProxy, "_request")
    def test_add_task_from_url(
        self,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_url."""
        mock_request.return_value = {"id": 123}
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.add_task_from_url("magnet:?xt=urn:btih:test", directory="/path")
        assert result == "123"
        assert mock_request.call_args[1]["json_data"]["download_dir"] == "/path"

    @patch.object(FreeboxDownloadProxy, "_request")
    def test_get_tasks(
        self,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test get_tasks."""
        mock_request.return_value = [{"id": 123, "name": "test"}]
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.get_tasks()
        assert len(result) == 1

    @patch.object(FreeboxDownloadProxy, "_request")
    def test_delete_task(
        self,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test delete_task."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy.delete_task("123", delete_data=True)
        mock_request.assert_called_with("DELETE", "downloads/123/erase")


class TestFreeboxDownloadClient:
    """Test FreeboxDownloadClient."""

    def test_init_with_freebox_download_settings(
        self,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with FreeboxDownloadSettings."""
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, FreeboxDownloadSettings)
        assert client.enabled is True
        assert client.client_name == "Freebox Download"

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = FreeboxDownloadClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, FreeboxDownloadSettings)

    @patch.object(FreeboxDownloadProxy, "add_task_from_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = "123"
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "add_task_from_url")
    def test_add_url(
        self,
        mock_add: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        mock_add.return_value = "123"
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_url("http://example.com/test.torrent", None, None, None)
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "add_task_from_file")
    def test_add_file(
        self,
        mock_add: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        sample_torrent_file: Path,
    ) -> None:
        """Test add_file."""
        mock_add.return_value = "123"
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_file(str(sample_torrent_file), None, None, None)
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        encoded_dir = base64.b64encode(b"/downloads").decode("utf-8")
        mock_get_tasks.return_value = [
            {
                "id": 123,
                "name": "Test Download",
                "status": "downloading",
                "size": 1000000,
                "rx_bytes": 500000,
                "rx_pct": 5000,  # 50.00%
                "rx_rate": 1024,
                "eta": 60,
                "download_dir": encoded_dir,
            },
            {"id": ""},  # Should skip
        ]
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "123"
        # 5000 / 10000.0 = 0.5
        assert items[0]["progress"] == 0.5

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items_bad_base64_path(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with invalid base64 path."""
        mock_get_tasks.return_value = [
            {
                "id": 123,
                "name": "Test Download",
                "download_dir": "invalid-base64",
            },
        ]
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert items[0]["file_path"] == "invalid-base64"

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items_status_mapping(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items status mapping."""
        mock_get_tasks.return_value = [
            {"id": "1", "status": "done"},
            {"id": "2", "status": "seeding"},
            {"id": "3", "status": "error"},
            {"id": "4", "status": "stopped"},
            {"id": "5", "status": "queued"},
            {"id": "6", "status": "starting"},
            {"id": "7", "status": "checking"},
            {"id": "8", "status": "extracting"},
            {"id": "9", "status": "unknown"},
        ]
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = {item["client_item_id"]: item["status"] for item in client.get_items()}

        assert items["1"] == DownloadStatus.COMPLETED
        assert items["2"] == DownloadStatus.COMPLETED
        assert items["3"] == DownloadStatus.FAILED
        assert items["4"] == DownloadStatus.PAUSED
        assert items["5"] == DownloadStatus.QUEUED
        assert items["6"] == DownloadStatus.QUEUED
        assert items["7"] == DownloadStatus.QUEUED
        assert items["8"] == DownloadStatus.QUEUED
        assert items["9"] == DownloadStatus.DOWNLOADING  # Default is DOWNLOADING

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items_progress_cap(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items progress cap."""
        mock_get_tasks.return_value = [
            {"id": "1", "rx_pct": 10100},  # 101%
        ]
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert items[0]["progress"] == 1.0

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items_error(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items error."""
        mock_get_tasks.side_effect = Exception("API Error")
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_get_items_disabled(
        self,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items disabled."""
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(FreeboxDownloadProxy, "delete_task")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.remove_item("123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item disabled."""
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("123")

    @patch.object(FreeboxDownloadProxy, "delete_task")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item error."""
        mock_remove.side_effect = Exception("API Error")
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("123")

    @patch.object(FreeboxDownloadProxy, "_request")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    def test_test_connection(
        self,
        mock_authenticate: MagicMock,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_request.return_value = []
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.test_connection()
        assert result is True
        mock_authenticate.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "authenticate")
    def test_test_connection_error(
        self,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection error."""
        mock_authenticate.side_effect = Exception("Connect Error")
        client = FreeboxDownloadClient(
            settings=freebox_download_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    @patch("bookcard.pvr.download_clients.freebox_download.handle_http_error_response")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_http_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_handle_error: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge to cover unreachable raise after HTTP error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(status_code: int, response_text: str = "") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_error.side_effect = no_raise_handler

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        # The raise statement will execute, but since it's a bare raise,
        # it will re-raise the original exception
        with pytest.raises(httpx.HTTPStatusError):
            proxy._get_challenge()

    @patch("bookcard.pvr.download_clients.freebox_download.handle_httpx_exception")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_timeout_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_handle_exception: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge to cover unreachable raise after timeout."""
        mock_client = MagicMock()
        timeout_error = httpx.TimeoutException("Timeout")
        mock_client.get.side_effect = timeout_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(error: Exception, context: str = "Request") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_exception.side_effect = no_raise_handler

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.TimeoutException):
            proxy._get_challenge()

    @patch("bookcard.pvr.download_clients.freebox_download.handle_http_error_response")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_http_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_handle_error: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request to cover unreachable raise after HTTP error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handler to not raise so we can reach the unreachable raise
        mock_handle_error.side_effect = None

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._session_token = "test-session"
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("GET", "endpoint")

    @patch("bookcard.pvr.download_clients.freebox_download.handle_httpx_exception")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_network_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_handle_exception: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request to cover unreachable raise after network error."""
        mock_client = MagicMock()
        network_error = httpx.RequestError("Network Error")
        mock_client.get.side_effect = network_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(error: Exception, context: str = "Request") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_exception.side_effect = no_raise_handler

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._session_token = "test-session"
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.RequestError):
            proxy._request("GET", "endpoint")

    @patch("bookcard.pvr.download_clients.freebox_download.handle_http_error_response")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_http_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_handle_error: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file to cover unreachable raise after HTTP error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handler to not raise so we can reach the unreachable raise
        mock_handle_error.side_effect = None

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.HTTPStatusError):
            proxy.add_task_from_file(b"content", "test.torrent")

    @patch("bookcard.pvr.download_clients.freebox_download.handle_httpx_exception")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_add_task_from_file_network_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_handle_exception: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_file to cover unreachable raise after network error."""
        mock_client = MagicMock()
        network_error = httpx.RequestError("Network Error")
        mock_client.post.side_effect = network_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(error: Exception, context: str = "Request") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_exception.side_effect = no_raise_handler

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.RequestError):
            proxy.add_task_from_file(b"content", "test.torrent")

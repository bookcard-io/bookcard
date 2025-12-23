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

"""Tests for qBittorrent download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
)
from bookcard.pvr.download_clients.qbittorrent import (
    QBittorrentClient,
    QBittorrentProxy,
    QBittorrentSettings,
)


class TestQBittorrentProxy:
    """Test QBittorrentProxy."""

    def test_init(self, qbittorrent_settings: QBittorrentSettings) -> None:
        """Test proxy initialization."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        assert proxy.settings == qbittorrent_settings
        assert proxy.base_url == "http://localhost:8080"
        assert proxy._auth_cookies is None

    def test_init_with_ssl(self) -> None:
        """Test proxy initialization with SSL."""
        settings = QBittorrentSettings(
            host="localhost",
            port=443,
            use_ssl=True,
            timeout_seconds=30,
        )
        proxy = QBittorrentProxy(settings)
        assert proxy.base_url == "https://localhost:443"

    def test_init_with_url_base(self) -> None:
        """Test proxy initialization with url_base."""
        settings = QBittorrentSettings(
            host="localhost",
            port=8080,
            url_base="/qbt",
            timeout_seconds=30,
        )
        proxy = QBittorrentProxy(settings)
        assert proxy.base_url == "http://localhost:8080/qbt/"

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_no_credentials(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test authentication without credentials."""
        qbittorrent_settings.username = None
        qbittorrent_settings.password = None
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._authenticate()
        assert proxy._auth_cookies == {}

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_success(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test successful authentication."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Ok."
        mock_response.cookies = {"SID": "test-session-id"}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._authenticate()

        assert proxy._auth_cookies == {"SID": "test-session-id"}
        mock_client.post.assert_called_once()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_failure(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test authentication failure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Fails."
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        with pytest.raises(PVRProviderAuthenticationError, match="invalid credentials"):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_http_error_401(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test authentication with HTTP 401 error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        with pytest.raises(PVRProviderAuthenticationError, match="invalid credentials"):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_httpx_exception")
    def test_authenticate_request_error(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test authentication with RequestError."""
        mock_client = MagicMock()
        mock_error = httpx.RequestError("Connection failed")
        mock_client.post.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        # Should raise the original error
        with pytest.raises(httpx.RequestError):
            proxy._authenticate()
        mock_handle.assert_called_once()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_httpx_exception")
    def test_authenticate_timeout_exception(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test authentication with TimeoutException."""
        mock_client = MagicMock()
        mock_error = httpx.TimeoutException("Timeout")
        mock_client.post.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        # Should raise the original error
        with pytest.raises(httpx.TimeoutException):
            proxy._authenticate()
        mock_handle.assert_called_once()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_httpx_exception")
    def test_authenticate_http_status_error_not_401_403(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test authentication with HTTPStatusError (not 401/403)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        # Should raise the original error
        with pytest.raises(httpx.HTTPStatusError):
            proxy._authenticate()
        mock_handle.assert_called_once()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_force_reauth(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test forced re-authentication."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Ok."
        mock_response.cookies = {"SID": "new-session-id"}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "old-session-id"}
        proxy._authenticate(force=True)

        assert proxy._auth_cookies == {"SID": "new-session-id"}

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_authenticate_no_force_when_authenticated(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test that authentication is skipped when already authenticated."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "existing-session-id"}
        proxy._authenticate(force=False)

        mock_create_client.assert_not_called()

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_execute_request_get(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test _execute_request with GET method."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        result = proxy._execute_request(mock_client, "GET", "http://test.com", {})

        assert result == mock_response
        mock_client.get.assert_called_once_with(
            "http://test.com", cookies={}, params=None
        )

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_execute_request_post(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test _execute_request with POST method."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.post.return_value = mock_response
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        data = {"key": "value"}
        result = proxy._execute_request(
            mock_client, "POST", "http://test.com", {}, data=data
        )

        assert result == mock_response
        mock_client.post.assert_called_once_with(
            "http://test.com", cookies={}, data=data, files=None, params=None
        )

    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_execute_request_post_with_files(
        self, mock_create_client: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test _execute_request with POST method and files."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.post.return_value = mock_response
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        files = {"file": ("test.torrent", b"content")}
        result = proxy._execute_request(
            mock_client, "POST", "http://test.com", {}, files=files
        )

        assert result == mock_response
        # Check that post was called with files parameter
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        assert "files" in call_kwargs

    def test_execute_request_unsupported_method(
        self, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test _execute_request with unsupported method."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Unsupported HTTP method"):
            proxy._execute_request(MagicMock(), "PUT", "http://test.com", {})

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        result = proxy._request("GET", "/api/v2/app/version")

        assert result == '{"result": "success"}'
        mock_authenticate.assert_called_once()

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request with session expiration (403)."""
        mock_client = MagicMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.text = "Ok"
        mock_response_200.raise_for_status = Mock()
        mock_client.get.side_effect = [mock_response_403, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        result = proxy._request("GET", "/api/v2/app/version")

        assert result == "Ok"
        assert mock_authenticate.call_count == 2  # Initial + re-auth

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    def test_request_api_error_fails(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request with API error response 'Fails.'."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Fails."
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        with pytest.raises(PVRProviderError, match="Fails"):
            proxy._request("GET", "/api/v2/app/version")

    @patch.object(QBittorrentProxy, "_request")
    def test_get_version(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_version."""
        mock_request.return_value = "4.5.0"
        proxy = QBittorrentProxy(qbittorrent_settings)
        result = proxy.get_version()
        assert result == "4.5.0"
        mock_request.assert_called_once_with("GET", "/api/v2/app/version")

    @patch.object(QBittorrentProxy, "_request")
    def test_add_torrent_from_url(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_torrent_from_url."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy.add_torrent_from_url(
            "magnet:?xt=urn:btih:test", category="test", save_path="/path"
        )
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/torrents/add"
        assert "urls" in call_args[1]["data"]
        assert call_args[1]["data"]["category"] == "test"
        assert call_args[1]["data"]["savepath"] == "/path"

    @patch.object(QBittorrentProxy, "_request")
    def test_add_torrent_from_file(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_torrent_from_file."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy.add_torrent_from_file(b"torrent content", "test.torrent", category="test")
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "files" in call_args[1]

    @patch.object(QBittorrentProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_torrents."""
        mock_request.return_value = '[{"hash": "abc123", "name": "test"}]'
        proxy = QBittorrentProxy(qbittorrent_settings)
        result = proxy.get_torrents(category="test")
        assert result == [{"hash": "abc123", "name": "test"}]
        mock_request.assert_called_once()

    @patch.object(QBittorrentProxy, "_request")
    def test_get_torrents_parse_error(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_torrents with parse error."""
        mock_request.return_value = "invalid json"
        proxy = QBittorrentProxy(qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to parse"):
            proxy.get_torrents()

    @patch.object(QBittorrentProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test remove_torrent."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy.remove_torrent("abc123", delete_files=True)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["data"]["hashes"] == "abc123"
        assert call_args[1]["data"]["deleteFiles"] == "true"

    @patch.object(QBittorrentProxy, "_request")
    def test_get_torrent_properties(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_torrent_properties."""
        mock_request.return_value = '{"hash": "abc123"}'
        proxy = QBittorrentProxy(qbittorrent_settings)
        result = proxy.get_torrent_properties("abc123")
        assert result == {"hash": "abc123"}

    @patch.object(QBittorrentProxy, "_request")
    def test_get_torrent_properties_parse_error(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_torrent_properties with invalid JSON."""
        mock_request.return_value = "invalid json"
        proxy = QBittorrentProxy(qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to parse"):
            proxy.get_torrent_properties("abc123")

    @patch.object(QBittorrentProxy, "_request")
    def test_add_torrent_from_file_with_save_path(
        self, mock_request: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_torrent_from_file with save_path."""
        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy.add_torrent_from_file(
            b"torrent content", "test.torrent", save_path="/custom/path"
        )
        mock_request.assert_called_once()
        # Check that save_path was passed in data
        call_args = mock_request.call_args
        assert call_args[1]["data"]["savepath"] == "/custom/path"

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_http_error_response")
    def test_execute_request_http_status_error(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request with HTTPStatusError."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_http_error_response to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        # Should raise the original error
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("GET", "/api/v2/app/version")
        mock_handle.assert_called_once()

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_httpx_exception")
    def test_execute_request_request_error(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request with RequestError."""
        mock_client = MagicMock()
        mock_error = httpx.RequestError("Connection failed")
        mock_client.get.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        # Should raise the original error
        with pytest.raises(httpx.RequestError):
            proxy._request("GET", "/api/v2/app/version")
        mock_handle.assert_called_once()

    @patch.object(QBittorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.qbittorrent.create_httpx_client")
    @patch("bookcard.pvr.download_clients.qbittorrent.handle_httpx_exception")
    def test_execute_request_timeout_exception(
        self,
        mock_handle: MagicMock,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _request with TimeoutException."""
        mock_client = MagicMock()
        mock_error = httpx.TimeoutException("Timeout")
        mock_client.get.side_effect = mock_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of raise statement)
        mock_handle.return_value = None

        proxy = QBittorrentProxy(qbittorrent_settings)
        proxy._auth_cookies = {"SID": "test"}
        # Should raise the original error
        with pytest.raises(httpx.TimeoutException):
            proxy._request("GET", "/api/v2/app/version")
        mock_handle.assert_called_once()


class TestQBittorrentClient:
    """Test QBittorrentClient."""

    def test_init_with_qbittorrent_settings(
        self, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test initialization with QBittorrentSettings."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        assert isinstance(client.settings, QBittorrentSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = QBittorrentClient(settings=base_download_client_settings)
        assert isinstance(client.settings, QBittorrentSettings)

    def test_init_disabled(self, qbittorrent_settings: QBittorrentSettings) -> None:
        """Test initialization with enabled=False."""
        client = QBittorrentClient(settings=qbittorrent_settings, enabled=False)
        assert client.enabled is False

    @patch.object(QBittorrentProxy, "add_torrent_from_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_download with magnet link."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(QBittorrentProxy, "add_torrent_from_url")
    def test_add_download_magnet_exception(
        self, mock_add: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_download with magnet link that raises exception during hash extraction."""
        mock_add.side_effect = RuntimeError("Network error")
        client = QBittorrentClient(settings=qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to add download"):
            client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")

    @patch.object(QBittorrentProxy, "add_torrent_from_url")
    def test_add_download_http_url(
        self, mock_add: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_download with HTTP URL."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client.add_download("http://example.com/torrent.torrent")
        assert result == "pending"
        mock_add.assert_called_once()

    @patch.object(QBittorrentProxy, "add_torrent_from_file")
    def test_add_download_file_path(
        self,
        mock_add: MagicMock,
        qbittorrent_settings: QBittorrentSettings,
        sample_torrent_file: Path,
    ) -> None:
        """Test add_download with file path."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client.add_download(str(sample_torrent_file))
        assert result == "pending"
        mock_add.assert_called_once()

    @patch.object(QBittorrentProxy, "add_torrent_from_url")
    def test_add_download_disabled(
        self, mock_add: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test add_download when disabled."""
        client = QBittorrentClient(settings=qbittorrent_settings, enabled=False)
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("magnet:?xt=urn:btih:test")

    @patch.object(QBittorrentProxy, "get_torrents")
    def test_get_items(
        self, mock_get_torrents: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_items."""
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "state": "downloading",
                "progress": 50.0,
                "size": 1000000,
                "completed": 500000,
                "dlspeed": 100000,
                "eta": 5,
                "save_path": "/downloads",
            }
        ]
        client = QBittorrentClient(settings=qbittorrent_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"
        assert items[0]["title"] == "Test Torrent"
        assert items[0]["status"] == "downloading"
        assert items[0]["progress"] == 0.5

    @patch.object(QBittorrentProxy, "get_torrents")
    def test_get_items_disabled(
        self, mock_get_torrents: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_items when disabled."""
        client = QBittorrentClient(settings=qbittorrent_settings, enabled=False)
        items = client.get_items()
        assert items == []

    @patch.object(QBittorrentProxy, "get_torrents")
    def test_get_items_progress_over_100(
        self, mock_get_torrents: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_items with progress over 100%."""
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test",
                "state": "uploading",
                "progress": 150.0,
                "size": 1000000,
                "completed": 1000000,
                "save_path": "/downloads",
            }
        ]
        client = QBittorrentClient(settings=qbittorrent_settings)
        items = client.get_items()
        assert items[0]["progress"] == 1.0

    @patch.object(QBittorrentProxy, "get_torrents")
    def test_get_items_exception(
        self, mock_get_torrents: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test get_items with exception."""
        mock_get_torrents.side_effect = RuntimeError("Network error")
        client = QBittorrentClient(settings=qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(QBittorrentProxy, "remove_torrent")
    def test_remove_item(
        self, mock_remove: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test remove_item."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client.remove_item("ABC123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with("abc123", delete_files=True)

    @patch.object(QBittorrentProxy, "remove_torrent")
    def test_remove_item_disabled(
        self, mock_remove: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test remove_item when disabled."""
        client = QBittorrentClient(settings=qbittorrent_settings, enabled=False)
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("ABC123")

    @patch.object(QBittorrentProxy, "remove_torrent")
    def test_remove_item_exception(
        self, mock_remove: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test remove_item with exception."""
        mock_remove.side_effect = RuntimeError("Network error")
        client = QBittorrentClient(settings=qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to remove download"):
            client.remove_item("ABC123")

    @patch.object(QBittorrentProxy, "get_version")
    def test_test_connection(
        self, mock_get_version: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "4.5.0"
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client.test_connection()
        assert result is True

    @patch.object(QBittorrentProxy, "get_version")
    def test_test_connection_exception(
        self, mock_get_version: MagicMock, qbittorrent_settings: QBittorrentSettings
    ) -> None:
        """Test test_connection with exception."""
        mock_get_version.side_effect = RuntimeError("Network error")
        client = QBittorrentClient(settings=qbittorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    @pytest.mark.parametrize(
        ("state", "expected_status"),
        [
            ("uploading", "completed"),
            ("stalledUP", "completed"),
            ("queuedUP", "completed"),
            ("forcedUP", "completed"),
            ("pausedUP", "completed"),
            ("stoppedUP", "completed"),
            ("downloading", "downloading"),
            ("forcedDL", "downloading"),
            ("moving", "downloading"),
            ("pausedDL", "paused"),
            ("stoppedDL", "paused"),
            ("queuedDL", "queued"),
            ("checkingDL", "queued"),
            ("checkingUP", "queued"),
            ("checkingResumeData", "queued"),
            ("metaDL", "queued"),
            ("forcedMetaDL", "queued"),
            ("error", "failed"),
            ("missingFiles", "failed"),
            ("unknown", "downloading"),  # Default
        ],
    )
    def test_map_state_to_status(
        self,
        state: str,
        expected_status: str,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _map_state_to_status with various states."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        result = client._map_state_to_status(state)
        assert result == expected_status

    @pytest.mark.parametrize(
        ("eta", "expected"),
        [
            (None, None),
            (-1, None),
            (0, 0),
            (100, 100),
            (8640000, None),  # Unknown ETA threshold
            (8640001, None),
        ],
    )
    def test_calculate_eta(
        self,
        eta: int | None,
        expected: int | None,
        qbittorrent_settings: QBittorrentSettings,
    ) -> None:
        """Test _calculate_eta with various ETA values."""
        client = QBittorrentClient(settings=qbittorrent_settings)
        torrent = {"eta": eta}
        result = client._calculate_eta(torrent)
        assert result == expected

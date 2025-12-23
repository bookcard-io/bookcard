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

"""Tests for Deluge download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.deluge import (
    DelugeClient,
    DelugeProxy,
    DelugeSettings,
)
from bookcard.pvr.exceptions import PVRProviderAuthenticationError


class TestDelugeProxy:
    """Test DelugeProxy."""

    def test_init(self, deluge_settings: DelugeSettings) -> None:
        """Test proxy initialization."""
        proxy = DelugeProxy(deluge_settings)
        assert proxy.settings == deluge_settings
        assert proxy.rpc_url.endswith("/json")
        assert proxy._session_id is None

    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_authenticate_success(
        self, mock_create_client: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test successful authentication."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test-session-id", "error": None}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DelugeProxy(deluge_settings)
        proxy._authenticate()

        assert proxy._session_id == "test-session-id"

    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_authenticate_no_credentials(
        self, mock_create_client: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test authentication without credentials."""
        deluge_settings.username = None
        deluge_settings.password = None
        proxy = DelugeProxy(deluge_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires username and password"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_authenticate_error_response(
        self, mock_create_client: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test authentication with error response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": None,
            "error": {"message": "Auth failed"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DelugeProxy(deluge_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_authenticate_no_session_id(
        self, mock_create_client: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test authentication with no session ID in response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": None, "error": None}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DelugeProxy(deluge_settings)
        with pytest.raises(PVRProviderAuthenticationError, match="no session ID"):
            proxy._authenticate()

    @patch.object(DelugeProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        deluge_settings: DelugeSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "test-result", "error": None}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DelugeProxy(deluge_settings)
        proxy._session_id = "test-session"
        result = proxy._request("test.method", "arg1", "arg2")

        assert result == "test-result"

    @patch.object(DelugeProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.deluge.create_httpx_client")
    def test_request_rpc_error_retry(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        deluge_settings: DelugeSettings,
    ) -> None:
        """Test _request with RPC error that triggers retry."""
        mock_client = MagicMock()
        mock_response_error = MagicMock()
        mock_response_error.json.return_value = {
            "result": None,
            "error": {"code": 1, "message": "Auth error"},
        }
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"result": "success", "error": None}
        mock_response_success.raise_for_status = Mock()
        mock_client.post.side_effect = [mock_response_error, mock_response_success]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DelugeProxy(deluge_settings)
        proxy._session_id = "test-session"
        result = proxy._request("test.method")

        assert result == "success"
        assert mock_authenticate.call_count == 2

    @patch.object(DelugeProxy, "_request")
    def test_get_version(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test get_version."""
        mock_request.return_value = "2.1.1"
        proxy = DelugeProxy(deluge_settings)
        result = proxy.get_version()
        assert result == "2.1.1"

    @patch.object(DelugeProxy, "_request")
    def test_add_torrent_magnet(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test add_torrent_magnet."""
        mock_request.return_value = "abc123hash"
        proxy = DelugeProxy(deluge_settings)
        result = proxy.add_torrent_magnet(
            "magnet:?xt=urn:btih:test", {"download_location": "/path"}
        )
        assert result == "abc123hash"
        mock_request.assert_called_once()

    @patch.object(DelugeProxy, "_request")
    def test_add_torrent_file(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test add_torrent_file."""
        mock_request.return_value = "abc123hash"
        proxy = DelugeProxy(deluge_settings)
        result = proxy.add_torrent_file("test.torrent", b"torrent content")
        assert result == "abc123hash"
        mock_request.assert_called_once()
        # Verify base64 encoding
        call_args = mock_request.call_args
        assert call_args[0][1] == "test.torrent"
        assert isinstance(call_args[0][2], str)  # base64 encoded

    @patch.object(DelugeProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test get_torrents."""
        mock_request.return_value = {
            "torrents": {"hash1": {"name": "test1"}, "hash2": {"name": "test2"}}
        }
        proxy = DelugeProxy(deluge_settings)
        result = proxy.get_torrents()
        assert len(result) == 2

    @patch.object(DelugeProxy, "_request")
    def test_get_torrents_empty(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test get_torrents with empty result."""
        mock_request.return_value = None
        proxy = DelugeProxy(deluge_settings)
        result = proxy.get_torrents()
        assert result == []

    @patch.object(DelugeProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, deluge_settings: DelugeSettings
    ) -> None:
        """Test remove_torrent."""
        proxy = DelugeProxy(deluge_settings)
        _ = proxy.remove_torrent("abc123", remove_data=True)
        mock_request.assert_called_once()


class TestDelugeClient:
    """Test DelugeClient."""

    def test_init_with_deluge_settings(
        self,
        deluge_settings: DelugeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DelugeSettings."""
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, DelugeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = DelugeClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, DelugeSettings)

    @patch.object(DelugeProxy, "_authenticate")
    @patch.object(DelugeProxy, "set_torrent_label")
    @patch.object(DelugeProxy, "add_torrent_magnet")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        mock_set_label: MagicMock,
        mock_auth: MagicMock,
        deluge_settings: DelugeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = "abc123hash"
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "ABC123HASH"
        mock_add.assert_called_once()

    @patch.object(DelugeProxy, "_authenticate")
    @patch.object(DelugeProxy, "set_torrent_label")
    @patch.object(DelugeProxy, "add_torrent_file")
    def test_add_download_file_path(
        self,
        mock_add: MagicMock,
        mock_set_label: MagicMock,
        mock_auth: MagicMock,
        deluge_settings: DelugeSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path."""
        mock_add.return_value = "abc123hash"
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(str(sample_torrent_file))
        assert result == "ABC123HASH"
        mock_add.assert_called_once()

    @patch.object(DelugeProxy, "get_torrents_by_label")
    @patch.object(DelugeProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        mock_get_torrents_by_label: MagicMock,
        deluge_settings: DelugeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        mock_get_torrents_by_label.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "state": "Downloading",
                "progress": 50.0,
                "total_size": 1000000,
                "total_done": 500000,
                "save_path": "/downloads",
            }
        ]
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "state": "Downloading",
                "progress": 50.0,
                "total_size": 1000000,
                "total_done": 500000,
                "save_path": "/downloads",
            }
        ]
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(DelugeProxy, "_authenticate")
    @patch.object(DelugeProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        mock_auth: MagicMock,
        deluge_settings: DelugeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        mock_remove.return_value = True
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        # DelugeClient passes delete_files to remove_torrent which maps to remove_data
        mock_remove.assert_called_once()

    @patch.object(DelugeProxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        deluge_settings: DelugeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "2.1.1"
        client = DelugeClient(
            settings=deluge_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

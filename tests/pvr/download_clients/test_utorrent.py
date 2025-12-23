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

"""Tests for uTorrent download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.utorrent import (
    UTorrentClient,
    UTorrentProxy,
    UTorrentSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)


class TestUTorrentProxy:
    """Test UTorrentProxy."""

    def test_init(self) -> None:
        """Test proxy initialization."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        proxy = UTorrentProxy(settings)
        assert proxy.settings == settings
        assert proxy.api_url.endswith("/gui/")
        assert proxy._token is None

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_success(self, mock_create_client: MagicMock) -> None:
        """Test successful authentication."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        # uTorrent returns token in HTML with single quotes
        mock_response.text = "<html><body><div id='token' style='display:none;'>test-token</div></body></html>"
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._authenticate()

        assert proxy._token == "test-token"

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_no_credentials(self, mock_create_client: MagicMock) -> None:
        """Test authentication without credentials."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            timeout_seconds=30,
        )
        proxy = UTorrentProxy(settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires username and password"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_no_token_div(self, mock_create_client: MagicMock) -> None:
        """Test authentication without token div."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "<html><body>No token here</body></html>"
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="Failed to extract token"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_no_token_end(self, mock_create_client: MagicMock) -> None:
        """Test authentication without token end div."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "<html><body><div id='token' style='display:none;'>test-token"
        )
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="Failed to extract token"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_empty_token(self, mock_create_client: MagicMock) -> None:
        """Test authentication with empty token."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "<html><body><div id='token' style='display:none;'></div></body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        with pytest.raises(PVRProviderAuthenticationError, match="empty token"):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_timeout(self, mock_create_client: MagicMock) -> None:
        """Test authentication with timeout."""
        import httpx

        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        with pytest.raises(httpx.TimeoutException):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_authenticate_request_error(self, mock_create_client: MagicMock) -> None:
        """Test authentication with request error."""
        import httpx

        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Request error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        with pytest.raises(httpx.RequestError):
            proxy._authenticate()

    @patch.object(UTorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request successful call."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        # uTorrent returns JSON wrapped in response
        mock_response.json.return_value = {"build": 12345, "torrents": []}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._token = "test-token"
        result = proxy._request("list", {"list": 1})

        assert result == {"build": 12345, "torrents": []}

    @patch.object(UTorrentProxy, "_request")
    def test_get_torrents(self, mock_request: MagicMock) -> None:
        """Test get_torrents."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_request.return_value = {
            "build": 12345,
            "torrents": [
                [
                    "hash1",
                    "name1",
                    1000,
                    500,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ],
        }
        proxy = UTorrentProxy(settings)
        result = proxy.get_torrents()
        assert len(result) == 1

    @patch.object(UTorrentProxy, "_request")
    def test_get_torrents_with_cache_id(self, mock_request: MagicMock) -> None:
        """Test get_torrents with cache_id."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_request.return_value = {"build": 12345, "torrents": []}
        proxy = UTorrentProxy(settings)
        result = proxy.get_torrents(cache_id="cache123")
        assert result == []
        call_args = mock_request.call_args
        assert call_args[1]["params"]["cid"] == "cache123"

    @patch.object(UTorrentProxy, "_request")
    def test_get_torrents_short_list(self, mock_request: MagicMock) -> None:
        """Test get_torrents with short list items."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_request.return_value = {
            "build": 12345,
            "torrents": [["hash1", "name1"]],  # Too short
        }
        proxy = UTorrentProxy(settings)
        result = proxy.get_torrents()
        assert len(result) == 0

    @patch.object(UTorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_add_torrent_file(
        self, mock_create_client: MagicMock, mock_authenticate: MagicMock
    ) -> None:
        """Test add_torrent_file."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._token = "test-token"
        result = proxy.add_torrent_file("test.torrent", b"torrent content")
        assert result == "pending"

    @patch.object(UTorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_add_torrent_file_token_expired(
        self, mock_create_client: MagicMock, mock_authenticate: MagicMock
    ) -> None:
        """Test add_torrent_file with token expiration."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        mock_client.post.side_effect = [mock_response_400, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._token = "old-token"
        result = proxy.add_torrent_file("test.torrent", b"torrent content")
        assert result == "pending"
        assert mock_authenticate.call_count == 2

    @patch.object(UTorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_add_torrent_file_auth_error(
        self, mock_create_client: MagicMock, mock_authenticate: MagicMock
    ) -> None:
        """Test add_torrent_file with auth error."""
        import httpx

        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._token = "test-token"
        with pytest.raises(PVRProviderAuthenticationError):
            proxy.add_torrent_file("test.torrent", b"torrent content")

    @patch.object(UTorrentProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.utorrent.create_httpx_client")
    def test_add_torrent_file_timeout(
        self, mock_create_client: MagicMock, mock_authenticate: MagicMock
    ) -> None:
        """Test add_torrent_file with timeout."""
        import httpx

        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = UTorrentProxy(settings)
        proxy._token = "test-token"
        with pytest.raises(httpx.TimeoutException):
            proxy.add_torrent_file("test.torrent", b"torrent content")

    @patch.object(UTorrentProxy, "_request")
    def test_remove_torrent(self, mock_request: MagicMock) -> None:
        """Test remove_torrent."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        proxy = UTorrentProxy(settings)
        proxy.remove_torrent("hash123", remove_data=True)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "removedata"

    @patch.object(UTorrentProxy, "_request")
    def test_set_torrent_label(self, mock_request: MagicMock) -> None:
        """Test set_torrent_label."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        proxy = UTorrentProxy(settings)
        proxy.set_torrent_label("hash123", "test-label")
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "setprops"
        assert call_args[1]["params"]["s"] == "label"
        assert call_args[1]["params"]["v"] == "test-label"


class TestUTorrentClient:
    """Test UTorrentClient."""

    def test_init_with_utorrent_settings(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test initialization with UTorrentSettings."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, UTorrentSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = UTorrentClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, UTorrentSettings)

    @patch.object(UTorrentProxy, "add_torrent_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_add.return_value = "ABCDEF1234567890"
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    def test_add_download_disabled(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test add_download when disabled."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("magnet:?xt=urn:btih:test")

    @patch.object(UTorrentProxy, "add_torrent_url")
    @patch.object(UTorrentProxy, "set_torrent_label")
    def test_add_download_with_label(
        self,
        mock_set_label: MagicMock,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with label."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
            category="test-category",
        )
        mock_add.return_value = "ABCDEF1234567890"
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(
            "magnet:?xt=urn:btih:ABCDEF1234567890", category="custom-label"
        )
        assert result == "ABCDEF1234567890"
        mock_set_label.assert_called_once_with("ABCDEF1234567890", "custom-label")

    @patch.object(UTorrentProxy, "add_torrent_file")
    def test_add_download_file_path(
        self,
        mock_add_file: MagicMock,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_add_file.return_value = "ABCDEF1234567890"
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(str(sample_torrent_file))
        assert result == "ABCDEF1234567890"
        mock_add_file.assert_called_once()

    def test_add_download_invalid_url(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test add_download with invalid URL."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Invalid download URL"):
            client.add_download("invalid://url")

    @patch.object(UTorrentProxy, "add_torrent_url")
    def test_add_download_pending_hash(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with pending hash."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_add.return_value = "pending"
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:test")
        assert result == "PENDING"

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "status": 4,  # Downloading
                "progress": 50.0,
            }
        ]
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_disabled(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        items = client.get_items()
        assert items == []
        mock_get_torrents.assert_not_called()

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_no_hash(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with torrent without hash."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "hash": "",
                "name": "Test Torrent",
                "status": 4,
                "progress": 50.0,
            }
        ]
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 0

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_with_category_filter(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with category filter."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
            category="test-category",
        )
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "status": 4,
                "progress": 50.0,
                "label": "test-category",
            },
            {
                "hash": "def456",
                "name": "Other Torrent",
                "status": 4,
                "progress": 50.0,
                "label": "other-category",
            },
        ]
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_progress_over_100(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with progress over 100%."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "status": 4,
                "progress": 1500,  # Over 1000 (100%)
            }
        ]
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["progress"] == 1.0

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_with_eta(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with ETA."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "hash": "abc123",
                "name": "Test Torrent",
                "status": 4,
                "progress": 500,
                "size": 1000,
                "downloaded": 500,
                "eta": 60,
                "downspeed": 100,
            }
        ]
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["eta_seconds"] == 60
        assert items[0]["download_speed_bytes_per_sec"] == 100

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with error."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.side_effect = Exception("Connection error")
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(UTorrentProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test remove_item when disabled."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("abc123")

    @patch.object(UTorrentProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with error."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_remove.side_effect = Exception("Remove error")
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("abc123")

    @patch.object(UTorrentProxy, "get_torrents")
    def test_test_connection_error(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with error."""
        mock_get_torrents.side_effect = Exception("Connection error")
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    @patch.object(UTorrentProxy, "get_torrents")
    def test_test_connection(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_torrents.return_value = []
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True
        mock_get_torrents.assert_called_once()

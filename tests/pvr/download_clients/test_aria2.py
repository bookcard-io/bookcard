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

"""Tests for Aria2 download client."""

from unittest.mock import MagicMock, Mock, patch

from bookcard.pvr.base import (
    DownloadClientSettings,
)
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.aria2 import (
    Aria2Client,
    Aria2Proxy,
    Aria2Settings,
)


class TestAria2Proxy:
    """Test Aria2Proxy."""

    def test_init(self) -> None:
        """Test proxy initialization."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            secret="test-secret",
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        assert proxy.settings == settings
        assert proxy.rpc_url.endswith("/jsonrpc")

    def test_get_token(self) -> None:
        """Test _get_token."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            secret="test-secret",
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        token = proxy._get_token()
        assert token == "token:test-secret"

    def test_get_token_no_secret(self) -> None:
        """Test _get_token without secret."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        token = proxy._get_token()
        assert token == ""

    def test_build_xmlrpc_request(self) -> None:
        """Test _build_xmlrpc_request."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        # Private method _build_xmlrpc_request accessed via proxy.builder
        request = proxy.builder.build_request("aria2.addUri", "http://test.com")
        assert "aria2.addUri" in request
        assert "http://test.com" in request

    def test_request_success(self) -> None:
        """Test _request successful call."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><string>gid123</string></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy._request("aria2.addUri", ["http://test.com"])

        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_add_magnet(self, mock_request: MagicMock) -> None:
        """Test add_magnet."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.add_magnet("magnet:?xt=urn:btih:test")
        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_get_torrents(self, mock_request: MagicMock) -> None:
        """Test get_torrents."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        # get_torrents calls _request 3 times (active, waiting, stopped)
        mock_request.side_effect = [
            [{"gid": "gid1", "status": "active"}],
            [{"gid": "gid2", "status": "waiting"}],
            [{"gid": "gid3", "status": "stopped"}],
        ]
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.get_torrents()
        assert len(result) == 3


class TestAria2Client:
    """Test Aria2Client."""

    def test_init_with_aria2_settings(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test initialization with Aria2Settings."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, Aria2Settings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = Aria2Client(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, Aria2Settings)

    @patch.object(Aria2Proxy, "add_magnet")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_add.return_value = "gid123"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:test")
        assert result == "gid123"
        mock_add.assert_called_once()

    @patch.object(Aria2Proxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "gid": "gid1",
                "status": "active",
                "completedLength": "1000",
                "totalLength": "2000",
            },
            {
                "gid": "gid2",
                "status": "waiting",
                "completedLength": "0",
                "totalLength": "1000",
            },
        ]
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert isinstance(items, list)
        assert len(items) == 2

    @patch.object(Aria2Proxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_version.return_value = "1.36.0"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

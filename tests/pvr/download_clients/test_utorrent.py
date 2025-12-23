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

from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
    PVRProviderAuthenticationError,
)
from bookcard.pvr.download_clients.utorrent import (
    UTorrentClient,
    UTorrentProxy,
    UTorrentSettings,
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


class TestUTorrentClient:
    """Test UTorrentClient."""

    def test_init_with_utorrent_settings(self) -> None:
        """Test initialization with UTorrentSettings."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(settings=settings)
        assert isinstance(client.settings, UTorrentSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = UTorrentClient(settings=base_download_client_settings)
        assert isinstance(client.settings, UTorrentSettings)

    @patch.object(UTorrentProxy, "add_torrent_url")
    def test_add_download_magnet(self, mock_add: MagicMock) -> None:
        """Test add_download with magnet link."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_add.return_value = "ABCDEF1234567890"
        client = UTorrentClient(settings=settings)
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(UTorrentProxy, "get_torrents")
    def test_get_items(self, mock_get_torrents: MagicMock) -> None:
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
        client = UTorrentClient(settings=settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(UTorrentProxy, "remove_torrent")
    def test_remove_item(self, mock_remove: MagicMock) -> None:
        """Test remove_item."""
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(settings=settings)
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(UTorrentProxy, "get_torrents")
    def test_test_connection(self, mock_get_torrents: MagicMock) -> None:
        """Test test_connection."""
        mock_get_torrents.return_value = []
        settings = UTorrentSettings(
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = UTorrentClient(settings=settings)
        result = client.test_connection()
        assert result is True
        mock_get_torrents.assert_called_once()

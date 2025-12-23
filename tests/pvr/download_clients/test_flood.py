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

"""Tests for Flood download client."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.flood import (
    FloodClient,
    FloodProxy,
    FloodSettings,
)
from bookcard.pvr.exceptions import PVRProviderAuthenticationError


class TestFloodProxy:
    """Test FloodProxy."""

    def test_init(self) -> None:
        """Test proxy initialization."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        proxy = FloodProxy(settings)
        assert proxy.settings == settings
        assert proxy.api_url.endswith("/api")
        assert proxy._auth_cookies is None

    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_authenticate_success(self, mock_create_client: MagicMock) -> None:
        """Test successful authentication."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_cookie = MagicMock()
        mock_cookie.name = "session"
        mock_cookie.value = "session-id"
        mock_response.cookies = [mock_cookie]
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        proxy._authenticate()

        assert proxy._auth_cookies == {"session": "session-id"}

    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_authenticate_no_credentials(self, mock_create_client: MagicMock) -> None:
        """Test authentication without credentials."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username=None,
            password=None,
            timeout_seconds=30,
        )
        proxy = FloodProxy(settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires username and password"
        ):
            proxy._authenticate()

    @patch.object(FloodProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request successful call."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        proxy._auth_cookies = {"session": "test"}
        result = proxy._request("GET", "/torrents")

        assert result == {"result": "success"}

    @patch.object(FloodProxy, "_request")
    def test_get_torrents(self, mock_request: MagicMock) -> None:
        """Test get_torrents."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_request.return_value = {
            "torrents": {"abc123": {"hash": "abc123", "name": "test"}}
        }
        proxy = FloodProxy(settings)
        result = proxy.get_torrents()
        assert isinstance(result, dict)
        assert "abc123" in result


class TestFloodClient:
    """Test FloodClient."""

    def test_init_with_flood_settings(self) -> None:
        """Test initialization with FloodSettings."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(settings=settings)
        assert isinstance(client.settings, FloodSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = FloodClient(settings=base_download_client_settings)
        assert isinstance(client.settings, FloodSettings)

    @patch.object(FloodProxy, "add_torrent_url")
    def test_add_download_magnet(self, mock_add: MagicMock) -> None:
        """Test add_download with magnet link."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(settings=settings)
        # Flood extracts hash from magnet link - use lowercase hash
        result = client.add_download("magnet:?xt=urn:btih:abcdef1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(FloodProxy, "get_torrents")
    def test_get_items(self, mock_get_torrents: MagicMock) -> None:
        """Test get_items."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = {
            "ABC123": {
                "hash": "ABC123",
                "name": "Test Torrent",
                "status": ["downloading"],
                "percentComplete": 50.0,
                "sizeBytes": 1000000,
                "bytesDone": 500000,
            }
        }
        client = FloodClient(settings=settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(FloodProxy, "remove_torrent")
    def test_remove_item(self, mock_remove: MagicMock) -> None:
        """Test remove_item."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(settings=settings)
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(FloodProxy, "verify_auth")
    def test_test_connection(self, mock_verify_auth: MagicMock) -> None:
        """Test test_connection."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(settings=settings)
        result = client.test_connection()
        assert result is True
        mock_verify_auth.assert_called_once()

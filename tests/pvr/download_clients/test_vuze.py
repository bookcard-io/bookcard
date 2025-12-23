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

"""Tests for Vuze download client."""

import base64
from unittest.mock import MagicMock, Mock, patch

from bookcard.pvr.base import (
    DownloadClientSettings,
)
from bookcard.pvr.download_clients.vuze import (
    VuzeClient,
    VuzeProxy,
    VuzeSettings,
)


class TestVuzeProxy:
    """Test VuzeProxy."""

    def test_init(self, vuze_settings: VuzeSettings) -> None:
        """Test proxy initialization."""
        proxy = VuzeProxy(vuze_settings)
        assert proxy.settings == vuze_settings
        assert proxy.rpc_url.endswith("/rpc")
        assert proxy._session_id is None

    def test_build_auth_header_with_credentials(
        self, vuze_settings: VuzeSettings
    ) -> None:
        """Test _build_auth_header with credentials."""
        proxy = VuzeProxy(vuze_settings)
        header = proxy._build_auth_header()
        assert header is not None
        assert header.startswith("Basic ")
        decoded = base64.b64decode(header.split(" ")[1]).decode("utf-8")
        assert decoded == f"{vuze_settings.username}:{vuze_settings.password}"

    def test_build_auth_header_no_credentials(
        self, vuze_settings: VuzeSettings
    ) -> None:
        """Test _build_auth_header without credentials."""
        vuze_settings.username = None
        vuze_settings.password = None
        proxy = VuzeProxy(vuze_settings)
        header = proxy._build_auth_header()
        assert header is None

    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_authenticate_success_409(
        self, mock_create_client: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test authentication with 409 response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.headers = {"X-Transmission-Session-Id": "test-session-id"}
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        proxy._authenticate()

        assert proxy._session_id == "test-session-id"

    @patch.object(VuzeProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        vuze_settings: VuzeSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success", "arguments": {}}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        proxy._session_id = "test-session"
        result = proxy._request("session-get")

        assert result == {"result": "success", "arguments": {}}

    @patch.object(VuzeProxy, "_request")
    def test_get_protocol_version(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test get_protocol_version."""
        mock_request.return_value = {"arguments": {"version": "5.7.6.0"}}
        proxy = VuzeProxy(vuze_settings)
        result = proxy.get_protocol_version()
        assert result == "5.7.6.0"

    @patch.object(VuzeProxy, "_request")
    def test_add_torrent_from_url(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test add_torrent_from_url."""
        mock_request.return_value = {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "abc123"}},
        }
        proxy = VuzeProxy(vuze_settings)
        result = proxy.add_torrent_from_url("magnet:?xt=urn:btih:test")
        assert result == {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "abc123"}},
        }


class TestVuzeClient:
    """Test VuzeClient."""

    def test_init_with_vuze_settings(self, vuze_settings: VuzeSettings) -> None:
        """Test initialization with VuzeSettings."""
        client = VuzeClient(settings=vuze_settings)
        assert isinstance(client.settings, VuzeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = VuzeClient(settings=base_download_client_settings)
        assert isinstance(client.settings, VuzeSettings)

    @patch.object(VuzeProxy, "add_torrent_from_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}},
        }
        client = VuzeClient(settings=vuze_settings)
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items(
        self, mock_get_torrents: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test get_items."""
        mock_get_torrents.return_value = [
            {
                "hashString": "abc123",
                "name": "Test Torrent",
                "status": 4,  # Downloading
                "totalSize": 1000000,
                "leftUntilDone": 500000,
            }
        ]
        client = VuzeClient(settings=vuze_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(VuzeProxy, "remove_torrent")
    def test_remove_item(
        self, mock_remove: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test remove_item."""
        client = VuzeClient(settings=vuze_settings)
        result = client.remove_item("ABC123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(VuzeProxy, "get_protocol_version")
    def test_test_connection(
        self, mock_get_version: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test test_connection."""
        # Vuze requires protocol version >= 14
        mock_get_version.return_value = "15"
        client = VuzeClient(settings=vuze_settings)
        result = client.test_connection()
        assert result is True

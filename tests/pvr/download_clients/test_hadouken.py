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

"""Tests for Hadouken download client."""

import base64
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.hadouken import (
    HadoukenClient,
    HadoukenProxy,
    HadoukenSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)


class TestHadoukenProxy:
    """Test HadoukenProxy."""

    def test_init(self, hadouken_settings: HadoukenSettings) -> None:
        """Test proxy initialization."""
        proxy = HadoukenProxy(hadouken_settings)
        assert proxy.settings == hadouken_settings
        assert proxy.api_url.endswith("/api")

    def test_build_auth_header_with_credentials(
        self, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _build_auth_header with credentials."""
        proxy = HadoukenProxy(hadouken_settings)
        header = proxy._build_auth_header()
        assert header is not None
        assert header.startswith("Basic ")
        decoded = base64.b64decode(header.split(" ")[1]).decode("utf-8")
        assert decoded == f"{hadouken_settings.username}:{hadouken_settings.password}"

    def test_build_auth_header_no_credentials(
        self, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _build_auth_header without credentials."""
        hadouken_settings.username = None
        hadouken_settings.password = None
        proxy = HadoukenProxy(hadouken_settings)
        header = proxy._build_auth_header()
        assert header is None

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_success(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"data": "success"}, "error": None}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        result = proxy._request("torrents.list")

        assert result == {"data": "success"}

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_auth_error(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with authentication error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._request("torrents.list")

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_rpc_error(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with JSON-RPC error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": None,
            "error": {"message": "RPC error"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(PVRProviderError, match="JSON-RPC error"):
            proxy._request("torrents.list")

    @patch.object(HadoukenProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_torrents."""
        mock_request.return_value = [{"hash": "abc123", "name": "test"}]
        proxy = HadoukenProxy(hadouken_settings)
        result = proxy.get_torrents()
        assert len(result) == 1


class TestHadoukenClient:
    """Test HadoukenClient."""

    def test_init_with_hadouken_settings(
        self, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test initialization with HadoukenSettings."""
        client = HadoukenClient(settings=hadouken_settings)
        assert isinstance(client.settings, HadoukenSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = HadoukenClient(settings=base_download_client_settings)
        assert isinstance(client.settings, HadoukenSettings)

    @patch.object(HadoukenProxy, "add_torrent_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test add_download with magnet link."""
        client = HadoukenClient(settings=hadouken_settings)
        # Hadouken extracts hash from magnet link - use lowercase hash
        result = client.add_download("magnet:?xt=urn:btih:abcdef1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items(
        self, mock_get_torrents: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_items."""
        # Hadouken returns list of lists - need at least 27 elements
        mock_get_torrents.return_value = [
            [
                "abc123",  # 0: hash
                1,  # 1: state
                "Test Torrent",  # 2: name
                1000000,  # 3: total_size
                500000,  # 4: progress
                500000,  # 5: downloaded_bytes
                0,  # 6: upload_rate
                0,  # 7: (unused)
                0,  # 8: (unused)
                0,  # 9: download_rate
                0,  # 10: (unused)
                "test",  # 11: label (must match category)
                0,  # 12: (unused)
                0,  # 13: (unused)
                0,  # 14: (unused)
                0,  # 15: (unused)
                0,  # 16: (unused)
                0,  # 17: (unused)
                0,  # 18: (unused)
                0,  # 19: (unused)
                0,  # 20: (unused)
                "",  # 21: error
                0,  # 22: (unused)
                0,  # 23: (unused)
                0,  # 24: (unused)
                0,  # 25: (unused)
                "/path",  # 26: save_path
            ]
        ]
        client = HadoukenClient(settings=hadouken_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(HadoukenProxy, "remove_torrent")
    def test_remove_item(
        self, mock_remove: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test remove_item."""
        client = HadoukenClient(settings=hadouken_settings)
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(HadoukenProxy, "get_system_info")
    def test_test_connection(
        self, mock_get_system_info: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test test_connection."""
        mock_get_system_info.return_value = {"version": "5.0.0"}
        client = HadoukenClient(settings=hadouken_settings)
        result = client.test_connection()
        assert result is True

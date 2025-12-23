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
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.vuze import (
    VuzeClient,
    VuzeProxy,
    VuzeSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
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

    def test_handle_auth_response_409_no_session(
        self, vuze_settings: VuzeSettings
    ) -> None:
        """Test _handle_auth_response with 409 but no session ID."""
        proxy = VuzeProxy(vuze_settings)
        response = MagicMock()
        response.status_code = 409
        response.headers = {}
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return session ID"
        ):
            proxy._handle_auth_response(response)

    def test_handle_auth_response_200_success(
        self, vuze_settings: VuzeSettings
    ) -> None:
        """Test _handle_auth_response with 200 success."""
        proxy = VuzeProxy(vuze_settings)
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"result": "success"}
        proxy._handle_auth_response(response)
        assert proxy._session_id == ""

    def test_handle_auth_response_200_no_success(
        self, vuze_settings: VuzeSettings
    ) -> None:
        """Test _handle_auth_response with 200 but no success."""
        proxy = VuzeProxy(vuze_settings)
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"result": "error"}
        proxy._handle_auth_response(response)
        # Session ID should remain None

    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_authenticate_http_error(
        self, mock_create_client: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test authentication with HTTP error."""
        import httpx

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        with pytest.raises(httpx.HTTPStatusError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_authenticate_timeout(
        self, mock_create_client: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test authentication with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        with pytest.raises(httpx.TimeoutException):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_authenticate_request_error(
        self, mock_create_client: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test authentication with request error."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Request error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        with pytest.raises(httpx.RequestError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_authenticate_value_error(
        self, mock_create_client: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test authentication with ValueError."""
        mock_client = MagicMock()
        mock_client.post.side_effect = ValueError("Value error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        with pytest.raises(ValueError, match="Value error"):
            proxy._authenticate()

    def test_parse_rpc_response_error(self, vuze_settings: VuzeSettings) -> None:
        """Test _parse_rpc_response with error."""

        proxy = VuzeProxy(vuze_settings)
        response = MagicMock()
        response.json.return_value = {"result": "error message"}
        with pytest.raises(PVRProviderError, match="RPC error"):
            proxy._parse_rpc_response(response)

    def test_parse_rpc_response_json_error(self, vuze_settings: VuzeSettings) -> None:
        """Test _parse_rpc_response with JSON decode error."""
        import json

        proxy = VuzeProxy(vuze_settings)
        response = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        with pytest.raises(PVRProviderError, match="Failed to parse"):
            proxy._parse_rpc_response(response)

    @patch.object(VuzeProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_request_http_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        vuze_settings: VuzeSettings,
    ) -> None:
        """Test _request with HTTP error."""
        import httpx

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        proxy._session_id = "test-session"
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("session-get")

    @patch.object(VuzeProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.vuze.create_httpx_client")
    def test_request_timeout(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        vuze_settings: VuzeSettings,
    ) -> None:
        """Test _request with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = VuzeProxy(vuze_settings)
        proxy._session_id = "test-session"
        with pytest.raises(httpx.TimeoutException):
            proxy._request("session-get")

    @patch.object(VuzeProxy, "_request")
    def test_get_protocol_version_unknown(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test get_protocol_version with unknown version."""
        mock_request.return_value = {"arguments": {}}
        proxy = VuzeProxy(vuze_settings)
        result = proxy.get_protocol_version()
        assert result == "0"

    @patch.object(VuzeProxy, "_request")
    def test_add_torrent_from_url_with_dir(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test add_torrent_from_url with download directory."""
        mock_request.return_value = {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "abc123"}},
        }
        proxy = VuzeProxy(vuze_settings)
        result = proxy.add_torrent_from_url(
            "magnet:?xt=urn:btih:test", download_dir="/path"
        )
        assert "arguments" in result
        call_args = mock_request.call_args
        assert call_args[0][1]["download-dir"] == "/path"

    @patch.object(VuzeProxy, "_request")
    def test_add_torrent_from_file_with_dir(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test add_torrent_from_file with download directory."""
        mock_request.return_value = {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "abc123"}},
        }
        proxy = VuzeProxy(vuze_settings)
        result = proxy.add_torrent_from_file(b"content", download_dir="/path")
        assert "arguments" in result
        call_args = mock_request.call_args
        assert call_args[0][1]["download-dir"] == "/path"

    @patch.object(VuzeProxy, "_request")
    def test_get_torrents_with_ids(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test get_torrents with specific IDs."""
        mock_request.return_value = {
            "arguments": {"torrents": [{"id": 1, "name": "test"}]}
        }
        proxy = VuzeProxy(vuze_settings)
        result = proxy.get_torrents(ids=["abc123"])
        assert result == [{"id": 1, "name": "test"}]
        call_args = mock_request.call_args
        assert call_args[0][1]["ids"] == ["abc123"]

    @patch.object(VuzeProxy, "_request")
    def test_get_torrents_with_fields(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test get_torrents with specific fields."""
        mock_request.return_value = {
            "arguments": {"torrents": [{"id": 1, "name": "test"}]}
        }
        proxy = VuzeProxy(vuze_settings)
        result = proxy.get_torrents(fields=["id", "name"])
        assert result == [{"id": 1, "name": "test"}]
        call_args = mock_request.call_args
        assert call_args[0][1]["fields"] == ["id", "name"]

    @patch.object(VuzeProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, vuze_settings: VuzeSettings
    ) -> None:
        """Test remove_torrent."""
        proxy = VuzeProxy(vuze_settings)
        proxy.remove_torrent("abc123", delete_files=True)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["ids"] == ["abc123"]
        assert call_args[0][1]["delete-local-data"] is True

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

    def test_init_with_vuze_settings(
        self,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with VuzeSettings."""
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, VuzeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = VuzeClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, VuzeSettings)

    @patch.object(VuzeProxy, "add_torrent_from_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}},
        }
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"

    def test_add_download_disabled(
        self,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download when disabled."""
        client = VuzeClient(
            settings=vuze_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("magnet:?xt=urn:btih:test")

    @patch.object(VuzeProxy, "add_torrent_from_url")
    def test_add_download_duplicate(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with duplicate torrent."""
        mock_add.return_value = {
            "arguments": {"torrent-duplicate": {"hashString": "ABCDEF1234567890"}},
        }
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890")
        assert result == "ABCDEF1234567890"

    @patch.object(VuzeProxy, "add_torrent_from_url")
    def test_add_download_extract_hash_from_magnet(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download extracting hash from magnet when not in response."""
        mock_add.return_value = {"arguments": {}}
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"

    @patch.object(VuzeProxy, "add_torrent_from_url")
    def test_add_download_no_hash_error(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with no hash in response."""
        mock_add.return_value = {"arguments": {}}
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get torrent hash"):
            client.add_download("http://example.com/torrent.torrent")

    @patch.object(VuzeProxy, "add_torrent_from_file")
    def test_add_download_file_path(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}},
        }
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(str(sample_torrent_file))
        assert result == "ABCDEF1234567890"

    @patch.object(VuzeProxy, "add_torrent_from_file")
    def test_add_download_file_path_error(
        self,
        mock_add: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path error."""
        mock_add.return_value = {"arguments": {}}
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get torrent hash"):
            client.add_download("/path/to/torrent.torrent")

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
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
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items_disabled(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        client = VuzeClient(
            settings=vuze_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        items = client.get_items()
        assert items == []
        mock_get_torrents.assert_not_called()

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items_multi_file(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with multi-file torrent."""
        mock_get_torrents.return_value = [
            {
                "hashString": "abc123",
                "name": "Test Torrent",
                "status": 4,
                "totalSize": 1000000,
                "leftUntilDone": 500000,
                "downloadDir": "/downloads",
                "files": [
                    {"name": "file1.txt"},
                    {"name": "file2.txt"},
                ],
            }
        ]
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["file_path"] == "/downloads"

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items_single_file(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with single-file torrent."""
        mock_get_torrents.return_value = [
            {
                "hashString": "abc123",
                "name": "test.torrent",
                "status": 4,
                "totalSize": 1000000,
                "leftUntilDone": 500000,
                "downloadDir": "/downloads",
                "files": [
                    {"name": "other.torrent"},
                ],
            }
        ]
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["file_path"] == "/downloads/test.torrent"

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items_with_eta(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with ETA calculation."""
        mock_get_torrents.return_value = [
            {
                "hashString": "abc123",
                "name": "Test Torrent",
                "status": 4,
                "totalSize": 1000000,
                "leftUntilDone": 500000,
                "eta": 10,
                "downloadDir": "/downloads",
            }
        ]
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["eta_seconds"] == 10
        assert items[0]["download_speed_bytes_per_sec"] == 50000  # 500000 / 10

    @patch.object(VuzeProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with error."""
        mock_get_torrents.side_effect = Exception("Connection error")
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(VuzeProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("ABC123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        client = VuzeClient(
            settings=vuze_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("ABC123")

    @patch.object(VuzeProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with error."""
        mock_remove.side_effect = Exception("Remove error")
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("ABC123")

    @patch.object(VuzeProxy, "get_protocol_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        # Vuze requires protocol version >= 14
        mock_get_version.return_value = "15"
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

    @patch.object(VuzeProxy, "get_protocol_version")
    def test_test_connection_version_too_old(
        self,
        mock_get_version: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with version too old."""
        mock_get_version.return_value = "13"
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="too old"):
            client.test_connection()

    @patch.object(VuzeProxy, "get_protocol_version")
    def test_test_connection_version_not_digit(
        self,
        mock_get_version: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with non-digit version."""
        mock_get_version.return_value = "unknown"
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="too old"):
            client.test_connection()

    @patch.object(VuzeProxy, "get_protocol_version")
    def test_test_connection_error(
        self,
        mock_get_version: MagicMock,
        vuze_settings: VuzeSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with error."""
        mock_get_version.side_effect = Exception("Connection error")
        client = VuzeClient(
            settings=vuze_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

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
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.hadouken import (
    HadoukenClient,
    HadoukenProxy,
    HadoukenSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.utils.status import DownloadStatus


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

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_rpc_error_string(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with JSON-RPC error as string."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": None,
            "error": "RPC Error String",
        }
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(PVRProviderError, match="JSON-RPC error: RPC Error String"):
            proxy._request("method")

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_network_error(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request network error."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = HadoukenProxy(hadouken_settings)

        # Timeout
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._request("method")

        # HTTP Status Error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderNetworkError):
            proxy._request("method")

    @patch.object(HadoukenProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_torrents."""
        mock_request.return_value = [{"hash": "abc123", "name": "test"}]
        proxy = HadoukenProxy(hadouken_settings)
        result = proxy.get_torrents()
        assert len(result) == 1

    @patch.object(HadoukenProxy, "_request")
    def test_get_torrents_dict_response(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_torrents with dict response."""
        mock_request.return_value = {"torrents": [["item1"], "invalid"]}
        proxy = HadoukenProxy(hadouken_settings)
        result = proxy.get_torrents()
        assert len(result) == 2
        assert result[0] == ["item1"]
        assert result[1] == []  # Invalid item replaced by empty list

    @patch.object(HadoukenProxy, "_request")
    def test_get_system_info(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_system_info."""
        mock_request.return_value = {"version": "1.0"}
        proxy = HadoukenProxy(hadouken_settings)
        assert proxy.get_system_info() == {"version": "1.0"}

    @patch.object(HadoukenProxy, "_request")
    def test_get_system_info_invalid(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_system_info invalid response."""
        mock_request.return_value = "invalid"
        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(PVRProviderError, match="Unexpected response type"):
            proxy.get_system_info()

    @patch.object(HadoukenProxy, "_request")
    def test_add_torrent_url(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test add_torrent_url."""
        proxy = HadoukenProxy(hadouken_settings)
        proxy.add_torrent_url("url", category="cat")
        mock_request.assert_called_with(
            "webui.addTorrent", {"url": "url", "label": "cat"}
        )

    @patch.object(HadoukenProxy, "_request")
    def test_add_torrent_file(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test add_torrent_file."""
        mock_request.return_value = "hash"
        proxy = HadoukenProxy(hadouken_settings)
        assert proxy.add_torrent_file(b"content", category="cat") == "hash"

        call_args = mock_request.call_args
        assert call_args[0][0] == "webui.addTorrent"
        assert "file" in call_args[0][1]
        assert call_args[0][1]["label"] == "cat"

    @patch.object(HadoukenProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test remove_torrent."""
        proxy = HadoukenProxy(hadouken_settings)
        proxy.remove_torrent("hash", delete_data=True)
        mock_request.assert_called_with("webui.perform", "removedata", ["hash"])


class TestHadoukenClient:
    """Test HadoukenClient."""

    def test_init_with_hadouken_settings(
        self,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with HadoukenSettings."""
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, HadoukenSettings)
        assert client.enabled is True
        assert client.client_name == "Hadouken"

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = HadoukenClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, HadoukenSettings)

    @patch.object(HadoukenProxy, "add_torrent_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        # Hadouken extracts hash from magnet link - use lowercase hash
        result = client.add_download("magnet:?xt=urn:btih:abcdef1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(HadoukenProxy, "add_torrent_url")
    def test_add_download_magnet_invalid(
        self,
        mock_add: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with invalid magnet link."""
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?dn=test")  # No hash
        assert result == "pending"

    @patch.object(HadoukenProxy, "add_torrent_url")
    def test_add_url(
        self,
        mock_add: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_url("http://example.com/test.torrent", None, "cat", None)
        assert result == "pending"
        mock_add.assert_called_with("http://example.com/test.torrent", category="cat")

    @patch.object(HadoukenProxy, "add_torrent_file")
    def test_add_file(
        self,
        mock_add: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        sample_torrent_file: Path,
    ) -> None:
        """Test add_file."""
        mock_add.return_value = "hash"
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_file(str(sample_torrent_file), None, "cat", None)
        assert result == "HASH"
        mock_add.assert_called_once()

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        # Hadouken returns list of lists - need at least 27 elements
        mock_get_torrents.return_value = [
            [
                "abc123",  # 0: hash
                1,  # 1: state
                "Test Torrent",  # 2: name
                1000000,  # 3: total_size
                500.0,  # 4: progress (0-1000)
                500000,  # 5: downloaded_bytes
                0,  # 6: upload_rate
                0,  # 7: (unused)
                0,  # 8: (unused)
                1024,  # 9: download_rate
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
            ],
            [],  # Invalid
        ]
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"
        assert items[0]["progress"] == 0.5
        assert items[0]["download_speed_bytes_per_sec"] == 1024
        # ETA: 500000 / 1024 approx 488
        assert items[0]["eta_seconds"] == 488

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items_progress_cap(
        self,
        mock_get_torrents: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items progress cap."""
        hadouken_settings.category = None  # Disable filtering
        item = [0] * 27
        item[0] = "hash"
        item[4] = 1500.0  # > 1000
        mock_get_torrents.return_value = [item]
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert items[0]["progress"] == 1.0

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items_status_mapping(
        self,
        mock_get_torrents: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items status mapping."""
        hadouken_settings.category = None  # Disable filtering

        def make_item(
            state: int, error: str = "", progress: int = 0
        ) -> list[int | str]:
            item: list[int | str] = [0] * 27
            item[0] = "hash"
            item[1] = state
            item[4] = progress
            item[21] = error
            return item

        mock_get_torrents.return_value = [
            make_item(0, error="Error"),  # Failed
            make_item(1),  # Downloading
            make_item(2),  # Queued (checking)
            make_item(32),  # Paused
            make_item(64),  # Queued
            make_item(0, progress=1000),  # Completed
            make_item(0),  # Default Queued
        ]
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = [item["status"] for item in client.get_items()]
        assert items[0] == DownloadStatus.FAILED
        assert items[1] == DownloadStatus.DOWNLOADING
        assert items[2] == DownloadStatus.QUEUED
        assert items[3] == DownloadStatus.PAUSED
        assert items[4] == DownloadStatus.QUEUED
        assert items[5] == DownloadStatus.COMPLETED
        assert items[6] == DownloadStatus.QUEUED

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items error."""
        mock_get_torrents.side_effect = Exception("API Error")
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_get_items_disabled(
        self,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items disabled."""
        client = HadoukenClient(
            settings=hadouken_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(HadoukenProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item disabled."""
        client = HadoukenClient(
            settings=hadouken_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("abc")

    @patch.object(HadoukenProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item error."""
        mock_remove.side_effect = Exception("API Error")
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("abc")

    @patch.object(HadoukenProxy, "get_system_info")
    def test_test_connection(
        self,
        mock_get_system_info: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_system_info.return_value = {"version": "5.0.0"}
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

    @patch.object(HadoukenProxy, "get_system_info")
    def test_test_connection_error(
        self,
        mock_get_system_info: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection error."""
        mock_get_system_info.side_effect = Exception("Connect Error")
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_with_params(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with params to cover params assignment."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success", "error": None}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        result = proxy._request("test.method", "param1", "param2")
        assert result == "success"
        # Verify params were included in request
        call_args = mock_client.post.call_args
        json_data = call_args[1]["json"]
        assert "params" in json_data
        assert json_data["params"] == ["param1", "param2"]

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_http_status_error_401(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with 401 HTTPStatusError."""
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

        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_http_status_error_403(
        self, mock_create_client: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test _request with 403 HTTPStatusError."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = HadoukenProxy(hadouken_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.hadouken.handle_http_error_response")
    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_http_status_error_other(
        self,
        mock_create_client: MagicMock,
        mock_handle_error: MagicMock,
        hadouken_settings: HadoukenSettings,
    ) -> None:
        """Test _request with other HTTPStatusError to cover raise statement."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(status_code: int, response_text: str = "") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_error.side_effect = no_raise_handler

        proxy = HadoukenProxy(hadouken_settings)
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.hadouken.handle_httpx_exception")
    @patch("bookcard.pvr.download_clients.hadouken.create_httpx_client")
    def test_request_request_error_unreachable_raise(
        self,
        mock_create_client: MagicMock,
        mock_handle_exception: MagicMock,
        hadouken_settings: HadoukenSettings,
    ) -> None:
        """Test _request with RequestError to cover unreachable raise."""
        mock_client = MagicMock()
        request_error = httpx.RequestError("Network Error")
        mock_client.post.side_effect = request_error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        # Mock handler to not raise so we can reach the unreachable raise
        def no_raise_handler(error: Exception, context: str = "Request") -> None:
            """Mock handler that doesn't raise."""

        mock_handle_exception.side_effect = no_raise_handler

        proxy = HadoukenProxy(hadouken_settings)
        # The raise statement will re-raise the original exception
        with pytest.raises(httpx.RequestError):
            proxy._request("test.method")

    @patch.object(HadoukenProxy, "_request")
    def test_get_torrents_list_response(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test get_torrents with list response."""
        mock_request.return_value = [["item1"], ["item2"]]
        proxy = HadoukenProxy(hadouken_settings)
        result = proxy.get_torrents()
        assert len(result) == 2
        assert result[0] == ["item1"]
        assert result[1] == ["item2"]

    @patch.object(HadoukenProxy, "_request")
    def test_add_torrent_file_non_string_result(
        self, mock_request: MagicMock, hadouken_settings: HadoukenSettings
    ) -> None:
        """Test add_torrent_file when result is not a string."""
        mock_request.return_value = 123  # Not a string
        proxy = HadoukenProxy(hadouken_settings)
        result = proxy.add_torrent_file(b"content", category="cat")
        assert result == ""

    @patch.object(HadoukenProxy, "get_torrents")
    def test_get_items_category_filter(
        self,
        mock_get_torrents: MagicMock,
        hadouken_settings: HadoukenSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with category filtering."""
        hadouken_settings.category = "movies"
        # Hadouken returns list of lists - need at least 27 elements
        item_with_category: list[Any] = [0] * 27
        item_with_category[0] = "abc123"  # hash
        item_with_category[1] = 1  # state
        item_with_category[2] = "Test Torrent"  # name
        item_with_category[11] = "movies"  # label - matches category

        item_wrong_category: list[Any] = [0] * 27
        item_wrong_category[0] = "def456"  # hash
        item_wrong_category[1] = 1  # state
        item_wrong_category[2] = "Other Torrent"  # name
        item_wrong_category[11] = "tv"  # label - doesn't match

        mock_get_torrents.return_value = [item_with_category, item_wrong_category]
        client = HadoukenClient(
            settings=hadouken_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        # Only item with matching category should be included
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

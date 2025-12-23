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

"""Tests for NZBGet download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.nzbget import (
    NzbgetClient,
    NzbgetProxy,
    NzbgetSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.utils.status import DownloadStatus


class TestNzbgetProxy:
    """Test NzbgetProxy."""

    def test_init(self, nzbget_settings: NzbgetSettings) -> None:
        """Test proxy initialization."""
        proxy = NzbgetProxy(nzbget_settings)
        assert proxy.settings == nzbget_settings
        assert proxy.rpc_url.endswith("/jsonrpc")

    @patch("bookcard.pvr.download_clients.nzbget.create_httpx_client")
    def test_request_success(
        self, mock_create_client: MagicMock, nzbget_settings: NzbgetSettings
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

        proxy = NzbgetProxy(nzbget_settings)
        result = proxy._request("test.method", "arg1")

        # _request returns the "result" field from JSON-RPC response
        assert result == "test-result"

    @patch("bookcard.pvr.download_clients.nzbget.create_httpx_client")
    def test_request_auth_error(
        self, mock_create_client: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test _request with 401 authentication error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbgetProxy(nzbget_settings)
        with pytest.raises(PVRProviderAuthenticationError, match="invalid credentials"):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.nzbget.create_httpx_client")
    def test_request_network_errors(
        self, mock_create_client: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test _request network errors."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = NzbgetProxy(nzbget_settings)

        # Timeout
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._request("method")

        # HTTP Status Error (other than 401)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderNetworkError):
            proxy._request("method")

    @patch("bookcard.pvr.download_clients.nzbget.create_httpx_client")
    def test_request_rpc_error(
        self, mock_create_client: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test _request with RPC error."""
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

        proxy = NzbgetProxy(nzbget_settings)
        with pytest.raises(PVRProviderError, match="RPC error"):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.nzbget.create_httpx_client")
    def test_request_rpc_error_string(
        self, mock_create_client: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test _request with RPC error as string."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": None,
            "error": "String Error",
        }
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbgetProxy(nzbget_settings)
        with pytest.raises(PVRProviderError, match="NZBGet RPC error: String Error"):
            proxy._request("test.method")

    @patch.object(NzbgetProxy, "_request")
    def test_get_version(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_version."""
        mock_request.return_value = "21.1"
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.get_version()
        assert result == "21.1"

    @patch.object(NzbgetProxy, "_request")
    def test_append_nzb(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test append_nzb."""
        mock_request.return_value = 123
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.append_nzb(b"nzb content", "test.nzb", category="test")
        assert result == 123
        mock_request.assert_called_once()

    @patch.object(NzbgetProxy, "_request")
    def test_append_nzb_failed(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test append_nzb failure."""
        mock_request.return_value = 0
        proxy = NzbgetProxy(nzbget_settings)
        with pytest.raises(PVRProviderError, match="NZBGet failed to add NZB"):
            proxy.append_nzb(b"content", "test.nzb")

    def test_make_int64(
        self,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _make_int64 helper."""
        client = NzbgetClient(nzbget_settings, file_fetcher, url_router)
        assert client._make_int64(1, 0) == 4294967296
        assert client._make_int64(None, 0) is None

    @patch.object(NzbgetProxy, "_request")
    def test_get_queue(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_queue."""
        mock_request.return_value = [{"ID": 1, "NZBName": "test"}]
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.get_queue()
        assert len(result) == 1

    @patch.object(NzbgetProxy, "_request")
    def test_get_queue_invalid(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_queue invalid response."""
        mock_request.return_value = "invalid"
        proxy = NzbgetProxy(nzbget_settings)
        assert proxy.get_queue() == []

    @patch.object(NzbgetProxy, "_request")
    def test_get_history(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_history."""
        mock_request.return_value = [{"ID": 1, "NZBName": "test"}]
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.get_history()
        assert len(result) == 1

    @patch.object(NzbgetProxy, "_request")
    def test_get_history_invalid(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_history invalid response."""
        mock_request.return_value = "invalid"
        proxy = NzbgetProxy(nzbget_settings)
        assert proxy.get_history() == []

    @patch.object(NzbgetProxy, "_request")
    def test_get_global_status_invalid(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_global_status invalid response."""
        mock_request.return_value = "invalid"
        proxy = NzbgetProxy(nzbget_settings)
        assert proxy.get_global_status() == {}

    @patch.object(NzbgetProxy, "_request")
    def test_edit_queue(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test edit_queue."""
        mock_request.return_value = True
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.edit_queue("Command", 0, "", 123)
        assert result is True
        mock_request.assert_called_with("editqueue", "Command", 0, "", 123)

    @patch.object(NzbgetProxy, "_request")
    def test_remove_item(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test remove_item."""
        proxy = NzbgetProxy(nzbget_settings)
        proxy.remove_item(123)
        mock_request.assert_called_with("editqueue", "GroupFinalDelete", 0, "", 123)


class TestNzbgetClient:
    """Test NzbgetClient."""

    def test_init_with_nzbget_settings(
        self,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with NzbgetSettings."""
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, NzbgetSettings)
        assert client.enabled is True
        assert client.client_name == "NZBGet"

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = NzbgetClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, NzbgetSettings)

    @patch.object(NzbgetProxy, "append_nzb")
    def test_add_download_nzb_file(
        self,
        mock_append: MagicMock,
        nzbget_settings: NzbgetSettings,
        sample_nzb_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with NZB file path."""
        mock_append.return_value = 123
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(str(sample_nzb_file))
        assert result == "123"
        mock_append.assert_called_once()

    @patch.object(NzbgetProxy, "append_nzb")
    def test_add_url(
        self,
        mock_append: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        mock_append.return_value = 123
        mock_file_fetcher = MagicMock(spec=FileFetcherProtocol)
        mock_file_fetcher.fetch_with_filename.return_value = (b"content", "file.nzb")

        client = NzbgetClient(
            settings=nzbget_settings,
            file_fetcher=mock_file_fetcher,
            url_router=url_router,
        )
        result = client.add_url("http://example.com/test.nzb", None, "cat", None)
        assert result == "123"
        mock_append.assert_called_once()

    @patch.object(NzbgetProxy, "get_global_status")
    @patch.object(NzbgetProxy, "get_queue")
    @patch.object(NzbgetProxy, "get_history")
    def test_get_items(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        mock_get_global_status: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        mock_get_global_status.return_value = {"DownloadRate": 1000000}
        mock_get_queue.return_value = [
            {
                "NZBID": 1,
                "NZBName": "Test NZB",
                "Status": "DOWNLOADING",
                "FileSizeHi": 0,
                "FileSizeLo": 1000000,
                "RemainingSizeHi": 0,
                "RemainingSizeLo": 500000,
            }
        ]
        mock_get_history.return_value = [
            {
                "ID": 2,
                "Name": "Completed NZB",
                "Status": "SUCCESS",
                "FileSizeHi": 0,
                "FileSizeLo": 2000000,
                "FinalDir": "/downloads/completed",
            },
            {
                "ID": 3,
                "Name": "Ignored NZB",
                "Status": "DELETED",
            },
        ]
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 2

        # Check queue item
        assert items[0]["client_item_id"] == "1"
        assert items[0]["progress"] == 0.5
        assert items[0]["status"] == DownloadStatus.DOWNLOADING
        assert items[0]["download_speed_bytes_per_sec"] == 1000000
        assert items[0]["eta_seconds"] == 0  # 500000 / 1000000 = 0.5 -> 0

        # Check history item
        assert items[1]["client_item_id"] == "2"
        assert items[1]["status"] == DownloadStatus.COMPLETED
        assert items[1]["progress"] == 1.0
        assert items[1]["file_path"] == "/downloads/completed"

    @patch.object(NzbgetProxy, "get_global_status")
    @patch.object(NzbgetProxy, "get_queue")
    @patch.object(NzbgetProxy, "get_history")
    def test_get_items_status_mapping(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        mock_get_global_status: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items status mapping."""
        mock_get_global_status.return_value = {}
        mock_get_queue.return_value = [
            {"NZBID": 1, "Status": "PAUSED"},
            {"NZBID": 2, "Status": "QUEUED"},
            {"NZBID": 3, "Status": "FETCHING"},
            {"NZBID": 4, "Status": "UNKNOWN"},
        ]
        mock_get_history.return_value = []
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()

        assert items[0]["status"] == DownloadStatus.PAUSED
        assert items[1]["status"] == DownloadStatus.QUEUED
        assert items[2]["status"] == DownloadStatus.QUEUED
        assert items[3]["status"] == DownloadStatus.DOWNLOADING

    @patch.object(NzbgetProxy, "get_queue")
    @patch.object(NzbgetProxy, "get_history")
    def test_get_items_error(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items error."""
        mock_get_queue.side_effect = Exception("API Error")
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_get_items_disabled(
        self,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items disabled."""
        client = NzbgetClient(
            settings=nzbget_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(NzbgetProxy, "remove_item")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("123", _delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with(123)

    def test_remove_item_disabled(
        self,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item disabled."""
        client = NzbgetClient(
            settings=nzbget_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("123")

    @patch.object(NzbgetProxy, "remove_item")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item error."""
        mock_remove.side_effect = Exception("API Error")
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("123")

    @patch.object(NzbgetProxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "21.1"
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

    @patch.object(NzbgetProxy, "get_version")
    def test_test_connection_error(
        self,
        mock_get_version: MagicMock,
        nzbget_settings: NzbgetSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection error."""
        mock_get_version.side_effect = Exception("Connect Error")
        client = NzbgetClient(
            settings=nzbget_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

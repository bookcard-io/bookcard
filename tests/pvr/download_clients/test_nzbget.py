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

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.nzbget import (
    NzbgetClient,
    NzbgetProxy,
    NzbgetSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)


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
    def test_append_nzb_invalid_id(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test append_nzb with invalid ID."""
        mock_request.return_value = 0
        proxy = NzbgetProxy(nzbget_settings)
        with pytest.raises(PVRProviderError, match="failed to add NZB"):
            proxy.append_nzb(b"nzb content", "test.nzb")

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
    def test_get_history(
        self, mock_request: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test get_history."""
        mock_request.return_value = [{"ID": 1, "NZBName": "test"}]
        proxy = NzbgetProxy(nzbget_settings)
        result = proxy.get_history()
        assert len(result) == 1

    @patch.object(NzbgetProxy, "remove_item")
    def test_remove_item(
        self, mock_remove: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test remove_item."""
        proxy = NzbgetProxy(nzbget_settings)
        proxy.remove_item(123)
        mock_remove.assert_called_once_with(123)


class TestNzbgetClient:
    """Test NzbgetClient."""

    def test_init_with_nzbget_settings(self, nzbget_settings: NzbgetSettings) -> None:
        """Test initialization with NzbgetSettings."""
        client = NzbgetClient(settings=nzbget_settings)
        assert isinstance(client.settings, NzbgetSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = NzbgetClient(settings=base_download_client_settings)
        assert isinstance(client.settings, NzbgetSettings)

    @patch.object(NzbgetProxy, "append_nzb")
    def test_add_download_nzb_file(
        self,
        mock_append: MagicMock,
        nzbget_settings: NzbgetSettings,
        sample_nzb_file: Path,
    ) -> None:
        """Test add_download with NZB file path."""
        mock_append.return_value = 123
        client = NzbgetClient(settings=nzbget_settings)
        result = client.add_download(str(sample_nzb_file))
        assert result == "123"
        mock_append.assert_called_once()

    @patch.object(NzbgetProxy, "append_nzb")
    @patch("bookcard.pvr.download_clients.nzbget.httpx.Client")
    def test_add_download_nzb_url(
        self,
        mock_client_class: MagicMock,
        mock_append: MagicMock,
        nzbget_settings: NzbgetSettings,
        sample_nzb_url: str,
    ) -> None:
        """Test add_download with NZB URL."""
        mock_append.return_value = 123
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        client = NzbgetClient(settings=nzbget_settings)
        result = client.add_download(sample_nzb_url)
        assert result == "123"

    @patch.object(NzbgetProxy, "get_global_status")
    @patch.object(NzbgetProxy, "get_queue")
    @patch.object(NzbgetProxy, "get_history")
    def test_get_items(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        mock_get_global_status: MagicMock,
        nzbget_settings: NzbgetSettings,
    ) -> None:
        """Test get_items."""
        mock_get_global_status.return_value = {"DownloadRate": 1000000}
        mock_get_queue.return_value = [
            {
                "ID": 1,
                "NZBName": "Test NZB",
                "Status": "DOWNLOADING",
                "FileSizeMB": 1000,
                "RemainingSizeMB": 500,
                "DownloadedSizeMB": 500,
            }
        ]
        mock_get_history.return_value = []
        client = NzbgetClient(settings=nzbget_settings)
        items = client.get_items()
        assert len(items) > 0

    @patch.object(NzbgetProxy, "remove_item")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        nzbget_settings: NzbgetSettings,
    ) -> None:
        """Test remove_item."""
        client = NzbgetClient(settings=nzbget_settings)
        result = client.remove_item("123", _delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with(123)

    @patch.object(NzbgetProxy, "get_version")
    def test_test_connection(
        self, mock_get_version: MagicMock, nzbget_settings: NzbgetSettings
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "21.1"
        client = NzbgetClient(settings=nzbget_settings)
        result = client.test_connection()
        assert result is True

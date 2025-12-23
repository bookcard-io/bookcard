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

"""Tests for rTorrent download client."""

from unittest.mock import MagicMock, Mock, patch
from xml.etree import ElementTree as ET  # noqa: S405

import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
    PVRProviderError,
)
from bookcard.pvr.download_clients.rtorrent import (
    RTorrentClient,
    RTorrentProxy,
    RTorrentSettings,
)


class TestRTorrentProxy:
    """Test RTorrentProxy."""

    def test_init(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test proxy initialization."""
        proxy = RTorrentProxy(rtorrent_settings)
        assert proxy.settings == rtorrent_settings
        assert proxy.rpc_url.endswith("/RPC2")

    def test_add_xmlrpc_array(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_array."""
        proxy = RTorrentProxy(rtorrent_settings)
        data_elem = ET.Element("data")
        proxy._add_xmlrpc_array(data_elem, ["test1", "test2", 123])
        assert len(data_elem.findall("value")) == 3

    def test_add_xmlrpc_struct(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_struct."""
        proxy = RTorrentProxy(rtorrent_settings)
        struct_elem = ET.Element("struct")
        proxy._add_xmlrpc_struct(struct_elem, {"key1": "value1", "key2": 123})
        assert len(struct_elem.findall("member")) == 2

    def test_build_xmlrpc_request(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _build_xmlrpc_request."""
        proxy = RTorrentProxy(rtorrent_settings)
        request = proxy._build_xmlrpc_request("test.method", "arg1", 123)
        assert "test.method" in request
        assert "arg1" in request

    def test_check_xmlrpc_fault_no_fault(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _check_xmlrpc_fault with no fault."""
        proxy = RTorrentProxy(rtorrent_settings)
        root = ET.Element("methodResponse")
        params = ET.SubElement(root, "params")
        param = ET.SubElement(params, "param")
        value = ET.SubElement(param, "value")
        string_elem = ET.SubElement(value, "string")
        string_elem.text = "success"
        # Should not raise
        proxy._check_xmlrpc_fault(root)

    def test_check_xmlrpc_fault_with_fault(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _check_xmlrpc_fault with fault."""
        proxy = RTorrentProxy(rtorrent_settings)
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        value = ET.SubElement(fault, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        name = ET.SubElement(member, "name")
        name.text = "faultString"
        value2 = ET.SubElement(member, "value")
        string_elem = ET.SubElement(value2, "string")
        string_elem.text = "Test error"
        with pytest.raises(PVRProviderError, match="XML-RPC fault"):
            proxy._check_xmlrpc_fault(root)

    @patch("bookcard.pvr.download_clients.rtorrent.create_httpx_client")
    def test_request_success(
        self, mock_create_client: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><string>success</string></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy._request("test.method", "arg1")

        assert result == "success"

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_url(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_url."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.add_torrent_url("magnet:?xt=urn:btih:test")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_torrents."""
        # rTorrent returns list of lists with torrent data
        mock_request.return_value = [
            ["torrent1", "hash1", "/path1", "", 1000, 500, 0, 0, 0, 0, 0, 0, 0],
            ["torrent2", "hash2", "/path2", "", 2000, 1000, 0, 0, 0, 0, 0, 0, 0],
        ]
        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy.get_torrents()
        assert len(result) == 2
        assert result[0]["hash"] == "hash1"


class TestRTorrentClient:
    """Test RTorrentClient."""

    def test_init_with_rtorrent_settings(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test initialization with RTorrentSettings."""
        client = RTorrentClient(settings=rtorrent_settings)
        assert isinstance(client.settings, RTorrentSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = RTorrentClient(settings=base_download_client_settings)
        assert isinstance(client.settings, RTorrentSettings)

    @patch.object(RTorrentProxy, "add_torrent_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_download with magnet link."""
        client = RTorrentClient(settings=rtorrent_settings)
        # rTorrent extracts hash from magnet link - use lowercase
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "ABC123"
        mock_add.assert_called_once()

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items(
        self, mock_get_torrents: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_items."""
        mock_get_torrents.return_value = [
            {"hash": "hash1", "label": "test", "name": "Test 1"},
            {"hash": "hash2", "label": "test", "name": "Test 2"},
        ]
        client = RTorrentClient(settings=rtorrent_settings)
        items = client.get_items()
        assert len(items) == 2

    @patch.object(RTorrentProxy, "get_version")
    def test_test_connection(
        self, mock_get_version: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "0.9.8"
        client = RTorrentClient(settings=rtorrent_settings)
        result = client.test_connection()
        assert result is True

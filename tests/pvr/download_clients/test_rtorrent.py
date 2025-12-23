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

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from xml.etree import ElementTree as ET  # noqa: S405

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.rtorrent import (
    RTorrentClient,
    RTorrentProxy,
    RTorrentSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
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

    def test_add_xmlrpc_array_with_int(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _add_xmlrpc_array with int values."""
        proxy = RTorrentProxy(rtorrent_settings)
        data_elem = ET.Element("data")
        proxy._add_xmlrpc_array(data_elem, [123, 456])
        values = data_elem.findall("value")
        assert len(values) == 2
        assert values[0].find("int") is not None

    def test_add_xmlrpc_struct(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_struct."""
        proxy = RTorrentProxy(rtorrent_settings)
        struct_elem = ET.Element("struct")
        proxy._add_xmlrpc_struct(struct_elem, {"key1": "value1", "key2": 123})
        assert len(struct_elem.findall("member")) == 2

    def test_add_xmlrpc_struct_with_int(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _add_xmlrpc_struct with int values."""
        proxy = RTorrentProxy(rtorrent_settings)
        struct_elem = ET.Element("struct")
        proxy._add_xmlrpc_struct(struct_elem, {"key": 456})
        members = struct_elem.findall("member")
        assert len(members) == 1
        assert members[0].find("value/int") is not None

    def test_build_xmlrpc_request(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _build_xmlrpc_request."""
        proxy = RTorrentProxy(rtorrent_settings)
        request = proxy._build_xmlrpc_request("test.method", "arg1", 123)
        assert "test.method" in request
        assert "arg1" in request

    def test_add_xmlrpc_param_bytes(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_param with bytes parameter."""
        proxy = RTorrentProxy(rtorrent_settings)
        params_elem = ET.Element("params")
        proxy._add_xmlrpc_param(params_elem, b"test bytes")
        param = params_elem.find("param/value/base64")
        assert param is not None
        assert param.text is not None

    def test_add_xmlrpc_param_list(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_param with list parameter."""
        proxy = RTorrentProxy(rtorrent_settings)
        params_elem = ET.Element("params")
        proxy._add_xmlrpc_param(params_elem, ["item1", "item2"])
        param = params_elem.find("param/value/array")
        assert param is not None

    def test_add_xmlrpc_param_dict(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _add_xmlrpc_param with dict parameter."""
        proxy = RTorrentProxy(rtorrent_settings)
        params_elem = ET.Element("params")
        proxy._add_xmlrpc_param(params_elem, {"key": "value"})
        param = params_elem.find("param/value/struct")
        assert param is not None

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

    def test_check_xmlrpc_fault_no_fault_value(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _check_xmlrpc_fault with fault but no value."""
        proxy = RTorrentProxy(rtorrent_settings)
        root = ET.Element("methodResponse")
        ET.SubElement(root, "fault")
        # Should not raise if no value
        proxy._check_xmlrpc_fault(root)

    def test_check_xmlrpc_fault_no_string(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _check_xmlrpc_fault with fault but no string."""
        proxy = RTorrentProxy(rtorrent_settings)
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        value = ET.SubElement(fault, "value")
        ET.SubElement(value, "struct")
        # No string element
        # Should not raise
        proxy._check_xmlrpc_fault(root)

    def test_parse_xmlrpc_array(self, rtorrent_settings: RTorrentSettings) -> None:
        """Test _parse_xmlrpc_array."""
        proxy = RTorrentProxy(rtorrent_settings)
        data = ET.Element("data")
        value1 = ET.SubElement(data, "value")
        string1 = ET.SubElement(value1, "string")
        string1.text = "test1"
        value2 = ET.SubElement(data, "value")
        int1 = ET.SubElement(value2, "int")
        int1.text = "123"
        value3 = ET.SubElement(data, "value")
        i8 = ET.SubElement(value3, "i8")
        i8.text = "456"
        result = proxy._parse_xmlrpc_array(data)
        assert result == ["test1", 123, 456]

    def test_parse_xmlrpc_array_empty_text(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_array with empty text."""
        proxy = RTorrentProxy(rtorrent_settings)
        data = ET.Element("data")
        value = ET.SubElement(data, "value")
        int_elem = ET.SubElement(value, "int")
        int_elem.text = None
        result = proxy._parse_xmlrpc_array(data)
        assert result == [0]

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

    def test_parse_xmlrpc_response_parse_error(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_response with parse error."""
        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(PVRProviderError, match="Failed to parse"):
            proxy._parse_xmlrpc_response("invalid xml")

    def test_parse_xmlrpc_response_no_params(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_response with no params."""
        proxy = RTorrentProxy(rtorrent_settings)
        xml = '<?xml version="1.0"?><methodResponse><params></params></methodResponse>'
        result = proxy._parse_xmlrpc_response(xml)
        assert result is None

    def test_parse_xmlrpc_response_int(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_response with int value."""
        proxy = RTorrentProxy(rtorrent_settings)
        xml = '<?xml version="1.0"?><methodResponse><params><param><value><int>123</int></value></param></params></methodResponse>'
        result = proxy._parse_xmlrpc_response(xml)
        assert result == 123

    def test_parse_xmlrpc_response_int_empty(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_response with empty int."""
        proxy = RTorrentProxy(rtorrent_settings)
        xml = '<?xml version="1.0"?><methodResponse><params><param><value><int></int></value></param></params></methodResponse>'
        result = proxy._parse_xmlrpc_response(xml)
        assert result == 0

    def test_parse_xmlrpc_response_array(
        self, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _parse_xmlrpc_response with array."""
        proxy = RTorrentProxy(rtorrent_settings)
        xml = '<?xml version="1.0"?><methodResponse><params><param><value><array><data><value><string>test</string></value></data></array></value></param></params></methodResponse>'
        result = proxy._parse_xmlrpc_response(xml)
        assert result == ["test"]

    @patch("bookcard.pvr.download_clients.rtorrent.create_httpx_client")
    def test_request_with_auth(
        self, mock_create_client: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _request with authentication."""
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
        # Check auth header was added
        call_args = mock_client.post.call_args
        assert "Authorization" in call_args.kwargs.get("headers", {})

    @patch("bookcard.pvr.download_clients.rtorrent.create_httpx_client")
    def test_request_401_error(
        self, mock_create_client: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _request with 401 error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = RTorrentProxy(rtorrent_settings)

        def _raise_auth_error() -> None:
            """Raise authentication error."""
            msg = "rTorrent authentication failed"
            raise PVRProviderAuthenticationError(msg)

        with pytest.raises(PVRProviderAuthenticationError):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.rtorrent.create_httpx_client")
    def test_request_http_error(
        self, mock_create_client: MagicMock, rtorrent_settings: RTorrentSettings
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

        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("test.method")

    @patch("bookcard.pvr.download_clients.rtorrent.create_httpx_client")
    def test_request_timeout(
        self, mock_create_client: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test _request with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(httpx.TimeoutException):
            proxy._request("test.method")

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
    def test_add_torrent_url_with_label(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_url with label."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.add_torrent_url("magnet:?xt=urn:btih:test", label="test-label")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_url_with_directory(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_url with directory."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.add_torrent_url("magnet:?xt=urn:btih:test", directory="/downloads")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_url_error(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_url with error."""
        mock_request.return_value = 1
        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(PVRProviderError, match="failed to add torrent"):
            proxy.add_torrent_url("magnet:?xt=urn:btih:test")

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_file(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_file."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.add_torrent_file("test.torrent", b"torrent content")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_file_with_label(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_file with label."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.add_torrent_file("test.torrent", b"content", label="test-label")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_add_torrent_file_error(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test add_torrent_file with error."""
        mock_request.return_value = 1
        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(PVRProviderError, match="failed to add torrent"):
            proxy.add_torrent_file("test.torrent", b"content")

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

    @patch.object(RTorrentProxy, "_request")
    def test_get_torrents_empty(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_torrents with empty result."""
        mock_request.return_value = None
        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy.get_torrents()
        assert result == []

    @patch.object(RTorrentProxy, "_request")
    def test_get_torrents_not_list(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_torrents with non-list result."""
        mock_request.return_value = "not a list"
        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy.get_torrents()
        assert result == []

    @patch.object(RTorrentProxy, "_request")
    def test_get_torrents_short_list(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_torrents with short list items."""
        mock_request.return_value = [
            ["torrent1", "hash1"],  # Too short
        ]
        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy.get_torrents()
        assert len(result) == 0

    @patch.object(RTorrentProxy, "_request")
    def test_get_torrents_with_all_fields(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test get_torrents with all fields."""
        mock_request.return_value = [
            [
                "torrent1",
                "hash1",
                "/path1",
                "label1",
                1000,
                500,
                100,
                2,
                1,
                1,
                1,
                1234567890,
            ],
        ]
        proxy = RTorrentProxy(rtorrent_settings)
        result = proxy.get_torrents()
        assert len(result) == 1
        assert result[0]["name"] == "torrent1"
        assert result[0]["hash"] == "hash1"
        assert result[0]["label"] == "label1"

    @patch.object(RTorrentProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test remove_torrent."""
        mock_request.return_value = 0
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.remove_torrent("hash123")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_remove_torrent_error(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test remove_torrent with error."""
        mock_request.return_value = 1
        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(PVRProviderError, match="failed to remove torrent"):
            proxy.remove_torrent("hash123")

    @patch.object(RTorrentProxy, "_request")
    def test_set_torrent_label(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test set_torrent_label."""
        mock_request.return_value = "test-label"
        proxy = RTorrentProxy(rtorrent_settings)
        proxy.set_torrent_label("hash123", "test-label")
        mock_request.assert_called_once()

    @patch.object(RTorrentProxy, "_request")
    def test_set_torrent_label_error(
        self, mock_request: MagicMock, rtorrent_settings: RTorrentSettings
    ) -> None:
        """Test set_torrent_label with error."""
        mock_request.return_value = "different-label"
        proxy = RTorrentProxy(rtorrent_settings)
        with pytest.raises(PVRProviderError, match="failed to set label"):
            proxy.set_torrent_label("hash123", "test-label")


class TestRTorrentClient:
    """Test RTorrentClient."""

    def test_init_with_rtorrent_settings(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with RTorrentSettings."""
        client = RTorrentClient(
            settings=rtorrent_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, RTorrentSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = RTorrentClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, RTorrentSettings)

    @patch.object(RTorrentProxy, "add_torrent_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        # rTorrent extracts hash from magnet link - use lowercase
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "ABC123"
        mock_add.assert_called_once()

    @patch.object(RTorrentProxy, "add_torrent_url")
    def test_add_download_magnet_no_hash(
        self,
        mock_add: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link without hash."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?dn=test")
        assert result == "pending"
        mock_add.assert_called_once()

    @patch("bookcard.pvr.download_clients.rtorrent.httpx.Client")
    @patch.object(RTorrentProxy, "add_torrent_file")
    def test_add_download_http_url(
        self,
        mock_add_file: MagicMock,
        mock_client_class: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with HTTP URL."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"torrent content"
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("http://example.com/torrent.torrent")
        assert result == "pending"
        mock_add_file.assert_called_once()

    @patch.object(RTorrentProxy, "add_torrent_file")
    def test_add_download_file_path(
        self,
        mock_add_file: MagicMock,
        rtorrent_settings: RTorrentSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(str(sample_torrent_file))
        assert result == "pending"
        mock_add_file.assert_called_once()

    @patch.object(RTorrentProxy, "add_torrent_file")
    def test_add_download_file_path_with_title(
        self,
        mock_add_file: MagicMock,
        rtorrent_settings: RTorrentSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path and title."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download(
            str(sample_torrent_file), title="custom-title.torrent"
        )
        assert result == "pending"
        mock_add_file.assert_called_once()

    def test_add_download_invalid_url(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with invalid URL."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Invalid download URL"):
            client.add_download("invalid://url")

    def test_add_download_disabled(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download when disabled."""
        client = RTorrentClient(
            settings=rtorrent_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("magnet:?xt=urn:btih:test")

    @patch.object(RTorrentProxy, "add_torrent_url")
    def test_add_download_with_category(
        self,
        mock_add: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with category."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        client.add_download("magnet:?xt=urn:btih:test", category="test-category")
        mock_add.assert_called_once()
        # Check label was passed
        call_kwargs = mock_add.call_args[1]
        assert call_kwargs.get("label") == "test-category"

    @patch.object(RTorrentProxy, "add_torrent_url")
    def test_add_download_with_download_path(
        self,
        mock_add: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with download_path."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        client.add_download("magnet:?xt=urn:btih:test", download_path="/custom/path")
        mock_add.assert_called_once()
        # Check directory was passed
        call_kwargs = mock_add.call_args[1]
        assert call_kwargs.get("directory") == "/custom/path"

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        mock_get_torrents.return_value = [
            {"hash": "hash1", "label": "test", "name": "Test 1"},
            {"hash": "hash2", "label": "test", "name": "Test 2"},
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 2

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_disabled(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        client = RTorrentClient(
            settings=rtorrent_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        items = client.get_items()
        assert items == []
        mock_get_torrents.assert_not_called()

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_no_hash(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with torrent without hash."""
        mock_get_torrents.return_value = [
            {"hash": "", "label": "test", "name": "Test 1"},
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 0

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_with_category_filter(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with category filter."""
        mock_get_torrents.return_value = [
            {"hash": "hash1", "label": "test", "name": "Test 1"},
            {"hash": "hash2", "label": "other", "name": "Test 2"},
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        # Only items with matching category should be included
        assert len(items) == 1
        assert items[0]["client_item_id"] == "HASH1"

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_complete_torrent(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with completed torrent."""
        mock_get_torrents.return_value = [
            {
                "hash": "hash1",
                "label": "test",
                "name": "Test 1",
                "complete": 1,
                "is_active": 0,
                "size_bytes": 1000,
                "left_bytes": 0,
                "down_rate": 0,
            },
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["status"] == "completed"
        assert items[0]["progress"] == 1.0

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_downloading_torrent(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with downloading torrent."""
        mock_get_torrents.return_value = [
            {
                "hash": "hash1",
                "label": "test",
                "name": "Test 1",
                "complete": 0,
                "is_active": 1,
                "size_bytes": 1000,
                "left_bytes": 500,
                "down_rate": 100,
            },
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["status"] == "downloading"
        assert items[0]["progress"] == 0.5

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_paused_torrent(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with paused torrent."""
        mock_get_torrents.return_value = [
            {
                "hash": "hash1",
                "label": "test",
                "name": "Test 1",
                "complete": 0,
                "is_active": 0,
                "size_bytes": 1000,
                "left_bytes": 500,
                "down_rate": 0,
            },
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["status"] == "paused"

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_with_eta(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with ETA calculation."""
        mock_get_torrents.return_value = [
            {
                "hash": "hash1",
                "label": "test",
                "name": "Test 1",
                "complete": 0,
                "is_active": 1,
                "size_bytes": 1000,
                "left_bytes": 500,
                "down_rate": 100,  # 100 bytes/sec
            },
        ]
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["eta_seconds"] == 5  # 500 bytes / 100 bytes/sec

    @patch.object(RTorrentProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with error."""
        mock_get_torrents.side_effect = Exception("Connection error")
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(RTorrentProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("HASH123")
        assert result is True
        mock_remove.assert_called_once_with("hash123")

    def test_remove_item_disabled(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        client = RTorrentClient(
            settings=rtorrent_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("HASH123")

    @patch.object(RTorrentProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with error."""
        mock_remove.side_effect = Exception("Remove error")
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("HASH123")

    @patch.object(RTorrentProxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "0.9.8"
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

    @patch.object(RTorrentProxy, "get_version")
    def test_test_connection_error(
        self,
        mock_get_version: MagicMock,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with error."""
        mock_get_version.side_effect = Exception("Connection error")
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    def test_map_torrent_status_completed(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _map_torrent_status with completed torrent."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        torrent = {"complete": 1, "is_active": 0}
        status = client._map_torrent_status(torrent)
        assert status == "completed"

    def test_map_torrent_status_downloading(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _map_torrent_status with downloading torrent."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        torrent = {"complete": 0, "is_active": 1}
        status = client._map_torrent_status(torrent)
        assert status == "downloading"

    def test_map_torrent_status_paused(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _map_torrent_status with paused torrent."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        torrent = {"complete": 0, "is_active": 0}
        status = client._map_torrent_status(torrent)
        assert status == "paused"

    def test_calculate_progress(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _calculate_progress."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        progress = client._calculate_progress(1000, 500)
        assert progress == 0.5

    def test_calculate_progress_zero_total(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _calculate_progress with zero total."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        progress = client._calculate_progress(0, 0)
        assert progress == 0.0

    def test_calculate_progress_none(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _calculate_progress with None values."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        progress = client._calculate_progress(None, None)
        assert progress == 0.0

    def test_calculate_progress_over_100(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _calculate_progress that exceeds 1.0."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        progress = client._calculate_progress(1000, -100)
        assert progress == 1.0  # Should be capped at 1.0

    def test_build_download_item(
        self,
        rtorrent_settings: RTorrentSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _build_download_item."""
        client = RTorrentClient(
            settings=rtorrent_settings, file_fetcher=file_fetcher, url_router=url_router
        )
        torrent = {
            "hash": "hash1",
            "name": "Test",
            "complete": 0,
            "is_active": 1,
            "size_bytes": 1000,
            "left_bytes": 500,
            "down_rate": 100,
        }
        item = client._build_download_item(torrent)
        assert item["client_item_id"] == "HASH1"
        assert item["title"] == "Test"
        assert item["status"] == "downloading"
        assert item["progress"] == 0.5
        assert item["size_bytes"] == 1000
        assert item["downloaded_bytes"] == 500
        assert item["download_speed_bytes_per_sec"] == 100
        assert item["eta_seconds"] == 5

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

"""Tests for Aria2 download client."""

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.aria2 import (
    Aria2Client,
    Aria2Proxy,
    Aria2Settings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)


class TestAria2Proxy:
    """Test Aria2Proxy."""

    def test_init(self) -> None:
        """Test proxy initialization."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            secret="test-secret",
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        assert proxy.settings == settings
        assert proxy.rpc_url.endswith("/jsonrpc")

    def test_get_token(self) -> None:
        """Test _get_token."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            secret="test-secret",
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        token = proxy._get_token()
        assert token == "token:test-secret"

    def test_get_token_no_secret(self) -> None:
        """Test _get_token without secret."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        token = proxy._get_token()
        assert token == ""

    def test_build_xmlrpc_request(self) -> None:
        """Test _build_xmlrpc_request."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())
        # Private method _build_xmlrpc_request accessed via proxy.builder
        request = proxy.builder.build_request("aria2.addUri", "http://test.com")
        assert "aria2.addUri" in request
        assert "http://test.com" in request

    def test_request_success(self) -> None:
        """Test _request successful call."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><string>gid123</string></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy._request("aria2.addUri", ["http://test.com"])

        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_add_magnet(self, mock_request: MagicMock) -> None:
        """Test add_magnet."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.add_magnet("magnet:?xt=urn:btih:test")
        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_get_torrents(self, mock_request: MagicMock) -> None:
        """Test get_torrents."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        # get_torrents calls _request 3 times (active, waiting, stopped)
        mock_request.side_effect = [
            [{"gid": "gid1", "status": "active"}],
            [{"gid": "gid2", "status": "waiting"}],
            [{"gid": "gid3", "status": "stopped"}],
        ]
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.get_torrents()
        assert len(result) == 3


class TestAria2Client:
    """Test Aria2Client."""

    def test_init_with_aria2_settings(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test initialization with Aria2Settings."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, Aria2Settings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = Aria2Client(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, Aria2Settings)

    @patch.object(Aria2Proxy, "add_magnet")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_add.return_value = "gid123"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?xt=urn:btih:test")
        assert result == "gid123"
        mock_add.assert_called_once()

    @patch.object(Aria2Proxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {
                "gid": "gid1",
                "status": "active",
                "completedLength": "1000",
                "totalLength": "2000",
            },
            {
                "gid": "gid2",
                "status": "waiting",
                "completedLength": "0",
                "totalLength": "1000",
            },
        ]
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert isinstance(items, list)
        assert len(items) == 2

    @patch.object(Aria2Proxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_version.return_value = "1.36.0"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True

    def test_raise_auth_error(self) -> None:
        """Test _raise_auth_error raises authentication error."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        proxy = Aria2Proxy(settings, Mock())

        with pytest.raises(
            PVRProviderAuthenticationError, match="Aria2 authentication failed"
        ):
            proxy._raise_auth_error()

    def test_request_with_auth(self) -> None:
        """Test _request with username and password."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            username="user",
            password="pass",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><string>gid123</string></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy._request("aria2.addUri", ["http://test.com"])

        assert result == "gid123"
        # Verify auth tuple was passed
        call_args = mock_client.post.call_args
        assert call_args[1]["auth"] == ("user", "pass")

    def test_request_401_status(self) -> None:
        """Test _request with 401 status code."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(
            PVRProviderAuthenticationError, match="Aria2 authentication failed"
        ):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_parse_error(self) -> None:
        """Test _request with XML parse error."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "invalid xml"
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(
            PVRProviderError, match="Failed to parse Aria2 XML-RPC response"
        ):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_http_status_error_401(self) -> None:
        """Test _request with HTTPStatusError 401."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(
            PVRProviderAuthenticationError, match="Aria2 authentication failed"
        ):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_http_status_error_403(self) -> None:
        """Test _request with HTTPStatusError 403."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(
            PVRProviderAuthenticationError, match="Aria2 authentication failed"
        ):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_http_status_error_other(self) -> None:
        """Test _request with HTTPStatusError other status."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        # handle_http_error_response raises PVRProviderNetworkError
        # The raise statement re-raises the original HTTPStatusError
        with pytest.raises((httpx.HTTPStatusError, PVRProviderNetworkError)):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_request_error(self) -> None:
        """Test _request with RequestError."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        error = httpx.RequestError("Connection failed", request=MagicMock())
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        # handle_httpx_exception raises PVRProviderNetworkError
        # The raise statement re-raises the original RequestError
        with pytest.raises((httpx.RequestError, PVRProviderNetworkError)):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_timeout_exception(self) -> None:
        """Test _request with TimeoutException."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        error = httpx.TimeoutException("Request timeout", request=MagicMock())
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        # handle_httpx_exception raises PVRProviderTimeoutError
        # The raise statement re-raises the original TimeoutException
        with pytest.raises((httpx.TimeoutException, PVRProviderTimeoutError)):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_generic_exception(self) -> None:
        """Test _request with generic exception."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        error = ValueError("Unexpected error")
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(PVRProviderError, match="Aria2 request failed"):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_request_pvr_provider_error_passthrough(self) -> None:
        """Test _request passes through PVRProviderError."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        error = PVRProviderError("Custom error")
        mock_client.post.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)

        with pytest.raises(PVRProviderError, match="Custom error"):
            proxy._request("aria2.addUri", ["http://test.com"])

    def test_get_version_with_dict(self) -> None:
        """Test get_version with dict result."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><struct><member><name>version</name><value><string>1.36.0</string></value></member></struct></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy.get_version()

        assert result == "1.36.0"

    def test_get_version_with_string(self) -> None:
        """Test get_version with string result."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><string>1.36.0</string></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy.get_version()

        assert result == "1.36.0"

    def test_get_version_with_none(self) -> None:
        """Test get_version with None result."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<?xml version="1.0"?><methodResponse><params><param><value><nil/></value></param></params></methodResponse>'
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)

        proxy = Aria2Proxy(settings, lambda: mock_client)
        result = proxy.get_version()

        assert result == "unknown"

    @patch.object(Aria2Proxy, "_request")
    def test_add_torrent(self, mock_request: MagicMock) -> None:
        """Test add_torrent."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.add_torrent(b"torrent content", {"dir": "/downloads"})
        assert result == "gid123"
        mock_request.assert_called_once()

    @patch.object(Aria2Proxy, "_request")
    def test_add_torrent_without_options(self, mock_request: MagicMock) -> None:
        """Test add_torrent without options."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.add_torrent(b"torrent content")
        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_add_magnet_with_options(self, mock_request: MagicMock) -> None:
        """Test add_magnet with options."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.add_magnet("magnet:?xt=urn:btih:test", {"dir": "/downloads"})
        assert result == "gid123"

    @patch.object(Aria2Proxy, "_request")
    def test_remove_torrent_with_force(self, mock_request: MagicMock) -> None:
        """Test remove_torrent with force=True."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.remove_torrent("gid123", force=True)
        assert result is True
        mock_request.assert_called_once_with("aria2.forceRemove", "gid123")

    @patch.object(Aria2Proxy, "_request")
    def test_remove_torrent_without_force(self, mock_request: MagicMock) -> None:
        """Test remove_torrent with force=False."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "gid123"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.remove_torrent("gid123", force=False)
        assert result is True
        mock_request.assert_called_once_with("aria2.remove", "gid123")

    @patch.object(Aria2Proxy, "_request")
    def test_remove_completed(self, mock_request: MagicMock) -> None:
        """Test remove_completed."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "OK"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.remove_completed("gid123")
        assert result is True
        mock_request.assert_called_once_with("aria2.removeDownloadResult", "gid123")

    @patch.object(Aria2Proxy, "_request")
    def test_remove_completed_not_ok(self, mock_request: MagicMock) -> None:
        """Test remove_completed with non-OK result."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_request.return_value = "ERROR"
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.remove_completed("gid123")
        assert result is False

    @patch.object(Aria2Proxy, "_request")
    def test_get_torrents_with_non_list_results(self, mock_request: MagicMock) -> None:
        """Test get_torrents with non-list results."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        # Return non-list values
        mock_request.side_effect = [None, "not a list", []]
        proxy = Aria2Proxy(settings, Mock())
        result = proxy.get_torrents()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_client_name(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test client_name property."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert client.client_name == "Aria2"

    @pytest.mark.parametrize(
        ("total_length", "completed_length", "expected"),
        [
            ("1000", "500", 0.5),
            (1000, 500, 0.5),
            ("1000", None, 0.0),
            (None, "500", 0.0),
            (None, None, 0.0),
            ("invalid", "500", 0.0),
            ("1000", "invalid", 0.0),
            ("0", "0", 0.0),
            ("2000", "3000", 1.0),  # Progress capped at 1.0
        ],
    )
    def test_calculate_progress(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        total_length: str | int | None,
        completed_length: str | int | None,
        expected: float,
    ) -> None:
        """Test _calculate_progress with various inputs."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client._calculate_progress(total_length, completed_length)
        assert result == expected

    @pytest.mark.parametrize(
        ("download", "expected"),
        [
            ({"downloadSpeed": "1000"}, 1000),
            ({"downloadSpeed": 1000}, 1000),
            ({"downloadSpeed": "0"}, 0),
            ({"downloadSpeed": None}, None),
            ({}, 0),  # Empty dict defaults to "0" which becomes 0
            ({"downloadSpeed": ""}, None),  # Empty string is falsy, so returns None
            ({"downloadSpeed": "invalid"}, None),
        ],
    )
    def test_get_download_speed(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        download: dict[str, str | int | None],
        expected: int | None,
    ) -> None:
        """Test _get_download_speed with various inputs."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client._get_download_speed(download)
        assert result == expected

    @pytest.mark.parametrize(
        ("download", "expected"),
        [
            ({"eta": "3600"}, 3600),
            ({"eta": 3600}, 3600),
            ({"eta": "0"}, 0),
            ({"eta": ""}, None),
            ({"eta": None}, None),
            ({}, None),
            ({"eta": "invalid"}, None),
        ],
    )
    def test_get_eta(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        download: dict[str, str | int | None],
        expected: int | None,
    ) -> None:
        """Test _get_eta with various inputs."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client._get_eta(download)
        assert result == expected

    def test_get_download_title_from_bittorrent(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _get_download_title from bittorrent info."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        download = cast(
            "dict[str, str | int | None]",
            {
                "bittorrent": {
                    "info": {
                        "name": "Test Book Title",
                    },
                },
            },
        )
        result = client._get_download_title(download)
        assert result == "Test Book Title"

    def test_get_download_title_from_bittorrent_empty_name(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _get_download_title from bittorrent with empty name."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        download = cast(
            "dict[str, str | int | None]",
            {
                "bittorrent": {
                    "info": {
                        "name": "",
                    },
                },
            },
        )
        result = client._get_download_title(download)
        assert result == ""

    def test_get_download_title_from_files(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _get_download_title from files path."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        download = cast(
            "dict[str, str | int | None]",
            {
                "files": [
                    {
                        "path": "/downloads/Test Book Title.epub",
                    },
                ],
            },
        )
        result = client._get_download_title(download)
        assert result == "Test Book Title.epub"

    def test_get_download_title_from_files_empty_path(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _get_download_title from files with empty path."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        download = cast(
            "dict[str, str | int | None]",
            {
                "files": [
                    {
                        "path": "",
                    },
                ],
            },
        )
        result = client._get_download_title(download)
        assert result == ""

    def test_get_download_title_no_bittorrent_no_files(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _get_download_title with no bittorrent or files."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        download = {}
        result = client._get_download_title(download)
        assert result == ""

    def test_build_download_item_with_exception(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _build_download_item with exception in size calculation."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        # Use invalid values that will cause exception
        download = {
            "gid": "gid123",
            "status": "active",
            "totalLength": "invalid",
            "completedLength": "invalid",
            "dir": "/downloads",
        }
        # Should handle exception and set to 0
        item = client._build_download_item(download)
        assert item["size_bytes"] is None or item["size_bytes"] == 0
        assert item["downloaded_bytes"] is None or item["downloaded_bytes"] == 0

    def test_build_options_with_path(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _build_options with download_path."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            download_path="/custom/downloads",
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        options = client._build_options("/test/path")
        assert options["dir"] == "/test/path"

    def test_build_options_with_settings_path(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _build_options with settings download_path."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            download_path="/settings/downloads",
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        options = client._build_options(None)
        assert options["dir"] == "/settings/downloads"

    def test_build_options_without_path(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test _build_options without download_path."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        options = client._build_options(None)
        assert "dir" not in options or options["dir"] is None

    @patch.object(Aria2Proxy, "add_magnet")
    def test_add_url(
        self,
        mock_add_magnet: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url method."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_add_magnet.return_value = "gid123"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_url(
            "https://example.com/file.torrent", None, None, "/downloads"
        )
        assert result == "gid123"
        mock_add_magnet.assert_called_once()

    @patch.object(Aria2Proxy, "add_torrent")
    def test_add_file(
        self,
        mock_add_torrent: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        temp_dir: Path,
    ) -> None:
        """Test add_file method."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_add_torrent.return_value = "gid123"
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        # Create a test file
        test_file = temp_dir / "test.torrent"
        test_file.write_bytes(b"torrent content")

        result = client.add_file(str(test_file), None, None, "/downloads")
        assert result == "gid123"
        mock_add_torrent.assert_called_once()

    @patch.object(Aria2Proxy, "get_torrents")
    def test_get_items_when_disabled(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when client is disabled."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        items = client.get_items()
        assert items == []
        mock_get_torrents.assert_not_called()

    @patch.object(Aria2Proxy, "get_torrents")
    def test_get_items_with_missing_gid(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with downloads missing gid."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_torrents.return_value = [
            {"status": "active"},  # Missing gid
            {"gid": "gid2", "status": "waiting"},
        ]
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        # Should skip the one without gid
        assert len(items) == 1
        assert items[0]["client_item_id"] == "gid2"

    @patch.object(Aria2Proxy, "get_torrents")
    def test_get_items_with_exception(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with exception."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_torrents.side_effect = httpx.RequestError(
            "Connection failed", request=MagicMock()
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )

        with pytest.raises(
            PVRProviderError, match="Failed to get downloads from Aria2"
        ):
            _ = client.get_items()

    @patch.object(Aria2Proxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item method."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_remove.return_value = True
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("gid123", delete_files=False)
        assert result is True
        mock_remove.assert_called_once_with("gid123", force=False)

    @patch.object(Aria2Proxy, "remove_torrent")
    def test_remove_item_when_disabled(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when client is disabled."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        client = Aria2Client(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )

        with pytest.raises(PVRProviderError, match="Aria2 client is disabled"):
            _ = client.remove_item("gid123")

    @patch.object(Aria2Proxy, "remove_torrent")
    def test_remove_item_with_exception(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with exception."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_remove.side_effect = httpx.RequestError(
            "Connection failed", request=MagicMock()
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )

        with pytest.raises(
            PVRProviderError, match="Failed to remove download from Aria2"
        ):
            _ = client.remove_item("gid123")

    @patch.object(Aria2Proxy, "get_version")
    def test_test_connection_with_exception(
        self,
        mock_get_version: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with exception."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_version.side_effect = httpx.RequestError(
            "Connection failed", request=MagicMock()
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )

        with pytest.raises(PVRProviderError, match="Failed to connect to Aria2"):
            _ = client.test_connection()

    @patch.object(Aria2Proxy, "get_version")
    def test_test_connection_with_timeout(
        self,
        mock_get_version: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with timeout exception."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_get_version.side_effect = httpx.TimeoutException(
            "Request timeout", request=MagicMock()
        )
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )

        with pytest.raises(PVRProviderError, match="Failed to connect to Aria2"):
            _ = client.test_connection()

    @patch.object(Aria2Proxy, "get_version")
    def test_test_connection_with_http_status_error(
        self,
        mock_get_version: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with HTTPStatusError."""
        settings = Aria2Settings(
            host="localhost",
            port=6800,
            timeout_seconds=30,
        )
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_get_version.side_effect = error
        client = Aria2Client(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )

        with pytest.raises(PVRProviderError, match="Failed to connect to Aria2"):
            _ = client.test_connection()

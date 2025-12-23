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

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.flood import (
    FloodClient,
    FloodProxy,
    FloodSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.utils.status import DownloadStatus


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

    def test_authenticate_already_authenticated(self) -> None:
        """Test authenticate when already authenticated."""
        settings = FloodSettings(host="localhost", port=3000)
        proxy = FloodProxy(settings)
        proxy._auth_cookies = {"session": "existing"}
        with patch(
            "bookcard.pvr.download_clients.flood.create_httpx_client"
        ) as mock_create:
            proxy._authenticate()
            mock_create.assert_not_called()

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

    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_authenticate_failure_status(self, mock_create_client: MagicMock) -> None:
        """Test authentication with failure status code."""
        settings = FloodSettings(
            host="localhost", port=3000, username="user", password="pw"
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        with pytest.raises(PVRProviderAuthenticationError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_authenticate_network_error(self, mock_create_client: MagicMock) -> None:
        """Test authentication network error."""
        settings = FloodSettings(
            host="localhost", port=3000, username="user", password="pw"
        )
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = FloodProxy(settings)

        # Timeout
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._authenticate()

        # HTTP Status Error (401) - Caught by exception handler
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderAuthenticationError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_execute_request_methods(self, mock_create_client: MagicMock) -> None:
        """Test _execute_request methods."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_client = MagicMock()
        proxy = FloodProxy(settings)

        # GET
        proxy._execute_request(mock_client, "GET", "url", {})
        mock_client.get.assert_called_once()

        # POST
        proxy._execute_request(mock_client, "POST", "url", {})
        mock_client.post.assert_called_once()

        # DELETE
        proxy._execute_request(mock_client, "DELETE", "url", {})
        mock_client.delete.assert_called_once()

        # Unsupported
        with pytest.raises(PVRProviderError, match="Unsupported HTTP method"):
            proxy._execute_request(mock_client, "PUT", "url", {})

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
        mock_response.content = b'{"result": "success"}'
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        proxy._auth_cookies = {"session": "test"}
        result = proxy._request("GET", "/torrents")

        assert result == {"result": "success"}

    @patch.object(FloodProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request session expired retry."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_client = MagicMock()
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {}
        mock_response_200.content = b"{}"

        mock_client.get.side_effect = [mock_response_401, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        proxy._request("GET", "endpoint")

        assert mock_authenticate.call_count == 2  # Initial + Retry

    @patch.object(FloodProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_request_network_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request network error."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = FloodProxy(settings)

        # Timeout
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._request("GET", "endpoint")

    @patch.object(FloodProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_request_auth_failure_persistent(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request auth failure persists after retry."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401

        # raise_for_status should raise error for 401
        def raise_for_status() -> None:
            if mock_response.status_code >= 400:
                raise httpx.HTTPStatusError(
                    "Error", request=Mock(), response=mock_response
                )

        mock_response.raise_for_status.side_effect = raise_for_status

        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        with pytest.raises(PVRProviderAuthenticationError):
            proxy._request("GET", "endpoint")

    @patch.object(FloodProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.flood.create_httpx_client")
    def test_request_http_error_generic(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request generic HTTP error."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=mock_response
        )
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FloodProxy(settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy._request("GET", "endpoint")

    @patch.object(FloodProxy, "_request")
    def test_add_torrent_url_destination(self, mock_request: MagicMock) -> None:
        """Test add_torrent_url with destination."""
        settings = FloodSettings(host="localhost", port=3000)
        proxy = FloodProxy(settings)
        proxy.add_torrent_url("url", destination="/path")
        assert mock_request.call_args[0][2]["destination"] == "/path"

    @patch.object(FloodProxy, "_request")
    def test_add_torrent_file(self, mock_request: MagicMock) -> None:
        """Test add_torrent_file."""
        settings = FloodSettings(host="localhost", port=3000)
        proxy = FloodProxy(settings)
        proxy.add_torrent_file("test.torrent", b"content", destination="/path")

        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1].endswith("add-files")
        assert "files" in call_args[0][2]  # Base64
        assert call_args[0][2]["destination"] == "/path"

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

    @patch.object(FloodProxy, "_request")
    def test_remove_torrent(self, mock_request: MagicMock) -> None:
        """Test remove_torrent."""
        settings = FloodSettings(host="localhost", port=3000)
        proxy = FloodProxy(settings)

        # Without data
        proxy.remove_torrent("hash")
        mock_request.assert_called_with("DELETE", "torrents/hash")

        # With data
        proxy.remove_torrent("hash", delete_data=True)
        mock_request.assert_called_with("DELETE", "torrents/hash?deleteData=true")


class TestFloodClient:
    """Test FloodClient."""

    def test_init_with_flood_settings(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test initialization with FloodSettings."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        assert isinstance(client.settings, FloodSettings)
        assert client.enabled is True
        assert client.client_name == "Flood"

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = FloodClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, FloodSettings)

    @patch.object(FloodProxy, "add_torrent_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        # Flood extracts hash from magnet link - use lowercase hash
        result = client.add_download("magnet:?xt=urn:btih:abcdef1234567890&dn=test")
        assert result == "ABCDEF1234567890"
        mock_add.assert_called_once()

    @patch.object(FloodProxy, "add_torrent_url")
    def test_add_download_magnet_invalid(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with invalid magnet link."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_download("magnet:?dn=test")  # No xt
        assert result == "pending"

    @patch.object(FloodProxy, "add_torrent_url")
    def test_add_url(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_url(
            "http://example.com/test.torrent", None, "category", None
        )
        assert result == "pending"
        mock_add.assert_called_once()
        assert mock_add.call_args[1]["tags"] == ["category"]

    @patch.object(FloodProxy, "add_torrent_file")
    def test_add_file(
        self,
        mock_add: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        sample_torrent_file: Path,
    ) -> None:
        """Test add_file."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.add_file(str(sample_torrent_file), None, None, None)
        assert result == "pending"
        mock_add.assert_called_once()

    @patch.object(FloodProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        settings = FloodSettings(host="localhost", port=3000)
        settings.category = "cat"
        mock_get_torrents.return_value = {
            "ABC123": {
                "hash": "ABC123",
                "name": "Test Torrent",
                "status": ["downloading"],
                "percentComplete": 50.0,
                "sizeBytes": 1000000,
                "bytesDone": 500000,
                "tags": ["cat"],
            },
            "DEF456": {
                "hash": "DEF456",
                "tags": ["other"],  # Should be filtered
            },
            "": {},  # Should be skipped
        }
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"

    @patch.object(FloodProxy, "get_torrents")
    def test_get_items_status_mapping(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items status mapping."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_get_torrents.return_value = {
            "1": {"hash": "1", "status": ["seeding"]},
            "2": {"hash": "2", "status": ["error"]},
            "3": {"hash": "3", "status": ["paused"]},
            "4": {"hash": "4", "status": []},
            "5": {"hash": "5", "status": ["downloading"]},
        }
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = {item["client_item_id"]: item["status"] for item in client.get_items()}
        assert items["1"] == DownloadStatus.COMPLETED
        assert items["2"] == DownloadStatus.FAILED
        assert items["3"] == DownloadStatus.PAUSED
        assert items["4"] == DownloadStatus.QUEUED
        assert items["5"] == DownloadStatus.DOWNLOADING

    @patch.object(FloodProxy, "get_torrents")
    def test_get_items_progress_cap(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items progress cap."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_get_torrents.return_value = {
            "1": {"hash": "1", "sizeBytes": 100, "bytesDone": 200},
        }
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        items = client.get_items()
        assert items[0]["progress"] == 1.0

    @patch.object(FloodProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items error."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_get_torrents.side_effect = Exception("API Error")
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_get_items_disabled(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test get_items disabled."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(FloodProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.remove_item("abc123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self, file_fetcher: FileFetcherProtocol, url_router: UrlRouterProtocol
    ) -> None:
        """Test remove_item disabled."""
        settings = FloodSettings(host="localhost", port=3000)
        client = FloodClient(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("abc")

    @patch.object(FloodProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item error."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_remove.side_effect = Exception("API Error")
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("abc")

    @patch.object(FloodProxy, "verify_auth")
    def test_test_connection(
        self,
        mock_verify_auth: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        settings = FloodSettings(
            host="localhost",
            port=3000,
            username="admin",
            password="password",
            timeout_seconds=30,
        )
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        result = client.test_connection()
        assert result is True
        mock_verify_auth.assert_called_once()

    @patch.object(FloodProxy, "verify_auth")
    def test_test_connection_error(
        self,
        mock_verify_auth: MagicMock,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection error."""
        settings = FloodSettings(host="localhost", port=3000)
        mock_verify_auth.side_effect = Exception("Connect Error")
        client = FloodClient(
            settings=settings, file_fetcher=file_fetcher, url_router=url_router
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

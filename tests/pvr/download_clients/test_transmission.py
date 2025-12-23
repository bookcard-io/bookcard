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

"""Tests for Transmission download client."""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.transmission import (
    TransmissionClient,
    TransmissionProxy,
    TransmissionSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)


class TestTransmissionProxy:
    """Test TransmissionProxy."""

    def test_init(self, transmission_settings: TransmissionSettings) -> None:
        """Test proxy initialization."""
        proxy = TransmissionProxy(transmission_settings)
        assert proxy.settings == transmission_settings
        assert proxy.rpc_url == "http://localhost:8080/transmission/rpc"
        assert proxy._session_id is None

    def test_handle_409_response(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _handle_409_response with session ID."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.headers = {"X-Transmission-Session-Id": "test-session-id"}
        proxy._handle_409_response(response)
        assert proxy._session_id == "test-session-id"

    def test_handle_409_response_no_session_id(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _handle_409_response without session ID."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.headers = {}
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return session ID"
        ):
            proxy._handle_409_response(response)

    def test_handle_200_response_success(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _handle_200_response with success."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.json.return_value = {"result": "success"}
        proxy._handle_200_response(response)
        assert proxy._session_id == ""

    def test_handle_200_response_no_success(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _handle_200_response without success."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.json.return_value = {"result": "error"}
        proxy._handle_200_response(response)
        # Session ID should remain None

    def test_build_auth_header_with_credentials(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _build_auth_header with credentials."""
        proxy = TransmissionProxy(transmission_settings)
        header = proxy._build_auth_header()
        assert header is not None
        assert header.startswith("Basic ")
        decoded = base64.b64decode(header.split(" ")[1]).decode("utf-8")
        assert (
            decoded
            == f"{transmission_settings.username}:{transmission_settings.password}"
        )

    def test_build_auth_header_no_credentials(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _build_auth_header without credentials."""
        transmission_settings.username = None
        transmission_settings.password = None
        proxy = TransmissionProxy(transmission_settings)
        header = proxy._build_auth_header()
        assert header is None

    @pytest.mark.parametrize(
        ("status_code", "should_raise"),
        [
            (409, False),  # Handled by _handle_409_response
            (401, True),  # Raises auth error
            (403, True),  # Raises auth error
            (200, False),  # Handled by _handle_200_response
            (500, True),  # Raises unexpected error
        ],
    )
    def test_handle_auth_response(
        self,
        status_code: int,
        should_raise: bool,
        transmission_settings: TransmissionSettings,
    ) -> None:
        """Test _handle_auth_response with various status codes."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.status_code = status_code
        response.headers = (
            {"X-Transmission-Session-Id": "test-id"} if status_code == 409 else {}
        )
        response.json.return_value = {"result": "success"} if status_code == 200 else {}

        if should_raise:
            with pytest.raises(PVRProviderAuthenticationError):
                proxy._handle_auth_response(response)
        else:
            proxy._handle_auth_response(response)

    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_authenticate_success_409(
        self, mock_create_client: MagicMock, transmission_settings: TransmissionSettings
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

        proxy = TransmissionProxy(transmission_settings)
        proxy._authenticate()

        assert proxy._session_id == "test-session-id"

    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_authenticate_no_force_when_authenticated(
        self, mock_create_client: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test that authentication is skipped when already authenticated."""
        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "existing-session"
        proxy._authenticate(force=False)

        mock_create_client.assert_not_called()

    def test_build_auth_headers(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _build_auth_headers."""
        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "test-session-id"
        headers = proxy._build_auth_headers()
        assert "Authorization" in headers
        assert headers["X-Transmission-Session-Id"] == "test-session-id"

    def test_parse_rpc_response_success(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _parse_rpc_response with success."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.json.return_value = {"result": "success", "arguments": {}}
        result = proxy._parse_rpc_response(response)
        assert result == {"result": "success", "arguments": {}}

    def test_parse_rpc_response_error(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _parse_rpc_response with error."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.json.return_value = {"result": "error message"}
        with pytest.raises(PVRProviderError, match="RPC error"):
            proxy._parse_rpc_response(response)

    def test_parse_rpc_response_json_error(
        self, transmission_settings: TransmissionSettings
    ) -> None:
        """Test _parse_rpc_response with JSON decode error."""
        proxy = TransmissionProxy(transmission_settings)
        response = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        with pytest.raises(PVRProviderError, match="Failed to parse"):
            proxy._parse_rpc_response(response)

    @patch.object(TransmissionProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        transmission_settings: TransmissionSettings,
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

        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "test-session"
        result = proxy._request("session-get")

        assert result == {"result": "success", "arguments": {}}

    @patch.object(TransmissionProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        transmission_settings: TransmissionSettings,
    ) -> None:
        """Test _request with session expiration (409)."""
        mock_client = MagicMock()
        mock_response_409 = MagicMock()
        mock_response_409.status_code = 409
        mock_response_409.headers = {"X-Transmission-Session-Id": "new-session"}
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"result": "success", "arguments": {}}
        mock_response_200.raise_for_status = Mock()
        mock_client.post.side_effect = [mock_response_409, mock_response_200]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "old-session"
        result = proxy._request("session-get")

        assert result == {"result": "success", "arguments": {}}
        assert mock_authenticate.call_count == 2

    @patch.object(TransmissionProxy, "_request")
    def test_get_version(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test get_version."""
        mock_request.return_value = {"arguments": {"version": "3.0.0"}}
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.get_version()
        assert result == "3.0.0"

    @patch.object(TransmissionProxy, "_request")
    def test_get_version_unknown(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test get_version with unknown version."""
        mock_request.return_value = {"arguments": {}}
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.get_version()
        assert result == "unknown"

    @patch.object(TransmissionProxy, "_request")
    def test_add_torrent_from_url(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test add_torrent_from_url."""
        mock_request.return_value = {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "test"}},
        }
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.add_torrent_from_url(
            "magnet:?xt=urn:btih:test", download_dir="/path"
        )
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "torrent-add"
        assert call_args[0][1]["filename"] == "magnet:?xt=urn:btih:test"
        assert "arguments" in result

    @patch.object(TransmissionProxy, "_request")
    def test_add_torrent_from_file(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test add_torrent_from_file."""
        mock_request.return_value = {
            "result": "success",
            "arguments": {"torrent-added": {"hashString": "test"}},
        }
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.add_torrent_from_file(b"torrent content", download_dir="/path")
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "metainfo" in call_args[0][1]
        assert "arguments" in result

    @patch.object(TransmissionProxy, "_request")
    def test_get_torrents(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test get_torrents."""
        mock_request.return_value = {
            "arguments": {"torrents": [{"id": 1, "name": "test"}]}
        }
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.get_torrents()
        assert result == [{"id": 1, "name": "test"}]

    @patch.object(TransmissionProxy, "_request")
    def test_remove_torrent(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test remove_torrent."""
        proxy = TransmissionProxy(transmission_settings)
        proxy.remove_torrent("abc123", delete_files=True)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["ids"] == ["abc123"]
        assert call_args[0][1]["delete-local-data"] is True


class TestTransmissionClient:
    """Test TransmissionClient."""

    def test_init_with_transmission_settings(
        self,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with TransmissionSettings."""
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, TransmissionSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = TransmissionClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, TransmissionSettings)

    @patch.object(TransmissionProxy, "add_torrent_from_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}}
        }
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"

    @patch.object(TransmissionProxy, "add_torrent_from_url")
    def test_add_download_duplicate(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with duplicate torrent."""
        mock_add.return_value = {
            "arguments": {"torrent-duplicate": {"hashString": "ABCDEF1234567890"}}
        }
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890")
        assert result == "ABCDEF1234567890"

    @patch.object(TransmissionProxy, "add_torrent_from_file")
    def test_add_download_file_path(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}}
        }
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download(str(sample_torrent_file))
        assert result == "ABCDEF1234567890"

    @patch.object(TransmissionProxy, "add_torrent_from_url")
    def test_add_download_no_hash_extract_from_magnet(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download extracting hash from magnet when not in response."""
        mock_add.return_value = {"arguments": {}}
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("magnet:?xt=urn:btih:ABCDEF1234567890&dn=test")
        assert result == "ABCDEF1234567890"

    @patch.object(TransmissionProxy, "add_torrent_from_url")
    def test_add_download_no_hash_error(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with no hash in response."""
        mock_add.return_value = {"arguments": {}}
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get torrent hash"):
            client.add_download("http://example.com/torrent.torrent")

    @patch.object(TransmissionProxy, "get_torrents")
    def test_get_items(
        self,
        mock_get_torrents: MagicMock,
        transmission_settings: TransmissionSettings,
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
                "eta": 5,
                "downloadDir": "/downloads",
            }
        ]
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "ABC123"
        assert items[0]["status"] == "downloading"
        assert items[0]["progress"] == 0.5

    @patch.object(TransmissionProxy, "remove_torrent")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.remove_item("ABC123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with("abc123", delete_files=True)

    @patch.object(TransmissionProxy, "get_version")
    def test_test_connection(
        self,
        mock_get_version: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "3.0.0"
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.test_connection()
        assert result is True

    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_authenticate_http_error(
        self, mock_create_client: MagicMock, transmission_settings: TransmissionSettings
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

        proxy = TransmissionProxy(transmission_settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_authenticate_timeout(
        self, mock_create_client: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test authentication with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = TransmissionProxy(transmission_settings)
        with pytest.raises(PVRProviderTimeoutError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_authenticate_request_error(
        self, mock_create_client: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test authentication with request error."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Request error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = TransmissionProxy(transmission_settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy._authenticate()

    @patch.object(TransmissionProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_request_http_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        transmission_settings: TransmissionSettings,
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

        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "test-session"
        with pytest.raises(PVRProviderNetworkError):
            proxy._request("session-get")

    @patch.object(TransmissionProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.transmission.create_httpx_client")
    def test_request_timeout(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        transmission_settings: TransmissionSettings,
    ) -> None:
        """Test _request with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = TransmissionProxy(transmission_settings)
        proxy._session_id = "test-session"
        with pytest.raises(PVRProviderTimeoutError):
            proxy._request("session-get")

    @patch.object(TransmissionProxy, "_request")
    def test_get_torrents_with_ids(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test get_torrents with specific IDs."""
        mock_request.return_value = {
            "arguments": {"torrents": [{"id": 1, "name": "test"}]}
        }
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.get_torrents(ids=["abc123"])
        assert result == [{"id": 1, "name": "test"}]
        call_args = mock_request.call_args
        assert call_args[0][1]["ids"] == ["abc123"]

    @patch.object(TransmissionProxy, "_request")
    def test_get_torrents_with_fields(
        self, mock_request: MagicMock, transmission_settings: TransmissionSettings
    ) -> None:
        """Test get_torrents with specific fields."""
        mock_request.return_value = {
            "arguments": {"torrents": [{"id": 1, "name": "test"}]}
        }
        proxy = TransmissionProxy(transmission_settings)
        result = proxy.get_torrents(fields=["id", "name"])
        assert result == [{"id": 1, "name": "test"}]
        call_args = mock_request.call_args
        assert call_args[0][1]["fields"] == ["id", "name"]

    @patch.object(TransmissionProxy, "add_torrent_from_url")
    def test_add_download_http_url(
        self,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with HTTP URL."""
        mock_add.return_value = {
            "arguments": {"torrent-added": {"hashString": "ABCDEF1234567890"}}
        }
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("http://example.com/torrent.torrent")
        assert result == "ABCDEF1234567890"

    @patch.object(TransmissionProxy, "add_torrent_from_file")
    @patch("pathlib.Path.open")
    @patch("pathlib.Path.is_file")
    def test_add_download_file_path_error(
        self,
        mock_is_file: MagicMock,
        mock_open: MagicMock,
        mock_add: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with file path error."""
        mock_is_file.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"content"
        mock_add.return_value = {"arguments": {}}
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get torrent hash"):
            client.add_download("/path/to/torrent.torrent")

    @patch.object(TransmissionProxy, "get_torrents")
    def test_get_items_empty(
        self,
        mock_get_torrents: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with empty result."""
        mock_get_torrents.return_value = []
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert items == []

    @patch.object(TransmissionProxy, "get_torrents")
    def test_get_items_with_eta(
        self,
        mock_get_torrents: MagicMock,
        transmission_settings: TransmissionSettings,
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
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["eta_seconds"] == 10
        assert items[0]["download_speed_bytes_per_sec"] == 50000  # 500000 / 10

    @patch.object(TransmissionProxy, "get_torrents")
    def test_get_items_error(
        self,
        mock_get_torrents: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with error."""
        mock_get_torrents.side_effect = Exception("Connection error")
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_remove_item_disabled(
        self,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("ABC123")

    @patch.object(TransmissionProxy, "remove_torrent")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with error."""
        mock_remove.side_effect = Exception("Remove error")
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("ABC123")

    @patch.object(TransmissionProxy, "get_version")
    def test_test_connection_error(
        self,
        mock_get_version: MagicMock,
        transmission_settings: TransmissionSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with error."""
        mock_get_version.side_effect = Exception("Connection error")
        client = TransmissionClient(
            settings=transmission_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

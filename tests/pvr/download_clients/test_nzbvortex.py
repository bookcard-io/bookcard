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

"""Tests for NZBVortex download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
)
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.nzbvortex import (
    NzbvortexClient,
    NzbvortexProxy,
    NzbvortexSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.utils.status import DownloadStatus


@pytest.fixture
def nzbvortex_settings() -> NzbvortexSettings:
    """Return NZBVortex settings."""
    return NzbvortexSettings(
        host="localhost",
        port=4321,
        api_key="test-api-key",
        timeout_seconds=30,
        category="movies",
    )


class TestNzbvortexProxy:
    """Test NzbvortexProxy."""

    def test_init(self, nzbvortex_settings: NzbvortexSettings) -> None:
        """Test proxy initialization."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        assert proxy.settings == nzbvortex_settings
        assert proxy.api_url.endswith("/api")
        assert proxy._session_id is None

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_get_nonce(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test _get_nonce."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"authNonce": "test-nonce"}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        proxy = NzbvortexProxy(nzbvortex_settings)
        nonce = proxy._get_nonce(mock_client)
        assert nonce == "test-nonce"

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_get_nonce_missing(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test _get_nonce when nonce is missing."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.get.return_value = mock_response

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return nonce"
        ):
            proxy._get_nonce(mock_client)

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_success(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test successful authentication."""
        mock_client = MagicMock()
        mock_response_nonce = MagicMock()
        mock_response_nonce.json.return_value = {"authNonce": "test-nonce"}
        mock_response_nonce.raise_for_status = Mock()

        mock_response_auth = MagicMock()
        mock_response_auth.json.return_value = {"result": "success"}
        mock_response_auth.raise_for_status = Mock()

        # Mock cookies
        mock_cookie = MagicMock()
        type(mock_cookie).name = "sessionid"
        type(mock_cookie).value = "test-session"
        mock_response_auth.cookies = [mock_cookie]

        mock_client.get.side_effect = [mock_response_nonce, mock_response_auth]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        proxy._authenticate()

        assert proxy._session_id == "test-session"

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_already_authenticated(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authenticate when already authenticated."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        proxy._session_id = "existing-session"
        proxy._authenticate()
        mock_create_client.assert_not_called()

    def test_authenticate_no_api_key(
        self, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authenticate without API key."""
        nzbvortex_settings.api_key = None
        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(PVRProviderAuthenticationError, match="requires API key"):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_failure_result(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication when result is not success."""
        mock_client = MagicMock()
        mock_response_nonce = MagicMock()
        mock_response_nonce.json.return_value = {"authNonce": "test-nonce"}

        mock_response_auth = MagicMock()
        mock_response_auth.json.return_value = {"result": "error"}

        mock_client.get.side_effect = [mock_response_nonce, mock_response_auth]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_no_session_id(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication when session ID is missing."""
        mock_client = MagicMock()
        mock_response_nonce = MagicMock()
        mock_response_nonce.json.return_value = {"authNonce": "test-nonce"}

        mock_response_auth = MagicMock()
        mock_response_auth.json.return_value = {"result": "success"}
        mock_response_auth.cookies = []

        mock_client.get.side_effect = [mock_response_nonce, mock_response_auth]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return session ID"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_http_error(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication with HTTP error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "Auth failed", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_network_error(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication with network error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(PVRProviderNetworkError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_server_error(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication with 500 server error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        # handle_httpx_exception raises PVRProviderNetworkError for generic errors
        with pytest.raises(PVRProviderNetworkError):
            proxy._authenticate()

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_timeout(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test authentication timeout."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(nzbvortex_settings)
        with pytest.raises(PVRProviderTimeoutError):
            proxy._authenticate()

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_methods(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request with different HTTP methods."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        proxy._session_id = "sid"

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}

        # Test POST
        mock_client.post.return_value = mock_response
        proxy._request("POST", "test")
        mock_client.post.assert_called()

        # Test DELETE
        mock_client.delete.return_value = mock_response
        proxy._request("DELETE", "test")
        mock_client.delete.assert_called()

        # Test unsupported
        with pytest.raises(PVRProviderError, match="Unsupported HTTP method"):
            proxy._execute_request(mock_client, "PUT", "url", {}, {})

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request session expired retry."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        proxy._session_id = "old-sid"

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_response_expired = MagicMock()
        mock_response_expired.status_code = 401

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}

        mock_client.get.side_effect = [mock_response_expired, mock_response_success]

        proxy._request("GET", "test")
        assert mock_authenticate.call_count == 2  # Initial + Retry
        assert mock_authenticate.call_args_list[1][1]["force"] is True

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_session_expired_retry_fails(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request session expired retry fails."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        proxy._session_id = "old-sid"

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_response_expired = MagicMock()
        mock_response_expired.status_code = 401

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 401
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Auth Failed", request=MagicMock(), response=mock_response_fail
        )

        mock_client.get.side_effect = [mock_response_expired, mock_response_fail]

        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy._request("GET", "test")

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_not_logged_in_result(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request when result says notLoggedIn."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "notLoggedIn"}
        mock_client.get.return_value = mock_response

        with pytest.raises(PVRProviderAuthenticationError, match="session expired"):
            proxy._request("GET", "test")

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_http_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request with HTTP error."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = error

        with pytest.raises(PVRProviderNetworkError, match="HTTP 500"):
            proxy._request("GET", "test")

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_network_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
    ) -> None:
        """Test _request with network error."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        mock_client.get.side_effect = httpx.RequestError("Network Error")

        with pytest.raises(PVRProviderNetworkError):
            proxy._request("GET", "test")

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_execute_request_with_files(
        self, mock_create_client: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test _execute_request with files."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        files = {"file": b"data"}
        proxy._execute_request(mock_client, "POST", "url", {}, {}, files=files)

        mock_client.post.assert_called_with(
            "url",
            params={},
            files=files,
            cookies={},
            timeout=nzbvortex_settings.timeout_seconds,
        )

    @patch.object(NzbvortexProxy, "_request")
    def test_add_nzb_with_group(
        self, mock_request: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test add_nzb with group name."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_request.return_value = {"id": 123}
        proxy.add_nzb(b"data", "test.nzb", groupname="movies")

        _args, kwargs = mock_request.call_args
        assert kwargs["params"]["groupname"] == "movies"

    @patch.object(NzbvortexProxy, "_request")
    def test_get_queue_with_category(
        self, mock_request: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test get_queue with configured category."""
        proxy = NzbvortexProxy(nzbvortex_settings)
        mock_request.return_value = {"items": []}
        proxy.get_queue()

        _args, kwargs = mock_request.call_args
        assert kwargs["params"]["groupName"] == "movies"

    @patch.object(NzbvortexProxy, "_request")
    def test_remove_nzb(
        self, mock_request: MagicMock, nzbvortex_settings: NzbvortexSettings
    ) -> None:
        """Test remove_nzb with and without data."""
        proxy = NzbvortexProxy(nzbvortex_settings)

        proxy.remove_nzb(123, delete_data=False)
        mock_request.assert_called_with("GET", "nzb/123/cancel")

        proxy.remove_nzb(123, delete_data=True)
        mock_request.assert_called_with("GET", "nzb/123/cancelDelete")


class TestNzbvortexClient:
    """Test NzbvortexClient."""

    def test_client_name(
        self,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test client_name property."""
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert client.client_name == "NZBVortex"

    def test_init_with_download_client_settings(
        self,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        base_settings = DownloadClientSettings(
            host="localhost",
            port=4321,
            username="user",
            password="password",
        )
        client = NzbvortexClient(
            settings=base_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, NzbvortexSettings)
        # Check defaults
        assert client.settings.api_key is None

    def test_add_magnet(
        self,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_magnet raises error."""
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="not support magnet links"):
            client.add_magnet("magnet:?", None, None, None)

    @patch.object(NzbvortexProxy, "add_nzb")
    def test_add_url(
        self,
        mock_add_nzb: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        mock_add_nzb.return_value = "123"

        mock_file_fetcher = MagicMock()
        mock_file_fetcher.fetch_with_filename.return_value = (b"content", "test.nzb")

        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=mock_file_fetcher,
            url_router=url_router,
        )

        result = client.add_url("http://example.com/test.nzb", "Test Title", None, None)
        assert result == "123"

        mock_add_nzb.assert_called_with(
            b"content", "test.nzb", groupname=nzbvortex_settings.category
        )

    @patch.object(NzbvortexProxy, "add_nzb")
    def test_add_file(
        self,
        mock_add_nzb: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        tmp_path: Path,
    ) -> None:
        """Test add_file."""
        mock_add_nzb.return_value = "123"

        test_file = tmp_path / "test.nzb"
        test_file.write_bytes(b"content")

        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        result = client.add_file(str(test_file), None, None, None)
        assert result == "123"

        mock_add_nzb.assert_called_with(
            b"content", "test.nzb", groupname=nzbvortex_settings.category
        )

    def test_get_items_disabled(
        self,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(NzbvortexProxy, "get_queue")
    def test_get_items_error(
        self,
        mock_get_queue: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with error."""
        mock_get_queue.side_effect = Exception("API Error")
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(NzbvortexProxy, "get_queue")
    def test_get_items_parsing(
        self,
        mock_get_queue: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items response parsing."""
        mock_get_queue.return_value = [
            # Valid item
            {
                "id": 1,
                "name": "test1",
                "state": "downloading",
                "progress": 50.0,
                "size": 1000,
            },
            # Item with no ID (should be skipped)
            {
                "id": 0,
                "name": "test2",
            },
            # Item with progress > 100 (should be capped)
            {
                "id": 3,
                "name": "test3",
                "state": "completed",
                "progress": 200.0,
                "size": 2000,
            },
        ]

        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()

        assert len(items) == 2

        # Check first item
        item1 = items[0]
        assert item1["client_item_id"] == "1"
        assert item1["title"] == "test1"
        assert item1["status"] == DownloadStatus.DOWNLOADING
        assert item1["progress"] == 0.5
        assert item1["downloaded_bytes"] == 500

        # Check third item
        item3 = items[1]
        assert item3["client_item_id"] == "3"
        assert item3["status"] == DownloadStatus.COMPLETED
        assert item3["progress"] == 1.0
        assert item3["downloaded_bytes"] == 2000

    def test_remove_item_disabled(
        self,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="client is disabled"):
            client.remove_item("123")

    @patch.object(NzbvortexProxy, "remove_nzb")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item with error."""
        mock_remove.side_effect = Exception("API Error")
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to remove download"):
            client.remove_item("123")

    @patch.object(NzbvortexProxy, "get_queue")
    def test_test_connection_error(
        self,
        mock_get_queue: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with error."""
        mock_get_queue.side_effect = Exception("Connection refused")
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch.object(NzbvortexProxy, "remove_nzb")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        mock_auth: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item success."""
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.remove_item("123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with(123, True)

    @patch.object(NzbvortexProxy, "get_queue")
    def test_test_connection(
        self,
        mock_get_queue: MagicMock,
        nzbvortex_settings: NzbvortexSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection success."""
        mock_get_queue.return_value = []
        client = NzbvortexClient(
            settings=nzbvortex_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.test_connection()
        assert result is True
        mock_get_queue.assert_called_once()

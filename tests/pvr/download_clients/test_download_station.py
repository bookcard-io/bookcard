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

"""Tests for Download Station download client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.download_station import (
    DownloadStationClient,
    DownloadStationProxy,
    DownloadStationSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)


class TestDownloadStationProxy:
    """Test DownloadStationProxy."""

    def test_init(self, download_station_settings: DownloadStationSettings) -> None:
        """Test proxy initialization."""
        proxy = DownloadStationProxy(download_station_settings)
        assert proxy.settings == download_station_settings
        assert proxy.webapi_url.endswith("/webapi")
        assert proxy._session_id is None
        assert proxy._api_info == {}

    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_query_api_info_success(
        self,
        mock_create_client: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _query_api_info successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "SYNO.API.Auth": {"path": "auth.cgi", "maxVersion": 6},
                "SYNO.DownloadStation.Task": {
                    "path": "DownloadStation/task.cgi",
                    "maxVersion": 2,
                },
            },
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        result = proxy._query_api_info()

        assert "SYNO.API.Auth" in result
        assert result["SYNO.API.Auth"]["path"] == "auth.cgi"

    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_query_api_info_failure(
        self,
        mock_create_client: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _query_api_info with failure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(PVRProviderError, match="Failed to query"):
            proxy._query_api_info()

    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_query_api_info_network_error(
        self,
        mock_create_client: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _query_api_info with network error."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)

        # Timeout
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._query_api_info()

        # HTTP Error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderNetworkError):
            proxy._query_api_info()

    @patch("bookcard.pvr.download_clients.download_station.handle_httpx_exception")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_query_api_info_unreachable(
        self,
        mock_create_client: MagicMock,
        mock_handle: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _query_api_info unreachable code path (lines 131-132)."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        # Mock handle_httpx_exception to not raise (for coverage of unreachable code)
        mock_handle.return_value = None

        proxy = DownloadStationProxy(download_station_settings)
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderError, match="Failed to query API info"):
            proxy._query_api_info()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_success(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test successful authentication."""
        mock_query_api.return_value = {
            "SYNO.API.Auth": {"path": "auth.cgi", "maxVersion": 6},
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"sid": "test-session-id"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        # Set api_info before authentication
        proxy._api_info = {"auth": {"path": "auth.cgi", "maxVersion": 6}}
        proxy.authenticate()

        assert proxy._session_id == "test-session-id"

    def test_authenticate_already_authenticated(
        self, download_station_settings: DownloadStationSettings
    ) -> None:
        """Test authenticate when already authenticated."""
        proxy = DownloadStationProxy(download_station_settings)
        proxy._session_id = "existing-sid"
        with patch(
            "bookcard.pvr.download_clients.download_station.create_httpx_client"
        ) as mock_create:
            proxy.authenticate()
            mock_create.assert_not_called()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_no_credentials(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test authentication without credentials."""
        download_station_settings.username = None
        download_station_settings.password = None
        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires username and password"
        ):
            proxy.authenticate()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_failure_codes(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test authentication with failure codes."""
        mock_query_api.return_value = {"SYNO.API.Auth": {}}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": {"code": 400},
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="authentication failed"
        ):
            proxy.authenticate()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_generic_error(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test authentication with generic error."""
        mock_query_api.return_value = {"SYNO.API.Auth": {}}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": {"code": 999, "errors": {"reason": "Unknown"}},
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(
            PVRProviderError, match="Download Station authentication error"
        ):
            proxy.authenticate()

    @patch.object(DownloadStationProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {"tasks": []}}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        proxy._session_id = "test-session"
        result = proxy._request("SYNO.DownloadStation.Task", "list")

        assert result.get("tasks") == []

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch.object(DownloadStationProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_session_expired(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request session expired retry."""
        mock_query_api.return_value = {}
        mock_client = MagicMock()
        mock_response_expired = MagicMock()
        mock_response_expired.status_code = 403

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True, "data": {}}

        mock_client.get.side_effect = [mock_response_expired, mock_response_success]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        proxy._session_id = "old-sid"

        proxy._request("API", "method")

        # Verify re-authentication
        assert mock_authenticate.call_count == 2  # Initial + Retry

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch.object(DownloadStationProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_api_error(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request API error response."""
        mock_query_api.return_value = {}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": {"code": 100, "errors": [{"reason": "Bad request"}]},
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(
            PVRProviderError, match="Download Station API error: Bad request"
        ):
            proxy._request("API", "method")

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_no_sid(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test authentication with no SID in response."""
        mock_query_api.return_value = {"SYNO.API.Auth": {}}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {},  # No sid
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="did not return session ID"
        ):
            proxy.authenticate()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_authenticate_network_errors(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test authentication network errors."""
        mock_query_api.return_value = {"SYNO.API.Auth": {}}
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = DownloadStationProxy(download_station_settings)

        # 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderAuthenticationError):
            proxy.authenticate()

        # Timeout
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy.authenticate()

        # HTTP Status Error (not 401/403) - line 200
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Server Error"
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response_500
        )
        with pytest.raises(PVRProviderNetworkError):
            proxy.authenticate()

    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_execute_request_with_files(
        self,
        mock_create_client: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _execute_request with files."""
        mock_client = MagicMock()
        proxy = DownloadStationProxy(download_station_settings)

        proxy._execute_request(
            mock_client, "http://test", {}, files={"file": b"content"}
        )
        mock_client.post.assert_called_once()

    @patch.object(DownloadStationProxy, "authenticate")
    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_with_params(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        mock_authenticate: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request with params."""
        mock_query_api.return_value = {}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        proxy._session_id = "sid"

        proxy._request("API", "method", params={"key": "value"})

        # Verify params in call
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["key"] == "value"

    @patch.object(DownloadStationProxy, "authenticate")
    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_auth_failure_code(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        mock_authenticate: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request auth failure code in JSON."""
        mock_query_api.return_value = {}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False, "error": {"code": 105}}
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = DownloadStationProxy(download_station_settings)
        with pytest.raises(PVRProviderAuthenticationError):
            proxy._request("API", "method")

    @patch.object(DownloadStationProxy, "authenticate")
    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch("bookcard.pvr.download_clients.download_station.create_httpx_client")
    def test_request_network_errors(
        self,
        mock_create_client: MagicMock,
        mock_query_api: MagicMock,
        mock_authenticate: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request network errors."""
        mock_query_api.return_value = {}
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client
        proxy = DownloadStationProxy(download_station_settings)

        # 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        with pytest.raises(PVRProviderAuthenticationError):
            proxy._request("API", "method")

        # Timeout
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(PVRProviderTimeoutError):
            proxy._request("API", "method")

    @patch("bookcard.pvr.download_clients.download_station.handle_http_error_response")
    @patch.object(DownloadStationProxy, "_execute_request")
    @patch.object(DownloadStationProxy, "authenticate")
    @patch.object(DownloadStationProxy, "_query_api_info")
    def test_request_http_error_other(
        self,
        mock_query_api: MagicMock,
        mock_authenticate: MagicMock,
        mock_execute_request: MagicMock,
        mock_handle: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test _request with HTTPStatusError (not 401/403) - lines 329-330, 336-337."""
        mock_query_api.return_value = {}
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        # _execute_request raises HTTPStatusError
        mock_execute_request.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )
        # Mock handle_http_error_response to not raise (for coverage of unreachable code)
        mock_handle.return_value = None

        proxy = DownloadStationProxy(download_station_settings)
        proxy._session_id = "test-session"
        # handle_http_error_response is called, but mocked to not raise
        # So the exception handler completes and code continues to unreachable section
        with pytest.raises(PVRProviderError, match="Request failed"):
            proxy._request("API", "method")
        mock_handle.assert_called_once()

    @patch.object(DownloadStationProxy, "_request")
    def test_add_task_from_url(
        self,
        mock_request: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test add_task_from_url."""
        mock_request.return_value = {"taskid": "123"}
        proxy = DownloadStationProxy(download_station_settings)
        result = proxy.add_task_from_url(
            "magnet:?xt=urn:btih:test", destination="/path"
        )
        assert result == "123"
        assert mock_request.call_args[1]["params"]["destination"] == "/path"

    @patch.object(DownloadStationProxy, "_request")
    def test_add_task_from_file(
        self,
        mock_request: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test add_task_from_file."""
        mock_request.return_value = {"taskid": "123"}
        proxy = DownloadStationProxy(download_station_settings)
        result = proxy.add_task_from_file(
            b"content", "test.torrent", destination="/path"
        )
        assert result == "123"
        call_kwargs = mock_request.call_args[1]
        assert "files" in call_kwargs
        assert call_kwargs["params"]["destination"] == "/path"

    @patch.object(DownloadStationProxy, "_request")
    def test_get_tasks(
        self,
        mock_request: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test get_tasks."""
        mock_request.return_value = {"tasks": [{"id": "123", "title": "test"}]}
        proxy = DownloadStationProxy(download_station_settings)
        result = proxy.get_tasks()
        assert len(result) == 1

    @patch.object(DownloadStationProxy, "_request")
    def test_remove_task(
        self,
        mock_request: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test remove_task."""
        proxy = DownloadStationProxy(download_station_settings)
        proxy.remove_task("123")
        mock_request.assert_called_with(
            "SYNO.DownloadStation.Task", "delete", version=1, params={"id": "123"}
        )


class TestDownloadStationClient:
    """Test DownloadStationClient."""

    def test_init_with_download_station_settings(
        self,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadStationSettings."""
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, DownloadStationSettings)
        assert client.enabled is True
        assert client.client_name == "Download Station"

    def test_init_with_download_client_settings(
        self,
        sabnzbd_settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = DownloadStationClient(
            settings=sabnzbd_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, DownloadStationSettings)

    @patch.object(DownloadStationProxy, "add_task_from_url")
    def test_add_download_magnet(
        self,
        mock_add: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = "123"
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(DownloadStationProxy, "add_task_from_url")
    def test_add_url(
        self,
        mock_add: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_url."""
        mock_add.return_value = "123"
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_url("http://example.com/test.torrent", None, None, None)
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(DownloadStationProxy, "add_task_from_file")
    def test_add_file(
        self,
        mock_add: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        sample_torrent_file: Path,
    ) -> None:
        """Test add_file."""
        mock_add.return_value = "123"
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.add_file(str(sample_torrent_file), None, None, None)
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(DownloadStationProxy, "get_tasks")
    def test_get_items(
        self,
        mock_get_tasks: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items."""
        mock_get_tasks.return_value = [
            {
                "id": "123",
                "title": "Test Download",
                "status": 1,  # downloading
                "size": 1000000,
                "additional": {
                    "transfer": {
                        "size_downloaded": 500000,
                        "speed_download": 1024,
                        "eta": 60,
                    },
                    "detail": {"destination": "/dest"},
                },
            },
            {"id": ""},  # Should skip
        ]
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "123"
        assert items[0]["progress"] == 0.5
        assert items[0]["download_speed_bytes_per_sec"] == 1024
        assert items[0]["eta_seconds"] == 60

    @patch.object(DownloadStationProxy, "get_tasks")
    def test_get_items_progress_cap(
        self,
        mock_get_tasks: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items progress cap."""
        mock_get_tasks.return_value = [
            {
                "id": "123",
                "size": 100,
                "additional": {"transfer": {"size_downloaded": 200}},  # > 100%
            }
        ]
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert items[0]["progress"] == 1.0

    @patch.object(DownloadStationProxy, "get_tasks")
    def test_get_items_error(
        self,
        mock_get_tasks: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items error."""
        mock_get_tasks.side_effect = Exception("API Error")
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    def test_get_items_disabled(
        self,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.get_items() == []

    @patch.object(DownloadStationProxy, "remove_task")
    def test_remove_item(
        self,
        mock_remove: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item."""
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.remove_item("123", _delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    def test_remove_item_disabled(
        self,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("123")

    @patch.object(DownloadStationProxy, "remove_task")
    def test_remove_item_error(
        self,
        mock_remove: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item error."""
        mock_remove.side_effect = Exception("API Error")
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("123")

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch.object(DownloadStationProxy, "get_tasks")
    @patch.object(DownloadStationProxy, "authenticate")
    def test_test_connection(
        self,
        mock_authenticate: MagicMock,
        mock_get_tasks: MagicMock,
        mock_query_api: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection."""
        mock_get_tasks.return_value = []
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.test_connection()
        assert result is True
        mock_authenticate.assert_called_once()
        mock_get_tasks.assert_called_once()

    @patch.object(DownloadStationProxy, "authenticate")
    def test_test_connection_error(
        self,
        mock_authenticate: MagicMock,
        download_station_settings: DownloadStationSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection error."""
        mock_authenticate.side_effect = Exception("Connect Error")
        client = DownloadStationClient(
            settings=download_station_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

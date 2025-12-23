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

from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
)
from bookcard.pvr.download_clients.download_station import (
    DownloadStationClient,
    DownloadStationProxy,
    DownloadStationSettings,
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

    @patch.object(DownloadStationProxy, "_request")
    def test_add_task_from_url(
        self,
        mock_request: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test add_task_from_url."""
        mock_request.return_value = {"taskid": "123"}
        proxy = DownloadStationProxy(download_station_settings)
        result = proxy.add_task_from_url("magnet:?xt=urn:btih:test")
        assert result == "123"

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


class TestDownloadStationClient:
    """Test DownloadStationClient."""

    def test_init_with_download_station_settings(
        self, download_station_settings: DownloadStationSettings
    ) -> None:
        """Test initialization with DownloadStationSettings."""
        client = DownloadStationClient(settings=download_station_settings)
        assert isinstance(client.settings, DownloadStationSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = DownloadStationClient(settings=base_download_client_settings)
        assert isinstance(client.settings, DownloadStationSettings)

    @patch.object(DownloadStationProxy, "add_task_from_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, download_station_settings: DownloadStationSettings
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = "123"
        client = DownloadStationClient(settings=download_station_settings)
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(DownloadStationProxy, "get_tasks")
    def test_get_items(
        self,
        mock_get_tasks: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test get_items."""
        mock_get_tasks.return_value = [
            {
                "id": "123",
                "title": "Test Download",
                "status": "downloading",
                "size": 1000000,
                "additional": {"transfer": {"size_downloaded": 500000}},
            }
        ]
        client = DownloadStationClient(settings=download_station_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "123"

    @patch.object(DownloadStationProxy, "remove_task")
    def test_remove_item(
        self, mock_remove: MagicMock, download_station_settings: DownloadStationSettings
    ) -> None:
        """Test remove_item."""
        client = DownloadStationClient(settings=download_station_settings)
        result = client.remove_item("123", _delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(DownloadStationProxy, "_query_api_info")
    @patch.object(DownloadStationProxy, "get_tasks")
    @patch.object(DownloadStationProxy, "authenticate")
    def test_test_connection(
        self,
        mock_authenticate: MagicMock,
        mock_get_tasks: MagicMock,
        download_station_settings: DownloadStationSettings,
    ) -> None:
        """Test test_connection."""
        mock_get_tasks.return_value = []
        client = DownloadStationClient(settings=download_station_settings)
        result = client.test_connection()
        assert result is True
        mock_authenticate.assert_called_once()
        mock_get_tasks.assert_called_once()

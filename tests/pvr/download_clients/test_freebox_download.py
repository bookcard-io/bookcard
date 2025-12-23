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

"""Tests for Freebox Download client."""

import hashlib
import hmac
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import (
    DownloadClientSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
)
from bookcard.pvr.download_clients.freebox_download import (
    FreeboxDownloadClient,
    FreeboxDownloadProxy,
    FreeboxDownloadSettings,
)


class TestFreeboxDownloadProxy:
    """Test FreeboxDownloadProxy."""

    def test_init(self, freebox_download_settings: FreeboxDownloadSettings) -> None:
        """Test proxy initialization."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        assert proxy.settings == freebox_download_settings
        assert proxy.api_url.endswith("/api/v1/")
        assert proxy._session_token is None

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_success(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {"challenge": "test-challenge"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        challenge = proxy._get_challenge()

        assert challenge == "test-challenge"

    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_get_challenge_failure(
        self,
        mock_create_client: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _get_challenge with failure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(PVRProviderError, match="Failed to get Freebox challenge"):
            proxy._get_challenge()

    def test_compute_password(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test _compute_password."""
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        challenge = "test-challenge"
        password = proxy._compute_password(challenge)

        # Verify it's a hex string
        assert isinstance(password, str)
        assert len(password) == 40  # SHA1 hex digest length

        # Verify it matches expected HMAC-SHA1
        assert freebox_download_settings.app_token is not None
        expected = hmac.new(
            freebox_download_settings.app_token.encode("ascii"),
            challenge.encode("ascii"),
            hashlib.sha1,
        ).hexdigest()
        assert password == expected

    def test_compute_password_no_token(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test _compute_password without app token."""
        freebox_download_settings.app_token = None
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="App Token is required"
        ):
            proxy._compute_password("challenge")

    @patch.object(FreeboxDownloadProxy, "_get_challenge")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_authenticate_success(
        self,
        mock_create_client: MagicMock,
        mock_get_challenge: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test successful authentication."""
        mock_get_challenge.return_value = "test-challenge"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {"session_token": "test-session-token"},
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy.authenticate()

        assert proxy._session_token == "test-session-token"

    @patch.object(FreeboxDownloadProxy, "authenticate")
    @patch("bookcard.pvr.download_clients.freebox_download.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test _request successful call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": {"id": 123}}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = FreeboxDownloadProxy(freebox_download_settings)
        proxy._session_token = "test-session"
        result = proxy._request("GET", "/downloads")

        # _request returns data.get("result", {}) - check if it's a dict with id
        if isinstance(result, dict):
            assert result.get("id") == 123
        else:
            assert result == 123

    @patch.object(FreeboxDownloadProxy, "_request")
    def test_add_task_from_url(
        self,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test add_task_from_url."""
        mock_request.return_value = {"id": 123}
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.add_task_from_url("magnet:?xt=urn:btih:test")
        assert result == "123"

    @patch.object(FreeboxDownloadProxy, "_request")
    def test_get_tasks(
        self,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test get_tasks."""
        mock_request.return_value = [{"id": 123, "name": "test"}]
        proxy = FreeboxDownloadProxy(freebox_download_settings)
        result = proxy.get_tasks()
        assert len(result) == 1


class TestFreeboxDownloadClient:
    """Test FreeboxDownloadClient."""

    def test_init_with_freebox_download_settings(
        self, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test initialization with FreeboxDownloadSettings."""
        client = FreeboxDownloadClient(settings=freebox_download_settings)
        assert isinstance(client.settings, FreeboxDownloadSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = FreeboxDownloadClient(settings=base_download_client_settings)
        assert isinstance(client.settings, FreeboxDownloadSettings)

    @patch.object(FreeboxDownloadProxy, "add_task_from_url")
    def test_add_download_magnet(
        self, mock_add: MagicMock, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test add_download with magnet link."""
        mock_add.return_value = "123"
        client = FreeboxDownloadClient(settings=freebox_download_settings)
        result = client.add_download("magnet:?xt=urn:btih:abc123&dn=test")
        assert result == "123"
        mock_add.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "get_tasks")
    def test_get_items(
        self,
        mock_get_tasks: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test get_items."""
        mock_get_tasks.return_value = [
            {
                "id": 123,
                "name": "Test Download",
                "status": "downloading",
                "size": 1000000,
                "tx_bytes": 500000,
            }
        ]
        client = FreeboxDownloadClient(settings=freebox_download_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "123"

    @patch.object(FreeboxDownloadProxy, "delete_task")
    def test_remove_item(
        self, mock_remove: MagicMock, freebox_download_settings: FreeboxDownloadSettings
    ) -> None:
        """Test remove_item."""
        client = FreeboxDownloadClient(settings=freebox_download_settings)
        result = client.remove_item("123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(FreeboxDownloadProxy, "_request")
    @patch.object(FreeboxDownloadProxy, "authenticate")
    def test_test_connection(
        self,
        mock_authenticate: MagicMock,
        mock_request: MagicMock,
        freebox_download_settings: FreeboxDownloadSettings,
    ) -> None:
        """Test test_connection."""
        mock_request.return_value = []
        client = FreeboxDownloadClient(settings=freebox_download_settings)
        result = client.test_connection()
        assert result is True
        mock_authenticate.assert_called_once()

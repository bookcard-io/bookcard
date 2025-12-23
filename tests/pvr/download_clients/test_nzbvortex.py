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

from bookcard.pvr.base import (
    DownloadClientSettings,
)
from bookcard.pvr.download_clients.nzbvortex import (
    NzbvortexClient,
    NzbvortexProxy,
    NzbvortexSettings,
)


class TestNzbvortexProxy:
    """Test NzbvortexProxy."""

    def test_init(self) -> None:
        """Test proxy initialization."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        proxy = NzbvortexProxy(settings)
        assert proxy.settings == settings
        assert proxy.api_url.endswith("/api")
        assert proxy._session_id is None

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_get_nonce(self, mock_create_client: MagicMock) -> None:
        """Test _get_nonce."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"authNonce": "test-nonce"}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(settings)
        nonce = proxy._get_nonce(mock_client)
        assert nonce == "test-nonce"

    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_authenticate_success(self, mock_create_client: MagicMock) -> None:
        """Test successful authentication."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response_nonce = MagicMock()
        mock_response_nonce.json.return_value = {"authNonce": "test-nonce"}
        mock_response_nonce.raise_for_status = Mock()
        mock_response_auth = MagicMock()
        mock_response_auth.json.return_value = {"result": "success"}
        mock_response_auth.raise_for_status = Mock()
        # Mock cookies to return session ID - httpx.Cookies is iterable
        mock_cookie = MagicMock()
        mock_cookie.name = "sessionid"
        mock_cookie.value = "test-session"
        # Make sure getattr works for name and value
        type(mock_cookie).name = "sessionid"
        type(mock_cookie).value = "test-session"
        mock_response_auth.cookies = [mock_cookie]
        # _get_nonce uses GET, _perform_login also uses GET
        # So we need to return different responses for different GET calls
        mock_client.get.side_effect = [mock_response_nonce, mock_response_auth]
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(settings)
        proxy._authenticate()

        assert proxy._session_id == "test-session"

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch("bookcard.pvr.download_clients.nzbvortex.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_authenticate: MagicMock,
    ) -> None:
        """Test _request successful call."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = NzbvortexProxy(settings)
        proxy._session_id = "test-session"
        result = proxy._request("GET", "/queue")

        assert result == {"result": "success"}

    @patch.object(NzbvortexProxy, "_request")
    def test_add_nzb(self, mock_request: MagicMock) -> None:
        """Test add_nzb."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_request.return_value = {"id": 123}
        proxy = NzbvortexProxy(settings)
        result = proxy.add_nzb(b"nzb content", "test.nzb")
        assert result == "123"


class TestNzbvortexClient:
    """Test NzbvortexClient."""

    def test_init_with_nzbvortex_settings(self) -> None:
        """Test initialization with NzbvortexSettings."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        client = NzbvortexClient(settings=settings)
        assert isinstance(client.settings, NzbvortexSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = NzbvortexClient(settings=base_download_client_settings)
        assert isinstance(client.settings, NzbvortexSettings)

    @patch.object(NzbvortexProxy, "add_nzb")
    def test_add_download_nzb_file(
        self,
        mock_add_nzb: MagicMock,
        sample_nzb_file: Path,
    ) -> None:
        """Test add_download with NZB file path."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_add_nzb.return_value = 123
        client = NzbvortexClient(settings=settings)
        result = client.add_download(str(sample_nzb_file))
        assert result == "123"
        mock_add_nzb.assert_called_once()

    @patch.object(NzbvortexProxy, "get_queue")
    def test_get_items(self, mock_get_queue: MagicMock) -> None:
        """Test get_items."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        mock_get_queue.return_value = [
            {
                "id": 1,
                "name": "test",
                "state": "downloading",
                "progress": 50.0,
                "size": 1000000,
            }
        ]
        client = NzbvortexClient(settings=settings)
        items = client.get_items()
        assert len(items) > 0

    @patch.object(NzbvortexProxy, "_authenticate")
    @patch.object(NzbvortexProxy, "remove_nzb")
    def test_remove_item(self, mock_remove: MagicMock, mock_auth: MagicMock) -> None:
        """Test remove_item."""
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        client = NzbvortexClient(settings=settings)
        result = client.remove_item("123", delete_files=True)
        assert result is True
        mock_remove.assert_called_once_with(123, True)

    @patch.object(NzbvortexProxy, "get_queue")
    def test_test_connection(self, mock_get_queue: MagicMock) -> None:
        """Test test_connection."""
        mock_get_queue.return_value = []
        settings = NzbvortexSettings(
            host="localhost",
            port=4321,
            api_key="test-api-key",
            timeout_seconds=30,
        )
        client = NzbvortexClient(settings=settings)
        result = client.test_connection()
        assert result is True
        mock_get_queue.assert_called_once()

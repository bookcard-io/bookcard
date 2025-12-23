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

"""Tests for SABnzbd download client."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.sabnzbd import (
    SabnzbdClient,
    SabnzbdProxy,
    SabnzbdSettings,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)


class TestSabnzbdProxy:
    """Test SabnzbdProxy."""

    def test_init(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test proxy initialization."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        assert proxy.settings == sabnzbd_settings
        assert "api" in proxy.api_url

    def test_build_request_params_with_api_key(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test _build_request_params with API key."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        params = proxy._build_request_params("queue")
        assert params["mode"] == "queue"
        assert params["output"] == "json"
        assert params["apikey"] == sabnzbd_settings.api_key

    def test_build_request_params_with_username_password(self) -> None:
        """Test _build_request_params with username/password."""
        settings = SabnzbdSettings(
            host="localhost",
            port=8080,
            username="user",
            password="pass",
            timeout_seconds=30,
        )
        proxy = SabnzbdProxy(settings)
        params = proxy._build_request_params("queue")
        assert params["ma_username"] == "user"
        assert params["ma_password"] == "pass"

    def test_build_request_params_no_auth(self) -> None:
        """Test _build_request_params without authentication."""
        settings = SabnzbdSettings(
            host="localhost",
            port=8080,
            timeout_seconds=30,
        )
        proxy = SabnzbdProxy(settings)
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires either API key"
        ):
            proxy._build_request_params("queue")

    @pytest.mark.parametrize(
        ("method", "has_files"),
        [
            ("GET", False),
            ("POST", False),
            ("POST", True),
        ],
    )
    def test_execute_request(
        self,
        method: str,
        has_files: bool,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test _execute_request with various methods."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response

        files = {"file": ("test.nzb", b"content")} if has_files else None
        result = proxy._execute_request(
            mock_client, method, {"mode": "queue"}, "queue", files=files
        )

        assert result == mock_response
        if method == "GET":
            mock_client.get.assert_called_once()
        else:
            mock_client.post.assert_called_once()

    def test_execute_request_unsupported_method(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test _execute_request with unsupported method."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        with pytest.raises(PVRProviderError, match="Unsupported HTTP method"):
            proxy._execute_request(MagicMock(), "PUT", {}, "queue")

    def test_parse_response_success(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test _parse_response with success."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.return_value = {"status": True, "queue": {}}
        result = proxy._parse_response(response)
        assert result == {"status": True, "queue": {}}

    def test_parse_response_error_false(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test _parse_response with error status False."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.return_value = {"status": False, "error": "Test error"}
        with pytest.raises(PVRProviderError, match="API error"):
            proxy._parse_response(response)

    def test_parse_response_error_string(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test _parse_response with error status string 'false'."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.return_value = {"status": "false", "error": "Test error"}
        with pytest.raises(PVRProviderError, match="API error"):
            proxy._parse_response(response)

    def test_parse_response_json_error(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test _parse_response with JSON decode error."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.text = "error: Invalid response"
        with pytest.raises(PVRProviderError, match="API error"):
            proxy._parse_response(response)

    def test_parse_response_text_error(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test _parse_response with text error response."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.text = "Error: Something went wrong"
        with pytest.raises(PVRProviderError, match="API error"):
            proxy._parse_response(response)

    @patch.object(SabnzbdProxy, "_build_request_params")
    @patch("bookcard.pvr.download_clients.sabnzbd.create_httpx_client")
    def test_request_success(
        self,
        mock_create_client: MagicMock,
        mock_build_params: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test _request successful call."""
        mock_build_params.return_value = {
            "mode": "queue",
            "output": "json",
            "apikey": "test",
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": True}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy._request("GET", "queue")

        assert result == {"status": True}

    @patch.object(SabnzbdProxy, "_request")
    def test_get_version(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test get_version."""
        mock_request.return_value = {"version": "3.7.0"}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.get_version()
        assert result == "3.7.0"

    @patch.object(SabnzbdProxy, "_request")
    def test_add_nzb(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test add_nzb."""
        mock_request.return_value = {"nzo_ids": ["test-id-123"]}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.add_nzb(b"nzb content", "test.nzb", category="test")
        assert result == "test-id-123"
        mock_request.assert_called_once()

    @patch.object(SabnzbdProxy, "_request")
    def test_add_nzb_no_ids(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test add_nzb with no nzo_ids in response."""
        mock_request.return_value = {"status": "test-status"}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.add_nzb(b"nzb content", "test.nzb")
        assert result == "test-status"

    @patch.object(SabnzbdProxy, "_request")
    def test_add_nzb_no_id_error(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test add_nzb with no ID in response."""
        mock_request.return_value = {}
        proxy = SabnzbdProxy(sabnzbd_settings)
        with pytest.raises(PVRProviderError, match="did not return a queue ID"):
            proxy.add_nzb(b"nzb content", "test.nzb")

    @patch.object(SabnzbdProxy, "_request")
    def test_get_queue(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test get_queue."""
        mock_request.return_value = {"queue": {"slots": [{"nzo_id": "test"}]}}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.get_queue()
        assert result == [{"nzo_id": "test"}]

    @patch.object(SabnzbdProxy, "_request")
    def test_get_history(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test get_history."""
        mock_request.return_value = {"history": {"slots": [{"nzo_id": "test"}]}}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.get_history()
        assert result == [{"nzo_id": "test"}]

    @patch.object(SabnzbdProxy, "_request")
    def test_remove_from_queue(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test remove_from_queue."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        proxy.remove_from_queue("test-id", delete_files=True)
        mock_request.assert_called_once()


class TestSabnzbdClient:
    """Test SabnzbdClient."""

    def test_init_with_sabnzbd_settings(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test initialization with SabnzbdSettings."""
        client = SabnzbdClient(settings=sabnzbd_settings)
        assert isinstance(client.settings, SabnzbdSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = SabnzbdClient(settings=base_download_client_settings)
        assert isinstance(client.settings, SabnzbdSettings)

    @patch.object(SabnzbdProxy, "add_nzb")
    def test_add_download_nzb_file(
        self,
        mock_add_nzb: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
        sample_nzb_file: Path,
    ) -> None:
        """Test add_download with NZB file path."""
        mock_add_nzb.return_value = "test-id-123"
        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.add_download(str(sample_nzb_file))
        assert result == "test-id-123"
        mock_add_nzb.assert_called_once()

    @patch.object(SabnzbdProxy, "add_nzb")
    @patch("bookcard.pvr.download_clients.sabnzbd.httpx.Client")
    def test_add_download_nzb_url(
        self,
        mock_client_class: MagicMock,
        mock_add_nzb: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
        sample_nzb_url: str,
    ) -> None:
        """Test add_download with NZB URL."""
        mock_add_nzb.return_value = "test-id-123"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.add_download(sample_nzb_url)
        assert result == "test-id-123"

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items."""
        mock_get_queue.return_value = [
            {
                "nzo_id": "test-1",
                "filename": "Test NZB",
                "status": "Downloading",
                "mb": 1000,
                "mbleft": 500,
                "timeleft": 60,
            }
        ]
        mock_get_history.return_value = []
        client = SabnzbdClient(settings=sabnzbd_settings)
        items = client.get_items()
        assert len(items) > 0

    @patch.object(SabnzbdProxy, "remove_from_queue")
    def test_remove_item_from_queue(
        self, mock_remove: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test remove_item from queue."""
        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.remove_item("test-id", delete_files=True)
        assert result is True
        mock_remove.assert_called_once()

    @patch.object(SabnzbdProxy, "get_version")
    def test_test_connection(
        self, mock_get_version: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test test_connection."""
        mock_get_version.return_value = "3.7.0"
        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.test_connection()
        assert result is True

    def test_parse_response_text_error_lowercase(
        self, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test _parse_response with text error starting with 'error'."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        response = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.text = "error: Something went wrong"
        with pytest.raises(PVRProviderError, match="API error"):
            proxy._parse_response(response)

    @patch.object(SabnzbdProxy, "_build_request_params")
    @patch("bookcard.pvr.download_clients.sabnzbd.create_httpx_client")
    def test_request_with_params(
        self,
        mock_create_client: MagicMock,
        mock_build_params: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test _request with additional params."""
        mock_build_params.return_value = {
            "mode": "queue",
            "output": "json",
            "apikey": "test",
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": True}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy._request("GET", "queue", params={"start": 0, "limit": 10})
        assert result == {"status": True}

    @patch.object(SabnzbdProxy, "_build_request_params")
    @patch("bookcard.pvr.download_clients.sabnzbd.create_httpx_client")
    def test_request_http_error(
        self,
        mock_create_client: MagicMock,
        mock_build_params: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test _request with HTTP error."""
        import httpx

        mock_build_params.return_value = {
            "mode": "queue",
            "output": "json",
            "apikey": "test",
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = error
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_create_client.return_value = mock_client

        proxy = SabnzbdProxy(sabnzbd_settings)
        with pytest.raises(httpx.HTTPStatusError):
            proxy._request("GET", "queue")

    @patch.object(SabnzbdProxy, "_request")
    def test_add_nzb_with_priority(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test add_nzb with priority."""
        mock_request.return_value = {"nzo_ids": ["test-id-123"]}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.add_nzb(b"nzb content", "test.nzb", priority=1)
        assert result == "test-id-123"
        call_args = mock_request.call_args
        assert call_args[1]["params"]["priority"] == 1

    @patch.object(SabnzbdProxy, "_request")
    def test_get_queue_with_params(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test get_queue with start and limit."""
        mock_request.return_value = {"queue": {"slots": [{"nzo_id": "test"}]}}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.get_queue(start=10, limit=20)
        assert result == [{"nzo_id": "test"}]
        call_args = mock_request.call_args
        assert call_args[1]["params"]["start"] == 10
        assert call_args[1]["params"]["limit"] == 20

    @patch.object(SabnzbdProxy, "_request")
    def test_get_history_with_params(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test get_history with start and limit."""
        mock_request.return_value = {"history": {"slots": [{"nzo_id": "test"}]}}
        proxy = SabnzbdProxy(sabnzbd_settings)
        result = proxy.get_history(start=10, limit=20)
        assert result == [{"nzo_id": "test"}]
        call_args = mock_request.call_args
        assert call_args[1]["params"]["start"] == 10
        assert call_args[1]["params"]["limit"] == 20

    @patch.object(SabnzbdProxy, "_request")
    def test_remove_from_history(
        self, mock_request: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test remove_from_history."""
        proxy = SabnzbdProxy(sabnzbd_settings)
        proxy.remove_from_history("test-id", delete_files=True, delete_permanently=True)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["params"]["archive"] == 0

    def test_add_download_disabled(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test add_download when disabled."""
        client = SabnzbdClient(settings=sabnzbd_settings, enabled=False)
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("http://example.com/file.nzb")

    @patch.object(SabnzbdProxy, "add_nzb")
    def test_add_download_with_category(
        self, mock_add_nzb: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test add_download with category."""
        mock_add_nzb.return_value = "test-id-123"
        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.add_download("http://example.com/file.nzb", category="test-cat")
        assert result == "test-id-123"
        mock_add_nzb.assert_called_once()
        call_args = mock_add_nzb.call_args
        assert call_args[1]["category"] == "test-cat"

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items_with_history(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items with history items."""
        mock_get_queue.return_value = []
        mock_get_history.return_value = [
            {
                "nzo_id": "test-1",
                "name": "Test NZB",
                "status": "Completed",
                "mb": 1000,
                "storage": "/downloads/test",
            }
        ]
        client = SabnzbdClient(settings=sabnzbd_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["status"] == "completed"
        assert items[0]["file_path"] == "/downloads/test"

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items_with_failed(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items with failed items."""
        mock_get_queue.return_value = []
        mock_get_history.return_value = [
            {
                "nzo_id": "test-1",
                "name": "Test NZB",
                "status": "Failed",
                "mb": 1000,
            }
        ]
        client = SabnzbdClient(settings=sabnzbd_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["status"] == "failed"

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items_progress_over_100(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items with progress over 100%."""
        mock_get_queue.return_value = [
            {
                "nzo_id": "test-1",
                "filename": "Test NZB",
                "status": "Downloading",
                "mb": 1000,
                "mbleft": -100,  # Negative remaining
            }
        ]
        mock_get_history.return_value = []
        client = SabnzbdClient(settings=sabnzbd_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["progress"] == 1.0  # Should be capped

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items_with_timeleft_int(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items with timeleft as int."""
        mock_get_queue.return_value = [
            {
                "nzo_id": "test-1",
                "filename": "Test NZB",
                "status": "Downloading",
                "mb": 1000,
                "mbleft": 500,
                "timeleft": 60,
            }
        ]
        mock_get_history.return_value = []
        client = SabnzbdClient(settings=sabnzbd_settings)
        items = client.get_items()
        assert len(items) == 1
        assert items[0]["eta_seconds"] == 60

    @patch.object(SabnzbdProxy, "get_queue")
    @patch.object(SabnzbdProxy, "get_history")
    def test_get_items_error(
        self,
        mock_get_history: MagicMock,
        mock_get_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test get_items with error."""
        mock_get_queue.side_effect = Exception("Connection error")
        client = SabnzbdClient(settings=sabnzbd_settings)
        with pytest.raises(PVRProviderError, match="Failed to get downloads"):
            client.get_items()

    @patch.object(SabnzbdProxy, "remove_from_queue")
    @patch.object(SabnzbdProxy, "remove_from_history")
    def test_remove_item_from_history(
        self,
        mock_remove_history: MagicMock,
        mock_remove_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test remove_item from history when not in queue."""
        from bookcard.pvr.exceptions import PVRProviderError

        mock_remove_queue.side_effect = PVRProviderError("Not in queue")
        client = SabnzbdClient(settings=sabnzbd_settings)
        result = client.remove_item("test-id", delete_files=True)
        assert result is True
        mock_remove_history.assert_called_once()

    @patch.object(SabnzbdProxy, "remove_from_queue")
    @patch.object(SabnzbdProxy, "remove_from_history")
    def test_remove_item_error(
        self,
        mock_remove_history: MagicMock,
        mock_remove_queue: MagicMock,
        sabnzbd_settings: SabnzbdSettings,
    ) -> None:
        """Test remove_item with error."""
        mock_remove_queue.side_effect = Exception("Remove error")
        mock_remove_history.side_effect = Exception("Remove error")
        client = SabnzbdClient(settings=sabnzbd_settings)
        with pytest.raises(PVRProviderError, match="Failed to remove"):
            client.remove_item("test-id")

    def test_remove_item_disabled(self, sabnzbd_settings: SabnzbdSettings) -> None:
        """Test remove_item when disabled."""
        client = SabnzbdClient(settings=sabnzbd_settings, enabled=False)
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("test-id")

    @patch.object(SabnzbdProxy, "get_version")
    def test_test_connection_error(
        self, mock_get_version: MagicMock, sabnzbd_settings: SabnzbdSettings
    ) -> None:
        """Test test_connection with error."""
        mock_get_version.side_effect = Exception("Connection error")
        client = SabnzbdClient(settings=sabnzbd_settings)
        with pytest.raises(PVRProviderError, match="Failed to connect"):
            client.test_connection()

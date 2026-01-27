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

"""Tests for Direct HTTP client module."""

from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.direct_http.client import DirectHttpClient
from bookcard.pvr.download_clients.direct_http.settings import DirectHttpSettings
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.status import DownloadStatus


class TestDirectHttpClient:
    """Test DirectHttpClient class."""

    def test_init_with_direct_http_settings(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test initialization with DirectHttpSettings."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
        )
        assert client.settings == direct_http_settings
        assert client.client_name == "DirectHTTP"

    def test_init_with_base_settings(
        self,
        base_download_client_settings: DownloadClientSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test initialization with base DownloadClientSettings."""
        client = DirectHttpClient(
            base_download_client_settings,
            mock_file_fetcher,
            mock_url_router,
        )
        assert isinstance(client.settings, DirectHttpSettings)

    def test_init_with_dependencies(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_state_manager: MagicMock,
        mock_url_resolver: MagicMock,
        mock_file_downloader: MagicMock,
        mock_filename_resolver: MagicMock,
        mock_html_parser: MagicMock,
        mock_time_provider: MagicMock,
    ) -> None:
        """Test initialization with injected dependencies."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            state_manager=mock_state_manager,
            url_resolvers=[mock_url_resolver],
            file_downloader=mock_file_downloader,
            filename_resolver=mock_filename_resolver,
            html_parser=mock_html_parser,
            time_provider=mock_time_provider,
        )
        assert client._state_manager == mock_state_manager
        assert client._url_resolvers == [mock_url_resolver]

    def test_client_name(self) -> None:
        """Test client_name property."""
        client = DirectHttpClient(
            DirectHttpSettings(host="localhost", port=8080),
            MagicMock(),
            MagicMock(),
        )
        assert client.client_name == "DirectHTTP"

    def test_add_url(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_state_manager: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test adding a URL for download."""
        direct_http_settings.download_path = str(temp_dir)
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            state_manager=mock_state_manager,
        )

        download_id = client.add_url(
            "https://example.com/file.pdf",
            "Test Book",
            "category",
            None,
        )

        assert isinstance(download_id, str)
        assert len(download_id) > 0
        mock_state_manager.create.assert_called_once()
        mock_state_manager.cleanup_old.assert_called_once()

    def test_resolve_url(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_url_resolver: MagicMock,
    ) -> None:
        """Test URL resolution."""
        mock_url_resolver.can_resolve.return_value = True
        mock_url_resolver.resolve.return_value = "https://resolved.com/file.pdf"

        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            url_resolvers=[mock_url_resolver],
        )

        resolved = client._resolve_url("https://example.com")
        assert resolved == "https://resolved.com/file.pdf"

    def test_resolve_url_no_resolver(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test URL resolution when no resolver matches."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
        )

        url = "https://example.com/file.pdf"
        resolved = client._resolve_url(url)
        assert resolved == url

    def test_get_items(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_state_manager: MagicMock,
    ) -> None:
        """Test getting download items."""
        from bookcard.pvr.download_clients.direct_http.state import DownloadState

        mock_state = DownloadState(
            id="test-id",
            url="https://example.com",
            title="Test",
            status=DownloadStatus.DOWNLOADING,
            progress=0.5,
            size_bytes=1000,
            downloaded_bytes=500,
            speed=100.0,
            path="/path/to/file",
            error=None,
        )
        mock_state_manager.get_all.return_value = [mock_state]

        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            state_manager=mock_state_manager,
        )

        items = client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "test-id"
        assert items[0]["title"] == "Test"
        assert items[0]["status"] == DownloadStatus.DOWNLOADING

    def test_remove_item(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_state_manager: MagicMock,
    ) -> None:
        """Test removing a download item."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            state_manager=mock_state_manager,
        )

        # Add a future to active_futures
        future = Future()
        client._active_futures["test-id"] = future

        result = client.remove_item("test-id", delete_files=False)
        assert result is True
        assert "test-id" not in client._active_futures
        mock_state_manager.remove.assert_called_once_with("test-id")

    def test_remove_item_cancels_future(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_state_manager: MagicMock,
    ) -> None:
        """Test that removing item cancels active future."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            state_manager=mock_state_manager,
        )

        future = Future()
        client._active_futures["test-id"] = future

        client.remove_item("test-id")
        assert future.cancelled() is True

    def test_test_connection_success(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
        mock_http_client_factory: MagicMock,
    ) -> None:
        """Test connection test success."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_http_client_factory.return_value = mock_client

        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            http_client_factory=mock_http_client_factory,
        )

        result = client.test_connection()
        assert result is True

    def test_test_connection_failure(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test connection test failure."""

        # Create a new factory that returns a client that raises
        def failing_factory() -> MagicMock:
            mock_client = MagicMock()
            mock_client.get.side_effect = Exception("Connection failed")
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            return mock_client

        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            http_client_factory=failing_factory,
        )

        result = client.test_connection()
        assert result is False

    def test_test_connection_no_factory(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test connection test when factory is None."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
            http_client_factory=None,
        )
        client._http_client_factory = None

        result = client.test_connection()
        assert result is False

    def test_shutdown(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test shutdown."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
        )

        client.shutdown()
        # Executor should be shut down
        assert client._executor._shutdown is True

    def test_raise_provider_error(
        self,
        direct_http_settings: DirectHttpSettings,
        mock_file_fetcher: MagicMock,
        mock_url_router: MagicMock,
    ) -> None:
        """Test _raise_provider_error method."""
        client = DirectHttpClient(
            direct_http_settings,
            mock_file_fetcher,
            mock_url_router,
        )

        with pytest.raises(PVRProviderError, match="test error"):
            client._raise_provider_error("test error")

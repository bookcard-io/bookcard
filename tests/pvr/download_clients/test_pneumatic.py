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

"""Tests for Pneumatic download client."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol, UrlRouterProtocol
from bookcard.pvr.download_clients.pneumatic import (
    PneumaticClient,
    PneumaticSettings,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.status import DownloadStatus


class TestPneumaticClient:
    """Test PneumaticClient."""

    def test_init_with_pneumatic_settings(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with PneumaticSettings."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, PneumaticSettings)
        assert client.enabled is True
        assert Path(pneumatic_settings.nzb_folder).exists()
        assert Path(pneumatic_settings.strm_folder).exists()

    def test_client_name(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test client_name property."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert client.client_name == "Pneumatic"

    def test_init_with_download_client_settings(
        self,
        base_download_client_settings: DownloadClientSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        # Set download_path to a writable temp directory
        base_download_client_settings.download_path = str(temp_dir / "downloads")
        client = PneumaticClient(
            settings=base_download_client_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, PneumaticSettings)

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_add_download_nzb_file(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        sample_nzb_file: Path,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with NZB file path - Pneumatic only accepts HTTP URLs."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Pneumatic only accepts HTTP URLs, not file paths
        # So we need to mock it as if it's downloading from a URL
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = sample_nzb_file.read_bytes()
        mock_response.raise_for_status = lambda: None
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        # Use a URL instead of file path
        result = client.add_download("http://example.com/test.nzb", title="Test Book")
        assert result.startswith("pneumatic_")

        # Verify files were created
        nzb_file = Path(pneumatic_settings.nzb_folder) / "Test_Book.nzb"
        strm_file = Path(pneumatic_settings.strm_folder) / "Test_Book.strm"
        assert nzb_file.exists()
        assert strm_file.exists()

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_add_download_nzb_url(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        sample_nzb_url: str,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with NZB URL."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        mock_client = mock_client_class.return_value
        mock_response = mock_client.__enter__.return_value.get.return_value
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = lambda: None

        result = client.add_download(sample_nzb_url, title="Test Book")
        # Pneumatic returns ID based on filename and modification time
        assert result.startswith("pneumatic_")

    def test_add_download_disabled(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download when disabled."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download("http://example.com/test.nzb")

    def test_add_download_invalid_url(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with invalid URL (not starting with http)."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        with pytest.raises(PVRProviderError, match="Invalid download URL"):
            client.add_download("file:///path/to/file.nzb")

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_add_download_without_title(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download without title (uses 'download' as filename)."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = lambda: None
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        result = client.add_download("http://example.com/test.nzb")
        assert result.startswith("pneumatic_")

        # Verify files were created with "download" as base name
        nzb_file = Path(pneumatic_settings.nzb_folder) / "download.nzb"
        strm_file = Path(pneumatic_settings.strm_folder) / "download.strm"
        assert nzb_file.exists()
        assert strm_file.exists()

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_add_download_exception(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test add_download with exception during download."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.RequestError(
            "Network error",
            request=httpx.Request("GET", "http://example.com/test.nzb"),
        )
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(PVRProviderError, match="Failed to add download"):
            client.add_download("http://example.com/test.nzb")

    def test_get_items(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items returns empty list."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        items = client.get_items()
        assert items == []

    def test_get_items_disabled(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when disabled."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        items = client.get_items()
        assert items == []

    def test_get_items_folder_not_exists(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items when strm folder doesn't exist."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "nonexistent")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        # Remove the folder if it was created during init
        strm_path = Path(pneumatic_settings.strm_folder)
        if strm_path.exists():
            strm_path.rmdir()
        items = client.get_items()
        assert items == []

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_get_items_with_strm_files(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with .strm files."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Create a .strm file
        strm_file = Path(pneumatic_settings.strm_folder) / "test.strm"
        strm_file.write_text(
            "plugin://plugin.program.pneumatic/?mode=strm", encoding="utf-8"
        )

        items = client.get_items()
        assert len(items) == 1
        assert items[0]["title"] == "test"
        assert items[0]["status"] == DownloadStatus.COMPLETED
        assert items[0]["progress"] == 1.0
        assert items[0]["client_item_id"].startswith("pneumatic_test.strm_")

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_get_items_with_locked_file(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with locked .strm file (being processed)."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Create a .strm file
        strm_file = Path(pneumatic_settings.strm_folder) / "locked.strm"
        strm_file.write_text(
            "plugin://plugin.program.pneumatic/?mode=strm", encoding="utf-8"
        )

        # Mock Path.open to raise OSError for this specific file
        original_open = Path.open

        def mock_open(self: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if (self == strm_file and "r+" in mode) or mode == "r+":
                raise OSError("File is locked")
            return original_open(self, mode, *args, **kwargs)

        with patch.object(Path, "open", mock_open):
            items = client.get_items()
            assert len(items) == 1
            assert items[0]["status"] == DownloadStatus.DOWNLOADING
            assert items[0]["progress"] == 0.5

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_get_items_file_error(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with file processing error."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Create a .strm file
        strm_file = Path(pneumatic_settings.strm_folder) / "error.strm"
        strm_file.write_text(
            "plugin://plugin.program.pneumatic/?mode=strm", encoding="utf-8"
        )

        # Mock Path.stat to raise an error for this specific file
        original_stat = Path.stat

        def mock_stat(self: Path, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self == strm_file:
                raise OSError("Permission denied")
            return original_stat(self, *args, **kwargs)

        with patch.object(Path, "stat", mock_stat):
            items = client.get_items()
            # Should skip the error file and return empty list
            assert items == []

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_get_items_folder_error(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test get_items with folder access error."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Mock Path.glob to raise an error
        strm_folder = Path(pneumatic_settings.strm_folder)
        original_glob = Path.glob

        def mock_glob(self: Path, pattern: str, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self == strm_folder:
                raise OSError("Permission denied")
            return original_glob(self, pattern, *args, **kwargs)

        with patch.object(Path, "glob", mock_glob):
            items = client.get_items()
            assert items == []

    def test_remove_item(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item returns False."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.remove_item("item-id", delete_files=True)
        assert result is False

    def test_remove_item_disabled(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test remove_item when disabled."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        with pytest.raises(PVRProviderError, match="disabled"):
            client.remove_item("item-id")

    def test_test_connection_success(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection when directories are writable."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        result = client.test_connection()
        assert result is True

    def test_test_connection_write_error(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection when folders are not writable."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Mock Path.write_text to raise PermissionError
        test_nzb = Path(pneumatic_settings.nzb_folder) / ".test_write"
        original_write_text = Path.write_text

        def mock_write_text(self: Path, *args: Any, **kwargs: Any) -> int:  # noqa: ANN401
            if self == test_nzb:
                raise PermissionError("Permission denied")
            return original_write_text(self, *args, **kwargs)

        with (
            patch.object(Path, "write_text", mock_write_text),
            pytest.raises(PVRProviderError, match="not writable"),
        ):
            client.test_connection()

    def test_test_connection_os_error(
        self,
        pneumatic_settings: PneumaticSettings,
        temp_dir: Path,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
    ) -> None:
        """Test test_connection with OSError."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(
            settings=pneumatic_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        # Mock Path to raise OSError when creating Path objects in test_connection
        # This will trigger the outer exception handler (line 326-328)
        call_count = [0]
        original_path_init = Path.__init__

        def mock_path_init(self: Path, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
            # Count calls and raise OSError after Path objects are created in test_connection
            # The first two Path() calls are nzb_folder and strm_folder
            result = original_path_init(self, *args, **kwargs)
            call_count[0] += 1
            if call_count[0] > 2:  # After nzb_folder and strm_folder
                raise OSError("Access denied")
            return result

        with (
            patch.object(Path, "__init__", mock_path_init),
            pytest.raises(PVRProviderError, match="Failed to test"),
        ):
            client.test_connection()

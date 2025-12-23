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
from unittest.mock import MagicMock, patch

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.pneumatic import (
    PneumaticClient,
    PneumaticSettings,
)


class TestPneumaticClient:
    """Test PneumaticClient."""

    def test_init_with_pneumatic_settings(
        self, pneumatic_settings: PneumaticSettings, temp_dir: Path
    ) -> None:
        """Test initialization with PneumaticSettings."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)
        assert isinstance(client.settings, PneumaticSettings)
        assert client.enabled is True
        assert Path(pneumatic_settings.nzb_folder).exists()
        assert Path(pneumatic_settings.strm_folder).exists()

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings, temp_dir: Path
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        # Set download_path to a writable temp directory
        base_download_client_settings.download_path = str(temp_dir / "downloads")
        client = PneumaticClient(settings=base_download_client_settings)
        assert isinstance(client.settings, PneumaticSettings)

    @patch("bookcard.pvr.download_clients.pneumatic.httpx.Client")
    def test_add_download_nzb_file(
        self,
        mock_client_class: MagicMock,
        pneumatic_settings: PneumaticSettings,
        sample_nzb_file: Path,
        temp_dir: Path,
    ) -> None:
        """Test add_download with NZB file path - Pneumatic only accepts HTTP URLs."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)

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
    ) -> None:
        """Test add_download with NZB URL."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)

        mock_client = mock_client_class.return_value
        mock_response = mock_client.__enter__.return_value.get.return_value
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = lambda: None

        result = client.add_download(sample_nzb_url, title="Test Book")
        # Pneumatic returns ID based on filename and modification time
        assert result.startswith("pneumatic_")

    def test_get_items(
        self, pneumatic_settings: PneumaticSettings, temp_dir: Path
    ) -> None:
        """Test get_items returns empty list."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)
        items = client.get_items()
        assert items == []

    def test_remove_item(
        self, pneumatic_settings: PneumaticSettings, temp_dir: Path
    ) -> None:
        """Test remove_item returns False."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)
        result = client.remove_item("item-id", delete_files=True)
        assert result is False

    def test_test_connection_success(
        self, pneumatic_settings: PneumaticSettings, temp_dir: Path
    ) -> None:
        """Test test_connection when directories are writable."""
        pneumatic_settings.nzb_folder = str(temp_dir / "nzb")
        pneumatic_settings.strm_folder = str(temp_dir / "strm")
        client = PneumaticClient(settings=pneumatic_settings)
        result = client.test_connection()
        assert result is True

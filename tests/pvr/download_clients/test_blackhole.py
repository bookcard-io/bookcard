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

"""Tests for blackhole download clients."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.pvr.base import DownloadClientSettings, PVRProviderError
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeClient,
    TorrentBlackholeSettings,
    UsenetBlackholeClient,
    UsenetBlackholeSettings,
    _clean_filename,
)


class TestCleanFilename:
    """Test _clean_filename function."""

    @pytest.mark.parametrize(
        ("input_filename", "expected"),
        [
            ("normal_file", "normal_file"),
            ("file with spaces", "file_with_spaces"),
            ("file<>name", "file__name"),
            ('file:"name"', "file__name_"),
            ("file/name", "file_name"),
            ("file\\name", "file_name"),
            ("file|name", "file_name"),
            ("file?name", "file_name"),
            ("file*name", "file_name"),
            ("  file  ", "file"),
            ("...file...", "file"),
            ("file.", "file"),
            (".file", "file"),
            ("A" * 300, "A" * 200),  # Truncate long names
        ],
    )
    def test_clean_filename(self, input_filename: str, expected: str) -> None:
        """Test _clean_filename with various inputs."""
        result = _clean_filename(input_filename)
        assert result == expected


class TestTorrentBlackholeClient:
    """Test TorrentBlackholeClient."""

    def test_init_with_torrent_blackhole_settings(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test initialization with TorrentBlackholeSettings."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        assert isinstance(client.settings, TorrentBlackholeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = TorrentBlackholeClient(settings=base_download_client_settings)
        assert isinstance(client.settings, TorrentBlackholeSettings)

    def test_init_disabled(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test initialization with enabled=False."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings, enabled=False
        )
        assert client.enabled is False

    def test_add_download_magnet_link_enabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
    ) -> None:
        """Test adding magnet link when save_magnet_files is enabled."""
        torrent_blackhole_settings.save_magnet_files = True
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings, enabled=True
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(sample_magnet_link, title="Test Book")
        assert result == "magnet_blackhole"
        assert isinstance(result, str)

        # Verify file was created
        magnet_file = Path(client.settings.torrent_folder) / "Test_Book.magnet"
        assert magnet_file.exists()
        assert magnet_file.read_text() == sample_magnet_link

    def test_add_download_magnet_link_disabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
    ) -> None:
        """Test adding magnet link when save_magnet_files is disabled."""
        torrent_blackhole_settings.save_magnet_files = False
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)

        with pytest.raises(PVRProviderError, match="Magnet links not supported"):
            client.add_download(sample_magnet_link)

    def test_add_download_magnet_link_custom_extension(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
    ) -> None:
        """Test adding magnet link with custom extension."""
        torrent_blackhole_settings.save_magnet_files = True
        torrent_blackhole_settings.magnet_file_extension = ".mag"
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        client.add_download(sample_magnet_link, title="Test")
        magnet_file = Path(client.settings.torrent_folder) / "Test.mag"
        assert magnet_file.exists()

    def test_add_download_magnet_link_extension_with_dot(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
    ) -> None:
        """Test adding magnet link with extension that has leading dot."""
        torrent_blackhole_settings.save_magnet_files = True
        torrent_blackhole_settings.magnet_file_extension = ".magnet"
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        client.add_download(sample_magnet_link, title="Test")
        magnet_file = Path(client.settings.torrent_folder) / "Test.magnet"
        assert magnet_file.exists()

    def test_add_download_torrent_file(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_torrent_file: Path,
    ) -> None:
        """Test adding torrent from file path."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings, enabled=True
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_torrent_file), title="Test Book")
        assert result == "torrent_blackhole"

        # Verify file was copied
        copied_file = Path(client.settings.torrent_folder) / "Test_Book.torrent"
        assert copied_file.exists()
        assert copied_file.read_bytes() == sample_torrent_file.read_bytes()

    def test_add_download_torrent_file_no_title(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_torrent_file: Path,
    ) -> None:
        """Test adding torrent from file path without title."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_torrent_file))
        assert result == "torrent_blackhole"

        # Verify file was copied with default name
        copied_file = Path(client.settings.torrent_folder) / "download.torrent"
        assert copied_file.exists()

    @patch("bookcard.pvr.download_clients.blackhole.httpx.Client")
    def test_add_download_torrent_url(
        self,
        mock_client_class: MagicMock,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_torrent_url: str,
    ) -> None:
        """Test adding torrent from URL."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings, enabled=True
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"torrent content"
        mock_response.raise_for_status = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        result = client.add_download(sample_torrent_url, title="Test Book")
        assert result == "torrent_blackhole"

        # Verify file was saved
        saved_file = Path(client.settings.torrent_folder) / "Test_Book.torrent"
        assert saved_file.exists()

        # Verify file was saved
        saved_file = Path(client.settings.torrent_folder) / "Test_Book.torrent"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"torrent content"

    def test_add_download_unsupported_url(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test adding unsupported URL type."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)

        with pytest.raises(PVRProviderError, match="Unsupported download URL type"):
            client.add_download("ftp://example.com/file.torrent")

    def test_add_download_disabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
    ) -> None:
        """Test adding download when client is disabled."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings, enabled=False
        )

        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download(sample_magnet_link)

    def test_get_items(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test get_items returns empty list."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        items = client.get_items()
        assert items == []

    def test_remove_item(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test remove_item returns False."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        result = client.remove_item("item-id", delete_files=True)
        assert result is False

    def test_test_connection_success(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test test_connection when directories are writable."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        Path(client.settings.watch_folder).mkdir(parents=True, exist_ok=True)

        result = client.test_connection()
        assert result is True

    def test_test_connection_not_writable(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test test_connection when torrent folder is not writable."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        # Create a file with the same name as the folder to make it non-writable
        Path(client.settings.torrent_folder).parent.mkdir(parents=True, exist_ok=True)
        Path(client.settings.torrent_folder).touch()

        with pytest.raises(PVRProviderError, match="not writable"):
            client.test_connection()

    def test_test_connection_watch_folder_missing(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test test_connection when watch folder doesn't exist."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        # Don't create watch folder

        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client.test_connection()

    def test_raise_magnet_not_supported_error(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test _raise_magnet_not_supported_error method."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        with pytest.raises(PVRProviderError, match="Magnet links not supported"):
            client._raise_magnet_not_supported_error()

    def test_raise_unsupported_url_error(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test _raise_unsupported_url_error method."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        with pytest.raises(PVRProviderError, match="Unsupported download URL type"):
            client._raise_unsupported_url_error("ftp://example.com/file")

    def test_raise_watch_folder_error(
        self, torrent_blackhole_settings: TorrentBlackholeSettings
    ) -> None:
        """Test _raise_watch_folder_error method."""
        client = TorrentBlackholeClient(settings=torrent_blackhole_settings)
        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client._raise_watch_folder_error("/nonexistent/path")


class TestUsenetBlackholeClient:
    """Test UsenetBlackholeClient."""

    def test_init_with_usenet_blackhole_settings(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test initialization with UsenetBlackholeSettings."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        assert isinstance(client.settings, UsenetBlackholeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self, base_download_client_settings: DownloadClientSettings
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = UsenetBlackholeClient(settings=base_download_client_settings)
        assert isinstance(client.settings, UsenetBlackholeSettings)

    def test_init_disabled(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test initialization with enabled=False."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings, enabled=False
        )
        assert client.enabled is False

    def test_add_download_nzb_file(
        self, usenet_blackhole_settings: UsenetBlackholeSettings, sample_nzb_file: Path
    ) -> None:
        """Test adding NZB from file path."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings, enabled=True)
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_nzb_file), title="Test Book")
        assert result == "nzb_blackhole"

        # Verify file was copied
        copied_file = Path(client.settings.nzb_folder) / "Test_Book.nzb"
        assert copied_file.exists()
        assert copied_file.read_bytes() == sample_nzb_file.read_bytes()

    def test_add_download_nzb_file_no_title(
        self, usenet_blackhole_settings: UsenetBlackholeSettings, sample_nzb_file: Path
    ) -> None:
        """Test adding NZB from file path without title."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_nzb_file))
        assert result == "nzb_blackhole"

        # Verify file was copied with default name
        copied_file = Path(client.settings.nzb_folder) / "download.nzb"
        assert copied_file.exists()

    @patch("bookcard.pvr.download_clients.blackhole.httpx.Client")
    def test_add_download_nzb_url(
        self,
        mock_client_class: MagicMock,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        sample_nzb_url: str,
    ) -> None:
        """Test adding NZB from URL."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings, enabled=True)
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"nzb content"
        mock_response.raise_for_status = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        result = client.add_download(sample_nzb_url, title="Test Book")
        assert result == "nzb_blackhole"

        # Verify file was saved
        saved_file = Path(client.settings.nzb_folder) / "Test_Book.nzb"
        assert saved_file.exists()

        # Verify file was saved
        saved_file = Path(client.settings.nzb_folder) / "Test_Book.nzb"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"nzb content"

    def test_add_download_unsupported_url(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test adding unsupported URL type."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)

        with pytest.raises(PVRProviderError, match="Unsupported download URL type"):
            client.add_download("ftp://example.com/file.nzb")

    def test_add_download_disabled(
        self, usenet_blackhole_settings: UsenetBlackholeSettings, sample_nzb_url: str
    ) -> None:
        """Test adding download when client is disabled."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings, enabled=False
        )

        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download(sample_nzb_url)

    def test_get_items(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test get_items returns empty list."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        items = client.get_items()
        assert items == []

    def test_remove_item(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test remove_item returns False."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        result = client.remove_item("item-id", delete_files=True)
        assert result is False

    def test_test_connection_success(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test test_connection when directories are writable."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
        Path(client.settings.watch_folder).mkdir(parents=True, exist_ok=True)

        result = client.test_connection()
        assert result is True

    def test_test_connection_not_writable(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test test_connection when NZB folder is not writable."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        # Create a file with the same name as the folder to make it non-writable
        Path(client.settings.nzb_folder).parent.mkdir(parents=True, exist_ok=True)
        Path(client.settings.nzb_folder).touch()

        with pytest.raises(PVRProviderError, match="not writable"):
            client.test_connection()

    def test_test_connection_watch_folder_missing(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test test_connection when watch folder doesn't exist."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
        # Don't create watch folder

        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client.test_connection()

    def test_raise_unsupported_url_error(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test _raise_unsupported_url_error method."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        with pytest.raises(PVRProviderError, match="Unsupported download URL type"):
            client._raise_unsupported_url_error("ftp://example.com/file")

    def test_raise_watch_folder_error(
        self, usenet_blackhole_settings: UsenetBlackholeSettings
    ) -> None:
        """Test _raise_watch_folder_error method."""
        client = UsenetBlackholeClient(settings=usenet_blackhole_settings)
        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client._raise_watch_folder_error("/nonexistent/path")

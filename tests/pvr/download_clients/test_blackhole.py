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
from unittest.mock import MagicMock

import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.base.interfaces import FileFetcherProtocol
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeClient,
    TorrentBlackholeSettings,
    UsenetBlackholeClient,
    UsenetBlackholeSettings,
    _clean_filename,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.services.file_fetcher import FileFetcher
from bookcard.pvr.utils.url_router import DownloadUrlRouter


@pytest.fixture
def file_fetcher() -> FileFetcher:
    """Create a file fetcher for testing."""
    return FileFetcher(timeout=30)


@pytest.fixture
def url_router() -> DownloadUrlRouter:
    """Create a URL router for testing."""
    return DownloadUrlRouter()


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
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with TorrentBlackholeSettings."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, TorrentBlackholeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        base_download_client_settings: DownloadClientSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = TorrentBlackholeClient(
            settings=base_download_client_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, TorrentBlackholeSettings)

    def test_init_disabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with enabled=False."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.enabled is False

    def test_add_download_magnet_link_enabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding magnet link when save_magnet_files is enabled."""
        torrent_blackhole_settings.save_magnet_files = True
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=True,
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
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding magnet link when save_magnet_files is disabled."""
        torrent_blackhole_settings.save_magnet_files = False
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        with pytest.raises(PVRProviderError, match="Magnet links not supported"):
            client.add_download(sample_magnet_link)

    def test_add_download_magnet_link_custom_extension(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding magnet link with custom extension."""
        torrent_blackhole_settings.save_magnet_files = True
        torrent_blackhole_settings.magnet_file_extension = ".mag"
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        client.add_download(sample_magnet_link, title="Test")
        magnet_file = Path(client.settings.torrent_folder) / "Test.mag"
        assert magnet_file.exists()

    def test_add_download_magnet_link_extension_with_dot(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding magnet link with extension that has leading dot."""
        torrent_blackhole_settings.save_magnet_files = True
        torrent_blackhole_settings.magnet_file_extension = ".magnet"
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        client.add_download(sample_magnet_link, title="Test")
        magnet_file = Path(client.settings.torrent_folder) / "Test.magnet"
        assert magnet_file.exists()

    def test_add_download_torrent_file(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_torrent_file: Path,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding torrent from file path."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=True,
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
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding torrent from file path without title."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_torrent_file))
        assert result == "torrent_blackhole"

        # Verify file was copied with default name
        copied_file = Path(client.settings.torrent_folder) / "download.torrent"
        assert copied_file.exists()

    def test_add_download_torrent_url(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_torrent_url: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding torrent from URL."""
        # Create mock file fetcher
        mock_file_fetcher = MagicMock(spec=FileFetcherProtocol)
        mock_file_fetcher.fetch_with_filename.return_value = (
            b"torrent content",
            "Test_Book.torrent",
        )

        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=mock_file_fetcher,
            url_router=url_router,
            enabled=True,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(sample_torrent_url, title="Test Book")
        assert result == "torrent_blackhole"

        # Verify file was saved
        saved_file = Path(client.settings.torrent_folder) / "Test_Book.torrent"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"torrent content"

    def test_add_download_unsupported_url(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding unsupported URL type."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        with pytest.raises(PVRProviderError, match="Invalid download URL"):
            client.add_download("ftp://example.com/file.torrent")

    def test_add_download_disabled(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        sample_magnet_link: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding download when client is disabled."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )

        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download(sample_magnet_link)

    def test_test_connection_success(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when directories are writable."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        Path(client.settings.watch_folder).mkdir(parents=True, exist_ok=True)

        result = client.test_connection()
        assert result is True

    def test_test_connection_not_writable(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when torrent folder is not writable."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        # Create a file with the same name as the folder to make it non-writable
        Path(client.settings.torrent_folder).parent.mkdir(parents=True, exist_ok=True)
        Path(client.settings.torrent_folder).touch()

        with pytest.raises(PVRProviderError, match="not writable"):
            client.test_connection()

    def test_test_connection_watch_folder_missing(
        self,
        torrent_blackhole_settings: TorrentBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when watch folder doesn't exist."""
        client = TorrentBlackholeClient(
            settings=torrent_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        # Don't create watch folder

        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client.test_connection()


class TestUsenetBlackholeClient:
    """Test UsenetBlackholeClient."""

    def test_init_with_usenet_blackhole_settings(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with UsenetBlackholeSettings."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, UsenetBlackholeSettings)
        assert client.enabled is True

    def test_init_with_download_client_settings(
        self,
        base_download_client_settings: DownloadClientSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with DownloadClientSettings conversion."""
        client = UsenetBlackholeClient(
            settings=base_download_client_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        assert isinstance(client.settings, UsenetBlackholeSettings)

    def test_init_disabled(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test initialization with enabled=False."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.enabled is False

    def test_add_download_nzb_file(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        sample_nzb_file: Path,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding NZB from file path."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=True,
        )
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_nzb_file), title="Test Book")
        assert result == "nzb_blackhole"

        # Verify file was copied
        copied_file = Path(client.settings.nzb_folder) / "Test_Book.nzb"
        assert copied_file.exists()
        assert copied_file.read_bytes() == sample_nzb_file.read_bytes()

    def test_add_download_nzb_file_no_title(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        sample_nzb_file: Path,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding NZB from file path without title."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(str(sample_nzb_file))
        assert result == "nzb_blackhole"

        # Verify file was copied with default name
        copied_file = Path(client.settings.nzb_folder) / "download.nzb"
        assert copied_file.exists()

    def test_add_download_nzb_url(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        sample_nzb_url: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding NZB from URL."""
        # Mock file_fetcher.fetch_content
        file_fetcher.fetch_content = MagicMock(return_value=b"nzb content")  # type: ignore[assignment]

        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=True,
        )
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        result = client.add_download(sample_nzb_url, title="Test Book")
        assert result == "nzb_blackhole"

        # Verify file was saved
        saved_file = Path(client.settings.nzb_folder) / "Test_Book.nzb"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"nzb content"

    def test_add_download_unsupported_url(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding unsupported URL type."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )

        with pytest.raises(PVRProviderError, match="Invalid download URL"):
            client.add_download("ftp://example.com/file.nzb")

    def test_add_download_disabled(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        sample_nzb_url: str,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test adding download when client is disabled."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )

        with pytest.raises(PVRProviderError, match="disabled"):
            client.add_download(sample_nzb_url)

    def test_test_connection_success(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when directories are writable."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
        Path(client.settings.watch_folder).mkdir(parents=True, exist_ok=True)

        result = client.test_connection()
        assert result is True

    def test_test_connection_not_writable(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when NZB folder is not writable."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        # Create a file with the same name as the folder to make it non-writable
        Path(client.settings.nzb_folder).parent.mkdir(parents=True, exist_ok=True)
        Path(client.settings.nzb_folder).touch()

        with pytest.raises(PVRProviderError, match="not writable"):
            client.test_connection()

    def test_test_connection_watch_folder_missing(
        self,
        usenet_blackhole_settings: UsenetBlackholeSettings,
        file_fetcher: FileFetcher,
        url_router: DownloadUrlRouter,
    ) -> None:
        """Test test_connection when watch folder doesn't exist."""
        client = UsenetBlackholeClient(
            settings=usenet_blackhole_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
        )
        Path(client.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
        # Don't create watch folder

        with pytest.raises(PVRProviderError, match="Watch folder does not exist"):
            client.test_connection()

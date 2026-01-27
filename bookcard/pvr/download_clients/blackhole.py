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

"""Blackhole download client implementations.

Blackhole clients write download files (torrents or NZBs) to a directory,
where they are picked up by external download clients. These are the simplest
download clients as they don't require API communication.
"""

import logging
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

from bookcard.pvr.base import (
    BaseDownloadClient,
    DownloadClientSettings,
)
from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.exceptions import PVRProviderError

logger = logging.getLogger(__name__)


class BlackholeSettings(DownloadClientSettings):
    """Settings for blackhole download clients.

    Attributes
    ----------
    watch_folder : str
        Directory to watch for completed downloads.
    """

    watch_folder: str


class TorrentBlackholeSettings(BlackholeSettings):
    """Settings for torrent blackhole client.

    Attributes
    ----------
    torrent_folder : str
        Directory where .torrent files are written.
    save_magnet_files : bool
        Whether to save magnet links as files (default: False).
    magnet_file_extension : str
        Extension for magnet files (default: '.magnet').
    """

    torrent_folder: str
    save_magnet_files: bool = False
    magnet_file_extension: str = ".magnet"


class UsenetBlackholeSettings(BlackholeSettings):
    """Settings for usenet blackhole client.

    Attributes
    ----------
    nzb_folder : str
        Directory where .nzb files are written.
    """

    nzb_folder: str


def _clean_filename(filename: str) -> str:
    """Clean filename for filesystem compatibility.

    Parameters
    ----------
    filename : str
        Original filename.

    Returns
    -------
    str
        Cleaned filename safe for filesystem.
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing dots and spaces first
    filename = filename.strip(". ")
    # Replace remaining spaces with underscores for filesystem safety
    filename = filename.replace(" ", "_")
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


class TorrentBlackholeClient(BaseDownloadClient):
    """Torrent blackhole download client.

    Writes .torrent files or magnet links to a directory where they are
    picked up by an external torrent client.
    """

    def __init__(
        self,
        settings: TorrentBlackholeSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize torrent blackhole client.

        Parameters
        ----------
        settings : TorrentBlackholeSettings | DownloadClientSettings
            Client settings.
        file_fetcher : FileFetcherProtocol
            File fetcher service.
        url_router : UrlRouterProtocol
            URL router service.
        http_client_factory : Callable[[], HttpClientProtocol] | None
            HTTP client factory.
        enabled : bool
            Whether this client is enabled.
        """
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, TorrentBlackholeSettings
        ):
            # Convert to TorrentBlackholeSettings
            torrent_settings = TorrentBlackholeSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                watch_folder=settings.download_path or tempfile.gettempdir(),
                torrent_folder=settings.download_path or tempfile.gettempdir(),
                save_magnet_files=False,
                magnet_file_extension=".magnet",
            )
            settings = torrent_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: TorrentBlackholeSettings = settings

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Blackhole"

    def _raise_magnet_not_supported_error(self) -> None:
        """Raise error for unsupported magnet links.

        Raises
        ------
        PVRProviderError
            Always raises with error message.
        """
        msg = "Magnet links not supported (save_magnet_files is False)"
        raise PVRProviderError(msg)

    def _raise_watch_folder_error(self, watch_folder: str) -> None:
        """Raise error for missing watch folder.

        Parameters
        ----------
        watch_folder : str
            Watch folder path.

        Raises
        ------
        PVRProviderError
            Always raises with error message.
        """
        msg = f"Watch folder does not exist: {watch_folder}"
        raise PVRProviderError(msg)

    def add_magnet(
        self,
        magnet_url: str,
        title: str | None,
        _category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        if not self.settings.save_magnet_files:
            self._raise_magnet_not_supported_error()

        filename_base = _clean_filename(title) if title else "download"
        ext = self.settings.magnet_file_extension.lstrip(".")
        filepath = Path(self.settings.torrent_folder) / f"{filename_base}.{ext}"
        Path(self.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        with Path(filepath).open("w", encoding="utf-8") as f:
            f.write(magnet_url)
        logger.debug("Saved magnet link to: %s", filepath)
        return "magnet_blackhole"

    def add_url(
        self,
        url: str,
        title: str | None,
        _category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        filename_base = _clean_filename(title) if title else "download"
        filepath = Path(self.settings.torrent_folder) / f"{filename_base}.torrent"
        Path(self.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        file_content, _ = self._file_fetcher.fetch_with_filename(
            url, "download.torrent"
        )
        with Path(filepath).open("wb") as f:
            f.write(file_content)
        logger.debug("Downloaded and saved torrent to: %s", filepath)
        return "torrent_blackhole"

    def add_file(
        self,
        filepath: str,
        title: str | None,
        _category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from local file."""
        filename_base = _clean_filename(title) if title else "download"
        dest_filepath = Path(self.settings.torrent_folder) / f"{filename_base}.torrent"
        Path(self.settings.torrent_folder).mkdir(parents=True, exist_ok=True)
        with (
            Path(filepath).open("rb") as src,
            Path(dest_filepath).open("wb") as dst,
        ):
            dst.write(src.read())
        logger.debug("Copied torrent file to: %s", dest_filepath)
        return "torrent_blackhole"

    def test_connection(self) -> bool:
        """Test connectivity (check if directories are writable).

        Returns
        -------
        bool
            True if directories are accessible.

        Raises
        ------
        PVRProviderError
            If directories are not accessible.
        """
        try:
            # Check if torrent folder is writable
            test_file = Path(self.settings.torrent_folder) / ".test_write"
            try:
                with Path(test_file).open("w") as f:
                    f.write("test")
                Path(test_file).unlink()
            except Exception as e:
                msg = f"Torrent folder is not writable: {e}"
                raise PVRProviderError(msg) from e

            # Check watch folder exists
            if not Path(self.settings.watch_folder).is_dir():
                self._raise_watch_folder_error(self.settings.watch_folder)
        except Exception as e:
            msg = f"Failed to test torrent blackhole connection: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True


class UsenetBlackholeClient(BaseDownloadClient):
    """Usenet blackhole download client.

    Writes .nzb files to a directory where they are picked up by an
    external usenet client.
    """

    def __init__(
        self,
        settings: UsenetBlackholeSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize usenet blackhole client.

        Parameters
        ----------
        settings : UsenetBlackholeSettings | DownloadClientSettings
            Client settings.
        file_fetcher : FileFetcherProtocol
            File fetcher service.
        url_router : UrlRouterProtocol
            URL router service.
        http_client_factory : Callable[[], HttpClientProtocol] | None
            HTTP client factory.
        enabled : bool
            Whether this client is enabled.
        """
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, UsenetBlackholeSettings
        ):
            # Convert to UsenetBlackholeSettings
            usenet_settings = UsenetBlackholeSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                watch_folder=settings.download_path or tempfile.gettempdir(),
                nzb_folder=settings.download_path or tempfile.gettempdir(),
            )
            settings = usenet_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: UsenetBlackholeSettings = settings

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Usenet Blackhole"

    def _raise_unsupported_url_error(self, download_url: str) -> NoReturn:
        """Raise error for unsupported download URL type.

        Parameters
        ----------
        download_url : str
            Unsupported download URL.

        Raises
        ------
        PVRProviderError
            Always raises with error message.
        """
        msg = f"Unsupported download URL type: {download_url[:50]}"
        raise PVRProviderError(msg)

    def _raise_watch_folder_error(self, watch_folder: str) -> None:
        """Raise error for missing watch folder.

        Parameters
        ----------
        watch_folder : str
            Watch folder path.

        Raises
        ------
        PVRProviderError
            Always raises with error message.
        """
        msg = f"Watch folder does not exist: {watch_folder}"
        raise PVRProviderError(msg)

    def add_file(
        self,
        filepath: str,
        title: str | None = None,
        _category: str | None = None,
        _download_path: str | None = None,
    ) -> str:
        """Add download from local file."""
        # Determine filename
        filename_base = _clean_filename(title) if title else "download"

        # Ensure nzb folder exists
        Path(self.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        dest_filepath = Path(self.settings.nzb_folder) / f"{filename_base}.nzb"

        with (
            Path(filepath).open("rb") as src,
            Path(dest_filepath).open("wb") as dst,
        ):
            dst.write(src.read())
        logger.debug("Copied NZB file to: %s", dest_filepath)
        return "nzb_blackhole"

    def add_url(
        self,
        url: str,
        title: str | None = None,
        _category: str | None = None,
        _download_path: str | None = None,
    ) -> str:
        """Add download from URL."""
        # Determine filename
        filename_base = _clean_filename(title) if title else "download"

        # Ensure nzb folder exists
        Path(self.settings.nzb_folder).mkdir(parents=True, exist_ok=True)

        filepath = Path(self.settings.nzb_folder) / f"{filename_base}.nzb"

        # Use file_fetcher instead of creating new httpx client
        content = self._file_fetcher.fetch_content(url)

        with Path(filepath).open("wb") as f:
            f.write(content)
        logger.debug("Downloaded and saved NZB to: %s", filepath)
        return "nzb_blackhole"

    def test_connection(self) -> bool:
        """Test connectivity (check if directories are writable).

        Returns
        -------
        bool
            True if directories are accessible.

        Raises
        ------
        PVRProviderError
            If directories are not accessible.
        """
        try:
            # Check if NZB folder is writable
            test_file = Path(self.settings.nzb_folder) / ".test_write"
            try:
                with Path(test_file).open("w") as f:
                    f.write("test")
                Path(test_file).unlink()
            except Exception as e:
                msg = f"NZB folder is not writable: {e}"
                raise PVRProviderError(msg) from e

            # Check watch folder exists
            if not Path(self.settings.watch_folder).is_dir():
                self._raise_watch_folder_error(self.settings.watch_folder)
        except Exception as e:
            msg = f"Failed to test usenet blackhole connection: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

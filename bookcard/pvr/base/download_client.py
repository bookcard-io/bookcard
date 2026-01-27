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

"""Base classes for PVR download clients."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.base.settings import DownloadClientSettings
from bookcard.pvr.base.strategies import DownloadStrategyRegistry
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import DownloadItem


class BaseDownloadClient(ABC):
    """Abstract base class for download clients.

    This class defines the interface that all download client implementations
    must implement. Download clients handle actual downloads of torrents or
    usenet files.

    Subclasses should implement:
    - `add_download()`: Add a download to the client (handled by strategy)
    - `test_connection()`: Test connectivity to the client
    - Capability methods (add_magnet, add_url, add_file) if supported

    Attributes
    ----------
    enabled : bool
        Whether this download client is currently enabled.
    settings : DownloadClientSettings
        Download client configuration settings.
    _file_fetcher : FileFetcherProtocol
        File fetcher service for downloading files from URLs.
    _url_router : UrlRouterProtocol
        URL routing service.
    _http_client_factory : Callable[[], HttpClientProtocol] | None
        Factory for creating configured HTTP clients (optional).
    """

    def __init__(
        self,
        settings: DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize the download client.

        Parameters
        ----------
        settings : DownloadClientSettings
            Download client configuration settings.
        file_fetcher : FileFetcherProtocol
            File fetcher service.
        url_router : UrlRouterProtocol
            URL routing service.
        http_client_factory : Callable[[], HttpClientProtocol] | None
            Factory for creating configured HTTP clients.
        enabled : bool
            Whether this client is enabled by default.
        """
        self.settings = settings
        self.enabled = enabled
        self._file_fetcher = file_fetcher
        self._url_router = url_router
        self._http_client_factory = http_client_factory

        # Initialize strategy registry
        self._strategy_registry = DownloadStrategyRegistry(self._url_router)

    @property
    @abstractmethod
    def client_name(self) -> str:
        """Return client name for error messages.

        Returns
        -------
        str
            Client name (e.g., "qBittorrent", "Transmission").
        """
        raise NotImplementedError

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """Add a download to the client.

        Uses strategy pattern to delegate to client-specific implementations
        based on capability protocols.

        Parameters
        ----------
        download_url : str
            URL, magnet link, or file path for the download.
        title : str | None
            Optional title for the download.
        category : str | None
            Optional category/tag to assign.
        download_path : str | None
            Optional custom download path.
        **kwargs : Any
            Additional metadata/options.

        Returns
        -------
        str
            Client-specific item ID for the added download.

        Raises
        ------
        PVRProviderError
            If adding the download fails, client is disabled, or capability not supported.
        """
        self._ensure_enabled()

        try:
            resolved_category = category or self.settings.category
            resolved_path = download_path or self.settings.download_path

            return self._strategy_registry.handle(
                self, download_url, title, resolved_category, resolved_path, **kwargs
            )

        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Failed to add download to {self.client_name}: {e}"
            raise PVRProviderError(msg) from e

    def _ensure_enabled(self) -> None:
        """Ensure client is enabled.

        Raises
        ------
        PVRProviderError
            If client is disabled.
        """
        if not self.is_enabled():
            msg = f"{self.client_name} client is disabled"
            raise PVRProviderError(msg)

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connectivity to the download client.

        Returns
        -------
        bool
            True if connection test succeeds, False otherwise.

        Raises
        ------
        PVRProviderError
            If the connection test fails with a specific error.
        """
        raise NotImplementedError

    def is_enabled(self) -> bool:
        """Check if this download client is enabled.

        Returns
        -------
        bool
            True if client is enabled, False otherwise.
        """
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this download client.

        Parameters
        ----------
        enabled : bool
            Whether to enable the client.
        """
        self.enabled = enabled


class TrackingDownloadClient(BaseDownloadClient):
    """Base class for download clients that support tracking.

    Adds methods for getting items and removing items.
    """

    @abstractmethod
    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads.

        Returns
        -------
        Sequence[DownloadItem]
            Sequence of download items.

        Raises
        ------
        PVRProviderError
            If fetching items fails.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from the client.

        Parameters
        ----------
        client_item_id : str
            Client-specific item ID.
        delete_files : bool
            Whether to delete downloaded files (default: False).

        Returns
        -------
        bool
            True if removal succeeded, False otherwise.

        Raises
        ------
        PVRProviderError
            If removal fails.
        """
        raise NotImplementedError

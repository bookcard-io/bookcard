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

"""Abstract base classes for PVR indexers and download clients."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from pydantic import BaseModel, Field

# Import capabilities from _base directory
from bookcard.pvr._base.capabilities import FileSupport, MagnetSupport, UrlSupport
from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.base.strategies import DownloadStrategyRegistry
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import DownloadItem, ReleaseInfo


class IndexerSettings(BaseModel):
    """Base settings class for indexers.

    This is a base class that specific indexer implementations should extend
    with their own settings fields.

    Attributes
    ----------
    base_url : str
        Base URL of the indexer API.
    api_key : str | None
        API key for authentication.
    timeout_seconds : int
        Request timeout in seconds (default: 30).
    retry_count : int
        Number of retries on failure (default: 3).
    categories : list[int] | None
        List of category IDs to search (None = all categories).
    """

    base_url: str = Field(..., description="Base URL of the indexer API")
    api_key: str | None = Field(default=None, description="API key for authentication")
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    retry_count: int = Field(
        default=3, ge=0, le=10, description="Number of retries on failure"
    )
    categories: list[int] | None = Field(
        default=None,
        description="List of category IDs to search (None = all categories)",
    )


class DownloadClientSettings(BaseModel):
    """Base settings class for download clients.

    This is a base class that specific download client implementations should
    extend with their own settings fields.

    Attributes
    ----------
    host : str
        Hostname or IP address of the client.
    port : int
        Port number for the client API.
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication.
    use_ssl : bool
        Whether to use SSL/TLS (default: False).
    timeout_seconds : int
        Request timeout in seconds (default: 30).
    category : str | None
        Category/tag to assign to downloads.
    download_path : str | None
        Path where client should save downloads.
    """

    host: str = Field(..., description="Hostname or IP address of the client")
    port: int = Field(..., ge=1, le=65535, description="Port number for the client API")
    username: str | None = Field(
        default=None, description="Username for authentication"
    )
    password: str | None = Field(
        default=None, description="Password for authentication"
    )
    use_ssl: bool = Field(default=False, description="Whether to use SSL/TLS")
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    category: str | None = Field(
        default=None, description="Category/tag to assign to downloads"
    )
    download_path: str | None = Field(
        default=None, description="Path where client should save downloads"
    )


class BaseIndexer(ABC):
    """Abstract base class for indexers.

    This class defines the interface that all indexer implementations must
    implement. Indexers can search for books via torrent or usenet sources.

    Subclasses should implement:
    - `search()`: Search for releases matching a query
    - `test_connection()`: Test connectivity to the indexer

    Attributes
    ----------
    settings : IndexerSettings
        Indexer configuration settings.
    """

    def __init__(self, settings: IndexerSettings) -> None:
        """Initialize the indexer.

        Parameters
        ----------
        settings : IndexerSettings
            Indexer configuration settings.
        """
        self.settings = settings

    @abstractmethod
    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases matching the query.

        Parameters
        ----------
        query : str
            General search query (title, author, etc.).
        title : str | None
            Optional specific title to search for.
        author : str | None
            Optional specific author to search for.
        isbn : str | None
            Optional ISBN to search for.
        max_results : int
            Maximum number of results to return (default: 100).

        Returns
        -------
        Sequence[ReleaseInfo]
            Sequence of release information matching the query.

        Raises
        ------
        PVRProviderError
            If the search fails due to network, parsing, or other errors.
        """
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connectivity to the indexer.

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


class ManagedIndexer:
    """Wrapper for indexers that handles state management.

    Follows SRP by separating state (enabled/disabled) from indexer logic.
    """

    def __init__(self, indexer: BaseIndexer, enabled: bool = True) -> None:
        """Initialize managed indexer.

        Parameters
        ----------
        indexer : BaseIndexer
            The underlying indexer implementation.
        enabled : bool
            Whether this indexer is enabled.
        """
        self._indexer = indexer
        self._enabled = enabled

    @property
    def settings(self) -> IndexerSettings:
        """Get underlying indexer settings."""
        return self._indexer.settings

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases if enabled.

        Returns empty sequence if disabled.
        """
        if not self._enabled:
            return []
        return self._indexer.search(query, title, author, isbn, max_results)

    def test_connection(self) -> bool:
        """Test connectivity (delegates to indexer)."""
        return self._indexer.test_connection()

    def is_enabled(self) -> bool:
        """Check if indexer is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state."""
        self._enabled = enabled


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


__all__ = [
    "BaseDownloadClient",
    "BaseIndexer",
    "DownloadClientSettings",
    "FileSupport",
    "IndexerSettings",
    "MagnetSupport",
    "ManagedIndexer",
    "TrackingDownloadClient",
    "UrlSupport",
]

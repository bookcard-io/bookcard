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
from collections.abc import Sequence

from pydantic import BaseModel, Field

from bookcard.pvr.models import ReleaseInfo


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
    - Optionally override `is_enabled()` for conditional activation

    Attributes
    ----------
    enabled : bool
        Whether this indexer is currently enabled.
    settings : IndexerSettings
        Indexer configuration settings.
    """

    def __init__(self, settings: IndexerSettings, enabled: bool = True) -> None:
        """Initialize the indexer.

        Parameters
        ----------
        settings : IndexerSettings
            Indexer configuration settings.
        enabled : bool
            Whether this indexer is enabled by default.
        """
        self.settings = settings
        self.enabled = enabled

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
            Returns empty sequence if no results or if indexer is disabled.

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

    def is_enabled(self) -> bool:
        """Check if this indexer is enabled.

        Returns
        -------
        bool
            True if indexer is enabled, False otherwise.
        """
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this indexer.

        Parameters
        ----------
        enabled : bool
            Whether to enable the indexer.
        """
        self.enabled = enabled


class BaseDownloadClient(ABC):
    """Abstract base class for download clients.

    This class defines the interface that all download client implementations
    must implement. Download clients handle actual downloads of torrents or
    usenet files.

    Subclasses should implement:
    - `add_download()`: Add a download to the client
    - `get_items()`: Get list of active downloads
    - `remove_item()`: Remove a download from the client
    - `test_connection()`: Test connectivity to the client

    Attributes
    ----------
    enabled : bool
        Whether this download client is currently enabled.
    settings : DownloadClientSettings
        Download client configuration settings.
    """

    def __init__(self, settings: DownloadClientSettings, enabled: bool = True) -> None:
        """Initialize the download client.

        Parameters
        ----------
        settings : DownloadClientSettings
            Download client configuration settings.
        enabled : bool
            Whether this client is enabled by default.
        """
        self.settings = settings
        self.enabled = enabled

    @abstractmethod
    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add a download to the client.

        Parameters
        ----------
        download_url : str
            URL or magnet link for the download.
        title : str | None
            Optional title for the download.
        category : str | None
            Optional category/tag to assign.
        download_path : str | None
            Optional custom download path.

        Returns
        -------
        str
            Client-specific item ID for the added download.

        Raises
        ------
        PVRProviderError
            If adding the download fails.
        """
        raise NotImplementedError

    @abstractmethod
    def get_items(self) -> Sequence[dict[str, str | int | float | None]]:
        """Get list of active downloads.

        Returns
        -------
        Sequence[dict[str, str | int | float | None]]
            Sequence of download items, each containing:
            - client_item_id: str - Unique identifier in the client
            - title: str - Download title
            - status: str - Current status (downloading, completed, etc.)
            - progress: float - Progress (0.0 to 1.0)
            - size_bytes: int | None - Total size in bytes
            - downloaded_bytes: int | None - Bytes downloaded
            - download_speed_bytes_per_sec: float | None - Current speed
            - eta_seconds: int | None - Estimated time to completion
            - file_path: str | None - Path to downloaded file(s)

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


class PVRProviderError(Exception):
    """Base exception for PVR provider errors."""


class PVRProviderNetworkError(PVRProviderError):
    """Exception raised when network requests fail."""


class PVRProviderParseError(PVRProviderError):
    """Exception raised when parsing response data fails."""


class PVRProviderTimeoutError(PVRProviderError):
    """Exception raised when requests timeout."""


class PVRProviderAuthenticationError(PVRProviderError):
    """Exception raised when authentication fails."""


# Utility functions for raising exceptions
def raise_authentication_error(message: str) -> None:
    """Raise PVRProviderAuthenticationError with message.

    Parameters
    ----------
    message : str
        Error message.

    Raises
    ------
    PVRProviderAuthenticationError
        Always raises this exception.
    """
    raise PVRProviderAuthenticationError(message)


def raise_provider_error(message: str) -> None:
    """Raise PVRProviderError with message.

    Parameters
    ----------
    message : str
        Error message.

    Raises
    ------
    PVRProviderError
        Always raises this exception.
    """
    raise PVRProviderError(message)


def raise_network_error(message: str) -> None:
    """Raise PVRProviderNetworkError with message.

    Parameters
    ----------
    message : str
        Error message.

    Raises
    ------
    PVRProviderNetworkError
        Always raises this exception.
    """
    raise PVRProviderNetworkError(message)


def handle_api_error_response(
    error_code: int, description: str, provider_name: str = "Indexer"
) -> None:
    """Handle API error response and raise appropriate exception.

    Parameters
    ----------
    error_code : int
        Error code from API response.
    description : str
        Error description from API response.
    provider_name : str
        Name of the provider (for error messages).

    Raises
    ------
    PVRProviderAuthenticationError
        If error code is 100-199 (authentication errors).
    PVRProviderError
        For other API errors.
    """
    if 100 <= error_code <= 199:
        error_msg = f"Invalid API key: {description}"
        raise_authentication_error(error_msg)

    if description == "Request limit reached":
        error_msg = f"API limit reached: {description}"
        raise_provider_error(error_msg)

    error_msg = f"{provider_name} error: {description}"
    raise_provider_error(error_msg)


def handle_http_error_response(status_code: int, response_text: str = "") -> None:
    """Handle HTTP error response and raise appropriate exception.

    Parameters
    ----------
    status_code : int
        HTTP status code.
    response_text : str
        Response text (truncated to 200 chars).

    Raises
    ------
    PVRProviderAuthenticationError
        If status code is 401 or 403.
    PVRProviderNetworkError
        For other HTTP errors (>= 400).
    """
    if status_code == 401:
        raise_authentication_error("Unauthorized")
    if status_code == 403:
        raise_authentication_error("Forbidden")
    if status_code >= 400:
        error_msg = f"HTTP {status_code}: {response_text[:200]}"
        raise_network_error(error_msg)

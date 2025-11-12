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

"""Abstract base classes for metadata providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo


class MetadataProvider(ABC):
    """Abstract base class for metadata providers.

    This class defines the interface that all metadata providers must implement.
    Providers can fetch data from clean APIs, scrape HTML/XML, or use any other
    method. The abstraction makes no assumptions about the data source format.

    Subclasses should implement:
    - `get_source_info()`: Return information about the provider
    - `search()`: Search for books by query string
    - Optionally override `is_enabled()` for conditional activation

    Attributes
    ----------
    enabled : bool
        Whether this provider is currently enabled.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the metadata provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled by default.
        """
        self.enabled = enabled

    @abstractmethod
    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about this metadata source.

        Returns
        -------
        MetadataSourceInfo
            Source information including ID, name, description, and base URL.
        """

    @abstractmethod
    def search(
        self,
        query: str,
        locale: str = "en",
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books matching the query.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code for localized results (default: 'en').
        max_results : int
            Maximum number of results to return (default: 10).

        Returns
        -------
        Sequence[MetadataRecord]
            Sequence of metadata records matching the query.
            Returns empty sequence if no results or if provider is disabled.

        Raises
        ------
        MetadataProviderError
            If the search fails due to network, parsing, or other errors.
        """

    def is_enabled(self) -> bool:
        """Check if this provider is enabled.

        Returns
        -------
        bool
            True if provider is enabled, False otherwise.
        """
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this provider.

        Parameters
        ----------
        enabled : bool
            Whether to enable the provider.
        """
        self.enabled = enabled


class MetadataProviderError(Exception):
    """Base exception for metadata provider errors."""


class MetadataProviderNetworkError(MetadataProviderError):
    """Exception raised when network requests fail."""


class MetadataProviderParseError(MetadataProviderError):
    """Exception raised when parsing response data fails."""


class MetadataProviderTimeoutError(MetadataProviderError):
    """Exception raised when requests timeout."""

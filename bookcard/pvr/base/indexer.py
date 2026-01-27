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

"""Base classes for PVR indexers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from bookcard.pvr.base.settings import IndexerSettings
from bookcard.pvr.models import ReleaseInfo


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

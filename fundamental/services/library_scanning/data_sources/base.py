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

"""Base data source abstraction for external metadata providers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)


class DataSourceError(Exception):
    """Base exception for data source errors."""


class DataSourceNetworkError(DataSourceError):
    """Exception raised when network requests fail."""


class DataSourceRateLimitError(DataSourceError):
    """Exception raised when rate limit is exceeded."""


class DataSourceNotFoundError(DataSourceError):
    """Exception raised when requested entity is not found."""


class BaseDataSource(ABC):
    """Abstract base class for external data sources.

    Provides a unified interface for fetching author and book metadata
    from external sources (OpenLibrary, Goodreads, etc.). Handles rate
    limiting, error handling, and retries.

    Subclasses should implement:
    - `search_author()`: Search for authors by name and identifiers
    - `get_author()`: Get full author details by key
    - `get_author_works()`: Get work keys for an author
    - `search_book()`: Search for books by title, ISBN, authors
    - `get_book()`: Get full book details by key
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this data source.

        Returns
        -------
        str
            Data source name (e.g., "OpenLibrary").
        """
        raise NotImplementedError

    @abstractmethod
    def search_author(
        self,
        name: str,
        identifiers: IdentifierDict | None = None,
    ) -> Sequence[AuthorData]:
        """Search for authors by name and optional identifiers.

        Parameters
        ----------
        name : str
            Author name to search for.
        identifiers : IdentifierDict | None
            Optional external identifiers (VIAF, Goodreads, etc.).

        Returns
        -------
        Sequence[AuthorData]
            Sequence of matching author data. Empty if no matches.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        raise NotImplementedError

    @abstractmethod
    def get_author(self, key: str) -> AuthorData | None:
        """Get full author details by key.

        Parameters
        ----------
        key : str
            Author key/identifier from the data source.

        Returns
        -------
        AuthorData | None
            Full author data if found, None otherwise.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        DataSourceNotFoundError
            If author is not found.
        """
        raise NotImplementedError

    @abstractmethod
    def get_author_works(
        self,
        author_key: str,
        limit: int | None = None,
        lang: str = "eng",
    ) -> Sequence[str]:
        """Get work keys for an author.

        Parameters
        ----------
        author_key : str
            Author key/identifier from the data source.
        limit : int | None
            Maximum number of work keys to return (None = fetch all).
        lang : str
            Language code to filter works (default: "eng").

        Returns
        -------
        Sequence[str]
            Sequence of work keys. Empty if no works found.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        raise NotImplementedError

    @abstractmethod
    def search_book(
        self,
        title: str | None = None,
        isbn: str | None = None,
        authors: Sequence[str] | None = None,
    ) -> Sequence[BookData]:
        """Search for books by title, ISBN, or authors.

        Parameters
        ----------
        title : str | None
            Book title to search for.
        isbn : str | None
            ISBN identifier.
        authors : Sequence[str] | None
            Author names.

        Returns
        -------
        Sequence[BookData]
            Sequence of matching book data. Empty if no matches.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        raise NotImplementedError

    @abstractmethod
    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:
        """Get full book details by key.

        Parameters
        ----------
        key : str
            Book key/identifier from the data source.
        skip_authors : bool
            If True, skip fetching author data (faster, useful when only subjects are needed).

        Returns
        -------
        BookData | None
            Full book data if found, None otherwise.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        DataSourceNotFoundError
            If book is not found.
        """
        raise NotImplementedError

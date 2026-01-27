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

"""Author lookup strategies following Strategy pattern.

Allows extensible lookup mechanisms for different author ID formats.
"""

from abc import ABC, abstractmethod

from bookcard.models.author_metadata import AuthorMetadata
from bookcard.repositories.author_repository import AuthorRepository


class AuthorLookupStrategy(ABC):
    """Base class for author lookup strategies."""

    @abstractmethod
    def can_handle(self, author_id: str) -> bool:
        """Check if this strategy can handle the given author ID.

        Parameters
        ----------
        author_id : str
            Author identifier string.

        Returns
        -------
        bool
            True if this strategy can handle the ID, False otherwise.
        """

    @abstractmethod
    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author using this strategy.

        Parameters
        ----------
        author_id : str
            Author identifier string.
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """


class CalibreLookupStrategy(AuthorLookupStrategy):
    """Strategy for looking up authors by Calibre ID (calibre-{id} format)."""

    def can_handle(self, author_id: str) -> bool:
        """Check if this is a calibre- prefixed ID.

        Parameters
        ----------
        author_id : str
            Author identifier string.

        Returns
        -------
        bool
            True if ID starts with "calibre-", False otherwise.
        """
        return author_id.startswith("calibre-")

    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author by Calibre ID.

        Parameters
        ----------
        author_id : str
            Author identifier string (calibre-{id} format).
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        try:
            calibre_id = int(author_id.replace("calibre-", ""))
            return repo.get_by_calibre_id_and_library(calibre_id, library_id)
        except ValueError:
            return None


class LocalLookupStrategy(AuthorLookupStrategy):
    """Strategy for looking up authors by local ID (local-{id} format)."""

    def can_handle(self, author_id: str) -> bool:
        """Check if this is a local- prefixed ID.

        Parameters
        ----------
        author_id : str
            Author identifier string.

        Returns
        -------
        bool
            True if ID starts with "local-", False otherwise.
        """
        return author_id.startswith("local-")

    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author by local metadata ID.

        Parameters
        ----------
        author_id : str
            Author identifier string (local-{id} format).
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        try:
            metadata_id = int(author_id.replace("local-", ""))
            return repo.get_by_id_and_library(metadata_id, library_id)
        except ValueError:
            return None


class NumericLookupStrategy(AuthorLookupStrategy):
    """Strategy for looking up authors by numeric ID."""

    def can_handle(self, author_id: str) -> bool:
        """Check if this is a numeric ID.

        Parameters
        ----------
        author_id : str
            Author identifier string.

        Returns
        -------
        bool
            True if ID is numeric, False otherwise.
        """
        try:
            int(author_id)
        except ValueError:
            return False
        else:
            return True

    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author by numeric metadata ID.

        Parameters
        ----------
        author_id : str
            Author identifier string (numeric).
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        try:
            author_metadata_id = int(author_id)
            return repo.get_by_id_and_library(author_metadata_id, library_id)
        except ValueError:
            return None


class OpenLibraryLookupStrategy(AuthorLookupStrategy):
    """Strategy for looking up authors by OpenLibrary key."""

    def can_handle(self, author_id: str) -> bool:
        """Return True as fallback strategy.

        This strategy always returns True and is used as a fallback
        when no other strategy can handle the author_id format.

        Parameters
        ----------
        author_id : str
            Author identifier string (unused, but required by interface).

        Returns
        -------
        bool
            Always True (used as fallback).
        """
        del author_id
        return True

    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author by OpenLibrary key.

        Parameters
        ----------
        author_id : str
            Author identifier string (OpenLibrary key).
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        return repo.get_by_openlibrary_key_and_library(author_id, library_id)


class AuthorLookupStrategyChain:
    """Chain of responsibility for author lookup strategies."""

    def __init__(self) -> None:
        """Initialize strategy chain with default strategies."""
        self._strategies: list[AuthorLookupStrategy] = [
            CalibreLookupStrategy(),
            LocalLookupStrategy(),
            NumericLookupStrategy(),
            OpenLibraryLookupStrategy(),  # Fallback
        ]

    def lookup(
        self, author_id: str, library_id: int, repo: AuthorRepository
    ) -> AuthorMetadata | None:
        """Lookup author using strategy chain.

        Parameters
        ----------
        author_id : str
            Author identifier string.
        library_id : int
            Library identifier.
        repo : AuthorRepository
            Author repository for data access.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        for strategy in self._strategies:
            if strategy.can_handle(author_id):
                result = strategy.lookup(author_id, library_id, repo)
                if result is not None:
                    return result
        return None

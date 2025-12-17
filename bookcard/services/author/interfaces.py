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

"""Interfaces for author service components.

Follows Interface Segregation Principle by providing focused interfaces.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from bookcard.models.author_metadata import AuthorMetadata


class PhotoStorageInterface(ABC):
    """Interface for photo storage operations."""

    @abstractmethod
    def save(self, content: bytes, filename: str, author_id: int) -> str:
        """Save photo and return relative path.

        Parameters
        ----------
        content : bytes
            Photo content.
        filename : str
            Original filename.
        author_id : int
            Author metadata ID.

        Returns
        -------
        str
            Relative path to saved photo.

        Raises
        ------
        PhotoStorageError
            If save operation fails.
        """

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete photo at path.

        Parameters
        ----------
        path : str
            Relative path to photo.

        Raises
        ------
        PhotoStorageError
            If delete operation fails.
        """

    @abstractmethod
    def get_full_path(self, relative_path: str) -> Path:
        """Get full path from relative path.

        Parameters
        ----------
        relative_path : str
            Relative path to photo.

        Returns
        -------
        Path
            Full path to photo.
        """


class DataFetcherInterface(ABC):
    """Interface for fetching author metadata from external sources."""

    @abstractmethod
    def fetch_author_metadata(self, author_key: str) -> dict[str, object]:
        """Fetch author metadata from external source.

        Parameters
        ----------
        author_key : str
            Author identifier (e.g., OpenLibrary key).

        Returns
        -------
        dict[str, object]
            Author metadata dictionary.

        Raises
        ------
        AuthorMetadataFetchError
            If fetch operation fails.
        """


class AuthorSerializerInterface(ABC):
    """Interface for serializing author data."""

    @abstractmethod
    def to_dict(self, author: AuthorMetadata) -> dict[str, object]:
        """Convert author to dictionary.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata object.

        Returns
        -------
        dict[str, object]
            Author data dictionary.
        """

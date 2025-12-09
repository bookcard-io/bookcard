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

"""Interfaces for read list importers and book matchers.

Defines abstract base classes for implementing read list importers
and book matching services following IOC principles.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field


class BookReference(BaseModel):
    """Reference to a book from an external read list.

    Attributes
    ----------
    series : str | None
        Series name.
    volume : int | float | None
        Volume number.
    issue : int | float | None
        Issue number.
    year : int | None
        Publication year.
    title : str | None
        Book title.
    author : str | None
        Author name.
    """

    series: str | None = Field(default=None, description="Series name")
    volume: int | float | None = Field(default=None, description="Volume number")
    issue: int | float | None = Field(default=None, description="Issue number")
    year: int | None = Field(default=None, description="Publication year")
    title: str | None = Field(default=None, description="Book title")
    author: str | None = Field(default=None, description="Author name")


class ReadListData(BaseModel):
    """Parsed read list data from an external source.

    Attributes
    ----------
    name : str
        Read list name.
    description : str | None
        Optional description.
    books : list[BookReference]
        List of book references in order.
    """

    name: str = Field(description="Read list name")
    description: str | None = Field(default=None, description="Optional description")
    books: list[BookReference] = Field(
        default_factory=list,
        description="List of book references in order",
    )


class BookMatchResult(BaseModel):
    """Result of matching a book reference to a library book.

    Attributes
    ----------
    reference : BookReference
        Original book reference.
    book_id : int | None
        Matched book ID, or None if no match found.
    confidence : float
        Match confidence score (0.0 to 1.0).
    match_type : str
        Type of match: 'exact', 'fuzzy', 'title', or 'none'.
    """

    reference: BookReference = Field(description="Original book reference")
    book_id: int | None = Field(default=None, description="Matched book ID")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Match confidence score (0.0 to 1.0)",
    )
    match_type: str = Field(
        description="Type of match: 'exact', 'fuzzy', 'title', or 'none'",
    )


class ReadListImporter(ABC):
    """Abstract base class for read list importers.

    Implementations should handle parsing specific file formats
    (e.g., ComicRack .cbl, JSON, XML).
    """

    @abstractmethod
    def can_import(self, file_path: Path) -> bool:
        """Check if this importer can handle the given file.

        Parameters
        ----------
        file_path : Path
            Path to the file to check.

        Returns
        -------
        bool
            True if this importer can handle the file, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, file_path: Path) -> ReadListData:
        """Parse a read list file into ReadListData.

        Parameters
        ----------
        file_path : Path
            Path to the read list file.

        Returns
        -------
        ReadListData
            Parsed read list data.

        Raises
        ------
        ValueError
            If the file cannot be parsed.
        """
        raise NotImplementedError

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the name of the format this importer handles.

        Returns
        -------
        str
            Format name (e.g., "ComicRack .cbl").
        """
        raise NotImplementedError


class BookMatcher(ABC):
    """Abstract base class for book matching services.

    Implementations should match BookReference objects to actual
    books in the library using various strategies.
    """

    @abstractmethod
    def match_books(
        self,
        references: list[BookReference],
        library_id: int,
    ) -> list[BookMatchResult]:
        """Match book references to library books.

        Parameters
        ----------
        references : list[BookReference]
            List of book references to match.
        library_id : int
            Library ID to search within.

        Returns
        -------
        list[BookMatchResult]
            List of match results, one per reference.
        """
        raise NotImplementedError

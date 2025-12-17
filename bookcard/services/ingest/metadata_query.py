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

"""Metadata query dataclass for cleaner interfaces.

Follows ISP by providing a focused query object instead of many parameters.
"""

from dataclasses import dataclass


@dataclass
class MetadataQuery:
    """Query parameters for metadata search.

    Encapsulates all search parameters in a single object,
    following Interface Segregation Principle.

    Attributes
    ----------
    title : str | None
        Book title to search for.
    authors : list[str] | None
        List of author names.
    isbn : str | None
        ISBN identifier.
    locale : str
        Locale code for search (default: 'en').
    max_results_per_provider : int
        Maximum results per provider (default: 10).
    """

    title: str | None = None
    authors: list[str] | None = None
    isbn: str | None = None
    locale: str = "en"
    max_results_per_provider: int = 10

    def build_search_string(self) -> str | None:
        """Build search query string from query parameters.

        Combines title, authors (first 2), and ISBN into a search string.

        Returns
        -------
        str | None
            Search query string, or None if no parameters provided.
        """
        parts: list[str] = []
        if self.title:
            parts.append(self.title)
        if self.authors:
            parts.extend(self.authors[:2])  # Limit to first 2 authors
        if self.isbn:
            parts.append(self.isbn)

        return " ".join(parts) if parts else None

    def is_valid(self) -> bool:
        """Check if query has at least one search parameter.

        Returns
        -------
        bool
            True if query has title, authors, or ISBN.
        """
        return bool(self.title or self.authors or self.isbn)

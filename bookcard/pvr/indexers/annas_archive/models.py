# Copyright (C) 2026 knguyen and others
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

"""Data models for Anna's Archive indexer."""

from dataclasses import dataclass
from typing import Final


class AnnasArchiveTableColumns:
    """Column indices for Anna's Archive search results table."""

    TITLE: Final[int] = 1
    AUTHOR: Final[int] = 2
    PUBLISHER: Final[int] = 3
    YEAR: Final[int] = 4
    LANGUAGE: Final[int] = 7
    FILE_TYPE: Final[int] = 9
    SIZE: Final[int] = 10
    MINIMUM_COLUMNS: Final[int] = 11


@dataclass
class SearchParameters:
    """Search parameters for Anna's Archive."""

    query: str
    index: str = ""
    page: int = 1
    display: str = "table"
    sort: str = "relevance"

    def to_dict(self) -> dict[str, str]:
        """Convert to query parameters."""
        return {
            "q": self.query,
            "index": self.index,
            "page": str(self.page),
            "display": self.display,
            "sort": self.sort,
        }

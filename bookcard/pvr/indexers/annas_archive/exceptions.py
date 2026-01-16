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

"""Exceptions for Anna's Archive indexer."""


class AnnasArchiveError(Exception):
    """Base exception for Anna's Archive operations."""


class AnnasArchiveSearchError(AnnasArchiveError):
    """Error during search operation."""


class AnnasArchiveParsingError(AnnasArchiveError):
    """Error parsing search results."""


class RowParsingError(Exception):
    """Error parsing a table row."""

    def __init__(
        self, message: str, row_html: str | None = None, field: str | None = None
    ) -> None:
        super().__init__(message)
        self.row_html = row_html
        self.field = field

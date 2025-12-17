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

"""Data models for OpenLibrary dump ingestion."""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class DumpRecord:
    """Parsed dump file record.

    Attributes
    ----------
    record_type : str
        Type of the record (e.g., 'author', 'work', 'edition').
    key : str
        OpenLibrary key identifier (e.g., '/authors/OL123456A').
    revision : int | None
        Revision number of the record.
    last_modified : date | None
        Last modification date of the record.
    data : dict[str, Any]
        JSON data containing full record information.
    """

    record_type: str
    key: str
    revision: int | None
    last_modified: date | None
    data: dict[str, Any]

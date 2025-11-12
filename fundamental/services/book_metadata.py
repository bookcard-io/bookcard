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

"""Book metadata data structure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Contributor:
    """Book contributor (author, translator, etc.).

    Attributes
    ----------
    name : str
        Contributor name.
    role : str | None
        Contributor role (e.g., 'author', 'translator', 'editor').
    sort_as : str | None
        Sort name for the contributor.
    """

    name: str
    role: str | None = None
    sort_as: str | None = None


@dataclass
class BookMetadata:
    """Extracted book metadata.

    Attributes
    ----------
    title : str
        Book title.
    subtitle : str | None
        Book subtitle.
    sort_title : str | None
        Sort title for ordering.
    author : str
        Primary author name (or "Unknown" if not found).
        For multiple authors, use contributors list.
    description : str
        Book description/comment.
    tags : list[str]
        List of tags/genres.
    series : str | None
        Series name if part of a series.
    series_index : float | None
        Position in series.
    publisher : str | None
        Publisher name.
    pubdate : datetime | None
        Publication date.
    modified : datetime | None
        Last modification date.
    languages : list[str]
        List of language codes.
    identifiers : list[dict[str, str]]
        List of identifiers with 'type' and 'val' keys.
    contributors : list[Contributor]
        List of contributors with roles (authors, translators, etc.).
    rights : str | None
        Rights information.
    cover_path : Path | None
        Path to extracted cover image (temporary location).
    """

    title: str
    author: str = "Unknown"
    subtitle: str | None = None
    sort_title: str | None = None
    description: str = ""
    tags: list[str] | None = None
    series: str | None = None
    series_index: float | None = None
    publisher: str | None = None
    pubdate: datetime | None = None
    modified: datetime | None = None
    languages: list[str] | None = None
    identifiers: list[dict[str, str]] | None = None
    contributors: list[Contributor] | None = None
    rights: str | None = None
    cover_path: Path | None = None

    def __post_init__(self) -> None:
        """Normalize metadata after initialization."""
        if self.tags is None:
            self.tags = []
        if self.languages is None:
            self.languages = []
        if self.identifiers is None:
            self.identifiers = []
        if self.contributors is None:
            self.contributors = []

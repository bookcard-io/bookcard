# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

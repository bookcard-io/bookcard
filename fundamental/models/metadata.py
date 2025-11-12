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

"""Data models for metadata fetching from external sources."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MetadataSourceInfo(BaseModel):
    """Information about a metadata source provider.

    Attributes
    ----------
    id : str
        Unique identifier for the source (e.g., 'google', 'amazon').
    name : str
        Human-readable name of the source.
    description : str
        Description of the source.
    base_url : str
        Base URL of the source website/API.
    """

    id: str
    name: str
    description: str
    base_url: str


class MetadataRecord(BaseModel):
    """A single metadata record from an external source.

    This represents book metadata fetched from various sources (APIs, HTML, XML, etc.).
    The structure is designed to be flexible and accommodate different source formats.

    Attributes
    ----------
    source_id : str
        Identifier of the source provider.
    external_id : str | int
        Unique identifier for this record in the external source.
    title : str
        Book title.
    authors : list[str]
        List of author names.
    url : str
        URL to the book page on the source website.
    cover_url : str | None
        URL to the book cover image.
    description : str | None
        Book description/synopsis.
    series : str | None
        Series name if part of a series.
    series_index : float | None
        Position in series (1.0 = first book).
    identifiers : dict[str, str]
        Dictionary of identifiers (e.g., {'isbn': '9781234567890', 'asin': 'B00ABC123'}).
    publisher : str | None
        Publisher name.
    published_date : str | None
        Publication date (format varies by source).
    rating : float | None
        Average rating (typically 0-5 scale).
    languages : list[str]
        List of language codes or names.
    tags : list[str]
        List of tags/categories/genres.
    """

    source_id: str
    external_id: str | int
    title: str
    authors: list[str] = Field(default_factory=list)
    url: str
    cover_url: str | None = None
    description: str | None = None
    series: str | None = None
    series_index: float | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    publisher: str | None = None
    published_date: str | None = None
    rating: float | None = None
    languages: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

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

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

"""PVR data models for search results and release information."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReleaseInfo(BaseModel):
    """Release information from indexer search results.

    Represents a single release (torrent/usenet file) found by an indexer
    that matches a search query. Contains metadata about the release and
    download information.

    Attributes
    ----------
    indexer_id : int | None
        ID of the indexer that provided this release (None if not from database).
    title : str
        Release title/name.
    download_url : str
        URL or magnet link for downloading the release.
    size_bytes : int | None
        Size of the release in bytes.
    publish_date : datetime | None
        Date when the release was published.
    seeders : int | None
        Number of seeders (for torrents, None for usenet).
    leechers : int | None
        Number of leechers (for torrents, None for usenet).
    quality : str | None
        Quality/format indicator (e.g., 'epub', 'pdf', 'mobi').
    author : str | None
        Author name if available in release metadata.
    isbn : str | None
        ISBN if available in release metadata.
    description : str | None
        Release description/details.
    category : str | None
        Category name or ID.
    additional_info : dict[str, str | int | float | None] | None
        Additional indexer-specific metadata.
    """

    indexer_id: int | None = Field(
        default=None, description="ID of the indexer that provided this release"
    )
    title: str = Field(..., description="Release title/name")
    download_url: str = Field(..., description="URL or magnet link for downloading")
    size_bytes: int | None = Field(
        default=None, description="Size of the release in bytes"
    )
    publish_date: datetime | None = Field(
        default=None, description="Date when the release was published"
    )
    seeders: int | None = Field(
        default=None, ge=0, description="Number of seeders (for torrents)"
    )
    leechers: int | None = Field(
        default=None, ge=0, description="Number of leechers (for torrents)"
    )
    quality: str | None = Field(
        default=None, description="Quality/format indicator (e.g., 'epub', 'pdf')"
    )
    author: str | None = Field(default=None, description="Author name if available")
    isbn: str | None = Field(default=None, description="ISBN if available")
    description: str | None = Field(
        default=None, description="Release description/details"
    )
    category: str | None = Field(default=None, description="Category name or ID")
    additional_info: dict[str, str | int | float | None] | None = Field(
        default=None, description="Additional indexer-specific metadata"
    )

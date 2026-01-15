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

"""API schemas for PVR interactive search endpoints.

Pydantic models for request/response validation for interactive search operations.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from bookcard.pvr.models import ReleaseInfo


class PVRSearchRequest(BaseModel):
    """Request schema for manual search for a tracked book.

    Attributes
    ----------
    tracked_book_id : int
        ID of the tracked book to search for.
    indexer_ids : list[int] | None
        Optional list of specific indexer IDs to search. If None, searches all enabled indexers.
    max_results_per_indexer : int
        Maximum results per indexer (default: 100).
    """

    tracked_book_id: int = Field(
        ..., description="ID of the tracked book to search for"
    )
    indexer_ids: list[int] | None = Field(
        default=None, description="Optional list of specific indexer IDs to search"
    )
    max_results_per_indexer: int = Field(
        default=100, ge=1, le=1000, description="Maximum results per indexer"
    )


class PVRSearchResponse(BaseModel):
    """Response schema for search initiation.

    Attributes
    ----------
    tracked_book_id : int
        ID of the tracked book that was searched.
    search_initiated : bool
        Whether the search was successfully initiated.
    message : str
        Status message.
    """

    tracked_book_id: int = Field(..., description="ID of the tracked book")
    search_initiated: bool = Field(..., description="Whether search was initiated")
    message: str = Field(..., description="Status message")


class ReleaseInfoRead(BaseModel):
    """Response schema for release information.

    Attributes
    ----------
    indexer_id : int | None
        ID of the indexer that provided this release.
    title : str
        Release title/name.
    download_url : str
        URL or magnet link for downloading.
    size_bytes : int | None
        Size of the release in bytes.
    publish_date : datetime | None
        Date when the release was published.
    seeders : int | None
        Number of seeders (for torrents).
    leechers : int | None
        Number of leechers (for torrents).
    quality : str | None
        Quality/format indicator (e.g., 'epub', 'pdf').
    author : str | None
        Author name if available.
    isbn : str | None
        ISBN if available.
    description : str | None
        Release description/details.
    category : str | None
        Category name or ID.
    additional_info : dict[str, str | int | float | None] | None
        Additional indexer-specific metadata.
    """

    indexer_id: int | None = None
    title: str
    download_url: str
    size_bytes: int | None = None
    publish_date: datetime | None = None
    seeders: int | None = None
    leechers: int | None = None
    quality: str | None = None
    author: str | None = None
    isbn: str | None = None
    description: str | None = None
    category: str | None = None
    additional_info: dict[str, str | int | float | None] | None = None
    language: str | None = None
    guid: str | None = None
    warning: str | None = None

    @classmethod
    def from_release_info(cls, release: "ReleaseInfo") -> "ReleaseInfoRead":
        """Create ReleaseInfoRead from ReleaseInfo.

        Parameters
        ----------
        release : ReleaseInfo
            Release info to convert.

        Returns
        -------
        ReleaseInfoRead
            Converted release info.
        """
        return cls(
            indexer_id=release.indexer_id,
            title=release.title,
            download_url=release.download_url,
            size_bytes=release.size_bytes,
            publish_date=release.publish_date,
            seeders=release.seeders,
            leechers=release.leechers,
            quality=release.quality,
            author=release.author,
            isbn=release.isbn,
            description=release.description,
            category=release.category,
            additional_info=release.additional_info,
            language=release.language,
            guid=release.guid,
            warning=release.warning,
        )


class SearchResultRead(BaseModel):
    """Response schema for a single search result.

    Attributes
    ----------
    release : ReleaseInfoRead
        The release information.
    score : float
        Quality/relevance score (0.0-1.0, higher is better).
    indexer_name : str | None
        Name of the indexer that provided this result.
    indexer_priority : int
        Priority of the indexer (lower = higher priority).
    """

    release: ReleaseInfoRead
    score: float = Field(..., ge=0.0, le=1.0, description="Quality/relevance score")
    indexer_name: str | None = Field(default=None, description="Indexer name")
    indexer_priority: int = Field(default=0, description="Indexer priority")
    indexer_protocol: str | None = Field(
        default=None, description="Indexer protocol (torrent/usenet)"
    )
    download_status: str | None = Field(
        default=None, description="Current download status if already downloaded"
    )
    download_item_id: int | None = Field(
        default=None, description="ID of the download item if already downloaded"
    )


class PVRSearchResultsResponse(BaseModel):
    """Response schema for search results.

    Attributes
    ----------
    tracked_book_id : int
        ID of the tracked book.
    results : list[SearchResultRead]
        List of search results, sorted by score (highest first).
    total : int
        Total number of results.
    """

    tracked_book_id: int = Field(..., description="ID of the tracked book")
    results: list[SearchResultRead] = Field(..., description="List of search results")
    total: int = Field(..., description="Total number of results")


class PVRDownloadRequest(BaseModel):
    """Request schema for triggering download of a release.

    Attributes
    ----------
    release_index : int
        Index of the release in the search results (0-based).
    download_client_id : int | None
        Optional specific download client ID to use. If None, selects automatically.
    """

    release_index: int = Field(
        ..., ge=0, description="Index of the release in search results (0-based)"
    )
    download_client_id: int | None = Field(
        default=None, description="Optional specific download client ID"
    )


class PVRDownloadResponse(BaseModel):
    """Response schema for download initiation.

    Attributes
    ----------
    tracked_book_id : int
        ID of the tracked book.
    download_item_id : int
        ID of the created download item.
    release_title : str
        Title of the release being downloaded.
    message : str
        Status message.
    """

    tracked_book_id: int = Field(..., description="ID of the tracked book")
    download_item_id: int = Field(..., description="ID of the download item")
    release_title: str = Field(..., description="Title of the release")
    message: str = Field(..., description="Status message")

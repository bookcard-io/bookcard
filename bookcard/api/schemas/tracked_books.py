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

"""API schemas for tracked book management endpoints.

Pydantic models for request/response validation for tracked book operations.
"""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from bookcard.models.pvr import MonitorMode, TrackedBookStatus


class TrackedBookCreate(BaseModel):
    """Request schema for adding a book to tracking.

    Attributes
    ----------
    title : str
        Book title to track.
    author : str
        Author name to track.
    isbn : str | None
        Optional ISBN for more precise matching.
    library_id : int | None
        Target library ID (None uses active library).
    metadata_source_id : str | None
        Source ID of the metadata provider (e.g., 'google').
    metadata_external_id : str | None
        External ID from the metadata provider.
    auto_search_enabled : bool
        Whether to automatically search for this book.
    auto_download_enabled : bool
        Whether to automatically download when found.
    preferred_formats : list[str] | None
        List of preferred formats (e.g., ['epub', 'pdf']).
    """

    title: str = Field(..., max_length=500, description="Book title to track")
    author: str = Field(..., max_length=500, description="Author name to track")
    isbn: str | None = Field(
        default=None, max_length=20, description="Optional ISBN for precise matching"
    )
    library_id: int | None = Field(
        default=None, description="Target library ID (None uses active library)"
    )
    metadata_source_id: str | None = Field(
        default=None, max_length=100, description="Metadata provider source ID"
    )
    metadata_external_id: str | None = Field(
        default=None, max_length=255, description="Metadata provider external ID"
    )
    auto_search_enabled: bool = Field(
        default=True, description="Whether to automatically search for this book"
    )
    auto_download_enabled: bool = Field(
        default=False, description="Whether to automatically download when found"
    )
    monitor_mode: MonitorMode = Field(
        default=MonitorMode.BOOK_ONLY, description="Monitor mode"
    )
    preferred_formats: list[str] | None = Field(
        default=None, description="List of preferred formats"
    )
    cover_url: str | None = Field(
        default=None, max_length=2000, description="Book cover URL"
    )
    description: str | None = Field(
        default=None, description="Book description/synopsis"
    )
    publisher: str | None = Field(
        default=None, max_length=500, description="Publisher name"
    )
    published_date: str | None = Field(
        default=None, max_length=50, description="Publication date"
    )
    rating: float | None = Field(default=None, description="Average rating")
    tags: list[str] | None = Field(default=None, description="List of tags/genres")
    series_name: str | None = Field(
        default=None, max_length=500, description="Series name"
    )
    series_index: float | None = Field(default=None, description="Series index/number")
    exclude_keywords: list[str] | None = Field(
        default=None, description="Keywords to exclude from release title/description"
    )
    require_keywords: list[str] | None = Field(
        default=None,
        description="Keywords that must appear in release title/description",
    )
    require_title_match: bool = Field(
        default=True, description="Whether title must match search criteria"
    )
    require_author_match: bool = Field(
        default=True, description="Whether author must match search criteria"
    )
    require_isbn_match: bool = Field(
        default=False, description="Whether ISBN must match if provided"
    )


class TrackedBookUpdate(BaseModel):
    """Request schema for updating a tracked book.

    All fields are optional for partial updates.

    Attributes
    ----------
    status : TrackedBookStatus | None
        New tracking status.
    auto_search_enabled : bool | None
        Whether to automatically search for this book.
    auto_download_enabled : bool | None
        Whether to automatically download when found.
    preferred_formats : list[str] | None
        List of preferred formats.
    library_id : int | None
        Target library ID.
    """

    status: TrackedBookStatus | None = Field(
        default=None, description="New tracking status"
    )
    monitor_mode: MonitorMode | None = Field(
        default=None, description="New monitor mode"
    )
    auto_search_enabled: bool | None = Field(
        default=None, description="Whether to automatically search for this book"
    )
    auto_download_enabled: bool | None = Field(
        default=None, description="Whether to automatically download when found"
    )
    preferred_formats: list[str] | None = Field(
        default=None, description="List of preferred formats"
    )
    library_id: int | None = Field(default=None, description="Target library ID")
    title: str | None = Field(default=None, max_length=500, description="Book title")
    author: str | None = Field(default=None, max_length=500, description="Author name")
    isbn: str | None = Field(default=None, max_length=20, description="ISBN")
    cover_url: str | None = Field(
        default=None, max_length=2000, description="Cover URL"
    )
    description: str | None = Field(default=None, description="Book description")
    publisher: str | None = Field(default=None, max_length=500, description="Publisher")
    published_date: str | None = Field(
        default=None, max_length=50, description="Publication date"
    )
    rating: float | None = Field(default=None, description="Average rating")
    tags: list[str] | None = Field(default=None, description="List of tags/genres")
    series_name: str | None = Field(
        default=None, max_length=500, description="Series name"
    )
    series_index: float | None = Field(default=None, description="Series index/number")
    exclude_keywords: list[str] | None = Field(
        default=None, description="Keywords to exclude from release title/description"
    )
    require_keywords: list[str] | None = Field(
        default=None,
        description="Keywords that must appear in release title/description",
    )
    require_title_match: bool | None = Field(
        default=None, description="Whether title must match search criteria"
    )
    require_author_match: bool | None = Field(
        default=None, description="Whether author must match search criteria"
    )
    require_isbn_match: bool | None = Field(
        default=None, description="Whether ISBN must match if provided"
    )


class BookFileRead(BaseModel):
    """Schema for book file details."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(validation_alias=AliasChoices("name", "filename"))
    format: str = Field(validation_alias=AliasChoices("format", "file_type"))
    size: int = Field(validation_alias=AliasChoices("size", "size_bytes"))
    path: str


class TrackedBookRead(BaseModel):
    """Response schema for tracked book data.

    Attributes
    ----------
    id : int
        Primary key identifier.
    title : str
        Book title.
    author : str
        Author name.
    isbn : str | None
        ISBN.
    library_id : int | None
        Target library ID.
    metadata_source_id : str | None
        Metadata source ID.
    metadata_external_id : str | None
        Metadata external ID.
    status : TrackedBookStatus
        Current status.
    auto_search_enabled : bool
        Auto-search setting.
    auto_download_enabled : bool
        Auto-download setting.
    preferred_formats : list[str] | None
        Preferred formats.
    last_searched_at : datetime | None
        Timestamp of last search.
    last_downloaded_at : datetime | None
        Timestamp of last download.
    matched_book_id : int | None
        ID of matched book in Calibre library.
    matched_library_id : int | None
        Library ID where match was found.
    error_message : str | None
        Error message if failed.
    created_at : datetime
        Creation timestamp.
    updated_at : datetime
        Update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str | None
    library_id: int | None
    metadata_source_id: str | None
    metadata_external_id: str | None
    status: TrackedBookStatus
    monitor_mode: MonitorMode
    auto_search_enabled: bool
    auto_download_enabled: bool
    preferred_formats: list[str] | None
    last_searched_at: datetime | None
    last_downloaded_at: datetime | None
    matched_book_id: int | None
    matched_library_id: int | None
    error_message: str | None
    cover_url: str | None
    description: str | None
    publisher: str | None
    published_date: str | None
    rating: float | None
    tags: list[str] | None
    series_name: str | None
    series_index: float | None
    exclude_keywords: list[str] | None
    require_keywords: list[str] | None
    require_title_match: bool
    require_author_match: bool
    require_isbn_match: bool
    created_at: datetime
    updated_at: datetime
    files: list[BookFileRead] | None = Field(default=None)


class TrackedBookListResponse(BaseModel):
    """Response schema for listing tracked books.

    Attributes
    ----------
    items : list[TrackedBookRead]
        List of tracked books.
    total : int
        Total number of tracked books.
    """

    items: list[TrackedBookRead]
    total: int


class TrackedBookStatusResponse(BaseModel):
    """Response schema for tracked book status.

    Attributes
    ----------
    id : int
        Tracked book ID.
    status : TrackedBookStatus
        Current status.
    matched_book_id : int | None
        ID of matched book in Calibre library.
    error_message : str | None
        Error message if failed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TrackedBookStatus
    matched_book_id: int | None
    error_message: str | None

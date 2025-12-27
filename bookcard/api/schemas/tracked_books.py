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

from pydantic import BaseModel, ConfigDict, Field

from bookcard.models.pvr import TrackedBookStatus


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
    preferred_formats: list[str] | None = Field(
        default=None, description="List of preferred formats"
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
    auto_search_enabled: bool
    auto_download_enabled: bool
    preferred_formats: list[str] | None
    last_searched_at: datetime | None
    last_downloaded_at: datetime | None
    matched_book_id: int | None
    matched_library_id: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


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

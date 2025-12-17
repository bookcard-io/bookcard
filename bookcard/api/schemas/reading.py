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

"""API schemas for reading endpoints.

Pydantic models for request/response validation for reading operations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class ReadingProgressCreate(BaseModel):
    """Request schema for creating/updating reading progress.

    Attributes
    ----------
    book_id : int
        Book ID.
    format : str
        Book format (EPUB, PDF, etc.).
    progress : float
        Reading progress as percentage (0.0 to 1.0).
    cfi : str | None
        Canonical Fragment Identifier for EPUB (optional).
    page_number : int | None
        Page number for PDF or comic formats (optional).
    device : str | None
        Device identifier (optional).
    spread_mode : bool | None
        Whether reading in spread mode for comics (optional).
    reading_direction : str | None
        Reading direction for comics: 'ltr', 'rtl', or 'vertical' (optional).
    """

    book_id: int = Field(description="Book ID")
    format: str = Field(max_length=10, description="Book format (EPUB, PDF, etc.)")
    progress: float = Field(
        ge=0.0,
        le=1.0,
        description="Reading progress as percentage (0.0 to 1.0)",
    )
    cfi: str | None = Field(
        default=None,
        max_length=2000,
        description="Canonical Fragment Identifier for EPUB",
    )
    page_number: int | None = Field(
        default=None,
        ge=0,
        description="Page number for PDF or comic formats",
    )
    device: str | None = Field(
        default=None,
        max_length=255,
        description="Device identifier",
    )
    spread_mode: bool | None = Field(
        default=None,
        description="Whether reading in spread mode for comics",
    )
    reading_direction: str | None = Field(
        default=None,
        max_length=20,
        description="Reading direction for comics: 'ltr', 'rtl', or 'vertical'",
    )


class ReadingProgressRead(BaseModel):
    """Response schema for reading progress data.

    Attributes
    ----------
    id : int
        Progress primary key.
    user_id : int
        User ID.
    library_id : int
        Library ID.
    book_id : int
        Book ID.
    format : str
        Book format.
    progress : float
        Reading progress (0.0 to 1.0).
    cfi : str | None
        CFI for EPUB.
    page_number : int | None
        Page number for PDF or comic formats.
    device : str | None
        Device identifier.
    spread_mode : bool | None
        Whether reading in spread mode for comics.
    reading_direction : str | None
        Reading direction for comics: 'ltr', 'rtl', or 'vertical'.
    updated_at : datetime
        Last update timestamp.
    """

    id: int
    user_id: int
    library_id: int
    book_id: int
    format: str
    progress: float
    cfi: str | None
    page_number: int | None
    device: str | None
    spread_mode: bool | None = None
    reading_direction: str | None = None
    updated_at: datetime


class ReadingSessionCreate(BaseModel):
    """Request schema for starting a reading session.

    Attributes
    ----------
    book_id : int
        Book ID.
    format : str
        Book format (EPUB, PDF, etc.).
    device : str | None
        Device identifier (optional).
    """

    book_id: int = Field(description="Book ID")
    format: str = Field(max_length=10, description="Book format (EPUB, PDF, etc.)")
    device: str | None = Field(
        default=None,
        max_length=255,
        description="Device identifier",
    )


class ReadingSessionEnd(BaseModel):
    """Request schema for ending a reading session.

    Attributes
    ----------
    progress_end : float
        Final reading progress (0.0 to 1.0).
    """

    progress_end: float = Field(
        ge=0.0,
        le=1.0,
        description="Final reading progress (0.0 to 1.0)",
    )


class ReadingSessionRead(BaseModel):
    """Response schema for reading session data.

    Attributes
    ----------
    id : int
        Session primary key.
    user_id : int
        User ID.
    library_id : int
        Library ID.
    book_id : int
        Book ID.
    format : str
        Book format.
    started_at : datetime
        Session start timestamp.
    ended_at : datetime | None
        Session end timestamp (None if ongoing).
    progress_start : float
        Progress at session start.
    progress_end : float | None
        Progress at session end (None if ongoing).
    device : str | None
        Device identifier.
    created_at : datetime
        Record creation timestamp.
    duration : float | None
        Session duration in seconds (None if ongoing).
    """

    id: int
    user_id: int
    library_id: int
    book_id: int
    format: str
    started_at: datetime
    ended_at: datetime | None
    progress_start: float
    progress_end: float | None
    device: str | None
    created_at: datetime
    duration: float | None


class ReadStatusUpdate(BaseModel):
    """Request schema for updating read status.

    Attributes
    ----------
    status : str
        Read status: 'read' or 'not_read'.
    """

    status: str = Field(
        description="Read status: 'read' or 'not_read'",
        pattern="^(read|not_read)$",
    )


class ReadStatusRead(BaseModel):
    """Response schema for read status data.

    Attributes
    ----------
    id : int
        Status primary key.
    user_id : int
        User ID.
    library_id : int
        Library ID.
    book_id : int
        Book ID.
    status : str
        Current read status (NOT_READ, READING, READ).
    first_opened_at : datetime | None
        Timestamp when book was first opened.
    marked_as_read_at : datetime | None
        Timestamp when book was marked as read.
    auto_marked : bool
        Whether book was automatically marked as read.
    progress_when_marked : float | None
        Progress percentage when marked as read.
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    id: int
    user_id: int
    library_id: int
    book_id: int
    status: str
    first_opened_at: datetime | None
    marked_as_read_at: datetime | None
    auto_marked: bool
    progress_when_marked: float | None
    created_at: datetime
    updated_at: datetime


class RecentReadsResponse(BaseModel):
    """Response schema for recent reads list.

    Attributes
    ----------
    reads : list[ReadingProgressRead]
        List of recent reading progress records.
    total : int
        Total number of recent reads.
    """

    reads: list[ReadingProgressRead]
    total: int


class ReadingHistoryResponse(BaseModel):
    """Response schema for reading history.

    Attributes
    ----------
    sessions : list[ReadingSessionRead]
        List of reading sessions.
    total : int
        Total number of sessions.
    """

    sessions: list[ReadingSessionRead]
    total: int


class ReadingSessionsListResponse(BaseModel):
    """Response schema for listing reading sessions.

    Attributes
    ----------
    sessions : list[ReadingSessionRead]
        List of reading sessions.
    total : int
        Total number of sessions.
    page : int
        Current page number.
    page_size : int
        Number of items per page.
    """

    sessions: list[ReadingSessionRead]
    total: int
    page: int
    page_size: int

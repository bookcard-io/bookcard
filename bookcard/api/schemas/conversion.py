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

"""Book conversion API schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class ConversionRequest(BaseModel):
    """Request DTO for book format conversion.

    Attributes
    ----------
    book_id : int
        Book ID to convert.
    original_format : str
        Source format (e.g., "MOBI", "AZW3").
    target_format : str
        Target format (e.g., "EPUB", "KEPUB").
    """

    book_id: int
    original_format: str
    target_format: str


class BookConversionRead(BaseModel):
    """Book conversion record for API responses.

    Attributes
    ----------
    id : int
        Conversion record ID.
    book_id : int
        Book ID.
    original_format : str
        Source format.
    target_format : str
        Target format.
    conversion_method : str
        How conversion was triggered.
    status : str
        Conversion status.
    error_message : str | None
        Error message if failed.
    original_backed_up : bool
        Whether original was backed up.
    created_at : datetime
        Conversion start timestamp.
    completed_at : datetime | None
        Conversion completion timestamp.
    duration : float | None
        Conversion duration in seconds.
    """

    id: int
    book_id: int
    original_format: str
    target_format: str
    conversion_method: str
    status: str
    error_message: str | None
    original_backed_up: bool
    created_at: datetime
    completed_at: datetime | None
    duration: float | None = Field(default=None)


class BookConversionListResponse(BaseModel):
    """Response for conversion history list.

    Attributes
    ----------
    items : list[BookConversionRead]
        List of conversion records.
    total : int
        Total number of conversions.
    page : int
        Current page number.
    page_size : int
        Page size.
    total_pages : int
        Total number of pages.
    """

    items: list[BookConversionRead]
    total: int
    page: int
    page_size: int
    total_pages: int

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

"""API schemas for shelf endpoints.

Pydantic models for request/response validation for shelf operations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class ShelfCreate(BaseModel):
    """Request schema for creating a shelf.

    Attributes
    ----------
    name : str
        Shelf name (must be unique per user for private, globally for public).
    description : str | None
        Optional description of the shelf.
    is_public : bool
        Whether the shelf is shared with everyone.
    """

    name: str = Field(max_length=255, description="Shelf name")
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional description of the shelf",
    )
    is_public: bool = Field(
        default=False,
        description="Whether the shelf is shared with everyone",
    )


class ShelfUpdate(BaseModel):
    """Request schema for updating a shelf.

    Attributes
    ----------
    name : str | None
        New shelf name (optional).
    description : str | None
        New description (optional).
    is_public : bool | None
        New public status (optional).
    """

    name: str | None = Field(
        default=None,
        max_length=255,
        description="New shelf name",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="New description",
    )
    is_public: bool | None = Field(
        default=None,
        description="Whether the shelf is shared with everyone",
    )


class ShelfRead(BaseModel):
    """Response schema for shelf data.

    Attributes
    ----------
    id : int
        Shelf primary key.
    uuid : str
        Unique identifier for external references.
    name : str
        Shelf name.
    description : str | None
        Optional description of the shelf.
    cover_picture : str | None
        Path to cover picture file (relative to data_directory).
    is_public : bool
        Whether the shelf is shared with everyone.
    is_active : bool
        Whether the shelf is active (mirrors library's active status).
    user_id : int
        Owner user ID.
    library_id : int
        Library ID the shelf belongs to.
    created_at : datetime
        Shelf creation timestamp.
    updated_at : datetime
        Last update timestamp.
    last_modified : datetime
        Last time books were added/removed/reordered.
    book_count : int
        Number of books in the shelf.
    """

    id: int
    uuid: str
    name: str
    description: str | None
    cover_picture: str | None
    is_public: bool
    is_active: bool
    user_id: int
    library_id: int
    created_at: datetime
    updated_at: datetime
    last_modified: datetime
    book_count: int = Field(default=0, description="Number of books in the shelf")


class ShelfListResponse(BaseModel):
    """Response schema for listing shelves.

    Attributes
    ----------
    shelves : list[ShelfRead]
        List of shelves.
    total : int
        Total number of shelves.
    """

    shelves: list[ShelfRead]
    total: int


class BookShelfLinkRead(BaseModel):
    """Response schema for book-shelf link data.

    Attributes
    ----------
    book_id : int
        Calibre book ID.
    order : int
        Display order within the shelf.
    date_added : datetime
        Timestamp when book was added to shelf.
    """

    book_id: int
    order: int
    date_added: datetime


class ShelfReorderRequest(BaseModel):
    """Request schema for reordering books in a shelf.

    Attributes
    ----------
    book_orders : dict[int, int]
        Mapping of book_id to new order value.
    """

    book_orders: dict[int, int] = Field(
        description="Mapping of book_id to new order value",
    )


class ShelfBooksResponse(BaseModel):
    """Response schema for listing books in a shelf.

    Attributes
    ----------
    book_ids : list[int]
        List of book IDs in order.
    total : int
        Total number of books in the shelf.
    page : int
        Current page number.
    page_size : int
        Number of items per page.
    sort_by : str
        Sort field used.
    sort_order : str
        Sort order used ('asc' or 'desc').
    """

    book_ids: list[int]
    total: int
    page: int
    page_size: int
    sort_by: str
    sort_order: str

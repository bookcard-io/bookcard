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
from typing import Any

from pydantic import BaseModel, Field

from bookcard.models.shelves import ShelfTypeEnum


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
    shelf_type : ShelfTypeEnum
        Type of the shelf (SHELF or READ_LIST).
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
    shelf_type: ShelfTypeEnum = Field(
        default=ShelfTypeEnum.SHELF,
        description="Type of the shelf (SHELF, READ_LIST, or MAGIC_SHELF)",
    )
    filter_rules: dict[str, Any] | None = Field(
        default=None,
        description="Filter rules for Magic Shelves",
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
    shelf_type : ShelfTypeEnum | None
        New shelf type (optional).
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
    shelf_type: ShelfTypeEnum | None = Field(
        default=None,
        description="Type of the shelf (SHELF, READ_LIST, or MAGIC_SHELF)",
    )
    filter_rules: dict[str, Any] | None = Field(
        default=None,
        description="New filter rules",
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
    shelf_type : ShelfTypeEnum
        Type of the shelf (SHELF or READ_LIST).
    read_list_metadata : dict[str, Any] | None
        Original read list metadata if shelf was created from import.
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
    shelf_type: ShelfTypeEnum
    filter_rules: dict[str, Any] | None = Field(
        default=None,
        description="Filter rules for Magic Shelves",
    )
    read_list_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Original read list metadata if shelf was created from import",
    )
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


class ShelfBookRef(BaseModel):
    """Reference to a book within a shelf, including its library context.

    Attributes
    ----------
    book_id : int
        Calibre book ID.
    library_id : int
        Library the book belongs to.
    """

    book_id: int
    library_id: int


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


class ShelfBookOrderItem(BaseModel):
    """A single book-order entry for reorder requests.

    Attributes
    ----------
    book_id : int
        Calibre book ID.
    library_id : int
        Library the book belongs to.
    order : int
        New display order value.
    """

    book_id: int
    library_id: int
    order: int


class ShelfReorderRequest(BaseModel):
    """Request schema for reordering books in a shelf.

    Attributes
    ----------
    book_orders : list[ShelfBookOrderItem]
        List of book-order entries specifying the new order per (book_id, library_id).
    """

    book_orders: list[ShelfBookOrderItem] = Field(
        description="List of book-order entries with book_id, library_id, and order",
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


class BookMatch(BaseModel):
    """Schema for a matched book in import result.

    Attributes
    ----------
    book_id : int
        Matched book ID.
    confidence : float
        Match confidence score (0.0 to 1.0).
    match_type : str
        Type of match: 'exact', 'fuzzy', 'title', or 'none'.
    reference : dict
        Original book reference data.
    """

    book_id: int = Field(description="Matched book ID")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Match confidence score (0.0 to 1.0)",
    )
    match_type: str = Field(
        description="Type of match: 'exact', 'fuzzy', 'title', or 'none'",
    )
    reference: dict = Field(description="Original book reference data")


class BookReferenceSchema(BaseModel):
    """Schema for an unmatched book reference.

    Attributes
    ----------
    series : str | None
        Series name.
    volume : int | float | None
        Volume number.
    issue : int | float | None
        Issue number.
    year : int | None
        Publication year.
    title : str | None
        Book title.
    author : str | None
        Author name.
    """

    series: str | None = None
    volume: int | float | None = None
    issue: int | float | None = None
    year: int | None = None
    title: str | None = None
    author: str | None = None


class ShelfImportRequest(BaseModel):
    """Request schema for importing a read list.

    Attributes
    ----------
    importer : str
        Name of the importer to use (default: "comicrack").
    auto_match : bool
        If True, automatically add matched books to shelf (default: False).
    """

    importer: str = Field(
        default="comicrack",
        description="Name of the importer to use",
    )
    auto_match: bool = Field(
        default=False,
        description="If True, automatically add matched books to shelf",
    )


class ImportResultSchema(BaseModel):
    """Response schema for read list import result.

    Attributes
    ----------
    total_books : int
        Total number of books in the read list.
    matched : list[BookMatch]
        Successfully matched books.
    unmatched : list[BookReferenceSchema]
        Books that could not be matched.
    errors : list[str]
        List of error messages encountered during import.
    """

    total_books: int = Field(description="Total number of books in the read list")
    matched: list[BookMatch] = Field(
        default_factory=list,
        description="Successfully matched books",
    )
    unmatched: list[BookReferenceSchema] = Field(
        default_factory=list,
        description="Books that could not be matched",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of error messages encountered during import",
    )

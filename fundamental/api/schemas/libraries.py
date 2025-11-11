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

"""Library management API schemas."""

from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 Pydantic needs datetime at runtime for validation
)

from pydantic import BaseModel, ConfigDict, Field


class LibraryRead(BaseModel):
    """Library representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    calibre_db_path: str
    calibre_db_file: str
    calibre_uuid: str | None = None
    use_split_library: bool
    split_library_dir: str | None = None
    auto_reconnect: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LibraryCreate(BaseModel):
    """Payload to create a library."""

    name: str = Field(description="User-friendly library name")
    calibre_db_path: str = Field(
        description="Path to Calibre database directory (contains metadata.db)"
    )
    calibre_db_file: str = Field(
        default="metadata.db", description="Calibre database filename"
    )
    use_split_library: bool = Field(
        default=False, description="Whether to use split library mode"
    )
    split_library_dir: str | None = Field(
        default=None, description="Directory for split library mode"
    )
    auto_reconnect: bool = Field(
        default=True, description="Whether to automatically reconnect on errors"
    )
    is_active: bool = Field(default=False, description="Set as the active library")


class LibraryUpdate(BaseModel):
    """Payload to update a library."""

    name: str | None = Field(default=None, description="User-friendly library name")
    calibre_db_path: str | None = Field(
        default=None, description="Path to Calibre database directory"
    )
    calibre_db_file: str | None = Field(
        default=None, description="Calibre database filename"
    )
    calibre_uuid: str | None = Field(default=None, description="Calibre library UUID")
    use_split_library: bool | None = Field(
        default=None, description="Whether to use split library mode"
    )
    split_library_dir: str | None = Field(
        default=None, description="Directory for split library mode"
    )
    auto_reconnect: bool | None = Field(
        default=None, description="Whether to automatically reconnect on errors"
    )
    is_active: bool | None = Field(
        default=None, description="Set as the active library"
    )


class LibraryStats(BaseModel):
    """Library statistics representation."""

    total_books: int = Field(description="Total number of books")
    total_series: int = Field(description="Total number of unique series")
    total_authors: int = Field(description="Total number of unique authors")
    total_tags: int = Field(description="Total number of unique tags")
    total_ratings: int = Field(description="Total number of books with ratings")
    total_content_size: int = Field(description="Total file size in bytes")

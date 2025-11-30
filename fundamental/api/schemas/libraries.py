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
    auto_convert_on_ingest: bool
    auto_convert_target_format: str | None = None
    auto_convert_ignored_formats: str | None = None
    auto_convert_backup_originals: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LibraryCreate(BaseModel):
    """Payload to create a library."""

    name: str = Field(description="User-friendly library name")
    calibre_db_path: str | None = Field(
        default=None,
        description=(
            "Path to Calibre database directory (contains metadata.db). "
            "If not provided, path will be auto-generated from library name."
        ),
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
    auto_convert_on_ingest: bool | None = Field(
        default=None,
        description="Whether to automatically convert books to target format during auto-ingest",
    )
    auto_convert_target_format: str | None = Field(
        default=None,
        description="Target format for automatic conversion during ingest (e.g., 'epub')",
    )
    auto_convert_ignored_formats: str | None = Field(
        default=None,
        description="JSON array of format strings to ignore during auto-conversion on ingest",
    )
    auto_convert_backup_originals: bool | None = Field(
        default=None,
        description="Whether to backup original files before conversion during ingest",
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

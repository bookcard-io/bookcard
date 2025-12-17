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

"""Author management API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuthorUpdate(BaseModel):
    """Author update payload for editing author metadata.

    Attributes
    ----------
    name : str | None
        Author name.
    personal_name : str | None
        Personal name (if different from name).
    fuller_name : str | None
        Fuller name.
    title : str | None
        Title (e.g., "OBE").
    birth_date : str | None
        Birth date.
    death_date : str | None
        Death date.
    entity_type : str | None
        Entity type.
    biography : str | None
        Biography text.
    location : str | None
        Location/country.
    photo_url : str | None
        Photo URL (deprecated, use photo upload endpoints).
    genres : list[str] | None
        Genres associated with author (user-defined).
    styles : list[str] | None
        Styles associated with author (user-defined).
    shelves : list[str] | None
        Shelves associated with author (user-defined).
    similar_authors : list[str] | None
        Similar authors (array of author keys or names, user-defined).
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    personal_name: str | None = None
    fuller_name: str | None = None
    title: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    entity_type: str | None = None
    biography: str | None = None
    location: str | None = None
    photo_url: str | None = None
    genres: list[str] | None = None
    styles: list[str] | None = None
    shelves: list[str] | None = None
    similar_authors: list[str] | None = None


class AuthorRead(BaseModel):
    """Author representation for API responses.

    This matches the structure returned by AuthorService._build_author_dict().
    The actual structure is complex and defined by the service layer.
    """

    model_config = ConfigDict(from_attributes=True, extra="allow")


class PhotoFromUrlRequest(BaseModel):
    """Request model for uploading photo from URL.

    Attributes
    ----------
    url : str
        URL of the image to download and save.
    """

    url: str = Field(..., description="URL of the image to download and save")


class PhotoUploadResponse(BaseModel):
    """Response model for photo upload operations.

    Attributes
    ----------
    photo_id : int
        ID of the created photo record.
    photo_url : str
        URL to access the uploaded photo.
    file_path : str
        Relative file path from data_directory.
    """

    photo_id: int
    photo_url: str
    file_path: str


class AuthorMergeRecommendRequest(BaseModel):
    """Request model for author merge recommendation.

    Attributes
    ----------
    author_ids : list[str]
        List of author IDs to merge (author_metadata IDs or OpenLibrary keys).
    """

    author_ids: list[str] = Field(..., min_length=2, description="Author IDs to merge")


class AuthorMergeRequest(BaseModel):
    """Request model for author merge operation.

    Attributes
    ----------
    author_ids : list[str]
        List of author IDs to merge (author_metadata IDs or OpenLibrary keys).
    keep_author_id : str
        Author ID to keep (others will be merged into this one).
    """

    author_ids: list[str] = Field(..., min_length=2, description="Author IDs to merge")
    keep_author_id: str = Field(..., description="Author ID to keep")

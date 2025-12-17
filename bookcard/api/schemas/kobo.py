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

"""Kobo API schemas.

Pydantic models for Kobo API request/response validation.
Note: Most Kobo endpoints return raw JSON, but these schemas can be
used for validation and documentation.
"""

from pydantic import BaseModel, Field


class KoboAuthTokenResponse(BaseModel):
    """Response schema for Kobo device authentication.

    Attributes
    ----------
    AccessToken : str
        Access token.
    RefreshToken : str
        Refresh token.
    TokenType : str
        Token type (usually "Bearer").
    TrackingId : str
        Tracking ID.
    UserKey : str
        User key.
    """

    AccessToken: str = Field(description="Access token")
    RefreshToken: str = Field(description="Refresh token")
    TokenType: str = Field(default="Bearer", description="Token type")
    TrackingId: str = Field(description="Tracking ID")
    UserKey: str = Field(default="", description="User key")


class KoboInitializationResponse(BaseModel):
    """Response schema for Kobo initialization.

    Attributes
    ----------
    Resources : dict[str, object]
        Resource URLs and configuration.
    """

    Resources: dict[str, object] = Field(description="Resource URLs and configuration")


class KoboTagRequest(BaseModel):
    """Request schema for creating/updating Kobo tags (shelves).

    Attributes
    ----------
    Name : str
        Tag/shelf name.
    Items : list[dict[str, object]] | None
        List of items to add to the tag.
    """

    Name: str = Field(description="Tag/shelf name")
    Items: list[dict[str, object]] | None = Field(
        default=None, description="List of items to add"
    )


class KoboTagItemRequest(BaseModel):
    """Request schema for adding/removing tag items.

    Attributes
    ----------
    Items : list[dict[str, object]]
        List of items to add or remove.
    """

    Items: list[dict[str, object]] = Field(description="List of items")


class KoboReadingStateRequest(BaseModel):
    """Request schema for updating reading state.

    Attributes
    ----------
    ReadingStates : list[dict[str, object]]
        List of reading states to update.
    """

    ReadingStates: list[dict[str, object]] = Field(description="List of reading states")


class KoboReadingStateUpdateResult(BaseModel):
    """Response schema for reading state update result.

    Attributes
    ----------
    RequestResult : str
        Request result (usually "Success").
    UpdateResults : list[dict[str, object]]
        List of update results.
    """

    RequestResult: str = Field(description="Request result")
    UpdateResults: list[dict[str, object]] = Field(description="List of update results")

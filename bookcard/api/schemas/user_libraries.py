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

"""User-library association API schemas."""

from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 Pydantic needs datetime at runtime for validation
)

from pydantic import BaseModel, ConfigDict, Field


class UserLibraryRead(BaseModel):
    """User-library association representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    library_id: int
    is_visible: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserLibraryAssign(BaseModel):
    """Payload to assign a library to a user."""

    library_id: int = Field(description="Library to assign")
    is_visible: bool = Field(
        default=True, description="Whether the library is visible to the user"
    )
    is_active: bool = Field(
        default=False,
        description="Whether this is the user's active library for ingestion",
    )


class UserLibraryVisibilityUpdate(BaseModel):
    """Payload to update library visibility for a user."""

    is_visible: bool = Field(description="Whether the library should be visible")

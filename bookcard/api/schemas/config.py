#
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
#
"""Schemas for basic system configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BasicConfigRead(BaseModel):
    """Read model for basic system configuration."""

    allow_anonymous_browsing: bool = Field(
        default=False,
        description="Whether anonymous users can browse the library.",
    )
    allow_public_registration: bool = Field(
        default=False,
        description="Whether public user registration is allowed.",
    )
    require_email_for_registration: bool = Field(
        default=False,
        description="Whether email is required for user registration.",
    )
    max_upload_size_mb: int = Field(
        default=100,
        description="Maximum file upload size in megabytes.",
    )


class BasicConfigUpdate(BaseModel):
    """Update model for basic system configuration."""

    allow_anonymous_browsing: bool | None = Field(
        default=None,
        description="Whether anonymous users can browse the library.",
    )
    allow_public_registration: bool | None = Field(
        default=None,
        description="Whether public user registration is allowed.",
    )
    require_email_for_registration: bool | None = Field(
        default=None,
        description="Whether email is required for user registration.",
    )
    max_upload_size_mb: int | None = Field(
        default=None,
        description="Maximum file upload size in megabytes.",
    )

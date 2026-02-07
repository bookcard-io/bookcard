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

"""User-library association model for multi-library support.

Maps users to libraries with per-user visibility and active-library
semantics. Each user can have multiple visible libraries, but exactly one
active library (the ingest target).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Index, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel


class UserLibrary(SQLModel, table=True):
    """Association between a user and a library.

    Supports per-user library access control with two independent flags:

    * ``is_visible`` -- the library's books appear in the user's listings.
    * ``is_active``  -- the library is the user's ingest target (only one
      per user).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to the owning user (CASCADE on delete).
    library_id : int
        Foreign key to the library (CASCADE on delete).
    is_visible : bool
        Whether the library's books appear in the user's listings
        (default: True).
    is_active : bool
        Whether this is the user's active library for ingestion
        (default: False).  At most one row per user should have this set.
    created_at : datetime
        Timestamp when the association was created.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "user_libraries"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    library_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    is_visible: bool = Field(default=True)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    __table_args__ = (
        UniqueConstraint("user_id", "library_id", name="uq_user_library"),
        Index("ix_user_libraries_user_active", "user_id", "is_active"),
        Index("ix_user_libraries_user_visible", "user_id", "is_visible"),
    )

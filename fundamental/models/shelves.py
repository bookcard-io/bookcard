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

"""Shelf models for organizing books into collections.

Shelves are an application feature (not a Calibre paradigm) that allow users
to organize books into named collections with public/private sharing.
"""

from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4

from pydantic import ConfigDict
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel


class Shelf(SQLModel, table=True):
    """Shelf model for organizing books into collections.

    Shelves allow users to create named collections of books with optional
    public sharing. Each shelf belongs to a library and a user, and can contain
    multiple books in a specific order. Shelves are library-specific, meaning
    each library has its own set of shelves.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    uuid : str
        Unique identifier for external references (e.g., Kobo sync).
    name : str
        Shelf name. Must be unique per library/user for private shelves,
        per library for public shelves.
    description : str | None
        Optional description of the shelf.
    cover_picture : str | None
        Path to cover picture file (relative to data_directory/{shelf_id}/).
    is_public : bool
        Whether the shelf is shared with everyone (True) or private (False).
    user_id : int
        Foreign key to User (owner of the shelf).
    library_id : int
        Foreign key to Library (the shelf belongs to this library).
    is_active : bool
        Whether the shelf is active (mirrors library's active status).
    created_at : datetime
        Shelf creation timestamp.
    updated_at : datetime
        Last update timestamp (when shelf properties changed).
    last_modified : datetime
        Last time books were added/removed/reordered in the shelf.
    """

    __tablename__ = "shelves"

    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid4()),
        unique=True,
        index=True,
        max_length=36,
    )
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=5000)
    cover_picture: str | None = Field(default=None, max_length=500)
    is_public: bool = Field(default=False, index=True)
    is_active: bool = Field(default=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    book_links: list["BookShelfLink"] = Relationship(
        back_populates="shelf",
        cascade_delete=True,
    )

    model_config = ConfigDict()
    indexes: ClassVar[list[tuple[str, ...]]] = [
        (
            "library_id",
            "user_id",
            "is_public",
        ),  # Composite index for library/user shelf queries
        (
            "library_id",
            "name",
            "is_public",
        ),  # Composite index for name uniqueness checks per library
    ]


class BookShelfLink(SQLModel, table=True):
    """Link table for books and shelves many-to-many relationship.

    Associates Calibre books (by ID) with shelves, maintaining order
    and tracking when books were added.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    shelf_id : int
        Foreign key to Shelf.
    book_id : int
        Calibre book ID (not a foreign key to avoid coupling with Calibre DB).
    order : int
        Display order within the shelf (0-based).
    date_added : datetime
        Timestamp when book was added to shelf.
    """

    __tablename__ = "book_shelf_links"

    id: int | None = Field(default=None, primary_key=True)
    shelf_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("shelves.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)
    order: int = Field(default=0, index=True)
    date_added: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    shelf: Shelf = Relationship(back_populates="book_links")

    model_config = ConfigDict()
    indexes: ClassVar[list[tuple[str, ...]]] = [
        ("shelf_id", "book_id"),  # Composite unique index
        ("shelf_id", "order"),  # Composite index for ordered listing
    ]


class ShelfArchive(SQLModel, table=True):
    """Archive table for deleted shelves.

    Tracks deleted shelves for propagation to external systems (e.g., Kobo sync).
    Stores the UUID and original owner for cleanup operations.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    uuid : str
        UUID of the deleted shelf.
    user_id : int
        Foreign key to User (original owner).
    deleted_at : datetime
        Timestamp when shelf was deleted.
    """

    __tablename__ = "shelf_archive"

    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(max_length=36, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    deleted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

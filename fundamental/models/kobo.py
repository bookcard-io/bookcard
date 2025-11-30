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

"""Kobo sync database models for Fundamental.

Models for tracking Kobo device synchronization, including authentication
tokens, reading states, synced books, and archived books.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from fundamental.models import User


class KoboAuthToken(SQLModel, table=True):
    """Kobo authentication token model.

    Stores per-user authentication tokens for Kobo device authentication.
    Each user can have one active token that is used to authenticate
    requests from Kobo devices.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    auth_token : str
        Unique authentication token (hex-encoded random bytes).
    created_at : datetime
        Token creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "kobo_auth_tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    auth_token: str = Field(unique=True, index=True, max_length=64)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    user: "User" = Relationship(back_populates="kobo_auth_token")


class KoboBookmark(SQLModel, table=True):
    """Kobo bookmark model.

    Stores current bookmark position for a book on a Kobo device.
    This includes progress percentage, location information, and
    content source progress.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    reading_state_id : int
        Foreign key to KoboReadingState.
    progress_percent : float | None
        Reading progress as percentage (0.0 to 100.0).
    content_source_progress_percent : float | None
        Content source progress as percentage.
    location_value : str | None
        Location value (CFI, page number, etc.).
    location_type : str | None
        Location type (e.g., "CFI", "Page").
    location_source : str | None
        Location source identifier.
    last_modified : datetime
        Last modification timestamp.
    """

    __tablename__ = "kobo_bookmarks"

    id: int | None = Field(default=None, primary_key=True)
    reading_state_id: int = Field(
        foreign_key="kobo_reading_states.id",
        unique=True,
        index=True,
    )
    progress_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    content_source_progress_percent: float | None = Field(
        default=None, ge=0.0, le=100.0
    )
    location_value: str | None = Field(default=None, max_length=2000)
    location_type: str | None = Field(default=None, max_length=50)
    location_source: str | None = Field(default=None, max_length=255)
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    reading_state: "KoboReadingState" = Relationship(back_populates="current_bookmark")


class KoboStatistics(SQLModel, table=True):
    """Kobo reading statistics model.

    Stores reading statistics for a book on a Kobo device, including
    time spent reading and estimated remaining time.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    reading_state_id : int
        Foreign key to KoboReadingState.
    spent_reading_minutes : int | None
        Total minutes spent reading.
    remaining_time_minutes : int | None
        Estimated remaining reading time in minutes.
    last_modified : datetime
        Last modification timestamp.
    """

    __tablename__ = "kobo_statistics"

    id: int | None = Field(default=None, primary_key=True)
    reading_state_id: int = Field(
        foreign_key="kobo_reading_states.id",
        unique=True,
        index=True,
    )
    spent_reading_minutes: int | None = Field(default=None, ge=0)
    remaining_time_minutes: int | None = Field(default=None, ge=0)
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    reading_state: "KoboReadingState" = Relationship(back_populates="statistics")


class KoboReadingState(SQLModel, table=True):
    """Kobo reading state model.

    Stores Kobo-specific reading state for a user/book combination.
    This includes bookmarks, statistics, and links to the main
    reading progress tracking.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    last_modified : datetime
        Last modification timestamp.
    priority_timestamp : datetime
        Priority timestamp for sync ordering.
    """

    __tablename__ = "kobo_reading_states"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
    priority_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    user: "User" = Relationship(back_populates="kobo_reading_states")
    current_bookmark: KoboBookmark | None = Relationship(
        back_populates="reading_state",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )
    statistics: KoboStatistics | None = Relationship(
        back_populates="reading_state",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )

    __table_args__ = (
        Index(
            "idx_kobo_reading_states_user_book",
            "user_id",
            "book_id",
            unique=True,
        ),
        Index("idx_kobo_reading_states_last_modified", "last_modified"),
    )


class KoboSyncedBook(SQLModel, table=True):
    """Kobo synced book model.

    Tracks which books have been synced to Kobo devices for a user.
    Used to determine which books need to be included in sync responses
    and to track sync history.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    synced_at : datetime
        Timestamp when book was last synced.
    """

    __tablename__ = "kobo_synced_books"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    synced_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    __table_args__ = (
        Index(
            "idx_kobo_synced_books_user_book",
            "user_id",
            "book_id",
            unique=True,
        ),
    )


class KoboArchivedBook(SQLModel, table=True):
    """Kobo archived book model.

    Tracks books that have been archived (deleted) on Kobo devices.
    Used to propagate archive status during sync operations.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    is_archived : bool
        Whether the book is archived.
    last_modified : datetime
        Last modification timestamp.
    """

    __tablename__ = "kobo_archived_books"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    is_archived: bool = Field(default=False, index=True)
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    __table_args__ = (
        Index(
            "idx_kobo_archived_books_user_book",
            "user_id",
            "book_id",
            unique=True,
        ),
    )

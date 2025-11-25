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

"""Reading-related database models for Fundamental."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Index, Integer
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from fundamental.models import User


class ReadStatusEnum(StrEnum):
    """Read status enumeration.

    Attributes
    ----------
    NOT_READ : str
        Book has not been opened/read.
    READING : str
        Book is currently being read.
    READ : str
        Book has been marked as read (manually or automatically).
    """

    NOT_READ = "not_read"
    READING = "reading"
    READ = "read"


class ReadingProgress(SQLModel, table=True):
    """Reading progress model for tracking current reading position.

    Tracks the latest reading position for a user/library/book/format combination.
    Replaces the legacy LastReadPosition model with proper foreign keys.
    Note: book_id references books in Calibre's metadata.db (no FK constraint).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    library_id : int
        Foreign key to library.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    format : str
        Book format (EPUB, PDF, etc.).
    progress : float
        Reading progress as percentage (0.0 to 1.0).
    cfi : str | None
        Canonical Fragment Identifier (CFI) for EPUB format.
    page_number : int | None
        Page number for PDF and other page-based formats.
    device : str | None
        Device identifier where reading occurred.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "reading_progress"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    format: str = Field(max_length=10, index=True)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    cfi: str | None = Field(default=None, max_length=2000)
    page_number: int | None = None
    device: str | None = Field(default=None, max_length=255)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    user: User = Relationship(back_populates="reading_progress")
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        Index(
            "idx_reading_progress_user_library_book_format",
            "user_id",
            "library_id",
            "book_id",
            "format",
            unique=True,
        ),
    )


class ReadingSession(SQLModel, table=True):
    """Reading session model for tracking full reading history.

    Tracks every reading session with start/end times and progress changes.
    Note: book_id references books in Calibre's metadata.db (no FK constraint).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    library_id : int
        Foreign key to library.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    format : str
        Book format (EPUB, PDF, etc.).
    started_at : datetime
        Session start timestamp.
    ended_at : datetime | None
        Session end timestamp (None if session is still active).
    progress_start : float
        Reading progress at session start (0.0 to 1.0).
    progress_end : float | None
        Reading progress at session end (0.0 to 1.0, None if session ongoing).
    device : str | None
        Device identifier where reading occurred.
    created_at : datetime
        Record creation timestamp.
    """

    __tablename__ = "reading_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    format: str = Field(max_length=10, index=True)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    ended_at: datetime | None = None
    progress_start: float = Field(default=0.0, ge=0.0, le=1.0)
    progress_end: float | None = Field(default=None, ge=0.0, le=1.0)
    device: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    user: User = Relationship(back_populates="reading_sessions")
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        Index(
            "idx_reading_sessions_user_library_book",
            "user_id",
            "library_id",
            "book_id",
        ),
        Index("idx_reading_sessions_started_at", "started_at"),
    )

    @property
    def duration(self) -> float | None:
        """Calculate session duration in seconds.

        Returns
        -------
        float | None
            Duration in seconds, or None if session hasn't ended.
        """
        if self.ended_at is None:
            return None

        # Ensure timezone-aware datetimes for comparison
        started_at = self.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)

        ended_at = self.ended_at
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=UTC)

        return (ended_at - started_at).total_seconds()


class ReadStatus(SQLModel, table=True):
    """Read status model for tracking book read status.

    Tracks when books are marked as read, with support for automatic
    marking at 90% progress threshold and manual marking.
    Note: book_id references books in Calibre's metadata.db (no FK constraint).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    library_id : int
        Foreign key to library.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    status : ReadStatusEnum
        Current read status (NOT_READ, READING, READ).
    first_opened_at : datetime | None
        Timestamp when book was first opened.
    marked_as_read_at : datetime | None
        Timestamp when book was marked as read.
    auto_marked : bool
        Whether book was automatically marked as read (default False).
    progress_when_marked : float | None
        Progress percentage when marked as read (0.0 to 1.0).
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "read_status"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    status: ReadStatusEnum = Field(default=ReadStatusEnum.NOT_READ)
    first_opened_at: datetime | None = None
    marked_as_read_at: datetime | None = None
    auto_marked: bool = Field(default=False)
    progress_when_marked: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    user: User = Relationship(back_populates="read_statuses")
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        Index(
            "idx_read_status_user_library_book",
            "user_id",
            "library_id",
            "book_id",
            unique=True,
        ),
        Index("idx_read_status_status", "status"),
    )


class Annotation(SQLModel, table=True):
    """Annotation model for book annotations (highlights, bookmarks, notes).

    Updated to use proper foreign key to User model instead of string-based
    user identifier.
    Note: book_id references books in Calibre's metadata.db (no FK constraint).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user.
    library_id : int
        Foreign key to library.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    format : str
        Book format this annotation applies to.
    timestamp : float
        Timestamp when annotation was created.
    annot_id : str
        Unique annotation identifier.
    annot_type : str
        Type of annotation (e.g., 'highlight', 'bookmark', 'note').
    annot_data : str
        Annotation data (JSON or other format).
    searchable_text : str
        Searchable text content (default empty string).
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "annotations"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    format: str = Field(max_length=10, index=True)
    timestamp: float = Field(index=True)
    annot_id: str = Field(max_length=255, index=True)
    annot_type: str = Field(max_length=50, index=True)
    annot_data: str
    searchable_text: str = Field(default="", max_length=5000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    user: User = Relationship(back_populates="annotations")
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        Index(
            "idx_annotations_user_library_book",
            "user_id",
            "library_id",
            "book_id",
        ),
    )


class AnnotationDirtied(SQLModel, table=True):
    """Annotation dirtied model for tracking modified annotations.

    Note: book_id references books in Calibre's metadata.db (no FK constraint).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    library_id : int
        Foreign key to library.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "annotations_dirtied"

    id: int | None = Field(default=None, primary_key=True)
    library_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("libraries.id", ondelete="CASCADE"), index=True
        ),
    )
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

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

"""Book conversion database models for tracking format conversions."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from fundamental.models.auth import User
from fundamental.models.config import Library


class ConversionMethod(StrEnum):
    """Conversion method enumeration.

    Attributes
    ----------
    AUTO_IMPORT : str
        Automatic conversion during book import.
    MANUAL : str
        Manual conversion triggered by user.
    KINDLE_SEND : str
        Automatic conversion for Kindle device sending.
    """

    AUTO_IMPORT = "auto_import"
    MANUAL = "manual"
    KINDLE_SEND = "kindle_send"


class ConversionStatus(StrEnum):
    """Conversion status enumeration.

    Attributes
    ----------
    COMPLETED : str
        Conversion completed successfully.
    FAILED : str
        Conversion failed with an error.
    """

    COMPLETED = "completed"
    FAILED = "failed"


class BookConversion(SQLModel, table=True):
    """Book conversion model for tracking format conversions.

    Tracks each format conversion performed on a book, providing detailed
    audit trail of what was converted, when, and how.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    book_id : int
        Book ID from Calibre database (no FK constraint).
    library_id : int | None
        Foreign key to library (None if not library-specific).
    user_id : int | None
        Foreign key to user who triggered the conversion (None for automatic).
    original_format : str
        Source format (e.g., "MOBI", "AZW3").
    target_format : str
        Target format (e.g., "EPUB", "KEPUB").
    original_file_path : str
        Path to the original file that was converted.
    converted_file_path : str
        Path to the converted file.
    original_backed_up : bool
        Whether original file was backed up before conversion.
    backup_file_path : str | None
        Path to backup of original file (if backup was enabled).
    conversion_method : ConversionMethod
        How conversion was triggered.
    status : ConversionStatus
        Conversion status (completed or failed).
    error_message : str | None
        Error message if conversion failed.
    created_at : datetime
        Timestamp when conversion was initiated.
    completed_at : datetime | None
        Timestamp when conversion completed (None if still in progress or failed).
    """

    __tablename__ = "book_conversions"

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(index=True)  # No FK constraint - books are in Calibre DB
    library_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    original_format: str = Field(max_length=20, index=True)
    target_format: str = Field(max_length=20, index=True)
    original_file_path: str = Field(max_length=2000, index=True)
    converted_file_path: str = Field(max_length=2000)
    original_backed_up: bool = Field(default=False)
    backup_file_path: str | None = Field(default=None, max_length=2000)
    conversion_method: ConversionMethod = Field(
        sa_column=Column(
            SQLEnum(ConversionMethod, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    status: ConversionStatus = Field(
        sa_column=Column(
            SQLEnum(ConversionStatus, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    completed_at: datetime | None = None

    # Relationships
    user: User | None = Relationship()
    library: Library | None = Relationship()
    # Note: No relationship to Book - Book is in Calibre DB, this is in Fundamental DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        UniqueConstraint(
            "book_id", "original_format", "target_format", name="uq_book_conversion"
        ),
        Index("idx_book_conversions_book", "book_id"),
        Index("idx_book_conversions_library_created", "library_id", "created_at"),
        Index("idx_book_conversions_user_created", "user_id", "created_at"),
        Index("idx_book_conversions_status_created", "status", "created_at"),
    )

    @property
    def duration(self) -> float | None:
        """Calculate conversion duration in seconds.

        Returns
        -------
        float | None
            Duration in seconds, or None if conversion hasn't completed.
        """
        if self.completed_at is None:
            return None

        # Ensure timezone-aware datetimes for comparison
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        completed_at = self.completed_at
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=UTC)

        return (completed_at - created_at).total_seconds()

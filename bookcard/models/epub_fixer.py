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

"""EPUB fixer database models for tracking EPUB compatibility fixes."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, ForeignKey, Index, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from bookcard.models.auth import User


class EPUBFixType(StrEnum):
    """EPUB fix type enumeration.

    Attributes
    ----------
    ENCODING : str
        UTF-8 encoding declaration fix.
    BODY_ID_LINK : str
        Body ID hyperlink fix (NCX table of contents).
    LANGUAGE_TAG : str
        Invalid or missing language tag fix.
    STRAY_IMG : str
        Stray image tag removal (no source attribute).
    """

    ENCODING = "encoding"
    BODY_ID_LINK = "body_id_link"
    LANGUAGE_TAG = "language_tag"
    STRAY_IMG = "stray_img"


class EPUBFixRun(SQLModel, table=True):
    """EPUB fix run model for tracking fixer execution sessions.

    Tracks each execution of the EPUB fixer, whether it's a single file
    or a bulk library operation. Provides audit trail for when fixes
    were applied and by whom.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int | None
        Foreign key to user who triggered the fix (None for automatic).
    library_id : int | None
        Foreign key to library (None if not library-specific).
    manually_triggered : bool
        Whether the fix was manually triggered by a user.
    is_bulk_operation : bool
        Whether this run processed multiple files.
    total_files_processed : int
        Total number of files processed in this run.
    total_files_fixed : int
        Number of files that had fixes applied.
    total_fixes_applied : int
        Total number of individual fixes applied across all files.
    backup_enabled : bool
        Whether original files were backed up before fixing.
    started_at : datetime
        Run start timestamp.
    completed_at : datetime | None
        Run completion timestamp (None if still running).
    error_message : str | None
        Error message if run failed.
    created_at : datetime
        Record creation timestamp.
    """

    __tablename__ = "epub_fix_runs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    library_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    manually_triggered: bool = Field(default=False, index=True)
    is_bulk_operation: bool = Field(default=False, index=True)
    total_files_processed: int = Field(default=0)
    total_files_fixed: int = Field(default=0)
    total_fixes_applied: int = Field(default=0)
    backup_enabled: bool = Field(default=False)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    user: User | None = Relationship(back_populates="epub_fix_runs")
    fixes: list["EPUBFix"] = Relationship(back_populates="run")

    __table_args__ = (
        Index("idx_epub_fix_runs_user_created", "user_id", "created_at"),
        Index("idx_epub_fix_runs_library_created", "library_id", "created_at"),
        Index(
            "idx_epub_fix_runs_manually_triggered", "manually_triggered", "created_at"
        ),
    )

    @property
    def duration(self) -> float | None:
        """Calculate run duration in seconds.

        Returns
        -------
        float | None
            Duration in seconds, or None if run hasn't completed.
        """
        if self.completed_at is None:
            return None

        # Ensure timezone-aware datetimes for comparison
        started_at = self.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)

        completed_at = self.completed_at
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=UTC)

        return (completed_at - started_at).total_seconds()

    @property
    def success_rate(self) -> float | None:
        """Calculate success rate of files fixed.

        Returns
        -------
        float | None
            Success rate as percentage (0.0 to 1.0), or None if no files processed.
        """
        if self.total_files_processed == 0:
            return None
        return self.total_files_fixed / self.total_files_processed


class EPUBFix(SQLModel, table=True):
    """EPUB fix model for tracking individual fixes applied to books.

    Tracks each fix applied to a specific book, providing detailed
    audit trail of what was fixed, when, and how.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    run_id : int
        Foreign key to fix run that applied this fix.
    book_id : int | None
        Book ID from Calibre database (no FK constraint).
    book_title : str
        Book title (for reference, may not match Calibre DB).
    file_path : str
        Path to the EPUB file that was fixed.
    original_file_path : str | None
        Path to backup of original file (if backup was enabled).
    fix_type : EPUBFixType
        Type of fix that was applied.
    fix_description : str
        Human-readable description of the fix.
    file_name : str
        Filename within EPUB that was fixed (for encoding, body_id_link, stray_img).
    original_value : str | None
        Original value before fix (for language tag changes).
    fixed_value : str | None
        New value after fix (for language tag changes).
    backup_created : bool
        Whether backup of original file was created.
    applied_at : datetime
        Timestamp when fix was applied.
    created_at : datetime
        Record creation timestamp.
    """

    __tablename__ = "epub_fixes"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("epub_fix_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    book_id: int | None = Field(
        default=None, index=True
    )  # No FK constraint - books are in Calibre DB
    book_title: str = Field(max_length=500, index=True)
    file_path: str = Field(max_length=2000, index=True)
    original_file_path: str | None = Field(default=None, max_length=2000)
    fix_type: EPUBFixType = Field(
        sa_column=Column(
            SQLEnum(EPUBFixType, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    fix_description: str = Field(sa_column=Column(Text, nullable=False))
    file_name: str | None = Field(default=None, max_length=500)  # Filename within EPUB
    original_value: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    fixed_value: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    backup_created: bool = Field(default=False)
    applied_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    run: EPUBFixRun = Relationship(back_populates="fixes")
    # Note: No relationship to Book - Book is in Calibre DB, this is in Bookcard DB
    # Linked only by book_id (integer), not by SQLAlchemy relationship

    __table_args__ = (
        Index("idx_epub_fixes_run_book", "run_id", "book_id"),
        Index("idx_epub_fixes_book_applied", "book_id", "applied_at"),
        Index("idx_epub_fixes_type_applied", "fix_type", "applied_at"),
        Index("idx_epub_fixes_file_path", "file_path"),
    )

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

"""Ingest management database models for Fundamental.

Models for tracking automatic book ingest operations, retries, and audit logs.
"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Index
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from fundamental.models.auth import User


class IngestStatus(StrEnum):
    """Ingest status enumeration.

    Attributes
    ----------
    PENDING : str
        Ingest is queued but not yet started.
    PROCESSING : str
        Ingest is currently being processed.
    COMPLETED : str
        Ingest completed successfully.
    FAILED : str
        Ingest failed with an error.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestHistory(SQLModel, table=True):
    """Model for tracking ingest operations.

    Tracks each file or file group processed during automatic book ingest,
    including status, metadata, and error information.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    file_path : str
        Path to the file or directory being ingested.
    status : IngestStatus
        Current status of the ingest operation.
    book_id : int | None
        ID of the book created in the library (if successful).
    ingest_metadata : dict | None
        JSON data containing metadata used for the ingest (title, author, etc.).
    created_at : datetime
        When the ingest operation was created.
    started_at : datetime | None
        When processing started.
    completed_at : datetime | None
        When processing completed (successfully or with failure).
    error_message : str | None
        Error message if ingest failed.
    retry_count : int
        Number of times this ingest has been retried.
    user_id : int | None
        Foreign key to user who triggered the ingest (if manual).
    """

    __tablename__ = "ingest_history"

    id: int | None = Field(default=None, primary_key=True)
    file_path: str = Field(index=True, max_length=2000)
    status: IngestStatus = Field(
        default=IngestStatus.PENDING,
        sa_column=Column(SQLEnum(IngestStatus, native_enum=False), nullable=False),  # type: ignore[call-overload]
    )
    book_id: int | None = Field(default=None, index=True)
    ingest_metadata: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    retry_count: int = Field(default=0)
    user_id: int | None = Field(
        default=None, foreign_key="users.id", nullable=True, index=True
    )

    # Relationships
    user: User | None = Relationship()

    __table_args__ = (
        Index("idx_ingest_history_status_created", "status", "created_at"),
        Index("idx_ingest_history_file_path", "file_path"),
    )

    @property
    def duration(self) -> float | None:
        """Calculate ingest duration in seconds.

        Returns
        -------
        float | None
            Duration in seconds, or None if ingest hasn't started.
        """
        if self.started_at is None:
            return None

        # Ensure timezone-aware datetimes for comparison
        started_at = self.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)

        end_time = self.completed_at or datetime.now(UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)

        return (end_time - started_at).total_seconds()

    @property
    def is_complete(self) -> bool:
        """Check if ingest is in a terminal state.

        Returns
        -------
        bool
            True if ingest is completed or failed.
        """
        return self.status in (IngestStatus.COMPLETED, IngestStatus.FAILED)


class IngestRetry(SQLModel, table=True):
    """Model for tracking failed ingest retries.

    Tracks retry attempts for failed ingest operations with exponential
    backoff scheduling.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    history_id : int
        Foreign key to the ingest history record being retried.
    retry_count : int
        Number of retry attempts (1-based).
    next_retry_at : datetime
        When the next retry should be attempted.
    error_message : str | None
        Error message from the last failed attempt.
    created_at : datetime
        When the retry record was created.
    """

    __tablename__ = "ingest_retry"

    id: int | None = Field(default=None, primary_key=True)
    history_id: int = Field(foreign_key="ingest_history.id", index=True, nullable=False)
    retry_count: int = Field(default=1)
    next_retry_at: datetime = Field(index=True)
    error_message: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    history: IngestHistory = Relationship()

    __table_args__ = (Index("idx_ingest_retry_next_retry", "next_retry_at"),)


class IngestAudit(SQLModel, table=True):
    """Model for audit logging of ingest operations.

    Provides detailed audit trail of all ingest operations for compliance
    and debugging purposes.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    history_id : int | None
        Foreign key to the ingest history record (if applicable).
    action : str
        Action performed (e.g., 'file_discovered', 'metadata_fetched', 'book_added').
    file_path : str
        Path to the file being processed.
    audit_metadata : dict | None
        JSON data with additional context about the action.
    user_id : int | None
        Foreign key to user who triggered the action (if applicable).
    timestamp : datetime
        When the action occurred.
    """

    __tablename__ = "ingest_audit"

    id: int | None = Field(default=None, primary_key=True)
    history_id: int | None = Field(
        default=None, foreign_key="ingest_history.id", nullable=True, index=True
    )
    action: str = Field(max_length=100, index=True)
    file_path: str = Field(max_length=2000)
    audit_metadata: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    user_id: int | None = Field(
        default=None, foreign_key="users.id", nullable=True, index=True
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    history: IngestHistory | None = Relationship()
    user: User | None = Relationship()

    __table_args__ = (
        Index("idx_ingest_audit_action_timestamp", "action", "timestamp"),
        Index("idx_ingest_audit_history_id", "history_id"),
    )


class IngestConfig(SQLModel, table=True):
    """Configuration for automatic book ingest service.

    Singleton model for storing ingest service configuration.
    Only one record should exist.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    ingest_dir : str
        Watch directory path for book files (default: '/app/books_ingest').
    enabled : bool
        Whether automatic ingest is active (default: True).
    metadata_providers : dict | None
        JSON data containing list of enabled provider IDs
        (e.g., ["google", "hardcover", "openlibrary"]).
    metadata_merge_strategy : str
        Strategy for merging metadata from multiple providers
        (default: 'merge_best').
    metadata_priority_order : dict | None
        JSON data containing provider priority list for metadata fetching.
    supported_formats : dict | None
        JSON data containing list of supported file extensions
        (default: all 27+ Calibre formats).
    ignore_patterns : dict | None
        JSON data containing file patterns to ignore (e.g., ["*.tmp", "*.bak"]).
    retry_max_attempts : int
        Maximum number of retry attempts for failed ingests (default: 3).
    retry_backoff_seconds : int
        Base backoff time in seconds for exponential backoff (default: 300).
    process_timeout_seconds : int
        Timeout in seconds per book processing (default: 3600).
    auto_delete_after_ingest : bool
        Whether to delete source files after successful ingest (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "ingest_config"

    id: int | None = Field(default=None, primary_key=True)
    ingest_dir: str = Field(default="/app/books_ingest", max_length=2000)
    enabled: bool = Field(default=True)
    metadata_providers: dict | None = Field(
        default=["google", "openlibrary", "hardcover"],
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    metadata_merge_strategy: str = Field(default="merge_best", max_length=50)
    metadata_priority_order: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    supported_formats: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    ignore_patterns: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    retry_max_attempts: int = Field(default=3)
    retry_backoff_seconds: int = Field(default=300)
    process_timeout_seconds: int = Field(default=3600)
    auto_delete_after_ingest: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

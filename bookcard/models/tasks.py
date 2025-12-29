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

"""Task management database models for Bookcard."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Index
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from bookcard.models.auth import User


class TaskStatus(StrEnum):
    """Task status enumeration.

    Attributes
    ----------
    PENDING : str
        Task is queued but not yet started.
    RUNNING : str
        Task is currently executing.
    COMPLETED : str
        Task completed successfully.
    FAILED : str
        Task failed with an error.
    CANCELLED : str
        Task was cancelled before completion.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(StrEnum):
    """Task type enumeration.

    Attributes
    ----------
    BOOK_UPLOAD : str
        Single book file upload task.
    MULTI_BOOK_UPLOAD : str
        Multiple book files upload task.
    BOOK_CONVERT : str
        Book format conversion task.
    EMAIL_SEND : str
        Email sending task.
    METADATA_BACKUP : str
        Metadata backup task.
    THUMBNAIL_GENERATE : str
        Thumbnail generation task.
    LIBRARY_SCAN : str
        Library scan task (scans authors, genres, series, and publishers).
    """

    BOOK_UPLOAD = "book_upload"
    MULTI_BOOK_UPLOAD = "multi_book_upload"
    BOOK_CONVERT = "book_convert"
    BOOK_STRIP_DRM = "book_strip_drm"
    EMAIL_SEND = "email_send"
    METADATA_BACKUP = "metadata_backup"
    THUMBNAIL_GENERATE = "thumbnail_generate"
    LIBRARY_SCAN = "library_scan"
    AUTHOR_METADATA_FETCH = "author_metadata_fetch"
    OPENLIBRARY_DUMP_DOWNLOAD = "openlibrary_dump_download"
    OPENLIBRARY_DUMP_INGEST = "openlibrary_dump_ingest"
    EPUB_FIX_SINGLE = "epub_fix_single"
    EPUB_FIX_BATCH = "epub_fix_batch"
    EPUB_FIX_DAILY_SCAN = "epub_fix_daily_scan"
    INGEST_DISCOVERY = "ingest_discovery"
    INGEST_BOOK = "ingest_book"
    PVR_DOWNLOAD_MONITOR = "pvr_download_monitor"
    PROWLARR_SYNC = "prowlarr_sync"
    INDEXER_HEALTH_CHECK = "indexer_health_check"


class Task(SQLModel, table=True):
    """Task model for tracking background job execution.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    task_type : TaskType
        Type of task being executed.
    status : TaskStatus
        Current status of the task.
    progress : float
        Progress of task completion (0.0 to 1.0).
    user_id : int
        Foreign key to user who created the task.
    created_at : datetime
        Task creation timestamp.
    started_at : datetime | None
        Task start timestamp.
    completed_at : datetime | None
        Task completion timestamp.
    cancelled_at : datetime | None
        Task cancellation timestamp.
    error_message : str | None
        Error message if task failed.
    task_data : dict | None
        JSON data for task-specific information (filename, filesize, etc.).
    """

    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    task_type: TaskType = Field(
        sa_column=Column(SQLEnum(TaskType, native_enum=False), nullable=False),  # type: ignore[call-overload]
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(SQLEnum(TaskStatus, native_enum=False), nullable=False),  # type: ignore[call-overload]
    )
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    task_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )

    # Relationships
    user: User = Relationship(back_populates="tasks")

    __table_args__ = (
        Index("idx_tasks_user_status", "user_id", "status"),
        Index("idx_tasks_type_created", "task_type", "created_at"),
    )

    @property
    def duration(self) -> float | None:
        """Calculate task duration in seconds.

        Returns
        -------
        float | None
            Duration in seconds, or None if task hasn't started.
        """
        if self.started_at is None:
            return None

        # Ensure timezone-aware datetimes for comparison
        started_at = self.started_at
        if started_at.tzinfo is None:
            # If naive, assume UTC
            started_at = started_at.replace(tzinfo=UTC)

        end_time = self.completed_at or self.cancelled_at or datetime.now(UTC)
        if end_time.tzinfo is None:
            # If naive, assume UTC
            end_time = end_time.replace(tzinfo=UTC)

        return (end_time - started_at).total_seconds()

    @property
    def is_complete(self) -> bool:
        """Check if task is in a terminal state.

        Returns
        -------
        bool
            True if task is completed, failed, or cancelled.
        """
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )


class TaskStatistics(SQLModel, table=True):
    """Task statistics model for tracking task type performance.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    task_type : TaskType
        Type of task.
    avg_duration : float | None
        Average duration in seconds.
    min_duration : float | None
        Minimum duration in seconds.
    max_duration : float | None
        Maximum duration in seconds.
    total_count : int
        Total number of tasks executed.
    success_count : int
        Number of successful tasks.
    failure_count : int
        Number of failed tasks.
    last_run_at : datetime | None
        Timestamp of last task execution.
    updated_at : datetime
        Last statistics update timestamp.
    """

    __tablename__ = "task_statistics"

    id: int | None = Field(default=None, primary_key=True)
    task_type: TaskType = Field(
        sa_column=Column(
            SQLEnum(TaskType, native_enum=False), nullable=False, unique=True
        ),  # type: ignore[call-overload]
    )
    avg_duration: float | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    total_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    last_run_at: datetime | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        index=True,
    )

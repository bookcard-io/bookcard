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

"""Metadata enforcement database models for Fundamental.

Tracks automatic enforcement of metadata and cover changes to ebook files.
"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from fundamental.models.auth import User
from fundamental.models.config import Library


class EnforcementStatus(StrEnum):
    """Metadata enforcement status enumeration.

    Attributes
    ----------
    PENDING : str
        Enforcement is queued but not yet started.
    IN_PROGRESS : str
        Enforcement is currently executing.
    COMPLETED : str
        Enforcement completed successfully.
    FAILED : str
        Enforcement failed with an error.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MetadataEnforcementOperation(SQLModel, table=True):
    """Metadata enforcement operation tracking.

    Tracks when metadata and cover changes are automatically enforced
    to ebook files (OPF files, cover images, and embedded metadata).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    book_id : int
        Calibre book ID that was enforced.
    library_id : int | None
        Library ID where the book belongs.
    user_id : int | None
        User ID who triggered the metadata update.
    status : EnforcementStatus
        Current status of the enforcement operation.
    enforced_at : datetime | None
        Timestamp when enforcement completed (or failed).
    error_message : str | None
        Error message if enforcement failed.
    opf_updated : bool
        Whether OPF file was successfully updated (default: False).
    cover_updated : bool
        Whether cover image was successfully updated (default: False).
    ebook_files_updated : bool
        Whether ebook files (EPUB, AZW3) were successfully updated (default: False).
    supported_formats : list[str] | None
        JSON array of supported formats that were processed.
    created_at : datetime
        Operation creation timestamp.
    updated_at : datetime
        Last update timestamp.
    library : Library | None
        Relationship to library.
    user : User | None
        Relationship to user.
    """

    __tablename__ = "metadata_enforcement_operations"

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(index=True)
    library_id: int | None = Field(
        default=None, foreign_key="libraries.id", index=True, nullable=True
    )
    user_id: int | None = Field(default=None, foreign_key="users.id", nullable=True)
    status: EnforcementStatus = Field(
        default=EnforcementStatus.PENDING,
        sa_column=Column(
            SQLEnum(EnforcementStatus, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    enforced_at: datetime | None = Field(default=None, index=True)
    error_message: str | None = Field(default=None)
    opf_updated: bool = Field(default=False)
    cover_updated: bool = Field(default=False)
    ebook_files_updated: bool = Field(default=False)
    supported_formats: list[str] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    library: Library | None = Relationship()
    user: User | None = Relationship()

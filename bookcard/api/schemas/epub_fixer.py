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

"""API schemas for EPUB fixer endpoints.

Pydantic models for request/response validation for EPUB fixer operations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

# Import at runtime for Pydantic validation, but linter prefers TYPE_CHECKING
from bookcard.models.epub_fixer import EPUBFixType  # noqa: TC001


class EPUBFixSingleRequest(BaseModel):
    """Request schema for single file EPUB fix.

    Attributes
    ----------
    file_path : str
        Path to EPUB file to fix.
    book_id : int | None
        Optional Calibre book ID.
    book_title : str | None
        Optional book title for audit trail.
    library_id : int | None
        Optional library ID.
    """

    file_path: str = Field(description="Path to EPUB file to fix")
    book_id: int | None = Field(default=None, description="Optional Calibre book ID")
    book_title: str | None = Field(default=None, description="Optional book title")
    library_id: int | None = Field(default=None, description="Optional library ID")


class EPUBFixBatchRequest(BaseModel):
    """Request schema for batch EPUB fix.

    Attributes
    ----------
    library_id : int | None
        Optional library ID to fix EPUBs in.
    """

    library_id: int | None = Field(default=None, description="Optional library ID")


class EPUBFixRead(BaseModel):
    """Response schema for individual EPUB fix.

    Attributes
    ----------
    id : int
        Fix record ID.
    run_id : int
        Fix run ID.
    book_id : int | None
        Calibre book ID.
    book_title : str
        Book title.
    file_path : str
        Path to fixed file.
    original_file_path : str | None
        Path to backup file if created.
    fix_type : EPUBFixType
        Type of fix applied.
    fix_description : str
        Description of the fix.
    file_name : str | None
        Name of file within EPUB that was fixed.
    original_value : str | None
        Original value before fix.
    fixed_value : str | None
        New value after fix.
    backup_created : bool
        Whether backup was created.
    created_at : datetime
        When fix was recorded.
    """

    id: int
    run_id: int
    book_id: int | None = None
    book_title: str
    file_path: str
    original_file_path: str | None = None
    fix_type: EPUBFixType
    fix_description: str
    file_name: str | None = None
    original_value: str | None = None
    fixed_value: str | None = None
    backup_created: bool
    created_at: datetime


class EPUBFixRunRead(BaseModel):
    """Response schema for EPUB fix run.

    Attributes
    ----------
    id : int
        Run ID.
    user_id : int | None
        User who triggered the fix.
    library_id : int | None
        Library ID.
    manually_triggered : bool
        Whether manually triggered.
    is_bulk_operation : bool
        Whether bulk operation.
    total_files_processed : int
        Total files processed.
    total_files_fixed : int
        Files that had fixes.
    total_fixes_applied : int
        Total fixes applied.
    backup_enabled : bool
        Whether backups enabled.
    started_at : datetime
        Start timestamp.
    completed_at : datetime | None
        Completion timestamp.
    cancelled_at : datetime | None
        Cancellation timestamp.
    error_message : str | None
        Error message if failed.
    created_at : datetime
        Creation timestamp.
    duration : float | None
        Duration in seconds.
    """

    id: int
    user_id: int | None = None
    library_id: int | None = None
    manually_triggered: bool
    is_bulk_operation: bool
    total_files_processed: int
    total_files_fixed: int
    total_fixes_applied: int
    backup_enabled: bool
    started_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    duration: float | None = None


class EPUBFixRunListResponse(BaseModel):
    """Response schema for paginated fix runs list.

    Attributes
    ----------
    items : list[EPUBFixRunRead]
        List of fix runs.
    total : int
        Total number of runs.
    page : int
        Current page number.
    page_size : int
        Items per page.
    total_pages : int
        Total number of pages.
    """

    items: list[EPUBFixRunRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class EPUBFixListResponse(BaseModel):
    """Response schema for fixes list.

    Attributes
    ----------
    items : list[EPUBFixRead]
        List of fixes.
    total : int
        Total number of fixes.
    """

    items: list[EPUBFixRead]
    total: int


class EPUBFixStatisticsRead(BaseModel):
    """Response schema for EPUB fix statistics.

    Attributes
    ----------
    total_runs : int
        Total number of fix runs.
    total_files_processed : int
        Total files processed.
    total_files_fixed : int
        Total files fixed.
    total_fixes_applied : int
        Total fixes applied.
    fixes_by_type : dict[EPUBFixType, int]
        Count of fixes by type.
    """

    total_runs: int
    total_files_processed: int
    total_files_fixed: int
    total_fixes_applied: int
    fixes_by_type: dict[EPUBFixType, int]


class EPUBFixResponse(BaseModel):
    """Response schema for fix operation.

    Attributes
    ----------
    task_id : int
        Task ID for the fix operation.
    message : str
        Success message.
    """

    task_id: int
    message: str


class EPUBFixRollbackResponse(BaseModel):
    """Response schema for rollback operation.

    Attributes
    ----------
    run_id : int
        Fix run ID that was rolled back.
    files_restored : int
        Number of files restored.
    message : str
        Success message.
    """

    run_id: int
    files_restored: int
    message: str

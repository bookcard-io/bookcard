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

"""Ingest management API schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from fundamental.models.ingest import IngestStatus  # noqa: TC001


class IngestConfigResponse(BaseModel):
    """Ingest configuration response."""

    model_config = ConfigDict(from_attributes=True)

    ingest_dir: str
    enabled: bool
    metadata_fetch_enabled: bool
    metadata_providers: list[str] | None = None
    metadata_merge_strategy: str
    metadata_priority_order: list[str] | None = None
    supported_formats: list[str] | None = None
    ignore_patterns: list[str] | None = None
    retry_max_attempts: int
    retry_backoff_seconds: int
    process_timeout_seconds: int
    auto_delete_after_ingest: bool
    created_at: datetime
    updated_at: datetime


class IngestConfigUpdate(BaseModel):
    """Payload to update ingest configuration."""

    ingest_dir: str | None = Field(default=None, description="Watch directory path")
    enabled: bool | None = Field(default=None, description="Whether ingest is enabled")
    metadata_fetch_enabled: bool | None = Field(
        default=None,
        description="Whether external metadata fetching is enabled during ingest",
    )
    metadata_providers: list[str] | None = Field(
        default=None, description="List of enabled provider IDs"
    )
    metadata_merge_strategy: str | None = Field(
        default=None, description="Metadata merge strategy"
    )
    metadata_priority_order: list[str] | None = Field(
        default=None, description="Provider priority order"
    )
    supported_formats: list[str] | None = Field(
        default=None, description="List of supported file extensions"
    )
    ignore_patterns: list[str] | None = Field(
        default=None, description="File patterns to ignore"
    )
    retry_max_attempts: int | None = Field(
        default=None, description="Maximum retry attempts"
    )
    retry_backoff_seconds: int | None = Field(
        default=None, description="Base backoff time in seconds"
    )
    process_timeout_seconds: int | None = Field(
        default=None, description="Timeout per book in seconds"
    )
    auto_delete_after_ingest: bool | None = Field(
        default=None, description="Delete source files after ingest"
    )


class IngestHistoryResponse(BaseModel):
    """Ingest history record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    status: IngestStatus
    book_id: int | None = None
    ingest_metadata: dict | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int
    user_id: int | None = None
    duration: float | None = None


class IngestHistoryListResponse(BaseModel):
    """Paginated ingest history list response."""

    items: list[IngestHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class IngestScanResponse(BaseModel):
    """Response for manual scan trigger."""

    task_id: int
    message: str


class IngestRetryResponse(BaseModel):
    """Response for retry operation."""

    message: str
    history_id: int

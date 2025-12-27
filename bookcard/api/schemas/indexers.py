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

"""API schemas for indexer management endpoints.

Pydantic models for request/response validation for indexer operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bookcard.models.pvr import IndexerProtocol, IndexerStatus, IndexerType


class IndexerCreate(BaseModel):
    """Request schema for creating an indexer.

    Attributes
    ----------
    name : str
        User-friendly name for the indexer.
    indexer_type : IndexerType
        Type of indexer (Torznab, Newznab, RSS, etc.).
    protocol : IndexerProtocol
        Protocol used (Torrent or Usenet).
    base_url : str
        Base URL of the indexer API.
    api_key : str | None
        API key for authentication.
    enabled : bool
        Whether this indexer is enabled (default True).
    priority : int
        Priority for search order (lower = higher priority, default 0).
    timeout_seconds : int
        Request timeout in seconds (default 30).
    retry_count : int
        Number of retries on failure (default 3).
    categories : list[int] | None
        List of category IDs to search (None = all categories).
    additional_settings : dict[str, Any] | None
        Indexer-specific settings.
    """

    name: str = Field(max_length=255, description="User-friendly name for the indexer")
    indexer_type: IndexerType = Field(description="Type of indexer")
    protocol: IndexerProtocol = Field(description="Protocol used (Torrent or Usenet)")
    base_url: str = Field(max_length=1000, description="Base URL of the indexer API")
    api_key: str | None = Field(
        default=None, max_length=500, description="API key for authentication"
    )
    enabled: bool = Field(default=True, description="Whether this indexer is enabled")
    priority: int = Field(
        default=0,
        ge=0,
        description="Priority for search order (lower = higher priority)",
    )
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    retry_count: int = Field(
        default=3, ge=0, le=10, description="Number of retries on failure"
    )
    categories: list[int] | None = Field(
        default=None,
        description="List of category IDs to search (None = all categories)",
    )
    additional_settings: dict[str, Any] | None = Field(
        default=None, description="Indexer-specific settings"
    )


class IndexerUpdate(BaseModel):
    """Request schema for updating an indexer.

    All fields are optional for partial updates.

    Attributes
    ----------
    name : str | None
        User-friendly name for the indexer.
    base_url : str | None
        Base URL of the indexer API.
    api_key : str | None
        API key for authentication.
    enabled : bool | None
        Whether this indexer is enabled.
    priority : int | None
        Priority for search order (lower = higher priority).
    timeout_seconds : int | None
        Request timeout in seconds.
    retry_count : int | None
        Number of retries on failure.
    categories : list[int] | None
        List of category IDs to search (None = all categories).
    additional_settings : dict[str, Any] | None
        Indexer-specific settings.
    """

    name: str | None = Field(
        default=None, max_length=255, description="User-friendly name for the indexer"
    )
    base_url: str | None = Field(
        default=None, max_length=1000, description="Base URL of the indexer API"
    )
    api_key: str | None = Field(
        default=None, max_length=500, description="API key for authentication"
    )
    enabled: bool | None = Field(
        default=None, description="Whether this indexer is enabled"
    )
    priority: int | None = Field(
        default=None,
        ge=0,
        description="Priority for search order (lower = higher priority)",
    )
    timeout_seconds: int | None = Field(
        default=None, ge=1, le=300, description="Request timeout in seconds"
    )
    retry_count: int | None = Field(
        default=None, ge=0, le=10, description="Number of retries on failure"
    )
    categories: list[int] | None = Field(
        default=None,
        description="List of category IDs to search (None = all categories)",
    )
    additional_settings: dict[str, Any] | None = Field(
        default=None, description="Indexer-specific settings"
    )


class IndexerRead(BaseModel):
    """Response schema for indexer data.

    Attributes
    ----------
    id : int
        Primary key identifier.
    name : str
        User-friendly name for the indexer.
    indexer_type : IndexerType
        Type of indexer.
    protocol : IndexerProtocol
        Protocol used.
    base_url : str
        Base URL of the indexer API.
    enabled : bool
        Whether this indexer is enabled.
    priority : int
        Priority for search order.
    timeout_seconds : int
        Request timeout in seconds.
    retry_count : int
        Number of retries on failure.
    categories : list[int] | None
        List of category IDs to search.
    additional_settings : dict[str, Any] | None
        Indexer-specific settings.
    status : IndexerStatus
        Current health status.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_query_at : datetime | None
        Timestamp of last successful query.
    error_count : int
        Number of consecutive errors.
    error_message : str | None
        Last error message if status is unhealthy.
    created_at : datetime
        Timestamp when indexer was added.
    updated_at : datetime
        Last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    indexer_type: IndexerType
    protocol: IndexerProtocol
    base_url: str
    enabled: bool
    priority: int
    timeout_seconds: int
    retry_count: int
    categories: list[int] | None
    additional_settings: dict[str, Any] | None
    status: IndexerStatus
    last_checked_at: datetime | None
    last_successful_query_at: datetime | None
    error_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class IndexerListResponse(BaseModel):
    """Response schema for listing indexers.

    Attributes
    ----------
    items : list[IndexerRead]
        List of indexers.
    total : int
        Total number of indexers.
    """

    items: list[IndexerRead]
    total: int


class IndexerTestResponse(BaseModel):
    """Response schema for indexer connection test.

    Attributes
    ----------
    success : bool
        Whether the connection test succeeded.
    message : str
        Test result message.
    """

    success: bool
    message: str


class IndexerStatusResponse(BaseModel):
    """Response schema for indexer status.

    Attributes
    ----------
    id : int
        Indexer ID.
    status : IndexerStatus
        Current health status.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_query_at : datetime | None
        Timestamp of last successful query.
    error_count : int
        Number of consecutive errors.
    error_message : str | None
        Last error message if status is unhealthy.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: IndexerStatus
    last_checked_at: datetime | None
    last_successful_query_at: datetime | None
    error_count: int
    error_message: str | None

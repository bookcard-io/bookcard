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

"""API schemas for download client management endpoints.

Pydantic models for request/response validation for download client operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bookcard.models.pvr import DownloadClientStatus, DownloadClientType


class DownloadClientCreate(BaseModel):
    """Request schema for creating a download client.

    Attributes
    ----------
    name : str
        User-friendly name for the download client.
    client_type : DownloadClientType
        Type of download client (qBittorrent, Transmission, etc.).
    host : str
        Hostname or IP address of the client.
    port : int
        Port number for the client API.
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication.
    use_ssl : bool
        Whether to use SSL/TLS (default False).
    enabled : bool
        Whether this client is enabled (default True).
    priority : int
        Priority for download assignment (lower = higher priority, default 0).
    timeout_seconds : int
        Request timeout in seconds (default 30).
    category : str | None
        Category/tag to assign to downloads (e.g., 'bookcard').
    download_path : str | None
        Path where client should save downloads.
    additional_settings : dict[str, Any] | None
        Client-specific settings.
    """

    name: str = Field(
        max_length=255, description="User-friendly name for the download client"
    )
    client_type: DownloadClientType = Field(description="Type of download client")
    host: str = Field(
        max_length=255, description="Hostname or IP address of the client"
    )
    port: int = Field(
        default=8080, ge=1, le=65535, description="Port number for the client API"
    )
    username: str | None = Field(
        default=None, max_length=255, description="Username for authentication"
    )
    password: str | None = Field(
        default=None, max_length=500, description="Password for authentication"
    )
    use_ssl: bool = Field(default=False, description="Whether to use SSL/TLS")
    enabled: bool = Field(default=True, description="Whether this client is enabled")
    priority: int = Field(
        default=0,
        ge=0,
        description="Priority for download assignment (lower = higher priority)",
    )
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    category: str | None = Field(
        default=None, max_length=100, description="Category/tag to assign to downloads"
    )
    download_path: str | None = Field(
        default=None,
        max_length=1000,
        description="Path where client should save downloads",
    )
    additional_settings: dict[str, Any] | None = Field(
        default=None, description="Client-specific settings"
    )


class DownloadClientUpdate(BaseModel):
    """Request schema for updating a download client.

    All fields are optional for partial updates.

    Attributes
    ----------
    name : str | None
        User-friendly name for the download client.
    host : str | None
        Hostname or IP address of the client.
    port : int | None
        Port number for the client API.
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication.
    use_ssl : bool | None
        Whether to use SSL/TLS.
    enabled : bool | None
        Whether this client is enabled.
    priority : int | None
        Priority for download assignment (lower = higher priority).
    timeout_seconds : int | None
        Request timeout in seconds.
    category : str | None
        Category/tag to assign to downloads.
    download_path : str | None
        Path where client should save downloads.
    additional_settings : dict[str, Any] | None
        Client-specific settings.
    """

    name: str | None = Field(
        default=None,
        max_length=255,
        description="User-friendly name for the download client",
    )
    host: str | None = Field(
        default=None, max_length=255, description="Hostname or IP address of the client"
    )
    port: int | None = Field(
        default=None, ge=1, le=65535, description="Port number for the client API"
    )
    username: str | None = Field(
        default=None, max_length=255, description="Username for authentication"
    )
    password: str | None = Field(
        default=None, max_length=500, description="Password for authentication"
    )
    use_ssl: bool | None = Field(default=None, description="Whether to use SSL/TLS")
    enabled: bool | None = Field(
        default=None, description="Whether this client is enabled"
    )
    priority: int | None = Field(
        default=None,
        ge=0,
        description="Priority for download assignment (lower = higher priority)",
    )
    timeout_seconds: int | None = Field(
        default=None, ge=1, le=300, description="Request timeout in seconds"
    )
    category: str | None = Field(
        default=None, max_length=100, description="Category/tag to assign to downloads"
    )
    download_path: str | None = Field(
        default=None,
        max_length=1000,
        description="Path where client should save downloads",
    )
    additional_settings: dict[str, Any] | None = Field(
        default=None, description="Client-specific settings"
    )


class DownloadClientRead(BaseModel):
    """Response schema for download client data.

    Attributes
    ----------
    id : int
        Primary key identifier.
    name : str
        User-friendly name for the download client.
    client_type : DownloadClientType
        Type of download client.
    host : str
        Hostname or IP address of the client.
    port : int
        Port number for the client API.
    enabled : bool
        Whether this client is enabled.
    priority : int
        Priority for download assignment.
    timeout_seconds : int
        Request timeout in seconds.
    category : str | None
        Category/tag to assign to downloads.
    download_path : str | None
        Path where client should save downloads.
    additional_settings : dict[str, Any] | None
        Client-specific settings.
    status : DownloadClientStatus
        Current health status.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_connection_at : datetime | None
        Timestamp of last successful connection.
    error_count : int
        Number of consecutive errors.
    error_message : str | None
        Last error message if status is unhealthy.
    created_at : datetime
        Timestamp when client was added.
    updated_at : datetime
        Last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_type: DownloadClientType
    host: str
    port: int
    enabled: bool
    priority: int
    timeout_seconds: int
    category: str | None
    download_path: str | None
    additional_settings: dict[str, Any] | None
    status: DownloadClientStatus
    last_checked_at: datetime | None
    last_successful_connection_at: datetime | None
    error_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DownloadClientListResponse(BaseModel):
    """Response schema for listing download clients.

    Attributes
    ----------
    items : list[DownloadClientRead]
        List of download clients.
    total : int
        Total number of download clients.
    """

    items: list[DownloadClientRead]
    total: int


class DownloadClientTestResponse(BaseModel):
    """Response schema for download client connection test.

    Attributes
    ----------
    success : bool
        Whether the connection test succeeded.
    message : str
        Test result message.
    """

    success: bool
    message: str


class DownloadClientStatusResponse(BaseModel):
    """Response schema for download client status.

    Attributes
    ----------
    id : int
        Download client ID.
    status : DownloadClientStatus
        Current health status.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_connection_at : datetime | None
        Timestamp of last successful connection.
    error_count : int
        Number of consecutive errors.
    error_message : str | None
        Last error message if status is unhealthy.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: DownloadClientStatus
    last_checked_at: datetime | None
    last_successful_connection_at: datetime | None
    error_count: int
    error_message: str | None


class DownloadItemResponse(BaseModel):
    """Response schema for download item.

    Attributes
    ----------
    client_item_id : str
        Unique identifier for the item in the download client.
    title : str
        Title of the release being downloaded.
    status : str
        Current download status.
    progress : float
        Download progress (0.0 to 1.0).
    size_bytes : int | None
        Total size of download in bytes.
    downloaded_bytes : int | None
        Bytes downloaded so far.
    download_speed_bytes_per_sec : float | None
        Current download speed.
    eta_seconds : int | None
        Estimated time to completion in seconds.
    file_path : str | None
        Path to downloaded file(s) when complete.
    """

    client_item_id: str
    title: str
    status: str
    progress: float
    size_bytes: int | None
    downloaded_bytes: int | None
    download_speed_bytes_per_sec: float | None
    eta_seconds: int | None
    file_path: str | None


class DownloadItemsResponse(BaseModel):
    """Response schema for listing download items.

    Attributes
    ----------
    items : list[DownloadItemResponse]
        List of download items.
    total : int
        Total number of download items.
    """

    items: list[DownloadItemResponse]
    total: int

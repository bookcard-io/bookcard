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

"""Settings classes for PVR indexers and download clients."""

from pydantic import BaseModel, Field


class IndexerSettings(BaseModel):
    """Base settings class for indexers.

    This is a base class that specific indexer implementations should extend
    with their own settings fields.

    Attributes
    ----------
    base_url : str
        Base URL of the indexer API.
    api_key : str | None
        API key for authentication.
    timeout_seconds : int
        Request timeout in seconds (default: 30).
    retry_count : int
        Number of retries on failure (default: 3).
    categories : list[int] | None
        List of category IDs to search (None = all categories).
    """

    base_url: str = Field(..., description="Base URL of the indexer API")
    api_key: str | None = Field(default=None, description="API key for authentication")
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


class DownloadClientSettings(BaseModel):
    """Base settings class for download clients.

    This is a base class that specific download client implementations should
    extend with their own settings fields.

    Attributes
    ----------
    host : str
        Hostname or IP address of the client.
    port : int
        Port number for the client API.
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication.
    use_ssl : bool
        Whether to use SSL/TLS (default: False).
    timeout_seconds : int
        Request timeout in seconds (default: 30).
    category : str | None
        Category/tag to assign to downloads.
    download_path : str | None
        Path where client should save downloads.
    """

    host: str = Field(..., description="Hostname or IP address of the client")
    port: int = Field(..., ge=1, le=65535, description="Port number for the client API")
    username: str | None = Field(
        default=None, description="Username for authentication"
    )
    password: str | None = Field(
        default=None, description="Password for authentication"
    )
    use_ssl: bool = Field(default=False, description="Whether to use SSL/TLS")
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    category: str | None = Field(
        default=None, description="Category/tag to assign to downloads"
    )
    download_path: str | None = Field(
        default=None, description="Path where client should save downloads"
    )

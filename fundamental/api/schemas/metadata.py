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

"""Metadata search API schemas and events."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fundamental.models.metadata import (
    MetadataRecord,  # noqa: TC001
    MetadataSourceInfo,  # noqa: TC001
)


class MetadataSearchRequest(BaseModel):
    """Metadata search request.

    Attributes
    ----------
    query : str
        Search query (title, author, ISBN, etc.).
    locale : str
        Locale code for localized results (default: 'en').
    max_results_per_provider : int
        Maximum results per provider (default: 10).
    provider_ids : list[str] | None
        List of provider IDs to search. If None, searches all enabled providers.
    enable_providers : list[str] | None
        List of provider names to enable. If empty or None, all available providers
        are enabled. Unknown provider names are ignored.
    """

    query: str = Field(..., min_length=1)
    locale: str = "en"
    max_results_per_provider: int = Field(default=10, ge=1, le=50)
    provider_ids: list[str] | None = None
    enable_providers: list[str] | None = None


class MetadataSearchResponse(BaseModel):
    """Metadata search response.

    Attributes
    ----------
    results : list[MetadataRecord]
        List of metadata records from all providers.
    """

    results: list[MetadataRecord] = Field(default_factory=list)


class MetadataProvidersResponse(BaseModel):
    """List of available metadata providers.

    Attributes
    ----------
    providers : list[MetadataSourceInfo]
        List of available metadata providers.
    """

    providers: list[MetadataSourceInfo] = Field(default_factory=list)


# =========================
# Metadata Search - Events
# =========================


class MetadataSearchEvent(BaseModel):
    """Base event in the metadata search stream."""

    event: str = Field(description="Event type discriminator")
    request_id: str = Field(description="Client-provided correlation/request ID")
    timestamp_ms: int = Field(description="Event timestamp in milliseconds since epoch")


class MetadataSearchStartedEvent(MetadataSearchEvent):
    """Emitted when a metadata search starts."""

    event: str = Field(default="search.started")
    query: str
    locale: str
    provider_ids: list[str]
    total_providers: int


class MetadataProviderStartedEvent(MetadataSearchEvent):
    """Emitted when a provider search starts."""

    event: str = Field(default="provider.started")
    provider_id: str
    provider_name: str


class MetadataProviderProgressEvent(MetadataSearchEvent):
    """Optional progress update from a provider (records discovered so far)."""

    event: str = Field(default="provider.progress")
    provider_id: str
    discovered: int = Field(ge=0, description="Number of candidate records discovered")


class MetadataProviderCompletedEvent(MetadataSearchEvent):
    """Emitted when a provider completes successfully."""

    event: str = Field(default="provider.completed")
    provider_id: str
    result_count: int = Field(ge=0)
    duration_ms: int = Field(ge=0)


class MetadataProviderFailedEvent(MetadataSearchEvent):
    """Emitted when a provider fails."""

    event: str = Field(default="provider.failed")
    provider_id: str
    error_type: str
    message: str


class MetadataSearchProgressEvent(MetadataSearchEvent):
    """Aggregated progress across providers."""

    event: str = Field(default="search.progress")
    providers_completed: int = Field(ge=0)
    providers_failed: int = Field(ge=0)
    total_providers: int = Field(ge=0)
    total_results_so_far: int = Field(ge=0)
    results: list[MetadataRecord] = Field(
        default_factory=list,
        description="Accumulated metadata records from completed providers",
    )


class MetadataSearchCompletedEvent(MetadataSearchEvent):
    """Emitted once the overall metadata search finishes."""

    event: str = Field(default="search.completed")
    total_results: int = Field(ge=0)
    providers_completed: int = Field(ge=0)
    providers_failed: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    results: list[MetadataRecord] = Field(
        default_factory=list,
        description="Aggregated metadata records from all providers",
    )

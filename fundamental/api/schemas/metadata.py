# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    """

    query: str = Field(..., min_length=1)
    locale: str = "en"
    max_results_per_provider: int = Field(default=10, ge=1, le=50)
    provider_ids: list[str] | None = None


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

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

"""Metadata endpoints: search for book metadata from external sources."""

from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from fundamental.api.schemas import (
    MetadataProvidersResponse,
    MetadataSearchEvent,
    MetadataSearchRequest,
    MetadataSearchResponse,
)
from fundamental.metadata.base import MetadataProviderError
from fundamental.services.metadata_service import MetadataService

if TYPE_CHECKING:
    from collections.abc import Iterator

router = APIRouter(prefix="/metadata", tags=["metadata"])


def _get_metadata_service() -> MetadataService:
    """Get metadata service instance.

    Returns
    -------
    MetadataService
        Metadata service instance.
    """
    return MetadataService()


@router.get("/providers", response_model=MetadataProvidersResponse)
def list_providers() -> MetadataProvidersResponse:
    """List all available metadata providers.

    Returns
    -------
    MetadataProvidersResponse
        List of available metadata providers.

    Examples
    --------
    >>> GET / metadata / providers
    {
        "providers": [
            {
                "id": "google",
                "name": "Google Books",
                "description": "Google Books API",
                "base_url": "https://books.google.com/"
            }
        ]
    }
    """
    service = _get_metadata_service()
    providers = service.list_providers()
    return MetadataProvidersResponse(providers=providers)


@router.post("/search", response_model=MetadataSearchResponse)
def search_metadata(request: MetadataSearchRequest) -> MetadataSearchResponse:
    """Search for book metadata across multiple providers.

    Parameters
    ----------
    request : MetadataSearchRequest
        Search request with query and optional filters.

    Returns
    -------
    MetadataSearchResponse
        Aggregated search results from all providers.

    Raises
    ------
    HTTPException
        If search fails (500) or invalid request (400).

    Examples
    --------
    >>> POST / metadata / search
    {
        "query": "The Great Gatsby",
        "locale": "en",
        "max_results_per_provider": 10
    }
    """
    try:
        service = _get_metadata_service()
        results = service.search(
            query=request.query,
            locale=request.locale,
            max_results_per_provider=request.max_results_per_provider,
            provider_ids=request.provider_ids,
        )
        return MetadataSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata search failed: {e!s}",
        ) from e


@router.get("/search", response_model=MetadataSearchResponse)
def search_metadata_get(
    query: str = Query(..., min_length=1, description="Search query"),
    locale: str = Query(default="en", description="Locale code"),
    max_results_per_provider: int = Query(
        default=10, ge=1, le=50, description="Max results per provider"
    ),
    provider_ids: str | None = Query(
        default=None, description="Comma-separated list of provider IDs"
    ),
) -> MetadataSearchResponse:
    """Search for book metadata (GET endpoint for convenience).

    Parameters
    ----------
    query : str
        Search query (title, author, ISBN, etc.).
    locale : str
        Locale code for localized results (default: 'en').
    max_results_per_provider : int
        Maximum results per provider (default: 10, max: 50).
    provider_ids : str | None
        Comma-separated list of provider IDs to search.

    Returns
    -------
    MetadataSearchResponse
        Aggregated search results from all providers.

    Raises
    ------
    HTTPException
        If search fails (500) or invalid request (400).

    Examples
    --------
    >>> GET /metadata/search?query=The+Great+Gatsby&locale=en
    """
    provider_id_list = None
    if provider_ids:
        provider_id_list = [pid.strip() for pid in provider_ids.split(",")]

    request = MetadataSearchRequest(
        query=query,
        locale=locale,
        max_results_per_provider=max_results_per_provider,
        provider_ids=provider_id_list,
    )

    return search_metadata(request)


@router.get("/search/stream")
def search_metadata_stream(
    query: str = Query(..., min_length=1, description="Search query"),
    locale: str = Query(default="en", description="Locale code"),
    max_results_per_provider: int = Query(
        default=10, ge=1, le=50, description="Max results per provider"
    ),
    provider_ids: str | None = Query(
        default=None, description="Comma-separated list of provider IDs"
    ),
    request_id: str | None = Query(
        default=None, description="Client-provided correlation ID for events"
    ),
) -> StreamingResponse:
    """Stream live metadata search events via Server-Sent Events (SSE).

    Parameters
    ----------
    query : str
        Search query (title, author, ISBN, etc.).
    locale : str
        Locale code (default 'en').
    max_results_per_provider : int
        Maximum results per provider (1-50).
    provider_ids : str | None
        Comma-separated provider IDs to search; if omitted searches all enabled.
    request_id : str | None
        Optional correlation ID; if omitted a UUIDv4 is generated.

    Returns
    -------
    StreamingResponse
        SSE stream of JSON-encoded progress events.
    """
    service = _get_metadata_service()

    provider_id_list = None
    if provider_ids:
        provider_id_list = [pid.strip() for pid in provider_ids.split(",")]

    rid = request_id or str(uuid.uuid4())

    # Thread-safe queue for events (str for serialized JSON) and sentinel None
    event_queue: queue.Queue[str | None] = queue.Queue()

    def _event_callback(event: MetadataSearchEvent) -> None:
        # Pydantic model -> dict -> json
        try:
            payload = json.dumps(event.model_dump())
        except (TypeError, ValueError, AttributeError) as e:
            # Fallback to string repr to avoid breaking the stream
            # These are the specific exceptions that json.dumps and model_dump can raise
            payload = json.dumps({
                "event": getattr(event, "event", "unknown"),
                "request_id": getattr(event, "request_id", rid),
                "timestamp_ms": int(time.time() * 1000),
                "message": f"Failed to serialize event payload: {e}",
            })
        # Put event payload
        event_queue.put(payload)
        # Close after overall completion
        if getattr(event, "event", "") == "search.completed":
            event_queue.put(None)

    def _worker() -> None:
        try:
            service.search(
                query=query,
                locale=locale,
                max_results_per_provider=max_results_per_provider,
                provider_ids=provider_id_list,
                request_id=rid,
                event_callback=_event_callback,
            )
        except (MetadataProviderError, ValueError, RuntimeError, OSError) as e:
            # Emit a terminal failure event and close
            # Catch specific exceptions that can occur during search
            fail_payload = json.dumps({
                "event": "search.failed",
                "request_id": rid,
                "timestamp_ms": int(time.time() * 1000),
                "error_type": type(e).__name__,
                "message": str(e),
            })
            event_queue.put(fail_payload)
            event_queue.put(None)

    # Start search in background thread
    t = threading.Thread(target=_worker, name="metadata-search-stream", daemon=True)
    t.start()

    def _sse_generator() -> Iterator[str]:
        # Optional: initial retry directive
        yield "retry: 2000\n\n"
        while True:
            item = event_queue.get()
            if item is None:
                break
            # SSE format: data: <json>\n\n
            yield f"data: {item}\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        _sse_generator(), media_type="text/event-stream", headers=headers
    )

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

"""Service layer for metadata fetching.

This service orchestrates multiple metadata providers to search for
and fetch book metadata from various sources.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import TYPE_CHECKING

from fundamental.api.schemas import (
    MetadataProviderCompletedEvent,
    MetadataProviderFailedEvent,
    MetadataProviderStartedEvent,
    MetadataSearchCompletedEvent,
    MetadataSearchEvent,
    MetadataSearchProgressEvent,
    MetadataSearchStartedEvent,
)
from fundamental.metadata.base import MetadataProviderError
from fundamental.metadata.registry import get_registry

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from fundamental.metadata.base import MetadataProvider
    from fundamental.metadata.registry import MetadataProviderRegistry
    from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for fetching book metadata from multiple sources.

    This service coordinates searches across multiple metadata providers,
    handling errors gracefully and aggregating results.

    Attributes
    ----------
    registry
        Metadata provider registry.
    max_workers : int
        Maximum number of concurrent provider searches.
    """

    def __init__(
        self,
        registry: MetadataProviderRegistry | None = None,
        max_workers: int = 5,
    ) -> None:
        """Initialize metadata service.

        Parameters
        ----------
        registry : MetadataProviderRegistry | None
            Provider registry. If None, uses global registry.
        max_workers : int
            Maximum number of concurrent provider searches (default: 5).
        """
        self.registry = registry or get_registry()
        self.max_workers = max_workers

    def _handle_provider_success(
        self,
        provider: MetadataProvider,
        results: Sequence[MetadataRecord],
        provider_start_times: dict[str, float],
        providers_completed: int,
        providers_failed: int,
        total_providers: int,
        all_results: list[MetadataRecord],
        request_id: str | None,
        _now_ms: Callable[[], int],
        _publish: Callable[[MetadataSearchEvent], None],
    ) -> int:
        """Handle successful provider search result.

        Parameters
        ----------
        provider : MetadataProvider
            Provider that completed successfully.
        results : Sequence[MetadataRecord]
            Search results from provider.
        provider_start_times : dict[str, float]
            Dictionary mapping provider IDs to start times.
        providers_completed : int
            Current count of completed providers.
        providers_failed : int
            Current count of failed providers.
        total_providers : int
            Total number of providers.
        all_results : list[MetadataRecord]
            Accumulated results list to extend.
        request_id : str | None
            Request correlation ID.
        _now_ms : Callable[[], int]
            Function to get current timestamp in milliseconds.
        _publish : Callable[[MetadataSearchEvent], None]
            Function to publish events.

        Returns
        -------
        int
            Updated count of completed providers.
        """
        all_results.extend(results)
        provider_id = provider.get_source_info().id
        logger.debug(
            "Provider %s returned %d results",
            provider_id,
            len(results),
        )
        info = provider.get_source_info()
        import time

        duration_ms = int(
            (time.monotonic() - provider_start_times.get(info.id, time.monotonic()))
            * 1000
        )
        providers_completed += 1
        _publish(
            MetadataProviderCompletedEvent(
                event="provider.completed",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                provider_id=info.id,
                result_count=len(results),
                duration_ms=duration_ms,
            )
        )
        _publish(
            MetadataSearchProgressEvent(
                event="search.progress",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                providers_completed=providers_completed,
                providers_failed=providers_failed,
                total_providers=total_providers,
                total_results_so_far=len(all_results),
            )
        )
        return providers_completed

    def _handle_provider_failure(
        self,
        provider: MetadataProvider,
        error: Exception,
        providers_completed: int,
        providers_failed: int,
        total_providers: int,
        all_results: list[MetadataRecord],
        request_id: str | None,
        _now_ms: Callable[[], int],
        _publish: Callable[[MetadataSearchEvent], None],
    ) -> int:
        """Handle failed provider search result.

        Parameters
        ----------
        provider : MetadataProvider
            Provider that failed.
        error : Exception
            Exception that was raised.
        providers_completed : int
            Current count of completed providers.
        providers_failed : int
            Current count of failed providers.
        total_providers : int
            Total number of providers.
        all_results : list[MetadataRecord]
            Accumulated results list.
        request_id : str | None
            Request correlation ID.
        _now_ms : Callable[[], int]
            Function to get current timestamp in milliseconds.
        _publish : Callable[[MetadataSearchEvent], None]
            Function to publish events.

        Returns
        -------
        int
            Updated count of failed providers.
        """
        provider_id = provider.get_source_info().id
        if isinstance(error, MetadataProviderError):
            logger.warning(
                "Provider %s search failed: %s",
                provider_id,
                error,
            )
        else:
            logger.error(
                "Unexpected error from provider %s: %s",
                provider_id,
                error,
                exc_info=error,
            )
        info = provider.get_source_info()
        providers_failed += 1
        _publish(
            MetadataProviderFailedEvent(
                event="provider.failed",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                provider_id=info.id,
                error_type=type(error).__name__,
                message=str(error),
            )
        )
        _publish(
            MetadataSearchProgressEvent(
                event="search.progress",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                providers_completed=providers_completed,
                providers_failed=providers_failed,
                total_providers=total_providers,
                total_results_so_far=len(all_results),
            )
        )
        return providers_failed

    def _initialize_providers(
        self,
        provider_ids: list[str] | None,
    ) -> list[MetadataProvider]:
        """Get list of providers to search.

        Parameters
        ----------
        provider_ids : list[str] | None
            List of provider IDs to search, or None for all enabled.

        Returns
        -------
        list[MetadataProvider]
            List of providers to search.
        """
        if provider_ids:
            providers = [
                self.registry.get_provider(pid)
                for pid in provider_ids
                if self.registry.get_provider(pid) is not None
            ]
        else:
            providers = list(self.registry.get_enabled_providers())
        return providers

    def _start_provider_searches(
        self,
        providers: list[MetadataProvider],
        query: str,
        locale: str,
        max_results_per_provider: int,
        provider_start_times: dict[str, float],
        request_id: str | None,
        _now_ms: Callable[[], int],
        _publish: Callable[[MetadataSearchEvent], None],
        executor: concurrent.futures.ThreadPoolExecutor,
    ) -> dict[concurrent.futures.Future, MetadataProvider]:
        """Start provider searches and return future mapping.

        Parameters
        ----------
        providers : list[MetadataProvider]
            List of providers to search.
        query : str
            Search query.
        locale : str
            Locale code.
        max_results_per_provider : int
            Maximum results per provider.
        provider_start_times : dict[str, float]
            Dictionary to store provider start times.
        request_id : str | None
            Request correlation ID.
        _now_ms : Callable[[], int]
            Function to get current timestamp.
        _publish : Callable[[MetadataSearchEvent], None]
            Function to publish events.
        executor : concurrent.futures.ThreadPoolExecutor
            Thread pool executor.

        Returns
        -------
        dict[concurrent.futures.Future, MetadataProvider]
            Mapping of futures to providers.
        """
        future_to_provider = {
            executor.submit(
                self._search_provider,
                provider,
                query,
                locale,
                max_results_per_provider,
            ): provider
            for provider in providers
        }

        # Mark provider started events
        import time

        for provider in providers:
            info = provider.get_source_info()
            provider_start_times[info.id] = time.monotonic()
            _publish(
                MetadataProviderStartedEvent(
                    event="provider.started",
                    request_id=request_id or "",
                    timestamp_ms=_now_ms(),
                    provider_id=info.id,
                    provider_name=info.name,
                )
            )
        return future_to_provider

    def search(
        self,
        query: str,
        locale: str = "en",
        max_results_per_provider: int = 10,
        provider_ids: list[str] | None = None,
        *,
        request_id: str | None = None,
        event_callback: Callable[[MetadataSearchEvent], None] | None = None,
    ) -> list[MetadataRecord]:
        """Search for books across multiple metadata providers.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code for localized results (default: 'en').
        max_results_per_provider : int
            Maximum results per provider (default: 10).
        provider_ids : list[str] | None
            List of provider IDs to search. If None, searches all enabled providers.
        request_id : str | None
            Optional correlation ID to include in emitted events.
        event_callback : Callable[[MetadataSearchEvent], None] | None
            Optional callback to receive progress events for live updates.

        Returns
        -------
        list[MetadataRecord]
            Aggregated list of metadata records from all providers.
        """
        if not query or not query.strip():
            return []

        # Get providers to search
        providers = self._initialize_providers(provider_ids)
        if not providers:
            logger.warning("No metadata providers available for search")
            return []

        # Event helpers
        def _now_ms() -> int:
            import time

            return int(time.time() * 1000)

        def _publish(event: MetadataSearchEvent) -> None:
            if event_callback is not None:
                try:
                    event_callback(event)
                except (RuntimeError, ValueError, TypeError) as e:
                    # Do not let event publishing affect search
                    # Catch specific exceptions that callbacks might raise
                    logger.debug(
                        "Event callback raised; ignoring: %s", e, exc_info=True
                    )

        import time

        overall_start = time.monotonic()
        total_providers = len(providers)
        requested_provider_ids = [p.get_source_info().id for p in providers]

        # Emit search started
        _publish(
            MetadataSearchStartedEvent(
                event="search.started",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                query=query,
                locale=locale,
                provider_ids=requested_provider_ids,
                total_providers=total_providers,
            )
        )

        # Search providers concurrently
        all_results: list[MetadataRecord] = []
        providers_completed = 0
        providers_failed = 0
        provider_start_times: dict[str, float] = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Start provider searches
            future_to_provider = self._start_provider_searches(
                providers=providers,
                query=query,
                locale=locale,
                max_results_per_provider=max_results_per_provider,
                provider_start_times=provider_start_times,
                request_id=request_id,
                _now_ms=_now_ms,
                _publish=_publish,
                executor=executor,
            )

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    results = future.result()
                    providers_completed = self._handle_provider_success(
                        provider=provider,
                        results=results,
                        provider_start_times=provider_start_times,
                        providers_completed=providers_completed,
                        providers_failed=providers_failed,
                        total_providers=total_providers,
                        all_results=all_results,
                        request_id=request_id,
                        _now_ms=_now_ms,
                        _publish=_publish,
                    )
                except (MetadataProviderError, RuntimeError, OSError, ValueError) as e:
                    providers_failed = self._handle_provider_failure(
                        provider=provider,
                        error=e,
                        providers_completed=providers_completed,
                        providers_failed=providers_failed,
                        total_providers=total_providers,
                        all_results=all_results,
                        request_id=request_id,
                        _now_ms=_now_ms,
                        _publish=_publish,
                    )

        overall_duration_ms = int((time.monotonic() - overall_start) * 1000)
        _publish(
            MetadataSearchCompletedEvent(
                event="search.completed",
                request_id=request_id or "",
                timestamp_ms=_now_ms(),
                total_results=len(all_results),
                providers_completed=providers_completed,
                providers_failed=providers_failed,
                duration_ms=overall_duration_ms,
                results=all_results,
            )
        )

        return all_results

    def _search_provider(
        self,
        provider: MetadataProvider,
        query: str,
        locale: str,
        max_results: int,
    ) -> Sequence[MetadataRecord]:
        """Search a single provider.

        Parameters
        ----------
        provider : MetadataProvider
            Provider to search.
        query : str
            Search query.
        locale : str
            Locale code.
        max_results : int
            Maximum results.

        Returns
        -------
        Sequence[MetadataRecord]
            Search results from provider.
        """
        try:
            return provider.search(query, locale=locale, max_results=max_results)
        except MetadataProviderError:
            # Re-raise provider errors
            raise
        except (RuntimeError, OSError, ValueError, TypeError) as e:
            # Wrap unexpected errors
            provider_id = provider.get_source_info().id
            msg = f"Unexpected error in provider {provider_id}: {e}"
            raise MetadataProviderError(msg) from e

    def list_providers(self) -> list[MetadataSourceInfo]:
        """List all available metadata providers.

        Returns
        -------
        list[MetadataSourceInfo]
            List of provider source information.
        """
        providers = list(self.registry.get_all_providers())
        return [provider.get_source_info() for provider in providers]

    def get_provider(self, provider_id: str) -> MetadataSourceInfo | None:
        """Get information about a specific provider.

        Parameters
        ----------
        provider_id : str
            Provider identifier.

        Returns
        -------
        MetadataSourceInfo | None
            Provider information if found, None otherwise.
        """
        provider = self.registry.get_provider(provider_id)
        if provider is None:
            return None
        return provider.get_source_info()

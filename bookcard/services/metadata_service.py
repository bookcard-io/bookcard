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

"""Service layer for metadata fetching.

This service orchestrates multiple metadata providers to search for
and fetch book metadata from various sources.
"""

from __future__ import annotations

import concurrent.futures
import logging
import threading  # noqa: TC003
import time
from typing import TYPE_CHECKING

from bookcard.api.schemas import (
    MetadataProviderCompletedEvent,
    MetadataProviderFailedEvent,
    MetadataProviderStartedEvent,
    MetadataSearchCompletedEvent,
    MetadataSearchEvent,
    MetadataSearchProgressEvent,
    MetadataSearchStartedEvent,
)
from bookcard.metadata.base import MetadataProviderError
from bookcard.metadata.registry import get_registry

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bookcard.metadata.base import MetadataProvider
    from bookcard.metadata.registry import MetadataProviderRegistry
    from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

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
                results=list(all_results),
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
                results=list(all_results),
            )
        )
        return providers_failed

    def _initialize_providers(
        self,
        provider_ids: list[str] | None,
        enable_providers: list[str] | None = None,
    ) -> list[MetadataProvider]:
        """Get list of providers to search.

        Parameters
        ----------
        provider_ids : list[str] | None
            List of provider IDs to search, or None for all enabled.
        enable_providers : list[str] | None
            List of provider names to enable. If None, all available
            providers are enabled. If empty list, no providers are enabled.
            Unknown provider names are ignored.

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
            # Only pass enable_providers if it's not None
            # Empty list means no providers should be enabled
            if enable_providers is not None:
                providers = list(self.registry.get_enabled_providers(enable_providers))
            else:
                providers = list(self.registry.get_enabled_providers(None))
        return providers

    def _cancel_pending_futures(
        self,
        future_to_provider: dict[concurrent.futures.Future, MetadataProvider],
    ) -> None:
        """Cancel all pending futures.

        Parameters
        ----------
        future_to_provider : dict[concurrent.futures.Future, MetadataProvider]
            Mapping of futures to providers.
        """
        for pending_future in future_to_provider:
            if not pending_future.done():
                pending_future.cancel()

    def _check_cancellation(
        self,
        cancellation_event: threading.Event | None,
        future_to_provider: dict[concurrent.futures.Future, MetadataProvider],
    ) -> bool:
        """Check if cancellation is requested and cancel pending futures.

        Parameters
        ----------
        cancellation_event : threading.Event | None
            Event to signal cancellation.
        future_to_provider : dict[concurrent.futures.Future, MetadataProvider]
            Mapping of futures to providers.

        Returns
        -------
        bool
            True if cancellation was requested, False otherwise.
        """
        if cancellation_event and cancellation_event.is_set():
            self._cancel_pending_futures(future_to_provider)
            logger.info("Search cancelled by client")
            return True
        return False

    def _wait_for_futures(
        self,
        futures: list[concurrent.futures.Future],
    ) -> set[concurrent.futures.Future]:
        """Wait for futures to complete with timeout.

        Parameters
        ----------
        futures : list[concurrent.futures.Future]
            List of futures to wait for.

        Returns
        -------
        set[concurrent.futures.Future]
            Set of completed futures.
        """
        try:
            done, _ = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning("Error waiting for futures: %s", e)
            return set()
        else:
            return done

    def _process_completed_future(
        self,
        future: concurrent.futures.Future,
        provider: MetadataProvider,
        provider_start_times: dict[str, float],
        total_providers: int,
        all_results: list[MetadataRecord],
        request_id: str | None,
        _now_ms: Callable[[], int],
        _publish: Callable[[MetadataSearchEvent], None],
        providers_completed: int,
        providers_failed: int,
    ) -> tuple[int, int]:
        """Process a single completed future.

        Parameters
        ----------
        future : concurrent.futures.Future
            Completed future to process.
        provider : MetadataProvider
            Provider that was searched.
        provider_start_times : dict[str, float]
            Dictionary mapping provider IDs to start times.
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
        providers_completed : int
            Current count of completed providers.
        providers_failed : int
            Current count of failed providers.

        Returns
        -------
        tuple[int, int]
            Updated (providers_completed, providers_failed) counts.
        """
        try:
            results = future.result(timeout=0)
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
        except concurrent.futures.CancelledError:
            logger.debug("Provider search cancelled: %s", provider.get_source_info().id)
            providers_failed += 1
        except concurrent.futures.TimeoutError:
            logger.debug("Timeout getting result for %s", provider.get_source_info().id)
            providers_failed += 1
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
        return providers_completed, providers_failed

    def _collect_provider_results(
        self,
        future_to_provider: dict[concurrent.futures.Future, MetadataProvider],
        provider_start_times: dict[str, float],
        total_providers: int,
        all_results: list[MetadataRecord],
        request_id: str | None,
        _now_ms: Callable[[], int],
        _publish: Callable[[MetadataSearchEvent], None],
        cancellation_event: threading.Event | None,
    ) -> tuple[int, int]:
        """Collect results from provider futures as they complete.

        Parameters
        ----------
        future_to_provider : dict[concurrent.futures.Future, MetadataProvider]
            Mapping of futures to providers.
        provider_start_times : dict[str, float]
            Dictionary mapping provider IDs to start times.
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
        cancellation_event : threading.Event | None
            Event to signal cancellation.

        Returns
        -------
        tuple[int, int]
            Tuple of (providers_completed, providers_failed).
        """
        providers_completed = 0
        providers_failed = 0

        # Use wait with timeout to check cancellation more frequently
        while future_to_provider:
            # Check for cancellation before waiting for next result
            if self._check_cancellation(cancellation_event, future_to_provider):
                return providers_completed, providers_failed

            # Wait for next completed future with timeout to allow cancellation checks
            done = self._wait_for_futures(list(future_to_provider.keys()))

            if not done:
                # No futures completed yet, check cancellation and continue
                if self._check_cancellation(cancellation_event, future_to_provider):
                    return providers_completed, providers_failed
                continue

            # Process completed futures
            for future in done:
                # Check cancellation again before processing
                if self._check_cancellation(cancellation_event, future_to_provider):
                    return providers_completed, providers_failed

                provider = future_to_provider.pop(future)
                providers_completed, providers_failed = self._process_completed_future(
                    future=future,
                    provider=provider,
                    provider_start_times=provider_start_times,
                    total_providers=total_providers,
                    all_results=all_results,
                    request_id=request_id,
                    _now_ms=_now_ms,
                    _publish=_publish,
                    providers_completed=providers_completed,
                    providers_failed=providers_failed,
                )

        return providers_completed, providers_failed

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
        cancellation_event: threading.Event | None = None,
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
                cancellation_event,
            ): provider
            for provider in providers
        }

        # Mark provider started events
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
        enable_providers: list[str] | None = None,
        *,
        request_id: str | None = None,
        event_callback: Callable[[MetadataSearchEvent], None] | None = None,
        cancellation_event: threading.Event | None = None,
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
        enable_providers : list[str] | None
            List of provider names to enable. If None, all available
            providers are enabled. If empty list, no providers are enabled.
            Unknown provider names are ignored.
        request_id : str | None
            Optional correlation ID to include in emitted events.
        event_callback : Callable[[MetadataSearchEvent], None] | None
            Optional callback to receive progress events for live updates.
        cancellation_event : threading.Event | None
            Optional event to signal cancellation. When set, pending searches
            will be cancelled.

        Returns
        -------
        list[MetadataRecord]
            Aggregated list of metadata records from all providers.
        """
        if not query or not query.strip():
            return []

        # Get providers to search
        providers = self._initialize_providers(provider_ids, enable_providers)
        if not providers:
            logger.warning("No metadata providers available for search")
            return []

        # Event helpers
        def _now_ms() -> int:
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
                cancellation_event=cancellation_event,
            )

            # Collect results as they complete
            providers_completed, providers_failed = self._collect_provider_results(
                future_to_provider=future_to_provider,
                provider_start_times=provider_start_times,
                total_providers=total_providers,
                all_results=all_results,
                request_id=request_id,
                _now_ms=_now_ms,
                _publish=_publish,
                cancellation_event=cancellation_event,
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
        cancellation_event: threading.Event | None = None,
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
        cancellation_event : threading.Event | None
            Event to signal cancellation. If set, search will be aborted.

        Returns
        -------
        Sequence[MetadataRecord]
            Search results from provider.

        Raises
        ------
        concurrent.futures.CancelledError
            If cancellation is requested.
        """
        # Check for cancellation before starting
        if cancellation_event and cancellation_event.is_set():
            msg = "Search cancelled before provider start"
            raise concurrent.futures.CancelledError(msg)

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

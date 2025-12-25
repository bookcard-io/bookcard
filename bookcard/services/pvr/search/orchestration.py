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

"""Concurrent search orchestration.

Handles concurrent execution of indexer searches with timeout and error handling.
"""

import concurrent.futures
import logging
import threading
from collections.abc import Callable

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Orchestrates concurrent indexer searches.

    Handles thread pool management, timeouts, and error recovery.
    """

    def __init__(self, max_workers: int = 5, timeout_seconds: int = 30) -> None:
        """Initialize search orchestrator.

        Parameters
        ----------
        max_workers : int
            Maximum number of concurrent searches.
        timeout_seconds : int
            Timeout per indexer search in seconds.

        Raises
        ------
        ValueError
            If max_workers or timeout_seconds is less than 1.
        """
        if max_workers < 1:
            msg = "max_workers must be positive"
            raise ValueError(msg)
        if timeout_seconds < 1:
            msg = "timeout_seconds must be positive"
            raise ValueError(msg)

        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds

    def execute_searches(
        self,
        search_tasks: list[tuple[IndexerDefinition, Callable[[], list[ReleaseInfo]]]],
        cancellation_event: threading.Event | None = None,
    ) -> list[tuple[IndexerDefinition, list[ReleaseInfo]]]:
        """Execute multiple indexer searches concurrently.

        Parameters
        ----------
        search_tasks : list[tuple[IndexerDefinition, Callable[[], list[ReleaseInfo]]]]
            List of (indexer, search_function) tuples.
        cancellation_event : threading.Event | None
            Event to signal cancellation.

        Returns
        -------
        list[tuple[IndexerDefinition, list[ReleaseInfo]]]
            List of (indexer, releases) tuples for successful searches.
            Failed searches are excluded from the result.
        """
        # Use dict with indexer ID as key to avoid hashability issues
        indexer_to_results: dict[int, list[ReleaseInfo]] = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_indexer = {
                executor.submit(search_func): indexer
                for indexer, search_func in search_tasks
            }

            # Collect results as they complete
            try:
                for future in concurrent.futures.as_completed(
                    future_to_indexer, timeout=self.timeout_seconds * len(search_tasks)
                ):
                    if cancellation_event and cancellation_event.is_set():
                        logger.info("Search cancelled")
                        break

                    indexer = future_to_indexer[future]
                    try:
                        releases = future.result(timeout=self.timeout_seconds)
                        if indexer.id is not None:
                            indexer_to_results[indexer.id] = releases
                    except concurrent.futures.TimeoutError:
                        logger.warning(
                            "Indexer search timed out: %s (id=%s)",
                            indexer.name,
                            indexer.id,
                        )
                    except PVRProviderError as e:
                        logger.warning(
                            "Indexer search failed: %s (id=%s): %s",
                            indexer.name,
                            indexer.id,
                            e,
                        )
                    except Exception:
                        logger.exception(
                            "Unexpected error searching indexer %s (id=%s)",
                            indexer.name,
                            indexer.id,
                        )
            except concurrent.futures.TimeoutError:
                # Overall timeout for as_completed - log and continue
                logger.warning(
                    "Overall search timeout reached for %d tasks", len(search_tasks)
                )

        # Convert to list of tuples using original indexer objects
        results: list[tuple[IndexerDefinition, list[ReleaseInfo]]] = []
        for indexer, _ in search_tasks:
            if indexer.id is not None and indexer.id in indexer_to_results:
                results.append((indexer, indexer_to_results[indexer.id]))

        return results

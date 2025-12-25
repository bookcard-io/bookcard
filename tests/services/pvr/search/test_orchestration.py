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

"""Tests for search orchestration."""

import threading
import time

import pytest

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.orchestration import SearchOrchestrator


class TestSearchOrchestrator:
    """Test SearchOrchestrator."""

    @pytest.mark.parametrize(
        ("max_workers", "timeout_seconds", "should_raise"),
        [
            (1, 30, False),
            (5, 30, False),
            (10, 60, False),
            (0, 30, True),  # Invalid
            (-1, 30, True),  # Invalid
            (5, 0, True),  # Invalid
            (5, -1, True),  # Invalid
        ],
    )
    def test_init_validation(
        self, max_workers: int, timeout_seconds: int, should_raise: bool
    ) -> None:
        """Test orchestrator initialization validation.

        Parameters
        ----------
        max_workers : int
            Maximum workers.
        timeout_seconds : int
            Timeout in seconds.
        should_raise : bool
            Whether ValueError should be raised.
        """
        if should_raise:
            with pytest.raises(ValueError, match="must be positive"):
                SearchOrchestrator(
                    max_workers=max_workers, timeout_seconds=timeout_seconds
                )
        else:
            orchestrator = SearchOrchestrator(
                max_workers=max_workers, timeout_seconds=timeout_seconds
            )
            assert orchestrator.max_workers == max_workers
            assert orchestrator.timeout_seconds == timeout_seconds

    def test_execute_searches_success(self, sample_indexer: IndexerDefinition) -> None:
        """Test successful search execution.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        orchestrator = SearchOrchestrator(max_workers=2, timeout_seconds=5)

        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
        )

        def search_func() -> list[ReleaseInfo]:
            return [release]

        search_tasks = [(sample_indexer, search_func)]

        results = orchestrator.execute_searches(search_tasks)

        assert len(results) == 1
        assert results[0][0] == sample_indexer
        assert len(results[0][1]) == 1
        assert results[0][1][0] == release

    def test_execute_searches_multiple(
        self,
        sample_indexer: IndexerDefinition,
        sample_indexer_high_priority: IndexerDefinition,
    ) -> None:
        """Test executing multiple searches.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        sample_indexer_high_priority
            High priority indexer.
        """
        orchestrator = SearchOrchestrator(max_workers=2, timeout_seconds=5)

        release1 = ReleaseInfo(
            title="Book 1",
            download_url="https://example.com/book1.torrent",
        )
        release2 = ReleaseInfo(
            title="Book 2",
            download_url="https://example.com/book2.torrent",
        )

        search_tasks = [
            (sample_indexer, lambda: [release1]),
            (sample_indexer_high_priority, lambda: [release2]),
        ]

        results = orchestrator.execute_searches(search_tasks)

        assert len(results) == 2
        result_indexers = {r[0].id for r in results}
        assert sample_indexer.id in result_indexers
        assert sample_indexer_high_priority.id in result_indexers

    def test_execute_searches_timeout(self, sample_indexer: IndexerDefinition) -> None:
        """Test search timeout handling.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        orchestrator = SearchOrchestrator(max_workers=1, timeout_seconds=1)

        def slow_search() -> list[ReleaseInfo]:
            time.sleep(2)  # Longer than timeout
            return [
                ReleaseInfo(
                    title="Test", download_url="https://example.com/book.torrent"
                )
            ]

        search_tasks = [(sample_indexer, slow_search)]

        # The overall timeout will be 1 second * 1 task = 1 second
        # The future timeout is also 1 second, so the overall timeout may fire first
        # Either way, the result should be empty
        results = orchestrator.execute_searches(search_tasks)

        # Timeout should result in empty results for that indexer
        result_indexers = {r[0].id for r in results if r[0].id is not None}
        assert sample_indexer.id not in result_indexers

    def test_execute_searches_error(self, sample_indexer: IndexerDefinition) -> None:
        """Test error handling during search.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        orchestrator = SearchOrchestrator(max_workers=1, timeout_seconds=5)

        def failing_search() -> list[ReleaseInfo]:
            raise PVRProviderError("Search failed")

        search_tasks = [(sample_indexer, failing_search)]

        results = orchestrator.execute_searches(search_tasks)

        # Error should result in empty results for that indexer
        result_indexers = {r[0].id for r in results}
        assert sample_indexer.id not in result_indexers

    def test_execute_searches_cancellation(
        self, sample_indexer: IndexerDefinition
    ) -> None:
        """Test cancellation handling.

        Parameters
        ----------
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        orchestrator = SearchOrchestrator(max_workers=1, timeout_seconds=10)

        cancellation_event = threading.Event()

        def slow_search() -> list[ReleaseInfo]:
            time.sleep(0.1)
            return [
                ReleaseInfo(
                    title="Test", download_url="https://example.com/book.torrent"
                )
            ]

        search_tasks = [(sample_indexer, slow_search)]

        # Set cancellation event before starting
        cancellation_event.set()

        results = orchestrator.execute_searches(search_tasks, cancellation_event)

        # Cancellation should stop processing
        assert len(results) == 0

    def test_execute_searches_empty_tasks(self) -> None:
        """Test execution with empty task list."""
        orchestrator = SearchOrchestrator(max_workers=1, timeout_seconds=5)

        results = orchestrator.execute_searches([])

        assert results == []

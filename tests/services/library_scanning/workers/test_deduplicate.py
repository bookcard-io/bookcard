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

"""Tests for DeduplicateWorker to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.library_scanning.workers.deduplicate import (
    DeduplicateWorker,
    NoOpDataSource,
)
from fundamental.services.messaging.base import MessageBroker
from fundamental.services.messaging.redis_broker import RedisBroker


@pytest.fixture
def mock_broker() -> MagicMock:
    """Create a mock message broker.

    Returns
    -------
    MagicMock
        Mock broker.
    """
    return MagicMock(spec=MessageBroker)


@pytest.fixture
def mock_redis_broker() -> MagicMock:
    """Create a mock RedisBroker.

    Returns
    -------
    MagicMock
        Mock Redis broker.
    """
    broker = MagicMock(spec=RedisBroker)
    broker.client = MagicMock()
    return broker


class TestNoOpDataSource:
    """Test NoOpDataSource class."""

    def test_search_author_returns_empty(
        self,
    ) -> None:
        """Test search_author returns empty list (covers line 60)."""
        source = NoOpDataSource()
        result = source.search_author("test")
        assert result == []

    def test_get_author_returns_none(
        self,
    ) -> None:
        """Test get_author returns None (covers line 75)."""
        source = NoOpDataSource()
        result = source.get_author("test")
        assert result is None

    def test_search_book_returns_empty(
        self,
    ) -> None:
        """Test search_book returns empty sequence (covers line 99)."""
        source = NoOpDataSource()
        result = source.search_book()
        assert result == []

    def test_get_book_returns_none(
        self,
    ) -> None:
        """Test get_book returns None (covers line 116)."""
        source = NoOpDataSource()
        result = source.get_book("test")
        assert result is None

    def test_name_property(
        self,
    ) -> None:
        """Test name property (covers line 127)."""
        source = NoOpDataSource()
        assert source.name == "noop"


class TestDeduplicateWorkerProcess:
    """Test DeduplicateWorker.process method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> DeduplicateWorker:
        """Create DeduplicateWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        DeduplicateWorker
            Worker instance.
        """
        with patch(
            "fundamental.services.library_scanning.workers.deduplicate.create_db_engine"
        ):
            return DeduplicateWorker(mock_broker)

    def test_process_invalid_payload(self, worker: DeduplicateWorker) -> None:
        """Test process() with invalid payload.

        Parameters
        ----------
        worker : DeduplicateWorker
            Worker instance.
        """
        payload = {}
        result = worker.process(payload)
        assert result is None

    @pytest.mark.parametrize(
        ("task_id", "is_cancelled", "library_exists", "stage_success"),
        [
            (None, False, True, True),
            (123, False, True, True),
            (123, True, True, True),
            (123, False, False, True),
            (123, False, True, False),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        is_cancelled: bool,
        library_exists: bool,
        stage_success: bool,
    ) -> None:
        """Test process() with various scenarios (covers lines 158-205).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        task_id : int | None
            Task ID.
        is_cancelled : bool
            Whether task is cancelled.
        library_exists : bool
            Whether library exists.
        stage_success : bool
            Whether stage succeeds.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.LibraryRepository"
            ) as mock_repo_class,
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.JobProgressTracker"
            ) as mock_progress_class,
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.DeduplicateStage"
            ) as mock_stage_class,
            patch(
                "fundamental.services.library_scanning.workers.deduplicate.ScanTaskTracker"
            ),
        ):
            worker = DeduplicateWorker(mock_redis_broker)

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_library_repo = mock_repo_class.return_value
            if library_exists:
                mock_library = MagicMock()
                mock_library_repo.get.return_value = mock_library
            else:
                mock_library_repo.get.return_value = None

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = is_cancelled

            mock_stage = mock_stage_class.return_value
            mock_result = MagicMock()
            mock_result.success = stage_success
            mock_result.message = "Success"
            mock_stage.execute.return_value = mock_result

            payload = {"library_id": 1, "task_id": task_id}

            if (is_cancelled and task_id) or not library_exists or not stage_success:
                result = worker.process(payload)
                assert result is None
            else:
                result = worker.process(payload)
                assert result is not None

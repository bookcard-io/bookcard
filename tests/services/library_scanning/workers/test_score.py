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

"""Tests for ScoreWorker to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.library_scanning.workers.score import (
    NoOpDataSource,
    ScoreWorker,
)
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker


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


class TestScoreWorkerNoOpDataSource:
    """Test NoOpDataSource in ScoreWorker module."""

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


class TestScoreWorkerProcess:
    """Test ScoreWorker.process method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> ScoreWorker:
        """Create ScoreWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        ScoreWorker
            Worker instance.
        """
        with patch("bookcard.services.library_scanning.workers.score.create_db_engine"):
            return ScoreWorker(mock_broker)

    def test_process_invalid_payload(self, worker: ScoreWorker) -> None:
        """Test process() with invalid payload.

        Parameters
        ----------
        worker : ScoreWorker
            Worker instance.
        """
        payload = {}
        result = worker.process(payload)
        assert result is None

    @pytest.mark.parametrize(
        ("task_id", "is_cancelled", "library_exists", "stage_success", "output_topic"),
        [
            (None, False, True, True, "completion_jobs"),
            (123, False, True, True, "completion_jobs"),
            (123, True, True, True, "completion_jobs"),
            (123, False, False, True, "completion_jobs"),
            (123, False, True, False, "completion_jobs"),
            (123, False, True, True, None),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        is_cancelled: bool,
        library_exists: bool,
        stage_success: bool,
        output_topic: str | None,
    ) -> None:
        """Test process() with various scenarios (covers lines 160-210).

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
        output_topic : str | None
            Output topic.
        """
        with (
            patch("bookcard.services.library_scanning.workers.score.create_db_engine"),
            patch(
                "bookcard.services.library_scanning.workers.score.get_session"
            ) as mock_get_session,
            patch(
                "bookcard.services.library_scanning.workers.score.LibraryRepository"
            ) as mock_repo_class,
            patch(
                "bookcard.services.library_scanning.workers.score.JobProgressTracker"
            ) as mock_progress_class,
            patch(
                "bookcard.services.library_scanning.workers.score.ScoreStage"
            ) as mock_stage_class,
            patch("bookcard.services.library_scanning.workers.score.ScanTaskTracker"),
        ):
            worker = ScoreWorker(
                mock_redis_broker,
                output_topic=output_topic
                if output_topic is not None
                else "completion_jobs",
            )
            # Override output_topic if we want to test None case
            if output_topic is None:
                worker.output_topic = None

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

            if (
                (is_cancelled and task_id)
                or not library_exists
                or not stage_success
                or not output_topic
            ):
                result = worker.process(payload)
                assert result is None
            else:
                result = worker.process(payload)
                assert result is not None

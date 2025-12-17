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

"""Tests for CrawlWorker to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.core import Author
from bookcard.services.library_scanning.workers.crawl import CrawlWorker
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


@pytest.fixture
def crawl_worker(mock_broker: MagicMock) -> CrawlWorker:
    """Create CrawlWorker instance.

    Parameters
    ----------
    mock_broker : MagicMock
        Mock broker.

    Returns
    -------
    CrawlWorker
        Worker instance.
    """
    return CrawlWorker(mock_broker)


class TestCrawlWorkerCheckTaskCancelled:
    """Test CrawlWorker._check_task_cancelled method."""

    def test_check_task_cancelled_with_redis_broker_cancelled(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _check_task_cancelled returns True when cancelled (covers lines 69-74).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        worker = CrawlWorker(mock_redis_broker)
        with patch(
            "bookcard.services.library_scanning.workers.crawl.JobProgressTracker"
        ) as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.is_cancelled.return_value = True
            result = worker._check_task_cancelled(123)
            assert result is True

    def test_check_task_cancelled_with_redis_broker_not_cancelled(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _check_task_cancelled returns False when not cancelled.

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        worker = CrawlWorker(mock_redis_broker)
        with patch(
            "bookcard.services.library_scanning.workers.crawl.JobProgressTracker"
        ) as mock_tracker_class:
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.is_cancelled.return_value = False
            result = worker._check_task_cancelled(123)
            assert result is False

    def test_check_task_cancelled_with_non_redis_broker(
        self, mock_broker: MagicMock
    ) -> None:
        """Test _check_task_cancelled returns False with non-Redis broker.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        worker = CrawlWorker(mock_broker)
        result = worker._check_task_cancelled(123)
        assert result is False


class TestCrawlWorkerProcess:
    """Test CrawlWorker.process method."""

    def test_process_invalid_payload(self, crawl_worker: CrawlWorker) -> None:
        """Test process() with invalid payload.

        Parameters
        ----------
        crawl_worker : CrawlWorker
            Worker instance.
        """
        payload = {}
        result = crawl_worker.process(payload)
        assert result is None

    def test_process_missing_library_id(self, crawl_worker: CrawlWorker) -> None:
        """Test process() with missing library_id.

        Parameters
        ----------
        crawl_worker : CrawlWorker
            Worker instance.
        """
        payload = {"calibre_db_path": "/path/to/db"}
        result = crawl_worker.process(payload)
        assert result is None

    def test_process_missing_db_path(self, crawl_worker: CrawlWorker) -> None:
        """Test process() with missing calibre_db_path.

        Parameters
        ----------
        crawl_worker : CrawlWorker
            Worker instance.
        """
        payload = {"library_id": 1}
        result = crawl_worker.process(payload)
        assert result is None

    @pytest.mark.parametrize(
        ("task_id", "has_authors", "is_cancelled"),
        [
            (None, True, False),
            (123, True, False),
            (123, False, False),
            (123, True, True),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        has_authors: bool,
        is_cancelled: bool,
    ) -> None:
        """Test process() with various scenarios (covers lines 89-156).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        task_id : int | None
            Task ID.
        has_authors : bool
            Whether to return authors.
        is_cancelled : bool
            Whether task is cancelled.
        """
        worker = CrawlWorker(mock_redis_broker)
        payload = {
            "library_id": 1,
            "calibre_db_path": "/path/to/db",
            "task_id": task_id,
        }

        mock_author = MagicMock(spec=Author)
        mock_author.model_dump.return_value = {"id": 1, "name": "Test Author"}

        with (
            patch(
                "bookcard.services.library_scanning.workers.crawl.CalibreBookRepository"
            ) as mock_repo_class,
            patch("bookcard.services.library_scanning.workers.crawl.ScanTaskTracker"),
            patch(
                "bookcard.services.library_scanning.workers.crawl.JobProgressTracker"
            ) as mock_progress_class,
        ):
            mock_repo = mock_repo_class.return_value
            mock_session = MagicMock()
            mock_repo.get_session.return_value.__enter__.return_value = mock_session

            if has_authors:
                mock_session.exec.return_value.all.return_value = [mock_author]
            else:
                mock_session.exec.return_value.all.return_value = []

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = is_cancelled

            if task_id and is_cancelled:
                result = worker.process(payload)
                assert result is None
            elif has_authors:
                result = worker.process(payload)
                assert result is None
                mock_redis_broker.publish.assert_called()
            else:
                result = worker.process(payload)
                assert result is None
                # Should publish to score_jobs when no authors
                score_calls = [
                    call
                    for call in mock_redis_broker.publish.call_args_list
                    if call[0][0] == "score_jobs"
                ]
                assert len(score_calls) > 0

    def test_process_exception_raises(self, mock_redis_broker: MagicMock) -> None:
        """Test process() raises exception on error.

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        worker = CrawlWorker(mock_redis_broker)
        payload = {
            "library_id": 1,
            "calibre_db_path": "/path/to/db",
        }

        with patch(
            "bookcard.services.library_scanning.workers.crawl.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo_class.side_effect = ValueError("Database error")

            with pytest.raises(ValueError, match="Database error"):
                worker.process(payload)

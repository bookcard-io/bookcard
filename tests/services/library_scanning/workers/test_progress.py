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

"""Tests for JobProgressTracker to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.messaging.redis_broker import RedisBroker


@pytest.fixture
def mock_redis_client() -> MagicMock:
    """Create a mock Redis client.

    Returns
    -------
    MagicMock
        Mock Redis client.
    """
    return MagicMock()


@pytest.fixture
def mock_broker(mock_redis_client: MagicMock) -> MagicMock:
    """Create a mock RedisBroker.

    Parameters
    ----------
    mock_redis_client : MagicMock
        Mock Redis client.

    Returns
    -------
    MagicMock
        Mock broker.
    """
    broker = MagicMock(spec=RedisBroker)
    broker.client = mock_redis_client
    return broker


@pytest.fixture
def tracker(mock_broker: MagicMock) -> JobProgressTracker:
    """Create JobProgressTracker instance.

    Parameters
    ----------
    mock_broker : MagicMock
        Mock broker.

    Returns
    -------
    JobProgressTracker
        Tracker instance.
    """
    return JobProgressTracker(mock_broker)


class TestJobProgressTrackerInit:
    """Test JobProgressTracker initialization."""

    def test_init_stores_broker_and_client(self, mock_broker: MagicMock) -> None:
        """Test __init__ stores broker and client.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.
        """
        tracker = JobProgressTracker(mock_broker)
        assert tracker.broker == mock_broker
        assert tracker.client == mock_broker.client
        assert tracker.prefix == "scan:progress"


class TestJobProgressTrackerKeyMethods:
    """Test JobProgressTracker key generation methods."""

    @pytest.mark.parametrize(
        ("library_id", "expected_suffix"),
        [
            (1, "1"),
            (123, "123"),
        ],
    )
    def test_get_total_key(
        self, tracker: JobProgressTracker, library_id: int, expected_suffix: str
    ) -> None:
        """Test _get_total_key (covers line 40).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        library_id : int
            Library ID.
        expected_suffix : str
            Expected suffix.
        """
        key = tracker._get_total_key(library_id)
        assert key == f"scan:progress:{library_id}:total"

    @pytest.mark.parametrize(
        "library_id",
        [1, 123],
    )
    def test_get_processed_key(
        self, tracker: JobProgressTracker, library_id: int
    ) -> None:
        """Test _get_processed_key (covers line 43).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        library_id : int
            Library ID.
        """
        key = tracker._get_processed_key(library_id)
        assert key == f"scan:progress:{library_id}:processed"

    @pytest.mark.parametrize(
        "library_id",
        [1, 123],
    )
    def test_get_task_id_key(
        self, tracker: JobProgressTracker, library_id: int
    ) -> None:
        """Test _get_task_id_key (covers line 46).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        library_id : int
            Library ID.
        """
        key = tracker._get_task_id_key(library_id)
        assert key == f"scan:progress:{library_id}:task_id"

    @pytest.mark.parametrize(
        ("library_id", "stage"),
        [
            (1, "match"),
            (1, "ingest"),
            (1, "link"),
            (123, "match"),
        ],
    )
    def test_get_stage_started_key(
        self, tracker: JobProgressTracker, library_id: int, stage: str
    ) -> None:
        """Test _get_stage_started_key (covers line 49).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        library_id : int
            Library ID.
        stage : str
            Stage name.
        """
        key = tracker._get_stage_started_key(library_id, stage)
        assert key == f"scan:progress:{library_id}:stage_started:{stage}"

    @pytest.mark.parametrize(
        "task_id",
        [1, 123],
    )
    def test_get_cancellation_key(
        self, tracker: JobProgressTracker, task_id: int
    ) -> None:
        """Test _get_cancellation_key (covers line 52).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        task_id : int
            Task ID.
        """
        key = tracker._get_cancellation_key(task_id)
        assert key == f"scan:progress:cancelled:{task_id}"


class TestJobProgressTrackerMarkStageStarted:
    """Test JobProgressTracker.mark_stage_started method."""

    @pytest.mark.parametrize(
        ("library_id", "stage", "was_set"),
        [
            (1, "match", True),
            (1, "ingest", True),
            (1, "link", False),
        ],
    )
    def test_mark_stage_started(
        self,
        tracker: JobProgressTracker,
        mock_redis_client: MagicMock,
        library_id: int,
        stage: str,
        was_set: bool,
    ) -> None:
        """Test mark_stage_started (covers lines 71-77).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        library_id : int
            Library ID.
        stage : str
            Stage name.
        was_set : bool
            Whether key was set.
        """
        mock_redis_client.setnx.return_value = 1 if was_set else 0
        result = tracker.mark_stage_started(library_id, stage)

        assert result == was_set
        mock_redis_client.setnx.assert_called_once()
        if was_set:
            mock_redis_client.expire.assert_called_once()


class TestJobProgressTrackerClearJob:
    """Test JobProgressTracker.clear_job method."""

    def test_clear_job_deletes_all_keys(
        self, tracker: JobProgressTracker, mock_redis_client: MagicMock
    ) -> None:
        """Test clear_job deletes all keys (covers lines 87-99).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        """
        library_id = 1
        tracker.clear_job(library_id)

        # Should delete total, processed, task_id, and stage keys
        assert mock_redis_client.delete.call_count == 1
        call_args = mock_redis_client.delete.call_args[0]
        assert len(call_args) == 6  # 3 main keys + 3 stage keys


class TestJobProgressTrackerInitializeJob:
    """Test JobProgressTracker.initialize_job method."""

    @pytest.mark.parametrize(
        ("total_items", "task_id"),
        [
            (10, None),
            (10, 123),
            (100, 456),
        ],
    )
    def test_initialize_job(
        self,
        tracker: JobProgressTracker,
        mock_redis_client: MagicMock,
        total_items: int,
        task_id: int | None,
    ) -> None:
        """Test initialize_job (covers lines 116-131).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        total_items : int
            Total items.
        task_id : int | None
            Task ID.
        """
        mock_pipeline = MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = []

        tracker.initialize_job(1, total_items, task_id)

        mock_redis_client.pipeline.assert_called_once()
        assert mock_pipeline.set.call_count >= 2
        assert mock_pipeline.expire.call_count >= 2


class TestJobProgressTrackerMarkItemProcessed:
    """Test JobProgressTracker.mark_item_processed method."""

    def test_mark_item_processed_complete(
        self, tracker: JobProgressTracker, mock_redis_client: MagicMock
    ) -> None:
        """Test mark_item_processed when job completes (covers lines 147-179).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        """
        library_id = 1
        total = 10
        mock_redis_client.get.return_value = str(total)
        mock_redis_client.incr.return_value = total

        result = tracker.mark_item_processed(library_id)

        assert result is True
        mock_redis_client.get.assert_called_once()
        mock_redis_client.incr.assert_called_once()
        # Should delete keys when complete
        assert mock_redis_client.delete.call_count >= 3

    def test_mark_item_processed_not_complete(
        self, tracker: JobProgressTracker, mock_redis_client: MagicMock
    ) -> None:
        """Test mark_item_processed when job not complete.

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        """
        library_id = 1
        total = 10
        mock_redis_client.get.return_value = str(total)
        mock_redis_client.incr.return_value = 5

        result = tracker.mark_item_processed(library_id)

        assert result is False
        mock_redis_client.delete.assert_not_called()

    def test_mark_item_processed_no_total(
        self, tracker: JobProgressTracker, mock_redis_client: MagicMock
    ) -> None:
        """Test mark_item_processed when total not found.

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        """
        library_id = 1
        mock_redis_client.get.return_value = None

        result = tracker.mark_item_processed(library_id)

        assert result is False
        mock_redis_client.incr.assert_not_called()


class TestJobProgressTrackerGetTaskId:
    """Test JobProgressTracker.get_task_id method."""

    @pytest.mark.parametrize(
        ("task_id_val", "expected"),
        [
            (b"123", 123),
            ("456", 456),
            (None, None),
        ],
    )
    def test_get_task_id(
        self,
        tracker: JobProgressTracker,
        mock_redis_client: MagicMock,
        task_id_val: bytes | str | None,
        expected: int | None,
    ) -> None:
        """Test get_task_id (covers lines 194-195).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        task_id_val : bytes | str | None
            Task ID value from Redis.
        expected : int | None
            Expected result.
        """
        mock_redis_client.get.return_value = task_id_val
        result = tracker.get_task_id(1)
        assert result == expected


class TestJobProgressTrackerIsCancelled:
    """Test JobProgressTracker.is_cancelled method."""

    @pytest.mark.parametrize(
        ("exists_result", "expected"),
        [
            (1, True),
            (0, False),
        ],
    )
    def test_is_cancelled(
        self,
        tracker: JobProgressTracker,
        mock_redis_client: MagicMock,
        exists_result: int,
        expected: bool,
    ) -> None:
        """Test is_cancelled (covers line 210).

        Parameters
        ----------
        tracker : JobProgressTracker
            Tracker instance.
        mock_redis_client : MagicMock
            Mock Redis client.
        exists_result : int
            Result from exists().
        expected : bool
            Expected result.
        """
        mock_redis_client.exists.return_value = exists_result
        result = tracker.is_cancelled(123)
        assert result == expected

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

"""Tests for IngestWorker to achieve 100% coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.author_metadata import AuthorMetadata
from fundamental.services.library_scanning.workers.ingest import IngestWorker
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


class TestIngestWorkerCheckCompletion:
    """Test IngestWorker._check_completion method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> IngestWorker:
        """Create IngestWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        IngestWorker
            Worker instance.
        """
        with patch(
            "fundamental.services.library_scanning.workers.ingest.create_db_engine"
        ):
            return IngestWorker(mock_broker)

    def test_check_completion_with_task_id(self, mock_redis_broker: MagicMock) -> None:
        """Test _check_completion with task_id (covers lines 91-100).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.ingest.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.ingest.JobProgressTracker"
            ) as mock_tracker_class,
        ):
            worker = IngestWorker(mock_redis_broker)
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.mark_item_processed.return_value = True
            worker._check_completion(1, 123)
            mock_redis_broker.publish.assert_called_once()

    def test_check_completion_without_task_id(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _check_completion without task_id (covers lines 94-95).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.ingest.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.ingest.JobProgressTracker"
            ) as mock_tracker_class,
        ):
            worker = IngestWorker(mock_redis_broker)
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.get_task_id.return_value = 456
            mock_tracker.mark_item_processed.return_value = True
            worker._check_completion(1, None)
            mock_tracker.get_task_id.assert_called_once_with(1)


class TestIngestWorkerProcess:
    """Test IngestWorker.process method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> IngestWorker:
        """Create IngestWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        IngestWorker
            Worker instance.
        """
        with patch(
            "fundamental.services.library_scanning.workers.ingest.create_db_engine"
        ):
            return IngestWorker(mock_broker)

    @pytest.mark.parametrize(
        (
            "task_id",
            "is_cancelled",
            "deserialize_error",
            "should_skip_fetch",
            "author_data",
            "fetch_error",
        ),
        [
            (None, False, False, False, None, False),
            (123, False, False, False, None, False),
            (123, True, False, False, None, False),
            (123, False, True, False, None, False),
            (123, False, False, True, None, False),
            (123, False, False, False, MagicMock(), False),
            (123, False, False, False, None, True),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        is_cancelled: bool,
        deserialize_error: bool,
        should_skip_fetch: bool,
        author_data: MagicMock | None,
        fetch_error: bool,
    ) -> None:
        """Test process() with various scenarios (covers lines 115-208).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        task_id : int | None
            Task ID.
        is_cancelled : bool
            Whether task is cancelled.
        deserialize_error : bool
            Whether deserialization fails.
        should_skip_fetch : bool
            Whether to skip fetch.
        author_data : MagicMock | None
            Author data to return.
        fetch_error : bool
            Whether fetch raises error.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.ingest.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.ingest.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.ingest.JobProgressTracker"
            ) as mock_progress_class,
            patch(
                "fundamental.services.library_scanning.workers.ingest.deserialize_match_result"
            ) as mock_deserialize,
            patch(
                "fundamental.services.library_scanning.workers.ingest.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.ingest.IngestStageFactory"
            ) as mock_factory,
        ):
            worker = IngestWorker(mock_redis_broker)

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = is_cancelled
            mock_progress_tracker.mark_item_processed.return_value = False

            if deserialize_error:
                mock_deserialize.side_effect = KeyError("Missing key")
            else:
                mock_match_result = MagicMock()
                mock_match_result.matched_entity.key = "OL123A"
                mock_match_result.matched_entity.name = "Test Author"
                mock_deserialize.return_value = mock_match_result

            mock_session.exec.return_value.first.return_value = None

            if should_skip_fetch:
                worker._should_skip_fetch = lambda *args: True  # type: ignore[method-assign]
            else:
                worker._should_skip_fetch = lambda *args: False  # type: ignore[method-assign]

            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_components = {
                "author_fetcher": MagicMock(),
                "ingestion_uow": MagicMock(),
            }
            mock_factory.create_components.return_value = mock_components

            if author_data:
                mock_components[
                    "author_fetcher"
                ].fetch_author.return_value = author_data
            else:
                mock_components["author_fetcher"].fetch_author.return_value = None

            if fetch_error:
                mock_components["author_fetcher"].fetch_author.side_effect = ValueError(
                    "Fetch error"
                )

            payload = {
                "match_result": {"test": "data"},
                "library_id": 1,
                "task_id": task_id,
            }

            if (is_cancelled and task_id) or deserialize_error:
                result = worker.process(payload)
                assert result is None
            elif should_skip_fetch:
                result = worker.process(payload)
                assert result == payload
            elif fetch_error:
                with pytest.raises(ValueError, match="Fetch error"):
                    worker.process(payload)
            elif author_data:
                result = worker.process(payload)
                assert result == payload
            else:
                result = worker.process(payload)
                assert result is None


class TestIngestWorkerLoadProviderConfig:
    """Test IngestWorker._load_provider_config method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> IngestWorker:
        """Create IngestWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        IngestWorker
            Worker instance.
        """
        with patch(
            "fundamental.services.library_scanning.workers.ingest.create_db_engine"
        ):
            return IngestWorker(mock_broker)

    def test_load_provider_config_found(self, worker: IngestWorker) -> None:
        """Test _load_provider_config when config found (covers lines 227-230).

        Parameters
        ----------
        worker : IngestWorker
            Worker instance.
        """
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_session.exec.return_value.first.return_value = mock_config
        result = worker._load_provider_config(mock_session, "openlibrary")
        assert result == mock_config

    def test_load_provider_config_not_found(self, worker: IngestWorker) -> None:
        """Test _load_provider_config when config not found.

        Parameters
        ----------
        worker : IngestWorker
            Worker instance.
        """
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        result = worker._load_provider_config(mock_session, "openlibrary")
        assert result is None


class TestIngestWorkerShouldSkipFetch:
    """Test IngestWorker._should_skip_fetch method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> IngestWorker:
        """Create IngestWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        IngestWorker
            Worker instance.
        """
        with patch(
            "fundamental.services.library_scanning.workers.ingest.create_db_engine"
        ):
            return IngestWorker(mock_broker)

    @pytest.mark.parametrize(
        (
            "stale_max_age",
            "stale_refresh_interval",
            "author_exists",
            "last_synced_at",
            "expected",
        ),
        [
            (None, None, False, None, False),
            (None, None, True, None, False),
            (30, None, False, None, False),
            (30, None, True, datetime.now(UTC) - timedelta(days=10), True),
            (30, None, True, datetime.now(UTC) - timedelta(days=40), False),
            (None, 7, True, datetime.now(UTC) - timedelta(days=3), True),
            (None, 7, True, datetime.now(UTC) - timedelta(days=10), False),
            (30, 7, True, datetime.now(UTC) - timedelta(days=3), True),
            (30, 7, True, datetime.now(UTC) - timedelta(days=10), True),
            (30, 7, True, datetime.now(UTC) - timedelta(days=40), False),
        ],
    )
    def test_should_skip_fetch(
        self,
        worker: IngestWorker,
        stale_max_age: int | None,
        stale_refresh_interval: int | None,
        author_exists: bool,
        last_synced_at: datetime | None,
        expected: bool,
    ) -> None:
        """Test _should_skip_fetch (covers lines 258-294).

        Parameters
        ----------
        worker : IngestWorker
            Worker instance.
        stale_max_age : int | None
            Max age in days.
        stale_refresh_interval : int | None
            Refresh interval in days.
        author_exists : bool
            Whether author exists.
        last_synced_at : datetime | None
            Last sync time.
        expected : bool
            Expected result.
        """
        mock_session = MagicMock()
        if author_exists:
            mock_author = MagicMock(spec=AuthorMetadata)
            mock_author.last_synced_at = last_synced_at
            mock_session.exec.return_value.first.return_value = mock_author
        else:
            mock_session.exec.return_value.first.return_value = None

        result = worker._should_skip_fetch(
            mock_session, "OL123A", stale_max_age, stale_refresh_interval
        )
        assert result == expected

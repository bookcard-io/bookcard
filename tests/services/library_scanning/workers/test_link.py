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

"""Tests for LinkWorker to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.library_scanning.workers.link import LinkWorker
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


class TestLinkWorkerCheckCompletion:
    """Test LinkWorker._check_completion method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> LinkWorker:
        """Create LinkWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        LinkWorker
            Worker instance.
        """
        with patch("bookcard.services.library_scanning.workers.link.create_db_engine"):
            return LinkWorker(mock_broker)

    def test_check_completion_with_task_id(self, mock_redis_broker: MagicMock) -> None:
        """Test _check_completion with task_id (covers lines 72-85).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        with (
            patch("bookcard.services.library_scanning.workers.link.create_db_engine"),
            patch(
                "bookcard.services.library_scanning.workers.link.JobProgressTracker"
            ) as mock_tracker_class,
            patch(
                "bookcard.services.library_scanning.workers.link.ScanTaskTracker"
            ) as mock_task_tracker_class,
        ):
            worker = LinkWorker(mock_redis_broker)
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.mark_item_processed.return_value = True
            mock_task_tracker = mock_task_tracker_class.return_value
            worker._check_completion(1, 123)
            mock_redis_broker.publish.assert_called_once()
            mock_task_tracker.update_stage_progress.assert_called_once()

    def test_check_completion_without_task_id(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _check_completion without task_id (covers lines 75-76).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        with (
            patch("bookcard.services.library_scanning.workers.link.create_db_engine"),
            patch(
                "bookcard.services.library_scanning.workers.link.JobProgressTracker"
            ) as mock_tracker_class,
            patch("bookcard.services.library_scanning.workers.link.ScanTaskTracker"),
        ):
            worker = LinkWorker(mock_redis_broker)
            mock_tracker = mock_tracker_class.return_value
            mock_tracker.get_task_id.return_value = 456
            mock_tracker.mark_item_processed.return_value = True
            worker._check_completion(1, None)
            mock_tracker.get_task_id.assert_called_once_with(1)


class TestLinkWorkerProcess:
    """Test LinkWorker.process method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> LinkWorker:
        """Create LinkWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        LinkWorker
            Worker instance.
        """
        with patch("bookcard.services.library_scanning.workers.link.create_db_engine"):
            return LinkWorker(mock_broker)

    def test_process_invalid_payload(self, worker: LinkWorker) -> None:
        """Test process() with invalid payload.

        Parameters
        ----------
        worker : LinkWorker
            Worker instance.
        """
        payload = {}
        result = worker.process(payload)
        assert result is None

    @pytest.mark.parametrize(
        (
            "task_id",
            "deserialize_error",
            "mapping_result",
            "output_topic",
            "mapping_error",
        ),
        [
            (None, False, None, None, False),
            (123, False, None, None, False),
            (123, True, None, None, False),
            (123, False, (MagicMock(), True), None, False),
            (123, False, (MagicMock(), False), None, False),
            (123, False, (MagicMock(), True), "output", False),
            (123, False, None, None, True),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        deserialize_error: bool,
        mapping_result: tuple[MagicMock, bool] | None,
        output_topic: str | None,
        mapping_error: bool,
    ) -> None:
        """Test process() with various scenarios (covers lines 100-166).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        task_id : int | None
            Task ID.
        deserialize_error : bool
            Whether deserialization fails.
        mapping_result : tuple[MagicMock, bool] | None
            Mapping result.
        output_topic : str | None
            Output topic.
        mapping_error : bool
            Whether mapping raises error.
        """
        with (
            patch("bookcard.services.library_scanning.workers.link.create_db_engine"),
            patch(
                "bookcard.services.library_scanning.workers.link.get_session"
            ) as mock_get_session,
            patch(
                "bookcard.services.library_scanning.workers.link.JobProgressTracker"
            ) as mock_progress_class,
            patch(
                "bookcard.services.library_scanning.workers.link.deserialize_match_result"
            ) as mock_deserialize,
            patch(
                "bookcard.services.library_scanning.workers.link.LinkStageFactory"
            ) as mock_factory,
            patch("bookcard.services.library_scanning.workers.link.ScanTaskTracker"),
        ):
            worker = LinkWorker(mock_redis_broker, output_topic=output_topic)

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.mark_stage_started.return_value = True
            mock_progress_tracker.mark_item_processed.return_value = False

            if deserialize_error:
                mock_deserialize.side_effect = ValueError("Deserialize error")
            else:
                mock_match_result = MagicMock()
                mock_match_result.matched_entity.name = "Test Author"
                mock_match_result.calibre_author_id = 1
                mock_deserialize.return_value = mock_match_result

            mock_components = {"mapping_service": MagicMock()}
            mock_factory.create_components.return_value = mock_components

            if mapping_error:
                mock_components[
                    "mapping_service"
                ].create_or_update_mapping.side_effect = ValueError("Mapping error")
            elif mapping_result:
                mock_components[
                    "mapping_service"
                ].create_or_update_mapping.return_value = mapping_result
            else:
                mock_components[
                    "mapping_service"
                ].create_or_update_mapping.return_value = None

            payload = {
                "match_result": {"test": "data"},
                "library_id": 1,
                "task_id": task_id,
            }

            if deserialize_error:
                result = worker.process(payload)
                assert result is None
            elif mapping_error:
                with pytest.raises(ValueError, match="Mapping error"):
                    worker.process(payload)
            elif mapping_result:
                result = worker.process(payload)
                if output_topic:
                    assert result == payload
                else:
                    assert result is None
            else:
                result = worker.process(payload)
                assert result is None

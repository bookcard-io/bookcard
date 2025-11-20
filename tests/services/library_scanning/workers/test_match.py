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

"""Tests for MatchWorker to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.workers.match import MatchWorker
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


class TestMatchWorkerProcess:
    """Test MatchWorker.process method."""

    @pytest.fixture
    def worker(self, mock_broker: MagicMock) -> MatchWorker:
        """Create MatchWorker instance.

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker.

        Returns
        -------
        MatchWorker
            Worker instance.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source
            return MatchWorker(mock_broker)

    def test_process_invalid_payload(self, worker: MatchWorker) -> None:
        """Test process() with invalid payload.

        Parameters
        ----------
        worker : MatchWorker
            Worker instance.
        """
        payload = {}
        result = worker.process(payload)
        assert result is None

    def test_process_validation_error(self, worker: MatchWorker) -> None:
        """Test process() with validation error.

        Parameters
        ----------
        worker : MatchWorker
            Worker instance.
        """
        payload = {"author": {"invalid": "data"}, "library_id": 1}
        result = worker.process(payload)
        assert result is None

    @pytest.mark.parametrize(
        ("task_id", "is_cancelled", "author_id", "should_skip", "match_result"),
        [
            (None, False, 1, False, None),
            (123, False, 1, False, None),
            (123, True, 1, False, None),
            (123, False, None, False, None),
            (123, False, 1, True, None),
            (123, False, 1, False, "has_match"),
        ],
    )
    def test_process_with_various_scenarios(
        self,
        mock_redis_broker: MagicMock,
        task_id: int | None,
        is_cancelled: bool,
        author_id: int | None,
        should_skip: bool,
        match_result: MagicMock | None,
    ) -> None:
        """Test process() with various scenarios (covers lines 94-100, 111-130, 145-207).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        task_id : int | None
            Task ID.
        is_cancelled : bool
            Whether task is cancelled.
        author_id : int | None
            Author ID.
        should_skip : bool
            Whether to skip match.
        match_result : str | None
            Match result indicator ("has_match" for a match, None for no match).
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.match.JobProgressTracker"
            ) as mock_progress_class,
            patch(
                "fundamental.services.library_scanning.workers.match.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.match.AuthorMappingRepository"
            ) as mock_mapping_repo_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(mock_redis_broker)

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = is_cancelled
            mock_progress_tracker.mark_item_processed.return_value = False

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value
            if should_skip:
                mock_mapping = MagicMock()
                mock_mapping.updated_at = None
                mock_mapping.created_at = MagicMock()
                mock_mapping.created_at.tzinfo = None
                mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                    mock_mapping
                )
            else:
                mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                    None
                )

            # Mock the orchestrator.match method
            if match_result == "has_match":
                # Create a real MatchResult instance for asdict() to work
                author_data_obj = AuthorData(
                    key="OL123A",
                    name="Test Author",
                )
                real_match_result = MatchResult(
                    confidence_score=0.9,
                    matched_entity=author_data_obj,
                    match_method="exact",
                )
                worker.orchestrator.match = MagicMock(return_value=real_match_result)  # type: ignore[assignment]
            else:
                worker.orchestrator.match = MagicMock(return_value=None)  # type: ignore[assignment]

            author_data = {"id": author_id, "name": "Test Author"}
            payload = {
                "author": author_data,
                "library_id": 1,
                "task_id": task_id,
            }

            if (is_cancelled and task_id) or author_id is None or should_skip:
                result = worker.process(payload)
                assert result is None
            elif match_result == "has_match":
                result = worker.process(payload)
                assert result is not None
                assert "match_result" in result
            else:
                result = worker.process(payload)
                assert result is None

    def test_process_exception_handling(self, mock_redis_broker: MagicMock) -> None:
        """Test process() exception handling.

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.match.JobProgressTracker"
            ) as mock_progress_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(mock_redis_broker)

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = False
            mock_progress_tracker.mark_item_processed.return_value = False

            worker.orchestrator.match = MagicMock(side_effect=ValueError("Match error"))  # type: ignore[assignment]

            payload = {
                "author": {"id": 1, "name": "Test Author"},
                "library_id": 1,
                "task_id": 123,
            }

            with pytest.raises(ValueError, match="Match error"):
                worker.process(payload)

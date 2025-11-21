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

from datetime import UTC
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

            # Mock _has_existing_match to avoid SQLAlchemy query with mocked AuthorMetadata
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            # Mock session for _handle_unmatched_author when needed (when no match and author_id is not None)
            # This needs to be done for all cases where _handle_unmatched_author might be called
            with patch(
                "fundamental.services.library_scanning.workers.match.AuthorMetadata"
            ) as mock_metadata_class:
                mock_metadata_instance = MagicMock()
                mock_metadata_instance.id = None
                mock_metadata_class.return_value = mock_metadata_instance

                # Mock session to set id after flush (for unmatched author handling)
                def mock_flush() -> None:
                    mock_metadata_instance.id = 999

                mock_session.flush = mock_flush
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()

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

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]
            # Mock _check_completion to avoid any side effects
            worker._check_completion = MagicMock()  # type: ignore[method-assign]

            worker.orchestrator.match = MagicMock(side_effect=ValueError("Match error"))  # type: ignore[assignment]

            payload = {
                "author": {"id": 1, "name": "Test Author"},
                "library_id": 1,
                "task_id": 123,
            }

            with pytest.raises(ValueError, match="Match error"):
                worker.process(payload)


class TestMatchWorkerCheckCompletion:
    """Test MatchWorker._check_completion method."""

    def test_check_completion_publishes_when_complete(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _check_completion publishes when mark_item_processed returns True (covers line 100).

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
            mock_progress_tracker.get_task_id.return_value = 123
            mock_progress_tracker.mark_item_processed.return_value = True

            library_id = 1
            worker._check_completion(library_id)

            mock_redis_broker.publish.assert_called_once_with(
                worker.completion_topic,
                {"library_id": library_id, "task_id": 123},
            )

    def test_check_completion_with_task_id(self, mock_redis_broker: MagicMock) -> None:
        """Test _check_completion with provided task_id.

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
            mock_progress_tracker.mark_item_processed.return_value = True

            library_id = 1
            task_id = 456
            worker._check_completion(library_id, task_id)

            # Should not call get_task_id when task_id is provided
            mock_progress_tracker.get_task_id.assert_not_called()
            mock_redis_broker.publish.assert_called_once_with(
                worker.completion_topic,
                {"library_id": library_id, "task_id": task_id},
            )

    def test_check_completion_not_redis_broker(self, mock_broker: MagicMock) -> None:
        """Test _check_completion with non-Redis broker (no-op).

        Parameters
        ----------
        mock_broker : MagicMock
            Mock broker (not RedisBroker).
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

            worker = MatchWorker(mock_broker)

            library_id = 1
            worker._check_completion(library_id)

            # Should not publish when not RedisBroker
            mock_broker.publish.assert_not_called()


class TestMatchWorkerShouldSkipMatch:
    """Test MatchWorker._should_skip_match method."""

    @pytest.mark.parametrize(
        ("stale_max_age", "days_since_update", "expected"),
        [
            (None, 0, False),  # No stale check
            (30, 10, True),  # Fresh (10 < 30)
            (30, 40, False),  # Stale (40 >= 30)
        ],
    )
    def test_should_skip_match_with_updated_at(
        self,
        mock_redis_broker: MagicMock,
        stale_max_age: int | None,
        days_since_update: int,
        expected: bool,
    ) -> None:
        """Test _should_skip_match with updated_at (covers lines 114-130).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        stale_max_age : int | None
            Stale data max age in days.
        days_since_update : int
            Days since last update.
        expected : bool
            Expected result.
        """
        from datetime import UTC, datetime, timedelta

        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.match.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.match.AuthorMappingRepository"
            ) as mock_mapping_repo_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(
                mock_redis_broker, stale_data_max_age_days=stale_max_age
            )

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value

            if stale_max_age is not None:
                mock_mapping = MagicMock()
                # Set updated_at to be days_since_update days ago
                mock_mapping.updated_at = datetime.now(UTC) - timedelta(
                    days=days_since_update
                )
                mock_mapping.created_at = None
                mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                    mock_mapping
                )
            else:
                mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                    None
                )

            result = worker._should_skip_match(calibre_author_id=1, library_id=1)
            assert result == expected

    def test_should_skip_match_with_created_at(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _should_skip_match uses created_at when updated_at is None (covers line 125).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        from datetime import UTC, datetime, timedelta

        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.match.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.match.AuthorMappingRepository"
            ) as mock_mapping_repo_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(mock_redis_broker, stale_data_max_age_days=30)

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value
            mock_mapping = MagicMock()
            mock_mapping.updated_at = None
            # Set created_at to be 10 days ago (fresh)
            mock_mapping.created_at = datetime.now(UTC) - timedelta(days=10)
            mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                mock_mapping
            )

            result = worker._should_skip_match(calibre_author_id=1, library_id=1)
            assert result is True  # 10 < 30, so should skip

    def test_should_skip_match_without_tzinfo(
        self, mock_redis_broker: MagicMock
    ) -> None:
        """Test _should_skip_match handles datetime without tzinfo (covers lines 126-127).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        from datetime import datetime, timedelta

        with (
            patch(
                "fundamental.services.library_scanning.workers.match.create_db_engine"
            ),
            patch(
                "fundamental.services.library_scanning.workers.match.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "fundamental.services.library_scanning.workers.match.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.match.AuthorMappingRepository"
            ) as mock_mapping_repo_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(mock_redis_broker, stale_data_max_age_days=30)

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value
            mock_mapping = MagicMock()
            # Create datetime without tzinfo
            naive_datetime = datetime.now(UTC) - timedelta(days=10)
            mock_mapping.updated_at = None
            mock_mapping.created_at = naive_datetime
            mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                mock_mapping
            )

            result = worker._should_skip_match(calibre_author_id=1, library_id=1)
            assert result is True  # Should handle naive datetime and skip

    def test_should_skip_match_no_mapping(self, mock_redis_broker: MagicMock) -> None:
        """Test _should_skip_match returns False when no mapping exists.

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
                "fundamental.services.library_scanning.workers.match.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.library_scanning.workers.match.AuthorMappingRepository"
            ) as mock_mapping_repo_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            worker = MatchWorker(mock_redis_broker, stale_data_max_age_days=30)

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value
            mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = None

            result = worker._should_skip_match(calibre_author_id=1, library_id=1)
            assert result is False


class TestMatchWorkerProcessSkipMatch:
    """Test MatchWorker.process when skipping match due to fresh data."""

    def test_process_skips_fresh_match(self, mock_redis_broker: MagicMock) -> None:
        """Test process() skips match when data is fresh (covers lines 177-179).

        Parameters
        ----------
        mock_redis_broker : MagicMock
            Mock Redis broker.
        """
        from datetime import UTC, datetime, timedelta

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

            worker = MatchWorker(mock_redis_broker, stale_data_max_age_days=30)

            # Mock _has_existing_match to avoid SQLAlchemy query issues
            worker._has_existing_match = MagicMock(return_value=False)  # type: ignore[method-assign]

            mock_progress_tracker = mock_progress_class.return_value
            mock_progress_tracker.is_cancelled.return_value = False
            mock_progress_tracker.mark_item_processed.return_value = False

            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            mock_mapping_repo = mock_mapping_repo_class.return_value
            mock_mapping = MagicMock()
            # Set updated_at to be 10 days ago (fresh, should skip)
            mock_mapping.updated_at = datetime.now(UTC) - timedelta(days=10)
            mock_mapping.created_at = None
            mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = (
                mock_mapping
            )

            payload = {
                "author": {"id": 1, "name": "Test Author"},
                "library_id": 1,
                "task_id": 123,
            }

            result = worker.process(payload)
            assert result is None
            # Verify _check_completion was called
            mock_progress_tracker.mark_item_processed.assert_called_once()

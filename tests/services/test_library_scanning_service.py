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

"""Tests for library scanning service to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from fundamental.models.config import Library
from fundamental.models.library_scanning import LibraryScanState
from fundamental.models.tasks import TaskType
from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_scanning_service import LibraryScanningService


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.exec.return_value.first.return_value = None
    return session


@pytest.fixture
def mock_library() -> MagicMock:
    """Create a mock library."""
    library = MagicMock(spec=Library)
    library.id = 1
    return library


@pytest.fixture
def mock_library_repo(mock_library: MagicMock) -> MagicMock:
    """Create a mock library repository."""
    repo = MagicMock(spec=LibraryRepository)
    repo.get.return_value = mock_library
    return repo


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock task runner."""
    runner = MagicMock()
    runner.enqueue.return_value = 123
    return runner


class TestLibraryScanningService:
    """Test LibraryScanningService."""

    def test_init_stores_session_and_runner(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test __init__ stores session and task runner."""
        service = LibraryScanningService(mock_session, mock_task_runner)

        assert service.session == mock_session
        assert service.task_runner == mock_task_runner
        assert isinstance(service.library_repo, LibraryRepository)

    def test_init_with_none_runner(self, mock_session: MagicMock) -> None:
        """Test __init__ with None task runner."""
        service = LibraryScanningService(mock_session, None)

        assert service.session == mock_session
        assert service.task_runner is None

    def test_scan_library_success(
        self,
        mock_session: MagicMock,
        mock_library_repo: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test scan_library successfully enqueues task."""
        mock_session.exec.return_value.first.return_value = None
        service = LibraryScanningService(mock_session, mock_task_runner)
        service.library_repo = mock_library_repo

        task_id = service.scan_library(library_id=1, user_id=1)

        assert task_id == 123
        mock_library_repo.get.assert_called_once_with(1)
        mock_task_runner.enqueue.assert_called_once_with(
            task_type=TaskType.LIBRARY_SCAN,
            payload={
                "library_id": 1,
                "data_source_config": {"name": "openlibrary", "kwargs": {}},
            },
            user_id=1,
        )

    def test_scan_library_with_custom_data_source(
        self,
        mock_session: MagicMock,
        mock_library_repo: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test scan_library with custom data source config."""
        mock_session.exec.return_value.first.return_value = None
        service = LibraryScanningService(mock_session, mock_task_runner)
        service.library_repo = mock_library_repo

        data_source_config = {"name": "custom_source", "kwargs": {"api_key": "test"}}
        task_id = service.scan_library(
            library_id=1, user_id=1, data_source_config=data_source_config
        )

        assert task_id == 123
        mock_task_runner.enqueue.assert_called_once_with(
            task_type=TaskType.LIBRARY_SCAN,
            payload={"library_id": 1, "data_source_config": data_source_config},
            user_id=1,
        )

    def test_scan_library_library_not_found(
        self,
        mock_session: MagicMock,
        mock_library_repo: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test scan_library raises ValueError when library not found."""
        mock_library_repo.get.return_value = None
        service = LibraryScanningService(mock_session, mock_task_runner)
        service.library_repo = mock_library_repo

        with pytest.raises(ValueError, match=r"Library 1 not found"):
            service.scan_library(library_id=1, user_id=1)

    def test_scan_library_no_task_runner(
        self,
        mock_session: MagicMock,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test scan_library raises ValueError when task runner is None."""
        service = LibraryScanningService(mock_session, None)
        service.library_repo = mock_library_repo

        with pytest.raises(ValueError, match=r"Task runner not available"):
            service.scan_library(library_id=1, user_id=1)

    def test_scan_library_updates_scan_state(
        self,
        mock_session: MagicMock,
        mock_library_repo: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test scan_library updates scan state."""
        mock_session.exec.return_value.first.return_value = None
        service = LibraryScanningService(mock_session, mock_task_runner)
        service.library_repo = mock_library_repo

        service.scan_library(library_id=1, user_id=1)

        # Verify scan state was updated
        assert mock_session.exec.call_count >= 1
        assert mock_session.commit.called

    def test_get_scan_state_found(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test get_scan_state returns state when found."""
        scan_state = LibraryScanState(
            library_id=1,
            scan_status="completed",
        )
        mock_session.exec.return_value.first.return_value = scan_state

        service = LibraryScanningService(mock_session, mock_task_runner)
        result = service.get_scan_state(1)

        assert result == scan_state
        mock_session.exec.assert_called_once()

    def test_get_scan_state_not_found(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test get_scan_state returns None when not found."""
        mock_session.exec.return_value.first.return_value = None

        service = LibraryScanningService(mock_session, mock_task_runner)
        result = service.get_scan_state(1)

        assert result is None

    def test_update_scan_state_existing(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test _update_scan_state updates existing state."""
        existing_state = LibraryScanState(
            library_id=1,
            scan_status="pending",
        )
        mock_session.exec.return_value.first.return_value = existing_state

        service = LibraryScanningService(mock_session, mock_task_runner)
        service._update_scan_state(1, "running")

        assert existing_state.scan_status == "running"
        assert existing_state.updated_at is not None
        mock_session.commit.assert_called_once()

    def test_update_scan_state_existing_completed(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test _update_scan_state sets last_scan_at when completed."""
        existing_state = LibraryScanState(
            library_id=1,
            scan_status="pending",
        )
        mock_session.exec.return_value.first.return_value = existing_state

        service = LibraryScanningService(mock_session, mock_task_runner)
        service._update_scan_state(1, "completed")

        assert existing_state.scan_status == "completed"
        assert existing_state.last_scan_at is not None
        assert existing_state.updated_at is not None

    def test_update_scan_state_new(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test _update_scan_state creates new state when not found."""
        mock_session.exec.return_value.first.return_value = None

        service = LibraryScanningService(mock_session, mock_task_runner)
        service._update_scan_state(1, "pending")

        # Verify new state was added
        mock_session.add.assert_called_once()
        added_state = mock_session.add.call_args[0][0]
        assert isinstance(added_state, LibraryScanState)
        assert added_state.library_id == 1
        assert added_state.scan_status == "pending"
        mock_session.commit.assert_called_once()

    def test_update_scan_state_with_task_id(
        self, mock_session: MagicMock, mock_task_runner: MagicMock
    ) -> None:
        """Test _update_scan_state with task_id parameter."""
        existing_state = LibraryScanState(
            library_id=1,
            scan_status="pending",
        )
        mock_session.exec.return_value.first.return_value = existing_state

        service = LibraryScanningService(mock_session, mock_task_runner)
        service._update_scan_state(1, "running", task_id=123)

        assert existing_state.scan_status == "running"
        mock_session.commit.assert_called_once()

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

"""Tests for LibraryScanTask to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.tasks.library_scan_task import LibraryScanTask


@pytest.fixture
def worker_context() -> dict[str, MagicMock]:
    """Return mock worker context."""
    update_progress = MagicMock()
    return {
        "session": MagicMock(),
        "task_service": MagicMock(),
        "update_progress": update_progress,
    }


@pytest.fixture
def metadata() -> dict[str, int]:
    """Return task metadata with library_id."""
    return {"library_id": 1}


class TestLibraryScanTaskInit:
    """Test LibraryScanTask initialization."""

    def test_init_sets_library_id(self, metadata: dict[str, int]) -> None:
        """Test __init__ sets library_id from metadata."""
        task = LibraryScanTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.library_id == 1

    def test_init_missing_library_id(self) -> None:
        """Test __init__ raises ValueError when library_id missing."""
        with pytest.raises(ValueError, match="library_id is required in task metadata"):
            LibraryScanTask(
                task_id=1,
                user_id=1,
                metadata={},
            )

    def test_init_with_data_source_config(self) -> None:
        """Test __init__ sets data source configuration."""
        metadata = {
            "library_id": 1,
            "data_source_config": {
                "name": "custom_source",
                "kwargs": {"api_key": "test"},
            },
        }
        task = LibraryScanTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.library_id == 1
        assert task.data_source_name == "custom_source"
        assert task.data_source_kwargs == {"api_key": "test"}

    def test_init_default_data_source(self) -> None:
        """Test __init__ uses default data source when not specified."""
        metadata = {"library_id": 1}
        task = LibraryScanTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.data_source_name == "openlibrary"
        assert task.data_source_kwargs == {}


class TestLibraryScanTaskRun:
    """Test LibraryScanTask run method."""

    @pytest.fixture
    def task(self, metadata: dict[str, int]) -> LibraryScanTask:
        """Create LibraryScanTask instance."""
        return LibraryScanTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

    def test_run_success(
        self,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run successfully executes library scan."""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.return_value = {"success": True}
        task.orchestrator = mock_orchestrator

        task.run(worker_context)

        # Verify orchestrator was called
        mock_orchestrator.scan_library.assert_called_once()

    @patch("fundamental.services.tasks.library_scan_task.LibraryRepository")
    def test_run_library_not_found(
        self,
        mock_repo_class: MagicMock,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run raises ValueError when library not found."""
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo.get.return_value = None
        mock_repo_class.return_value = mock_library_repo

        # Setup mock orchestrator that will raise ValueError
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.side_effect = ValueError("Library 1 not found")
        task.orchestrator = mock_orchestrator

        with pytest.raises(ValueError, match=r"Library .* not found"):
            task.run(worker_context)

    @patch("fundamental.services.tasks.library_scan_task.LibraryRepository")
    def test_run_library_id_none(
        self,
        mock_repo_class: MagicMock,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run raises ValueError when library_id is None."""
        # Create a new task with None library_id by bypassing __init__ validation
        # We'll create it with invalid metadata that gets set to None
        task = LibraryScanTask.__new__(LibraryScanTask)
        task.task_id = 1
        task.user_id = 1
        task.metadata = {}
        task.library_id = None
        task.data_source_name = "openlibrary"
        task.data_source_kwargs = {}
        with pytest.raises(ValueError, match="library_id is required"):
            task.run(worker_context)

    def test_run_with_failure_result(
        self,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run handles failure result from executor."""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.return_value = {
            "success": False,
            "message": "Test error",
        }
        task.orchestrator = mock_orchestrator

        # Should not raise, just log warning
        task.run(worker_context)

        # Verify orchestrator was called
        mock_orchestrator.scan_library.assert_called_once()

    def test_run_exception(
        self,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run raises exception on error."""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.side_effect = ValueError("Test error")
        task.orchestrator = mock_orchestrator

        with pytest.raises(ValueError, match="Test error"):
            task.run(worker_context)

    def test_run_calls_progress_callback(
        self,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run sets up progress callback."""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.return_value = {"success": True}
        task.orchestrator = mock_orchestrator

        task.run(worker_context)

        # Verify orchestrator was called with progress_callback
        mock_orchestrator.scan_library.assert_called_once()
        call_kwargs = mock_orchestrator.scan_library.call_args[1]
        assert "progress_callback" in call_kwargs

        # Verify progress callback calls update_progress
        progress_callback = call_kwargs["progress_callback"]
        progress_callback(0.5, {"stage": "test"})
        worker_context["update_progress"].assert_called_with(0.5, {"stage": "test"})

    def test_run_no_update_progress(
        self,
        task: LibraryScanTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run handles missing update_progress in context."""
        # Setup mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan_library.return_value = {"success": True}
        task.orchestrator = mock_orchestrator

        # Remove update_progress from context
        worker_context.pop("update_progress", None)

        task.run(worker_context)

        # Should still work without update_progress
        mock_orchestrator.scan_library.assert_called_once()

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

"""Tests for OpenLibraryDumpIngestTask to achieve 100% coverage."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.tasks.openlibrary.task import OpenLibraryDumpIngestTask


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock SQLModel session."""
    return MagicMock()


@pytest.fixture
def mock_update_progress() -> MagicMock:
    """Create a mock update_progress callback."""
    return MagicMock()


@pytest.fixture
def worker_context(
    mock_session: MagicMock, mock_update_progress: MagicMock
) -> dict[str, Any]:
    """Create worker context dictionary.

    Parameters
    ----------
    mock_session : MagicMock
        Mock session object.
    mock_update_progress : MagicMock
        Mock update_progress callback.

    Returns
    -------
    dict[str, Any]
        Worker context dictionary.
    """
    return {
        "session": mock_session,
        "update_progress": mock_update_progress,
    }


@pytest.fixture
def base_metadata() -> dict[str, Any]:
    """Create base metadata dictionary.

    Returns
    -------
    dict[str, Any]
        Base metadata dictionary.
    """
    return {"data_directory": "/test/data"}


@pytest.mark.parametrize(
    (
        "data_directory",
        "batch_size",
        "process_authors",
        "process_works",
        "process_editions",
    ),
    [
        ("/test/data", 10000, True, True, True),
        ("/custom/path", 5000, False, True, False),
        ("/data", 20000, True, False, True),
    ],
)
class TestOpenLibraryDumpIngestTaskInit:
    """Test OpenLibraryDumpIngestTask initialization."""

    def test_init_with_metadata(
        self,
        data_directory: str,
        batch_size: int,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
    ) -> None:
        """Test __init__ with various metadata configurations.

        Parameters
        ----------
        data_directory : str
            Data directory path.
        batch_size : int
            Batch size for processing.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        """
        metadata: dict[str, Any] = {
            "data_directory": data_directory,
            "batch_size": batch_size,
            "process_authors": process_authors,
            "process_works": process_works,
            "process_editions": process_editions,
        }
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.config.data_directory == data_directory
        assert task.config.batch_size == batch_size
        assert task.config.process_authors == process_authors
        assert task.config.process_works == process_works
        assert task.config.process_editions == process_editions

    def test_init_with_defaults(
        self,
        data_directory: str,
        batch_size: int,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
    ) -> None:
        """Test __init__ with partial metadata using defaults.

        Parameters
        ----------
        data_directory : str
            Data directory path.
        batch_size : int
            Batch size for processing.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        """
        metadata: dict[str, Any] = {"data_directory": data_directory}
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.config.data_directory == data_directory
        assert task.config.batch_size == 10000  # default
        assert task.config.process_authors is True  # default
        assert task.config.process_works is True  # default
        assert task.config.process_editions is True  # default


class TestOpenLibraryDumpIngestTaskRun:
    """Test OpenLibraryDumpIngestTask run method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create OpenLibraryDumpIngestTask instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @patch(
        "fundamental.services.tasks.openlibrary.task.OpenLibraryDumpIngestOrchestrator"
    )
    def test_run_success(
        self,
        mock_orchestrator_class: MagicMock,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test successful run execution.

        Parameters
        ----------
        mock_orchestrator_class : MagicMock
            Mock orchestrator class.
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator

        task.run(worker_context)

        mock_orchestrator_class.assert_called_once()
        mock_orchestrator.run.assert_called_once()

    @patch(
        "fundamental.services.tasks.openlibrary.task.OpenLibraryDumpIngestOrchestrator"
    )
    def test_run_with_exception(
        self,
        mock_orchestrator_class: MagicMock,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
        mock_session: MagicMock,
    ) -> None:
        """Test run with exception triggers rollback.

        Parameters
        ----------
        mock_orchestrator_class : MagicMock
            Mock orchestrator class.
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        mock_session : MagicMock
            Mock session object.
        """
        mock_orchestrator = MagicMock()
        mock_orchestrator.run.side_effect = Exception("Test error")
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock the repository adapter
        with patch(
            "fundamental.services.tasks.openlibrary.task.DatabaseRepositoryAdapter"
        ) as mock_repo_adapter_class:
            mock_repo_adapter = MagicMock()
            mock_repo_adapter_class.return_value = mock_repo_adapter

            with pytest.raises(Exception, match="Test error"):
                task.run(worker_context)

            mock_repo_adapter.rollback.assert_called_once()

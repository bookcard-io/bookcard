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

"""Tests for AuthorMetadataFetchTask to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.tasks.author_metadata_fetch_task import (
    AuthorMetadataFetchTask,
)


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
def metadata() -> dict[str, str]:
    """Return task metadata with author_id."""
    return {"author_id": "OL123A"}


class TestAuthorMetadataFetchTaskInit:
    """Test AuthorMetadataFetchTask initialization."""

    def test_init_sets_author_id(self, metadata: dict[str, str]) -> None:
        """Test __init__ sets author_id from metadata."""
        task = AuthorMetadataFetchTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.author_id == "OL123A"

    def test_init_missing_author_id(self) -> None:
        """Test __init__ raises ValueError when author_id missing."""
        with pytest.raises(ValueError, match="author_id is required in task metadata"):
            AuthorMetadataFetchTask(
                task_id=1,
                user_id=1,
                metadata={},
            )

    def test_init_empty_author_id(self) -> None:
        """Test __init__ raises ValueError when author_id is empty."""
        with pytest.raises(ValueError, match="author_id is required in task metadata"):
            AuthorMetadataFetchTask(
                task_id=1,
                user_id=1,
                metadata={"author_id": ""},
            )


class TestAuthorMetadataFetchTaskRun:
    """Test AuthorMetadataFetchTask run method."""

    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryService")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorService")
    def test_run_success(
        self,
        mock_author_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_author_repo_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run successfully fetches author metadata."""
        # Setup mocks
        mock_author_repo = MagicMock()
        mock_author_repo_class.return_value = mock_author_repo
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library_service_class.return_value = mock_library_service
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.return_value = {
            "message": "Success",
            "updated": True,
        }
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

        task.run(worker_context)

        # Verify progress updates
        assert worker_context["update_progress"].call_count >= 3
        # Verify author service was called
        mock_author_service.fetch_author_metadata.assert_called_once_with("OL123A")

    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryService")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorService")
    def test_run_cancelled_before_processing(
        self,
        mock_author_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_author_repo_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run returns early when cancelled before processing."""
        task = AuthorMetadataFetchTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        task.mark_cancelled()

        task.run(worker_context)

        # Should not call author service
        mock_author_service_class.assert_not_called()

    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryService")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorService")
    def test_run_cancelled_during_execution(
        self,
        mock_author_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_author_repo_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run returns early when cancelled during execution."""
        # Setup mocks
        mock_author_repo = MagicMock()
        mock_author_repo_class.return_value = mock_author_repo
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library_service_class.return_value = mock_library_service
        mock_author_service = MagicMock()
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

        # Mark as cancelled after first progress update
        def cancel_after_first(*args: object, **kwargs: object) -> None:
            task.mark_cancelled()

        worker_context["update_progress"].side_effect = cancel_after_first

        task.run(worker_context)

        # Should not call fetch_author_metadata
        mock_author_service.fetch_author_metadata.assert_not_called()

    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryRepository")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.LibraryService")
    @patch("fundamental.services.tasks.author_metadata_fetch_task.AuthorService")
    def test_run_exception(
        self,
        mock_author_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_author_repo_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run raises exception on error."""
        # Setup mocks
        mock_author_repo = MagicMock()
        mock_author_repo_class.return_value = mock_author_repo
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library_service_class.return_value = mock_library_service
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.side_effect = ValueError("Test error")
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

        with pytest.raises(ValueError, match="Test error"):
            task.run(worker_context)

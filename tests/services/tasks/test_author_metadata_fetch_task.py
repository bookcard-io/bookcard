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

from bookcard.models.config import Library
from bookcard.services.tasks.author_metadata_fetch_task import (
    AuthorMetadataFetchTask,
)
from bookcard.services.tasks.exceptions import LibraryNotConfiguredError


@pytest.fixture
def library() -> Library:
    """Return a test Library instance.

    Returns
    -------
    Library
        Library with id=1.
    """
    lib = Library(name="Test Library", path="/tmp/test-library", is_active=True)
    lib.id = 1
    return lib


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

    @patch("bookcard.services.tasks.author_metadata_fetch_task.AuthorService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_success(
        self,
        mock_resolve: MagicMock,
        mock_author_service_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
        library: Library,
    ) -> None:
        """Test run successfully fetches author metadata.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        mock_author_service_class : MagicMock
            Mock for AuthorService class.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        library : Library
            Test library.
        """
        mock_resolve.return_value = library
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.return_value = {
            "message": "Success",
            "updated": True,
        }
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)

        task.run(worker_context)

        mock_resolve.assert_called_once_with(worker_context["session"], metadata, 1)
        assert worker_context["update_progress"].call_count >= 3
        mock_author_service.fetch_author_metadata.assert_called_once_with("OL123A")

    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_cancelled_before_processing(
        self,
        mock_resolve: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run returns early when cancelled before processing.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        """
        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)
        task.mark_cancelled()

        task.run(worker_context)

        mock_resolve.assert_not_called()

    @patch("bookcard.services.tasks.author_metadata_fetch_task.AuthorService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_cancelled_during_execution(
        self,
        mock_resolve: MagicMock,
        mock_author_service_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
        library: Library,
    ) -> None:
        """Test run returns early when cancelled during execution.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        mock_author_service_class : MagicMock
            Mock for AuthorService class.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        library : Library
            Test library.
        """
        mock_resolve.return_value = library
        mock_author_service = MagicMock()
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)

        def cancel_after_first(*args: object, **kwargs: object) -> None:
            task.mark_cancelled()

        worker_context["update_progress"].side_effect = cancel_after_first

        task.run(worker_context)

        mock_author_service.fetch_author_metadata.assert_not_called()

    @patch("bookcard.services.tasks.author_metadata_fetch_task.AuthorService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_exception(
        self,
        mock_resolve: MagicMock,
        mock_author_service_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
        library: Library,
    ) -> None:
        """Test run raises exception on error.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        mock_author_service_class : MagicMock
            Mock for AuthorService class.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        library : Library
            Test library.
        """
        mock_resolve.return_value = library
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.side_effect = ValueError("Test error")
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)

        with pytest.raises(ValueError, match="Test error"):
            task.run(worker_context)

    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_library_not_configured(
        self,
        mock_resolve: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
    ) -> None:
        """Test run raises LibraryNotConfiguredError when no library found.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        """
        mock_resolve.side_effect = LibraryNotConfiguredError()

        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)

        with pytest.raises(LibraryNotConfiguredError):
            task.run(worker_context)

    @patch("bookcard.services.tasks.author_metadata_fetch_task.AuthorService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_uses_library_id_from_metadata(
        self,
        mock_resolve: MagicMock,
        mock_author_service_class: MagicMock,
        worker_context: dict[str, MagicMock],
        library: Library,
    ) -> None:
        """Test that library_id from metadata is forwarded to the resolver.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        mock_author_service_class : MagicMock
            Mock for AuthorService class.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        library : Library
            Test library.
        """
        metadata = {"author_id": "OL456A", "library_id": 42}
        mock_resolve.return_value = library
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.return_value = {"message": "OK"}
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(task_id=1, user_id=7, metadata=metadata)

        task.run(worker_context)

        mock_resolve.assert_called_once_with(worker_context["session"], metadata, 7)

    @patch("bookcard.services.tasks.author_metadata_fetch_task.AuthorService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.PinnedLibraryService")
    @patch("bookcard.services.tasks.author_metadata_fetch_task.resolve_task_library")
    def test_run_injects_pinned_library_service(
        self,
        mock_resolve: MagicMock,
        mock_pinned_class: MagicMock,
        mock_author_service_class: MagicMock,
        worker_context: dict[str, MagicMock],
        metadata: dict[str, str],
        library: Library,
    ) -> None:
        """Test that AuthorService receives a PinnedLibraryService.

        Parameters
        ----------
        mock_resolve : MagicMock
            Mock for resolve_task_library.
        mock_pinned_class : MagicMock
            Mock for PinnedLibraryService class.
        mock_author_service_class : MagicMock
            Mock for AuthorService class.
        worker_context : dict[str, MagicMock]
            Mock worker context.
        metadata : dict[str, str]
            Task metadata.
        library : Library
            Test library.
        """
        mock_resolve.return_value = library
        mock_pinned_instance = MagicMock()
        mock_pinned_class.return_value = mock_pinned_instance
        mock_author_service = MagicMock()
        mock_author_service.fetch_author_metadata.return_value = {"message": "OK"}
        mock_author_service_class.return_value = mock_author_service

        task = AuthorMetadataFetchTask(task_id=1, user_id=1, metadata=metadata)

        task.run(worker_context)

        mock_pinned_class.assert_called_once()
        call_kwargs = mock_pinned_class.call_args
        assert call_kwargs[0][2] is library  # third positional arg = library
        mock_author_service_class.assert_called_once()
        svc_kwargs = mock_author_service_class.call_args[1]
        assert svc_kwargs["library_service"] is mock_pinned_instance

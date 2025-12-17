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

"""Tests for BookUploadTask to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.tasks.book_upload_task import BookUploadTask
from bookcard.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
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
def temp_file() -> Path:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as f:
        f.write(b"test content")
        return Path(f.name)


@pytest.fixture
def metadata(temp_file: Path) -> dict[str, str]:
    """Return task metadata with file_path."""
    return {
        "file_path": str(temp_file),
        "filename": temp_file.name,
        "file_format": "epub",
    }


class TestBookUploadTaskInit:
    """Test BookUploadTask initialization."""

    def test_init_sets_file_path(self, metadata: dict[str, str]) -> None:
        """Test __init__ sets file_path from metadata."""
        task = BookUploadTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.file_info.file_path == Path(metadata["file_path"])
        assert task.file_info.filename == metadata["filename"]
        assert task.file_info.file_format == metadata["file_format"]

    def test_init_missing_file_path(self) -> None:
        """Test __init__ raises ValueError when file_path missing."""
        with pytest.raises(ValueError, match="file_path is required in task metadata"):
            BookUploadTask(
                task_id=1,
                user_id=1,
                metadata={},
            )

    def test_init_empty_file_path(self) -> None:
        """Test __init__ raises ValueError when file_path is empty."""
        with pytest.raises(ValueError, match="file_path is required in task metadata"):
            BookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"file_path": ""},
            )

    def test_init_defaults(self) -> None:
        """Test __init__ sets default values for optional fields."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            file_path = f.name

        task = BookUploadTask(
            task_id=1,
            user_id=1,
            metadata={"file_path": file_path},
        )
        assert task.file_info.filename == "Unknown"
        assert task.file_info.file_format == ""


class TestBookUploadTaskValidateFile:
    """Test BookUploadTask._validate_file method."""

    def test_validate_file_success(self, metadata: dict[str, str]) -> None:
        """Test _validate_file returns file size for valid file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as f:
            f.write(b"test content")
            file_path = f.name

        task = BookUploadTask(
            task_id=1,
            user_id=1,
            metadata={
                "file_path": file_path,
                "filename": "test.epub",
                "file_format": "epub",
            },
        )
        file_size = task._validate_file()
        assert file_size > 0

    def test_validate_file_not_found(self, metadata: dict[str, str]) -> None:
        """Test _validate_file raises FileNotFoundError when file doesn't exist."""
        task = BookUploadTask(
            task_id=1,
            user_id=1,
            metadata={
                "file_path": "/nonexistent/file.epub",
                "filename": "file.epub",
                "file_format": "epub",
            },
        )
        with pytest.raises(FileNotFoundError, match="File not found"):
            task._validate_file()

    def test_validate_file_is_directory(self, metadata: dict[str, str]) -> None:
        """Test _validate_file raises ValueError when path is directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = BookUploadTask(
                task_id=1,
                user_id=1,
                metadata={
                    "file_path": tmpdir,
                    "filename": "test",
                    "file_format": "epub",
                },
            )
            with pytest.raises(ValueError, match="file_path is a directory"):
                task._validate_file()

    def test_validate_file_not_file(self, metadata: dict[str, str]) -> None:
        """Test _validate_file raises ValueError when path is not a file (covers lines 190-191)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = BookUploadTask(
                task_id=1,
                user_id=1,
                metadata={
                    "file_path": tmpdir,
                    "filename": "test",
                    "file_format": "epub",
                },
            )
            # First check will fail because it's a directory, not a file
            with pytest.raises(ValueError, match="file_path is a directory"):
                task._validate_file()


class TestBookUploadTaskAddBookToLibrary:
    """Test BookUploadTask._add_book_to_library method."""

    @pytest.fixture
    def task(self, metadata: dict[str, str]) -> BookUploadTask:
        """Create BookUploadTask instance."""
        return BookUploadTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_add_book_to_library_success(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _add_book_to_library successfully adds book."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        book_id = task._add_book_to_library(
            worker_context["session"],
            mock_library,
            worker_context["update_progress"],
        )

        assert book_id == 123
        assert task.metadata["book_ids"] == [123]
        mock_book_service.add_book.assert_called_once()

    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    def test_add_book_to_library_no_active_library(
        self,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _add_book_to_library raises ValueError when no active library."""
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library_service.get_active_library.return_value = None
        mock_library_service_class.return_value = mock_library_service

        with pytest.raises(LibraryNotConfiguredError):
            task._get_active_library(worker_context["session"])

    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_add_book_to_library_cancelled(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _add_book_to_library raises TaskCancelledError when cancelled."""
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service

        task.mark_cancelled()

        with pytest.raises(TaskCancelledError):
            task._add_book_to_library(
                worker_context["session"],
                mock_library,
                worker_context["update_progress"],
            )

    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_add_book_to_library_cancelled_after_library_found(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _add_book_to_library raises TaskCancelledError when cancelled after library found."""
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service

        # Mark as cancelled after first progress update
        def cancel_after_first(*args: object, **kwargs: object) -> None:
            task.mark_cancelled()

        worker_context["update_progress"].side_effect = cancel_after_first

        with pytest.raises(TaskCancelledError):
            task._add_book_to_library(
                worker_context["session"],
                mock_library,
                worker_context["update_progress"],
            )

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_add_book_to_library_extracts_title_from_filename(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _add_book_to_library extracts title from filename if not provided."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        # Remove title from metadata
        task.metadata.pop("title", None)
        # Update file_info filename
        task.file_info = task.file_info.__class__(
            file_path=task.file_info.file_path,
            filename="My Book.epub",
            file_format=task.file_info.file_format,
        )

        task._add_book_to_library(
            worker_context["session"],
            mock_library,
            worker_context["update_progress"],
        )

        # Verify add_book was called with extracted title
        call_args = mock_book_service.add_book.call_args
        assert call_args[1]["title"] == "My Book"


class TestBookUploadTaskRun:
    """Test BookUploadTask run method."""

    @pytest.fixture
    def task(self, metadata: dict[str, str]) -> BookUploadTask:
        """Create BookUploadTask instance."""
        return BookUploadTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_success(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run successfully uploads book."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        task.run(worker_context)

        # Verify progress updates
        assert worker_context["update_progress"].call_count >= 3
        # Verify book_ids is in metadata
        assert "book_ids" in task.metadata
        assert task.metadata["book_ids"] == [123]

    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_cancelled_before_processing(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run returns early when cancelled before processing."""
        task.mark_cancelled()

        task.run(worker_context)

        # Should not call book service
        mock_book_service_class.assert_not_called()

    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_cancelled_during_execution(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run returns early when cancelled during execution."""
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service

        # Mark as cancelled after first progress update
        def cancel_after_first(*args: object, **kwargs: object) -> None:
            task.mark_cancelled()

        worker_context["update_progress"].side_effect = cancel_after_first

        task.run(worker_context)

        # Should not call add_book
        mock_book_service_class.assert_not_called()

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_exception(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run raises exception on error."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.side_effect = ValueError("Test error")
        mock_book_service_class.return_value = mock_book_service

        with pytest.raises(ValueError, match="Test error"):
            task.run(worker_context)

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_sets_file_size(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run sets file_size in metadata."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        task.run(worker_context)

        assert "file_size" in task.metadata
        assert task.metadata["file_size"] > 0

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_logs_book_ids_confirmation(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run logs confirmation when book_ids is in metadata."""
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No duplicate found
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo
        # Setup mocks
        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        task.run(worker_context)

        # book_ids should be in metadata
        assert "book_ids" in task.metadata


class TestBookUploadTaskAdditional:
    """Additional tests for uncovered lines."""

    @pytest.fixture
    def task(self, metadata: dict[str, str]) -> BookUploadTask:
        """Create BookUploadTask instance."""
        return BookUploadTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

    @patch("bookcard.services.tasks.book_upload_task.BookMetadataService")
    def test_extract_author_exception_handling(
        self,
        mock_metadata_service_class: MagicMock,
        task: BookUploadTask,
    ) -> None:
        """Test _extract_author handles exceptions (covers lines 256-258)."""
        mock_metadata_service = MagicMock()
        mock_metadata_service.extract_metadata.side_effect = ValueError("Test error")
        mock_metadata_service_class.return_value = mock_metadata_service

        result = task._extract_author()

        assert result is None

    @patch("bookcard.services.tasks.book_upload_task.BookDuplicateHandler")
    def test_check_and_handle_duplicate_skip(
        self,
        mock_duplicate_handler_class: MagicMock,
        task: BookUploadTask,
    ) -> None:
        """Test _check_and_handle_duplicate when should_skip is True (covers lines 307-309)."""
        from bookcard.services.duplicate_detection.book_duplicate_handler import (
            DuplicateCheckResult,
        )

        mock_duplicate_handler = MagicMock()
        duplicate_result = DuplicateCheckResult(
            is_duplicate=True,
            duplicate_book_id=123,
            should_skip=True,
            should_overwrite=False,
        )
        mock_duplicate_handler.check_duplicate.return_value = duplicate_result
        mock_duplicate_handler_class.return_value = mock_duplicate_handler

        mock_library = MagicMock()
        mock_book_service = MagicMock()

        with pytest.raises(ValueError, match="Duplicate book found"):
            task._check_and_handle_duplicate(
                mock_library,
                mock_book_service,
                "Test Title",
                "Test Author",
            )

    @patch("bookcard.services.tasks.book_upload_task.BookDuplicateHandler")
    def test_check_and_handle_duplicate_overwrite(
        self,
        mock_duplicate_handler_class: MagicMock,
        task: BookUploadTask,
    ) -> None:
        """Test _check_and_handle_duplicate when should_overwrite is True (covers lines 313-321)."""
        from bookcard.services.duplicate_detection.book_duplicate_handler import (
            DuplicateCheckResult,
        )

        mock_duplicate_handler = MagicMock()
        duplicate_result = DuplicateCheckResult(
            is_duplicate=True,
            duplicate_book_id=123,
            should_skip=False,
            should_overwrite=True,
        )
        mock_duplicate_handler.check_duplicate.return_value = duplicate_result
        mock_duplicate_handler_class.return_value = mock_duplicate_handler

        mock_library = MagicMock()
        mock_book_service = MagicMock()

        result = task._check_and_handle_duplicate(
            mock_library,
            mock_book_service,
            "Test Title",
            "Test Author",
        )

        assert result == 123
        mock_book_service.delete_book.assert_called_once_with(
            book_id=123,
            delete_files_from_drive=True,
        )

    def test_get_post_processors_returns_existing(
        self,
        task: BookUploadTask,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test _get_post_processors returns existing processors (covers line 409)."""
        from bookcard.services.tasks.post_processors import PostIngestProcessor

        mock_processor = MagicMock(spec=PostIngestProcessor)
        task._post_processors = [mock_processor]

        result = task._get_post_processors(
            worker_context["session"],
            MagicMock(),
        )

        assert result == [mock_processor]

    def test_validate_metadata_before_completion_missing_book_ids(
        self,
        task: BookUploadTask,
    ) -> None:
        """Test _validate_metadata_before_completion raises when book_ids missing (covers lines 450-451)."""
        task.metadata = {}

        with pytest.raises(
            ValueError, match="Required metadata field 'book_ids' missing"
        ):
            task._validate_metadata_before_completion()

    @patch(
        "bookcard.services.duplicate_detection.book_duplicate_handler.CalibreBookRepository"
    )
    @patch("bookcard.services.tasks.book_upload_task.LibraryRepository")
    @patch("bookcard.services.tasks.book_upload_task.LibraryService")
    @patch("bookcard.services.tasks.book_upload_task.BookService")
    def test_run_with_worker_context_object(
        self,
        mock_book_service_class: MagicMock,
        mock_library_service_class: MagicMock,
        mock_library_repo_class: MagicMock,
        mock_calibre_repo_class: MagicMock,
        task: BookUploadTask,
    ) -> None:
        """Test run with WorkerContext object instead of dict (covers line 471)."""
        from bookcard.services.tasks.context import WorkerContext

        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None
        mock_calibre_session.exec.return_value = mock_exec_result
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        mock_calibre_repo_class.return_value = mock_calibre_repo

        mock_library_repo = MagicMock()
        mock_library_repo_class.return_value = mock_library_repo
        mock_library_service = MagicMock()
        mock_library = MagicMock()
        mock_library.duplicate_handling = "IGNORE"
        mock_library.calibre_db_path = "/test/calibre"
        mock_library.calibre_db_file = "metadata.db"
        mock_library_service.get_active_library.return_value = mock_library
        mock_library_service_class.return_value = mock_library_service
        mock_book_service = MagicMock()
        mock_book_service.add_book.return_value = 123
        mock_book_service_class.return_value = mock_book_service

        update_progress = MagicMock()
        context = WorkerContext(
            session=MagicMock(),
            update_progress=update_progress,
            task_service=MagicMock(),
        )

        task.run(context)

        assert "book_ids" in task.metadata

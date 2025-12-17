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

"""Tests for MultiBookUploadTask."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.tasks.multi_upload_task import MultiBookUploadTask


@pytest.fixture
def mock_files() -> list[dict[str, str]]:
    """Return mock file list."""
    return [
        {
            "file_path": "/tmp/file1.epub",
            "filename": "file1.epub",
            "file_format": "epub",
            "title": "Book 1",
            "author_name": "Author 1",
        },
        {
            "file_path": "/tmp/file2.pdf",
            "filename": "file2.pdf",
            "file_format": "pdf",
            "title": "Book 2",
            "author_name": "Author 2",
        },
    ]


@pytest.fixture
def worker_context() -> dict[str, MagicMock]:
    """Return mock worker context."""
    update_progress = MagicMock()
    return {
        "session": MagicMock(),
        "task_service": MagicMock(),
        "update_progress": update_progress,
    }


class TestMultiBookUploadTaskInit:
    """Test MultiBookUploadTask initialization."""

    def test_init_sets_files(self, mock_files: list[dict[str, str]]) -> None:
        """Test __init__ sets files from metadata."""
        task = MultiBookUploadTask(
            task_id=1,
            user_id=1,
            metadata={"files": mock_files},
        )
        assert task.files == mock_files

    def test_init_empty_files(self) -> None:
        """Test __init__ handles empty files list."""
        task = MultiBookUploadTask(
            task_id=1,
            user_id=1,
            metadata={"files": []},
        )
        assert task.files == []

    def test_init_no_files_key(self) -> None:
        """Test __init__ handles missing files key."""
        task = MultiBookUploadTask(
            task_id=1,
            user_id=1,
            metadata={},
        )
        assert task.files == []


class TestRun:
    """Test run method."""

    def test_run_no_files_raises_error(
        self, worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run raises ValueError when no files."""
        task = MultiBookUploadTask(
            task_id=1,
            user_id=1,
            metadata={"files": []},
        )
        with pytest.raises(ValueError, match="No files to upload"):
            task.run(worker_context)

    def test_run_success(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run successfully processes files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                mock_upload_task = MagicMock()
                mock_upload_task.metadata = {"book_ids": [1, 2]}
                mock_upload_task.run.return_value = None
                mock_book_upload.return_value = mock_upload_task

                task.run(worker_context)

                assert mock_book_upload.call_count == 2
                assert task.metadata["completed_files"] == 2
                assert task.metadata["failed_files"] == 0
                assert len(task.metadata["file_details"]) == 2

    def test_run_file_failure(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run handles partial file upload failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                # First file succeeds, second file fails
                mock_upload_task1 = MagicMock()
                mock_upload_task1.metadata = {"book_ids": [1]}
                mock_upload_task1.run.return_value = None
                mock_upload_task2 = MagicMock()
                mock_upload_task2.run.side_effect = Exception("Upload failed")
                mock_book_upload.side_effect = [mock_upload_task1, mock_upload_task2]

                # Should not raise - partial failures are tracked but don't stop execution
                task.run(worker_context)

                assert task.metadata["completed_files"] == 1
                assert task.metadata["failed_files"] == 1
                assert len(task.metadata["file_details"]) == 2
                # Check that one succeeded and one failed
                statuses = [
                    detail["status"] for detail in task.metadata["file_details"]
                ]
                assert "success" in statuses
                assert "failed" in statuses

    def test_run_cancelled(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run stops when cancelled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )
            task.mark_cancelled()

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                task.run(worker_context)

                # Should not process any files when cancelled
                mock_book_upload.assert_not_called()

    def test_run_all_files_failed_raises_error(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run raises RuntimeError when all files fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                mock_upload_task = MagicMock()
                mock_upload_task.run.side_effect = Exception("Upload failed")
                mock_book_upload.return_value = mock_upload_task

                with pytest.raises(
                    RuntimeError, match=r"All .* files failed to upload"
                ):
                    task.run(worker_context)

    def test_run_collects_book_ids(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run collects book_ids from upload tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                mock_upload_task1 = MagicMock()
                mock_upload_task1.metadata = {"book_ids": [1]}
                mock_upload_task1.run.return_value = None
                mock_upload_task2 = MagicMock()
                mock_upload_task2.metadata = {"book_ids": [2]}
                mock_upload_task2.run.return_value = None
                mock_book_upload.side_effect = [mock_upload_task1, mock_upload_task2]

                task.run(worker_context)

                assert task.metadata["book_ids"] == [1, 2]

    def test_run_tracks_file_details(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run tracks file details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                mock_upload_task = MagicMock()
                mock_upload_task.metadata = {"book_ids": [1]}
                mock_upload_task.run.return_value = None
                mock_book_upload.return_value = mock_upload_task

                task.run(worker_context)

                assert len(task.metadata["file_details"]) == 2
                assert all(
                    "filename" in detail for detail in task.metadata["file_details"]
                )
                assert all(
                    "status" in detail for detail in task.metadata["file_details"]
                )

    def test_run_updates_progress(
        self, mock_files: list[dict[str, str]], worker_context: dict[str, MagicMock]
    ) -> None:
        """Test run updates progress during execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            for file_info in mock_files:
                file_path = Path(tmpdir) / file_info["filename"]
                file_path.write_text("test content")
                file_info["file_path"] = str(file_path)

            task = MultiBookUploadTask(
                task_id=1,
                user_id=1,
                metadata={"files": mock_files},
            )

            with patch(
                "bookcard.services.tasks.multi_upload_task.BookUploadTask"
            ) as mock_book_upload:
                mock_upload_task = MagicMock()
                mock_upload_task.metadata = {"book_ids": [1]}
                mock_upload_task.run.return_value = None
                mock_book_upload.return_value = mock_upload_task

                task.run(worker_context)

                # Should call update_progress multiple times
                assert worker_context["update_progress"].call_count > 0

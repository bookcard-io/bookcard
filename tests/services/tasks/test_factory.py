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

"""Tests for task factory to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.models.tasks import TaskType
from fundamental.services.tasks.author_metadata_fetch_task import (
    AuthorMetadataFetchTask,
)
from fundamental.services.tasks.book_upload_task import BookUploadTask
from fundamental.services.tasks.factory import create_task
from fundamental.services.tasks.library_scan_task import LibraryScanTask
from fundamental.services.tasks.multi_upload_task import MultiBookUploadTask


class TestCreateTask:
    """Test create_task function."""

    @pytest.mark.parametrize(
        ("task_type", "expected_class"),
        [
            (TaskType.BOOK_UPLOAD, BookUploadTask),
            (TaskType.MULTI_BOOK_UPLOAD, MultiBookUploadTask),
            (TaskType.AUTHOR_METADATA_FETCH, AuthorMetadataFetchTask),
            (TaskType.LIBRARY_SCAN, LibraryScanTask),
        ],
    )
    def test_create_task_success(
        self, task_type: TaskType, expected_class: type
    ) -> None:
        """Test create_task creates correct task type."""
        metadata = {
            "task_type": task_type.value,
            "file_path": "/tmp/test.epub",
            "filename": "test.epub",
            "file_format": "epub",
        }
        if task_type == TaskType.AUTHOR_METADATA_FETCH:
            metadata = {
                "task_type": task_type.value,
                "author_id": "OL123A",
            }
        elif task_type == TaskType.LIBRARY_SCAN:
            metadata = {
                "task_type": task_type.value,
                "library_id": 1,
            }
        elif task_type == TaskType.MULTI_BOOK_UPLOAD:
            metadata = {
                "task_type": task_type.value,
                "files": [],
            }

        task = create_task(task_id=1, user_id=1, metadata=metadata)
        assert isinstance(task, expected_class)

    def test_create_task_missing_task_type(self) -> None:
        """Test create_task raises ValueError when task_type missing."""
        with pytest.raises(ValueError, match="task_type not found in metadata"):
            create_task(task_id=1, user_id=1, metadata={})

    def test_create_task_invalid_task_type(self) -> None:
        """Test create_task raises ValueError for invalid task_type."""
        with pytest.raises(ValueError, match="Unknown task type"):
            create_task(
                task_id=1,
                user_id=1,
                metadata={"task_type": "invalid_type"},
            )

    def test_create_task_not_implemented(self) -> None:
        """Test create_task raises ValueError for unimplemented task type."""
        with pytest.raises(ValueError, match=r"Task type .* not yet implemented"):
            create_task(
                task_id=1,
                user_id=1,
                metadata={"task_type": TaskType.BOOK_CONVERT.value},
            )

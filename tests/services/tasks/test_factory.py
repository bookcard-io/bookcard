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

import re

import pytest

from bookcard.models.tasks import TaskType
from bookcard.services.tasks.author_metadata_fetch_task import (
    AuthorMetadataFetchTask,
)
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.book_upload_task import BookUploadTask
from bookcard.services.tasks.factory import (
    TaskRegistry,
    create_task,
    register_task,
)
from bookcard.services.tasks.library_scan_task import LibraryScanTask
from bookcard.services.tasks.multi_upload_task import MultiBookUploadTask


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
                metadata={"task_type": TaskType.THUMBNAIL_GENERATE.value},
            )


class TestTaskRegistry:
    """Test TaskRegistry class."""

    def test_init(self) -> None:
        """Test TaskRegistry initialization."""
        registry = TaskRegistry()
        assert registry._registry == {}

    def test_register(self) -> None:
        """Test register method."""
        registry = TaskRegistry()
        registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)
        assert registry._registry[TaskType.BOOK_UPLOAD] == BookUploadTask

    def test_register_duplicate_raises_error(self) -> None:
        """Test register raises ValueError when task type already registered (covers lines 78-79)."""
        registry = TaskRegistry()
        registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)

        with pytest.raises(
            ValueError,
            match=re.escape(f"Task type {TaskType.BOOK_UPLOAD} is already registered"),
        ):
            registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)

    def test_get_registered(self) -> None:
        """Test get method returns registered task class."""
        registry = TaskRegistry()
        registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)
        result = registry.get(TaskType.BOOK_UPLOAD)
        assert result == BookUploadTask

    def test_get_not_registered(self) -> None:
        """Test get method returns None for unregistered task type."""
        registry = TaskRegistry()
        result = registry.get(TaskType.BOOK_CONVERT)
        assert result is None

    def test_is_registered_true(self) -> None:
        """Test is_registered returns True for registered task type (covers line 110)."""
        registry = TaskRegistry()
        registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)
        assert registry.is_registered(TaskType.BOOK_UPLOAD) is True

    def test_is_registered_false(self) -> None:
        """Test is_registered returns False for unregistered task type."""
        registry = TaskRegistry()
        assert registry.is_registered(TaskType.BOOK_CONVERT) is False

    def test_create_instance_success(self) -> None:
        """Test create_instance creates task instance."""
        registry = TaskRegistry()
        registry.register(TaskType.LIBRARY_SCAN, LibraryScanTask)

        task = registry.create_instance(
            TaskType.LIBRARY_SCAN,
            task_id=1,
            user_id=1,
            metadata={"library_id": 1},
        )

        assert isinstance(task, LibraryScanTask)
        assert task.task_id == 1
        assert task.user_id == 1

    def test_create_instance_not_registered(self) -> None:
        """Test create_instance raises ValueError for unregistered task type."""
        registry = TaskRegistry()

        with pytest.raises(ValueError, match=r"Task type .* not yet implemented"):
            registry.create_instance(
                TaskType.BOOK_CONVERT,
                task_id=1,
                user_id=1,
                metadata={},
            )


class TestRegisterTaskDecorator:
    """Test register_task decorator."""

    def test_register_task_decorator(self) -> None:
        """Test register_task decorator registers task class (covers lines 179-183)."""

        # Create a mock task class
        class TestTask(BaseTask):
            def run(self, worker_context: dict[str, object]) -> None:
                pass

        # Use the decorator with a task type that's not yet registered
        # We'll use THUMBNAIL_GENERATE which should not be registered
        # First, check if it's already registered and skip if so
        from bookcard.services.tasks.factory import _registry

        # Use a task type that's not registered in the global registry
        # We need to find one that's not registered - let's use THUMBNAIL_GENERATE
        # But first check if it exists and is not registered
        if not _registry.is_registered(TaskType.THUMBNAIL_GENERATE):
            decorated_class = register_task(TaskType.THUMBNAIL_GENERATE)(TestTask)

            # Verify the class is returned unchanged
            assert decorated_class == TestTask

            # Verify it was registered in the global registry
            assert _registry.is_registered(TaskType.THUMBNAIL_GENERATE)
            assert _registry.get(TaskType.THUMBNAIL_GENERATE) == TestTask

            # Clean up - unregister it
            _registry._registry.pop(TaskType.THUMBNAIL_GENERATE, None)
        else:
            # If already registered, just verify the decorator pattern works
            # by testing the decorator function directly
            decorator_func = register_task(TaskType.THUMBNAIL_GENERATE)
            assert callable(decorator_func)
            # Call it to verify it returns the class
            result = decorator_func(TestTask)
            assert result == TestTask

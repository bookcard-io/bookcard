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

"""Task factory for creating task instances.

Uses a registry pattern to map task types to their corresponding task classes.
This allows for easy extension without modifying the factory code (Open/Closed Principle).
"""

from collections.abc import Callable
from typing import Any, TypeVar

from fundamental.models.tasks import TaskType
from fundamental.services.tasks.author_metadata_fetch_task import (
    AuthorMetadataFetchTask,
)
from fundamental.services.tasks.base import BaseTask
from fundamental.services.tasks.book_upload_task import BookUploadTask
from fundamental.services.tasks.email_send_task import EmailSendTask
from fundamental.services.tasks.library_scan_task import LibraryScanTask
from fundamental.services.tasks.multi_upload_task import MultiBookUploadTask
from fundamental.services.tasks.openlibrary_dump_download_task import (
    OpenLibraryDumpDownloadTask,
)
from fundamental.services.tasks.openlibrary_dump_ingest_task import (
    OpenLibraryDumpIngestTask,
)

T = TypeVar("T", bound=BaseTask)


class TaskRegistry:
    """Registry for mapping task types to task classes.

    Follows the Registry pattern to decouple task registration from task creation.
    This allows new task types to be added without modifying the factory code.

    Attributes
    ----------
    _registry : dict[TaskType, type[BaseTask]]
        Internal mapping of task types to task classes.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._registry: dict[TaskType, type[BaseTask]] = {}

    def register(
        self,
        task_type: TaskType,
        task_class: type[BaseTask],
    ) -> None:
        """Register a task class for a given task type.

        Parameters
        ----------
        task_type : TaskType
            Task type to register.
        task_class : type[BaseTask]
            Task class that handles the task type.

        Raises
        ------
        ValueError
            If task_type is already registered.
        """
        if task_type in self._registry:
            msg = f"Task type {task_type} is already registered"
            raise ValueError(msg)
        self._registry[task_type] = task_class

    def get(self, task_type: TaskType) -> type[BaseTask] | None:
        """Get task class for a given task type.

        Parameters
        ----------
        task_type : TaskType
            Task type to look up.

        Returns
        -------
        type[BaseTask] | None
            Task class if registered, None otherwise.
        """
        return self._registry.get(task_type)

    def is_registered(self, task_type: TaskType) -> bool:
        """Check if a task type is registered.

        Parameters
        ----------
        task_type : TaskType
            Task type to check.

        Returns
        -------
        bool
            True if registered, False otherwise.
        """
        return task_type in self._registry

    def create_instance(
        self,
        task_type: TaskType,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> BaseTask:
        """Create a task instance for a given task type.

        Parameters
        ----------
        task_type : TaskType
            Task type to create.
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata.

        Returns
        -------
        BaseTask
            Task instance.

        Raises
        ------
        ValueError
            If task_type is not registered.
        """
        task_class = self.get(task_type)
        if task_class is None:
            msg = f"Task type {task_type} not yet implemented"
            raise ValueError(msg)
        return task_class(task_id, user_id, metadata)


# Global registry instance
_registry = TaskRegistry()


def register_task(task_type: TaskType) -> Callable[[type[T]], type[T]]:
    """Register a task class with a task type.

    Decorator function to register task classes with the global registry.

    Parameters
    ----------
    task_type : TaskType
        Task type to register.

    Returns
    -------
    Callable[[type[T]], type[T]]
        Decorator function.

    Examples
    --------
    >>> @register_task(
    ...     TaskType.BOOK_UPLOAD
    ... )
    ... class BookUploadTask(
    ...     BaseTask
    ... ):
    ...     pass
    """

    def decorator(task_class: type[T]) -> type[T]:
        _registry.register(task_type, task_class)
        return task_class

    return decorator


def create_task(
    task_id: int,
    user_id: int,
    metadata: dict[str, Any],
) -> BaseTask:
    """Create a task instance based on task type in metadata.

    Parameters
    ----------
    task_id : int
        Database task ID.
    user_id : int
        User ID creating the task.
    metadata : dict[str, Any]
        Task metadata containing task_type.

    Returns
    -------
    BaseTask
        Task instance.

    Raises
    ------
    ValueError
        If task_type is not found in metadata or not recognized.
    """
    task_type_str = metadata.get("task_type")
    if not task_type_str:
        msg = "task_type not found in metadata"
        raise ValueError(msg)

    try:
        task_type = TaskType(task_type_str)
    except ValueError:
        msg = f"Unknown task type: {task_type_str}"
        raise ValueError(msg) from None

    return _registry.create_instance(task_type, task_id, user_id, metadata)


# Register all task types
_registry.register(TaskType.BOOK_UPLOAD, BookUploadTask)
_registry.register(TaskType.MULTI_BOOK_UPLOAD, MultiBookUploadTask)
_registry.register(TaskType.LIBRARY_SCAN, LibraryScanTask)
_registry.register(TaskType.AUTHOR_METADATA_FETCH, AuthorMetadataFetchTask)
_registry.register(TaskType.OPENLIBRARY_DUMP_DOWNLOAD, OpenLibraryDumpDownloadTask)
_registry.register(TaskType.OPENLIBRARY_DUMP_INGEST, OpenLibraryDumpIngestTask)
_registry.register(TaskType.EMAIL_SEND, EmailSendTask)

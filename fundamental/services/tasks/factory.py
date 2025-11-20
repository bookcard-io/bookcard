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

Maps task types to their corresponding task classes.
"""

from typing import Any

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
        If task_type is not recognized.
    """
    task_type_str = metadata.get("task_type")
    if not task_type_str:
        # Try to get from task record if available
        msg = "task_type not found in metadata"
        raise ValueError(msg)

    try:
        task_type = TaskType(task_type_str)
    except ValueError:
        msg = f"Unknown task type: {task_type_str}"
        raise ValueError(msg) from None

    if task_type == TaskType.BOOK_UPLOAD:
        return BookUploadTask(task_id, user_id, metadata)
    if task_type == TaskType.MULTI_BOOK_UPLOAD:
        return MultiBookUploadTask(task_id, user_id, metadata)
    if task_type == TaskType.LIBRARY_SCAN:
        return LibraryScanTask(task_id, user_id, metadata)
    if task_type == TaskType.AUTHOR_METADATA_FETCH:
        return AuthorMetadataFetchTask(task_id, user_id, metadata)
    if task_type == TaskType.OPENLIBRARY_DUMP_DOWNLOAD:
        return OpenLibraryDumpDownloadTask(task_id, user_id, metadata)
    if task_type == TaskType.OPENLIBRARY_DUMP_INGEST:
        return OpenLibraryDumpIngestTask(task_id, user_id, metadata)
    if task_type == TaskType.EMAIL_SEND:
        return EmailSendTask(task_id, user_id, metadata)
    msg = f"Task type {task_type} not yet implemented"
    raise ValueError(msg)

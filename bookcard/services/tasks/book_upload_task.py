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

"""Book upload task implementation."""

import logging
from typing import Any

from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.book_upload_workflow import (
    BookUploadWorkflow,
    FileInfo,
    UploadContext,
)
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.exceptions import TaskCancelledError
from bookcard.services.tasks.post_processors import PostIngestProcessor

logger = logging.getLogger(__name__)


class BookUploadTask(BaseTask):
    """Task for uploading a single book file."""

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
        post_processors: list[PostIngestProcessor] | None = None,
        workflow: BookUploadWorkflow | None = None,
    ) -> None:
        """Initialize book upload task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing file_path, filename, file_format.
        post_processors : list[PostIngestProcessor] | None
            Optional list of post-ingest processors.
        workflow : BookUploadWorkflow | None
            Optional workflow implementation.
        """
        super().__init__(task_id, user_id, metadata)
        self.file_info = FileInfo.from_metadata(metadata)
        self._post_processors = post_processors
        self._workflow = workflow or BookUploadWorkflow()

    def _validate_metadata_before_completion(self) -> None:
        """Validate required metadata is present before task completion.

        Raises
        ------
        ValueError
            If required metadata fields are missing.
        """
        if "book_ids" not in self.metadata:
            msg = "Required metadata field 'book_ids' missing"
            raise ValueError(msg)

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute book upload task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, task_service, update_progress.
            Can be a dictionary (for backward compatibility) or WorkerContext.
        """
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        else:
            context = worker_context

        try:
            upload_context = UploadContext(
                session=context.session,
                update_progress=context.update_progress,
                check_cancelled=self.check_cancelled,
                task_id=self.task_id,
                user_id=self.user_id,
                file_info=self.file_info,
                task_metadata=self.metadata,
                post_processors=self._post_processors,
            )
            result = self._workflow.execute(upload_context)

            self.set_metadata("file_size", result.file_size)
            self.set_metadata("book_ids", [result.book_id])
            self.set_metadata("title", result.title)
            self._validate_metadata_before_completion()

            context.update_progress(1.0, self.metadata)

            logger.info(
                "Task %s: Book %s uploaded successfully (%s, %s bytes)",
                self.task_id,
                result.book_id,
                self.file_info.filename,
                result.file_size,
            )
        except TaskCancelledError:
            logger.info("Task %s cancelled", self.task_id)
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

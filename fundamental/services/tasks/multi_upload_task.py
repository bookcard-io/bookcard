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

"""Multi-file upload task implementation.

Handles batch uploads of multiple book files with per-file progress tracking.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fundamental.services.tasks.base import BaseTask
from fundamental.services.tasks.book_upload_task import BookUploadTask

logger = logging.getLogger(__name__)


class MultiBookUploadTask(BaseTask):
    """Task for uploading multiple book files.

    Processes files sequentially, tracking progress per file and overall.
    Each file is processed as a sub-task with its own progress.

    Attributes
    ----------
    files : list[dict[str, Any]]
        List of file metadata dictionaries.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize multi-file upload task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing files list.
        """
        super().__init__(task_id, user_id, metadata)
        self.files = metadata.get("files", [])

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute multi-file upload task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        update_progress = worker_context["update_progress"]

        total_files = len(self.files)
        if total_files == 0:
            msg = "No files to upload"
            raise ValueError(msg)

        self.set_metadata("total_files", total_files)
        self.set_metadata("completed_files", 0)
        self.set_metadata("failed_files", 0)
        self.set_metadata("file_details", [])

        completed = 0
        failed = 0
        total_size = 0
        formats: list[str] = []
        errors: list[dict[str, Any]] = []

        logger.info("Task %s: Starting upload of %s files", self.task_id, total_files)

        for idx, file_info in enumerate(self.files):
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled after %s files", self.task_id, completed)
                break

            file_path = Path(file_info.get("file_path", ""))
            filename = file_info.get("filename", "Unknown")
            file_format = file_info.get("file_format", "")

            try:
                # Calculate progress: (idx / total_files) * 0.9 (leave 0.1 for finalization)
                file_progress = (idx / total_files) * 0.9
                update_progress(
                    file_progress,
                    {
                        "current_file": filename,
                        "current_file_index": idx + 1,
                        "completed_files": completed,
                        "failed_files": failed,
                    },
                )

                # Process single file upload
                upload_task = BookUploadTask(
                    task_id=self.task_id,  # Use same task ID for tracking
                    user_id=self.user_id,
                    metadata={
                        "file_path": str(file_path),
                        "filename": filename,
                        "file_format": file_format,
                        "title": file_info.get("title"),
                        "author_name": file_info.get("author_name"),
                    },
                )

                # Execute upload with sub-progress tracking
                # Note: We can't easily track sub-progress in multi-upload,
                # so we just track overall progress
                upload_task.run(worker_context)

                # File uploaded successfully
                completed += 1
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    total_size += file_size
                if file_format and file_format not in formats:
                    formats.append(file_format)

                book_id = upload_task.metadata.get("book_id")
                file_details = {
                    "filename": filename,
                    "file_format": file_format,
                    "book_id": book_id,
                    "status": "success",
                }
                self.metadata.setdefault("file_details", []).append(file_details)

                logger.info(
                    "Task %s: File %s/%s (%s) uploaded successfully",
                    self.task_id,
                    idx + 1,
                    total_files,
                    filename,
                )

            except Exception as exc:
                failed += 1
                error_msg = str(exc)
                logger.exception(
                    "Task %s: File %s/%s (%s) failed: %s",
                    self.task_id,
                    idx + 1,
                    total_files,
                    filename,
                    error_msg,
                )

                file_details = {
                    "filename": filename,
                    "file_format": file_format,
                    "status": "failed",
                    "error": error_msg,
                }
                self.metadata.setdefault("file_details", []).append(file_details)
                errors.append({"filename": filename, "error": error_msg})

        # Finalize
        self.set_metadata("completed_files", completed)
        self.set_metadata("failed_files", failed)
        self.set_metadata("total_size", total_size)
        self.set_metadata("formats", formats)
        if errors:
            self.set_metadata("errors", errors)

        # Update final progress
        final_progress = (
            1.0
            if completed + failed == total_files
            else (completed + failed) / total_files
        )
        update_progress(final_progress, self.metadata)

        logger.info(
            "Task %s: Multi-upload complete - %s succeeded, %s failed out of %s total",
            self.task_id,
            completed,
            failed,
            total_files,
        )

        # If all files failed, raise an error
        if completed == 0 and failed > 0:
            msg = f"All {failed} files failed to upload"
            raise RuntimeError(msg)

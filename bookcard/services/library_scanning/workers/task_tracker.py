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

"""Task tracking utility for distributed scan workers."""

import logging
import random
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, ClassVar

from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from bookcard.database import create_db_engine, get_session
from bookcard.services.task_service import TaskService

logger = logging.getLogger(__name__)


class ScanTaskTracker:
    """Tracks task progress for distributed library scans."""

    # Progress milestones for each stage
    STAGE_PROGRESS: ClassVar[dict[str, float]] = {
        "crawl": 0.1,  # 0-10%
        "match": 0.3,  # 10-30%
        "ingest": 0.5,  # 30-50%
        "link": 0.6,  # 50-60%
        "deduplicate": 0.8,  # 60-80%
        "score": 0.95,  # 80-95%
        "completion": 1.0,  # 95-100%
    }

    def __init__(self) -> None:
        """Initialize task tracker."""
        self.engine = create_db_engine()

    def start_task(self, task_id: int) -> None:
        """Mark task as started.

        Parameters
        ----------
        task_id : int
            Task ID to start.
        """
        self._with_retry(
            lambda session: TaskService(session).start_task(task_id),
            f"start task {task_id}",
            max_retries=5,
        )

    def update_stage_progress(
        self,
        task_id: int,
        stage: str,
        stage_progress: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update task progress for a specific stage.

        Parameters
        ----------
        task_id : int
            Task ID to update.
        stage : str
            Stage name (crawl, match, ingest, link, deduplicate, score).
        stage_progress : float
            Progress within the stage (0.0 to 1.0).
        metadata : dict[str, Any] | None
            Optional metadata to include.
        """
        stage_base = self.STAGE_PROGRESS.get(stage, 0.0)
        stage_range = self._get_stage_range(stage)

        # Calculate overall progress: base + (stage_progress * range)
        overall_progress = stage_base + (stage_progress * stage_range)
        overall_progress = min(1.0, max(0.0, overall_progress))

        # Prepare metadata
        task_metadata = {"current_stage": stage, "stage_progress": stage_progress}
        if metadata:
            task_metadata.update(metadata)

        def update_progress(session: Session) -> None:
            task_service = TaskService(session)
            task_service.update_task_progress(task_id, overall_progress, task_metadata)
            logger.debug(
                "Updated task %d progress: %.2f%% (stage: %s, stage_progress: %.2f%%)",
                task_id,
                overall_progress * 100,
                stage,
                stage_progress * 100,
            )

        self._with_retry(
            update_progress,
            f"update task {task_id} progress",
            max_retries=5,
        )

    def complete_task(
        self,
        task_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark task as completed.

        Parameters
        ----------
        task_id : int
            Task ID to complete.
        metadata : dict[str, Any] | None
            Optional metadata to include.
        """
        self._with_retry(
            lambda session: TaskService(session).complete_task(
                task_id, metadata=metadata, normalize_metadata=False
            ),
            f"complete task {task_id}",
            max_retries=5,
        )
        logger.info("Marked task %d as COMPLETED", task_id)

    def fail_task(
        self,
        task_id: int,
        error_message: str,
    ) -> None:
        """Mark task as failed.

        Parameters
        ----------
        task_id : int
            Task ID to fail.
        error_message : str
            Error message to store.
        """
        self._with_retry(
            lambda session: TaskService(session).fail_task(task_id, error_message),
            f"fail task {task_id}",
            max_retries=5,
        )
        logger.error("Marked task %d as FAILED: %s", task_id, error_message)

    def _get_stage_range(self, stage: str) -> float:
        """Get the progress range for a stage.

        Parameters
        ----------
        stage : str
            Stage name.

        Returns
        -------
        float
            Progress range for the stage.
        """
        stages = list(self.STAGE_PROGRESS.keys())
        if stage not in stages:
            return 0.0

        stage_index = stages.index(stage)
        if stage_index == 0:
            return self.STAGE_PROGRESS[stage]
        return self.STAGE_PROGRESS[stage] - self.STAGE_PROGRESS[stages[stage_index - 1]]

    def _with_retry(
        self,
        operation: Callable[[Session], None],
        operation_name: str,
        max_retries: int = 5,
    ) -> None:
        """Execute a database operation with retry logic for lock errors.

        Parameters
        ----------
        operation : Callable[[Session], None]
            Function that takes a session and performs the operation.
        operation_name : str
            Human-readable name for logging.
        max_retries : int
            Maximum number of retry attempts (default: 5).
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                with get_session(self.engine, max_retries=1) as session:
                    operation(session)
            except OperationalError as e:
                if (
                    "database is locked" in str(e).lower()
                    and retry_count < max_retries - 1
                ):
                    retry_count += 1
                    # Exponential backoff with jitter: 0.1s, 0.2s, 0.4s, 0.8s, 1.6s
                    wait_time = 0.1 * (2 ** (retry_count - 1))
                    # Add small random jitter to avoid thundering herd
                    with suppress(Exception):
                        # Random is used for jitter, not crypto security
                        wait_time += random.uniform(0, 0.05)  # noqa: S311
                    logger.debug(
                        "Database locked during %s, retrying in %.3fs (attempt %d/%d)",
                        operation_name,
                        wait_time,
                        retry_count,
                        max_retries,
                    )
                    time.sleep(wait_time)
                    continue
                # Not a lock error or max retries reached
                logger.exception(
                    "Failed to %s after %d retries", operation_name, retry_count
                )
                raise
            except Exception:
                logger.exception("Failed to %s", operation_name)
                raise
            else:
                return

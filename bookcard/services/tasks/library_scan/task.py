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

"""Library scan task adapter.

This is a thin adapter that bridges the generic task runner framework to the
library scan domain orchestrator.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from bookcard.services.messaging.base import MessagePublisher
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.library_scan.errors import RedisUnavailableError
from bookcard.services.tasks.library_scan.orchestrator import LibraryScanOrchestrator
from bookcard.services.tasks.library_scan.publisher import ScanJobPublisher
from bookcard.services.tasks.library_scan.types import DataSourceConfig

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, dict[str, Any] | None], None]


class LibraryScanTask(BaseTask):
    """Task for executing a library scan via distributed scan workers.

    Notes
    -----
    This task is intentionally thin. It extracts inputs from task metadata and
    worker context, then delegates orchestration to ``LibraryScanOrchestrator``.
    """

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute library scan task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing at least:
            - ``session``: SQLModel session
            - ``update_progress``: progress callback
            - ``message_broker``: MessagePublisher for dispatching scan jobs
        """
        context = self._coerce_context(worker_context)

        publisher = context.get("message_broker")
        if publisher is None or not isinstance(publisher, MessagePublisher):
            msg = "Library scan requires a MessagePublisher in worker context (message_broker)."
            raise RedisUnavailableError(msg)

        session = cast("Session", context["session"])
        update_progress = cast("ProgressCallback", context["update_progress"])

        library_id = self.metadata.get("library_id")
        if library_id is not None and not isinstance(library_id, int):
            msg = "library_id must be an integer when provided"
            raise ValueError(msg)

        data_source_config = DataSourceConfig.from_metadata(self.metadata)

        orchestrator = LibraryScanOrchestrator(
            session,
            job_publisher=ScanJobPublisher(publisher),
        )

        logger.info(
            "Starting library scan task %s (library_id=%s)", self.task_id, library_id
        )

        orchestrator.scan(
            task_id=self.task_id,
            library_id=library_id,
            data_source_config=data_source_config,
            is_cancelled=self.check_cancelled,
            update_overall_progress=lambda p: update_progress(p, None),
        )

    @staticmethod
    def _coerce_context(
        worker_context: dict[str, Any] | WorkerContext,
    ) -> dict[str, Any]:
        """Coerce worker context to a plain dictionary.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context.

        Returns
        -------
        dict[str, Any]
            Normalized dictionary form.
        """
        if isinstance(worker_context, WorkerContext):
            # Preserve dict-like access patterns for tasks that haven't migrated.
            return {
                "session": worker_context.session,
                "update_progress": worker_context.update_progress,
                "task_service": worker_context.task_service,
                "enqueue_task": worker_context.enqueue_task,
                # message_broker may be injected as an attribute in a future refactor
                "message_broker": getattr(worker_context, "message_broker", None),
            }
        return worker_context

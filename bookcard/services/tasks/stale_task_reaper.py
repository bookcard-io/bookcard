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

"""Stale task reaper service.

Periodically detects RUNNING tasks that have exceeded their maximum allowed
runtime and marks them as FAILED.  This acts as a safety net when cooperative
cancellation (``mark_cancelled`` / ``check_cancelled``) is insufficient —
e.g. when a task is blocked on I/O and never polls its cancellation flag.

Follows SRP: sole responsibility is detecting and cleaning up stale tasks.
Follows IOC: accepts Engine and TaskRunner as constructor dependencies.
"""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.config import ScheduledTasksConfig
from bookcard.services.task_service import TaskService

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from bookcard.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)

_REAPER_ERROR_TEMPLATE = (
    "Task exceeded maximum runtime of {hours}h (reaped by watchdog)"
)


class StaleTaskReaper:
    """Detects and fails tasks that have exceeded their maximum runtime.

    Intended to be called periodically (e.g. every 5 minutes) via the
    application scheduler.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    task_runner : TaskRunner
        Task runner instance for cooperative cancellation signals.
    """

    def __init__(self, engine: Engine, task_runner: TaskRunner) -> None:
        self._engine = engine
        self._task_runner = task_runner

    def reap(self) -> int:
        """Scan for stale running tasks and mark them as failed.

        Returns
        -------
        int
            Number of tasks that were reaped.
        """
        max_runtime_seconds = self._get_max_runtime_seconds()
        if max_runtime_seconds is None:
            return 0

        try:
            with Session(self._engine) as session:
                task_service = TaskService(session)
                stale_tasks = task_service.find_stale_running_tasks(max_runtime_seconds)

                if not stale_tasks:
                    return 0

                duration_hours = max_runtime_seconds / 3600
                error_message = _REAPER_ERROR_TEMPLATE.format(
                    hours=f"{duration_hours:g}"
                )

                reaped = 0
                for task in stale_tasks:
                    task_id = task.id
                    if task_id is None:
                        continue

                    logger.warning(
                        "Reaping stale task %s (%s) — running since %s",
                        task_id,
                        task.task_type,
                        task.started_at,
                    )

                    with suppress(SQLAlchemyError):
                        self._task_runner.cancel(task_id)

                    task_service.fail_task(task_id, error_message)
                    reaped += 1

                if reaped:
                    logger.warning("Stale task reaper cleaned up %d task(s)", reaped)
                return reaped

        except SQLAlchemyError:
            logger.exception("Stale task reaper failed during scan")
            return 0

    def _get_max_runtime_seconds(self) -> int | None:
        """Read the configured max runtime from ``ScheduledTasksConfig``.

        Returns
        -------
        int | None
            Maximum runtime in seconds, or None if unavailable.
        """
        try:
            with Session(self._engine) as session:
                config = session.exec(select(ScheduledTasksConfig).limit(1)).first()
        except SQLAlchemyError:
            logger.exception("Stale task reaper: failed to read ScheduledTasksConfig")
            return None

        if config is None:
            return None

        try:
            duration_hours = int(config.duration_hours)
        except (TypeError, ValueError):
            logger.exception("Stale task reaper: invalid duration_hours value")
            return None

        if duration_hours <= 0:
            return None
        return duration_hours * 3600

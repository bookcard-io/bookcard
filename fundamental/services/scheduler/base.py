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

"""Base scheduler and shared utilities for scheduled tasks.

Provides common functionality for all scheduler implementations,
following SRP and DRY principles.
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.auth import User
from fundamental.models.config import ScheduledTasksConfig
from fundamental.models.tasks import TaskType

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine

    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTaskDefinition:
    """Definition for a scheduled task.

    Parameters
    ----------
    task_type : TaskType
        Task type to execute.
    config_flag_getter : Callable[[ScheduledTasksConfig], bool]
        Function to get the enabled flag from ScheduledTasksConfig.
    payload_factory : Callable[[], dict] | None
        Optional function to generate task payload. If None, empty dict is used.
    metadata_factory : Callable[[], dict] | None
        Optional function to generate task metadata. If None, minimal metadata is used.
    """

    task_type: TaskType
    config_flag_getter: Callable[[ScheduledTasksConfig], bool]
    payload_factory: Callable[[], dict] | None = None
    metadata_factory: Callable[[], dict] | None = None


class BaseScheduler(ABC):
    """Abstract base class for task schedulers.

    Provides common scheduling logic while allowing subclasses to implement
    specific execution mechanisms. Follows SRP and IOC principles.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.
    task_runner : TaskRunner
        Task runner for enqueueing tasks.
    task_definitions : list[ScheduledTaskDefinition] | None
        Optional list of task definitions. If None, uses default definitions.
    """

    def __init__(
        self,
        engine: Engine,  # type: ignore[name-defined]
        task_runner: TaskRunner,  # type: ignore[name-defined]
        task_definitions: list[ScheduledTaskDefinition] | None = None,
    ) -> None:
        """Initialize base scheduler.

        Parameters
        ----------
        engine : Engine
            Database engine.
        task_runner : TaskRunner
            Task runner instance.
        task_definitions : list[ScheduledTaskDefinition] | None
            Optional list of task definitions.
        """
        self._engine = engine
        self._task_runner = task_runner
        self._task_definitions = (
            task_definitions or self._get_default_task_definitions()
        )
        # Track last run time per task to avoid duplicate runs
        self._last_run_times: dict[TaskType, datetime] = {}
        self._lock = threading.Lock()
        self._shutdown = False

    @staticmethod
    def _get_default_task_definitions() -> list[ScheduledTaskDefinition]:
        """Get default task definitions.

        Returns
        -------
        list[ScheduledTaskDefinition]
            List of default scheduled task definitions.
        """
        return [
            ScheduledTaskDefinition(
                task_type=TaskType.EPUB_FIX_DAILY_SCAN,
                config_flag_getter=lambda cfg: cfg.epub_fixer_daily_scan,
                metadata_factory=lambda: {
                    "task_type": TaskType.EPUB_FIX_DAILY_SCAN.value
                },
            ),
        ]

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        raise NotImplementedError

    def _check_and_trigger_tasks(self, session: Session) -> None:
        """Check ScheduledTasksConfig and trigger tasks if needed.

        Parameters
        ----------
        session : Session
            Database session.
        """
        stmt = select(ScheduledTasksConfig).limit(1)
        config = session.exec(stmt).first()
        if config is None:
            return

        now = datetime.now(UTC)
        current_hour = now.hour

        # Check if we're in the scheduled time window
        if current_hour < config.start_time_hour:
            return
        if current_hour >= config.start_time_hour + config.duration_hours:
            return

        # Check each task definition
        for task_def in self._task_definitions:
            if task_def.config_flag_getter(config):
                self._trigger_task_if_needed(session, task_def, config, now)

    def _trigger_task_if_needed(
        self,
        session: Session,
        task_def: ScheduledTaskDefinition,
        config: ScheduledTasksConfig,
        now: datetime,
    ) -> None:
        """Trigger a scheduled task if it hasn't run recently.

        Parameters
        ----------
        session : Session
            Database session.
        task_def : ScheduledTaskDefinition
            Task definition to trigger.
        config : ScheduledTasksConfig
            Scheduled tasks configuration.
        now : datetime
            Current timestamp.
        """
        # Check if we should run at this time (within first 5 minutes of start hour)
        if now.hour != config.start_time_hour or now.minute >= 5:
            return

        # Check if we've already run today (avoid duplicate runs)
        with self._lock:
            last_run = self._last_run_times.get(task_def.task_type)
            if last_run and (now - last_run) < timedelta(hours=23):
                # Already ran in the last 23 hours, skip
                return

        system_user = self._get_system_user(session)
        if system_user is None or system_user.id is None:
            return

        # Generate payload and metadata
        payload = task_def.payload_factory() if task_def.payload_factory else {}
        metadata = task_def.metadata_factory() if task_def.metadata_factory else {}
        if "task_type" not in metadata:
            metadata["task_type"] = task_def.task_type.value

        # Trigger task
        try:
            task_id = self._task_runner.enqueue(
                task_type=task_def.task_type,
                payload=payload,
                user_id=system_user.id,
                metadata=metadata,
            )
            # Update last run time
            with self._lock:
                self._last_run_times[task_def.task_type] = now
            logger.info(
                "Triggered scheduled task %s: task_id=%d",
                task_def.task_type.value,
                task_id,
            )
        except Exception:
            logger.exception(
                "Failed to trigger scheduled task %s", task_def.task_type.value
            )

    @staticmethod
    def _get_system_user(session: Session) -> User | None:
        """Get system user for scheduled tasks.

        Returns first admin user, or first user if no admin exists.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        User | None
            System user, or None if no users exist.
        """
        stmt = select(User).where(User.is_admin == True).limit(1)  # noqa: E712
        system_user = session.exec(stmt).first()
        if system_user is None:
            # Fallback to first user if no admin exists
            stmt = select(User).limit(1)
            system_user = session.exec(stmt).first()

        if system_user is None or system_user.id is None:
            logger.error("No user found for system tasks")
            return None

        return system_user

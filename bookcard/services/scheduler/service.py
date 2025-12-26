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

"""APScheduler implementation for periodic tasks.

Replaces the custom TaskScheduler with a robust, industry-standard scheduler.
Supports cron-style scheduling, persistence, and proper timezone handling.
"""

import logging
from typing import TYPE_CHECKING, Any

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Engine
from sqlmodel import Session, select

from bookcard.models.auth import User
from bookcard.models.config import ScheduledJobDefinition
from bookcard.models.tasks import TaskType

if TYPE_CHECKING:
    from bookcard.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


class APSchedulerService:
    """Wrapper for APScheduler to integrate with Bookcard architecture.

    Manages the lifecycle of the BackgroundScheduler and handles dynamic
    job registration based on application configuration.
    """

    def __init__(
        self,
        engine: Engine,
        task_runner: "TaskRunner",
    ) -> None:
        """Initialize scheduler service.

        Parameters
        ----------
        engine : Engine
            Database engine for job persistence (if enabled) and config access.
        task_runner : TaskRunner
            Task runner for executing the actual tasks.
        """
        self._engine = engine
        self._task_runner = task_runner

        # Configure APScheduler
        # We use MemoryJobStore for now since our jobs are dynamic based on config
        # If we need persistence across restarts for specific one-off jobs, we can add SQLAlchemyJobStore
        self._scheduler = BackgroundScheduler(
            executors={
                "default": ThreadPoolExecutor(20),
            },
            job_defaults={
                "coalesce": True,  # Combine missed runs into one
                "max_instances": 1,  # Only one instance of a job at a time
            },
            timezone="UTC",
        )

    def start(self) -> None:
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("APScheduler started")

        # Initial job registration
        self.refresh_jobs()

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("APScheduler shut down")

    def refresh_jobs(self) -> None:
        """Refresh scheduled jobs based on current database configuration.

        Removes all existing jobs and re-registers them based on the latest config.
        This allows changing schedules without restarting the application.
        """
        try:
            with Session(self._engine) as session:
                stmt = select(ScheduledJobDefinition).where(
                    ScheduledJobDefinition.enabled
                )
                jobs = session.exec(stmt).all()

                if not jobs:
                    logger.warning("No enabled scheduled jobs found")
                    # We still clear existing jobs as the user might have disabled everything
                    self._scheduler.remove_all_jobs()
                    return

                system_user = self._get_system_user(session)
                if not system_user or not system_user.id:
                    logger.warning("No system user found, skipping job registration")
                    return

                # Clear existing jobs only if we proceed with registration
                self._scheduler.remove_all_jobs()

                for job in jobs:
                    user_id = job.user_id if job.user_id is not None else system_user.id
                    self._add_job(
                        task_type=job.task_type,
                        cron_expression=job.cron_expression,
                        user_id=user_id,
                        job_id=job.job_name,
                        payload=job.arguments,
                        job_metadata=job.job_metadata,
                    )

                logger.info(
                    "Refreshed scheduled jobs: %s",
                    [j.id for j in self._scheduler.get_jobs()],
                )

        except Exception:
            logger.exception("Failed to refresh scheduled jobs")

    def _add_job(
        self,
        task_type: TaskType,
        cron_expression: str,
        user_id: int,
        job_id: str,
        payload: dict[str, Any] | None = None,
        job_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a job to the scheduler.

        Parameters
        ----------
        task_type : TaskType
            Type of task to execute.
        cron_expression : str
            Cron expression for scheduling (e.g. "*/5 * * * *").
        user_id : int
            ID of user executing the task.
        job_id : str
            Unique identifier for the job.
        payload : dict[str, Any] | None
            Optional task payload.
        """
        payload = payload or {}
        metadata = {"task_type": task_type.value, "scheduled": True}
        if job_metadata:
            metadata.update(job_metadata)

        try:
            # CronTrigger.from_crontab raises ValueError if cron expression is invalid
            # It expects standard cron format: "minute hour day month day_of_week"
            # It does NOT support seconds in from_crontab, but APScheduler supports them via kwargs.
            # However, from_crontab is strict.
            # If cron_expression has 6 fields (seconds), we should use CronTrigger directly or adjust.
            # But here we are passing 5 fields "*/5 * * * *" and "0 4 * * *".
            # Ah, wait. "*/5 * * * *" is 5 fields.
            # "0 4 * * *" is 5 fields.

            # The error says "ValueError: Wrong number of fields; got 7, expected 5"
            # This is strange if we are passing 5 fields.
            # Unless apscheduler's CronTrigger.from_crontab expects something else or we have bad data in tests?

            # The issue might be related to how CronTrigger.from_crontab parses.
            # Let's try using CronTrigger directly which is more flexible.

            # Actually, standard cron is 5 fields.
            # Extended cron (Quartz/Spring) is 6-7.
            # APScheduler documentation says from_crontab takes a standard 5-field cron string.

            # Let's debug by logging the expression in the exception handler.
            trigger = CronTrigger.from_crontab(cron_expression, timezone="UTC")
        except ValueError:
            logger.exception("Invalid cron expression: '%s'", cron_expression)
            return

        self._scheduler.add_job(
            func=self._execute_task,
            trigger=trigger,
            id=job_id,
            args=[task_type, payload, user_id, metadata],
            replace_existing=True,
            name=f"Task: {task_type.value}",
        )

    def _execute_task(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Execute task callback (runs in scheduler thread pool)."""
        try:
            task_id = self._task_runner.enqueue(
                task_type=task_type,
                payload=payload,
                user_id=user_id,
                metadata=metadata,
            )
            logger.info("Scheduled task %s triggered (id=%s)", task_type.value, task_id)
        except Exception:
            logger.exception("Failed to trigger scheduled task %s", task_type.value)

    def _get_system_user(self, session: Session) -> User | None:
        """Get system user for scheduled tasks."""
        # Same logic as before: first admin, or first user
        stmt = select(User).where(User.is_admin == True).limit(1)  # noqa: E712
        system_user = session.exec(stmt).first()
        if not system_user:
            stmt = select(User).limit(1)
            system_user = session.exec(stmt).first()
        return system_user

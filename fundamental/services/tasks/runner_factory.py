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

"""Task runner factory for creating task runner instances.

Selects the appropriate task runner based on configuration.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from fundamental.services.tasks.factory import create_task
from fundamental.services.tasks.runner_celery import CeleryTaskRunner
from fundamental.services.tasks.runner_dramatiq import DramatiqTaskRunner
from fundamental.services.tasks.runner_thread import ThreadTaskRunner

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


def create_task_runner(engine: Engine) -> TaskRunner:
    """Create a task runner instance based on configuration.

    Reads TASK_RUNNER environment variable to determine which runner to use.
    Defaults to 'thread' if not specified.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine for database access.

    Returns
    -------
    TaskRunner
        Task runner instance.

    Raises
    ------
    ValueError
        If TASK_RUNNER is set to an unsupported value.
    """
    runner_type = os.getenv("TASK_RUNNER", "thread").lower()

    if runner_type == "thread":
        logger.info("Using thread-based task runner")
        return ThreadTaskRunner(engine, create_task)
    if runner_type == "dramatiq":
        logger.info("Using Dramatiq task runner (stub)")
        return DramatiqTaskRunner()
    if runner_type == "celery":
        logger.info("Using Celery task runner (stub)")
        return CeleryTaskRunner()
    msg = (
        f"Unknown task runner type: {runner_type}. Supported: thread, dramatiq, celery"
    )
    raise ValueError(msg)

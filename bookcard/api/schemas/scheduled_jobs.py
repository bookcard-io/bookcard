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

"""Scheduled job API schemas.

These schemas model the persistent scheduler registry stored in
``ScheduledJobDefinition`` and consumed by APScheduler.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field


class ScheduledJobRead(BaseModel):
    """Scheduled job definition representation (read)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_name: str
    description: str | None = None
    task_type: str
    cron_expression: str
    enabled: bool
    user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ScheduledJobUpdate(BaseModel):
    """Payload to update a scheduled job definition.

    Notes
    -----
    Validation of the cron expression's correctness is performed server-side
    using APScheduler's ``CronTrigger.from_crontab``.
    """

    enabled: bool | None = None
    cron_expression: str | None = Field(default=None, min_length=1, max_length=100)

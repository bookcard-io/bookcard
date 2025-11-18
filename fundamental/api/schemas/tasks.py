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

"""Task management API schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from fundamental.models.tasks import TaskStatus, TaskType  # noqa: TC001


class TaskRead(BaseModel):
    """Task representation for API responses.

    Attributes
    ----------
    id : int
        Task ID.
    task_type : TaskType
        Type of task.
    status : TaskStatus
        Current status.
    progress : float
        Progress (0.0 to 1.0).
    user_id : int
        User who created the task.
    username : str | None
        Username of the user who created the task.
    created_at : datetime
        Task creation timestamp.
    started_at : datetime | None
        Task start timestamp.
    completed_at : datetime | None
        Task completion timestamp.
    cancelled_at : datetime | None
        Task cancellation timestamp.
    error_message : str | None
        Error message if failed.
    metadata : dict | None
        Task metadata (mapped from task_data field).
    duration : float | None
        Task duration in seconds.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: TaskType
    status: TaskStatus
    progress: float = Field(ge=0.0, le=1.0)
    user_id: int
    username: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    error_message: str | None = None
    metadata: dict | None = None
    duration: float | None = None


class TaskListResponse(BaseModel):
    """Response for task list endpoint.

    Attributes
    ----------
    items : list[TaskRead]
        List of tasks.
    total : int
        Total number of tasks matching filters.
    page : int
        Current page number.
    page_size : int
        Number of items per page.
    total_pages : int
        Total number of pages.
    """

    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskCancelResponse(BaseModel):
    """Response for task cancellation.

    Attributes
    ----------
    success : bool
        Whether cancellation was successful.
    message : str
        Status message.
    """

    success: bool
    message: str


class TaskStatisticsRead(BaseModel):
    """Task statistics representation.

    Attributes
    ----------
    task_type : TaskType
        Type of task.
    avg_duration : float | None
        Average duration in seconds.
    min_duration : float | None
        Minimum duration in seconds.
    max_duration : float | None
        Maximum duration in seconds.
    total_count : int
        Total number of tasks.
    success_count : int
        Number of successful tasks.
    failure_count : int
        Number of failed tasks.
    last_run_at : datetime | None
        Timestamp of last execution.
    success_rate : float
        Success rate (0.0 to 1.0).
    """

    model_config = ConfigDict(from_attributes=True)

    task_type: TaskType
    avg_duration: float | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    total_count: int
    success_count: int
    failure_count: int
    last_run_at: datetime | None = None
    success_rate: float = Field(ge=0.0, le=1.0)


class TaskTypesResponse(BaseModel):
    """Response for available task types.

    Attributes
    ----------
    task_types : list[TaskType]
        List of available task types.
    """

    task_types: list[TaskType]

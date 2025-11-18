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

"""Task management endpoints for monitoring and controlling background tasks."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.schemas.tasks import (
    TaskCancelResponse,
    TaskListResponse,
    TaskRead,
    TaskStatisticsRead,
    TaskTypesResponse,
)
from fundamental.models.auth import User
from fundamental.models.tasks import Task, TaskStatus, TaskType
from fundamental.services.permission_service import PermissionService
from fundamental.services.task_service import TaskService

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

router = APIRouter(prefix="/tasks", tags=["tasks"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _get_task_runner(request: Request) -> TaskRunner | None:
    """Get task runner from app state.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    TaskRunner
        Task runner instance.

    Raises
    ------
    HTTPException
        If task runner is not initialized.
    """
    if not hasattr(request.app.state, "task_runner"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not initialized",
        )
    return request.app.state.task_runner


@router.get("", response_model=TaskListResponse)
def list_tasks(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: TaskStatus | None = Query(None, alias="status"),  # noqa: B008
    task_type: TaskType | None = Query(None, alias="task_type"),  # noqa: B008
) -> TaskListResponse:
    """List tasks with optional filters.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 50, max: 100).
    status : TaskStatus | None
        Optional status filter.
    task_type : TaskType | None
        Optional task type filter.

    Returns
    -------
    TaskListResponse
        Paginated list of tasks.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "tasks", "read")

    # For non-admin users, only show their own tasks
    user_id = current_user.id if not current_user.is_admin else None

    task_service = TaskService(session)
    tasks = task_service.list_tasks(
        user_id=user_id,
        status=status,
        task_type=task_type,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    # Convert to TaskRead with duration
    logger = logging.getLogger(__name__)
    task_reads = []
    for task in tasks:
        # Extract Task from Row if needed (fallback in case service didn't handle it)
        if not isinstance(task, Task):
            mapping = getattr(task, "_mapping", None)
            if mapping is not None and "Task" in mapping:
                task = mapping["Task"]
            elif hasattr(task, "__getitem__"):
                try:
                    task = task[0]
                except (IndexError, KeyError):
                    logger.exception(
                        "Could not extract Task from Row in route: %s", type(task)
                    )
                    continue

        task_read = TaskRead(
            id=task.id or 0,
            task_type=task.task_type,
            status=task.status,
            progress=task.progress,
            user_id=task.user_id,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            cancelled_at=task.cancelled_at,
            error_message=task.error_message,
            metadata=task.task_data,
            duration=task.duration,
        )
        task_reads.append(task_read)

    # Get total count - need to query separately for accurate count
    # For now, estimate: if we got a full page, there might be more
    # In production, use COUNT query with same filters
    if len(task_reads) == page_size:
        # Likely more results, estimate
        total = page_size * (page + 1)
    else:
        total = (page - 1) * page_size + len(task_reads)
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return TaskListResponse(
        items=task_reads,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
) -> TaskRead:
    """Get a task by ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    task_id : int
        Task ID.

    Returns
    -------
    TaskRead
        Task details.

    Raises
    ------
    HTTPException
        If task not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "tasks", "read")

    task_service = TaskService(session)
    # For non-admin users, only allow viewing their own tasks
    user_id = current_user.id if not current_user.is_admin else None
    task = task_service.get_task(task_id, user_id=user_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task_not_found",
        )

    return TaskRead(
        id=task.id or 0,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        user_id=task.user_id,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        cancelled_at=task.cancelled_at,
        error_message=task.error_message,
        metadata=task.task_data,
        duration=task.duration,
    )


@router.post("/{task_id}/cancel", response_model=TaskCancelResponse)
def cancel_task(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
) -> TaskCancelResponse:
    """Cancel a task.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    task_id : int
        Task ID to cancel.

    Returns
    -------
    TaskCancelResponse
        Cancellation result.

    Raises
    ------
    HTTPException
        If task not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "tasks", "write")

    task_service = TaskService(session)
    # For non-admin users, only allow cancelling their own tasks
    user_id = current_user.id if not current_user.is_admin else None

    # Check if task exists and user has permission
    task = task_service.get_task(task_id, user_id=user_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task_not_found",
        )

    # Cancel via task runner
    task_runner = _get_task_runner(request)
    if task_runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    success = task_runner.cancel(task_id)

    if success:
        return TaskCancelResponse(success=True, message="Task cancelled successfully")
    return TaskCancelResponse(success=False, message="Task could not be cancelled")


@router.get("/statistics", response_model=list[TaskStatisticsRead])
def get_task_statistics(
    session: SessionDep,
    current_user: CurrentUserDep,
    task_type: TaskType | None = Query(None, alias="task_type"),  # noqa: B008
) -> list[TaskStatisticsRead]:
    """Get task statistics.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    task_type : TaskType | None
        Optional task type filter.

    Returns
    -------
    list[TaskStatisticsRead]
        List of task statistics.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission (admin only for statistics)
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "tasks", "read")

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view task statistics",
        )

    task_service = TaskService(session)
    stats_list = task_service.get_task_statistics(task_type=task_type)

    # Convert to TaskStatisticsRead with success_rate
    result = []
    for stats in stats_list:
        success_rate = (
            stats.success_count / stats.total_count if stats.total_count > 0 else 0.0
        )
        result.append(
            TaskStatisticsRead(
                task_type=stats.task_type,
                avg_duration=stats.avg_duration,
                min_duration=stats.min_duration,
                max_duration=stats.max_duration,
                total_count=stats.total_count,
                success_count=stats.success_count,
                failure_count=stats.failure_count,
                last_run_at=stats.last_run_at,
                success_rate=success_rate,
            ),
        )

    return result


@router.get("/types", response_model=TaskTypesResponse)
def get_task_types(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TaskTypesResponse:
    """Get list of available task types.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    TaskTypesResponse
        List of available task types.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "tasks", "read")

    return TaskTypesResponse(task_types=list(TaskType))

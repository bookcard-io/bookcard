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

"""Ingest management API routes.

Routes for managing automatic book ingestion. Routes only handle HTTP,
delegating business logic to services.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, desc, select

from fundamental.api.deps import get_admin_user, get_current_user, get_db_session
from fundamental.api.schemas.ingest import (
    IngestConfigResponse,
    IngestConfigUpdate,
    IngestHistoryListResponse,
    IngestHistoryResponse,
    IngestRetryResponse,
    IngestScanResponse,
)
from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.repositories.ingest_repository import (
    IngestHistoryRepository,
)
from fundamental.services.ingest.ingest_config_service import IngestConfigService

if TYPE_CHECKING:
    from fundamental.models.auth import User
    from fundamental.services.ingest.ingest_watcher_service import IngestWatcherService
    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated["User", Depends(get_current_user)]
AdminUserDep = Annotated["User", Depends(get_admin_user)]


def _get_task_runner(request: Request) -> TaskRunner | None:
    """Get task runner from app state.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    TaskRunner | None
        Task runner instance, or None if not available.
    """
    if not hasattr(request.app.state, "task_runner"):
        return None
    return request.app.state.task_runner


def _get_ingest_watcher(request: Request) -> IngestWatcherService | None:
    """Get ingest watcher from app state.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    IngestWatcherService | None
        Watcher service instance, or None if not available.
    """
    if not hasattr(request.app.state, "ingest_watcher"):
        return None
    return request.app.state.ingest_watcher


@router.get(
    "/config",
    response_model=IngestConfigResponse,
    dependencies=[Depends(get_admin_user)],
)
def get_ingest_config(
    session: SessionDep,
) -> IngestConfigResponse:
    """Get ingest configuration.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IngestConfigResponse
        Ingest configuration.
    """
    config_service = IngestConfigService(session)
    config = config_service.get_config()
    return IngestConfigResponse.model_validate(config)


@router.put(
    "/config",
    response_model=IngestConfigResponse,
    dependencies=[Depends(get_admin_user)],
)
def update_ingest_config(
    session: SessionDep,
    config_update: IngestConfigUpdate,
) -> IngestConfigResponse:
    """Update ingest configuration.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    config_update : IngestConfigUpdate
        Configuration updates.

    Returns
    -------
    IngestConfigResponse
        Updated configuration.
    """
    config_service = IngestConfigService(session)
    update_dict = config_update.model_dump(exclude_unset=True)
    config = config_service.update_config(**update_dict)
    return IngestConfigResponse.model_validate(config)


@router.get(
    "/history",
    response_model=IngestHistoryListResponse,
    dependencies=[Depends(get_admin_user)],
)
def list_ingest_history(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: IngestStatus | None = Query(None, alias="status"),  # noqa: B008
) -> IngestHistoryListResponse:
    """List ingest history with pagination.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 50, max: 100).
    status : IngestStatus | None
        Optional status filter.

    Returns
    -------
    IngestHistoryListResponse
        Paginated ingest history.
    """
    # Build query
    stmt = select(IngestHistory)
    if status:
        stmt = stmt.where(IngestHistory.status == status)

    # Count total
    count_stmt = select(IngestHistory)
    if status:
        count_stmt = count_stmt.where(IngestHistory.status == status)
    total = len(list(session.exec(count_stmt).all()))

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(desc(IngestHistory.created_at)).offset(offset).limit(page_size)

    items = list(session.exec(stmt).all())
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return IngestHistoryListResponse(
        items=[IngestHistoryResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/history/{history_id}",
    response_model=IngestHistoryResponse,
    dependencies=[Depends(get_admin_user)],
)
def get_ingest_history(
    session: SessionDep,
    history_id: int,
) -> IngestHistoryResponse:
    """Get ingest history details.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    history_id : int
        Ingest history ID.

    Returns
    -------
    IngestHistoryResponse
        Ingest history details.

    Raises
    ------
    HTTPException
        If history not found.
    """
    history_repo = IngestHistoryRepository(session)
    history = history_repo.get(history_id)

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingest history {history_id} not found",
        )

    return IngestHistoryResponse.model_validate(history)


@router.post(
    "/scan",
    response_model=IngestScanResponse,
    dependencies=[Depends(get_admin_user)],
)
def trigger_scan(
    request: Request,
    current_user: AdminUserDep,
) -> IngestScanResponse:
    """Manually trigger a directory scan.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    current_user : AdminUserDep
        Current authenticated admin user.

    Returns
    -------
    IngestScanResponse
        Scan task information.

    Raises
    ------
    HTTPException
        If task runner or watcher not available.
    """
    watcher = _get_ingest_watcher(request)
    if watcher:
        task_id = watcher.trigger_manual_scan()
        if task_id is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to trigger scan",
            )
        return IngestScanResponse(task_id=task_id, message="Scan triggered")

    # Fallback: use task runner directly
    task_runner = _get_task_runner(request)
    if not task_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )

    from fundamental.models.tasks import TaskType

    task_id = task_runner.enqueue(
        task_type=TaskType.INGEST_DISCOVERY,
        payload={},
        user_id=current_user.id or 0,
        metadata={"task_type": TaskType.INGEST_DISCOVERY.value},
    )
    return IngestScanResponse(task_id=task_id, message="Scan triggered")


@router.post(
    "/retry/{history_id}",
    response_model=IngestRetryResponse,
    dependencies=[Depends(get_admin_user)],
)
def retry_ingest(
    request: Request,
    session: SessionDep,
    current_user: AdminUserDep,
    history_id: int,
) -> IngestRetryResponse:
    """Manually retry a failed ingest.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : AdminUserDep
        Current authenticated admin user.
    history_id : int
        Ingest history ID to retry.

    Returns
    -------
    IngestRetryResponse
        Retry operation result.

    Raises
    ------
    HTTPException
        If history not found, not failed, or task runner not available.
    """
    history_repo = IngestHistoryRepository(session)
    history = history_repo.get(history_id)

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingest history {history_id} not found",
        )

    if history.status != IngestStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingest history {history_id} is not in failed status",
        )

    # Get file group info from history
    ingest_metadata = history.ingest_metadata or {}
    files = ingest_metadata.get("files", [])
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files found in ingest history",
        )

    # Queue IngestBookTask
    task_runner = _get_task_runner(request)
    if not task_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )

    from fundamental.models.tasks import TaskType

    task_id = task_runner.enqueue(
        task_type=TaskType.INGEST_BOOK,
        payload={},
        user_id=current_user.id or 0,
        metadata={
            "task_type": TaskType.INGEST_BOOK.value,
            "history_id": history_id,
        },
    )

    logger.info("Queued retry task %d for ingest history %d", task_id, history_id)

    return IngestRetryResponse(
        message="Retry queued",
        history_id=history_id,
    )

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

"""API routes for EPUB fixer operations.

Endpoints for fixing EPUB files, viewing fix history, and managing fix runs.
"""

import logging
import math
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas.epub_fixer import (
    EPUBFixBatchRequest,
    EPUBFixListResponse,
    EPUBFixRead,
    EPUBFixResponse,
    EPUBFixRollbackResponse,
    EPUBFixRunListResponse,
    EPUBFixRunRead,
    EPUBFixSingleRequest,
    EPUBFixStatisticsRead,
)
from bookcard.models.auth import User
from bookcard.models.tasks import TaskType
from bookcard.services.epub_fixer_service import EPUBFixerService
from bookcard.services.permission_service import PermissionService

if TYPE_CHECKING:
    from bookcard.services.tasks.base import TaskRunner

router = APIRouter(prefix="/epub-fixer", tags=["epub-fixer"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

logger = logging.getLogger(__name__)


def _get_task_runner(request: Request) -> "TaskRunner | None":
    """Get task runner from app state.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    TaskRunner | None
        Task runner instance or None if not available.
    """
    if not hasattr(request.app.state, "task_runner"):
        return None
    return request.app.state.task_runner


@router.post(
    "/fix-single", response_model=EPUBFixResponse, status_code=status.HTTP_201_CREATED
)
def fix_single_epub(
    request_body: EPUBFixSingleRequest,
    http_request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixResponse:
    """Fix a single EPUB file.

    Parameters
    ----------
    request_body : EPUBFixSingleRequest
        Request with file path and optional metadata.
    http_request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixResponse
        Task ID and message.

    Raises
    ------
    HTTPException
        If permission denied or task runner unavailable.
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "write")

    # Get task runner
    task_runner = _get_task_runner(http_request)
    if task_runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )

    # Prepare metadata
    metadata = {
        "task_type": TaskType.EPUB_FIX_SINGLE.value,
        "file_path": request_body.file_path,
    }
    if request_body.book_id is not None:
        metadata["book_id"] = request_body.book_id
    if request_body.book_title:
        metadata["book_title"] = request_body.book_title
    if request_body.library_id is not None:
        metadata["library_id"] = request_body.library_id

    # Enqueue task
    try:
        task_id = task_runner.enqueue(
            task_type=TaskType.EPUB_FIX_SINGLE,
            payload={},  # Empty payload, all data in metadata
            user_id=current_user.id,  # type: ignore[arg-type]
            metadata=metadata,
        )
        return EPUBFixResponse(
            task_id=task_id,
            message=f"EPUB fix task created for {request_body.file_path}",
        )
    except Exception as e:
        logger.exception("Failed to enqueue EPUB fix task")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fix task: {e}",
        ) from e


@router.post(
    "/fix-batch", response_model=EPUBFixResponse, status_code=status.HTTP_201_CREATED
)
def fix_batch_epub(
    request_body: EPUBFixBatchRequest,
    http_request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixResponse:
    """Fix EPUB files in batch (library scan).

    Parameters
    ----------
    request_body : EPUBFixBatchRequest
        Request with optional library ID.
    http_request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixResponse
        Task ID and message.

    Raises
    ------
    HTTPException
        If permission denied or task runner unavailable.
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "write")

    # Get task runner
    task_runner = _get_task_runner(http_request)
    if task_runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )

    # Prepare metadata
    metadata = {
        "task_type": TaskType.EPUB_FIX_BATCH.value,
    }
    if request_body.library_id is not None:
        metadata["library_id"] = request_body.library_id

    # Enqueue task
    try:
        task_id = task_runner.enqueue(
            task_type=TaskType.EPUB_FIX_BATCH,
            payload={},  # Empty payload, all data in metadata
            user_id=current_user.id,  # type: ignore[arg-type]
            metadata=metadata,
        )
        return EPUBFixResponse(
            task_id=task_id,
            message="EPUB batch fix task created",
        )
    except Exception as e:
        logger.exception("Failed to enqueue EPUB batch fix task")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch fix task: {e}",
        ) from e


@router.get("/runs", response_model=EPUBFixRunListResponse)
def list_fix_runs(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> EPUBFixRunListResponse:
    """List EPUB fix runs with pagination.

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

    Returns
    -------
    EPUBFixRunListResponse
        Paginated list of fix runs.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "read")

    fixer_service = EPUBFixerService(session)
    offset = (page - 1) * page_size

    # For non-admin users, only show their own runs
    if not current_user.is_admin:
        runs = fixer_service.get_runs_by_user(
            user_id=current_user.id,  # type: ignore[arg-type]
            limit=page_size,
            offset=offset,
        )
    else:
        # For admin users, get all recent runs with pagination
        runs = fixer_service.get_recent_runs(limit=page_size + offset)
        # Apply offset manually (not ideal, but get_recent_runs doesn't support offset)
        runs = runs[offset:]

    # Convert to response models
    run_reads = [
        EPUBFixRunRead(
            id=run.id or 0,
            user_id=run.user_id,
            library_id=run.library_id,
            manually_triggered=run.manually_triggered,
            is_bulk_operation=run.is_bulk_operation,
            total_files_processed=run.total_files_processed,
            total_files_fixed=run.total_files_fixed,
            total_fixes_applied=run.total_fixes_applied,
            backup_enabled=run.backup_enabled,
            started_at=run.started_at,
            completed_at=run.completed_at,
            cancelled_at=run.cancelled_at,
            error_message=run.error_message,
            created_at=run.created_at,
            duration=run.duration,
        )
        for run in runs
    ]

    # Estimate total (in production, use COUNT query)
    if len(run_reads) == page_size:
        total = page_size * (page + 1)
    else:
        total = (page - 1) * page_size + len(run_reads)
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return EPUBFixRunListResponse(
        items=run_reads,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/runs/{run_id}", response_model=EPUBFixRunRead)
def get_fix_run(
    run_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixRunRead:
    """Get a fix run by ID.

    Parameters
    ----------
    run_id : int
        Fix run ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixRunRead
        Fix run details.

    Raises
    ------
    HTTPException
        If run not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "read")

    fixer_service = EPUBFixerService(session)
    run = fixer_service.get_fix_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fix run not found",
        )

    # For non-admin users, only allow viewing their own runs
    if not current_user.is_admin and run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return EPUBFixRunRead(
        id=run.id or 0,
        user_id=run.user_id,
        library_id=run.library_id,
        manually_triggered=run.manually_triggered,
        is_bulk_operation=run.is_bulk_operation,
        total_files_processed=run.total_files_processed,
        total_files_fixed=run.total_files_fixed,
        total_fixes_applied=run.total_fixes_applied,
        backup_enabled=run.backup_enabled,
        started_at=run.started_at,
        completed_at=run.completed_at,
        cancelled_at=run.cancelled_at,
        error_message=run.error_message,
        created_at=run.created_at,
        duration=run.duration,
    )


@router.get("/runs/{run_id}/fixes", response_model=EPUBFixListResponse)
def get_fixes_for_run(
    run_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixListResponse:
    """Get all fixes for a fix run.

    Parameters
    ----------
    run_id : int
        Fix run ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixListResponse
        List of fixes.

    Raises
    ------
    HTTPException
        If run not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "read")

    fixer_service = EPUBFixerService(session)
    run = fixer_service.get_fix_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fix run not found",
        )

    # For non-admin users, only allow viewing their own runs
    if not current_user.is_admin and run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    fixes = fixer_service.get_fixes_for_run(run_id)

    fix_reads = [
        EPUBFixRead(
            id=fix.id or 0,
            run_id=fix.run_id or 0,
            book_id=fix.book_id,
            book_title=fix.book_title,
            file_path=fix.file_path,
            original_file_path=fix.original_file_path,
            fix_type=fix.fix_type,
            fix_description=fix.fix_description,
            file_name=fix.file_name,
            original_value=fix.original_value,
            fixed_value=fix.fixed_value,
            backup_created=fix.backup_created,
            created_at=fix.created_at,
        )
        for fix in fixes
    ]

    return EPUBFixListResponse(items=fix_reads, total=len(fix_reads))


@router.post("/runs/{run_id}/rollback", response_model=EPUBFixRollbackResponse)
def rollback_fix_run(
    run_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixRollbackResponse:
    """Rollback a fix run, restoring original files from backups.

    Parameters
    ----------
    run_id : int
        Fix run ID to rollback.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixRollbackResponse
        Rollback result with number of files restored.

    Raises
    ------
    HTTPException
        If run not found (404), permission denied (403), or rollback failed (400).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "write")

    fixer_service = EPUBFixerService(session)
    run = fixer_service.get_fix_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fix run not found",
        )

    # For non-admin users, only allow rolling back their own runs
    if not current_user.is_admin and run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    try:
        rolled_back_run = fixer_service.rollback_fix_run(run_id)
        fixes = fixer_service.get_fixes_for_run(run_id)
        files_restored = sum(
            1 for fix in fixes if fix.backup_created and fix.original_file_path
        )

        return EPUBFixRollbackResponse(
            run_id=rolled_back_run.id or 0,
            files_restored=files_restored,
            message=f"Rolled back fix run {run_id}, restored {files_restored} file(s)",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("Failed to rollback fix run %d", run_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback: {e}",
        ) from e


@router.get("/statistics", response_model=EPUBFixStatisticsRead)
def get_fix_statistics(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EPUBFixStatisticsRead:
    """Get EPUB fix statistics.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EPUBFixStatisticsRead
        Fix statistics.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "read")

    fixer_service = EPUBFixerService(session)
    stats = fixer_service.get_statistics()
    fixes_by_type_raw = fixer_service.get_fix_statistics_by_type()

    # Convert dict[str, int] to dict[EPUBFixType, int]
    from bookcard.models.epub_fixer import EPUBFixType

    fixes_by_type: dict[EPUBFixType, int] = {}
    for fix_type_str, count in fixes_by_type_raw.items():
        try:
            fix_type = EPUBFixType(fix_type_str)
            fixes_by_type[fix_type] = count
        except ValueError:
            # Skip invalid fix types
            continue

    return EPUBFixStatisticsRead(
        total_runs=int(stats.get("total_runs", 0) or 0),
        total_files_processed=int(stats.get("total_files_processed", 0) or 0),
        total_files_fixed=int(stats.get("total_files_fixed", 0) or 0),
        total_fixes_applied=int(stats.get("total_fixes_applied", 0) or 0),
        fixes_by_type=fixes_by_type,
    )

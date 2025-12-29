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

"""Indexer management endpoints.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from bookcard.api.deps import get_admin_user, get_data_encryptor, get_db_session
from bookcard.api.schemas.indexers import (
    IndexerCreate,
    IndexerListResponse,
    IndexerRead,
    IndexerStatusResponse,
    IndexerTestResponse,
    IndexerUpdate,
)
from bookcard.models.auth import User
from bookcard.models.config import ScheduledJobDefinition
from bookcard.models.tasks import TaskType
from bookcard.services.config_service import ScheduledTasksConfigService
from bookcard.services.indexer_service import IndexerService

router = APIRouter(prefix="/indexers", tags=["indexers"])

SessionDep = Annotated[Session, Depends(get_db_session)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]


def _get_indexer_service(session: SessionDep, request: Request) -> IndexerService:
    """Create IndexerService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerService
        Indexer service instance.
    """
    encryptor = get_data_encryptor(request)
    return IndexerService(session, encryptor=encryptor)


def _raise_not_found(indexer_id: int) -> None:
    """Raise HTTPException for indexer not found.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.

    Raises
    ------
    HTTPException
        Always raises with 404 status code.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Indexer {indexer_id} not found",
    )


@router.get(
    "",
    response_model=IndexerListResponse,
    dependencies=[Depends(get_admin_user)],
)
def list_indexers(
    session: SessionDep,
    request: Request,
    enabled_only: bool = Query(
        default=False, description="Only return enabled indexers"
    ),
) -> IndexerListResponse:
    """List all indexers.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.
    enabled_only : bool
        If True, only return enabled indexers.

    Returns
    -------
    IndexerListResponse
        List of indexers.
    """
    service = _get_indexer_service(session, request)
    indexers = service.list_indexers(enabled_only=enabled_only)
    return IndexerListResponse(
        items=[IndexerRead.model_validate(indexer) for indexer in indexers],
        total=len(indexers),
    )


@router.get(
    "/{indexer_id}",
    response_model=IndexerRead,
    dependencies=[Depends(get_admin_user)],
)
def get_indexer(
    indexer_id: int,
    session: SessionDep,
    request: Request,
) -> IndexerRead:
    """Get an indexer by ID.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerRead
        Indexer data.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session, request)
    indexer = service.get_indexer(indexer_id)
    if indexer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indexer {indexer_id} not found",
        )
    return IndexerRead.model_validate(indexer)


@router.post(
    "",
    response_model=IndexerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_indexer(
    data: IndexerCreate,
    session: SessionDep,
    request: Request,
) -> IndexerRead:
    """Create a new indexer.

    Parameters
    ----------
    data : IndexerCreate
        Indexer creation data.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerRead
        Created indexer.

    Raises
    ------
    HTTPException
        If indexer creation fails.
    """
    service = _get_indexer_service(session, request)
    try:
        indexer = service.create_indexer(data)

        # Register health check task if it doesn't exist
        stmt = select(ScheduledJobDefinition).where(
            ScheduledJobDefinition.job_name == "indexer_health_check"
        )
        job = session.exec(stmt).first()
        if not job:
            scheduled_tasks_service = ScheduledTasksConfigService(session)
            scheduled_tasks_service.register_job(
                task_type=TaskType.INDEXER_HEALTH_CHECK,
                cron_expression="0 4 * * *",  # Daily at 4 AM
                enabled=True,
                job_name="indexer_health_check",
            )
            if hasattr(request.app.state, "scheduler") and request.app.state.scheduler:
                request.app.state.scheduler.refresh_jobs()

        return IndexerRead.model_validate(indexer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create indexer: {e}",
        ) from e


@router.put(
    "/{indexer_id}",
    response_model=IndexerRead,
    dependencies=[Depends(get_admin_user)],
)
def update_indexer(
    indexer_id: int,
    data: IndexerUpdate,
    session: SessionDep,
    request: Request,
) -> IndexerRead:
    """Update an indexer.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    data : IndexerUpdate
        Update data (partial).
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerRead
        Updated indexer.

    Raises
    ------
    HTTPException
        If indexer not found or update fails.
    """
    service = _get_indexer_service(session, request)
    try:
        indexer = service.update_indexer(indexer_id, data)
        if indexer is None:
            _raise_not_found(indexer_id)

        # Register health check task if it doesn't exist
        stmt = select(ScheduledJobDefinition).where(
            ScheduledJobDefinition.job_name == "indexer_health_check"
        )
        job = session.exec(stmt).first()
        if not job:
            scheduled_tasks_service = ScheduledTasksConfigService(session)
            scheduled_tasks_service.register_job(
                task_type=TaskType.INDEXER_HEALTH_CHECK,
                cron_expression="0 4 * * *",  # Daily at 4 AM
                enabled=True,
                job_name="indexer_health_check",
            )
            if hasattr(request.app.state, "scheduler") and request.app.state.scheduler:
                request.app.state.scheduler.refresh_jobs()

        return IndexerRead.model_validate(indexer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update indexer: {e}",
        ) from e


@router.delete(
    "/{indexer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_indexer(
    indexer_id: int,
    session: SessionDep,
    request: Request,
) -> None:
    """Delete an indexer.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session, request)
    deleted = service.delete_indexer(indexer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indexer {indexer_id} not found",
        )


@router.post(
    "/test",
    response_model=IndexerTestResponse,
    dependencies=[Depends(get_admin_user)],
)
def test_indexer_settings(
    data: IndexerCreate,
    session: SessionDep,
    request: Request,
) -> IndexerTestResponse:
    """Test connection with provided settings.

    Parameters
    ----------
    data : IndexerCreate
        Indexer settings.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerTestResponse
        Test result.

    Raises
    ------
    HTTPException
        If test fails.
    """
    service = _get_indexer_service(session, request)
    try:
        success, message = service.test_connection_with_settings(data)
        return IndexerTestResponse(success=success, message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test indexer connection: {e}",
        ) from e


@router.post(
    "/{indexer_id}/test",
    response_model=IndexerTestResponse,
    dependencies=[Depends(get_admin_user)],
)
def test_indexer_connection(
    indexer_id: int,
    session: SessionDep,
    request: Request,
) -> IndexerTestResponse:
    """Test connection to an indexer.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerTestResponse
        Test result.

    Raises
    ------
    HTTPException
        If indexer not found or test fails.
    """
    service = _get_indexer_service(session, request)
    try:
        success, message = service.test_connection(indexer_id)
        return IndexerTestResponse(success=success, message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test indexer connection: {e}",
        ) from e


@router.get(
    "/{indexer_id}/status",
    response_model=IndexerStatusResponse,
    dependencies=[Depends(get_admin_user)],
)
def get_indexer_status(
    indexer_id: int,
    session: SessionDep,
    request: Request,
) -> IndexerStatusResponse:
    """Get indexer status information.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.
    request : Request
        FastAPI request object.

    Returns
    -------
    IndexerStatusResponse
        Indexer status information.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session, request)
    indexer = service.get_indexer_status(indexer_id)
    if indexer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indexer {indexer_id} not found",
        )
    return IndexerStatusResponse.model_validate(indexer)

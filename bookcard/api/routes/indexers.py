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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from bookcard.api.deps import get_admin_user, get_db_session
from bookcard.api.schemas.indexers import (
    IndexerCreate,
    IndexerListResponse,
    IndexerRead,
    IndexerStatusResponse,
    IndexerTestResponse,
    IndexerUpdate,
)
from bookcard.models.auth import User
from bookcard.services.indexer_service import IndexerService

router = APIRouter(prefix="/indexers", tags=["indexers"])

SessionDep = Annotated[Session, Depends(get_db_session)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]


def _get_indexer_service(session: SessionDep) -> IndexerService:
    """Create IndexerService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerService
        Indexer service instance.
    """
    return IndexerService(session)


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
    enabled_only: bool = Query(
        default=False, description="Only return enabled indexers"
    ),
) -> IndexerListResponse:
    """List all indexers.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    enabled_only : bool
        If True, only return enabled indexers.

    Returns
    -------
    IndexerListResponse
        List of indexers.
    """
    service = _get_indexer_service(session)
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
) -> IndexerRead:
    """Get an indexer by ID.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerRead
        Indexer data.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session)
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
) -> IndexerRead:
    """Create a new indexer.

    Parameters
    ----------
    data : IndexerCreate
        Indexer creation data.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerRead
        Created indexer.

    Raises
    ------
    HTTPException
        If indexer creation fails.
    """
    service = _get_indexer_service(session)
    try:
        indexer = service.create_indexer(data)
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

    Returns
    -------
    IndexerRead
        Updated indexer.

    Raises
    ------
    HTTPException
        If indexer not found or update fails.
    """
    service = _get_indexer_service(session)
    try:
        indexer = service.update_indexer(indexer_id, data)
        if indexer is None:
            _raise_not_found(indexer_id)
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
) -> None:
    """Delete an indexer.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session)
    deleted = service.delete_indexer(indexer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indexer {indexer_id} not found",
        )


@router.post(
    "/{indexer_id}/test",
    response_model=IndexerTestResponse,
    dependencies=[Depends(get_admin_user)],
)
def test_indexer_connection(
    indexer_id: int,
    session: SessionDep,
) -> IndexerTestResponse:
    """Test connection to an indexer.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerTestResponse
        Test result.

    Raises
    ------
    HTTPException
        If indexer not found or test fails.
    """
    service = _get_indexer_service(session)
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
) -> IndexerStatusResponse:
    """Get indexer status information.

    Parameters
    ----------
    indexer_id : int
        Indexer ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerStatusResponse
        Indexer status information.

    Raises
    ------
    HTTPException
        If indexer not found.
    """
    service = _get_indexer_service(session)
    indexer = service.get_indexer_status(indexer_id)
    if indexer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indexer {indexer_id} not found",
        )
    return IndexerStatusResponse.model_validate(indexer)

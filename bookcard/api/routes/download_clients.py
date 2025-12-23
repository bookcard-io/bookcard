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

"""Download client management endpoints.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from bookcard.api.deps import get_admin_user, get_db_session
from bookcard.api.schemas.download_clients import (
    DownloadClientCreate,
    DownloadClientListResponse,
    DownloadClientRead,
    DownloadClientStatusResponse,
    DownloadClientTestResponse,
    DownloadClientUpdate,
    DownloadItemResponse,
    DownloadItemsResponse,
)
from bookcard.models.auth import User
from bookcard.services.download_client_service import DownloadClientService

router = APIRouter(prefix="/download-clients", tags=["download-clients"])

SessionDep = Annotated[Session, Depends(get_db_session)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]


def _get_download_client_service(
    session: SessionDep,
) -> DownloadClientService:
    """Create DownloadClientService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientService
        Download client service instance.
    """
    return DownloadClientService(session)


def _raise_not_found(client_id: int) -> None:
    """Raise HTTPException for download client not found.

    Parameters
    ----------
    client_id : int
        Download client ID.

    Raises
    ------
    HTTPException
        Always raises with 404 status code.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Download client {client_id} not found",
    )


@router.get(
    "",
    response_model=DownloadClientListResponse,
    dependencies=[Depends(get_admin_user)],
)
def list_download_clients(
    session: SessionDep,
    enabled_only: bool = Query(
        default=False, description="Only return enabled download clients"
    ),
) -> DownloadClientListResponse:
    """List all download clients.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    enabled_only : bool
        If True, only return enabled download clients.

    Returns
    -------
    DownloadClientListResponse
        List of download clients.
    """
    service = _get_download_client_service(session)
    clients = service.list_download_clients(enabled_only=enabled_only)
    return DownloadClientListResponse(
        items=[DownloadClientRead.model_validate(client) for client in clients],
        total=len(clients),
    )


@router.get(
    "/{client_id}",
    response_model=DownloadClientRead,
    dependencies=[Depends(get_admin_user)],
)
def get_download_client(
    client_id: int,
    session: SessionDep,
) -> DownloadClientRead:
    """Get a download client by ID.

    Parameters
    ----------
    client_id : int
        Download client ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientRead
        Download client data.

    Raises
    ------
    HTTPException
        If download client not found.
    """
    service = _get_download_client_service(session)
    client = service.get_download_client(client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download client {client_id} not found",
        )
    return DownloadClientRead.model_validate(client)


@router.post(
    "",
    response_model=DownloadClientRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_download_client(
    data: DownloadClientCreate,
    session: SessionDep,
) -> DownloadClientRead:
    """Create a new download client.

    Parameters
    ----------
    data : DownloadClientCreate
        Download client creation data.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientRead
        Created download client.

    Raises
    ------
    HTTPException
        If download client creation fails.
    """
    service = _get_download_client_service(session)
    try:
        client = service.create_download_client(data)
        return DownloadClientRead.model_validate(client)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download client: {e}",
        ) from e


@router.put(
    "/{client_id}",
    response_model=DownloadClientRead,
    dependencies=[Depends(get_admin_user)],
)
def update_download_client(
    client_id: int,
    data: DownloadClientUpdate,
    session: SessionDep,
) -> DownloadClientRead:
    """Update a download client.

    Parameters
    ----------
    client_id : int
        Download client ID.
    data : DownloadClientUpdate
        Update data (partial).
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientRead
        Updated download client.

    Raises
    ------
    HTTPException
        If download client not found or update fails.
    """
    service = _get_download_client_service(session)
    try:
        client = service.update_download_client(client_id, data)
        if client is None:
            _raise_not_found(client_id)
        return DownloadClientRead.model_validate(client)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update download client: {e}",
        ) from e


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_download_client(
    client_id: int,
    session: SessionDep,
) -> None:
    """Delete a download client.

    Parameters
    ----------
    client_id : int
        Download client ID.
    session : SessionDep
        Database session dependency.

    Raises
    ------
    HTTPException
        If download client not found.
    """
    service = _get_download_client_service(session)
    deleted = service.delete_download_client(client_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download client {client_id} not found",
        )


@router.post(
    "/{client_id}/test",
    response_model=DownloadClientTestResponse,
    dependencies=[Depends(get_admin_user)],
)
def test_download_client_connection(
    client_id: int,
    session: SessionDep,
) -> DownloadClientTestResponse:
    """Test connection to a download client.

    Parameters
    ----------
    client_id : int
        Download client ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientTestResponse
        Test result.

    Raises
    ------
    HTTPException
        If download client not found or test fails.
    """
    service = _get_download_client_service(session)
    try:
        success, message = service.test_connection(client_id)
        return DownloadClientTestResponse(success=success, message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test download client connection: {e}",
        ) from e


@router.get(
    "/{client_id}/status",
    response_model=DownloadClientStatusResponse,
    dependencies=[Depends(get_admin_user)],
)
def get_download_client_status(
    client_id: int,
    session: SessionDep,
) -> DownloadClientStatusResponse:
    """Get download client status information.

    Parameters
    ----------
    client_id : int
        Download client ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadClientStatusResponse
        Download client status information.

    Raises
    ------
    HTTPException
        If download client not found.
    """
    service = _get_download_client_service(session)
    client = service.get_download_client_status(client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download client {client_id} not found",
        )
    return DownloadClientStatusResponse.model_validate(client)


@router.get(
    "/{client_id}/items",
    response_model=DownloadItemsResponse,
    dependencies=[Depends(get_admin_user)],
)
def get_download_client_items(
    client_id: int,
    session: SessionDep,
) -> DownloadItemsResponse:
    """Get active downloads from a download client.

    Parameters
    ----------
    client_id : int
        Download client ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadItemsResponse
        List of active download items.

    Raises
    ------
    HTTPException
        If download client not found or fetching items fails.
    """
    from bookcard.pvr.exceptions import PVRProviderError

    service = _get_download_client_service(session)
    try:
        items = service.get_download_items(client_id)
        return DownloadItemsResponse(
            items=[DownloadItemResponse.model_validate(item) for item in items],
            total=len(items),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PVRProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download items: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting download items: {e}",
        ) from e

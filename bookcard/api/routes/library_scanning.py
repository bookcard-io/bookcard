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

"""API routes for library scanning."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session

from bookcard.api.deps import get_admin_user, get_db_session
from bookcard.models.auth import User
from bookcard.models.tasks import TaskType
from bookcard.services.library_scanning_service import LibraryScanningService

SessionDep = Annotated[Session, Depends(get_db_session)]

router = APIRouter(prefix="/library-scanning", tags=["library-scanning"])


class ScanRequest(BaseModel):
    """Request model for initiating a library scan."""

    library_id: int
    data_source_config: dict[str, Any] | None = None


class ScanResponse(BaseModel):
    """Response model for scan initiation."""

    task_id: int
    message: str


class ScanStateResponse(BaseModel):
    """Response model for scan state."""

    library_id: int
    last_scan_at: str | None
    scan_status: str
    books_scanned: int
    authors_scanned: int


def _raise_service_unavailable(detail: str) -> None:
    """Raise HTTPException for service unavailability."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )


@router.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def scan_library(
    request: ScanRequest,
    http_request: Request,
    session: SessionDep,  # noqa: ARG001
    current_user: Annotated[User, Depends(get_admin_user)],
) -> ScanResponse:
    """Initiate a library scan.

    Creates and enqueues a LIBRARY_SCAN task for the specified library.

    Parameters
    ----------
    request : ScanRequest
        Scan request with library_id and optional data_source_config.
    http_request : Request
        FastAPI request object for accessing app state.
    session : SessionDep
        Database session dependency.
    current_user : User
        Current authenticated admin user.

    Returns
    -------
    ScanResponse
        Task ID and message.

    Raises
    ------
    HTTPException
        If library is not found or scan cannot be initiated.
    """
    try:
        # Get task runner from app state
        task_runner = getattr(http_request.app.state, "task_runner", None)
        if task_runner is None:
            _raise_service_unavailable("Task runner not available")

        # Initiate scan via TaskRunner
        # Note: We rely on the unified TaskRunner which will dispatch a LibraryScanTask.
        # This simplifies the flow and ensures we use the same task infrastructure for everything.

        # Default data source config
        data_source_config = request.data_source_config or {
            "name": "openlibrary",
            "kwargs": {},
        }

        task_metadata = {
            "library_id": request.library_id,
            "data_source_config": data_source_config,
            "task_type": "library_scan",  # Required for factory to know type
        }

        task_id = task_runner.enqueue(  # type: ignore[union-attr]
            task_type=TaskType.LIBRARY_SCAN,
            payload={},  # No specific payload, everything is in metadata
            user_id=current_user.id,
            metadata=task_metadata,
        )

        return ScanResponse(
            task_id=task_id,
            message=f"Library scan job for library {request.library_id} queued via TaskRunner",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate scan: {e}",
        ) from e


@router.get(
    "/state/{library_id}",
    response_model=ScanStateResponse | None,
    dependencies=[Depends(get_admin_user)],
)
def get_scan_state(
    library_id: int,
    session: SessionDep,
    _current_user: Annotated[User, Depends(get_admin_user)],
) -> ScanStateResponse | None:
    """Get scan state for a library.

    Parameters
    ----------
    library_id : int
        ID of library.
    session : SessionDep
        Database session dependency.
    _current_user : Any
        Current authenticated admin user.

    Returns
    -------
    ScanStateResponse | None
        Scan state if found, None otherwise.
    """
    scanning_service = LibraryScanningService(
        session,
        None,  # Message broker not needed for read operations
    )

    scan_state = scanning_service.get_scan_state(library_id)

    if not scan_state:
        return None

    return ScanStateResponse(
        library_id=scan_state.library_id,
        last_scan_at=scan_state.last_scan_at.isoformat()
        if scan_state.last_scan_at
        else None,
        scan_status=scan_state.scan_status,
        books_scanned=scan_state.books_scanned,
        authors_scanned=scan_state.authors_scanned,
    )

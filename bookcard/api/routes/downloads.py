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

"""API routes for managing downloads.

Provides endpoints for:
- Viewing download queue (active)
- Viewing download history (completed/failed)
- Cancelling/removing downloads
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from bookcard.api.deps import get_data_encryptor, get_db_session
from bookcard.database import EngineSessionFactory
from bookcard.models.pvr import DownloadHistory, DownloadItem, DownloadQueue
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.download.client_selector import ProtocolBasedSelector
from bookcard.services.download.repository import SQLModelDownloadItemRepository
from bookcard.services.download_client_service import DownloadClientService
from bookcard.services.download_service import DownloadService
from bookcard.services.pvr_import_service import PVRImportService

router = APIRouter(prefix="/downloads", tags=["downloads"])


def get_download_service(
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
) -> DownloadService:
    """Get download service instance."""
    encryptor = get_data_encryptor(request)
    repo = SQLModelDownloadItemRepository(session)
    client_service = DownloadClientService(session, encryptor=encryptor)
    client_selector = ProtocolBasedSelector()

    return DownloadService(repo, client_service, client_selector=client_selector)


def get_import_service(
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
) -> PVRImportService:
    """Get PVR import service instance."""
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    active_library = library_service.get_active_library()

    if not active_library:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active library configured. Cannot import downloads.",
        )

    # Create session factory using the app's engine
    session_factory = EngineSessionFactory(request.app.state.engine)

    return PVRImportService(session, session_factory, active_library)


@router.get("/queue", response_model=DownloadQueue)
def get_queue(
    service: Annotated[DownloadService, Depends(get_download_service)],
) -> DownloadQueue:
    """Get current download queue.

    Returns
    -------
    DownloadQueue
        Active downloads.
    """
    items = service.get_active_downloads()
    return DownloadQueue(items=list(items), total_count=len(items))


@router.get("/history", response_model=DownloadHistory)
def get_history(
    service: Annotated[DownloadService, Depends(get_download_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DownloadHistory:
    """Get download history.

    Parameters
    ----------
    service : DownloadService
        Download service.
    limit : int
        Maximum number of items to return.
    offset : int
        Number of items to skip.

    Returns
    -------
    DownloadHistory
        Completed/failed downloads.
    """
    items = service.get_download_history(limit, offset)
    return DownloadHistory(items=list(items), total_count=len(items))


@router.post("/{item_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_download(
    item_id: int,
    service: Annotated[DownloadService, Depends(get_download_service)],
) -> None:
    """Cancel an active download.

    Parameters
    ----------
    item_id : int
        ID of the download item.
    service : DownloadService
        Download service.
    """
    try:
        service.cancel_download(item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download item not found or cannot be cancelled",
        ) from e


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_download(
    item_id: int,
    service: Annotated[DownloadService, Depends(get_download_service)],
) -> None:
    """Remove a download item (history or queue).

    Parameters
    ----------
    item_id : int
        ID of the download item.
    service : DownloadService
        Download service.
    """
    # Use cancel_download to remove item (it handles removal from client and DB update)
    # If explicit deletion is needed, DownloadService should be updated.
    try:
        service.cancel_download(item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download item not found",
        ) from e


@router.post("/import-pending", status_code=status.HTTP_200_OK)
def import_pending_downloads(
    service: Annotated[PVRImportService, Depends(get_import_service)],
) -> dict[str, int]:
    """Trigger import of pending completed downloads.

    Returns
    -------
    dict[str, int]
        Number of imported items.
    """
    results = service.import_pending_downloads()
    return {
        "processed": results.total_processed,
        "successful": results.successful,
        "failed": results.failed,
    }


@router.post("/{item_id}/retry", status_code=status.HTTP_200_OK)
def retry_download(
    item_id: int,
    session: Annotated[Session, Depends(get_db_session)],
    service: Annotated[PVRImportService, Depends(get_import_service)],
) -> dict[str, str]:
    """Retry importing a specific download item.

    Parameters
    ----------
    item_id : int
        ID of the download item.
    session : Session
        Database session.
    service : PVRImportService
        Import service.

    Returns
    -------
    dict[str, str]
        Result message.
    """
    item = session.get(DownloadItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download item not found",
        )

    result = service.process_completed_download(item)
    if result.is_success:
        return {"status": "success", "message": "Download imported successfully"}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Import failed: {result.error_message}",
    )

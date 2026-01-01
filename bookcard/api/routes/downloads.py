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
from bookcard.models.pvr import DownloadHistory, DownloadItem, DownloadQueue
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
    return DownloadService(repo, client_service)


def get_import_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PVRImportService:
    """Get PVR import service instance."""
    return PVRImportService(session)


@router.get("/queue", response_model=DownloadQueue)
def get_queue(
    service: Annotated[DownloadService, Depends(get_download_service)],
) -> DownloadQueue:
    """Get active downloads (queue)."""
    items = service.get_active_downloads()
    return DownloadQueue(items=list(items), total_count=len(items))


@router.get("/history", response_model=DownloadHistory)
def get_history(
    service: Annotated[DownloadService, Depends(get_download_service)],
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> DownloadHistory:
    """Get download history."""
    items = service.get_download_history(limit=limit, offset=offset)
    return DownloadHistory(items=list(items), total_count=len(items))


@router.delete("/{download_id}", response_model=DownloadItem)
def cancel_download(
    download_id: int,
    service: Annotated[DownloadService, Depends(get_download_service)],
) -> DownloadItem:
    """Cancel a download.

    Removes the download from the client and marks it as REMOVED in the database.
    """
    try:
        return service.cancel_download(download_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{download_id}/import")
def force_import(
    download_id: int,
    session: Annotated[Session, Depends(get_db_session)],
    import_service: Annotated[PVRImportService, Depends(get_import_service)],
) -> dict[str, str]:
    """Force retry import for a download item.

    Useful if an import failed due to temporary issues or manual intervention
    is required (e.g., fixing a corrupt archive).
    """
    item = session.get(DownloadItem, download_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Download item not found"
        )

    try:
        import_service.process_completed_download(item)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Import failed: {e}"
        ) from e

    return {"status": "imported", "message": "Download imported successfully"}

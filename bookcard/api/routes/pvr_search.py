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

"""Interactive PVR search endpoints.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

import logging
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_data_encryptor, get_db_session
from bookcard.api.schemas.pvr_search import (
    PVRDownloadRequest,
    PVRDownloadResponse,
    PVRSearchRequest,
    PVRSearchResponse,
    PVRSearchResultsResponse,
)
from bookcard.models.auth import User
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.download.repository import SQLModelDownloadItemRepository
from bookcard.services.download_client_service import DownloadClientService
from bookcard.services.download_service import DownloadService
from bookcard.services.indexer_service import IndexerService
from bookcard.services.permission_service import PermissionService
from bookcard.services.pvr.search.service import IndexerSearchService
from bookcard.services.pvr.tracked_book_search_service import (
    TrackedBookSearchError,
    TrackedBookSearchService,
)
from bookcard.services.tracked_book_service import TrackedBookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pvr/search", tags=["pvr-search"])

SessionDep = Annotated[Session, Depends(get_db_session)]
UserDep = Annotated[User, Depends(get_current_user)]


def _get_permission_helper(session: SessionDep) -> BookPermissionHelper:
    """Get book permission helper instance."""
    return BookPermissionHelper(session)


PermissionHelperDep = Annotated[
    BookPermissionHelper,
    Depends(_get_permission_helper),
]


def _get_tracked_book_search_service(
    session: SessionDep, request: Request
) -> TrackedBookSearchService:
    """Create TrackedBookSearchService instance for routes."""
    encryptor = get_data_encryptor(request)

    tracked_book_service = TrackedBookService(session)
    indexer_service = IndexerService(session, encryptor=encryptor)
    indexer_search_service = IndexerSearchService(indexer_service)

    download_item_repo = SQLModelDownloadItemRepository(session)
    download_client_service = DownloadClientService(session, encryptor=encryptor)
    download_service = DownloadService(
        download_item_repo=download_item_repo,
        download_client_service=download_client_service,
    )

    return TrackedBookSearchService(
        session,
        tracked_book_service,
        indexer_search_service,
        download_service,
        download_client_service,
    )


def _raise_not_found(detail: str) -> NoReturn:
    """Raise HTTPException with 404 status code."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


@router.post(
    "",
    response_model=PVRSearchResponse,
    dependencies=[Depends(get_current_user)],
)
def search_tracked_book(
    request: PVRSearchRequest,
    session: SessionDep,
    current_user: UserDep,
    permission_helper: PermissionHelperDep,
    fastapi_request: Request,
) -> PVRSearchResponse:
    """Initiate manual search for a tracked book.

    Searches all enabled indexers (or specified indexers) for the tracked book
    and stores results in cache for later retrieval.
    """
    # Check read permission for search operation
    permission_helper.check_read_permission(current_user)

    service = _get_tracked_book_search_service(session, fastapi_request)

    try:
        return service.search_tracked_book(
            tracked_book_id=request.tracked_book_id,
            max_results_per_indexer=request.max_results_per_indexer,
            indexer_ids=request.indexer_ids,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            _raise_not_found(str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except (RuntimeError, TrackedBookSearchError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{tracked_book_id}/results",
    response_model=PVRSearchResultsResponse,
    dependencies=[Depends(get_current_user)],
)
def get_search_results(
    tracked_book_id: int,
    session: SessionDep,
    current_user: UserDep,
    permission_helper: PermissionHelperDep,
    fastapi_request: Request,
) -> PVRSearchResultsResponse:
    """Get search results for a tracked book.

    Retrieves cached search results from the most recent search.
    """
    # Check read permission for retrieving results
    permission_helper.check_read_permission(current_user)

    service = _get_tracked_book_search_service(session, fastapi_request)

    try:
        return service.get_search_results(tracked_book_id)
    except ValueError as e:
        if "not found" in str(e).lower() and "tracked book" in str(e).lower():
            _raise_not_found(str(e))
        # For "No search results available", we return 404 as well per previous implementation logic
        _raise_not_found(str(e))


@router.post(
    "/{tracked_book_id}/download",
    response_model=PVRDownloadResponse,
    dependencies=[Depends(get_current_user)],
)
def trigger_download(
    tracked_book_id: int,
    request: PVRDownloadRequest,
    session: SessionDep,
    current_user: UserDep,
    fastapi_request: Request,
) -> PVRDownloadResponse:
    """Trigger download for a specific release from search results.

    Initiates download of the release at the specified index in the search results.
    """
    # Check write permission for download operation
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "create")

    service = _get_tracked_book_search_service(session, fastapi_request)

    try:
        return service.trigger_download(
            tracked_book_id=tracked_book_id,
            release_index=request.release_index,
            download_client_id=request.download_client_id,
        )
    except ValueError as e:
        if "not found" in str(e).lower() and "tracked book" in str(e).lower():
            _raise_not_found(str(e))
        if "not found" in str(e).lower() and "download client" in str(e).lower():
            _raise_not_found(str(e))
        # "No search results available" -> 404
        if "no search results" in str(e).lower():
            _raise_not_found(str(e))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except (RuntimeError, TrackedBookSearchError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

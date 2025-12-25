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
import threading
from datetime import UTC, datetime
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas.pvr_search import (
    PVRDownloadRequest,
    PVRDownloadResponse,
    PVRSearchRequest,
    PVRSearchResponse,
    PVRSearchResultsResponse,
    ReleaseInfoRead,
    SearchResultRead,
)
from bookcard.models.auth import User
from bookcard.models.pvr import TrackedBookStatus
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.download.repository import SQLModelDownloadItemRepository
from bookcard.services.download_client_service import DownloadClientService
from bookcard.services.download_service import DownloadService
from bookcard.services.indexer_service import IndexerService
from bookcard.services.permission_service import PermissionService
from bookcard.services.pvr.search.service import IndexerSearchService
from bookcard.services.tracked_book_service import TrackedBookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pvr/search", tags=["pvr-search"])

SessionDep = Annotated[Session, Depends(get_db_session)]
UserDep = Annotated[User, Depends(get_current_user)]

# In-memory cache for search results (keyed by tracked_book_id)
# In production, consider using Redis or a database table for persistence
_search_results_cache: dict[int, list] = {}
_cache_lock = threading.Lock()


def _get_permission_helper(session: SessionDep) -> BookPermissionHelper:
    """Get book permission helper instance.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    BookPermissionHelper
        Permission helper instance.
    """
    return BookPermissionHelper(session)


PermissionHelperDep = Annotated[
    BookPermissionHelper,
    Depends(_get_permission_helper),
]


def _get_tracked_book_service(session: SessionDep) -> TrackedBookService:
    """Create TrackedBookService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    TrackedBookService
        Tracked book service instance.
    """
    return TrackedBookService(session)


def _get_indexer_search_service(session: SessionDep) -> IndexerSearchService:
    """Create IndexerSearchService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    IndexerSearchService
        Indexer search service instance.
    """
    indexer_service = IndexerService(session)
    return IndexerSearchService(indexer_service)


def _get_download_service(session: SessionDep) -> DownloadService:
    """Create DownloadService instance for routes.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    DownloadService
        Download service instance.
    """
    download_item_repo = SQLModelDownloadItemRepository(session)
    download_client_service = DownloadClientService(session)
    return DownloadService(
        download_item_repo=download_item_repo,
        download_client_service=download_client_service,
    )


def _raise_not_found(tracked_book_id: int) -> NoReturn:
    """Raise HTTPException for tracked book not found.

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.

    Raises
    ------
    HTTPException
        Always raises with 404 status code.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tracked book {tracked_book_id} not found",
    )


def _raise_download_client_not_found(download_client_id: int) -> NoReturn:
    """Raise HTTPException for download client not found.

    Parameters
    ----------
    download_client_id : int
        Download client ID.

    Raises
    ------
    HTTPException
        Always raises with 404 status code.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Download client {download_client_id} not found",
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
) -> PVRSearchResponse:
    """Initiate manual search for a tracked book.

    Searches all enabled indexers (or specified indexers) for the tracked book
    and stores results in cache for later retrieval.

    Parameters
    ----------
    request : PVRSearchRequest
        Search request with tracked book ID and optional filters.
    session : SessionDep
        Database session dependency.
    current_user : UserDep
        Current authenticated user.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    PVRSearchResponse
        Search initiation response.

    Raises
    ------
    HTTPException
        If tracked book not found (404) or search fails (500).
    PermissionError
        If user does not have read permission.
    """
    # Check read permission for search operation
    permission_helper.check_read_permission(current_user)

    tracked_book_service = _get_tracked_book_service(session)
    tracked_book = tracked_book_service.get_tracked_book(request.tracked_book_id)

    if tracked_book is None:
        _raise_not_found(request.tracked_book_id)

    # Type narrowing: tracked_book is guaranteed to be not None after the check
    # Use a local variable to help type checker
    book = tracked_book
    query = f"{book.title} {book.author}".strip()  # type: ignore[union-attr]
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracked book must have title or author",
        )

    try:
        # Perform search
        search_service = _get_indexer_search_service(session)
        results = search_service.search_all_indexers(
            query=query,
            title=book.title,  # type: ignore[union-attr]
            author=book.author,  # type: ignore[union-attr]
            isbn=book.isbn,  # type: ignore[union-attr]
            max_results_per_indexer=request.max_results_per_indexer,
            indexer_ids=request.indexer_ids,
        )

        # Store results in cache
        with _cache_lock:
            _search_results_cache[request.tracked_book_id] = results

        # Update tracked book
        book.last_searched_at = datetime.now(UTC)  # type: ignore[assignment]
        book.status = TrackedBookStatus.SEARCHING  # type: ignore[assignment]
        session.add(book)
        session.commit()

        logger.info(
            "Search initiated for tracked book %d: %d results found",
            request.tracked_book_id,
            len(results),
        )

        return PVRSearchResponse(
            tracked_book_id=request.tracked_book_id,
            search_initiated=True,
            message=f"Search completed: {len(results)} results found",
        )

    except Exception as e:
        logger.exception(
            "Failed to search for tracked book %d", request.tracked_book_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e}",
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
) -> PVRSearchResultsResponse:
    """Get search results for a tracked book.

    Retrieves cached search results from the most recent search.

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    session : SessionDep
        Database session dependency.
    current_user : UserDep
        Current authenticated user.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    PVRSearchResultsResponse
        Search results response.

    Raises
    ------
    HTTPException
        If tracked book not found (404) or no results available (404).
    PermissionError
        If user does not have read permission.
    """
    # Check read permission for retrieving results
    permission_helper.check_read_permission(current_user)

    tracked_book_service = _get_tracked_book_service(session)
    tracked_book = tracked_book_service.get_tracked_book(tracked_book_id)

    if tracked_book is None:
        _raise_not_found(tracked_book_id)

    # Retrieve results from cache
    with _cache_lock:
        results = _search_results_cache.get(tracked_book_id)

    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No search results available for tracked book {tracked_book_id}. "
            "Please initiate a search first.",
        )

    # Convert results to response format
    search_results = [
        SearchResultRead(
            release=ReleaseInfoRead.from_release_info(result.release),
            score=result.score,
            indexer_name=result.indexer_name,
            indexer_priority=result.indexer_priority,
        )
        for result in results
    ]

    return PVRSearchResultsResponse(
        tracked_book_id=tracked_book_id,
        results=search_results,
        total=len(search_results),
    )


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
) -> PVRDownloadResponse:
    """Trigger download for a specific release from search results.

    Initiates download of the release at the specified index in the search results.

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    request : PVRDownloadRequest
        Download request with release index.
    session : SessionDep
        Database session dependency.
    current_user : UserDep
        Current authenticated user.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    PVRDownloadResponse
        Download initiation response.

    Raises
    ------
    HTTPException
        If tracked book not found (404), no results available (404),
        invalid release index (400), or download fails (500).
    PermissionError
        If user does not have write permission.
    """
    # Check write permission for download operation
    # Downloads create new download items, so we check write permission directly
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "create")

    tracked_book_service = _get_tracked_book_service(session)
    tracked_book = tracked_book_service.get_tracked_book(tracked_book_id)

    if tracked_book is None:
        _raise_not_found(tracked_book_id)

    # Type narrowing: tracked_book is guaranteed to be not None after the check
    # Use a local variable to help type checker
    book = tracked_book

    # Retrieve results from cache
    with _cache_lock:
        results = _search_results_cache.get(tracked_book_id)

    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No search results available for tracked book {tracked_book_id}. "
            "Please initiate a search first.",
        )

    # Validate release index
    if request.release_index >= len(results):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid release index {request.release_index}. "
            f"Only {len(results)} results available.",
        )

    # Get the selected release
    selected_result = results[request.release_index]
    release = selected_result.release

    try:
        # Get download client if specified
        download_client = None
        if request.download_client_id:
            download_client_service = DownloadClientService(session)
            download_client = download_client_service.get_download_client(
                request.download_client_id
            )
            if download_client is None:
                _raise_download_client_not_found(request.download_client_id)

        # Initiate download
        download_service = _get_download_service(session)
        download_item = download_service.initiate_download(
            release=release,
            tracked_book=book,  # type: ignore[arg-type]
            client=download_client,
        )

        logger.info(
            "Download initiated for tracked book %d: release '%s' (download_item_id=%d)",
            tracked_book_id,
            release.title,
            download_item.id or 0,
        )

        return PVRDownloadResponse(
            tracked_book_id=tracked_book_id,
            download_item_id=download_item.id or 0,  # type: ignore[arg-type]
            release_title=release.title,
            message=f"Download initiated for '{release.title}'",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except PVRProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {e}",
        ) from e
    except Exception as e:
        logger.exception(
            "Failed to initiate download for tracked book %d", tracked_book_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {e}",
        ) from e

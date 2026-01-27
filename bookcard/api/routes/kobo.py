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

"""Kobo sync API endpoints.

Routes handle Kobo device synchronization, including library sync,
reading state management, shelf/tag operations, and book downloads.
"""

import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlmodel import Session, select

from bookcard.api.deps import (
    get_db_session,
    get_kobo_auth_token,
    get_kobo_user,
)
from bookcard.api.schemas.kobo import (
    KoboAuthTokenResponse,
    KoboInitializationResponse,
    KoboReadingStateRequest,
    KoboReadingStateUpdateResult,
    KoboTagItemRequest,
    KoboTagRequest,
)
from bookcard.models.auth import User
from bookcard.models.config import IntegrationConfig, Library
from bookcard.models.core import Book
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.kobo_repository import (
    KoboArchivedBookRepository,
    KoboReadingStateRepository,
    KoboSyncedBookRepository,
)
from bookcard.repositories.reading_repository import ReadStatusRepository
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.kobo.book_lookup_service import KoboBookLookupService
from bookcard.services.kobo.cover_service import KoboCoverService
from bookcard.services.kobo.device_auth_service import KoboDeviceAuthService
from bookcard.services.kobo.download_service import KoboDownloadService
from bookcard.services.kobo.initialization_service import KoboInitializationService
from bookcard.services.kobo.library_service import KoboLibraryService
from bookcard.services.kobo.metadata_service import KoboMetadataService
from bookcard.services.kobo.reading_state_service import KoboReadingStateService
from bookcard.services.kobo.shelf_item_service import KoboShelfItemService
from bookcard.services.kobo.shelf_service import KoboShelfService
from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService
from bookcard.services.kobo.sync_service import KoboSyncService
from bookcard.services.kobo.sync_token_service import SyncToken
from bookcard.services.shelf_service import ShelfService

router = APIRouter(prefix="/kobo/{auth_token}", tags=["kobo"])

SessionDep = Annotated[Session, Depends(get_db_session)]
KoboUserDep = Annotated[User, Depends(get_kobo_user)]
AuthTokenDep = Annotated[str, Depends(get_kobo_auth_token)]

# Kobo Store API URL
KOBO_STOREAPI_URL = "https://storeapi.kobo.com"
KOBO_IMAGEHOST_URL = "https://cdn.kobo.com/book-images"

# Kobo native resources (fallback when proxy is disabled)
NATIVE_KOBO_RESOURCES = {
    "library_sync": "/kobo/{auth_token}/v1/library/sync",
    "library_metadata": "/kobo/{auth_token}/v1/library/{Ids}/metadata",
    "reading_state": "/kobo/{auth_token}/v1/library/{Ids}/state",
    "tags": "/kobo/{auth_token}/v1/library/tags",
    "image_host": "//cdn.kobo.com/book-images/",
    "image_url_template": "https://cdn.kobo.com/book-images/{ImageId}/{Width}/{Height}/false/image.jpg",
    "image_url_quality_template": "https://cdn.kobo.com/book-images/{ImageId}/{Width}/{Height}/{Quality}/{IsGreyscale}/image.jpg",
}


def _get_active_library(session: SessionDep) -> Library:
    """Get active library.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    Library
        Active library.

    Raises
    ------
    HTTPException
        If no active library (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None or library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return library


def _get_integration_config(session: SessionDep) -> IntegrationConfig | None:
    """Get integration configuration.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    IntegrationConfig | None
        Integration config if exists.
    """
    stmt = select(IntegrationConfig).limit(1)
    return session.exec(stmt).first()


def _check_kobo_sync_enabled(session: SessionDep) -> None:
    """Check if Kobo sync is enabled.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Raises
    ------
    HTTPException
        If Kobo sync is disabled (403).
    """
    config = _get_integration_config(session)
    if not config or not config.kobo_sync_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="kobo_sync_disabled",
        )


def _get_book_service(
    session: SessionDep,
) -> BookService:
    """Get book service for active library.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    BookService
        Book service instance.
    """
    library = _get_active_library(session)
    return BookService(library, session=session)


def _get_book_by_uuid(
    book_service: BookService, book_uuid: str
) -> tuple[int, Book] | None:
    """Get book by UUID.

    Parameters
    ----------
    book_service : BookService
        Book service.
    book_uuid : str
        Book UUID.

    Returns
    -------
    tuple[int, Book] | None
        Tuple of (book_id, Book) if found, None otherwise.
    """
    # Query Calibre DB for book by UUID
    with book_service._book_repo.get_session() as calibre_session:  # noqa: SLF001
        stmt = select(Book).where(Book.uuid == book_uuid)
        book = calibre_session.exec(stmt).first()
        if book is None or book.id is None:
            return None
        return (book.id, book)


def _get_kobo_metadata_service(
    request: Request,
    auth_token: AuthTokenDep,
) -> KoboMetadataService:
    """Get Kobo metadata service.

    Parameters
    ----------
    request : Request
        FastAPI request.
    auth_token : str
        Auth token.

    Returns
    -------
    KoboMetadataService
        Metadata service instance.
    """
    # Get base URL from request
    base_url = str(request.base_url).rstrip("/")
    return KoboMetadataService(base_url=base_url, auth_token=auth_token)


def _get_kobo_metadata_service_dep(
    request: Request,
    auth_token: AuthTokenDep,
) -> KoboMetadataService:
    """Dependency for Kobo metadata service.

    Parameters
    ----------
    request : Request
        FastAPI request.
    auth_token : str
        Auth token.

    Returns
    -------
    KoboMetadataService
        Metadata service instance.
    """
    return _get_kobo_metadata_service(request, auth_token)


def _get_kobo_sync_service(
    session: SessionDep,
    book_service: BookService,
    metadata_service: KoboMetadataService,
    shelf_service: ShelfService | None = None,
) -> KoboSyncService:
    """Get Kobo sync service.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_service : BookService
        Book service.
    metadata_service : KoboMetadataService
        Metadata service.
    shelf_service : ShelfService | None
        Optional shelf service.

    Returns
    -------
    KoboSyncService
        Sync service instance.
    """
    reading_state_repo = KoboReadingStateRepository(session)
    synced_book_repo = KoboSyncedBookRepository(session)
    archived_book_repo = KoboArchivedBookRepository(session)
    read_status_repo = ReadStatusRepository(session)

    return KoboSyncService(
        session=session,
        book_service=book_service,
        metadata_service=metadata_service,
        reading_state_repo=reading_state_repo,
        synced_book_repo=synced_book_repo,
        archived_book_repo=archived_book_repo,
        read_status_repo=read_status_repo,
        shelf_service=shelf_service,
    )


def _get_kobo_reading_state_service(
    session: SessionDep,
) -> KoboReadingStateService:
    """Get Kobo reading state service.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    KoboReadingStateService
        Reading state service instance.
    """
    reading_state_repo = KoboReadingStateRepository(session)
    read_status_repo = ReadStatusRepository(session)

    from bookcard.repositories.reading_repository import (
        AnnotationRepository,
        ReadingProgressRepository,
        ReadingSessionRepository,
    )
    from bookcard.services.reading_service import ReadingService

    progress_repo = ReadingProgressRepository(session)
    session_repo = ReadingSessionRepository(session)
    annotation_repo = AnnotationRepository(session)

    reading_service = ReadingService(
        session=session,
        progress_repo=progress_repo,
        session_repo=session_repo,
        status_repo=read_status_repo,
        annotation_repo=annotation_repo,
    )

    return KoboReadingStateService(
        session=session,
        reading_state_repo=reading_state_repo,
        read_status_repo=read_status_repo,
        reading_service=reading_service,
    )


def _get_kobo_shelf_service(
    session: SessionDep,
) -> KoboShelfService:
    """Get Kobo shelf service.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    KoboShelfService
        Shelf service instance.
    """
    from bookcard.repositories.shelf_repository import (
        BookShelfLinkRepository,
        ShelfRepository,
    )

    shelf_repo = ShelfRepository(session)
    link_repo = BookShelfLinkRepository(session)
    shelf_service = ShelfService(session, shelf_repo, link_repo)
    reading_state_repo = KoboReadingStateRepository(session)

    return KoboShelfService(
        session=session,
        shelf_service=shelf_service,
        reading_state_repo=reading_state_repo,
    )


def _get_kobo_download_service(
    book_service: Annotated[BookService, Depends(_get_book_service)],
) -> KoboDownloadService:
    """Get Kobo download service.

    Parameters
    ----------
    book_service : BookService
        Book service.

    Returns
    -------
    KoboDownloadService
        Download service instance.
    """
    return KoboDownloadService(book_service=book_service)


def _get_kobo_book_lookup_service(
    book_service: Annotated[BookService, Depends(_get_book_service)],
) -> KoboBookLookupService:
    """Get Kobo book lookup service.

    Parameters
    ----------
    book_service : BookService
        Book service.

    Returns
    -------
    KoboBookLookupService
        Book lookup service instance.
    """
    return KoboBookLookupService(book_service=book_service)


def _get_kobo_device_auth_service(
    session: SessionDep,
) -> KoboDeviceAuthService:
    """Get Kobo device auth service.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    KoboDeviceAuthService
        Device auth service instance.
    """
    proxy_service = _get_kobo_store_proxy_service(session)
    return KoboDeviceAuthService(session=session, proxy_service=proxy_service)


def _get_kobo_initialization_service(
    session: SessionDep,
) -> KoboInitializationService:
    """Get Kobo initialization service.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    KoboInitializationService
        Initialization service instance.
    """
    proxy_service = _get_kobo_store_proxy_service(session)
    return KoboInitializationService(proxy_service=proxy_service)


def _get_kobo_library_service(
    session: SessionDep,
    request: Request,
    auth_token: AuthTokenDep,
    book_service: Annotated[BookService, Depends(_get_book_service)],
) -> KoboLibraryService:
    """Get Kobo library service.

    Parameters
    ----------
    session : SessionDep
        Database session.
    request : Request
        FastAPI request.
    auth_token : str
        Auth token.
    book_service : BookService
        Book service.

    Returns
    -------
    KoboLibraryService
        Library service instance.
    """
    metadata_service = _get_kobo_metadata_service(request, auth_token)
    sync_service = _get_kobo_sync_service(session, book_service, metadata_service)
    shelf_service = _get_kobo_shelf_service(session)
    proxy_service = _get_kobo_store_proxy_service(session)
    book_lookup_service = _get_kobo_book_lookup_service(book_service)

    return KoboLibraryService(
        session=session,
        book_service=book_service,
        metadata_service=metadata_service,
        sync_service=sync_service,
        shelf_service=shelf_service,
        proxy_service=proxy_service,
        book_lookup_service=book_lookup_service,
    )


def _get_kobo_cover_service(
    session: SessionDep,
    book_service: Annotated[BookService, Depends(_get_book_service)],
) -> KoboCoverService:
    """Get Kobo cover service.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_service : BookService
        Book service.

    Returns
    -------
    KoboCoverService
        Cover service instance.
    """
    book_lookup_service = _get_kobo_book_lookup_service(book_service)
    proxy_service = _get_kobo_store_proxy_service(session)
    return KoboCoverService(
        book_service=book_service,
        book_lookup_service=book_lookup_service,
        proxy_service=proxy_service,
    )


def _get_kobo_shelf_item_service(
    session: SessionDep,
    book_service: Annotated[BookService, Depends(_get_book_service)],
) -> KoboShelfItemService:
    """Get Kobo shelf item service.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_service : BookService
        Book service.

    Returns
    -------
    KoboShelfItemService
        Shelf item service instance.
    """
    book_lookup_service = _get_kobo_book_lookup_service(book_service)
    return KoboShelfItemService(
        session=session, book_lookup_service=book_lookup_service
    )


def _get_kobo_store_proxy_service(
    session: SessionDep,
) -> KoboStoreProxyService:
    """Get Kobo store proxy service.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    KoboStoreProxyService
        Store proxy service instance.
    """
    config = _get_integration_config(session)
    return KoboStoreProxyService(integration_config=config)


# Authentication endpoints
@router.post("/v1/auth/device", response_model=KoboAuthTokenResponse)
async def handle_auth_device(
    request: Request,
    session: SessionDep,
    device_auth_service: Annotated[
        KoboDeviceAuthService, Depends(_get_kobo_device_auth_service)
    ],
) -> KoboAuthTokenResponse:
    """Handle Kobo device authentication.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : SessionDep
        Database session.
    device_auth_service : KoboDeviceAuthService
        Device auth service.

    Returns
    -------
    KoboAuthTokenResponse
        Auth token response.
    """
    _check_kobo_sync_enabled(session)

    body = await request.json() if request.method == "POST" else {}
    user_key = body.get("UserKey", "")

    return await device_auth_service.authenticate_device(request, user_key)


@router.get("/v1/initialization", response_model=KoboInitializationResponse)
def handle_initialization(
    request: Request,
    session: SessionDep,
    auth_token: AuthTokenDep,
    init_service: Annotated[
        KoboInitializationService, Depends(_get_kobo_initialization_service)
    ],
) -> KoboInitializationResponse:
    """Handle Kobo device initialization.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : SessionDep
        Database session.
    auth_token : str
        Auth token.
    init_service : KoboInitializationService
        Initialization service.

    Returns
    -------
    KoboInitializationResponse
        Initialization response with resources.
    """
    _check_kobo_sync_enabled(session)

    return init_service.get_initialization_resources(request, auth_token)


# Library sync endpoints
@router.get("/v1/library/sync")
async def handle_library_sync(
    request: Request,
    session: SessionDep,
    kobo_user: KoboUserDep,
    library_service: Annotated[KoboLibraryService, Depends(_get_kobo_library_service)],
) -> Response:
    """Handle Kobo library sync.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    library_service : KoboLibraryService
        Library service.

    Returns
    -------
    Response
        Sync response with JSON data.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    library = _get_active_library(session)
    if library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    # Parse sync token from headers
    sync_token = SyncToken.from_headers(dict(request.headers))

    return await library_service.sync_library(
        request=request,
        user_id=kobo_user.id,
        library_id=library.id,
        sync_token=sync_token,
    )


@router.get("/v1/library/{book_uuid}/metadata")
def handle_library_metadata(
    session: SessionDep,
    book_uuid: str,
    library_service: Annotated[KoboLibraryService, Depends(_get_kobo_library_service)],
) -> Response:
    """Handle book metadata request.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_uuid : str
        Book UUID.
    library_service : KoboLibraryService
        Library service.

    Returns
    -------
    Response
        Metadata response or proxy redirect.
    """
    _check_kobo_sync_enabled(session)

    try:
        metadata = library_service.get_book_metadata(book_uuid)
    except HTTPException:
        proxy_service = _get_kobo_store_proxy_service(session)
        if proxy_service.should_proxy():
            return RedirectResponse(
                url=f"{KOBO_STOREAPI_URL}/v1/library/{book_uuid}/metadata",
                status_code=307,
            )
        raise

    return JSONResponse(
        content=[metadata],
        media_type="application/json; charset=utf-8",
    )


@router.delete("/v1/library/{book_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def handle_library_delete(
    session: SessionDep,
    kobo_user: KoboUserDep,
    book_uuid: str,
    library_service: Annotated[KoboLibraryService, Depends(_get_kobo_library_service)],
) -> Response:
    """Handle book deletion request.

    Parameters
    ----------
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    book_uuid : str
        Book UUID.
    library_service : KoboLibraryService
        Library service.

    Returns
    -------
    Response
        Empty response (204) or proxy redirect.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    try:
        library_service.archive_book(kobo_user.id, book_uuid)
    except HTTPException:
        proxy_service = _get_kobo_store_proxy_service(session)
        if proxy_service.should_proxy():
            return RedirectResponse(
                url=f"{KOBO_STOREAPI_URL}/v1/library/{book_uuid}",
                status_code=307,
            )
        raise

    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Reading state endpoints
@router.get("/v1/library/{book_uuid}/state")
def handle_reading_state_get(
    request: Request,
    session: SessionDep,
    kobo_user: KoboUserDep,
    auth_token: AuthTokenDep,
    book_uuid: str,
    book_lookup_service: Annotated[
        KoboBookLookupService, Depends(_get_kobo_book_lookup_service)
    ],
) -> Response:
    """Get reading state for a book.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    auth_token : str
        Auth token.
    book_uuid : str
        Book UUID.
    book_lookup_service : KoboBookLookupService
        Book lookup service.

    Returns
    -------
    Response
        Reading state response or proxy redirect.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Get book by UUID
    book_result = book_lookup_service.find_book_by_uuid(book_uuid)
    if book_result is None:
        proxy_service = _get_kobo_store_proxy_service(session)
        if proxy_service.should_proxy():
            return RedirectResponse(
                url=f"{KOBO_STOREAPI_URL}/v1/library/{book_uuid}/state",
                status_code=307,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    book_id, book = book_result

    # Get reading state
    reading_state_service = _get_kobo_reading_state_service(session)
    reading_state = reading_state_service.get_or_create_reading_state(
        kobo_user.id, book_id
    )

    library = _get_active_library(session)
    if library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )
    read_status_repo = ReadStatusRepository(session)
    read_status = read_status_repo.get_by_user_book(kobo_user.id, library.id, book_id)

    # Format response
    metadata_service = _get_kobo_metadata_service(request, auth_token)
    state_response = metadata_service.get_reading_state_response(
        book, reading_state, read_status
    )

    return JSONResponse(content=[state_response])


@router.put(
    "/v1/library/{book_uuid}/state", response_model=KoboReadingStateUpdateResult
)
async def handle_reading_state_put(
    session: SessionDep,
    kobo_user: KoboUserDep,
    book_uuid: str,
    book_lookup_service: Annotated[
        KoboBookLookupService, Depends(_get_kobo_book_lookup_service)
    ],
    state_data: KoboReadingStateRequest,
) -> KoboReadingStateUpdateResult:
    """Update reading state for a book.

    Parameters
    ----------
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    book_uuid : str
        Book UUID.
    book_lookup_service : KoboBookLookupService
        Book lookup service.
    state_data : KoboReadingStateRequest
        Reading state update data.

    Returns
    -------
    KoboReadingStateUpdateResult
        Update result.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Get book by UUID
    book_result = book_lookup_service.find_book_by_uuid(book_uuid)
    if book_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    book_id, _book = book_result

    library = _get_active_library(session)
    if library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    # Update reading state
    reading_state_service = _get_kobo_reading_state_service(session)
    if not state_data.ReadingStates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reading_states_required",
        )

    state_dict = state_data.ReadingStates[0]
    update_results = reading_state_service.update_reading_state(
        user_id=kobo_user.id,
        book_id=book_id,
        library_id=library.id,
        state_data=state_dict,
    )

    session.commit()

    return KoboReadingStateUpdateResult(
        RequestResult="Success",
        UpdateResults=[update_results],
    )


# Shelf/Tag endpoints
@router.post("/v1/library/tags", status_code=status.HTTP_201_CREATED)
def handle_tags_create(
    session: SessionDep,
    kobo_user: KoboUserDep,
    tag_data: KoboTagRequest,
) -> Response:
    """Create a shelf from Kobo tag request.

    Parameters
    ----------
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    tag_data : KoboTagRequest
        Tag creation data.

    Returns
    -------
    Response
        Shelf UUID response.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    library = _get_active_library(session)
    if library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    shelf_service = _get_kobo_shelf_service(session)
    shelf = shelf_service.create_shelf_from_kobo(
        user_id=kobo_user.id,
        library_id=library.id,
        tag_data=tag_data.model_dump(),
    )

    session.commit()

    return Response(
        content=json.dumps(str(shelf.uuid)),
        status_code=status.HTTP_201_CREATED,
        media_type="application/json",
    )


@router.put("/v1/library/tags/{tag_id}")
@router.delete("/v1/library/tags/{tag_id}")
def handle_tags_update(
    request: Request,
    session: SessionDep,
    kobo_user: KoboUserDep,
    auth_token: AuthTokenDep,
    tag_id: str,
    tag_data: KoboTagRequest | None = None,
) -> Response:
    """Update or delete a shelf.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    auth_token : str
        Auth token.
    tag_id : str
        Tag/shelf UUID.
    tag_data : KoboTagRequest | None
        Tag update data (for PUT).

    Returns
    -------
    Response
        Empty response.
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    from bookcard.repositories.shelf_repository import ShelfRepository

    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.find_by_uuid(tag_id)

    if shelf is None or shelf.user_id != kobo_user.id:
        proxy_service = _get_kobo_store_proxy_service(session)
        if proxy_service.should_proxy():
            path = request.url.path.replace(f"/kobo/{auth_token}", "")
            return RedirectResponse(
                url=f"{KOBO_STOREAPI_URL}{path}",
                status_code=307,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="shelf_not_found",
        )

    if request.method == "DELETE":
        from bookcard.repositories.shelf_repository import BookShelfLinkRepository
        from bookcard.services.shelf_service import ShelfService

        link_repo = BookShelfLinkRepository(session)
        shelf_service = ShelfService(session, shelf_repo, link_repo)
        shelf_service.delete_shelf(shelf.id or 0, kobo_user)
    else:
        if tag_data:
            shelf_service = _get_kobo_shelf_service(session)
            shelf_service.update_shelf_from_kobo(shelf, tag_data.model_dump())

    session.commit()

    return Response(status_code=status.HTTP_200_OK)


@router.post("/v1/library/tags/{tag_id}/items", status_code=status.HTTP_201_CREATED)
def handle_tags_add_items(
    session: SessionDep,
    kobo_user: KoboUserDep,
    tag_id: str,
    item_data: KoboTagItemRequest,
    shelf_item_service: Annotated[
        KoboShelfItemService, Depends(_get_kobo_shelf_item_service)
    ],
) -> Response:
    """Add items to a shelf.

    Parameters
    ----------
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    tag_id : str
        Tag/shelf UUID.
    item_data : KoboTagItemRequest
        Items to add.
    shelf_item_service : KoboShelfItemService
        Shelf item service.

    Returns
    -------
    Response
        Empty response (201).
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    from bookcard.repositories.shelf_repository import ShelfRepository

    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.find_by_uuid(tag_id)

    if shelf is None or shelf.user_id != kobo_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="shelf_not_found",
        )

    if shelf.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="shelf_missing_id",
        )

    shelf_item_service.add_items_to_shelf(shelf.id, kobo_user, item_data)

    session.commit()

    return Response(status_code=status.HTTP_201_CREATED)


@router.post("/v1/library/tags/{tag_id}/items/delete")
def handle_tags_remove_items(
    session: SessionDep,
    kobo_user: KoboUserDep,
    tag_id: str,
    item_data: KoboTagItemRequest,
    shelf_item_service: Annotated[
        KoboShelfItemService, Depends(_get_kobo_shelf_item_service)
    ],
) -> Response:
    """Remove items from a shelf.

    Parameters
    ----------
    session : SessionDep
        Database session.
    kobo_user : User
        Authenticated user.
    tag_id : str
        Tag/shelf UUID.
    item_data : KoboTagItemRequest
        Items to remove.
    shelf_item_service : KoboShelfItemService
        Shelf item service.

    Returns
    -------
    Response
        Empty response (200).
    """
    _check_kobo_sync_enabled(session)

    if kobo_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    from bookcard.repositories.shelf_repository import ShelfRepository

    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.find_by_uuid(tag_id)

    if shelf is None or shelf.user_id != kobo_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="shelf_not_found",
        )

    if shelf.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="shelf_missing_id",
        )

    shelf_item_service.remove_items_from_shelf(shelf.id, kobo_user.id, item_data)  # type: ignore[invalid-argument-type]

    session.commit()

    return Response(status_code=status.HTTP_200_OK)


# Download endpoint
@router.get("/download/{book_id}/{book_format}", response_model=None)
def handle_download(
    session: SessionDep,
    book_id: int,
    book_format: str,
    download_service: Annotated[
        KoboDownloadService, Depends(_get_kobo_download_service)
    ],
) -> FileResponse:
    """Download a book file.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_id : int
        Book ID.
    book_format : str
        Book format.
    download_service : KoboDownloadService
        Download service.

    Returns
    -------
    FileResponse
        Book file response.
    """
    _check_kobo_sync_enabled(session)

    file_info = download_service.get_download_file_info(book_id, book_format)

    return FileResponse(
        path=str(file_info.file_path),
        media_type=file_info.media_type,
        filename=file_info.filename,
    )


# Cover image endpoint
@router.get(
    "/{book_uuid}/{width}/{height}/{isGreyscale}/image.jpg",
    response_model=None,
)
@router.get(
    "/{book_uuid}/{width}/{height}/{Quality}/{isGreyscale}/image.jpg",
    response_model=None,
)
def handle_cover_image(
    session: SessionDep,
    book_uuid: str,
    width: str,
    height: str,
    isGreyscale: str,  # noqa: N803
    cover_service: Annotated[KoboCoverService, Depends(_get_kobo_cover_service)],
    Quality: str = "",  # noqa: N803
) -> FileResponse | Response:
    """Handle cover image request.

    Parameters
    ----------
    session : SessionDep
        Database session.
    book_uuid : str
        Book UUID.
    width : str
        Image width.
    height : str
        Image height.
    is_greyscale : str
        Greyscale flag.
    cover_service : KoboCoverService
        Cover service.
    quality : str
        Image quality (optional).

    Returns
    -------
    FileResponse | Response
        Cover image or 404/proxy redirect.
    """
    _check_kobo_sync_enabled(session)

    # isGreyscale and Quality are path parameters required by Kobo API format
    # but not currently used in our implementation
    _ = isGreyscale
    _ = Quality

    return cover_service.get_cover_image(book_uuid, width, height)


# Top-level endpoint
@router.get("")
def handle_top_level(
    session: SessionDep,
) -> dict[str, object]:
    """Handle top-level Kobo endpoint.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    dict[str, object]
        Empty response.
    """
    _check_kobo_sync_enabled(session)
    return {}

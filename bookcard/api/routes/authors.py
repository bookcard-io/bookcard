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

"""Authors endpoints for listing and retrieving author metadata.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas.author import (
    AuthorMergeRecommendRequest,
    AuthorMergeRequest,
    AuthorUpdate,
    PhotoFromUrlRequest,
    PhotoUploadResponse,
)
from bookcard.models.auth import User
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_exception_mapper import AuthorExceptionMapper
from bookcard.services.author_exceptions import AuthorServiceError
from bookcard.services.author_merge_service import AuthorMergeService
from bookcard.services.author_permission_helper import AuthorPermissionHelper
from bookcard.services.author_rematch_service import AuthorRematchService
from bookcard.services.author_service import AuthorService
from bookcard.services.config_service import LibraryService
from bookcard.services.permission_service import PermissionService

if TYPE_CHECKING:
    from bookcard.services.messaging.base import MessageBroker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authors", tags=["authors"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _get_author_service(
    session: SessionDep,
    request: Request,
) -> AuthorService:
    """Get author service instance.

    Parameters
    ----------
    session : SessionDep
        Database session.
    request : Request
        FastAPI request object for accessing app state.

    Returns
    -------
    AuthorService
        Author service instance.
    """
    author_repo = AuthorRepository(session)
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    cfg = request.app.state.config
    return AuthorService(
        session,
        author_repo,
        library_service,
        library_repo,
        data_directory=cfg.data_directory,
    )


def _get_rematch_service(
    session: SessionDep,
    request: Request,
    author_service: Annotated[AuthorService, Depends(_get_author_service)],
) -> AuthorRematchService:
    """Get author rematch service instance.

    Parameters
    ----------
    session : SessionDep
        Database session.
    request : Request
        FastAPI request object for accessing app state.
    author_service : AuthorService
        Author service instance.

    Returns
    -------
    AuthorRematchService
        Author rematch service instance.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    message_broker: MessageBroker | None = getattr(
        request.app.state, "scan_worker_broker", None
    )
    return AuthorRematchService(
        session=session,
        author_service=author_service,
        library_repo=library_repo,
        library_service=library_service,
        message_broker=message_broker,
    )


def _get_permission_helper(session: SessionDep) -> AuthorPermissionHelper:
    """Get author permission helper instance.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    AuthorPermissionHelper
        Permission helper instance.
    """
    return AuthorPermissionHelper(session)


AuthorServiceDep = Annotated[AuthorService, Depends(_get_author_service)]
RematchServiceDep = Annotated[
    AuthorRematchService,
    Depends(_get_rematch_service),
]
PermissionHelperDep = Annotated[
    AuthorPermissionHelper,
    Depends(_get_permission_helper),
]


def _get_merge_service(
    session: SessionDep,
    request: Request,
) -> AuthorMergeService:
    """Get author merge service instance.

    Parameters
    ----------
    session : SessionDep
        Database session.
    request : Request
        FastAPI request object for accessing app state.

    Returns
    -------
    AuthorMergeService
        Author merge service instance.
    """
    author_repo = AuthorRepository(session)
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    cfg = request.app.state.config
    return AuthorMergeService(
        session,
        author_repo,
        library_service,
        library_repo,
        data_directory=cfg.data_directory,
    )


MergeServiceDep = Annotated[AuthorMergeService, Depends(_get_merge_service)]


async def _parse_rematch_request(request: Request) -> dict[str, object] | None:
    """Parse optional rematch request body.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    dict[str, object] | None
        Parsed JSON body if present and valid, otherwise None.
    """
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            return await request.json()
    except (ValueError, TypeError) as exc:
        logger.warning("Failed to parse request body: %s", exc)
    return None


def _get_author_or_raise(
    author_id: str,
    author_service: AuthorService,
) -> dict[str, object]:
    """Get author data or raise HTTPException.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key.
    author_service : AuthorService
        Author service instance.

    Returns
    -------
    dict[str, object]
        Author data dictionary.

    Raises
    ------
    HTTPException
        If author is not found or no active library exists.
    """
    try:
        author_data = author_service.get_author_by_id_or_key(author_id)
        logger.debug(
            "Author data retrieved: id=%s, key=%s, name=%s, is_unmatched=%s",
            author_data.get("id"),
            author_data.get("key"),
            author_data.get("name"),
            author_data.get("is_unmatched"),
        )
    except (ValueError, AuthorServiceError) as exc:
        logger.exception("Failed to get author")
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc
    else:
        return author_data


@router.get("")
def list_authors(
    current_user: CurrentUserDep,
    session: SessionDep,
    author_service: AuthorServiceDep,
    page: int = 1,
    page_size: int = 20,
    filter_type: str | None = Query(None, alias="filter"),
) -> dict[str, object]:
    """List authors with metadata for the active library with pagination.

    Returns authors that have been mapped to the active library via AuthorMapping.
    Includes metadata from AuthorMetadata (photos, remote IDs, alternate names, etc.).

    Parameters
    ----------
    current_user : CurrentUserDep
        Current authenticated user.
    session : SessionDep
        Database session dependency.
    author_service : AuthorServiceDep
        Author service instance.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).
    filter_type : str | None
        Filter type: "unmatched" to show only unmatched authors, None for all authors.

    Returns
    -------
    dict[str, object]
        Response with items array, total count, page, and total_pages.

    Raises
    ------
    HTTPException
        If no active library is found or permission denied (403).
    """
    # Check books:read permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "books", "read")
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    try:
        items, total = author_service.list_authors_for_active_library(
            page=page,
            page_size=page_size,
            filter_type=filter_type,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{author_id}")
def get_author(
    author_id: str,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Get a single author by ID or OpenLibrary key.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Author data with metadata.

    Raises
    ------
    HTTPException
        If author is not found, no active library exists, or permission denied (403).
    """
    author_data = _get_author_or_raise(author_id, author_service)
    # Check books:read permission with author context
    permission_helper.check_read_permission(current_user, author_data)
    return author_data


@router.put(
    "/{author_id}",
    response_model=dict[str, object],
    dependencies=[Depends(get_current_user)],
)
def update_author(
    author_id: str,
    update: AuthorUpdate,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Update author metadata.

    Updates AuthorMetadata fields and saves user-defined metadata
    (genres, styles, shelves, similar_authors) to AuthorUserMetadata.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
    update : AuthorUpdate
        Author update payload.
    author_service : AuthorServiceDep
        Author service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Updated author data dictionary.

    Raises
    ------
    HTTPException
        If author is not found (404), update fails (500), or permission denied (403).
    """
    author_data = _get_author_or_raise(author_id, author_service)
    permission_helper.check_write_permission(current_user, author_data)

    update_dict = update.model_dump(exclude_unset=True)
    try:
        return author_service.update_author(author_id, update_dict)
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.post(
    "/{author_id}/rematch",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def rematch_author(
    author_id: str,
    request: Request,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    rematch_service: RematchServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Re-match a single author to a specific OpenLibrary ID.

    Triggers a single-author workflow: match -> ingest -> link -> score.
    The match stage will use the provided OpenLibrary key directly,
    bypassing skip logic. The score stage will only score links
    involving this author.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
    request : Request
        FastAPI request object for accessing app state.
    session : SessionDep
        Database session.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    rematch_service : RematchServiceDep
        Rematch service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Response with task_id and message.

    Raises
    ------
    HTTPException
        If author is not found, no active library exists, message broker unavailable,
        or author does not have an OpenLibrary key or mapping.
    """
    logger.info(
        "Rematch request: author_id=%s, user_id=%s",
        author_id,
        current_user.id,
    )

    rematch_request = await _parse_rematch_request(request)
    author_data = _get_author_or_raise(author_id, author_service)
    permission_helper.check_write_permission(current_user, author_data)

    try:
        provided_olid = (
            rematch_request.get("openlibrary_key") if rematch_request else None
        )
        openlibrary_key = rematch_service.determine_openlibrary_key(
            provided_olid,  # ty:ignore[invalid-argument-type]
            author_data,
        )

        library_id, calibre_author_id, author_metadata_id = (
            rematch_service.resolve_library_and_author_ids(author_id, author_data)
        )

        author_dict = rematch_service.get_calibre_author_dict(
            library_id, calibre_author_id
        )

        rematch_service.enqueue_rematch_job(
            library_id, author_dict, openlibrary_key, author_metadata_id
        )

        logger.info(
            "Published single-author rematch job for author %s (OLID: %s, library: %d, metadata_id: %s)",
            author_data.get("name"),
            openlibrary_key,
            library_id,
            author_metadata_id,
        )

        return {
            "message": f"Author rematch job enqueued for {author_data.get('name')}",
            "openlibrary_key": openlibrary_key,
            "library_id": library_id,
        }
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.post(
    "/merge/recommend",
    response_model=dict[str, object],
    dependencies=[Depends(get_current_user)],
)
def recommend_merge_author(
    request_body: AuthorMergeRecommendRequest,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    merge_service: MergeServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Recommend which author to keep when merging.

    Parameters
    ----------
    request_body : AuthorMergeRecommendRequest
        Request with list of author IDs to merge.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    merge_service : MergeServiceDep
        Author merge service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Dictionary with recommended keep author ID and author details.

    Raises
    ------
    HTTPException
        If validation fails, authors not found, or permission denied.
    """
    # Check write permission for all authors being merged
    for author_id in request_body.author_ids:
        try:
            author_data = _get_author_or_raise(author_id, author_service)
            permission_helper.check_write_permission(current_user, author_data)
        except (ValueError, AuthorServiceError) as exc:
            raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc

    try:
        return merge_service.recommend_keep_author(request_body.author_ids)
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.post(
    "/merge",
    response_model=dict[str, object],
    dependencies=[Depends(get_current_user)],
)
def merge_authors(
    request_body: AuthorMergeRequest,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    merge_service: MergeServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Merge multiple authors into one.

    Parameters
    ----------
    request_body : AuthorMergeRequest
        Request with list of author IDs and keep author ID.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    merge_service : MergeServiceDep
        Author merge service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Dictionary with merged author details.

    Raises
    ------
    HTTPException
        If validation fails, authors not found, merge fails, or permission denied.
    """
    # Check write permission for all authors being merged
    for author_id in request_body.author_ids:
        try:
            author_data = _get_author_or_raise(author_id, author_service)
            permission_helper.check_write_permission(current_user, author_data)
        except (ValueError, AuthorServiceError) as exc:
            raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc

    try:
        return merge_service.merge_authors(
            request_body.author_ids,
            request_body.keep_author_id,
        )
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.post(
    "/{author_id}/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def upload_author_photo(
    author_id: str,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
    file: Annotated[UploadFile, File()],
) -> PhotoUploadResponse:
    """Upload an author photo from file.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key.
    author_service : AuthorServiceDep
        Author service instance.
    file : UploadFile
        Image file to upload.

    Returns
    -------
    PhotoUploadResponse
        Photo info with ID, URL, and file path.

    Raises
    ------
    HTTPException
        If author not found (404), invalid file type (400), upload fails (500),
        or permission denied (403).
    """
    author_data = _get_author_or_raise(author_id, author_service)
    permission_helper.check_write_permission(current_user, author_data)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="filename_required",
        )

    try:
        file_content = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_read_file: {exc!s}",
        ) from exc

    try:
        # Check if author has any existing photos - if not, set new photo as primary
        existing_photos = author_service.get_author_photos(author_id)
        set_as_primary = len(existing_photos) == 0

        user_photo = author_service.upload_author_photo(
            author_id=author_id,
            file_content=file_content,
            filename=file.filename,
            set_as_primary=set_as_primary,
        )
        photo_url = f"/api/authors/{author_id}/photos/{user_photo.id}"
        return PhotoUploadResponse(
            photo_id=user_photo.id or 0,
            photo_url=photo_url,
            file_path=user_photo.file_path,
        )
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_photo_error_to_http_exception(exc) from exc


@router.post(
    "/{author_id}/photos-from-url",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_photo_from_url(
    author_id: str,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
    request: PhotoFromUrlRequest,
) -> PhotoUploadResponse:
    """Upload an author photo from URL.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key.
    session : SessionDep
        Database session.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    request : PhotoFromUrlRequest
        Request containing image URL.

    Returns
    -------
    PhotoUploadResponse
        Photo info with ID, URL, and file path.

    Raises
    ------
    HTTPException
        If author not found (404), invalid URL (400), upload fails (500),
        or permission denied (403).
    """
    author_data = _get_author_or_raise(author_id, author_service)
    permission_helper.check_write_permission(current_user, author_data)

    try:
        # Check if author has any existing photos - if not, set new photo as primary
        existing_photos = author_service.get_author_photos(author_id)
        set_as_primary = len(existing_photos) == 0

        user_photo = author_service.upload_photo_from_url(
            author_id=author_id,
            url=request.url,
            set_as_primary=set_as_primary,
        )
        photo_url = f"/api/authors/{author_id}/photos/{user_photo.id}"
        return PhotoUploadResponse(
            photo_id=user_photo.id or 0,
            photo_url=photo_url,
            file_path=user_photo.file_path,
        )
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_photo_error_to_http_exception(exc) from exc
    except Exception as exc:
        # Catch any other unexpected errors (database errors, etc.)
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error uploading photo from URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {type(exc).__name__}: {exc!s}",
        ) from exc


@router.get(
    "/{author_id}/photos/{photo_id}",
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
def get_author_photo(
    author_id: str,
    photo_id: int,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
    request: Request,
) -> FileResponse | Response:
    """Get an author photo by ID.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key.
    photo_id : int
        Photo ID to retrieve.
    session : SessionDep
        Database session.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.
    request : Request
        FastAPI request object for accessing app state.

    Returns
    -------
    FileResponse | Response
        Photo image file or 404 response.

    Raises
    ------
    HTTPException
        If author not found (404), photo not found (404), file not found (404),
        or permission denied (403).
    """
    try:
        author_data = _get_author_or_raise(author_id, author_service)
        permission_helper.check_read_permission(current_user, author_data)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        raise

    # Get photo record and verify it belongs to the author
    photo = author_service.get_author_photo_by_id(author_id, photo_id)

    if not photo:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Get data directory from app state
    data_directory = Path(request.app.state.config.data_directory)

    # Build full file path
    photo_path = data_directory / photo.file_path

    if not photo_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Determine media type from photo record or file extension
    media_type = photo.mime_type or "image/jpeg"
    if not media_type.startswith("image/"):
        media_type = "image/jpeg"

    return FileResponse(
        path=str(photo_path),
        media_type=media_type,
        filename=photo.file_name or "photo.jpg",
    )


@router.delete(
    "/{author_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
def delete_author_photo(
    author_id: str,
    photo_id: int,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
    permission_helper: PermissionHelperDep,
) -> Response:
    """Delete an author photo and its file.

    Deletes both the database record and the file from the filesystem
    in an atomic operation (DB deletion happens first, then file deletion).

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key.
    photo_id : int
        Photo ID to delete.
    session : SessionDep
        Database session.
    current_user : CurrentUserDep
        Current authenticated user.
    author_service : AuthorServiceDep
        Author service instance.

    Returns
    -------
    Response
        Empty 204 No Content response on success.

    Raises
    ------
    HTTPException
        If author not found (404), photo not found (404), or permission denied (403).
    """
    author_data = _get_author_or_raise(author_id, author_service)
    permission_helper.check_write_permission(current_user, author_data)

    try:
        author_service.delete_photo(author_id, photo_id)
    except (ValueError, AuthorServiceError) as exc:
        raise AuthorExceptionMapper.map_value_error_to_http_exception(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)

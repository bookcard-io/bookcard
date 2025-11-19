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
Business logic is delegated to AuthorService.
"""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.models.auth import User
from fundamental.models.tasks import TaskType
from fundamental.repositories.author_repository import AuthorRepository
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.author_service import AuthorService
from fundamental.services.config_service import LibraryService

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

router = APIRouter(prefix="/authors", tags=["authors"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _get_author_service(session: SessionDep) -> AuthorService:
    """Get author service instance.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    AuthorService
        Author service instance.
    """
    author_repo = AuthorRepository(session)
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    return AuthorService(session, author_repo, library_service, library_repo)


AuthorServiceDep = Annotated[AuthorService, Depends(_get_author_service)]


@router.get("")
def list_authors(
    author_service: AuthorServiceDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, object]:
    """List authors with metadata for the active library with pagination.

    Returns authors that have been mapped to the active library via AuthorMapping.
    Includes metadata from AuthorMetadata (photos, remote IDs, alternate names, etc.).

    Parameters
    ----------
    author_service : AuthorServiceDep
        Author service instance.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).

    Returns
    -------
    dict[str, object]
        Response with items array, total count, page, and total_pages.

    Raises
    ------
    HTTPException
        If no active library is found.
    """
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
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    except ValueError as e:
        if "No active library found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active library found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

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
    author_service: AuthorServiceDep,
) -> dict[str, object]:
    """Get a single author by ID or OpenLibrary key.

    Parameters
    ----------
    author_id : str
        Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
    author_service : AuthorServiceDep
        Author service instance.

    Returns
    -------
    dict[str, object]
        Author data with metadata.

    Raises
    ------
    HTTPException
        If author is not found or no active library exists.
    """
    try:
        author_data = author_service.get_author_by_id_or_key(author_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        if "No active library found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active library found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e

    return author_data


@router.post(
    "/{author_id}/fetch-metadata",
    status_code=status.HTTP_201_CREATED,
)
def fetch_author_metadata(
    author_id: str,
    request: Request,
    current_user: CurrentUserDep,
    author_service: AuthorServiceDep,
) -> dict[str, object]:
    """Create a background task to fetch and update metadata for a single author.

    Creates and enqueues an AUTHOR_METADATA_FETCH task that will trigger
    the ingest stage of the pipeline for this author only. Fetches latest
    biography, metadata, subjects, etc. from OpenLibrary.

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
        Author service instance (used only for validation).

    Returns
    -------
    dict[str, object]
        Response with task_id for tracking the task.

    Raises
    ------
    HTTPException
        If author is not found, no active library exists, task runner unavailable,
        or author does not have an OpenLibrary key.
    """
    # Validate author exists and has OpenLibrary key
    try:
        author_data = author_service.get_author_by_id_or_key(author_id)
        openlibrary_key = author_data.get("key")
        if not openlibrary_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Author does not have an OpenLibrary key",
            )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from e
        if "No active library found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active library found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e

    # Get task runner
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner: TaskRunner = request.app.state.task_runner

    # Enqueue task
    task_id = task_runner.enqueue(
        task_type=TaskType.AUTHOR_METADATA_FETCH,
        payload={"author_id": author_id},
        user_id=current_user.id or 0,
        metadata={
            "task_type": TaskType.AUTHOR_METADATA_FETCH,
            "author_id": author_id,
        },
    )

    return {
        "task_id": task_id,
        "message": f"Author metadata fetch task {task_id} enqueued",
    }

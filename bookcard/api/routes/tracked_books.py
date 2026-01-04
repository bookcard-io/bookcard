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

"""Tracked book management endpoints.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

import logging
from typing import Annotated, NoReturn, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas.tracked_books import (
    BookFileRead,
    TrackedBookCreate,
    TrackedBookListResponse,
    TrackedBookRead,
    TrackedBookStatusResponse,
    TrackedBookUpdate,
)
from bookcard.models.auth import User
from bookcard.models.pvr import TrackedBook, TrackedBookStatus
from bookcard.services.tracked_book_service import TrackedBookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracked-books", tags=["tracked-books"])

SessionDep = Annotated[Session, Depends(get_db_session)]
UserDep = Annotated[User, Depends(get_current_user)]

_STATUS_FILTER_QUERY = Query(default=None, description="Filter by status")


def _get_tracked_book_service(
    session: SessionDep,
) -> TrackedBookService:
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


@router.get(
    "",
    response_model=TrackedBookListResponse,
    dependencies=[Depends(get_current_user)],
)
def list_tracked_books(
    session: SessionDep,
    status_filter: TrackedBookStatus | None = _STATUS_FILTER_QUERY,
) -> TrackedBookListResponse:
    """List tracked books.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    status_filter : TrackedBookStatus | None
        Optional status filter.

    Returns
    -------
    TrackedBookListResponse
        List of tracked books.
    """
    service = _get_tracked_book_service(session)
    books = service.list_tracked_books(status=status_filter)
    return TrackedBookListResponse(
        items=[TrackedBookRead.model_validate(book) for book in books],
        total=len(books),
    )


@router.get(
    "/{tracked_book_id}",
    response_model=TrackedBookRead,
    dependencies=[Depends(get_current_user)],
)
def get_tracked_book(
    tracked_book_id: int,
    session: SessionDep,
) -> TrackedBookRead:
    """Get a tracked book by ID.

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    TrackedBookRead
        Tracked book data.

    Raises
    ------
    HTTPException
        If tracked book not found.
    """
    service = _get_tracked_book_service(session)
    book = service.get_tracked_book(tracked_book_id)
    if book is None:
        _raise_not_found(tracked_book_id)

    # _raise_not_found raises an exception, so book is not None here.
    # We cast to satisfy type checkers that might not infer NoReturn behavior fully across functions.
    book = cast("TrackedBook", book)

    # Manually construct response to avoid validation issues with relationship attributes
    # when validation happens before we populate custom fields.
    # We first validate the base book attributes
    response = TrackedBookRead.model_validate(book)

    # Populate files using service logic to keep route clean
    # The files are not part of the TrackedBook model fields that Pydantic validates from attributes directly
    # because they are loaded separately via relationship but we are using from_attributes=True.
    # However, TrackedBookRead defines files as optional.
    # Let's populate the Pydantic model with data including files if available.

    files_data = service.get_book_files(book)
    files_list = [BookFileRead(**f) for f in files_data] if files_data else []

    # We can update the response object directly since Pydantic models are mutable
    response.files = files_list

    return response


@router.post(
    "",
    response_model=TrackedBookRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_tracked_book(
    data: TrackedBookCreate,
    session: SessionDep,
) -> TrackedBookRead:
    """Add a book to track.

    Parameters
    ----------
    data : TrackedBookCreate
        Tracked book creation data.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    TrackedBookRead
        Created tracked book.

    Raises
    ------
    HTTPException
        If book creation fails (e.g. already tracked).
    """
    service = _get_tracked_book_service(session)
    try:
        book = service.create_tracked_book(data)
        return TrackedBookRead.model_validate(book)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tracked book: {e}",
        ) from e


@router.put(
    "/{tracked_book_id}",
    response_model=TrackedBookRead,
    dependencies=[Depends(get_current_user)],
)
def update_tracked_book(
    tracked_book_id: int,
    data: TrackedBookUpdate,
    session: SessionDep,
) -> TrackedBookRead:
    """Update a tracked book.

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    data : TrackedBookUpdate
        Update data.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    TrackedBookRead
        Updated tracked book.

    Raises
    ------
    HTTPException
        If tracked book not found.
    """
    service = _get_tracked_book_service(session)
    book = service.update_tracked_book(tracked_book_id, data)
    if book is None:
        _raise_not_found(tracked_book_id)
    return TrackedBookRead.model_validate(book)


@router.delete(
    "/{tracked_book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
def delete_tracked_book(
    tracked_book_id: int,
    session: SessionDep,
) -> None:
    """Stop tracking a book (delete tracked book entry).

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    session : SessionDep
        Database session dependency.

    Raises
    ------
    HTTPException
        If tracked book not found.
    """
    service = _get_tracked_book_service(session)
    try:
        deleted = service.delete_tracked_book(tracked_book_id)
        if not deleted:
            _raise_not_found(tracked_book_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete tracked book %s", tracked_book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tracked book",
        ) from e


@router.get(
    "/{tracked_book_id}/status",
    response_model=TrackedBookStatusResponse,
    dependencies=[Depends(get_current_user)],
)
def get_tracked_book_status(
    tracked_book_id: int,
    session: SessionDep,
) -> TrackedBookStatusResponse:
    """Get tracking status (and trigger re-check of library match).

    Parameters
    ----------
    tracked_book_id : int
        Tracked book ID.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    TrackedBookStatusResponse
        Status information.

    Raises
    ------
    HTTPException
        If tracked book not found.
    """
    service = _get_tracked_book_service(session)
    book = service.check_status(tracked_book_id)
    if book is None:
        _raise_not_found(tracked_book_id)
    return TrackedBookStatusResponse.model_validate(book)

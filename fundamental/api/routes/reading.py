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

"""Reading endpoints: manage reading progress, sessions, and status."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlmodel import Session, select

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.schemas.reading import (
    ReadingHistoryResponse,
    ReadingProgressCreate,
    ReadingProgressRead,
    ReadingSessionCreate,
    ReadingSessionEnd,
    ReadingSessionRead,
    ReadingSessionsListResponse,
    ReadStatusRead,
    ReadStatusUpdate,
    RecentReadsResponse,
)
from fundamental.models.auth import User
from fundamental.models.reading import ReadingSession
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.repositories.reading_repository import (
    AnnotationRepository,
    ReadingProgressRepository,
    ReadingSessionRepository,
    ReadStatusRepository,
)
from fundamental.services.config_service import LibraryService
from fundamental.services.permission_service import PermissionService
from fundamental.services.reading_service import ReadingService

READING_RESOURCE_NAME = "books"
READING_ACTION_UPDATE = "read"
READING_ACTION_READ = "read"
READING_ACTION_CREATE = "read"

router = APIRouter(prefix="/reading", tags=["reading"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _get_active_library_id(
    session: SessionDep,
) -> int:
    """Get the active library ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    int
        Active library ID.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    if library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return library.id


ActiveLibraryIdDep = Annotated[int, Depends(_get_active_library_id)]


def _reading_service(session: SessionDep) -> ReadingService:
    """Create a ReadingService instance.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    ReadingService
        Reading service instance.
    """
    progress_repo = ReadingProgressRepository(session)
    session_repo = ReadingSessionRepository(session)
    status_repo = ReadStatusRepository(session)
    annotation_repo = AnnotationRepository(session)
    return ReadingService(
        session,
        progress_repo,
        session_repo,
        status_repo,
        annotation_repo,
    )


ReadingServiceDep = Annotated[ReadingService, Depends(_reading_service)]


@router.put("/progress", response_model=ReadingProgressRead)
def update_progress(
    progress_data: ReadingProgressCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ReadingProgressRead:
    """Update reading progress for a book.

    Parameters
    ----------
    progress_data : ReadingProgressCreate
        Progress update data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadingProgressRead
        Updated reading progress.

    Raises
    ------
    HTTPException
        If permission denied (403) or validation error (400).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_UPDATE
    )

    try:
        progress = reading_service.update_progress(
            user_id=current_user.id,
            library_id=library_id,
            book_id=progress_data.book_id,
            book_format=progress_data.format,
            progress=progress_data.progress,
            cfi=progress_data.cfi,
            page_number=progress_data.page_number,
            device=progress_data.device,
            spread_mode=getattr(progress_data, "spread_mode", None),
            reading_direction=getattr(progress_data, "reading_direction", None),
        )
        session.commit()

        if progress.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Progress has no ID",
            )

        return ReadingProgressRead(
            id=progress.id,
            user_id=progress.user_id,
            library_id=progress.library_id,
            book_id=progress.book_id,
            format=progress.format,
            progress=progress.progress,
            cfi=progress.cfi,
            page_number=progress.page_number,
            device=progress.device,
            spread_mode=progress.spread_mode,
            reading_direction=progress.reading_direction,
            updated_at=progress.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/progress/{book_id}", response_model=ReadingProgressRead)
def get_progress(
    book_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
    book_format: str = Query(
        ..., alias="format", description="Book format (EPUB, PDF, etc.)"
    ),
) -> ReadingProgressRead:
    """Get reading progress for a book.

    Parameters
    ----------
    book_id : int
        Book ID.
    book_format : str
        Book format (EPUB, PDF, etc.).
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadingProgressRead
        Reading progress data.

    Raises
    ------
    HTTPException
        If progress not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_READ
    )

    progress = reading_service.get_progress(
        user_id=current_user.id,
        library_id=library_id,
        book_id=book_id,
        book_format=book_format,
    )

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="progress_not_found",
        )

    if progress.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Progress has no ID",
        )

    return ReadingProgressRead(
        id=progress.id,
        user_id=progress.user_id,
        library_id=progress.library_id,
        book_id=progress.book_id,
        format=progress.format,
        progress=progress.progress,
        cfi=progress.cfi,
        page_number=progress.page_number,
        device=progress.device,
        spread_mode=progress.spread_mode,
        reading_direction=progress.reading_direction,
        updated_at=progress.updated_at,
    )


@router.post(
    "/sessions", response_model=ReadingSessionRead, status_code=status.HTTP_201_CREATED
)
def start_session(
    session_data: ReadingSessionCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ReadingSessionRead:
    """Start a reading session.

    Parameters
    ----------
    session_data : ReadingSessionCreate
        Session creation data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadingSessionRead
        Created reading session.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_CREATE
    )

    reading_session = reading_service.start_session(
        user_id=current_user.id,
        library_id=library_id,
        book_id=session_data.book_id,
        book_format=session_data.format,
        device=session_data.device,
    )
    session.commit()

    if reading_session.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session has no ID",
        )

    return ReadingSessionRead(
        id=reading_session.id,
        user_id=reading_session.user_id,
        library_id=reading_session.library_id,
        book_id=reading_session.book_id,
        format=reading_session.format,
        started_at=reading_session.started_at,
        ended_at=reading_session.ended_at,
        progress_start=reading_session.progress_start,
        progress_end=reading_session.progress_end,
        device=reading_session.device,
        created_at=reading_session.created_at,
        duration=reading_session.duration,
    )


@router.put("/sessions/{session_id}", response_model=ReadingSessionRead)
def end_session(
    session_id: int,
    session_end_data: ReadingSessionEnd,
    session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
) -> ReadingSessionRead:
    """End a reading session.

    Parameters
    ----------
    session_id : int
        Session ID.
    session_end_data : ReadingSessionEnd
        Session end data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.

    Returns
    -------
    ReadingSessionRead
        Updated reading session.

    Raises
    ------
    HTTPException
        If session not found (404), permission denied (403), or validation error (400).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_UPDATE
    )

    # Verify session belongs to current user
    session_repo = ReadingSessionRepository(session)
    reading_session = session_repo.get(session_id)
    if reading_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session_not_found",
        )

    if reading_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied",
        )

    try:
        reading_session = reading_service.end_session(
            session_id=session_id,
            progress_end=session_end_data.progress_end,
        )
        session.commit()

        if reading_session.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session has no ID",
            )

        return ReadingSessionRead(
            id=reading_session.id,
            user_id=reading_session.user_id,
            library_id=reading_session.library_id,
            book_id=reading_session.book_id,
            format=reading_session.format,
            started_at=reading_session.started_at,
            ended_at=reading_session.ended_at,
            progress_start=reading_session.progress_start,
            progress_end=reading_session.progress_end,
            device=reading_session.device,
            created_at=reading_session.created_at,
            duration=reading_session.duration,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/sessions", response_model=ReadingSessionsListResponse)
def list_sessions(
    db_session: SessionDep,
    current_user: CurrentUserDep,
    library_id: ActiveLibraryIdDep,
    book_id: int | None = Query(None, description="Filter by book ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> ReadingSessionsListResponse:
    """List reading sessions.

    Parameters
    ----------
    book_id : int | None
        Filter by book ID (optional).
    page : int
        Page number (default: 1).
    page_size : int
        Items per page (default: 50, max: 100).
    db_session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadingSessionsListResponse
        List of reading sessions with pagination.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(db_session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_READ
    )

    session_repo = ReadingSessionRepository(db_session)
    offset = (page - 1) * page_size

    if book_id is not None:
        sessions = session_repo.get_sessions_by_book(
            user_id=current_user.id,
            library_id=library_id,
            book_id=book_id,
            limit=page_size,
        )
        # Note: This is a simplified pagination - in production you'd want
        # proper offset/limit in the repository method
        total = len(sessions)
        sessions = sessions[offset : offset + page_size]
    else:
        # Get all sessions for user (simplified - would need proper query)
        stmt = (
            select(ReadingSession)
            .where(
                ReadingSession.user_id == current_user.id,
                ReadingSession.library_id == library_id,
            )
            .order_by(desc(ReadingSession.started_at))
            .offset(offset)
            .limit(page_size)
        )
        sessions = list(db_session.exec(stmt).all())

        # Get total count
        count_stmt = select(ReadingSession).where(
            ReadingSession.user_id == current_user.id,
            ReadingSession.library_id == library_id,
        )
        total = len(list(db_session.exec(count_stmt).all()))

    session_reads = [
        ReadingSessionRead(
            id=s.id,
            user_id=s.user_id,
            library_id=s.library_id,
            book_id=s.book_id,
            format=s.format,
            started_at=s.started_at,
            ended_at=s.ended_at,
            progress_start=s.progress_start,
            progress_end=s.progress_end,
            device=s.device,
            created_at=s.created_at,
            duration=s.duration,
        )
        for s in sessions
        if s.id is not None
    ]

    return ReadingSessionsListResponse(
        sessions=session_reads,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/recent", response_model=RecentReadsResponse)
def get_recent_reads(
    db_session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of recent reads"),
) -> RecentReadsResponse:
    """Get recent reads for the current user.

    Parameters
    ----------
    limit : int
        Maximum number of recent reads (default: 10, max: 100).
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    RecentReadsResponse
        List of recent reads.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(db_session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_READ
    )

    reads = reading_service.get_recent_reads(
        user_id=current_user.id,
        library_id=library_id,
        limit=limit,
    )

    read_data = [
        ReadingProgressRead(
            id=r.id,
            user_id=r.user_id,
            library_id=r.library_id,
            book_id=r.book_id,
            format=r.format,
            progress=r.progress,
            cfi=r.cfi,
            page_number=r.page_number,
            device=r.device,
            updated_at=r.updated_at,
        )
        for r in reads
        if r.id is not None
    ]

    return RecentReadsResponse(reads=read_data, total=len(read_data))


@router.get("/history/{book_id}", response_model=ReadingHistoryResponse)
def get_reading_history(
    book_id: int,
    db_session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions"),
) -> ReadingHistoryResponse:
    """Get reading history for a book.

    Parameters
    ----------
    book_id : int
        Book ID.
    limit : int
        Maximum number of sessions (default: 50, max: 100).
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadingHistoryResponse
        Reading history for the book.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(db_session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_READ
    )

    sessions = reading_service.get_reading_history(
        user_id=current_user.id,
        library_id=library_id,
        book_id=book_id,
        limit=limit,
    )

    session_data = [
        ReadingSessionRead(
            id=s.id,
            user_id=s.user_id,
            library_id=s.library_id,
            book_id=s.book_id,
            format=s.format,
            started_at=s.started_at,
            ended_at=s.ended_at,
            progress_start=s.progress_start,
            progress_end=s.progress_end,
            device=s.device,
            created_at=s.created_at,
            duration=s.duration,
        )
        for s in sessions
        if s.id is not None
    ]

    return ReadingHistoryResponse(sessions=session_data, total=len(session_data))


@router.put("/status/{book_id}", response_model=ReadStatusRead)
def update_read_status(
    book_id: int,
    status_data: ReadStatusUpdate,
    db_session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ReadStatusRead:
    """Manually mark a book as read or unread.

    Parameters
    ----------
    book_id : int
        Book ID.
    status_data : ReadStatusUpdate
        Status update data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadStatusRead
        Updated read status.

    Raises
    ------
    HTTPException
        If permission denied (403) or invalid status (400).
    """
    # Check permission
    permission_service = PermissionService(db_session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_UPDATE
    )

    if status_data.status == "read":
        read_status = reading_service.mark_as_read(
            user_id=current_user.id,
            library_id=library_id,
            book_id=book_id,
            manual=True,
        )
    elif status_data.status == "not_read":
        read_status = reading_service.mark_as_unread(
            user_id=current_user.id,
            library_id=library_id,
            book_id=book_id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'read' or 'not_read'",
        )

    db_session.commit()

    if read_status.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Read status has no ID",
        )

    return ReadStatusRead(
        id=read_status.id,
        user_id=read_status.user_id,
        library_id=read_status.library_id,
        book_id=read_status.book_id,
        status=read_status.status.value,
        first_opened_at=read_status.first_opened_at,
        marked_as_read_at=read_status.marked_as_read_at,
        auto_marked=read_status.auto_marked,
        progress_when_marked=read_status.progress_when_marked,
        created_at=read_status.created_at,
        updated_at=read_status.updated_at,
    )


@router.get("/status/{book_id}", response_model=ReadStatusRead)
def get_read_status(
    book_id: int,
    db_session: SessionDep,
    current_user: CurrentUserDep,
    reading_service: ReadingServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ReadStatusRead:
    """Get read status for a book.

    Parameters
    ----------
    book_id : int
        Book ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    reading_service : ReadingServiceDep
        Reading service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ReadStatusRead
        Read status data.

    Raises
    ------
    HTTPException
        If status not found (404) or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(db_session)
    permission_service.check_permission(
        current_user, READING_RESOURCE_NAME, READING_ACTION_READ
    )

    read_status = reading_service.get_read_status(
        user_id=current_user.id,
        library_id=library_id,
        book_id=book_id,
    )

    if read_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="read_status_not_found",
        )

    if read_status.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Read status has no ID",
        )

    return ReadStatusRead(
        id=read_status.id,
        user_id=read_status.user_id,
        library_id=read_status.library_id,
        book_id=read_status.book_id,
        status=read_status.status.value,
        first_opened_at=read_status.first_opened_at,
        marked_as_read_at=read_status.marked_as_read_at,
        auto_marked=read_status.auto_marked,
        progress_when_marked=read_status.progress_when_marked,
        created_at=read_status.created_at,
        updated_at=read_status.updated_at,
    )

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

"""Shelf endpoints: create, manage, and organize books into shelves."""

from __future__ import annotations

import tempfile
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas.shelves import (
    BookMatch,
    BookReferenceSchema,
    ImportResultSchema,
    ShelfCreate,
    ShelfListResponse,
    ShelfRead,
    ShelfReorderRequest,
    ShelfUpdate,
)
from bookcard.models.auth import User
from bookcard.models.shelves import ShelfTypeEnum
from bookcard.repositories.calibre.repository import CalibreBookRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.shelf_repository import (
    BookShelfLinkRepository,
    ShelfRepository,
)
from bookcard.services.config_service import LibraryService
from bookcard.services.magic_shelf.evaluator import BookRuleEvaluator
from bookcard.services.magic_shelf.service import MagicShelfService
from bookcard.services.permission_service import PermissionService
from bookcard.services.shelf_service import ShelfService

if TYPE_CHECKING:
    from bookcard.models.shelves import Shelf

router = APIRouter(prefix="/shelves", tags=["shelves"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _shelf_service(request: Request, session: SessionDep) -> ShelfService:
    """Create a ShelfService instance.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    ShelfService
        Shelf service instance.
    """
    cfg = request.app.state.config
    shelf_repo = ShelfRepository(session)
    link_repo = BookShelfLinkRepository(session)
    return ShelfService(
        session, shelf_repo, link_repo, data_directory=cfg.data_directory
    )


ShelfServiceDep = Annotated[ShelfService, Depends(_shelf_service)]


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


def _magic_shelf_service(
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
) -> MagicShelfService:
    """Create a MagicShelfService instance.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    MagicShelfService
        MagicShelf service instance.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_library(library_id)

    if not library or not library.calibre_db_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Active library has no path",
        )

    shelf_repo = ShelfRepository(session)
    book_repo = CalibreBookRepository(calibre_db_path=library.calibre_db_path)
    evaluator = BookRuleEvaluator()

    return MagicShelfService(shelf_repo, book_repo, evaluator)


MagicShelfServiceDep = Annotated[MagicShelfService, Depends(_magic_shelf_service)]


def _build_shelf_permission_context(shelf: Shelf) -> dict[str, object]:
    """Build permission context from shelf metadata.

    Parameters
    ----------
    shelf
        Shelf model instance.

    Returns
    -------
    dict[str, object]
        Permission context dictionary with owner_id, etc.
    """
    context: dict[str, object] = {}
    if shelf.user_id is not None:
        context["owner_id"] = shelf.user_id
    return context


def _read_upload_file_bytes(file: UploadFile) -> bytes:
    """Read bytes from an UploadFile.

    Parameters
    ----------
    file : UploadFile
        Upload file handle.

    Returns
    -------
    bytes
        File contents.

    Raises
    ------
    HTTPException
        If the file cannot be read.
    """
    try:
        return file.file.read()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_read_file: {exc!s}",
        ) from exc


def _get_shelf_book_count(
    session: SessionDep,
    magic_shelf_service: MagicShelfService,
    shelf: Shelf,
) -> int:
    """Compute correct `book_count` for a shelf (including Magic Shelves).

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    magic_shelf_service : MagicShelfService
        Magic shelf service dependency used to evaluate dynamic shelves.
    shelf : Shelf
        Shelf model instance.

    Returns
    -------
    int
        Number of books in the shelf.

    Raises
    ------
    HTTPException
        If the shelf has no ID (500).
    """
    shelf_id = _require_shelf_id(shelf)

    if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
        return magic_shelf_service.count_books_for_shelf(shelf_id)

    link_repo = BookShelfLinkRepository(session)
    return len(link_repo.find_by_shelf(shelf_id))


def _require_shelf_id(shelf: Shelf) -> int:
    """Return shelf ID or raise 500 if missing.

    Parameters
    ----------
    shelf : Shelf
        Shelf model instance.

    Returns
    -------
    int
        Shelf ID.

    Raises
    ------
    HTTPException
        If the shelf has no ID (500).
    """
    if shelf.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shelf has no ID",
        )
    return shelf.id


@router.post("", response_model=ShelfRead, status_code=status.HTTP_201_CREATED)
def create_shelf(
    shelf_data: ShelfCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ShelfRead:
    """Create a new shelf.

    Parameters
    ----------
    shelf_data : ShelfCreate
        Shelf creation data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ShelfRead
        Created shelf data.

    Raises
    ------
    HTTPException
        If shelf name already exists or permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "shelves", "create")

    try:
        shelf = shelf_service.create_shelf(
            library_id=library_id,
            user_id=current_user.id,  # ty:ignore[invalid-argument-type]
            name=shelf_data.name,
            description=shelf_data.description,
            is_public=shelf_data.is_public,
            shelf_type=shelf_data.shelf_type,
            filter_rules=shelf_data.filter_rules,
        )
        session.commit()

        # Get book count
        if shelf.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Shelf has no ID",
            )
        if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
            book_count = magic_shelf_service.count_books_for_shelf(shelf.id)
        else:
            link_repo = BookShelfLinkRepository(session)
            book_count = len(link_repo.find_by_shelf(shelf.id))

        return ShelfRead(
            id=shelf.id,
            uuid=shelf.uuid,
            name=shelf.name,
            description=shelf.description,
            cover_picture=shelf.cover_picture,
            is_public=shelf.is_public,
            is_active=shelf.is_active,
            shelf_type=shelf.shelf_type,
            filter_rules=shelf.filter_rules,
            read_list_metadata=shelf.read_list_metadata,
            user_id=shelf.user_id,
            library_id=shelf.library_id,
            created_at=shelf.created_at,
            updated_at=shelf.updated_at,
            last_modified=shelf.last_modified,
            book_count=book_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("", response_model=ShelfListResponse)
def list_shelves(
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ShelfListResponse:
    """List shelves accessible to the current user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ShelfListResponse
        List of shelves with total count.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Check permission
    permission_service = PermissionService(session)
    permission_service.check_permission(current_user, "shelves", "read")

    shelves = shelf_service.list_user_shelves(
        library_id=library_id,
        user_id=current_user.id,  # ty:ignore[invalid-argument-type]
        include_public=True,
    )

    # Get book counts for each shelf
    link_repo = BookShelfLinkRepository(session)
    shelf_reads = []
    for shelf in shelves:
        if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
            if shelf.id is None:
                book_count = 0
            else:
                book_count = magic_shelf_service.count_books_for_shelf(shelf.id)
        else:
            book_count = len(
                link_repo.find_by_shelf(shelf.id)  # ty:ignore[invalid-argument-type]
            )
        shelf_reads.append(
            ShelfRead(
                id=shelf.id,  # ty:ignore[invalid-argument-type]
                uuid=shelf.uuid,
                name=shelf.name,
                description=shelf.description,
                cover_picture=shelf.cover_picture,
                is_public=shelf.is_public,
                is_active=shelf.is_active,
                shelf_type=shelf.shelf_type,
                filter_rules=shelf.filter_rules,
                read_list_metadata=shelf.read_list_metadata,
                user_id=shelf.user_id,
                library_id=shelf.library_id,
                created_at=shelf.created_at,
                updated_at=shelf.updated_at,
                last_modified=shelf.last_modified,
                book_count=book_count,
            ),
        )

    return ShelfListResponse(shelves=shelf_reads, total=len(shelf_reads))


@router.get("/{shelf_id}", response_model=ShelfRead)
def get_shelf(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ShelfRead:
    """Get a shelf by ID.

    Parameters
    ----------
    shelf_id : int
        Shelf ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ShelfRead
        Shelf data.

    Raises
    ------
    HTTPException
        If shelf not found, user cannot view it, or permission denied (403).
    """
    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.get(shelf_id)
    if shelf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Verify shelf belongs to active library
    if shelf.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf)
    permission_service.check_permission(current_user, "shelves", "read", shelf_context)

    # Also check existing can_view_shelf logic (for backward compatibility)
    if not shelf_service.can_view_shelf(shelf, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: cannot view this shelf",
        )

    # Get book count
    if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
        book_count = magic_shelf_service.count_books_for_shelf(shelf_id)
    else:
        link_repo = BookShelfLinkRepository(session)
        book_count = len(link_repo.find_by_shelf(shelf_id))

    if shelf.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shelf has no ID",
        )

    return ShelfRead(
        id=shelf.id,
        uuid=shelf.uuid,
        name=shelf.name,
        description=shelf.description,
        cover_picture=shelf.cover_picture,
        is_public=shelf.is_public,
        is_active=shelf.is_active,
        shelf_type=shelf.shelf_type,
        filter_rules=shelf.filter_rules,
        user_id=shelf.user_id,
        library_id=shelf.library_id,
        created_at=shelf.created_at,
        updated_at=shelf.updated_at,
        last_modified=shelf.last_modified,
        book_count=book_count,
    )


@router.patch("/{shelf_id}", response_model=ShelfRead)
def update_shelf(
    shelf_id: int,
    shelf_data: ShelfUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ShelfRead:
    """Update a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID to update.
    shelf_data : ShelfUpdate
        Shelf update data.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ShelfRead
        Updated shelf data.

    Raises
    ------
    HTTPException
        If shelf not found, permission denied, or name conflict.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(current_user, "shelves", "edit", shelf_context)

    try:
        shelf = shelf_service.update_shelf(
            shelf_id=shelf_id,
            user=current_user,
            name=shelf_data.name,
            description=shelf_data.description,
            is_public=shelf_data.is_public,
            shelf_type=shelf_data.shelf_type,
            filter_rules=shelf_data.filter_rules,
        )
        session.commit()

        # Get book count
        if shelf.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Shelf has no ID",
            )
        if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
            book_count = magic_shelf_service.count_books_for_shelf(shelf.id)
        else:
            link_repo = BookShelfLinkRepository(session)
            book_count = len(link_repo.find_by_shelf(shelf.id))

        return ShelfRead(
            id=shelf.id,
            uuid=shelf.uuid,
            name=shelf.name,
            description=shelf.description,
            cover_picture=shelf.cover_picture,
            is_public=shelf.is_public,
            is_active=shelf.is_active,
            shelf_type=shelf.shelf_type,
            filter_rules=shelf.filter_rules,
            read_list_metadata=shelf.read_list_metadata,
            user_id=shelf.user_id,
            library_id=shelf.library_id,
            created_at=shelf.created_at,
            updated_at=shelf.updated_at,
            last_modified=shelf.last_modified,
            book_count=book_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/{shelf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shelf(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Delete a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID to delete.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Raises
    ------
    HTTPException
        If shelf not found or permission denied.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(
        current_user, "shelves", "delete", shelf_context
    )

    try:
        shelf_service.delete_shelf(shelf_id, current_user)
        session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/{shelf_id}/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def add_book_to_shelf(
    shelf_id: int,
    book_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Add a book to a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID.
    book_id : int
        Calibre book ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.

    Raises
    ------
    HTTPException
        If shelf not found, permission denied, or book already in shelf.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(current_user, "shelves", "edit", shelf_context)

    try:
        shelf_service.add_book_to_shelf(shelf_id, book_id, current_user)
        session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete(
    "/{shelf_id}/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_book_from_shelf(
    shelf_id: int,
    book_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Remove a book from a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID.
    book_id : int
        Calibre book ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.

    Raises
    ------
    HTTPException
        If shelf not found, permission denied, or book not in shelf.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(current_user, "shelves", "edit", shelf_context)

    try:
        shelf_service.remove_book_from_shelf(shelf_id, book_id, current_user)
        session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/{shelf_id}/books/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reorder_shelf_books(
    shelf_id: int,
    reorder_data: ShelfReorderRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Reorder books in a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID.
    reorder_data : ShelfReorderRequest
        Book order mapping.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.

    Raises
    ------
    HTTPException
        If shelf not found or permission denied.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission with shelf context
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(current_user, "shelves", "edit", shelf_context)

    try:
        shelf_service.reorder_books(
            shelf_id,
            reorder_data.book_orders,
            current_user,
        )
        session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{shelf_id}/books", response_model=list[int])
def get_shelf_books(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        default="order",
        description="Sort field: 'order', 'date_added', 'book_id'",
    ),
    sort_order: str = Query(
        default="asc",
        description="Sort order: 'asc' or 'desc'",
    ),
) -> list[int]:
    """List book IDs in a shelf with pagination and sorting.

    Parameters
    ----------
    shelf_id : int
        Shelf ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    magic_shelf_service : MagicShelfServiceDep
        Magic Shelf service dependency.
    page : int
        Page number (1-indexed).
    page_size : int
        Number of items per page.
    sort_by : str
        Sort field: 'order', 'date_added', or 'book_id'.
    sort_order : str
        Sort order: 'asc' or 'desc'.

    Returns
    -------
    list[int]
        List of book IDs in the shelf.

    Raises
    ------
    HTTPException
        If shelf not found or user cannot view it.
    """
    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.get(shelf_id)
    if shelf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Verify shelf belongs to active library
    if shelf.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    if not shelf_service.can_view_shelf(shelf, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: cannot view this shelf",
        )

    # Handle Magic Shelves
    from bookcard.models.shelves import ShelfTypeEnum

    if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
        try:
            books, _ = magic_shelf_service.get_books_for_shelf(
                shelf_id=shelf_id,
                page=page,
                page_size=page_size,
                sort_by=sort_by if sort_by != "order" else "timestamp",
                sort_order=sort_order,
                full=False,
            )
            return [book.book.id for book in books if book.book.id is not None]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    link_repo = BookShelfLinkRepository(session)
    links = link_repo.find_by_shelf(shelf_id)

    # Sort links
    if sort_by == "order":
        links.sort(key=lambda x: x.order, reverse=(sort_order == "desc"))
    elif sort_by == "date_added":
        links.sort(key=lambda x: x.date_added, reverse=(sort_order == "desc"))
    elif sort_by == "book_id":
        links.sort(key=lambda x: x.book_id, reverse=(sort_order == "desc"))

    # Paginate
    offset = (page - 1) * page_size
    paginated_links = links[offset : offset + page_size]

    return [link.book_id for link in paginated_links]


@router.post("/{shelf_id}/cover-picture", response_model=ShelfRead)
def upload_shelf_cover_picture(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
    file: Annotated[UploadFile, File()],
) -> ShelfRead:
    """Upload a shelf's cover picture.

    Accepts an image file and saves it to {data_directory}/shelves/{shelf_id}/{filename}.
    Replaces any existing cover picture.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    shelf_id : int
        Shelf identifier.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.
    file : UploadFile
        Image file to upload (JPEG, PNG, GIF, WebP, or SVG).

    Returns
    -------
    ShelfRead
        Updated shelf data.

    Raises
    ------
    HTTPException
        If shelf not found (404), permission denied (403), invalid file type (400),
        or file save fails (500).
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="filename_required",
        )

    file_content = _read_upload_file_bytes(file)

    try:
        shelf = shelf_service.upload_cover_picture(
            shelf_id,
            current_user.id,  # type: ignore[arg-type]
            file_content,
            file.filename,
        )
        session.commit()

        shelf_id_int = _require_shelf_id(shelf)
        book_count = _get_shelf_book_count(session, magic_shelf_service, shelf)

        return ShelfRead(
            id=shelf_id_int,
            uuid=shelf.uuid,
            name=shelf.name,
            description=shelf.description,
            cover_picture=shelf.cover_picture,
            is_public=shelf.is_public,
            is_active=shelf.is_active,
            shelf_type=shelf.shelf_type,
            filter_rules=shelf.filter_rules,
            read_list_metadata=shelf.read_list_metadata,
            user_id=shelf.user_id,
            library_id=shelf.library_id,
            created_at=shelf.created_at,
            updated_at=shelf.updated_at,
            last_modified=shelf.last_modified,
            book_count=book_count,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "shelf_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == "invalid_file_type":
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg.startswith("failed_to_save_file"):
            raise HTTPException(status_code=500, detail=msg) from exc
        raise
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied",
        ) from exc


@router.get("/{shelf_id}/cover-picture", response_model=None)
def get_shelf_cover_picture(
    request: Request,
    shelf_id: int,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
) -> FileResponse | Response:
    """Get a shelf's cover picture.

    Serves the cover picture file if it exists. Public shelves can be viewed
    by anyone; private shelves can only be viewed by the owner.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    shelf_id : int
        Shelf identifier.
    session : SessionDep
        Database session dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    FileResponse | Response
        Cover picture file or 404 if not found.
    """
    cfg = request.app.state.config
    shelf_repo = ShelfRepository(session)
    shelf = shelf_repo.get(shelf_id)

    if shelf is None or shelf.library_id != library_id:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if not shelf.cover_picture:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Handle both relative and absolute paths
    picture_path = Path(shelf.cover_picture)
    if picture_path.is_absolute():
        full_path = picture_path
    else:
        # Relative path - construct full path from data_directory
        full_path = Path(cfg.data_directory) / shelf.cover_picture

    if not full_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Determine media type from extension
    ext = full_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(full_path), media_type=media_type)


@router.delete("/{shelf_id}/cover-picture", response_model=ShelfRead)
def delete_shelf_cover_picture(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    magic_shelf_service: MagicShelfServiceDep,
    library_id: ActiveLibraryIdDep,
) -> ShelfRead:
    """Delete a shelf's cover picture.

    Removes the cover picture file and clears the shelf's cover_picture field.

    Parameters
    ----------
    shelf_id : int
        Shelf identifier.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.

    Returns
    -------
    ShelfRead
        Updated shelf data.

    Raises
    ------
    HTTPException
        If shelf not found (404) or permission denied (403).
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    try:
        shelf = shelf_service.delete_cover_picture(
            shelf_id,
            current_user.id,  # type: ignore[arg-type]
        )
        session.commit()

        # Get book count
        if shelf.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Shelf has no ID",
            )
        if shelf.shelf_type == ShelfTypeEnum.MAGIC_SHELF:
            book_count = magic_shelf_service.count_books_for_shelf(shelf.id)
        else:
            link_repo = BookShelfLinkRepository(session)
            book_count = len(link_repo.find_by_shelf(shelf.id))

        return ShelfRead(
            id=shelf.id,
            uuid=shelf.uuid,
            name=shelf.name,
            description=shelf.description,
            cover_picture=shelf.cover_picture,
            is_public=shelf.is_public,
            is_active=shelf.is_active,
            shelf_type=shelf.shelf_type,
            filter_rules=shelf.filter_rules,
            read_list_metadata=shelf.read_list_metadata,
            user_id=shelf.user_id,
            library_id=shelf.library_id,
            created_at=shelf.created_at,
            updated_at=shelf.updated_at,
            last_modified=shelf.last_modified,
            book_count=book_count,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "shelf_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied",
        ) from exc


@router.post(
    "/{shelf_id}/import",
    response_model=ImportResultSchema,
    status_code=status.HTTP_200_OK,
)
def import_read_list(
    shelf_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    shelf_service: ShelfServiceDep,
    library_id: ActiveLibraryIdDep,
    file: Annotated[UploadFile, File()],
    importer: Annotated[str, Form()] = "comicrack",
    auto_match: Annotated[bool, Form()] = False,
) -> ImportResultSchema:
    """Import a read list from a file into a shelf.

    Parameters
    ----------
    shelf_id : int
        Shelf ID to import into.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    shelf_service : ShelfServiceDep
        Shelf service dependency.
    library_id : ActiveLibraryIdDep
        Active library ID dependency.
    file : UploadFile
        Read list file to import (.cbl, etc.).
    importer : str
        Name of the importer to use (default: "comicrack").
    auto_match : bool
        If True, automatically add matched books to shelf (default: False).

    Returns
    -------
    ImportResultSchema
        Import result with matched and unmatched books.

    Raises
    ------
    HTTPException
        If shelf not found, permission denied, or import fails.
    """
    # Verify shelf belongs to active library
    shelf_repo = ShelfRepository(session)
    shelf_check = shelf_repo.get(shelf_id)
    if shelf_check is None or shelf_check.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelf {shelf_id} not found",
        )

    # Check permission
    permission_service = PermissionService(session)
    shelf_context = _build_shelf_permission_context(shelf_check)
    permission_service.check_permission(current_user, "shelves", "edit", shelf_context)

    # Save uploaded file to temporary location
    try:
        file_content = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {exc!s}",
        ) from exc

    # Create temporary file
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=Path(file.filename or "").suffix,
    ) as tmp_file:
        tmp_file.write(file_content)
        tmp_path = Path(tmp_file.name)

    try:
        # Import read list
        result = shelf_service.import_read_list(
            shelf_id=shelf_id,
            file_path=tmp_path,
            importer_name=importer,
            user=current_user,
            auto_match=auto_match,
        )
        session.commit()

        # Convert to response schema
        matched = [
            BookMatch(
                book_id=match.book_id,
                confidence=match.confidence,
                match_type=match.match_type,
                reference=match.reference.model_dump(),
            )
            for match in result.matched
            if match.book_id is not None
        ]

        unmatched = [
            BookReferenceSchema(**ref.model_dump()) for ref in result.unmatched
        ]

        return ImportResultSchema(
            total_books=result.total_books,
            matched=matched,
            unmatched=unmatched,
            errors=result.errors,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    finally:
        # Clean up temporary file
        with suppress(OSError):
            tmp_path.unlink()

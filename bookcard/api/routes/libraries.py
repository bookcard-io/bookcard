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

"""Library endpoints.

Exposes read-only endpoints that are safe for authenticated and (optionally)
anonymous users. All write operations remain under the admin router.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from bookcard.api.deps import get_current_user, get_db_session, get_optional_user
from bookcard.api.schemas.libraries import LibraryRead
from bookcard.api.schemas.user_libraries import UserLibraryRead
from bookcard.models.auth import User
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.user_library_repository import UserLibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.user_library_service import UserLibraryService

router = APIRouter(prefix="/libraries", tags=["libraries"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get(
    "/active",
    response_model=LibraryRead | None,
    dependencies=[Depends(get_optional_user)],
)
def get_active_library(
    session: SessionDep,
) -> LibraryRead | None:
    """Get the currently active library.

    Unauthenticated requests are allowed only when anonymous browsing is enabled.
    This is enforced by the ``get_optional_user`` dependency.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    LibraryRead | None
        The active library if one exists, None otherwise.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()
    if library is None:
        return None
    return LibraryRead.model_validate(library)


@router.get(
    "/me",
    response_model=list[UserLibraryRead],
)
def list_my_libraries(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[UserLibraryRead]:
    """List the current user's library assignments.

    Returns all libraries assigned to the authenticated user with their
    visibility and active status.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user.

    Returns
    -------
    list[UserLibraryRead]
        The user's library assignments.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    library_repo = LibraryRepository(session)
    service = UserLibraryService(
        session=session,
        user_library_repo=UserLibraryRepository(session),
        library_repo=library_repo,
    )
    assignments = service.list_assignments_for_user(current_user.id)

    # Build a library_id -> name lookup to enrich the response
    library_ids = [a.library_id for a in assignments]
    name_map: dict[int, str] = {}
    for lib_id in library_ids:
        lib = library_repo.get(lib_id)
        if lib is not None:
            name_map[lib_id] = lib.name

    result: list[UserLibraryRead] = []
    for a in assignments:
        read = UserLibraryRead.model_validate(a, from_attributes=True)
        read.library_name = name_map.get(a.library_id)
        result.append(read)
    return result


@router.put(
    "/me/{library_id}/active",
    response_model=UserLibraryRead,
)
def set_my_active_library(
    library_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserLibraryRead:
    """Set the active library for the current user.

    Parameters
    ----------
    library_id : int
        Library to activate.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user.

    Returns
    -------
    UserLibraryRead
        The updated association.

    Raises
    ------
    HTTPException
        404 if the assignment does not exist.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    service = UserLibraryService(
        session=session,
        user_library_repo=UserLibraryRepository(session),
        library_repo=LibraryRepository(session),
    )
    try:
        ul = service.set_active_library_for_user(current_user.id, library_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    session.commit()
    return UserLibraryRead.model_validate(ul, from_attributes=True)


@router.put(
    "/me/{library_id}/visibility",
    response_model=UserLibraryRead,
)
def set_my_library_visibility(
    library_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    is_visible: bool = True,
) -> UserLibraryRead:
    """Update visibility of a library for the current user.

    Parameters
    ----------
    library_id : int
        Library to update.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user.
    is_visible : bool
        Whether the library should be visible (default: True).

    Returns
    -------
    UserLibraryRead
        The updated association.

    Raises
    ------
    HTTPException
        404 if the assignment does not exist.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    service = UserLibraryService(
        session=session,
        user_library_repo=UserLibraryRepository(session),
        library_repo=LibraryRepository(session),
    )
    try:
        ul = service.set_visibility_for_user(
            current_user.id, library_id, is_visible=is_visible
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    session.commit()
    return UserLibraryRead.model_validate(ul, from_attributes=True)

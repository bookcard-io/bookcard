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

from fastapi import APIRouter, Depends
from sqlmodel import Session

from bookcard.api.deps import get_db_session, get_optional_user
from bookcard.api.schemas.libraries import LibraryRead
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService

router = APIRouter(prefix="/libraries", tags=["libraries"])

SessionDep = Annotated[Session, Depends(get_db_session)]


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

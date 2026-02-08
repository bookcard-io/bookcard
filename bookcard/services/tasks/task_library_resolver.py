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

"""Shared library resolver for background tasks.

Provides a single reusable function that all tasks call to resolve the
library they should operate on.  This eliminates duplicated
``_get_active_library()`` helper methods across task files (DRY).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.tasks.exceptions import LibraryNotConfiguredError

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.config import Library

logger = logging.getLogger(__name__)


def resolve_task_library(
    session: Session,
    metadata: dict[str, Any],
    user_id: int | None = None,
) -> Library:
    """Resolve the target library for a background task.

    Resolution order:

    1. Explicit ``library_id`` in *metadata* (captured at enqueue time).
    2. Per-user active library via ``UserLibrary`` (if *user_id* given).
    3. Global active library (``Library.is_active``).

    Parameters
    ----------
    session : Session
        Active database session.
    metadata : dict[str, Any]
        Task metadata dictionary, may contain ``library_id``.
    user_id : int | None
        Optional user identifier for per-user fallback.

    Returns
    -------
    Library
        Resolved library configuration.

    Raises
    ------
    LibraryNotConfiguredError
        If no library could be resolved through any strategy.
    """
    # 1. Explicit library_id in metadata
    library_id = metadata.get("library_id")
    if library_id is not None:
        library_repo = LibraryRepository(session)
        library = library_repo.get(library_id)
        if library is not None:
            logger.debug(
                "Resolved library from metadata: id=%s name=%s",
                library.id,
                library.name,
            )
            return library
        logger.warning(
            "library_id=%s from metadata not found, falling back", library_id
        )

    # 2. Per-user active library
    if user_id is not None:
        from bookcard.repositories.user_library_repository import (
            UserLibraryRepository,
        )

        ul_repo = UserLibraryRepository(session)
        library = ul_repo.get_active_library_for_user(user_id)
        if library is not None:
            logger.debug(
                "Resolved library from user assignment: user_id=%s library=%s",
                user_id,
                library.id,
            )
            return library

    # 3. Global active library
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()
    if library is not None:
        logger.debug("Resolved library from global active: id=%s", library.id)
        return library

    raise LibraryNotConfiguredError

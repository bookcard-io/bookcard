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

"""Service for triggering metadata enforcement.

Handles the business logic of checking if enforcement is enabled
and triggering enforcement operations.
"""

import logging
from contextlib import suppress

from sqlmodel import Session

from fundamental.repositories.config_repository import LibraryRepository
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.config_service import LibraryService
from fundamental.services.metadata_enforcement_service import (
    MetadataEnforcementService,
)

logger = logging.getLogger(__name__)


class MetadataEnforcementTriggerService:
    """Service for triggering metadata enforcement after book updates.

    Encapsulates the business logic of checking enforcement settings
    and triggering enforcement operations. Follows SRP by focusing
    solely on enforcement triggering logic.

    Parameters
    ----------
    session : Session
        Database session for enforcement operations.
    library_repo : LibraryRepository | None
        Library repository. If None, creates a new instance.
    library_service : LibraryService | None
        Library service. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,
        library_repo: LibraryRepository | None = None,
        library_service: LibraryService | None = None,
    ) -> None:
        """Initialize metadata enforcement trigger service.

        Parameters
        ----------
        session : Session
            Database session.
        library_repo : LibraryRepository | None
            Library repository instance.
        library_service : LibraryService | None
            Library service instance.
        """
        self._session = session
        self._library_repo = library_repo or LibraryRepository(session)
        self._library_service = library_service or LibraryService(
            session, self._library_repo
        )

    def trigger_enforcement_if_enabled(
        self,
        book_id: int,
        book_with_rels: BookWithFullRelations,
        user_id: int | None = None,
    ) -> None:
        """Trigger metadata enforcement if enabled for the active library.

        Checks if auto_metadata_enforcement is enabled for the active library.
        If enabled, triggers enforcement operation. Errors are logged but
        do not propagate to caller (graceful degradation).

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        user_id : int | None
            User ID who triggered the update (optional).
        """
        library = self._library_service.get_active_library()
        if not library or not library.auto_metadata_enforcement:
            return

        with suppress(Exception):
            enforcement_service = MetadataEnforcementService(
                session=self._session,
                library=library,
            )
            enforcement_service.enforce_metadata(
                book_id=book_id,
                book_with_rels=book_with_rels,
                user_id=user_id,
            )

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

"""Persistence adapter for ``LibraryScanState``.

Centralizes all access patterns to avoid subtle bugs such as using
primary-key lookups when the domain identifier is ``library_id``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from bookcard.models.library_scanning import LibraryScanState
from bookcard.services.tasks.library_scan.types import ScanStatus


class LibraryScanStateRepository:
    """Repository for reading/writing ``LibraryScanState`` by ``library_id``.

    Parameters
    ----------
    session : Session
        SQLModel session used for persistence operations.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        self._session = session

    def get_by_library_id(self, library_id: int) -> LibraryScanState | None:
        """Get scan state for a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        LibraryScanState | None
            Scan state row if present; otherwise None.
        """
        stmt = select(LibraryScanState).where(LibraryScanState.library_id == library_id)
        return self._session.exec(stmt).first()

    def upsert_status(self, library_id: int, status: ScanStatus) -> LibraryScanState:
        """Create or update scan state status.

        Parameters
        ----------
        library_id : int
            Library identifier.
        status : ScanStatus
            New scan status.

        Returns
        -------
        LibraryScanState
            Persisted scan state.
        """
        state = self.get_by_library_id(library_id)
        now = datetime.now(UTC)

        if state is None:
            state = LibraryScanState(library_id=library_id, scan_status=status.value)
            self._session.add(state)
        else:
            state.scan_status = status.value
            state.updated_at = now
            if status is ScanStatus.COMPLETED:
                state.last_scan_at = now

        self._session.commit()
        return state

    def refresh_view(self) -> None:
        """Expire cached ORM objects to observe external updates."""
        self._session.expire_all()

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

"""Library repository.

Repository for managing Calibre library configurations.
"""

from __future__ import annotations

from sqlmodel import Session, select

from fundamental.models.config import Library
from fundamental.repositories.base import Repository


class LibraryRepository(Repository[Library]):
    """Repository for `Library` entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Library)

    def find_active(self) -> Library | None:
        """Get the currently active library.

        Returns
        -------
        Library | None
            The active library if one exists, None otherwise.
        """
        stmt = select(Library).where(Library.is_active == True)  # noqa: E712
        return self._session.exec(stmt).first()

    def find_by_path(self, path: str) -> Library | None:
        """Find a library by database path.

        Parameters
        ----------
        path : str
            Calibre database path.

        Returns
        -------
        Library | None
            Library with matching path if found, None otherwise.
        """
        stmt = select(Library).where(Library.calibre_db_path == path)
        return self._session.exec(stmt).first()

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

"""Configuration repositories.

Repositories for system configuration models. These are singleton models
(only one record per table should exist).
"""

from __future__ import annotations

from sqlmodel import Session, select

from fundamental.models.config import Library
from fundamental.repositories.base import Repository


class LibraryRepository(Repository[Library]):
    """Repository for `Library` entities.

    Libraries can be multiple, but only one should be active at a time.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, Library)

    def get_active(self) -> Library | None:
        """Get the currently active library.

        Returns
        -------
        Library | None
            The active library if one exists, None otherwise.
        """
        stmt = select(Library).where(Library.is_active == True)  # noqa: E712
        return self._session.exec(stmt).first()

    def list_all(self) -> list[Library]:
        """List all libraries, ordered by creation date.

        Returns
        -------
        list[Library]
            All libraries.
        """
        stmt = select(Library).order_by(Library.created_at)
        return list(self._session.exec(stmt).all())

    def find_by_path(self, calibre_db_path: str) -> Library | None:
        """Find a library by its database path.

        Parameters
        ----------
        calibre_db_path : str
            Path to Calibre database directory.

        Returns
        -------
        Library | None
            Library with matching path if found, None otherwise.
        """
        stmt = select(Library).where(Library.calibre_db_path == calibre_db_path)
        return self._session.exec(stmt).first()

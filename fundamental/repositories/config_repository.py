# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

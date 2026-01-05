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

"""Transaction management for PVR import."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session


class ImportTransaction:
    """Manages transaction boundaries for import operations."""

    def __init__(self, session: Session) -> None:
        """Initialize import transaction.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session
        self._pending_entities: list = []

    def add(self, entity: object) -> None:
        """Add entity to be committed.

        Parameters
        ----------
        entity : object
            Entity to add.
        """
        self._pending_entities.append(entity)

    def commit(self) -> None:
        """Commit all pending entities."""
        for entity in self._pending_entities:
            self._session.add(entity)
        self._session.commit()
        self._pending_entities.clear()

    def rollback(self) -> None:
        """Rollback and clear pending entities."""
        self._session.rollback()
        self._pending_entities.clear()


@contextmanager
def import_transaction(session: Session) -> Generator[ImportTransaction, None, None]:
    """Provide transactional context for import operations.

    Parameters
    ----------
    session : Session
        Database session.

    Yields
    ------
    ImportTransaction
        The transaction manager.
    """
    transaction = ImportTransaction(session)
    try:
        yield transaction
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise

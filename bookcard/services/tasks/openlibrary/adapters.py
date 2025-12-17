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

"""Adapters for integrating with existing task system.

These adapters bridge the new architecture with the existing task system,
allowing for gradual migration without breaking existing functionality.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from bookcard.services.tasks.openlibrary.progress import ProgressReporterAdapter

__all__ = [
    "CancellationCheckerAdapter",
    "DatabaseRepositoryAdapter",
    "ProgressReporterAdapter",
]


class DatabaseRepositoryAdapter:
    """Adapter for SQLAlchemy session to DatabaseRepository protocol.

    Allows the new architecture to work with existing SQLAlchemy sessions
    without modification.
    """

    def __init__(self, session: Session) -> None:
        """Initialize database repository adapter.

        Parameters
        ----------
        session : Session
            SQLAlchemy session.
        """
        self.session = session

    def bulk_save(self, objects: list[Any]) -> None:
        """Bulk save objects.

        Parameters
        ----------
        objects : list[Any]
            List of model objects to save.
        """
        if objects:
            self.session.bulk_save_objects(objects)

    def commit(self) -> None:
        """Commit transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback transaction."""
        self.session.rollback()

    def truncate_tables(self, table_names: list[str]) -> None:
        """Truncate specified tables.

        Parameters
        ----------
        table_names : list[str]
            List of table names to truncate.
        """
        self.session.connection().execute(
            text(f"TRUNCATE TABLE {', '.join(table_names)} CASCADE")
        )
        self.session.commit()


class CancellationCheckerAdapter:
    """Adapter for cancellation check callback.

    Converts the existing callback-based cancellation checking to the
    CancellationChecker protocol.
    """

    def __init__(self, check_cancelled: Callable[[], bool]) -> None:
        """Initialize cancellation checker adapter.

        Parameters
        ----------
        check_cancelled : Callable
            Cancellation check callback function.
        """
        self.check_cancelled = check_cancelled

    def is_cancelled(self) -> bool:
        """Check if task is cancelled.

        Returns
        -------
        bool
            True if task has been cancelled, False otherwise.
        """
        return self.check_cancelled()

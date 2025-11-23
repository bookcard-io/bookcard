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

"""Session manager for Calibre database connections.

This module handles database connection management following SRP.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import event
from sqlmodel import Session, create_engine

from fundamental.repositories.interfaces import ISessionManager

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Iterator

    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


class CalibreSessionManager(ISessionManager):
    """Manages database connections for Calibre SQLite database.

    Handles engine creation, SQLite function registration, and session management.
    Follows SRP by focusing solely on database connection concerns.

    Parameters
    ----------
    calibre_db_path : str
        Path to Calibre library directory (contains metadata.db).
    calibre_db_file : str
        Calibre database filename (default: 'metadata.db').
    """

    def __init__(
        self,
        calibre_db_path: str,
        calibre_db_file: str = "metadata.db",
    ) -> None:
        self._calibre_db_path = Path(calibre_db_path)
        self._calibre_db_file = calibre_db_file
        self._db_path = self._calibre_db_path / self._calibre_db_file
        self._engine: Engine | None = None

    @staticmethod
    def _get_calibre_sqlite_functions() -> list[tuple[str, int, Callable[..., object]]]:
        """Get list of SQLite functions to register for Calibre database.

        Returns
        -------
        list[tuple[str, int, Callable[..., object]]]
            List of tuples containing (function_name, num_args, function_impl).
            Each tuple defines a SQLite function to register.

        Notes
        -----
        To add a new function, simply add a tuple to this list:
        - function_name: Name of the SQL function (e.g., "my_function")
        - num_args: Number of arguments the function accepts (-1 for variable)
        - function_impl: Python callable that implements the function
        """
        return [
            (
                "title_sort",
                1,
                lambda x: x or "",
            ),
            (
                "uuid4",
                0,
                lambda: str(uuid4()),
            ),
        ]

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine for Calibre database.

        Returns
        -------
        Engine
            SQLAlchemy engine instance.

        Raises
        ------
        FileNotFoundError
            If Calibre database file does not exist.
        """
        if not self._db_path.exists():
            msg = f"Calibre database not found at {self._db_path}"
            raise FileNotFoundError(msg)
        if self._engine is None:
            db_url = f"sqlite:///{self._db_path}"

            def _register_calibre_functions(
                dbapi_conn: sqlite3.Connection, connection_record: object
            ) -> None:
                """Register SQLite functions required by Calibre database.

                Registers functions needed by Calibre's database triggers.
                SQLite's create_function is idempotent, so it's safe to call
                multiple times - subsequent calls simply replace the function.

                To add a new function, add it to the list returned by
                _get_calibre_sqlite_functions().

                Parameters
                ----------
                dbapi_conn : sqlite3.Connection
                    SQLite database connection.
                connection_record : object
                    Connection record (required by event listener signature).
                """
                # connection_record is required by event listener signature but unused
                _ = connection_record
                # Register each function
                # Note: create_function is idempotent, so calling it multiple times
                # is safe and has negligible overhead
                for (
                    func_name,
                    num_args,
                    func_impl,
                ) in self._get_calibre_sqlite_functions():
                    dbapi_conn.create_function(func_name, num_args, func_impl)

            self._engine = create_engine(db_url, echo=False, future=True)
            event.listen(self._engine, "connect", _register_calibre_functions)
        return self._engine

    def dispose(self) -> None:
        """Dispose of the database engine and close all connections.

        This is useful for cleanup in tests or when the manager is no longer needed.
        After calling this method, the engine will be recreated on the next use.
        """
        if self._engine is not None:
            # Force close all connections and dispose the engine
            self._engine.dispose(close=True)
            # On Windows, we need to ensure all connections are fully closed
            # before the file can be deleted. The dispose(close=True) should handle this,
            # but we set engine to None immediately to prevent reuse.
            self._engine = None

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Get a SQLModel session for the Calibre database.

        Yields
        ------
        Session
            SQLModel session.
        """
        engine = self._get_engine()
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

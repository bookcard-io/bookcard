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

"""Database engine and session management.

This module centralizes SQLAlchemy/SQLModel engine creation and session
lifecycle management. It is framework-agnostic and suitable for DI/IOC.
"""

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, event
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from fundamental.config import AppConfig


def create_db_engine(config: AppConfig | None = None) -> Engine:
    """Create a SQLAlchemy engine for the configured database.

    For SQLite databases, configures WAL mode and connection timeouts
    to handle concurrent access better.

    Parameters
    ----------
    config : AppConfig | None
        Application configuration. If ``None``, environment-based config is used.

    Returns
    -------
    Engine
        A configured SQLAlchemy engine instance.
    """
    cfg = config or AppConfig.from_env()

    # Configure SQLite for better concurrent access
    connect_args = {}
    if cfg.database_url.startswith("sqlite"):
        # Enable WAL mode for better concurrent read/write performance
        # Set timeout to 30 seconds for lock contention
        connect_args = {
            "timeout": 30.0,
            "check_same_thread": False,
        }

    engine = create_engine(
        cfg.database_url,
        echo=cfg.echo_sql,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,  # Verify connections before using
    )

    # Enable WAL mode for SQLite databases
    if cfg.database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(
            dbapi_conn: sqlite3.Connection,
            connection_record: object,  # noqa: ARG001
        ) -> None:
            """Set SQLite pragmas for better concurrent access."""
            cursor = dbapi_conn.cursor()
            # Enable WAL mode (Write-Ahead Logging) for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Increase busy timeout (already set in connect_args, but ensure it)
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

    return engine


def create_all_tables(engine: Engine) -> None:
    """Create all tables defined by SQLModel metadata if they do not exist.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine bound to the target database.
    """
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(engine: Engine, max_retries: int = 3) -> Iterator[Session]:
    """Yield a short-lived database session with retry logic.

    Intended for request-scoped/session-scoped usage in services and
    repositories. Automatically retries on database lock errors with
    exponential backoff.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine bound to the target database.
    max_retries : int
        Maximum number of retry attempts for database lock errors (default: 3).

    Yields
    ------
    Session
        An active SQLModel session that is committed on success and
        rolled back on exception.
    """
    session = Session(engine)
    try:
        yield session
        # Retry commit on lock errors
        retry_count = 0
        while retry_count < max_retries:
            try:
                session.commit()
                break
            except OperationalError as e:
                if (
                    "database is locked" in str(e).lower()
                    and retry_count < max_retries - 1
                ):
                    retry_count += 1
                    # Exponential backoff: 0.1s, 0.2s, 0.4s
                    wait_time = 0.1 * (2 ** (retry_count - 1))
                    time.sleep(wait_time)
                    continue
                # Not a lock error or max retries reached
                raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

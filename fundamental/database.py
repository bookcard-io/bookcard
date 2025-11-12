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

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlmodel import Session, SQLModel, create_engine

from fundamental.config import AppConfig

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine


def create_db_engine(config: AppConfig | None = None) -> Engine:
    """Create a SQLAlchemy engine for the configured database.

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
    return create_engine(cfg.database_url, echo=cfg.echo_sql, future=True)


def create_all_tables(engine: Engine) -> None:
    """Create all tables defined by SQLModel metadata if they do not exist.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine bound to the target database.
    """
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(engine: Engine) -> Iterator[Session]:
    """Yield a short-lived database session.

    Intended for request-scoped/session-scoped usage in services and
    repositories.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine bound to the target database.

    Yields
    ------
    Session
        An active SQLModel session that is committed on success and
        rolled back on exception.
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

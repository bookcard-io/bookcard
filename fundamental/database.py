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

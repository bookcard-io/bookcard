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

"""SQLite retry policy helpers.

Calibre uses SQLite with triggers; transient "database is locked/busy" errors can
occur under concurrency. This module provides a small policy object that can be
shared by repository services.
"""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy.exc import OperationalError

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from sqlmodel import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SQLiteRetryPolicy:
    """Retry policy for transient SQLite locking errors.

    Notes
    -----
    SQLite raises `sqlalchemy.exc.OperationalError` for lock contention. This
    policy treats only "database is locked" and "database is busy" as transient.
    """

    def __init__(self, *, max_retries: int = 3) -> None:
        self._max_retries = max_retries

    @staticmethod
    def is_lock_error(exc: OperationalError) -> bool:
        """Return True if an OperationalError looks like a transient lock error."""
        msg = str(exc).lower()
        return ("database is locked" in msg) or ("database is busy" in msg)

    @staticmethod
    def sleep_with_backoff(attempt: int) -> None:
        """Sleep using exponential backoff with small jitter."""
        base = 0.1 * (2 ** max(0, attempt - 1))
        delay = base + random.uniform(0, 0.05)  # noqa: S311
        time.sleep(delay)

    def run_read(
        self,
        session_factory: Callable[[], AbstractContextManager[Session]],
        operation: Callable[[Session], T],
        *,
        operation_name: str,
        max_retries: int | None = None,
    ) -> T:
        """Execute a read-only operation with retry on transient lock errors.

        Parameters
        ----------
        session_factory : Callable[[], Session]
            Factory that returns a ready-to-use `Session`. The policy will close
            the session after use.
        operation : Callable[[Session], T]
            Read operation to execute.
        operation_name : str
            Name used for debugging logs.
        max_retries : int | None
            Override the policy default max retries.

        Returns
        -------
        T
            Operation result.

        Raises
        ------
        OperationalError
            If the error is non-transient, or retries are exhausted.
        """
        retries = self._max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            try:
                with session_factory() as session:
                    return operation(session)
            except OperationalError as e:
                if self.is_lock_error(e) and attempt < retries - 1:
                    attempt += 1
                    logger.debug(
                        "SQLite locked during %s, retrying (attempt %d/%d)",
                        operation_name,
                        attempt + 1,
                        retries,
                    )
                    self.sleep_with_backoff(attempt)
                    continue
                raise

    def commit(self, session: Session, *, max_retries: int | None = None) -> None:
        """Commit a session, retrying on transient SQLite lock errors."""
        retries = self._max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            try:
                session.commit()
            except OperationalError as e:
                if self.is_lock_error(e) and attempt < retries - 1:
                    attempt += 1
                    logger.debug(
                        "SQLite locked during commit, retrying (attempt %d/%d)",
                        attempt + 1,
                        retries,
                    )
                    self.sleep_with_backoff(attempt)
                    continue
                raise
            else:
                return

    def flush(self, session: Session, *, max_retries: int | None = None) -> None:
        """Flush a session, retrying on transient SQLite lock errors."""
        retries = self._max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            try:
                session.flush()
            except OperationalError as e:
                if self.is_lock_error(e) and attempt < retries - 1:
                    attempt += 1
                    logger.debug(
                        "SQLite locked during flush, retrying (attempt %d/%d)",
                        attempt + 1,
                        retries,
                    )
                    self.sleep_with_backoff(attempt)
                    continue
                raise
            else:
                return

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

"""Worker pool management."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manages the thread pool executor.

    Handles submission of tasks and shutdown of the executor.
    """

    def __init__(
        self,
        executor: concurrent.futures.Executor | None = None,
        max_workers: int = 8,
    ) -> None:
        """Initialize worker pool.

        Parameters
        ----------
        executor : concurrent.futures.Executor | None
            Optional executor instance. If None, a ThreadPoolExecutor is created.
        max_workers : int
            Maximum number of workers if creating a default executor.
        """
        self._executor = executor or concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="TaskWorker",
        )

    def submit(
        self,
        fn: Callable[..., Any],
        *args: object,
        **kwargs: object,
    ) -> concurrent.futures.Future:
        """Submit a function to the executor.

        Parameters
        ----------
        fn : Callable
            Function to execute.
        *args : Any
            Positional arguments for the function.
        **kwargs : Any
            Keyword arguments for the function.

        Returns
        -------
        concurrent.futures.Future
            Future representing the execution of the function.
        """
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """Shutdown the executor.

        Parameters
        ----------
        wait : bool
            Whether to wait for pending futures to finish.
        cancel_futures : bool
            Whether to cancel pending futures.
        """
        # Note: cancel_futures is available in Python 3.9+ for ThreadPoolExecutor
        # We should check if the executor supports it or if we are on a version that supports it.
        # However, concurrent.futures.Executor.shutdown signature in 3.9+ includes cancel_futures.
        # If the passed executor is custom, it might not support it.
        # For standard ThreadPoolExecutor in 3.9+, it works.
        try:
            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        except TypeError:
            # Fallback for older python or executors that don't support cancel_futures
            self._executor.shutdown(wait=wait)

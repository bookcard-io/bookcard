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

"""Tests for WorkerPool."""

from __future__ import annotations

import concurrent.futures
from unittest.mock import MagicMock

from bookcard.services.tasks.thread_runner.worker import WorkerPool


class TestWorkerPool:
    """Tests for WorkerPool."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        pool = WorkerPool()
        assert isinstance(pool._executor, concurrent.futures.ThreadPoolExecutor)
        pool.shutdown()

    def test_init_custom_executor(self) -> None:
        """Test initialization with custom executor."""
        mock_executor = MagicMock(spec=concurrent.futures.Executor)
        pool = WorkerPool(executor=mock_executor)
        assert pool._executor == mock_executor

    def test_submit(self) -> None:
        """Test submitting a task."""
        mock_executor = MagicMock(spec=concurrent.futures.Executor)
        pool = WorkerPool(executor=mock_executor)
        mock_fn = MagicMock()
        pool.submit(mock_fn, 1, key="value")
        mock_executor.submit.assert_called_once_with(mock_fn, 1, key="value")

    def test_shutdown(self) -> None:
        """Test shutdown."""
        mock_executor = MagicMock(spec=concurrent.futures.Executor)
        pool = WorkerPool(executor=mock_executor)
        pool.shutdown(wait=True, cancel_futures=True)
        mock_executor.shutdown.assert_called_once_with(wait=True, cancel_futures=True)

    def test_shutdown_fallback(self) -> None:
        """Test shutdown fallback for executors not supporting cancel_futures."""
        mock_executor = MagicMock(spec=concurrent.futures.Executor)

        def shutdown_side_effect(*args: object, **kwargs: object) -> None:
            if "cancel_futures" in kwargs:
                raise TypeError("unexpected keyword argument 'cancel_futures'")
            return

        mock_executor.shutdown.side_effect = shutdown_side_effect

        pool = WorkerPool(executor=mock_executor)
        pool.shutdown(wait=True, cancel_futures=True)

        # Should have called shutdown twice: once with cancel_futures (failed)
        # and once without (succeeded)
        assert mock_executor.shutdown.call_count == 2
        mock_executor.shutdown.assert_called_with(wait=True)

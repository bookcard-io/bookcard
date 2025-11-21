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

"""Tests for ScanWorkerManager to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from fundamental.services.library_scanning.workers.manager import ScanWorkerManager


@pytest.fixture
def redis_url() -> str:
    """Create Redis URL for testing.

    Returns
    -------
    str
        Redis URL.
    """
    return "redis://localhost:6379/0"


class TestScanWorkerManagerInit:
    """Test ScanWorkerManager initialization."""

    def test_init_stores_broker_and_threads(self, redis_url: str) -> None:
        """Test __init__ stores broker and threads_per_worker.

        Parameters
        ----------
        redis_url : str
            Redis URL.
        """
        manager = ScanWorkerManager(redis_url, threads_per_worker=3)
        assert manager.broker is not None
        assert manager.threads_per_worker == 3
        assert manager.workers == []
        assert manager._started is False


class TestScanWorkerManagerStartWorkers:
    """Test ScanWorkerManager.start_workers method."""

    def test_start_workers_creates_and_starts_workers(self, redis_url: str) -> None:
        """Test start_workers creates and starts workers."""
        manager = ScanWorkerManager(redis_url, threads_per_worker=1)
        # Mock the broker's start method
        manager.broker.start = MagicMock()  # type: ignore[method-assign]
        manager.start_workers()

        assert manager._started is True
        assert len(manager.workers) == 6  # 6 worker types
        manager.broker.start.assert_called_once()  # type: ignore[attr-defined]

    def test_start_workers_when_already_started(self, redis_url: str) -> None:
        """Test start_workers when already started (covers lines 62-63).

        Parameters
        ----------
        redis_url : str
            Redis URL.
        """
        manager = ScanWorkerManager(redis_url)
        manager._started = True
        manager.start_workers()

        # Should not create new workers
        assert len(manager.workers) == 0


class TestScanWorkerManagerStopWorkers:
    """Test ScanWorkerManager.stop_workers method."""

    def test_stop_workers_when_started(self, redis_url: str) -> None:
        """Test stop_workers when started."""
        manager = ScanWorkerManager(redis_url)
        manager._started = True
        manager.broker = MagicMock()
        manager.stop_workers()

        assert manager._started is False
        manager.broker.stop.assert_called_once()

    def test_stop_workers_when_not_started(self, redis_url: str) -> None:
        """Test stop_workers when not started (covers line 96).

        Parameters
        ----------
        redis_url : str
            Redis URL.
        """
        manager = ScanWorkerManager(redis_url)
        manager.broker = MagicMock()
        manager.stop_workers()

        # Should not call stop if not started
        manager.broker.stop.assert_not_called()


class TestScanWorkerManagerGetRedisUrl:
    """Test ScanWorkerManager.get_redis_url static method."""

    @pytest.mark.parametrize(
        ("redis_password", "redis_host", "redis_port", "expected_url"),
        [
            (None, "localhost", "6379", "redis://localhost:6379/0"),
            ("password", "localhost", "6379", "redis://:password@localhost:6379/0"),
            (None, "redis.example.com", "6380", "redis://redis.example.com:6380/0"),
            (
                "secret",
                "redis.example.com",
                "6380",
                "redis://:secret@redis.example.com:6380/0",
            ),
        ],
    )
    def test_get_redis_url_with_various_env_vars(
        self,
        monkeypatch: pytest.MonkeyPatch,
        redis_password: str | None,
        redis_host: str,
        redis_port: str,
        expected_url: str,
    ) -> None:
        """Test get_redis_url with various environment variables (covers lines 117-123).

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch fixture.
        redis_password : str | None
            Redis password.
        redis_host : str
            Redis host.
        redis_port : str
            Redis port.
        expected_url : str
            Expected Redis URL.
        """
        if redis_password:
            monkeypatch.setenv("REDIS_PASSWORD", redis_password)
        else:
            monkeypatch.delenv("REDIS_PASSWORD", raising=False)
        monkeypatch.setenv("REDIS_HOST", redis_host)
        monkeypatch.setenv("REDIS_PORT", redis_port)

        result = ScanWorkerManager.get_redis_url()
        assert result == expected_url

    def test_get_redis_url_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_redis_url with default values.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch fixture.
        """
        monkeypatch.delenv("REDIS_PASSWORD", raising=False)
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)

        result = ScanWorkerManager.get_redis_url()
        assert result == "redis://localhost:6379/0"

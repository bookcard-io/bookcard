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

"""Tests for service bootstrap and lifecycle management."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from bookcard.api.services.bootstrap import (
    initialize_services,
    start_background_services,
    stop_background_services,
)


@pytest.fixture
def fastapi_app() -> FastAPI:
    """Create a FastAPI app instance for testing.

    Returns
    -------
    FastAPI
        FastAPI application instance.
    """
    app = FastAPI()
    # Initialize state attributes as needed
    if not hasattr(app.state, "task_runner"):
        app.state.task_runner = None
    if not hasattr(app.state, "scan_worker_manager"):
        app.state.scan_worker_manager = None
    if not hasattr(app.state, "scheduler"):
        app.state.scheduler = None
    if not hasattr(app.state, "ingest_watcher"):
        app.state.ingest_watcher = None
    return app


@pytest.fixture
def mock_container() -> MagicMock:
    """Create a mock service container.

    Returns
    -------
    MagicMock
        Mock service container.
    """
    container = MagicMock()
    container.create_task_runner.return_value = MagicMock()
    container.create_redis_broker.return_value = MagicMock()
    container.create_scan_worker_manager.return_value = MagicMock()
    container.create_scheduler.return_value = MagicMock()
    container.create_ingest_watcher.return_value = MagicMock()
    return container


@pytest.fixture
def mock_scan_worker_manager() -> MagicMock:
    """Create a mock scan worker manager.

    Returns
    -------
    MagicMock
        Mock scan worker manager with start_workers and stop_workers methods.
    """
    manager = MagicMock()
    manager.start_workers = MagicMock()
    manager.stop_workers = MagicMock()
    return manager


@pytest.fixture
def mock_scheduler() -> MagicMock:
    """Create a mock scheduler.

    Returns
    -------
    MagicMock
        Mock scheduler with start and shutdown methods.
    """
    scheduler = MagicMock()
    scheduler.start = MagicMock()
    scheduler.shutdown = MagicMock()
    # Remove methods that would be checked before 'start'
    del scheduler.start_workers
    del scheduler.start_watching
    del scheduler.stop_workers
    del scheduler.stop_watching
    return scheduler


@pytest.fixture
def mock_ingest_watcher() -> MagicMock:
    """Create a mock ingest watcher.

    Returns
    -------
    MagicMock
        Mock ingest watcher with start_watching and stop_watching methods.
    """
    watcher = MagicMock()
    watcher.start_watching = MagicMock()
    watcher.stop_watching = MagicMock()
    # Remove methods that would be checked before 'start_watching'
    del watcher.start_workers
    del watcher.stop_workers
    del watcher.start
    del watcher.shutdown
    return watcher


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock task runner.

    Returns
    -------
    MagicMock
        Mock task runner with shutdown method.
    """
    runner = MagicMock()
    runner.shutdown = MagicMock()
    return runner


class TestInitializeServices:
    """Test initialize_services function."""

    def test_initialize_services_success(
        self, fastapi_app: FastAPI, mock_container: MagicMock
    ) -> None:
        """Test successful service initialization.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_container : MagicMock
            Mock service container.
        """
        initialize_services(fastapi_app, mock_container)

        assert hasattr(fastapi_app.state, "task_runner")
        assert hasattr(fastapi_app.state, "scan_worker_broker")
        assert hasattr(fastapi_app.state, "scan_worker_manager")
        assert hasattr(fastapi_app.state, "scheduler")
        assert hasattr(fastapi_app.state, "ingest_watcher")

        mock_container.create_task_runner.assert_called_once()
        mock_container.create_redis_broker.assert_called_once()
        mock_container.create_scan_worker_manager.assert_called_once()
        mock_container.create_scheduler.assert_called_once_with(
            fastapi_app.state.task_runner
        )
        mock_container.create_ingest_watcher.assert_called_once_with(
            fastapi_app.state.task_runner
        )


class TestStartBackgroundServices:
    """Test start_background_services function."""

    def test_start_background_services_scan_workers(
        self,
        fastapi_app: FastAPI,
        mock_scan_worker_manager: MagicMock,
    ) -> None:
        """Test starting scan worker manager.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scan_worker_manager : MagicMock
            Mock scan worker manager.
        """
        fastapi_app.state.scan_worker_manager = mock_scan_worker_manager
        start_background_services(fastapi_app)

        mock_scan_worker_manager.start_workers.assert_called_once()

    def test_start_background_services_scheduler(
        self,
        fastapi_app: FastAPI,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test starting scheduler.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scheduler : MagicMock
            Mock scheduler.
        """
        # Ensure scheduler doesn't have start_workers or start_watching
        if hasattr(mock_scheduler, "start_workers"):
            del mock_scheduler.start_workers
        if hasattr(mock_scheduler, "start_watching"):
            del mock_scheduler.start_watching
        fastapi_app.state.scheduler = mock_scheduler
        start_background_services(fastapi_app)

        mock_scheduler.start.assert_called_once()

    def test_start_background_services_ingest_watcher(
        self,
        fastapi_app: FastAPI,
        mock_ingest_watcher: MagicMock,
    ) -> None:
        """Test starting ingest watcher.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_ingest_watcher : MagicMock
            Mock ingest watcher.
        """
        # Ensure ingest watcher doesn't have start_workers
        if hasattr(mock_ingest_watcher, "start_workers"):
            del mock_ingest_watcher.start_workers
        fastapi_app.state.ingest_watcher = mock_ingest_watcher
        start_background_services(fastapi_app)

        mock_ingest_watcher.start_watching.assert_called_once()

    def test_start_background_services_all_services(
        self,
        fastapi_app: FastAPI,
        mock_scan_worker_manager: MagicMock,
        mock_scheduler: MagicMock,
        mock_ingest_watcher: MagicMock,
    ) -> None:
        """Test starting all background services together.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scan_worker_manager : MagicMock
            Mock scan worker manager.
        mock_scheduler : MagicMock
            Mock scheduler.
        mock_ingest_watcher : MagicMock
            Mock ingest watcher.
        """
        # Ensure services don't have conflicting methods
        if hasattr(mock_scheduler, "start_workers"):
            del mock_scheduler.start_workers
        if hasattr(mock_scheduler, "start_watching"):
            del mock_scheduler.start_watching
        if hasattr(mock_ingest_watcher, "start_workers"):
            del mock_ingest_watcher.start_workers
        fastapi_app.state.scan_worker_manager = mock_scan_worker_manager
        fastapi_app.state.scheduler = mock_scheduler
        fastapi_app.state.ingest_watcher = mock_ingest_watcher

        start_background_services(fastapi_app)

        mock_scan_worker_manager.start_workers.assert_called_once()
        mock_scheduler.start.assert_called_once()
        mock_ingest_watcher.start_watching.assert_called_once()

    @pytest.mark.parametrize(
        ("exception_type", "service_name"),
        [
            (ConnectionError, "scan workers"),
            (ValueError, "scheduler"),
            (RuntimeError, "ingest watcher"),
            (ImportError, "scan workers"),
            (OSError, "scheduler"),
        ],
    )
    def test_start_background_services_exception_handling(
        self,
        fastapi_app: FastAPI,
        exception_type: type[Exception],
        service_name: str,
    ) -> None:
        """Test exception handling when starting services.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        exception_type : type[Exception]
            Type of exception to raise.
        service_name : str
            Name of the service for identification.
        """
        if service_name == "scan workers":
            service = MagicMock()
            service.start_workers = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.scan_worker_manager = service
        elif service_name == "scheduler":
            service = MagicMock()
            service.start = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.scheduler = service
        else:  # ingest watcher
            service = MagicMock()
            service.start_watching = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.ingest_watcher = service

        # Should not raise, should log warning
        start_background_services(fastapi_app)


class TestStopBackgroundServices:
    """Test stop_background_services function."""

    def test_stop_background_services_scan_workers(
        self,
        fastapi_app: FastAPI,
        mock_scan_worker_manager: MagicMock,
    ) -> None:
        """Test stopping scan worker manager.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scan_worker_manager : MagicMock
            Mock scan worker manager.
        """
        fastapi_app.state.scan_worker_manager = mock_scan_worker_manager
        stop_background_services(fastapi_app)

        mock_scan_worker_manager.stop_workers.assert_called_once()

    def test_stop_background_services_scheduler(
        self,
        fastapi_app: FastAPI,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test stopping scheduler.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scheduler : MagicMock
            Mock scheduler.
        """
        # Ensure scheduler doesn't have stop_workers or stop_watching
        if hasattr(mock_scheduler, "stop_workers"):
            del mock_scheduler.stop_workers
        if hasattr(mock_scheduler, "stop_watching"):
            del mock_scheduler.stop_watching
        fastapi_app.state.scheduler = mock_scheduler
        stop_background_services(fastapi_app)

        mock_scheduler.shutdown.assert_called_once()

    def test_stop_background_services_ingest_watcher(
        self,
        fastapi_app: FastAPI,
        mock_ingest_watcher: MagicMock,
    ) -> None:
        """Test stopping ingest watcher.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_ingest_watcher : MagicMock
            Mock ingest watcher.
        """
        # Ensure ingest watcher doesn't have stop_workers
        if hasattr(mock_ingest_watcher, "stop_workers"):
            del mock_ingest_watcher.stop_workers
        fastapi_app.state.ingest_watcher = mock_ingest_watcher
        stop_background_services(fastapi_app)

        mock_ingest_watcher.stop_watching.assert_called_once()

    def test_stop_background_services_all_services(
        self,
        fastapi_app: FastAPI,
        mock_scan_worker_manager: MagicMock,
        mock_scheduler: MagicMock,
        mock_ingest_watcher: MagicMock,
    ) -> None:
        """Test stopping all background services together.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_scan_worker_manager : MagicMock
            Mock scan worker manager.
        mock_scheduler : MagicMock
            Mock scheduler.
        mock_ingest_watcher : MagicMock
            Mock ingest watcher.
        """
        # Ensure services don't have conflicting methods
        if hasattr(mock_scheduler, "stop_workers"):
            del mock_scheduler.stop_workers
        if hasattr(mock_scheduler, "stop_watching"):
            del mock_scheduler.stop_watching
        if hasattr(mock_ingest_watcher, "stop_workers"):
            del mock_ingest_watcher.stop_workers
        fastapi_app.state.scan_worker_manager = mock_scan_worker_manager
        fastapi_app.state.scheduler = mock_scheduler
        fastapi_app.state.ingest_watcher = mock_ingest_watcher

        stop_background_services(fastapi_app)

        mock_scan_worker_manager.stop_workers.assert_called_once()
        mock_scheduler.shutdown.assert_called_once()
        mock_ingest_watcher.stop_watching.assert_called_once()

    @pytest.mark.parametrize(
        ("exception_type", "service_name"),
        [
            (RuntimeError, "scan workers"),
            (OSError, "scheduler"),
            (RuntimeError, "ingest watcher"),
        ],
    )
    def test_stop_background_services_exception_handling(
        self,
        fastapi_app: FastAPI,
        exception_type: type[Exception],
        service_name: str,
    ) -> None:
        """Test exception handling when stopping services.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        exception_type : type[Exception]
            Type of exception to raise.
        service_name : str
            Name of the service for identification.
        """
        if service_name == "scan workers":
            service = MagicMock()
            service.stop_workers = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.scan_worker_manager = service
        elif service_name == "scheduler":
            service = MagicMock()
            service.shutdown = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.scheduler = service
        else:  # ingest watcher
            service = MagicMock()
            service.stop_watching = MagicMock(side_effect=exception_type("Test error"))
            fastapi_app.state.ingest_watcher = service

        # Should not raise, should log warning
        stop_background_services(fastapi_app)

    def test_stop_background_services_task_runner_shutdown(
        self,
        fastapi_app: FastAPI,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task runner shutdown (covers lines 192-193).

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_task_runner : MagicMock
            Mock task runner.
        """
        fastapi_app.state.task_runner = mock_task_runner
        stop_background_services(fastapi_app)

        mock_task_runner.shutdown.assert_called_once()

    def test_stop_background_services_task_runner_shutdown_exception(
        self,
        fastapi_app: FastAPI,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task runner shutdown exception handling (covers lines 192-193).

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_task_runner : MagicMock
            Mock task runner that raises exception.
        """
        mock_task_runner.shutdown.side_effect = RuntimeError("Shutdown error")
        fastapi_app.state.task_runner = mock_task_runner

        # Should not raise, should log warning
        stop_background_services(fastapi_app)

    def test_stop_background_services_task_runner_shutdown_oserror(
        self,
        fastapi_app: FastAPI,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test task runner shutdown OSError handling (covers lines 192-193).

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        mock_task_runner : MagicMock
            Mock task runner that raises OSError.
        """
        mock_task_runner.shutdown.side_effect = OSError("OS error")
        fastapi_app.state.task_runner = mock_task_runner

        # Should not raise, should log warning
        stop_background_services(fastapi_app)

    def test_stop_background_services_no_task_runner(
        self,
        fastapi_app: FastAPI,
    ) -> None:
        """Test stopping services when task runner is not present.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        """
        fastapi_app.state.task_runner = None
        # Should not raise
        stop_background_services(fastapi_app)

    def test_stop_background_services_task_runner_no_shutdown_method(
        self,
        fastapi_app: FastAPI,
    ) -> None:
        """Test stopping services when task runner has no shutdown method.

        Parameters
        ----------
        fastapi_app : FastAPI
            FastAPI application instance.
        """
        fastapi_app.state.task_runner = MagicMock()
        del fastapi_app.state.task_runner.shutdown
        # Should not raise
        stop_background_services(fastapi_app)

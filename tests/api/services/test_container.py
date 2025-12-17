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

"""Tests for service container."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.services.container import (
    ServiceContainer,
)
from bookcard.config import AppConfig


@pytest.fixture
def test_config() -> AppConfig:
    """Create test configuration.

    Returns
    -------
    AppConfig
        Test configuration instance.
    """
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key="test-key",
        redis_enabled=True,
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def test_config_no_redis() -> AppConfig:
    """Create test configuration with Redis disabled.

    Returns
    -------
    AppConfig
        Test configuration instance with Redis disabled.
    """
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key="test-key",
        redis_enabled=False,
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def mock_engine() -> MagicMock:
    """Create a mock database engine.

    Returns
    -------
    MagicMock
        Mock database engine.
    """
    return MagicMock()


@pytest.fixture
def container(test_config: AppConfig, mock_engine: MagicMock) -> ServiceContainer:
    """Create a service container instance.

    Parameters
    ----------
    test_config : AppConfig
        Test configuration.
    mock_engine : MagicMock
        Mock database engine.

    Returns
    -------
    ServiceContainer
        Service container instance.
    """
    return ServiceContainer(test_config, mock_engine)


class TestCreateTaskRunner:
    """Test create_task_runner method."""

    def test_create_task_runner_success(
        self, container: ServiceContainer, mock_engine: MagicMock
    ) -> None:
        """Test successful task runner creation.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        """
        with patch("bookcard.api.services.container.create_task_runner") as mock_create:
            mock_runner = MagicMock()
            mock_create.return_value = mock_runner

            result = container.create_task_runner()

            assert result == mock_runner
            mock_create.assert_called_once_with(mock_engine, container.config)

    @pytest.mark.parametrize(
        "exception_type",
        [
            ValueError,
            RuntimeError,
            OSError,
        ],
    )
    def test_create_task_runner_exception(
        self,
        container: ServiceContainer,
        mock_engine: MagicMock,
        exception_type: type[Exception],
    ) -> None:
        """Test task runner creation with exception.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        exception_type : type[Exception]
            Type of exception to raise.
        """
        with patch("bookcard.api.services.container.create_task_runner") as mock_create:
            mock_create.side_effect = exception_type("Test error")

            result = container.create_task_runner()

            assert result is None


class TestCreateRedisBroker:
    """Test create_redis_broker method."""

    def test_create_redis_broker_success(self, container: ServiceContainer) -> None:
        """Test successful Redis broker creation.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        """
        with patch("bookcard.api.services.container.RedisBroker") as mock_broker_class:
            mock_broker = MagicMock()
            mock_broker_class.return_value = mock_broker

            result = container.create_redis_broker()

            assert result == mock_broker
            mock_broker_class.assert_called_once_with(container.config.redis_url)

    def test_create_redis_broker_disabled(
        self, test_config_no_redis: AppConfig, mock_engine: MagicMock
    ) -> None:
        """Test Redis broker creation when Redis is disabled.

        Parameters
        ----------
        test_config_no_redis : AppConfig
            Configuration with Redis disabled.
        mock_engine : MagicMock
            Mock database engine.
        """
        container = ServiceContainer(test_config_no_redis, mock_engine)
        result = container.create_redis_broker()

        assert result is None

    @pytest.mark.parametrize(
        "exception_type",
        [
            ConnectionError,
            ValueError,
            RuntimeError,
            ImportError,
            OSError,
        ],
    )
    def test_create_redis_broker_exception(
        self,
        container: ServiceContainer,
        exception_type: type[Exception],
    ) -> None:
        """Test Redis broker creation with exception (covers lines 111-116).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        exception_type : type[Exception]
            Type of exception to raise.
        """
        with patch("bookcard.api.services.container.RedisBroker") as mock_broker_class:
            mock_broker_class.side_effect = exception_type("Test error")

            result = container.create_redis_broker()

            assert result is None


class TestCreateScanWorkerManager:
    """Test create_scan_worker_manager method."""

    def test_create_scan_worker_manager_success(
        self, container: ServiceContainer
    ) -> None:
        """Test successful scan worker manager creation.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        """
        with patch(
            "bookcard.api.services.container.ScanWorkerManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager

            result = container.create_scan_worker_manager()

            assert result == mock_manager
            mock_manager_class.assert_called_once_with(container.config.redis_url)

    def test_create_scan_worker_manager_disabled(
        self, test_config_no_redis: AppConfig, mock_engine: MagicMock
    ) -> None:
        """Test scan worker manager creation when Redis is disabled.

        Parameters
        ----------
        test_config_no_redis : AppConfig
            Configuration with Redis disabled.
        mock_engine : MagicMock
            Mock database engine.
        """
        container = ServiceContainer(test_config_no_redis, mock_engine)
        result = container.create_scan_worker_manager()

        assert result is None

    @pytest.mark.parametrize(
        "exception_type",
        [
            ConnectionError,
            ValueError,
            RuntimeError,
            ImportError,
            OSError,
        ],
    )
    def test_create_scan_worker_manager_exception(
        self,
        container: ServiceContainer,
        exception_type: type[Exception],
    ) -> None:
        """Test scan worker manager creation with exception (covers lines 133-138).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        exception_type : type[Exception]
            Type of exception to raise.
        """
        with patch(
            "bookcard.api.services.container.ScanWorkerManager"
        ) as mock_manager_class:
            mock_manager_class.side_effect = exception_type("Test error")

            result = container.create_scan_worker_manager()

            assert result is None


class TestCreateScheduler:
    """Test create_scheduler method."""

    def test_create_scheduler_success(
        self, container: ServiceContainer, mock_engine: MagicMock
    ) -> None:
        """Test successful scheduler creation.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        """
        mock_task_runner = MagicMock()
        with patch(
            "bookcard.api.services.container.TaskScheduler"
        ) as mock_scheduler_class:
            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler

            result = container.create_scheduler(mock_task_runner)

            assert result == mock_scheduler
            mock_scheduler_class.assert_called_once_with(mock_engine, mock_task_runner)

    def test_create_scheduler_disabled(
        self, test_config_no_redis: AppConfig, mock_engine: MagicMock
    ) -> None:
        """Test scheduler creation when Redis is disabled.

        Parameters
        ----------
        test_config_no_redis : AppConfig
            Configuration with Redis disabled.
        mock_engine : MagicMock
            Mock database engine.
        """
        container = ServiceContainer(test_config_no_redis, mock_engine)
        mock_task_runner = MagicMock()
        result = container.create_scheduler(mock_task_runner)

        assert result is None

    def test_create_scheduler_no_task_runner(self, container: ServiceContainer) -> None:
        """Test scheduler creation when task runner is None.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        """
        result = container.create_scheduler(None)

        assert result is None

    @pytest.mark.parametrize(
        "exception_type",
        [
            ConnectionError,
            ValueError,
            RuntimeError,
            ImportError,
            OSError,
        ],
    )
    def test_create_scheduler_exception(
        self,
        container: ServiceContainer,
        exception_type: type[Exception],
    ) -> None:
        """Test scheduler creation with exception (covers lines 166-171).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        exception_type : type[Exception]
            Type of exception to raise.
        """
        mock_task_runner = MagicMock()
        with patch(
            "bookcard.api.services.container.TaskScheduler"
        ) as mock_scheduler_class:
            mock_scheduler_class.side_effect = exception_type("Test error")

            result = container.create_scheduler(mock_task_runner)

            assert result is None


class TestCreateIngestWatcher:
    """Test create_ingest_watcher method."""

    def test_create_ingest_watcher_success(
        self, container: ServiceContainer, mock_engine: MagicMock
    ) -> None:
        """Test successful ingest watcher creation.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        """
        mock_task_runner = MagicMock()
        mock_config = SimpleNamespace(enabled=True)

        with (
            patch("bookcard.api.services.container.get_session") as mock_get_session,
            patch(
                "bookcard.api.services.container.IngestConfigService"
            ) as mock_config_service_class,
            patch(
                "bookcard.api.services.container.IngestWatcherService"
            ) as mock_watcher_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_service = MagicMock()
            mock_config_service.get_config.return_value = mock_config
            mock_config_service_class.return_value = mock_config_service
            mock_watcher = MagicMock()
            mock_watcher_class.return_value = mock_watcher

            result = container.create_ingest_watcher(mock_task_runner)

            assert result == mock_watcher
            mock_watcher_class.assert_called_once_with(
                engine=mock_engine, task_runner=mock_task_runner
            )

    def test_create_ingest_watcher_no_task_runner(
        self, container: ServiceContainer
    ) -> None:
        """Test ingest watcher creation when task runner is None.

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        """
        result = container.create_ingest_watcher(None)

        assert result is None

    def test_create_ingest_watcher_disabled(
        self, container: ServiceContainer, mock_engine: MagicMock
    ) -> None:
        """Test ingest watcher creation when ingest is disabled (covers lines 202-203).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        """
        mock_task_runner = MagicMock()
        mock_config = SimpleNamespace(enabled=False)

        with (
            patch("bookcard.api.services.container.get_session") as mock_get_session,
            patch(
                "bookcard.api.services.container.IngestConfigService"
            ) as mock_config_service_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_service = MagicMock()
            mock_config_service.get_config.return_value = mock_config
            mock_config_service_class.return_value = mock_config_service

            result = container.create_ingest_watcher(mock_task_runner)

            assert result is None

    @pytest.mark.parametrize(
        "exception_type",
        [
            ConnectionError,
            ValueError,
            RuntimeError,
            ImportError,
            OSError,
        ],
    )
    def test_create_ingest_watcher_exception(
        self,
        container: ServiceContainer,
        mock_engine: MagicMock,
        exception_type: type[Exception],
    ) -> None:
        """Test ingest watcher creation with exception (covers lines 211-216).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        exception_type : type[Exception]
            Type of exception to raise.
        """
        mock_task_runner = MagicMock()

        with patch("bookcard.api.services.container.get_session") as mock_get_session:
            # Test exception during config service creation
            if exception_type in (
                ConnectionError,
                ValueError,
                RuntimeError,
                ImportError,
                OSError,
            ):
                mock_get_session.side_effect = exception_type("Test error")

            result = container.create_ingest_watcher(mock_task_runner)

            assert result is None

    def test_create_ingest_watcher_exception_during_watcher_creation(
        self, container: ServiceContainer, mock_engine: MagicMock
    ) -> None:
        """Test ingest watcher creation with exception during watcher creation (covers lines 211-216).

        Parameters
        ----------
        container : ServiceContainer
            Service container instance.
        mock_engine : MagicMock
            Mock database engine.
        """
        mock_task_runner = MagicMock()
        mock_config = SimpleNamespace(enabled=True)

        with (
            patch("bookcard.api.services.container.get_session") as mock_get_session,
            patch(
                "bookcard.api.services.container.IngestConfigService"
            ) as mock_config_service_class,
            patch(
                "bookcard.api.services.container.IngestWatcherService"
            ) as mock_watcher_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_service = MagicMock()
            mock_config_service.get_config.return_value = mock_config
            mock_config_service_class.return_value = mock_config_service
            mock_watcher_class.side_effect = RuntimeError("Watcher creation error")

            result = container.create_ingest_watcher(mock_task_runner)

            assert result is None

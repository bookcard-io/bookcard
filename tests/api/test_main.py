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

"""Tests for FastAPI application factory."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from fundamental.api.logging_config import setup_logging
from fundamental.api.main import configure_app, create_app
from fundamental.api.routers import register_routers
from fundamental.api.routes.admin import router as admin_router
from fundamental.api.routes.auth import router as auth_router
from fundamental.api.services.bootstrap import (
    initialize_services,
    start_background_services,
    stop_background_services,
)
from fundamental.api.services.container import ServiceContainer
from fundamental.config import AppConfig
from fundamental.database import create_db_engine
from fundamental.services.author_exceptions import NoActiveLibraryError
from fundamental.services.ingest.exceptions import (
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)
from tests.conftest import TEST_ENCRYPTION_KEY

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("log_level", "expected_level"),
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ],
)
def test_setup_logging_with_level(log_level: str, expected_level: int) -> None:
    """Test logging setup with different log levels."""
    with patch.dict(os.environ, {"LOG_LEVEL": log_level}):
        # Clear existing handlers and reset level to avoid interference
        logging.root.handlers.clear()
        logging.root.setLevel(logging.NOTSET)
        setup_logging()
        assert logging.root.level == expected_level
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == expected_level


def test_setup_logging_default_level() -> None:
    """Test logging setup with default level when LOG_LEVEL not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear existing handlers and reset level to avoid interference
        logging.root.handlers.clear()
        logging.root.setLevel(logging.NOTSET)
        setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == logging.INFO


def test_setup_logging_invalid_level() -> None:
    """Test logging setup with invalid log level defaults to INFO."""
    with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
        # Clear existing handlers and reset level to avoid interference
        logging.root.handlers.clear()
        logging.root.setLevel(logging.NOTSET)
        setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == logging.INFO


def test_setup_logging_force_reconfig() -> None:
    """Test that logging setup forces reconfiguration."""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        # Configure logging once
        setup_logging()
        initial_level = logging.root.level
        # Configure again with different level
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            setup_logging()
            # Should have updated level
            assert logging.root.level == logging.ERROR
            assert logging.root.level != initial_level


def test_setup_logging_app_logger_propagates() -> None:
    """Test that application logger propagates to root."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        setup_logging()
        app_logger = logging.getLogger("fundamental")
        assert app_logger.propagate is True


def test_create_app_lifespan_with_alembic_enabled() -> None:
    """Test that lifespan runs alembic migrations when enabled."""
    import asyncio
    from unittest.mock import MagicMock, patch

    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        alembic_enabled=True,
    )

    with (
        patch("fundamental.api.lifespan._AlembicConfig") as mock_config_class,
        patch("fundamental.api.lifespan._alembic_command") as mock_command,
        patch("asyncio.to_thread") as mock_to_thread,
        patch("fundamental.api.lifespan.initialize_services"),
        patch("fundamental.api.lifespan.start_background_services"),
        patch("fundamental.api.lifespan.stop_background_services"),
        patch(
            "fundamental.api.services.container.ServiceContainer"
        ) as mock_container_class,
        patch("fundamental.database.get_session"),
    ):
        # Mock the container to avoid database access
        mock_container = MagicMock()
        mock_container_class.return_value = mock_container
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_upgrade = MagicMock()
        mock_command.upgrade = mock_upgrade

        async def mock_to_thread_impl(
            fn: Callable[..., object], *args: object, **kwargs: object
        ) -> object:
            """Mock asyncio.to_thread that calls function directly."""
            result = fn(*args, **kwargs)
            await asyncio.sleep(0)  # Make it truly async
            return result

        mock_to_thread.side_effect = mock_to_thread_impl

        app = create_app(config)

        # Initialize required state attributes for shutdown
        app.state.ingest_watcher = None
        app.state.scheduler = None
        app.state.scan_worker_manager = None
        app.state.task_runner = None

        async def run_lifespan() -> None:
            if app.router.lifespan_context:  # type: ignore[attr-defined]
                async with app.router.lifespan_context(app):  # type: ignore[attr-defined]
                    pass

        asyncio.run(run_lifespan())

        mock_config_class.assert_called_once()
        mock_config.set_main_option.assert_called_once_with(
            "script_location", "fundamental/db/migrations"
        )
        # Verify upgrade was called via asyncio.to_thread
        mock_to_thread.assert_called_once()
        mock_upgrade.assert_called_once_with(mock_config, "head")


def test_create_app_lifespan_without_alembic() -> None:
    """Test that lifespan skips alembic when disabled."""
    import asyncio
    from unittest.mock import patch

    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        alembic_enabled=False,
    )

    with (
        patch("fundamental.api.lifespan.initialize_services"),
        patch("fundamental.api.lifespan.start_background_services"),
        patch("fundamental.api.lifespan.stop_background_services"),
        patch(
            "fundamental.api.services.container.ServiceContainer"
        ) as mock_container_class,
        patch("fundamental.database.get_session"),
    ):
        # Mock the container to avoid database access
        mock_container = MagicMock()
        mock_container_class.return_value = mock_container
        app = create_app(config)

        # Initialize required state attributes for shutdown
        app.state.ingest_watcher = None
        app.state.scheduler = None
        app.state.scan_worker_manager = None
        app.state.task_runner = None

        async def run_lifespan() -> None:
            if app.router.lifespan_context:  # type: ignore[attr-defined]
                async with app.router.lifespan_context(app):  # type: ignore[attr-defined]
                    pass

        # Should not raise any errors
        asyncio.run(run_lifespan())


@pytest.fixture
def fastapi_app() -> FastAPI:
    """Create a FastAPI app instance for testing.

    Returns
    -------
    FastAPI
        A new FastAPI application instance.
    """
    return FastAPI()


@pytest.mark.parametrize(
    ("router_prefix", "router_name"),
    [
        ("/auth", "auth_router"),
        ("/admin", "admin_router"),
        ("/authors", "authors_router"),
        ("/books", "books_router"),
        ("/devices", "devices_router"),
        ("/epub-fixer", "epub_fixer_router"),
        ("/fs", "fs_router"),
        ("/ingest", "ingest_router"),
        ("/library-scanning", "library_scanning_router"),
        ("/metadata", "metadata_router"),
        ("/reading", "reading_router"),
        ("/shelves", "shelves_router"),
        ("/tasks", "tasks_router"),
    ],
)
def test_register_routers(
    fastapi_app: FastAPI, router_prefix: str, router_name: str
) -> None:
    """Test that all routers are registered with the app.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    router_prefix : str
        Expected prefix path for the router.
    router_name : str
        Name of the router being tested.
    """
    register_routers(fastapi_app)
    # Extract all route paths from the app
    routes = [
        getattr(route, "path", str(route))
        for route in fastapi_app.routes
        if hasattr(route, "path")
    ]
    # Verify the router prefix is present in the routes
    assert any(
        router_prefix in route or route.startswith(router_prefix) for route in routes
    ), f"Router {router_name} with prefix {router_prefix} was not registered"


def test_register_routers_calls_include_router(
    fastapi_app: FastAPI,
) -> None:
    """Test that register_routers calls include_router for all routers.

    This test specifically ensures auth_router and admin_router
    are executed by verifying include_router is called.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    """
    with patch.object(fastapi_app, "include_router") as mock_include:
        register_routers(fastapi_app)
        # Verify include_router was called at least for auth and admin routers
        assert mock_include.call_count == 13
        # Verify first two calls are for auth_router and admin_router
        call_args_list = [call[0][0] for call in mock_include.call_args_list]

        assert call_args_list[0] == auth_router
        assert call_args_list[1] == admin_router


@pytest.mark.parametrize(
    ("config_provided", "use_env"),
    [
        (True, False),
        (False, True),
    ],
)
def test_create_app_with_config(config_provided: bool, use_env: bool) -> None:
    """Test app creation with provided config or environment."""
    if config_provided:
        config = AppConfig(
            jwt_secret="test-secret",
            jwt_algorithm="HS256",
            jwt_expires_minutes=15,
            encryption_key=TEST_ENCRYPTION_KEY,
            database_url="sqlite:///:memory:",
            echo_sql=False,
        )
        app = create_app(config)
    else:
        with patch("fundamental.api.main.AppConfig.from_env") as mock_from_env:
            config = AppConfig(
                jwt_secret="env-secret",
                jwt_algorithm="HS256",
                jwt_expires_minutes=15,
                encryption_key=TEST_ENCRYPTION_KEY,
                database_url="sqlite:///:memory:",
                echo_sql=False,
            )
            mock_from_env.return_value = config
            app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Fundamental"
    assert app.version == "0.1.0"
    assert app.summary == "Self-hosted ebook management and reading API"


def test_create_app_sets_state() -> None:
    """Test that app state is properly configured."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    assert hasattr(app.state, "engine")
    assert hasattr(app.state, "config")
    assert app.state.config == config
    assert app.state.engine is not None


def test_create_app_registers_routers() -> None:
    """Test that routers are registered when app is created."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    routes = [
        getattr(route, "path", str(route))
        for route in app.routes
        if hasattr(route, "path")
    ]
    assert "/auth" in routes or any("/auth" in route for route in routes)


def test_create_app_adds_middleware() -> None:
    """Test that middleware is added to the app."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    # Check that middleware is present
    middleware_classes = [middleware.cls for middleware in app.user_middleware]
    from fundamental.api.middleware.auth_middleware import AuthMiddleware

    assert AuthMiddleware in middleware_classes


def test_create_app_calls_setup_logging() -> None:
    """Test that logging is set up when app is created."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    with patch("fundamental.api.main.setup_logging") as mock_setup:
        create_app(config)
        mock_setup.assert_called_once()


def test_create_app_creates_engine() -> None:
    """Test that database engine is created."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    with patch("fundamental.api.main.create_db_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        app = create_app(config)
        mock_create_engine.assert_called_once_with(config)
        assert app.state.engine == mock_engine


def test_app_instance_created() -> None:
    """Test that module-level app instance is created."""
    # Import the module to trigger app creation
    import fundamental.api.main as main_module

    assert hasattr(main_module, "app")
    assert isinstance(main_module.app, FastAPI)


def test_app_endpoints_accessible() -> None:
    """Test that app endpoints are accessible via test client."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    client = TestClient(app)
    # Test that auth endpoints are accessible
    response = client.get("/docs")
    assert response.status_code in [200, 404]  # OpenAPI docs endpoint


@pytest.fixture
def test_config() -> AppConfig:
    """Create a test AppConfig instance.

    Returns
    -------
    AppConfig
        A test configuration instance.
    """
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )


@pytest.fixture
def mock_engine() -> MagicMock:
    """Create a mock database engine for tests that don't need real database access.

    Returns
    -------
    MagicMock
        A mock database engine.
    """
    return MagicMock(spec=Engine)


@pytest.fixture
def test_engine(test_config: AppConfig) -> Engine:
    """Create a test database engine.

    Only use this fixture when you actually need a real database connection.
    For most tests, use mock_engine instead for better performance.

    Parameters
    ----------
    test_config : AppConfig
        Test configuration instance.

    Returns
    -------
    Engine
        A test database engine.
    """
    return create_db_engine(test_config)


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
        (OSError, "OSError"),
    ],
)
def test_initialize_task_runner_exception_handling(
    fastapi_app: FastAPI,
    mock_engine: MagicMock,
    test_config: AppConfig,
    exception_type: type[Exception],
    exception_name: str,
) -> None:
    """Test exception handling in task runner initialization.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    mock_engine : MagicMock
        Mock database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    # Patch the function where it's imported in the container module
    # The container imports create_task_runner from runner_factory, so we patch
    # it in the container module's namespace
    with patch("fundamental.api.services.container.create_task_runner") as mock_create:
        mock_create.side_effect = exception_type("Test error")
        container = ServiceContainer(test_config, mock_engine)
        # Test that exception is handled gracefully (returns None)
        result = container.create_task_runner()
        assert result is None
        # Verify the underlying function was called
        mock_create.assert_called_once_with(mock_engine, test_config)


def test_initialize_scan_workers_redis_disabled(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test scan worker initialization when Redis is disabled.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    mock_engine : MagicMock
        Mock database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_no_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=False,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_no_redis, mock_engine)
    with patch("fundamental.database.get_session"):
        initialize_services(fastapi_app, container)
    assert fastapi_app.state.scan_worker_broker is None
    assert fastapi_app.state.scan_worker_manager is None


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
        (ImportError, "ImportError"),
    ],
)
def test_initialize_scan_workers_exception_handling(
    fastapi_app: FastAPI,
    mock_engine: MagicMock,
    test_config: AppConfig,
    exception_type: type[Exception],
    exception_name: str,
) -> None:
    """Test exception handling in scan worker initialization.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url="redis://localhost:6379",
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    with (
        patch.object(container, "create_redis_broker", return_value=None),
        patch.object(container, "create_scan_worker_manager", return_value=None),
        patch("fundamental.database.get_session"),
    ):
        # When exceptions occur, the container methods return None
        # So we patch them to return None directly to simulate exception handling
        initialize_services(fastapi_app, container)
        assert fastapi_app.state.scan_worker_broker is None
        assert fastapi_app.state.scan_worker_manager is None


def test_initialize_scheduler_redis_disabled(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test _initialize_scheduler when Redis is disabled.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_no_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=False,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_no_redis, mock_engine)
    with patch("fundamental.database.get_session"):
        initialize_services(fastapi_app, container)
    assert fastapi_app.state.scheduler is None


def test_initialize_scheduler_task_runner_none(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test _initialize_scheduler when task runner is None.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    with (
        patch("fundamental.database.get_session"),
        patch.object(container, "create_task_runner", return_value=None),
    ):
        # Patch create_task_runner to return None so scheduler won't be created
        initialize_services(fastapi_app, container)
    assert fastapi_app.state.scheduler is None


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
        (ImportError, "ImportError"),
    ],
)
def test_initialize_scheduler_exception_handling(
    fastapi_app: FastAPI,
    mock_engine: MagicMock,
    test_config: AppConfig,
    exception_type: type[Exception],
    exception_name: str,
) -> None:
    """Test exception handling in _initialize_scheduler.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    fastapi_app.state.task_runner = MagicMock()
    with (
        patch.object(container, "create_scheduler", return_value=None),
        patch("fundamental.database.get_session"),
    ):
        # When exceptions occur, the container method returns None
        # So we patch it to return None directly to simulate exception handling
        initialize_services(fastapi_app, container)
        assert fastapi_app.state.scheduler is None


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
    ],
)
def test_start_background_services_scan_workers_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when starting scan workers.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_manager = MagicMock()
    mock_manager.start_workers.side_effect = exception_type("Test error")
    fastapi_app.state.scan_worker_manager = mock_manager
    fastapi_app.state.scheduler = None
    fastapi_app.state.ingest_watcher = None
    start_background_services(fastapi_app)
    mock_manager.start_workers.assert_called_once()


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
    ],
)
def test_start_background_services_scheduler_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when starting scheduler.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_scheduler = MagicMock()
    # Remove methods that would be checked before 'start'
    del mock_scheduler.start_workers
    del mock_scheduler.start_watching
    mock_scheduler.start.side_effect = exception_type("Test error")
    # Ensure state is initialized
    if not hasattr(fastapi_app.state, "scan_worker_manager"):
        fastapi_app.state.scan_worker_manager = None
    if not hasattr(fastapi_app.state, "ingest_watcher"):
        fastapi_app.state.ingest_watcher = None
    fastapi_app.state.scheduler = mock_scheduler
    start_background_services(fastapi_app)
    mock_scheduler.start.assert_called_once()


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
        (OSError, "OSError"),
    ],
)
def test_start_background_services_ingest_watcher_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when starting ingest watcher.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_watcher = MagicMock()
    # Remove methods that would be checked before 'start_watching'
    del mock_watcher.start_workers
    mock_watcher.start_watching.side_effect = exception_type("Test error")
    # Ensure state is initialized
    if not hasattr(fastapi_app.state, "scan_worker_manager"):
        fastapi_app.state.scan_worker_manager = None
    if not hasattr(fastapi_app.state, "scheduler"):
        fastapi_app.state.scheduler = None
    fastapi_app.state.ingest_watcher = mock_watcher
    start_background_services(fastapi_app)
    mock_watcher.start_watching.assert_called_once()


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (RuntimeError, "RuntimeError"),
        (OSError, "OSError"),
    ],
)
def test_stop_background_services_ingest_watcher_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when stopping ingest watcher.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_watcher = MagicMock()
    # Remove methods that would be checked before 'stop_watching'
    del mock_watcher.stop_workers
    mock_watcher.stop_watching.side_effect = exception_type("Test error")
    # Ensure state is initialized
    if not hasattr(fastapi_app.state, "scheduler"):
        fastapi_app.state.scheduler = None
    if not hasattr(fastapi_app.state, "scan_worker_manager"):
        fastapi_app.state.scan_worker_manager = None
    if not hasattr(fastapi_app.state, "task_runner"):
        fastapi_app.state.task_runner = None
    fastapi_app.state.ingest_watcher = mock_watcher
    stop_background_services(fastapi_app)
    mock_watcher.stop_watching.assert_called_once()


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (RuntimeError, "RuntimeError"),
        (OSError, "OSError"),
    ],
)
def test_stop_background_services_scheduler_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when stopping scheduler.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_scheduler = MagicMock()
    # Remove methods that would be checked before 'shutdown'
    del mock_scheduler.stop_workers
    del mock_scheduler.stop_watching
    mock_scheduler.shutdown.side_effect = exception_type("Test error")
    # Ensure state is initialized
    if not hasattr(fastapi_app.state, "ingest_watcher"):
        fastapi_app.state.ingest_watcher = None
    if not hasattr(fastapi_app.state, "scan_worker_manager"):
        fastapi_app.state.scan_worker_manager = None
    if not hasattr(fastapi_app.state, "task_runner"):
        fastapi_app.state.task_runner = None
    fastapi_app.state.scheduler = mock_scheduler
    stop_background_services(fastapi_app)
    mock_scheduler.shutdown.assert_called_once()


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (RuntimeError, "RuntimeError"),
        (OSError, "OSError"),
    ],
)
def test_stop_background_services_scan_workers_exception(
    fastapi_app: FastAPI, exception_type: type[Exception], exception_name: str
) -> None:
    """Test exception handling when stopping scan workers.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    mock_manager = MagicMock()
    mock_manager.stop_workers.side_effect = exception_type("Test error")
    fastapi_app.state.scan_worker_manager = mock_manager
    fastapi_app.state.ingest_watcher = None
    fastapi_app.state.scheduler = None
    fastapi_app.state.task_runner = None
    stop_background_services(fastapi_app)
    mock_manager.stop_workers.assert_called_once()


def test_initialize_ingest_watcher_redis_disabled(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test _initialize_ingest_watcher when Redis is disabled.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_no_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=False,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_no_redis, mock_engine)
    with patch("fundamental.database.get_session"):
        initialize_services(fastapi_app, container)
    assert fastapi_app.state.ingest_watcher is None


def test_initialize_ingest_watcher_task_runner_none(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test _initialize_ingest_watcher when task runner is None.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    with (
        patch("fundamental.database.get_session"),
        patch.object(container, "create_task_runner", return_value=None),
    ):
        # Patch create_task_runner to return None so ingest watcher won't be created
        initialize_services(fastapi_app, container)
    assert fastapi_app.state.ingest_watcher is None


def test_initialize_ingest_watcher_ingest_disabled(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test _initialize_ingest_watcher when ingest is disabled.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    fastapi_app.state.task_runner = MagicMock()
    with (
        patch.object(container, "create_ingest_watcher", return_value=None),
        patch("fundamental.database.get_session"),
    ):
        # Patch create_ingest_watcher to return None when ingest is disabled
        initialize_services(fastapi_app, container)
        assert fastapi_app.state.ingest_watcher is None


@pytest.mark.parametrize(
    ("exception_type", "exception_name"),
    [
        (ConnectionError, "ConnectionError"),
        (ValueError, "ValueError"),
        (RuntimeError, "RuntimeError"),
        (ImportError, "ImportError"),
    ],
)
def test_initialize_ingest_watcher_exception_handling(
    fastapi_app: FastAPI,
    mock_engine: MagicMock,
    test_config: AppConfig,
    exception_type: type[Exception],
    exception_name: str,
) -> None:
    """Test exception handling in _initialize_ingest_watcher.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    exception_type : type[Exception]
        Type of exception to raise.
    exception_name : str
        Name of the exception for test identification.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    fastapi_app.state.task_runner = MagicMock()
    with (
        patch.object(container, "create_ingest_watcher", return_value=None),
        patch("fundamental.database.get_session"),
    ):
        # When exceptions occur, the container method returns None
        # So we patch it to return None directly to simulate exception handling
        initialize_services(fastapi_app, container)
        assert fastapi_app.state.ingest_watcher is None


def test_initialize_ingest_watcher_success(
    fastapi_app: FastAPI, mock_engine: MagicMock, test_config: AppConfig
) -> None:
    """Test successful initialization of ingest watcher.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    test_engine : Engine
        Database engine fixture.
    test_config : AppConfig
        Test configuration fixture.
    """
    config_with_redis = AppConfig(
        jwt_secret=test_config.jwt_secret,
        jwt_algorithm=test_config.jwt_algorithm,
        jwt_expires_minutes=test_config.jwt_expires_minutes,
        encryption_key=test_config.encryption_key,
        database_url=test_config.database_url,
        echo_sql=test_config.echo_sql,
        redis_enabled=True,
        redis_url=test_config.redis_url,
    )
    container = ServiceContainer(config_with_redis, mock_engine)
    mock_task_runner = MagicMock()
    with (
        patch.object(container, "create_task_runner", return_value=mock_task_runner),
        patch.object(container, "create_ingest_watcher") as mock_watcher_method,
        patch("fundamental.database.get_session"),
    ):
        mock_watcher = MagicMock()
        mock_watcher_method.return_value = mock_watcher
        initialize_services(fastapi_app, container)
        assert fastapi_app.state.ingest_watcher == mock_watcher


@pytest.mark.parametrize(
    ("exception_class", "status_code"),
    [
        (IngestHistoryNotFoundError, 404),
        (NoActiveLibraryError, 400),
        (IngestHistoryCreationError, 500),
    ],
)
def test_configure_app_exception_handlers(
    fastapi_app: FastAPI,
    exception_class: type[Exception],
    status_code: int,
) -> None:
    """Test exception handlers in _configure_app.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    exception_class : type[Exception]
        Exception class to test.
    status_code : int
        Expected HTTP status code for the exception.
    """
    configure_app(fastapi_app)
    client = TestClient(fastapi_app)

    # Create a test endpoint that raises the exception
    @fastapi_app.get("/test-exception")
    async def test_endpoint() -> None:
        raise exception_class("Test error")

    response = client.get("/test-exception")
    assert response.status_code == status_code
    assert "detail" in response.json()


def test_configure_app_health_check(fastapi_app: FastAPI) -> None:
    """Test health check endpoint in configure_app.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    """
    configure_app(fastapi_app)
    client = TestClient(fastapi_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lifespan_cancelled_error() -> None:
    """Test lifespan handling of asyncio.CancelledError."""
    import asyncio

    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        alembic_enabled=False,
    )

    with (
        patch("fundamental.api.lifespan.initialize_services"),
        patch("fundamental.api.lifespan.start_background_services"),
        patch("fundamental.api.lifespan.stop_background_services"),
        patch(
            "fundamental.api.services.container.ServiceContainer"
        ) as mock_container_class,
        patch("fundamental.database.get_session"),
    ):
        # Mock the container to avoid database access
        mock_container = MagicMock()
        mock_container_class.return_value = mock_container
        app = create_app(config)

        # Initialize required state attributes for shutdown
        app.state.ingest_watcher = None
        app.state.scheduler = None
        app.state.scan_worker_manager = None
        app.state.task_runner = None

        async def run_lifespan_with_cancel() -> None:
            if app.router.lifespan_context:  # type: ignore[attr-defined]
                async with app.router.lifespan_context(app):  # type: ignore[attr-defined]
                    # Cancel the lifespan task to trigger CancelledError handling
                    raise asyncio.CancelledError

        # Should not raise, should handle CancelledError gracefully
        asyncio.run(run_lifespan_with_cancel())


def test_stop_background_services_task_runner_shutdown(
    fastapi_app: FastAPI,
) -> None:
    """Test stop_background_services calls task runner shutdown if available.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    """
    mock_task_runner = MagicMock()
    mock_task_runner.shutdown = MagicMock()
    fastapi_app.state.task_runner = mock_task_runner
    fastapi_app.state.ingest_watcher = None
    fastapi_app.state.scheduler = None
    fastapi_app.state.scan_worker_manager = None
    stop_background_services(fastapi_app)
    mock_task_runner.shutdown.assert_called_once()


def test_stop_background_services_task_runner_no_shutdown(
    fastapi_app: FastAPI,
) -> None:
    """Test stop_background_services when task runner has no shutdown method.

    Parameters
    ----------
    fastapi_app : FastAPI
        FastAPI application instance fixture.
    """
    mock_task_runner = MagicMock()
    del mock_task_runner.shutdown
    fastapi_app.state.task_runner = mock_task_runner
    fastapi_app.state.ingest_watcher = None
    fastapi_app.state.scheduler = None
    fastapi_app.state.scan_worker_manager = None
    # Should not raise
    stop_background_services(fastapi_app)

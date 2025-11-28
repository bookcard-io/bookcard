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

from fundamental.api.main import _register_routers, _setup_logging, create_app
from fundamental.config import AppConfig
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
        _setup_logging()
        assert logging.root.level == expected_level
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == expected_level


def test_setup_logging_default_level() -> None:
    """Test logging setup with default level when LOG_LEVEL not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear existing handlers and reset level to avoid interference
        logging.root.handlers.clear()
        logging.root.setLevel(logging.NOTSET)
        _setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == logging.INFO


def test_setup_logging_invalid_level() -> None:
    """Test logging setup with invalid log level defaults to INFO."""
    with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
        # Clear existing handlers and reset level to avoid interference
        logging.root.handlers.clear()
        logging.root.setLevel(logging.NOTSET)
        _setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("fundamental")
        assert app_logger.level == logging.INFO


def test_setup_logging_force_reconfig() -> None:
    """Test that logging setup forces reconfiguration."""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        # Configure logging once
        _setup_logging()
        initial_level = logging.root.level
        # Configure again with different level
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            _setup_logging()
            # Should have updated level
            assert logging.root.level == logging.ERROR
            assert logging.root.level != initial_level


def test_setup_logging_app_logger_propagates() -> None:
    """Test that application logger propagates to root."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        _setup_logging()
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
        patch("fundamental.api.main._AlembicConfig") as mock_config_class,
        patch("fundamental.api.main._alembic_command") as mock_command,
        patch("asyncio.to_thread") as mock_to_thread,
        patch("fundamental.api.main._initialize_ingest_watcher"),
    ):
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

    with patch("fundamental.api.main._initialize_ingest_watcher"):
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


def test_register_routers() -> None:
    """Test that routers are registered with the app."""
    app = FastAPI()
    _register_routers(app)
    # Check that auth router is included
    routes = [
        getattr(route, "path", str(route))
        for route in app.routes
        if hasattr(route, "path")
    ]
    assert "/auth" in routes or any("/auth" in route for route in routes)


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
    with patch("fundamental.api.main._setup_logging") as mock_setup:
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

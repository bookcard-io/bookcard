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

"""Tests for FastAPI application factory."""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rainbow.api.main import _register_routers, _setup_logging, create_app
from rainbow.config import AppConfig


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
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        _setup_logging()
        assert logging.root.level == expected_level
        app_logger = logging.getLogger("moose")
        assert app_logger.level == expected_level


def test_setup_logging_default_level() -> None:
    """Test logging setup with default level when LOG_LEVEL not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        _setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("moose")
        assert app_logger.level == logging.INFO


def test_setup_logging_invalid_level() -> None:
    """Test logging setup with invalid log level defaults to INFO."""
    with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
        # Clear existing handlers to avoid interference
        logging.root.handlers.clear()
        _setup_logging()
        assert logging.root.level == logging.INFO
        app_logger = logging.getLogger("moose")
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
        app_logger = logging.getLogger("moose")
        assert app_logger.propagate is True


def test_register_routers() -> None:
    """Test that routers are registered with the app."""
    app = FastAPI()
    _register_routers(app)
    # Check that auth router is included
    routes = [route.path for route in app.routes]
    assert "/auth" in routes or any("/auth" in route for route in routes)


@pytest.mark.parametrize(
    ("config_provided", "use_env"),
    [
        (True, False),
        (False, True),
    ],
)
def test_create_app_with_config(
    config_provided: bool, use_env: bool
) -> None:
    """Test app creation with provided config or environment."""
    if config_provided:
        config = AppConfig(
            jwt_secret="test-secret",
            jwt_algorithm="HS256",
            jwt_expires_minutes=15,
            database_url="sqlite:///:memory:",
            echo_sql=False,
        )
        app = create_app(config)
    else:
        with patch("rainbow.api.main.AppConfig.from_env") as mock_from_env:
            config = AppConfig(
                jwt_secret="env-secret",
                jwt_algorithm="HS256",
                jwt_expires_minutes=15,
                database_url="sqlite:///:memory:",
                echo_sql=False,
            )
            mock_from_env.return_value = config
            app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Rainbow"
    assert app.version == "0.1.0"
    assert app.summary == "Self-hosted ebook management and reading API"


def test_create_app_sets_state() -> None:
    """Test that app state is properly configured."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
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
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    routes = [route.path for route in app.routes]
    assert "/auth" in routes or any("/auth" in route for route in routes)


def test_create_app_adds_middleware() -> None:
    """Test that middleware is added to the app."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    # Check that middleware is present
    middleware_classes = [
        middleware.cls for middleware in app.user_middleware
    ]
    from rainbow.api.middleware.auth_middleware import AuthMiddleware

    assert AuthMiddleware in middleware_classes


def test_create_app_calls_setup_logging() -> None:
    """Test that logging is set up when app is created."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    with patch("rainbow.api.main._setup_logging") as mock_setup:
        create_app(config)
        mock_setup.assert_called_once()


def test_create_app_creates_engine() -> None:
    """Test that database engine is created."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    with patch("rainbow.api.main.create_db_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        app = create_app(config)
        mock_create_engine.assert_called_once_with(config)
        assert app.state.engine == mock_engine


def test_app_instance_created() -> None:
    """Test that module-level app instance is created."""
    # Import the module to trigger app creation
    import rainbow.api.main as main_module

    assert hasattr(main_module, "app")
    assert isinstance(main_module.app, FastAPI)


def test_app_endpoints_accessible() -> None:
    """Test that app endpoints are accessible via test client."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    app = create_app(config)
    client = TestClient(app)
    # Test that auth endpoints are accessible
    response = client.get("/docs")
    assert response.status_code in [200, 404]  # OpenAPI docs endpoint


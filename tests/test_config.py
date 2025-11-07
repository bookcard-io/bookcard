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

"""Tests for application configuration."""

import os
from unittest.mock import patch

import pytest

from rainbow.config import AppConfig


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("", False),
    ],
)
def test_parse_bool_env(env_value: str, expected: bool) -> None:
    """Test boolean environment variable parsing."""
    with patch.dict(os.environ, {"TEST_KEY": env_value}):
        result = AppConfig._parse_bool_env("TEST_KEY", "false")
        assert result == expected


def test_parse_bool_env_missing_key() -> None:
    """Test boolean parsing with missing environment variable."""
    with patch.dict(os.environ, {}, clear=True):
        result = AppConfig._parse_bool_env("MISSING_KEY", "false")
        assert result is False


def test_get_jwt_secret_success() -> None:
    """Test successful JWT secret retrieval."""
    with patch.dict(os.environ, {"RAINBOW_JWT_SECRET": "test-secret-123"}):
        result = AppConfig._get_jwt_secret()
        assert result == "test-secret-123"


def test_get_jwt_secret_missing() -> None:
    """Test JWT secret retrieval when environment variable is missing."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ValueError, match="RAINBOW_JWT_SECRET is not set"),
    ):
        AppConfig._get_jwt_secret()


def test_get_jwt_algorithm_success() -> None:
    """Test successful JWT algorithm retrieval."""
    with patch.dict(os.environ, {"RAINBOW_JWT_ALG": "HS256"}):
        result = AppConfig._get_jwt_algorithm()
        assert result == "HS256"


def test_get_jwt_algorithm_missing() -> None:
    """Test JWT algorithm retrieval when environment variable is missing."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ValueError, match="RAINBOW_JWT_ALG is not set"),
    ):
        AppConfig._get_jwt_algorithm()


@pytest.mark.parametrize(
    ("jwt_secret", "jwt_alg", "jwt_expires", "db_url", "echo_sql", "expected_echo"),
    [
        ("secret1", "HS256", "15", "sqlite:///test.db", "true", True),
        ("secret2", "HS512", "30", "postgresql://localhost/db", "false", False),
        ("secret3", "RS256", "60", "sqlite:///", "", False),
    ],
)
def test_from_env(
    jwt_secret: str,
    jwt_alg: str,
    jwt_expires: str,
    db_url: str,
    echo_sql: str,
    expected_echo: bool,
) -> None:
    """Test configuration creation from environment variables."""
    env_vars = {
        "RAINBOW_JWT_SECRET": jwt_secret,
        "RAINBOW_JWT_ALG": jwt_alg,
        "RAINBOW_JWT_EXPIRES_MIN": jwt_expires,
        "RAINBOW_DATABASE_URL": db_url,
        "RAINBOW_ECHO_SQL": echo_sql,
    }
    with patch.dict(os.environ, env_vars):
        config = AppConfig.from_env()
        assert config.jwt_secret == jwt_secret
        assert config.jwt_algorithm == jwt_alg
        assert config.jwt_expires_minutes == int(jwt_expires)
        assert config.database_url == db_url
        assert config.echo_sql == expected_echo


def test_from_env_default_database_url() -> None:
    """Test that default database URL is used when not set."""
    env_vars = {
        "RAINBOW_JWT_SECRET": "secret",
        "RAINBOW_JWT_ALG": "HS256",
        "RAINBOW_JWT_EXPIRES_MIN": "15",
    }
    with patch.dict(os.environ, env_vars):
        config = AppConfig.from_env()
        assert config.database_url == "sqlite:///rainbow.db"

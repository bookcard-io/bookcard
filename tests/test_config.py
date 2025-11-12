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

"""Tests for application configuration."""

import os
from unittest.mock import patch

import pytest

from fundamental.config import AppConfig


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
    with patch.dict(os.environ, {"FUNDAMENTAL_JWT_SECRET": "test-secret-123"}):
        result = AppConfig._get_jwt_secret()
        assert result == "test-secret-123"


def test_get_jwt_secret_missing() -> None:
    """Test JWT secret retrieval when environment variable is missing."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ValueError, match="FUNDAMENTAL_JWT_SECRET is not set"),
    ):
        AppConfig._get_jwt_secret()


def test_get_jwt_algorithm_success() -> None:
    """Test successful JWT algorithm retrieval."""
    with patch.dict(os.environ, {"FUNDAMENTAL_JWT_ALG": "HS256"}):
        result = AppConfig._get_jwt_algorithm()
        assert result == "HS256"


def test_get_jwt_algorithm_missing() -> None:
    """Test JWT algorithm retrieval when environment variable is missing."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ValueError, match="FUNDAMENTAL_JWT_ALG is not set"),
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
        "FUNDAMENTAL_JWT_SECRET": jwt_secret,
        "FUNDAMENTAL_JWT_ALG": jwt_alg,
        "FUNDAMENTAL_JWT_EXPIRES_MIN": jwt_expires,
        "FUNDAMENTAL_DATABASE_URL": db_url,
        "FUNDAMENTAL_ECHO_SQL": echo_sql,
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
        "FUNDAMENTAL_JWT_SECRET": "secret",
        "FUNDAMENTAL_JWT_ALG": "HS256",
        "FUNDAMENTAL_JWT_EXPIRES_MIN": "15",
    }
    with patch.dict(os.environ, env_vars):
        config = AppConfig.from_env()
        assert config.database_url == "sqlite:///fundamental.db"

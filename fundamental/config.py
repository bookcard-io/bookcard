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

"""Application configuration.

Provides centralized configuration for database and application settings.
Environment variables (if present) override default values.

Notes
-----
- Designed to be framework-agnostic and IOC-friendly.
- Keep this module free of side effects; defer heavy work to callers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable application configuration.

    Parameters
    ----------
    database_url : str
        SQLAlchemy URL for the database connection. Defaults to SQLite
        (``sqlite:///fundamental.db``). Can be overridden with environment variable
        or set to PostgreSQL (``postgresql+psycopg://...``) if needed.
    echo_sql : bool
        Whether to echo SQL statements for debugging.
    data_directory : str
        Base directory for user assets. User assets are organized as
        ``{data_directory}/{user_id}/assets/``, e.g., ``/data/1/profile_picture.jpg``.
        Can be overridden with ``DATA_DIRECTORY`` environment variable.
    task_runner : str
        Task runner type to use. Supported values: 'thread', 'dramatiq', 'celery'.
        Defaults to 'thread'. Can be overridden with ``TASK_RUNNER`` environment variable.
    """

    jwt_secret: str
    jwt_algorithm: str
    jwt_expires_minutes: int
    encryption_key: str
    alembic_enabled: bool = False
    database_url: str = "sqlite:///fundamental.db"
    echo_sql: bool = False
    data_directory: str = "/data"
    task_runner: str = "thread"
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = True

    @staticmethod
    def _normalize_env_value(value: str | None) -> str | None:
        """Normalize environment variable value by stripping whitespace.

        Parameters
        ----------
        value : str | None
            Environment variable value to normalize.

        Returns
        -------
        str | None
            Stripped value, or None if input was None.
        """
        if value is None:
            return None
        return value.strip()

    @staticmethod
    def _normalize_env_value_with_default(value: str | None, default: str) -> str:
        """Normalize environment variable value with a default.

        Parameters
        ----------
        value : str | None
            Environment variable value to normalize.
        default : str
            Default value to use if value is None.

        Returns
        -------
        str
            Stripped value, or stripped default if value was None.
        """
        return (value or default).strip()

    @staticmethod
    def _get_jwt_secret() -> str:
        """Get and validate JWT secret from environment.

        Returns
        -------
        str
            JWT secret value.

        Raises
        ------
        ValueError
            If FUNDAMENTAL_JWT_SECRET is not set.
        """
        jwt_secret = AppConfig._normalize_env_value(os.getenv("FUNDAMENTAL_JWT_SECRET"))
        if jwt_secret is None:
            msg = "FUNDAMENTAL_JWT_SECRET is not set"
            raise ValueError(msg)
        return jwt_secret

    @staticmethod
    def _get_jwt_algorithm() -> str:
        """Get and validate JWT algorithm from environment.

        Returns
        -------
        str
            JWT algorithm value.

        Raises
        ------
        ValueError
            If FUNDAMENTAL_JWT_ALG is not set.
        """
        jwt_algorithm = AppConfig._normalize_env_value(os.getenv("FUNDAMENTAL_JWT_ALG"))
        if jwt_algorithm is None:
            msg = "FUNDAMENTAL_JWT_ALG is not set"
            raise ValueError(msg)
        return jwt_algorithm

    @staticmethod
    def _get_encryption_key() -> str:
        """Get and validate encryption key from environment.

        Returns
        -------
        str
            Encryption key value (base64-encoded Fernet key).

        Raises
        ------
        ValueError
            If FUNDAMENTAL_FERNET_KEY is not set.
        """
        encryption_key = AppConfig._normalize_env_value(
            os.getenv("FUNDAMENTAL_FERNET_KEY")
        )
        if encryption_key is None:
            msg = "FUNDAMENTAL_FERNET_KEY is not set"
            raise ValueError(msg)
        return encryption_key

    @staticmethod
    def _get_redis_url() -> str:
        """Get Redis URL from environment.

        Returns
        -------
        str
            Redis connection URL.
        """
        redis_password = AppConfig._normalize_env_value(os.getenv("REDIS_PASSWORD"))
        redis_host = AppConfig._normalize_env_value_with_default(
            os.getenv("REDIS_HOST"), "localhost"
        )
        redis_port = AppConfig._normalize_env_value_with_default(
            os.getenv("REDIS_PORT"), "6379"
        )

        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        return f"redis://{redis_host}:{redis_port}/0"

    @staticmethod
    def _parse_bool_env(key: str, default: str = "false") -> bool:
        """Parse boolean environment variable.

        Parameters
        ----------
        key : str
            Environment variable name.
        default : str, optional
            Default value if not set, by default "false".

        Returns
        -------
        bool
            Parsed boolean value.
        """
        value = AppConfig._normalize_env_value_with_default(os.getenv(key), default)
        return value.lower() == "true"

    @staticmethod
    def from_env() -> AppConfig:
        """Create configuration from environment variables.

        Returns
        -------
        AppConfig
            Fully constructed configuration with env overrides applied.
        """
        jwt_expires_min = AppConfig._normalize_env_value(
            os.getenv("FUNDAMENTAL_JWT_EXPIRES_MIN", "131400")
        )
        return AppConfig(
            jwt_secret=AppConfig._get_jwt_secret(),
            jwt_algorithm=AppConfig._get_jwt_algorithm(),
            jwt_expires_minutes=int(jwt_expires_min),
            encryption_key=AppConfig._get_encryption_key(),
            database_url=(
                db_url
                if (
                    db_url := AppConfig._normalize_env_value(
                        os.getenv("FUNDAMENTAL_DATABASE_URL")
                    )
                )
                else "sqlite:///fundamental.db"
            ),
            echo_sql=AppConfig._parse_bool_env("FUNDAMENTAL_ECHO_SQL", "false"),
            alembic_enabled=AppConfig._parse_bool_env(
                "FUNDAMENTAL_ALEMBIC_ENABLED", "false"
            ),
            data_directory=AppConfig._normalize_env_value_with_default(
                os.getenv("DATA_DIRECTORY"), "/data"
            ),
            task_runner=AppConfig._normalize_env_value_with_default(
                os.getenv("TASK_RUNNER"), "thread"
            ).lower(),
            redis_url=AppConfig._get_redis_url(),
            redis_enabled=AppConfig._parse_bool_env("ENABLE_REDIS", "true"),
        )

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
    """

    jwt_secret: str
    jwt_algorithm: str
    jwt_expires_minutes: int
    database_url: str = "sqlite:///fundamental.db"
    echo_sql: bool = False

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
        jwt_secret = os.getenv("FUNDAMENTAL_JWT_SECRET")
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
        jwt_algorithm = os.getenv("FUNDAMENTAL_JWT_ALG")
        if jwt_algorithm is None:
            msg = "FUNDAMENTAL_JWT_ALG is not set"
            raise ValueError(msg)
        return jwt_algorithm

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
        return os.getenv(key, default).lower() == "true"

    @staticmethod
    def from_env() -> AppConfig:
        """Create configuration from environment variables.

        Returns
        -------
        AppConfig
            Fully constructed configuration with env overrides applied.
        """
        return AppConfig(
            jwt_secret=AppConfig._get_jwt_secret(),
            jwt_algorithm=AppConfig._get_jwt_algorithm(),
            jwt_expires_minutes=int(os.getenv("FUNDAMENTAL_JWT_EXPIRES_MIN")),
            database_url=os.getenv(
                "FUNDAMENTAL_DATABASE_URL", "sqlite:///fundamental.db"
            ),
            echo_sql=AppConfig._parse_bool_env("FUNDAMENTAL_ECHO_SQL", "false"),
        )

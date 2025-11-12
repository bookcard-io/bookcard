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

"""Security utilities: password hashing and JWT handling.

Adheres to SRP by encapsulating crypto and token details away from routes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import jwt
from passlib.context import CryptContext

if TYPE_CHECKING:
    from collections.abc import Callable

    from fundamental.config import AppConfig


class PasswordHasher:
    """BCrypt password hashing utility."""

    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        """Return a secure password hash for the given plaintext password."""
        return self._ctx.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Return True if the plaintext password matches the stored hash."""
        return self._ctx.verify(password, password_hash)


class JWTManager:
    """JWT encoder/decoder using AppConfig settings."""

    def __init__(self, config: AppConfig) -> None:  # type: ignore[type-arg]
        self._secret = config.jwt_secret
        self._alg = config.jwt_algorithm
        self._expires_minutes = int(config.jwt_expires_minutes)

    def create_access_token(
        self, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> str:
        """Create a short-lived access token with subject and optional claims.

        Includes a JWT ID (jti) claim for token blacklisting support.

        Parameters
        ----------
        subject : str
            Subject claim (typically user ID).
        extra_claims : dict[str, Any] | None
            Additional claims to include in the token.

        Returns
        -------
        str
            Encoded JWT token string.
        """
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self._expires_minutes)
        payload: dict[str, Any] = {
            "sub": subject,
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self._secret, algorithm=self._alg)

    def decode_token(
        self,
        token: str,
        is_blacklisted: Callable[[str], bool] | None = None,  # type: ignore[type-arg]
    ) -> dict[str, Any]:
        """Decode and validate a JWT, returning its claims if valid.

        Parameters
        ----------
        token : str
            JWT token string to decode.
        is_blacklisted : Callable[[str], bool] | None
            Optional function to check if a token JTI is blacklisted.
            Should return True if the token is blacklisted.

        Returns
        -------
        dict[str, Any]
            Decoded token claims.

        Raises
        ------
        SecurityTokenError
            If token is invalid, expired, or blacklisted.
        """
        try:
            claims = jwt.decode(token, self._secret, algorithms=[self._alg])
        except jwt.InvalidTokenError as err:  # type: ignore[attr-defined]
            raise SecurityTokenError from err

        # Check blacklist if provided
        if is_blacklisted is not None:
            jti = claims.get("jti")
            if jti and is_blacklisted(jti):
                raise SecurityTokenError(SecurityTokenError.BLACKLISTED_MESSAGE)

        return claims


class SecurityTokenError(Exception):
    """Raised when a JWT is invalid or cannot be decoded."""

    BLACKLISTED_MESSAGE = "Token is blacklisted"

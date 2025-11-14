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

"""Security utilities: password hashing, JWT handling, and data encryption.

Adheres to SRP by encapsulating crypto and token details away from routes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import jwt
from cryptography.fernet import Fernet, InvalidToken
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


class DataEncryptor:
    """Symmetric encryption utility for sensitive data.

    Uses Fernet (symmetric encryption) to encrypt and decrypt sensitive data
    such as SMTP passwords and OAuth tokens. Data must be encrypted before
    storage and decrypted when retrieved.

    Parameters
    ----------
    encryption_key : str
        Base64-encoded Fernet key. Can be generated using Fernet.generate_key().
        Should be stored securely (e.g., environment variable).

    Raises
    ------
    ValueError
        If encryption_key is invalid or cannot be used to create a Fernet instance.
    """

    def __init__(self, encryption_key: str) -> None:
        """Initialize the encryptor with a Fernet key.

        Parameters
        ----------
        encryption_key : str
            Base64-encoded Fernet key. Can be generated using Fernet.generate_key().

        Raises
        ------
        ValueError
            If the key is invalid.
        """
        try:
            # Fernet expects a base64-encoded key as bytes
            key_bytes = (
                encryption_key.encode()
                if isinstance(encryption_key, str)
                else encryption_key
            )
            self._fernet = Fernet(key_bytes)
        except Exception as e:
            msg = f"Invalid encryption key: {e}"
            raise ValueError(msg) from e

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext data.

        Parameters
        ----------
        plaintext : str
            Plaintext string to encrypt.

        Returns
        -------
        str
            Encrypted string (base64-encoded).

        Raises
        ------
        ValueError
            If plaintext is None or empty.
        """
        if not plaintext:
            msg = "Cannot encrypt empty or None value"
            raise ValueError(msg)
        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt encrypted data.

        Parameters
        ----------
        ciphertext : str
            Encrypted string (base64-encoded) to decrypt.

        Returns
        -------
        str
            Decrypted plaintext string.

        Raises
        ------
        ValueError
            If ciphertext is None, empty, or invalid.
        DecryptionError
            If decryption fails (e.g., wrong key or corrupted data).
        """
        if not ciphertext:
            msg = "Cannot decrypt empty or None value"
            raise ValueError(msg)
        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except InvalidToken as e:
            msg = "Failed to decrypt data: invalid or corrupted ciphertext"
            raise ValueError(msg) from e

    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary by JSON-encoding it first.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionary to encrypt.

        Returns
        -------
        str
            Encrypted JSON string.

        Raises
        ------
        ValueError
            If data is None or cannot be JSON-encoded.
        """
        import json

        if data is None:
            msg = "Cannot encrypt None value"
            raise ValueError(msg)
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, ciphertext: str) -> dict[str, Any]:
        """Decrypt and JSON-decode a dictionary.

        Parameters
        ----------
        ciphertext : str
            Encrypted JSON string.

        Returns
        -------
        dict[str, Any]
            Decrypted dictionary.

        Raises
        ------
        ValueError
            If decryption or JSON decoding fails.
        """
        import json

        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)


class DecryptionError(Exception):
    """Raised when decryption fails."""

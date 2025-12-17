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

"""Tests for security utilities: password hashing and JWT handling."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from bookcard.config import AppConfig
from bookcard.services.security import (
    JWTManager,
    PasswordHasher,
    SecurityTokenError,
)
from tests.conftest import TEST_ENCRYPTION_KEY


@pytest.mark.parametrize(
    "password",
    [
        "simple_password",
        "Complex@Password123",
        "very_long_password_" * 10,
        "short",
        "",
    ],
)
def test_password_hasher_hash(password: str) -> None:
    """Test password hashing produces different hashes for same password."""
    hasher = PasswordHasher()
    hash1 = hasher.hash(password)
    hash2 = hasher.hash(password)
    # BCrypt includes salt, so hashes should be different
    assert hash1 != hash2
    assert len(hash1) > 0


@pytest.mark.parametrize(
    ("password", "wrong_password"),
    [
        ("correct_password", "wrong_password"),
        ("test123", "test124"),
        ("", "not_empty"),
    ],
)
def test_password_hasher_verify_correct(password: str, wrong_password: str) -> None:
    """Test password verification with correct password."""
    hasher = PasswordHasher()
    password_hash = hasher.hash(password)
    assert hasher.verify(password, password_hash) is True
    assert hasher.verify(wrong_password, password_hash) is False


def test_password_hasher_verify_incorrect() -> None:
    """Test password verification with incorrect password."""
    hasher = PasswordHasher()
    password_hash = hasher.hash("correct_password")
    assert hasher.verify("wrong_password", password_hash) is False


@pytest.mark.parametrize(
    ("subject", "extra_claims"),
    [
        ("user123", None),
        ("user456", {"username": "testuser", "is_admin": True}),
        ("user789", {"username": "admin", "is_admin": False, "role": "user"}),
    ],
)
def test_jwt_manager_create_access_token(
    subject: str, extra_claims: dict[str, bool | str] | None
) -> None:
    """Test JWT token creation."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token(subject, extra_claims)
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_manager_create_access_token_contains_claims() -> None:
    """Test that created token contains expected claims."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token("user123", {"username": "testuser"})
    decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    assert decoded["sub"] == "user123"
    assert decoded["username"] == "testuser"
    assert "iat" in decoded
    assert "exp" in decoded


def test_jwt_manager_create_access_token_expiration() -> None:
    """Test that token expiration is set correctly."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=30,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token("user123")
    decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)
    iat_time = datetime.fromtimestamp(decoded["iat"], tz=UTC)
    expected_exp = iat_time + timedelta(minutes=30)
    # Allow 1 second tolerance
    assert abs((exp_time - expected_exp).total_seconds()) < 1


@pytest.mark.parametrize(
    ("algorithm", "secret"),
    [
        ("HS256", "secret-key-1"),
        ("HS512", "secret-key-2"),
    ],
)
def test_jwt_manager_decode_token_success(algorithm: str, secret: str) -> None:
    """Test successful JWT token decoding."""
    config = AppConfig(
        jwt_secret=secret,
        jwt_algorithm=algorithm,
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token("user123", {"username": "testuser"})
    claims = jwt_mgr.decode_token(token)
    assert claims["sub"] == "user123"
    assert claims["username"] == "testuser"


def test_jwt_manager_decode_token_invalid() -> None:
    """Test JWT token decoding with invalid token."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    with pytest.raises(SecurityTokenError):
        jwt_mgr.decode_token("invalid.token.here")


def test_jwt_manager_decode_token_wrong_secret() -> None:
    """Test JWT token decoding with wrong secret."""
    config1 = AppConfig(
        jwt_secret="secret1",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    config2 = AppConfig(
        jwt_secret="secret2",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr1 = JWTManager(config1)
    jwt_mgr2 = JWTManager(config2)
    token = jwt_mgr1.create_access_token("user123")
    with pytest.raises(SecurityTokenError):
        jwt_mgr2.decode_token(token)


def test_jwt_manager_decode_token_expired() -> None:
    """Test JWT token decoding with expired token."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=-1,  # Negative expiration for testing
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    # Create token with past expiration
    now = datetime.now(UTC)
    payload = {
        "sub": "user123",
        "iat": int((now - timedelta(minutes=2)).timestamp()),
        "exp": int((now - timedelta(minutes=1)).timestamp()),
    }
    expired_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    with pytest.raises(SecurityTokenError):
        jwt_mgr.decode_token(expired_token)


def test_jwt_manager_decode_token_blacklisted() -> None:
    """Test JWT token decoding with blacklisted token (covers lines 122-124)."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token("user123")

    # Decode to get the jti
    decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    jti = decoded["jti"]

    # Create a blacklist that includes this jti
    blacklist = {jti}

    def is_blacklisted(token_jti: str) -> bool:
        return token_jti in blacklist

    # Should raise SecurityTokenError when token is blacklisted
    with pytest.raises(SecurityTokenError) as exc_info:
        jwt_mgr.decode_token(token, is_blacklisted=is_blacklisted)
    assert str(exc_info.value) == SecurityTokenError.BLACKLISTED_MESSAGE


def test_jwt_manager_decode_token_not_blacklisted() -> None:
    """Test JWT token decoding with non-blacklisted token."""
    config = AppConfig(
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    jwt_mgr = JWTManager(config)
    token = jwt_mgr.create_access_token("user123")

    # Create a blacklist that doesn't include this token's jti
    blacklist = {"different-jti"}

    def is_blacklisted(token_jti: str) -> bool:
        return token_jti in blacklist

    # Should succeed when token is not blacklisted
    claims = jwt_mgr.decode_token(token, is_blacklisted=is_blacklisted)
    assert claims["sub"] == "user123"


def test_security_token_error() -> None:
    """Test SecurityTokenError exception."""
    error = SecurityTokenError()
    assert isinstance(error, Exception)


# Tests for DataEncryptor missing lines
def test_data_encryptor_init_invalid_key() -> None:
    """Test DataEncryptor.__init__ raises ValueError for invalid key (covers lines 176-178)."""
    from bookcard.services.security import DataEncryptor

    with pytest.raises(ValueError, match="Invalid encryption key"):
        DataEncryptor("invalid_key_too_short")


@pytest.mark.parametrize(
    "plaintext",
    [
        "",
        None,
    ],
)
def test_data_encryptor_encrypt_empty_or_none(plaintext: str | None) -> None:
    """Test DataEncryptor.encrypt raises ValueError for empty/None (covers lines 198-202)."""
    from bookcard.services.security import DataEncryptor

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)

    with pytest.raises(ValueError, match="Cannot encrypt empty or None value"):
        encryptor.encrypt(plaintext)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "ciphertext",
    [
        "",
        None,
    ],
)
def test_data_encryptor_decrypt_empty_or_none(ciphertext: str | None) -> None:
    """Test DataEncryptor.decrypt raises ValueError for empty/None (covers lines 224-226)."""
    from bookcard.services.security import DataEncryptor

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)

    with pytest.raises(ValueError, match="Cannot decrypt empty or None value"):
        encryptor.decrypt(ciphertext)  # type: ignore[arg-type]


def test_data_encryptor_decrypt_invalid_token() -> None:
    """Test DataEncryptor.decrypt raises ValueError for invalid token (covers lines 227-232)."""
    from bookcard.services.security import DataEncryptor

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)

    # Create truly invalid ciphertext (not properly encrypted)
    invalid_ciphertext = "invalid_encrypted_data_not_base64"

    with pytest.raises(ValueError, match="Failed to decrypt data"):
        encryptor.decrypt(invalid_ciphertext)


def test_data_encryptor_encrypt_dict_none() -> None:
    """Test DataEncryptor.encrypt_dict raises ValueError for None (covers lines 252-258)."""
    from bookcard.services.security import DataEncryptor

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)

    with pytest.raises(ValueError, match="Cannot encrypt None value"):
        encryptor.encrypt_dict(None)  # type: ignore[arg-type]


def test_data_encryptor_decrypt_dict_success() -> None:
    """Test DataEncryptor.decrypt_dict successfully decrypts and parses JSON (covers lines 278-281)."""
    from bookcard.services.security import DataEncryptor

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)
    original_data = {"key": "value", "number": 123, "nested": {"inner": "data"}}

    encrypted = encryptor.encrypt_dict(original_data)
    decrypted = encryptor.decrypt_dict(encrypted)

    assert decrypted == original_data

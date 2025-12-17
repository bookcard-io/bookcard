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

"""Tests for email configuration service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from bookcard.models.config import EmailServerConfig, EmailServerType
from bookcard.services.email_config_service import EmailConfigService


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_encryptor() -> MagicMock:
    """Create a mock data encryptor."""
    encryptor = MagicMock()
    encryptor.decrypt.return_value = "decrypted_password"
    encryptor.decrypt_dict.return_value = {
        "access_token": "token",
        "email": "test@gmail.com",
    }
    return encryptor


@pytest.fixture
def email_config() -> EmailServerConfig:
    """Create a test email server configuration."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_from_email="sender@example.com",
        smtp_username="user@example.com",
        smtp_password="encrypted_password",
        gmail_token="encrypted_token",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_email_config_service_init_with_encryptor(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
) -> None:
    """Test EmailConfigService initialization with encryptor (covers lines 58-59)."""
    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)

    assert service._session is mock_session
    assert service._encryptor is mock_encryptor


def test_email_config_service_init_without_encryptor(
    mock_session: MagicMock,
) -> None:
    """Test EmailConfigService initialization without encryptor (covers lines 58-59)."""
    service = EmailConfigService(session=mock_session, encryptor=None)

    assert service._session is mock_session
    assert service._encryptor is None


def test_get_config_no_config(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
) -> None:
    """Test get_config returns None when no config exists (covers line 76)."""
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is None


def test_get_config_with_decrypt_false(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config returns config without decryption when decrypt=False (covers line 77)."""
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=False)

    assert result is email_config
    mock_encryptor.decrypt.assert_not_called()
    mock_encryptor.decrypt_dict.assert_not_called()


def test_get_config_without_encryptor(
    mock_session: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config returns config without decryption when no encryptor (covers line 77)."""
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=None)
    result = service.get_config(decrypt=True)

    assert result is email_config


def test_get_config_decrypts_password(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config decrypts password when present (covers lines 75-85)."""
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    assert result.smtp_password == "decrypted_password"
    mock_session.expunge.assert_called_once_with(email_config)
    mock_encryptor.decrypt.assert_called_once_with("encrypted_password")


def test_get_config_decrypts_gmail_token(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config decrypts Gmail token when present (covers lines 75-90)."""
    email_config.smtp_password = None  # No password to decrypt
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    assert result.gmail_token == {"access_token": "token", "email": "test@gmail.com"}
    mock_session.expunge.assert_called_once_with(email_config)
    mock_encryptor.decrypt_dict.assert_called_once_with("encrypted_token")


def test_get_config_decrypts_both_password_and_token(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config decrypts both password and token when both present (covers lines 75-92)."""
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    assert result.smtp_password == "decrypted_password"
    assert result.gmail_token == {"access_token": "token", "email": "test@gmail.com"}
    mock_encryptor.decrypt.assert_called_once_with("encrypted_password")
    mock_encryptor.decrypt_dict.assert_called_once_with("encrypted_token")


def test_get_config_skips_gmail_token_when_not_string(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config skips Gmail token decryption when token is not a string (covers line 89)."""
    email_config.gmail_token = {"already": "decrypted"}  # Already a dict
    email_config.smtp_password = None
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    assert result.gmail_token == {"already": "decrypted"}
    mock_encryptor.decrypt_dict.assert_not_called()


def test_get_config_skips_password_when_none(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config skips password decryption when password is None (covers line 84)."""
    email_config.smtp_password = None
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    mock_encryptor.decrypt.assert_not_called()


def test_get_config_skips_token_when_none(
    mock_session: MagicMock,
    mock_encryptor: MagicMock,
    email_config: EmailServerConfig,
) -> None:
    """Test get_config skips token decryption when token is None (covers line 89)."""
    email_config.gmail_token = None
    mock_result = MagicMock()
    mock_result.first.return_value = email_config
    mock_session.exec.return_value = mock_result

    service = EmailConfigService(session=mock_session, encryptor=mock_encryptor)
    result = service.get_config(decrypt=True)

    assert result is not None
    mock_encryptor.decrypt_dict.assert_not_called()

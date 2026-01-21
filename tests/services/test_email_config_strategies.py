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

"""Tests for email configuration strategies."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.config import EmailServerConfig, EmailServerType
from bookcard.services.email_config_strategies import (
    GmailConfigStrategy,
    SMTPConfigStrategy,
)
from bookcard.services.email_config_update import EmailServerConfigUpdate

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> EmailServerConfig:
    """Return a fresh EmailServerConfig."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="old.smtp.com",
        smtp_port=25,
        smtp_username="olduser",
        smtp_password="oldpassword",
        smtp_use_tls=False,
        smtp_use_ssl=False,
        smtp_from_email="old@example.com",
        smtp_from_name="Old Sender",
        gmail_token="old_token",
    )


@pytest.fixture
def encryptor() -> MagicMock:
    """Return a mock DataEncryptor."""
    mock = MagicMock(spec=["encrypt", "decrypt", "encrypt_dict", "decrypt_dict"])
    mock.encrypt.return_value = "encrypted_value"
    mock.encrypt_dict.return_value = "encrypted_dict_value"
    return mock


@pytest.fixture
def smtp_strategy() -> SMTPConfigStrategy:
    """Return an SMTP strategy instance."""
    return SMTPConfigStrategy()


@pytest.fixture
def gmail_strategy() -> GmailConfigStrategy:
    """Return a Gmail strategy instance."""
    return GmailConfigStrategy()


# ---------------------------------------------------------------------------
# SMTPConfigStrategy tests
# ---------------------------------------------------------------------------


class TestSMTPConfigStrategy:
    """Tests for SMTPConfigStrategy.apply."""

    def test_apply_connection_fields(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply sets host and port."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_host="new.smtp.com",
            smtp_port=587,
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_host == "new.smtp.com"
        assert config.smtp_port == 587

    def test_apply_username_set(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply sets username when provided."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_username="newuser",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_username == "newuser"

    def test_apply_username_cleared(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply clears username when empty string provided."""
        config.smtp_from_email = "sender@example.com"  # Required fallback
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_username="",  # Empty string clears
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_username is None

    def test_apply_password_with_encryptor(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
        encryptor: MagicMock,
    ) -> None:
        """Apply encrypts password when encryptor provided."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_password="secret123",
            smtp_username="user",
        )

        smtp_strategy.apply(config, encryptor, update)

        assert config.smtp_password == "encrypted_value"
        encryptor.encrypt.assert_called_once_with("secret123")

    def test_apply_password_without_encryptor(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply stores password as-is when no encryptor."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_password="plaintext",
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_password == "plaintext"

    def test_apply_password_cleared(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply clears password when empty string provided."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_password="",  # Empty string clears
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_password is None

    def test_apply_password_none_no_change(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply does not change password when None provided."""
        original_password = config.smtp_password
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_password=None,
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_password == original_password

    def test_apply_security_flags(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply sets TLS and SSL flags."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_use_tls=True,
            smtp_use_ssl=False,
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_use_tls is True
        assert config.smtp_use_ssl is False

    def test_apply_sender_fields(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply sets from email and name."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_from_email="noreply@example.com",
            smtp_from_name="System",
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_from_email == "noreply@example.com"
        assert config.smtp_from_name == "System"

    def test_apply_clears_gmail_token(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply clears Gmail token (SMTP doesn't use it)."""
        config.gmail_token = "some_token"
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_username="user",
        )

        smtp_strategy.apply(config, None, update)

        assert config.gmail_token is None

    def test_apply_requires_from_email_when_no_username(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply raises when no username and no from email."""
        config.smtp_username = None
        config.smtp_from_email = None
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
        )

        with pytest.raises(ValueError, match="smtp_from_email_required"):
            smtp_strategy.apply(config, None, update)

    def test_apply_allows_no_username_with_from_email(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply succeeds with no username if from email is set."""
        config.smtp_username = None
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_from_email="sender@example.com",
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_from_email == "sender@example.com"

    def test_apply_none_values_no_change(
        self,
        smtp_strategy: SMTPConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply does not change fields when None provided."""
        original_host = config.smtp_host
        original_port = config.smtp_port
        original_tls = config.smtp_use_tls
        original_ssl = config.smtp_use_ssl
        original_from_email = config.smtp_from_email
        original_from_name = config.smtp_from_name

        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_username="user",
            smtp_host=None,
            smtp_port=None,
            smtp_use_tls=None,
            smtp_use_ssl=None,
            smtp_from_email=None,
            smtp_from_name=None,
        )

        smtp_strategy.apply(config, None, update)

        assert config.smtp_host == original_host
        assert config.smtp_port == original_port
        assert config.smtp_use_tls == original_tls
        assert config.smtp_use_ssl == original_ssl
        assert config.smtp_from_email == original_from_email
        assert config.smtp_from_name == original_from_name


# ---------------------------------------------------------------------------
# GmailConfigStrategy tests
# ---------------------------------------------------------------------------


class TestGmailConfigStrategy:
    """Tests for GmailConfigStrategy.apply."""

    def test_apply_gmail_token_with_encryptor(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
        encryptor: MagicMock,
    ) -> None:
        """Apply encrypts Gmail token when encryptor provided."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token={"access_token": "abc123"},
        )

        gmail_strategy.apply(config, encryptor, update)

        assert config.gmail_token == "encrypted_dict_value"
        encryptor.encrypt_dict.assert_called_once_with({"access_token": "abc123"})

    def test_apply_gmail_token_without_encryptor(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply stores Gmail token as-is when no encryptor."""
        token = {"access_token": "abc123"}
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token=token,
        )

        gmail_strategy.apply(config, None, update)

        assert config.gmail_token == token

    def test_apply_gmail_token_cleared(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply clears Gmail token when None provided."""
        config.gmail_token = "existing_token"
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token=None,
        )

        gmail_strategy.apply(config, None, update)

        assert config.gmail_token is None

    def test_apply_clears_smtp_password(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply clears SMTP password (Gmail doesn't use it)."""
        config.smtp_password = "some_password"
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token={"access_token": "abc123"},
        )

        gmail_strategy.apply(config, None, update)

        assert config.smtp_password is None

    def test_apply_optional_smtp_fields(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
    ) -> None:
        """Apply sets optional SMTP override fields for Gmail."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token={"access_token": "abc123"},
            smtp_host="smtp.gmail.com",
            smtp_port=465,
            smtp_username="user@gmail.com",
            smtp_use_tls=True,
            smtp_use_ssl=False,
            smtp_from_email="noreply@gmail.com",
            smtp_from_name="Gmail Sender",
        )

        gmail_strategy.apply(config, None, update)

        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 465
        assert config.smtp_username == "user@gmail.com"
        assert config.smtp_use_tls is True
        assert config.smtp_use_ssl is False
        assert config.smtp_from_email == "noreply@gmail.com"
        assert config.smtp_from_name == "Gmail Sender"

    @pytest.mark.parametrize(
        "field",
        [
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_use_tls",
            "smtp_use_ssl",
            "smtp_from_email",
            "smtp_from_name",
        ],
    )
    def test_apply_none_smtp_fields_no_change(
        self,
        gmail_strategy: GmailConfigStrategy,
        config: EmailServerConfig,
        field: str,
    ) -> None:
        """Apply does not change SMTP fields when None provided."""
        original_value = getattr(config, field)
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token={"access_token": "abc123"},
        )

        gmail_strategy.apply(config, None, update)

        assert getattr(config, field) == original_value

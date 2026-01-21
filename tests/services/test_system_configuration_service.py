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

"""Tests for system configuration service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.config import (
    EmailServerConfig,
    EmailServerType,
    OpenLibraryDumpConfig,
)
from bookcard.services.email_config_update import EmailServerConfigUpdate
from bookcard.services.system_configuration_service import SystemConfigurationService
from tests.conftest import DummySession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session() -> DummySession:
    """Return a fresh DummySession."""
    return DummySession()


@pytest.fixture
def encryptor() -> MagicMock:
    """Return a mock DataEncryptor."""
    mock = MagicMock(spec=["encrypt", "decrypt", "encrypt_dict", "decrypt_dict"])
    mock.encrypt.return_value = "encrypted_password"
    mock.decrypt.return_value = "decrypted_password"
    mock.encrypt_dict.return_value = "encrypted_token"
    mock.decrypt_dict.return_value = {"access_token": "decrypted"}
    return mock


@pytest.fixture
def service(session: DummySession) -> SystemConfigurationService:
    """Return a SystemConfigurationService without encryptor."""
    return SystemConfigurationService(session=session)  # type: ignore[arg-type]


@pytest.fixture
def service_with_encryptor(
    session: DummySession,
    encryptor: MagicMock,
) -> SystemConfigurationService:
    """Return a SystemConfigurationService with encryptor."""
    return SystemConfigurationService(session=session, encryptor=encryptor)  # type: ignore[arg-type]


@pytest.fixture
def smtp_config() -> EmailServerConfig:
    """Return a sample SMTP email config."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="encrypted_pw",
        smtp_use_tls=True,
        smtp_use_ssl=False,
        smtp_from_email="noreply@example.com",
        enabled=True,
    )


@pytest.fixture
def gmail_config() -> EmailServerConfig:
    """Return a sample Gmail email config."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.GMAIL,
        gmail_token="encrypted_token_json",
        enabled=True,
    )


@pytest.fixture
def openlibrary_config() -> OpenLibraryDumpConfig:
    """Return a sample OpenLibrary dump config."""
    return OpenLibraryDumpConfig(
        id=1,
        authors_url="https://example.com/authors.txt.gz",
        works_url="https://example.com/works.txt.gz",
        editions_url="https://example.com/editions.txt.gz",
    )


# ---------------------------------------------------------------------------
# get_email_server_config tests
# ---------------------------------------------------------------------------


class TestGetEmailServerConfig:
    """Tests for SystemConfigurationService.get_email_server_config."""

    def test_get_email_server_config_none(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Get returns None when no config exists."""
        session.add_exec_result([None])

        result = service.get_email_server_config()

        assert result is None

    def test_get_email_server_config_no_decrypt(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        smtp_config: EmailServerConfig,
    ) -> None:
        """Get returns config without decryption by default."""
        session.add_exec_result([smtp_config])

        result = service.get_email_server_config()

        assert result is smtp_config
        assert result.smtp_password == "encrypted_pw"  # Not decrypted

    def test_get_email_server_config_decrypt_no_encryptor(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        smtp_config: EmailServerConfig,
    ) -> None:
        """Get returns config as-is when decrypt=True but no encryptor."""
        session.add_exec_result([smtp_config])

        result = service.get_email_server_config(decrypt=True)

        assert result is smtp_config
        assert result.smtp_password == "encrypted_pw"  # Can't decrypt

    def test_get_email_server_config_decrypt_smtp_password(
        self,
        service_with_encryptor: SystemConfigurationService,
        session: DummySession,
        encryptor: MagicMock,
        smtp_config: EmailServerConfig,
    ) -> None:
        """Get decrypts SMTP password when requested."""
        session.add_exec_result([smtp_config])

        result = service_with_encryptor.get_email_server_config(decrypt=True)

        assert result is not None
        assert result.smtp_password == "decrypted_password"
        encryptor.decrypt.assert_called_once_with("encrypted_pw")
        assert smtp_config in session.expunged

    def test_get_email_server_config_decrypt_gmail_token(
        self,
        service_with_encryptor: SystemConfigurationService,
        session: DummySession,
        encryptor: MagicMock,
        gmail_config: EmailServerConfig,
    ) -> None:
        """Get decrypts Gmail token when requested."""
        session.add_exec_result([gmail_config])

        result = service_with_encryptor.get_email_server_config(decrypt=True)

        assert result is not None
        assert result.gmail_token == {"access_token": "decrypted"}
        encryptor.decrypt_dict.assert_called_once_with("encrypted_token_json")

    def test_get_email_server_config_decrypt_no_secrets(
        self,
        service_with_encryptor: SystemConfigurationService,
        session: DummySession,
        encryptor: MagicMock,
    ) -> None:
        """Get does not call decrypt when no secrets are set."""
        config = EmailServerConfig(
            id=1,
            server_type=EmailServerType.SMTP,
            smtp_host="smtp.example.com",
            smtp_password=None,
            gmail_token=None,
        )
        session.add_exec_result([config])

        result = service_with_encryptor.get_email_server_config(decrypt=True)

        assert result is not None
        encryptor.decrypt.assert_not_called()
        encryptor.decrypt_dict.assert_not_called()


# ---------------------------------------------------------------------------
# upsert_email_server_config tests
# ---------------------------------------------------------------------------


class TestUpsertEmailServerConfig:
    """Tests for SystemConfigurationService.upsert_email_server_config."""

    def test_upsert_creates_new_smtp_config(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert creates new config when none exists."""
        session.add_exec_result([None])  # No existing config
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user@example.com",
            smtp_from_email="noreply@example.com",
        )

        result = service.upsert_email_server_config(update)

        assert result.server_type == EmailServerType.SMTP
        assert result.smtp_host == "smtp.example.com"
        assert result.smtp_port == 587
        assert result in session.added
        assert session.flush_count == 1

    def test_upsert_updates_existing_config(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        smtp_config: EmailServerConfig,
    ) -> None:
        """Upsert updates existing config."""
        session.add_exec_result([smtp_config])
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_host="new.smtp.example.com",
            smtp_from_email="sender@example.com",
        )

        result = service.upsert_email_server_config(update)

        assert result.smtp_host == "new.smtp.example.com"
        assert result.smtp_from_email == "sender@example.com"
        # Existing values preserved
        assert result.smtp_port == 587

    def test_upsert_smtp_with_encryptor(
        self,
        service_with_encryptor: SystemConfigurationService,
        session: DummySession,
        encryptor: MagicMock,
    ) -> None:
        """Upsert encrypts SMTP password when encryptor provided."""
        session.add_exec_result([None])
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_host="smtp.example.com",
            smtp_password="secret123",
            smtp_username="user@example.com",
        )

        result = service_with_encryptor.upsert_email_server_config(update)

        assert result.smtp_password == "encrypted_password"
        encryptor.encrypt.assert_called_once_with("secret123")

    def test_upsert_gmail_config(
        self,
        service_with_encryptor: SystemConfigurationService,
        session: DummySession,
        encryptor: MagicMock,
    ) -> None:
        """Upsert creates Gmail config with encrypted token."""
        session.add_exec_result([None])
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.GMAIL,
            gmail_token={"access_token": "abc123"},
        )

        result = service_with_encryptor.upsert_email_server_config(update)

        assert result.server_type == EmailServerType.GMAIL
        assert result.gmail_token == "encrypted_token"
        encryptor.encrypt_dict.assert_called_once()

    def test_upsert_sets_enabled(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert sets enabled flag."""
        session.add_exec_result([None])
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            enabled=True,
            smtp_username="user@example.com",
        )

        result = service.upsert_email_server_config(update)

        assert result.enabled is True

    def test_upsert_sets_max_email_size(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert sets max email size."""
        session.add_exec_result([None])
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            max_email_size_mb=25,
            smtp_username="user@example.com",
        )

        result = service.upsert_email_server_config(update)

        assert result.max_email_size_mb == 25

    def test_upsert_rejects_tls_and_ssl(
        self,
        service: SystemConfigurationService,
    ) -> None:
        """Upsert rejects config with both TLS and SSL enabled."""
        update = EmailServerConfigUpdate(
            server_type=EmailServerType.SMTP,
            smtp_use_tls=True,
            smtp_use_ssl=True,
            smtp_username="user@example.com",
        )

        with pytest.raises(ValueError, match="invalid_smtp_encryption"):
            service.upsert_email_server_config(update)


# ---------------------------------------------------------------------------
# get_openlibrary_dump_config tests
# ---------------------------------------------------------------------------


class TestGetOpenLibraryDumpConfig:
    """Tests for SystemConfigurationService.get_openlibrary_dump_config."""

    def test_get_openlibrary_dump_config_none(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Get returns None when no config exists."""
        session.add_exec_result([None])

        result = service.get_openlibrary_dump_config()

        assert result is None

    def test_get_openlibrary_dump_config_exists(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        openlibrary_config: OpenLibraryDumpConfig,
    ) -> None:
        """Get returns config when it exists."""
        session.add_exec_result([openlibrary_config])

        result = service.get_openlibrary_dump_config()

        assert result is openlibrary_config


# ---------------------------------------------------------------------------
# upsert_openlibrary_dump_config tests
# ---------------------------------------------------------------------------


class TestUpsertOpenLibraryDumpConfig:
    """Tests for SystemConfigurationService.upsert_openlibrary_dump_config."""

    def test_upsert_creates_new_config(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert creates new config when none exists."""
        session.add_exec_result([None])

        result = service.upsert_openlibrary_dump_config(
            authors_url="https://example.com/authors.txt.gz",
            works_url="https://example.com/works.txt.gz",
        )

        assert result.authors_url == "https://example.com/authors.txt.gz"
        assert result.works_url == "https://example.com/works.txt.gz"
        assert result in session.added
        assert session.flush_count == 1

    def test_upsert_updates_existing_config(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        openlibrary_config: OpenLibraryDumpConfig,
    ) -> None:
        """Upsert updates existing config."""
        session.add_exec_result([openlibrary_config])

        result = service.upsert_openlibrary_dump_config(
            authors_url="https://new.example.com/authors.txt.gz",
        )

        assert result.authors_url == "https://new.example.com/authors.txt.gz"
        # Existing values preserved
        assert result.works_url == "https://example.com/works.txt.gz"

    def test_upsert_sets_all_fields(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert correctly sets all fields."""
        session.add_exec_result([None])

        result = service.upsert_openlibrary_dump_config(
            authors_url="https://example.com/a.gz",
            works_url="https://example.com/w.gz",
            editions_url="https://example.com/e.gz",
            default_process_authors=True,
            default_process_works=False,
            default_process_editions=True,
            staleness_threshold_days=7,
            enable_auto_download=True,
            enable_auto_process=False,
            auto_check_interval_hours=24,
        )

        assert result.authors_url == "https://example.com/a.gz"
        assert result.works_url == "https://example.com/w.gz"
        assert result.editions_url == "https://example.com/e.gz"
        assert result.default_process_authors is True
        assert result.default_process_works is False
        assert result.default_process_editions is True
        assert result.staleness_threshold_days == 7
        assert result.enable_auto_download is True
        assert result.enable_auto_process is False
        assert result.auto_check_interval_hours == 24

    def test_upsert_ignores_none_values(
        self,
        service: SystemConfigurationService,
        session: DummySession,
        openlibrary_config: OpenLibraryDumpConfig,
    ) -> None:
        """Upsert does not overwrite fields with None values."""
        original_url = openlibrary_config.authors_url
        session.add_exec_result([openlibrary_config])

        result = service.upsert_openlibrary_dump_config(authors_url=None)

        assert result.authors_url == original_url

    def test_upsert_sets_updated_at(
        self,
        service: SystemConfigurationService,
        session: DummySession,
    ) -> None:
        """Upsert sets updated_at timestamp."""
        session.add_exec_result([None])

        result = service.upsert_openlibrary_dump_config()

        assert result.updated_at is not None

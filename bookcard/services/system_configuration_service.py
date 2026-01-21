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

"""System configuration service.

This module manages singleton configuration records (email server config and
OpenLibrary dump config) at the service layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import select

from bookcard.models.config import (
    EmailServerConfig,
    EmailServerType,
    OpenLibraryDumpConfig,
)
from bookcard.services.email_config_strategies import (
    GmailConfigStrategy,
    SMTPConfigStrategy,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.services.email_config_update import EmailServerConfigUpdate
    from bookcard.services.security import DataEncryptor


class SystemConfigurationService:
    """Handle system-wide (singleton) configuration records."""

    def __init__(
        self,
        session: Session,
        encryptor: DataEncryptor | None = None,
    ) -> None:
        self._session = session
        self._encryptor = encryptor
        self._smtp_strategy = SMTPConfigStrategy()
        self._gmail_strategy = GmailConfigStrategy()

    def get_email_server_config(
        self, decrypt: bool = False
    ) -> EmailServerConfig | None:
        """Return the singleton email server configuration.

        Parameters
        ----------
        decrypt : bool, optional
            Whether to decrypt secrets into the returned object. When True, the returned
            object is detached from the session to avoid persisting decrypted values.

        Returns
        -------
        EmailServerConfig | None
            The persisted configuration if present, else ``None``.
        """
        stmt = select(EmailServerConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None or not decrypt or self._encryptor is None:
            return config

        self._session.expunge(config)

        if config.smtp_password:
            config.smtp_password = self._encryptor.decrypt(config.smtp_password)

        if config.gmail_token and isinstance(config.gmail_token, str):
            config.gmail_token = self._encryptor.decrypt_dict(config.gmail_token)

        return config

    def upsert_email_server_config(
        self,
        update: EmailServerConfigUpdate,
    ) -> EmailServerConfig:
        """Create or update the singleton email server configuration.

        Parameters
        ----------
        update : EmailServerConfigUpdate
            Update payload. Only non-``None`` values are applied.

        Returns
        -------
        EmailServerConfig
            Persisted configuration instance.

        Raises
        ------
        ValueError
            If both TLS and SSL are enabled.
        """
        if update.smtp_use_tls is True and update.smtp_use_ssl is True:
            msg = "invalid_smtp_encryption"
            raise ValueError(msg)

        config = self.get_email_server_config()
        if config is None:
            config = EmailServerConfig()
            self._session.add(config)

        config.server_type = update.server_type
        if update.max_email_size_mb is not None:
            config.max_email_size_mb = update.max_email_size_mb
        if update.enabled is not None:
            config.enabled = update.enabled

        if update.server_type == EmailServerType.SMTP:
            self._smtp_strategy.apply(config, self._encryptor, update)
        else:
            self._gmail_strategy.apply(config, self._encryptor, update)

        config.updated_at = datetime.now(UTC)
        self._session.flush()
        return config

    def get_openlibrary_dump_config(
        self,
    ) -> OpenLibraryDumpConfig | None:
        """Return the singleton OpenLibrary dump configuration."""
        stmt = select(OpenLibraryDumpConfig).limit(1)
        return self._session.exec(stmt).first()

    def upsert_openlibrary_dump_config(
        self,
        *,
        authors_url: str | None = None,
        works_url: str | None = None,
        editions_url: str | None = None,
        default_process_authors: bool | None = None,
        default_process_works: bool | None = None,
        default_process_editions: bool | None = None,
        staleness_threshold_days: int | None = None,
        enable_auto_download: bool | None = None,
        enable_auto_process: bool | None = None,
        auto_check_interval_hours: int | None = None,
    ) -> OpenLibraryDumpConfig:
        """Create or update the singleton OpenLibrary dump configuration.

        Only non-``None`` arguments are applied.
        """
        config = self.get_openlibrary_dump_config()
        if config is None:
            config = OpenLibraryDumpConfig()
            self._session.add(config)

        field_values: dict[str, object | None] = {
            "authors_url": authors_url,
            "works_url": works_url,
            "editions_url": editions_url,
            "default_process_authors": default_process_authors,
            "default_process_works": default_process_works,
            "default_process_editions": default_process_editions,
            "staleness_threshold_days": staleness_threshold_days,
            "enable_auto_download": enable_auto_download,
            "enable_auto_process": enable_auto_process,
            "auto_check_interval_hours": auto_check_interval_hours,
        }
        for field, value in field_values.items():
            if value is not None:
                setattr(config, field, value)

        config.updated_at = datetime.now(UTC)
        self._session.flush()
        return config

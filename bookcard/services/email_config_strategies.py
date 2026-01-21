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

"""Email server configuration strategies.

This module implements the strategy pattern for applying server-type-specific
updates to the singleton `EmailServerConfig`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from bookcard.models.config import EmailServerConfig
    from bookcard.services.email_config_update import EmailServerConfigUpdate
    from bookcard.services.security import DataEncryptor


class EmailConfigStrategy(Protocol):
    """Apply a server-type-specific email configuration update."""

    def apply(
        self,
        config: EmailServerConfig,
        encryptor: DataEncryptor | None,
        update: EmailServerConfigUpdate,
    ) -> None:
        """Apply an update to an `EmailServerConfig`.

        Parameters
        ----------
        config : EmailServerConfig
            The persisted config object to mutate.
        encryptor : DataEncryptor | None
            Encryptor for secrets, if configured.
        update : EmailServerConfigUpdate
            The update to apply.
        """


class SMTPConfigStrategy:
    """Apply SMTP-specific fields."""

    def apply(
        self,
        config: EmailServerConfig,
        encryptor: DataEncryptor | None,
        update: EmailServerConfigUpdate,
    ) -> None:
        """Apply SMTP fields and validate required sender details.

        Parameters
        ----------
        config : EmailServerConfig
            Persisted config to update.
        encryptor : DataEncryptor | None
            Encryptor used to store secrets.
        update : EmailServerConfigUpdate
            Update payload.

        Raises
        ------
        ValueError
            If SMTP authentication is disabled and no from email is configured.
        """
        self._apply_connection(config, update)
        self._apply_credentials(config, encryptor, update)
        self._apply_security_flags(config, update)
        self._apply_sender(config, update)
        self._validate_sender(config)
        self._clear_gmail_fields(config)

    def _apply_connection(
        self, config: EmailServerConfig, update: EmailServerConfigUpdate
    ) -> None:
        if update.smtp_host is not None:
            config.smtp_host = update.smtp_host
        if update.smtp_port is not None:
            config.smtp_port = update.smtp_port

    def _apply_credentials(
        self,
        config: EmailServerConfig,
        encryptor: DataEncryptor | None,
        update: EmailServerConfigUpdate,
    ) -> None:
        if update.smtp_username is not None:
            config.smtp_username = (
                update.smtp_username if update.smtp_username else None
            )

        if update.smtp_password is None:
            return

        if len(update.smtp_password) == 0:
            config.smtp_password = None
            return

        if encryptor is not None:
            config.smtp_password = encryptor.encrypt(update.smtp_password)
            return

        config.smtp_password = update.smtp_password

    def _apply_security_flags(
        self, config: EmailServerConfig, update: EmailServerConfigUpdate
    ) -> None:
        if update.smtp_use_tls is not None:
            config.smtp_use_tls = update.smtp_use_tls
        if update.smtp_use_ssl is not None:
            config.smtp_use_ssl = update.smtp_use_ssl

    def _apply_sender(
        self, config: EmailServerConfig, update: EmailServerConfigUpdate
    ) -> None:
        if update.smtp_from_email is not None:
            config.smtp_from_email = update.smtp_from_email
        if update.smtp_from_name is not None:
            config.smtp_from_name = update.smtp_from_name

    def _validate_sender(self, config: EmailServerConfig) -> None:
        if config.smtp_username or config.smtp_from_email:
            return
        msg = "smtp_from_email_required"
        raise ValueError(msg)

    def _clear_gmail_fields(self, config: EmailServerConfig) -> None:
        config.gmail_token = None


class GmailConfigStrategy:
    """Apply Gmail-specific fields."""

    def apply(
        self,
        config: EmailServerConfig,
        encryptor: DataEncryptor | None,
        update: EmailServerConfigUpdate,
    ) -> None:
        """Apply Gmail token and optional SMTP override fields.

        Parameters
        ----------
        config : EmailServerConfig
            Persisted config to update.
        encryptor : DataEncryptor | None
            Encryptor used to store secrets.
        update : EmailServerConfigUpdate
            Update payload.
        """
        self._apply_gmail_token(config, encryptor, update)
        self._clear_smtp_password(config)
        self._apply_optional_smtp_fields(config, update)

    def _apply_gmail_token(
        self,
        config: EmailServerConfig,
        encryptor: DataEncryptor | None,
        update: EmailServerConfigUpdate,
    ) -> None:
        if update.gmail_token is None:
            config.gmail_token = None
            return

        if encryptor is not None:
            config.gmail_token = encryptor.encrypt_dict(update.gmail_token)
            return

        config.gmail_token = update.gmail_token

    def _clear_smtp_password(self, config: EmailServerConfig) -> None:
        config.smtp_password = None

    def _apply_optional_smtp_fields(
        self, config: EmailServerConfig, update: EmailServerConfigUpdate
    ) -> None:
        if update.smtp_host is not None:
            config.smtp_host = update.smtp_host
        if update.smtp_port is not None:
            config.smtp_port = update.smtp_port
        if update.smtp_username is not None:
            config.smtp_username = update.smtp_username
        if update.smtp_use_tls is not None:
            config.smtp_use_tls = update.smtp_use_tls
        if update.smtp_use_ssl is not None:
            config.smtp_use_ssl = update.smtp_use_ssl
        if update.smtp_from_email is not None:
            config.smtp_from_email = update.smtp_from_email
        if update.smtp_from_name is not None:
            config.smtp_from_name = update.smtp_from_name

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

"""Email configuration service for reading email server configuration.

Separate from AuthService to provide a simpler interface for consumers
(regular users, services) that only need to read email config.
AuthService retains responsibility for writing/updating config (admin operations).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import select

from bookcard.models.config import EmailServerConfig

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.services.security import DataEncryptor


class EmailConfigService:
    """Service for reading email server configuration.

    Provides a simple interface for consumers (regular users, services)
    to read email server configuration without requiring full AuthService
    dependencies.

    Parameters
    ----------
    session : Session
        Database session.
    encryptor : DataEncryptor | None
        Optional encryptor for decrypting stored credentials.
        If None, returns config without decryption.
    """

    def __init__(
        self,
        session: Session,
        encryptor: DataEncryptor | None = None,
    ) -> None:
        self._session = session
        self._encryptor = encryptor

    def get_config(self, decrypt: bool = True) -> EmailServerConfig | None:
        """Get the singleton email server configuration.

        Parameters
        ----------
        decrypt : bool, optional
            Whether to decrypt passwords and tokens. Defaults to True.
            Set to False to get raw encrypted values.

        Returns
        -------
        EmailServerConfig | None
            The configuration if it exists, otherwise None.
        """
        stmt = select(EmailServerConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None or not decrypt or self._encryptor is None:
            return config

        # Detach from session to avoid modifying the database object
        self._session.expunge(config)

        # Decrypt password if it exists
        if config.smtp_password:
            config.smtp_password = self._encryptor.decrypt(config.smtp_password)

        # Decrypt Gmail token if it exists
        # gmail_token is stored as an encrypted string in the database
        if config.gmail_token and isinstance(config.gmail_token, str):
            config.gmail_token = self._encryptor.decrypt_dict(config.gmail_token)

        return config

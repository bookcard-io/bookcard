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

"""Default implementations for email send dependencies.

Concrete implementations of protocol dependencies following
Dependency Inversion Principle.
"""

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.email_config_service import EmailConfigService
from bookcard.services.email_service import EmailService
from bookcard.services.security import DataEncryptor
from bookcard.services.tasks.email_send.exceptions import (
    EmailServerNotConfiguredError,
    LibraryNotConfiguredError,
)


class DefaultLibraryProvider:
    """Default implementation of library provider."""

    def get_active_library(self, session: Session) -> Library:  # type: ignore[type-arg]
        """Get active library configuration.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        Library
            Active library configuration.

        Raises
        ------
        LibraryNotConfiguredError
            If no active library is configured.
        """
        library_repo = LibraryRepository(session)
        library_service = LibraryService(session, library_repo)
        try:
            return library_service.require_active_library()
        except ValueError as e:
            raise LibraryNotConfiguredError from e


class DefaultEmailServiceFactory:
    """Default implementation of email service factory."""

    def __init__(self, encryption_key: str) -> None:
        """Initialize factory.

        Parameters
        ----------
        encryption_key : str
            Encryption key for decrypting email config.
        """
        self.encryption_key = encryption_key

    def create(
        self,
        session: Session,
        encryption_key: str,  # type: ignore[type-arg]
    ) -> EmailService:
        """Create email service instance.

        Parameters
        ----------
        session : Session
            Database session.
        encryption_key : str
            Encryption key for decrypting email config.

        Returns
        -------
        EmailService
            Configured email service.

        Raises
        ------
        EmailServerNotConfiguredError
            If email server is not configured or disabled.
        """
        encryptor = DataEncryptor(encryption_key)
        email_config_service = EmailConfigService(session, encryptor=encryptor)
        email_config = email_config_service.get_config(decrypt=True)

        if email_config is None or not email_config.enabled:
            raise EmailServerNotConfiguredError

        return EmailService(email_config)


class DefaultEmailSendBookServiceFactory:
    """Default implementation of book service factory for email send task."""

    def create(
        self,
        library: Library,
        session: Session,  # type: ignore[type-arg]
    ) -> BookService:
        """Create book service instance.

        Parameters
        ----------
        library : Library
            Library configuration.
        session : Session
            Database session.

        Returns
        -------
        BookService
            Book service instance.
        """
        return BookService(library, session=session)

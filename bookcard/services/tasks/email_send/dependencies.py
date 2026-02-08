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

"""Dependency injection container for email send task.

Implements Dependency Inversion Principle by providing all dependencies
through a single container, eliminating Service Locator anti-pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.config import Library
    from bookcard.services.book_service import BookService
    from bookcard.services.email_service import EmailService
    from bookcard.services.tasks.email_send.domain import (
        SendBookRequest,
        SendPreparation,
    )
    from bookcard.services.tasks.email_send.preprocessing import PreprocessingContext


class LibraryProvider(Protocol):
    """Protocol for library provider.

    Follows Dependency Inversion Principle by depending on abstraction.
    """

    def get_active_library(
        self,
        session: Session,
        metadata: dict[str, Any] | None = None,
        user_id: int | None = None,
    ) -> Library:
        """Get target library configuration.

        Parameters
        ----------
        session : Session
            Database session.
        metadata : dict[str, Any] | None
            Task metadata that may contain ``library_id``.
        user_id : int | None
            User identifier for per-user fallback.

        Returns
        -------
        Library
            Library configuration.

        Raises
        ------
        LibraryNotConfiguredError
            If no library could be resolved.
        """
        ...


class EmailServiceFactory(Protocol):
    """Protocol for email service factory.

    Follows Dependency Inversion Principle by depending on abstraction.
    """

    def create(
        self,
        session: Session,
        encryption_key: str,
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
        ...


class EmailSendBookServiceFactory(Protocol):
    """Protocol for book service factory for email send task.

    Note: This is separate from pvr.importing.protocols.BookServiceFactory
    because it requires a session parameter and returns concrete BookService
    rather than BookServiceProtocol.

    Follows Dependency Inversion Principle by depending on abstraction.
    """

    def create(
        self,
        library: Library,
        session: Session,
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
        ...


class SendPreparationService(Protocol):
    """Protocol for send preparation service.

    Follows Dependency Inversion Principle by depending on abstraction.
    """

    def prepare(
        self,
        request: SendBookRequest,
        book_service: BookService,
        session: Session,
        user_id: int,
    ) -> SendPreparation:
        """Prepare book for sending.

        Parameters
        ----------
        request : SendBookRequest
            Send book request.
        book_service : BookService
            Book service instance.
        session : Session
            Database session.
        user_id : int
            User ID.

        Returns
        -------
        SendPreparation
            Prepared send data.

        Raises
        ------
        BookNotFoundError
            If book is not found.
        """
        ...


class PreprocessingPipelineProtocol(Protocol):
    """Protocol for preprocessing pipeline.

    Follows Dependency Inversion Principle by depending on abstraction.
    """

    def execute(self, context: PreprocessingContext) -> None:
        """Execute preprocessing pipeline.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.
        """
        ...


@dataclass(frozen=True)
class EmailSendDependencies:
    """Container for all email send task dependencies.

    Implements Dependency Inversion Principle by providing all dependencies
    through constructor injection, eliminating Service Locator pattern.
    """

    library_provider: LibraryProvider
    email_service_factory: EmailServiceFactory
    book_service_factory: EmailSendBookServiceFactory
    preparation_service: SendPreparationService
    preprocessing_pipeline: PreprocessingPipelineProtocol

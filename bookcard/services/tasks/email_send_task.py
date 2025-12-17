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

"""Email send task implementation.

Handles sending books via email in the background with progress tracking.
Refactored to follow SOLID principles, DRY, SRP, IoC, and SoC.
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.repositories import BookWithFullRelations
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.email_config_service import EmailConfigService
from bookcard.services.email_service import EmailService
from bookcard.services.email_utils import build_attachment_filename
from bookcard.services.security import DataEncryptor
from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import ProgressCallback, WorkerContext
from bookcard.services.tasks.exceptions import (
    BookNotFoundError,
    EmailServerNotConfiguredError,
    LibraryNotConfiguredError,
    TaskCancelledError,
)
from bookcard.services.tasks.utils import AuthorExtractor, BookFormatResolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailTarget:
    """Target for email delivery.

    Makes the semantics of None (default device) explicit.
    """

    address: str | None = None

    def __str__(self) -> str:
        """Return string representation.

        Returns
        -------
        str
            Email address or "default device" if None.
        """
        return self.address or "default device"


@dataclass(frozen=True)
class SendMetadata:
    """Metadata for completed email send.

    Follows Single Responsibility Principle by encapsulating completion metadata.
    """

    book_title: str
    attachment_filename: str


class EmailSendTask(BaseTask):
    """Task for sending a book via email.

    Handles email sending in the background with progress tracking.
    Refactored to follow SOLID principles.

    Attributes
    ----------
    _book_id : int
        Calibre book ID to send.
    _email_target : EmailTarget
        Email address to send to. If None, uses default device.
    _file_format : str | None
        Optional file format to send (e.g., 'EPUB', 'MOBI').
    _encryption_key : str
        Encryption key for decrypting email server configuration.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize email send task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing book_id, to_email, file_format, encryption_key.

        Raises
        ------
        ValueError
            If required metadata fields are missing or invalid.
        TypeError
            If metadata types are incorrect.
        """
        super().__init__(task_id, user_id, metadata)
        self._book_id = self._require_int("book_id", metadata)
        self._encryption_key = self._require_str("encryption_key", metadata)
        self._email_target = EmailTarget(metadata.get("to_email"))
        self._file_format = metadata.get("file_format")

    def _require_int(self, key: str, metadata: dict[str, Any]) -> int:
        """Require an integer value from metadata.

        Parameters
        ----------
        key : str
            Metadata key.
        metadata : dict[str, Any]
            Metadata dictionary.

        Returns
        -------
        int
            Integer value.

        Raises
        ------
        ValueError
            If key is missing.
        TypeError
            If value is not an integer.
        """
        value = metadata.get(key)
        if value is None:
            msg = f"{key} is required in task metadata"
            raise ValueError(msg)
        if not isinstance(value, int):
            msg = f"{key} must be an integer"
            raise TypeError(msg)
        return value

    def _require_str(self, key: str, metadata: dict[str, Any]) -> str:
        """Require a string value from metadata.

        Parameters
        ----------
        key : str
            Metadata key.
        metadata : dict[str, Any]
            Metadata dictionary.

        Returns
        -------
        str
            String value.

        Raises
        ------
        ValueError
            If key is missing or empty.
        TypeError
            If value is not a string.
        """
        value = metadata.get(key)
        if not value:
            msg = f"{key} is required in task metadata"
            raise ValueError(msg)
        if not isinstance(value, str):
            msg = f"{key} must be a string"
            raise TypeError(msg)
        return value

    def _check_cancellation(self) -> None:
        """Check if task is cancelled and raise exception if so.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def _update_progress_or_cancel(
        self,
        progress: float,
        update_progress: ProgressCallback,
    ) -> None:
        """Update progress and check for cancellation.

        Combines progress update and cancellation check to follow DRY.

        Parameters
        ----------
        progress : float
            Progress value (0.0 to 1.0).
        update_progress : ProgressCallback
            Progress update callback.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        update_progress(progress, None)
        self._check_cancellation()

    def _get_library(
        self,
        session: Session,  # type: ignore[type-arg]
    ) -> Library:  # type: ignore[name-defined]
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
        library = library_service.get_active_library()

        if library is None:
            raise LibraryNotConfiguredError

        return library

    def _get_email_service(
        self,
        session: Session,  # type: ignore[type-arg]
    ) -> EmailService:
        """Get configured email service.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        EmailService
            Configured email service.

        Raises
        ------
        EmailServerNotConfiguredError
            If email server is not configured or disabled.
        """
        encryptor = DataEncryptor(self._encryption_key)
        email_config_service = EmailConfigService(session, encryptor=encryptor)
        email_config = email_config_service.get_config(decrypt=True)

        if email_config is None or not email_config.enabled:
            raise EmailServerNotConfiguredError

        return EmailService(email_config)

    def _get_book_or_raise(self, book_service: BookService) -> BookWithFullRelations:  # type: ignore[type-arg]
        """Fetch book or raise if not found.

        Parameters
        ----------
        book_service : BookService
            Book service instance.

        Returns
        -------
        BookWithFullRelations
            Book with full relationships.

        Raises
        ------
        BookNotFoundError
            If book is not found.
        """
        book_with_rels = book_service.get_book_full(self._book_id)
        if book_with_rels is None:
            raise BookNotFoundError(self._book_id)
        return book_with_rels

    def _prepare_send_metadata(self, book_service: BookService) -> SendMetadata:
        """Prepare metadata for task completion.

        Parameters
        ----------
        book_service : BookService
            Book service instance.

        Returns
        -------
        SendMetadata
            Metadata for completed email send.

        Raises
        ------
        BookNotFoundError
            If book is not found.
        """
        book_with_rels = self._get_book_or_raise(book_service)

        book_title = book_with_rels.book.title or "Unknown Book"
        author_name = AuthorExtractor.get_primary_author_name(book_with_rels)
        format_to_send = BookFormatResolver.resolve_send_format(
            self._file_format, book_with_rels
        )

        attachment_filename = build_attachment_filename(
            author=author_name,
            title=book_title,
            extension=format_to_send.lower() if format_to_send else None,
        )

        return SendMetadata(
            book_title=book_title,
            attachment_filename=attachment_filename,
        )

    def _send_book(
        self,
        book_service: BookService,
        email_service: EmailService,
    ) -> None:
        """Send book and store completion metadata.

        Parameters
        ----------
        book_service : BookService
            Book service instance.
        email_service : EmailService
            Email service instance.
        """
        send_metadata = self._prepare_send_metadata(book_service)

        book_service.send_book(
            book_id=self._book_id,
            user_id=self.user_id,
            email_service=email_service,
            to_email=self._email_target.address,
            file_format=self._file_format,
        )

        self.set_metadata("book_title", send_metadata.book_title)
        self.set_metadata("attachment_filename", send_metadata.attachment_filename)

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute email send task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, task_service, update_progress.
            Can be a dictionary (for backward compatibility) or WorkerContext.
        """
        # Convert dict to WorkerContext for type safety
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        else:
            context = worker_context

        try:
            self._execute(context)
        except TaskCancelledError:
            logger.info("Task %s cancelled", self.task_id)
            # Don't re-raise - cancellation is expected
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

    def _execute(self, context: WorkerContext) -> None:
        """Core execution workflow.

        Parameters
        ----------
        context : WorkerContext
            Worker context.

        Raises
        ------
        TaskCancelledError
            If task is cancelled.
        LibraryNotConfiguredError
            If no active library is configured.
        EmailServerNotConfiguredError
            If email server is not configured.
        BookNotFoundError
            If book is not found.
        """
        self._check_cancellation()
        context.update_progress(0.1, None)

        library = self._get_library(context.session)
        context.update_progress(0.2, None)

        self._check_cancellation()
        email_service = self._get_email_service(context.session)
        context.update_progress(0.3, None)

        self._check_cancellation()
        book_service = BookService(library, session=context.session)
        context.update_progress(0.4, None)

        self._check_cancellation()
        self._send_book(book_service, email_service)
        context.update_progress(1.0, None)

        logger.info(
            "Task %s: Book %s sent successfully to %s",
            self.task_id,
            self._book_id,
            self._email_target,
        )

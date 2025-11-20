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
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_service import BookService
from fundamental.services.config_service import LibraryService
from fundamental.services.email_config_service import EmailConfigService
from fundamental.services.email_service import EmailService, EmailServiceError
from fundamental.services.email_utils import build_attachment_filename
from fundamental.services.security import DataEncryptor
from fundamental.services.tasks.base import BaseTask

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger(__name__)


def _raise_no_library_configured() -> None:
    """Raise error for missing library configuration."""
    msg = "No active library configured"
    raise ValueError(msg)


def _raise_email_server_not_configured() -> None:
    """Raise error for missing or disabled email server configuration."""
    msg = "email_server_not_configured_or_disabled"
    raise ValueError(msg)


class EmailSendTask(BaseTask):
    """Task for sending a book via email.

    Handles email sending in the background with progress tracking.

    Attributes
    ----------
    book_id : int
        Calibre book ID to send.
    to_email : str | None
        Email address to send to. If None, uses default device.
    file_format : str | None
        Optional file format to send (e.g., 'EPUB', 'MOBI').
    encryption_key : str
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
        """
        super().__init__(task_id, user_id, metadata)
        book_id = metadata.get("book_id")
        if book_id is None:
            msg = "book_id is required in task metadata"
            raise ValueError(msg)
        if not isinstance(book_id, int):
            msg = "book_id must be an integer"
            raise TypeError(msg)
        self.book_id: int = book_id
        self.to_email = metadata.get("to_email")
        self.file_format = metadata.get("file_format")
        encryption_key = metadata.get("encryption_key")
        if not encryption_key:
            msg = "encryption_key is required in task metadata"
            raise ValueError(msg)
        if not isinstance(encryption_key, str):
            msg = "encryption_key must be a string"
            raise TypeError(msg)
        self.encryption_key: str = encryption_key

    def _prepare_completion_metadata(
        self, book_service: BookService
    ) -> tuple[str, str]:
        """Prepare book title and attachment filename for completion metadata.

        Parameters
        ----------
        book_service : BookService
            Book service instance to fetch book data.

        Returns
        -------
        tuple[str, str]
            Tuple of (book_title, attachment_filename).

        Raises
        ------
        ValueError
            If book not found.
        """
        book_with_rels = book_service.get_book_full(self.book_id)
        if book_with_rels is None:
            msg = "book_not_found"
            raise ValueError(msg)

        book = book_with_rels.book
        book_title = book.title or "Unknown Book"
        # Accessing static method for author name extraction
        author_name = BookService._get_primary_author_name(  # noqa: SLF001
            book_with_rels
        )

        # Determine format that will be sent
        format_to_send = (
            self.file_format.upper()
            if self.file_format
            else (
                str(book_with_rels.formats[0].get("format", "")).upper()
                if book_with_rels.formats and book_with_rels.formats[0].get("format")
                else None
            )
        )

        # Build attachment filename
        attachment_filename = build_attachment_filename(
            author=author_name,
            title=book_title,
            extension=format_to_send.lower() if format_to_send else None,
        )

        return book_title, attachment_filename

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute email send task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Update progress: 0.1 - task started
            update_progress(0.1)

            # Get active library
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            library = library_service.get_active_library()

            if library is None:
                _raise_no_library_configured()
                return  # Never reached, but helps type checker

            # Update progress: 0.2 - library found
            update_progress(0.2)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Get email configuration
            encryptor = DataEncryptor(self.encryption_key)
            email_config_service = EmailConfigService(session, encryptor=encryptor)
            email_config = email_config_service.get_config(decrypt=True)

            if email_config is None or not email_config.enabled:
                _raise_email_server_not_configured()
                return  # Never reached, but helps type checker

            email_service = EmailService(email_config)

            # Update progress: 0.3 - email service ready
            update_progress(0.3)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Create book service
            book_service = BookService(library, session=session)

            # Update progress: 0.4 - book service ready
            update_progress(0.4)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Get book information and prepare completion metadata
            book_title, attachment_filename = self._prepare_completion_metadata(
                book_service
            )

            # Send book via email
            book_service.send_book(
                book_id=self.book_id,
                user_id=self.user_id,
                email_service=email_service,
                to_email=self.to_email,
                file_format=self.file_format,
            )

            # Store completion metadata (book title and attachment filename)
            # This will be included when the task executor calls complete_task
            self.set_metadata("book_title", book_title)
            self.set_metadata("attachment_filename", attachment_filename)

            # Update progress: 1.0 - complete
            update_progress(1.0)

            logger.info(
                "Task %s: Book %s sent successfully to %s",
                self.task_id,
                self.book_id,
                self.to_email or "default device",
            )

        except ValueError:
            logger.exception("Task %s failed with ValueError", self.task_id)
            raise
        except EmailServiceError:
            logger.exception("Task %s failed with EmailServiceError", self.task_id)
            raise
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

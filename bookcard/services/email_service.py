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

"""Email service for sending e-books to devices.

Uses py-ezmail to send emails via SMTP or Gmail.
Follows SRP by handling only email sending operations.
Uses Strategy pattern to decouple email sending strategies from the service.
"""

from __future__ import annotations

import contextlib
import logging
import shutil
import smtplib
import socket
import ssl
import tempfile
from abc import ABC, abstractmethod
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import ClassVar

from ezmail import EzSender
from pydantic import EmailStr, TypeAdapter, ValidationError

from bookcard.models.config import EmailServerConfig, EmailServerType
from bookcard.services.email_utils import build_attachment_filename

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Error raised when email sending fails."""


class EmailSenderStrategy(ABC):
    """Abstract base class for email sending strategies.

    Each email server type (SMTP, Gmail, etc.) implements this interface
    to provide server-specific email sending.
    """

    @abstractmethod
    def can_handle(self, server_type: EmailServerType) -> bool:
        """Check if this strategy can handle the given server type.

        Parameters
        ----------
        server_type : EmailServerType
            Email server type.

        Returns
        -------
        bool
            True if this strategy can handle the server type.
        """

    @abstractmethod
    def send(
        self,
        *,
        to_email: str,
        subject: str,
        message: str,
        attachment_path: Path,
    ) -> None:
        """Send an email with attachment.

        Parameters
        ----------
        to_email : str
            Recipient email address.
        subject : str
            Email subject.
        message : str
            Email message body.
        attachment_path : Path
            Path to file to attach.
            The attachment path may be deleted immediately after this method
            returns. Implementations MUST read any required file contents before
            returning.

        Raises
        ------
        EmailServiceError
            If configuration is invalid or sending fails.
        """


class SmtpEmailSenderStrategy(EmailSenderStrategy):
    """Strategy for sending emails via SMTP server."""

    def __init__(self, config: EmailServerConfig) -> None:
        """Initialize SMTP email sender strategy.

        Parameters
        ----------
        config : EmailServerConfig
            Email server configuration with decrypted credentials.
        """
        self._config = config

    def can_handle(self, server_type: EmailServerType) -> bool:
        """Check if this strategy can handle SMTP server type."""
        return server_type == EmailServerType.SMTP

    def send(
        self,
        *,
        to_email: str,
        subject: str,
        message: str,
        attachment_path: Path,
    ) -> None:
        """Send email via SMTP server.

        Parameters
        ----------
        to_email : str
            Recipient email address.
        subject : str
            Email subject.
        message : str
            Email message body.
        attachment_path : Path
            Path to file to attach.

        Raises
        ------
        EmailServiceError
            If SMTP configuration is invalid or sending fails.
        """
        if not self._config.smtp_host:
            msg = "smtp_host_required"
            raise EmailServiceError(msg)

        if not self._config.smtp_from_email:
            msg = "smtp_from_email_required"
            raise EmailServiceError(msg)

        # Prepare SMTP configuration for py-ezmail EzSender
        smtp = {
            "server": self._config.smtp_host,
            "port": self._config.smtp_port or 587,
        }

        # Prepare sender configuration
        sender = {
            "email": self._config.smtp_from_email,
        }

        # Add password authentication if credentials are provided
        if self._config.smtp_username and self._config.smtp_password:
            sender["email"] = self._config.smtp_username
            sender["password"] = self._config.smtp_password
        elif self._config.smtp_password:
            # If no username, use from_email as username
            sender["password"] = self._config.smtp_password

        try:
            with EzSender(smtp, sender) as ez:
                ez.subject = subject
                ez.add_text(message)
                ez.add_attachment(str(attachment_path))
                ez.send([to_email])
        except Exception as exc:
            msg = f"failed_to_send_email: {exc}"
            raise EmailServiceError(msg) from exc


class NoAuthSmtpEmailSenderStrategy(EmailSenderStrategy):
    """Strategy for sending emails via SMTP without authentication.

    This is intentionally implemented without `py-ezmail` because that library
    always requires credentials and performs `SMTP.login(...)`.
    """

    def __init__(self, config: EmailServerConfig) -> None:
        """Initialize no-auth SMTP email sender strategy.

        Parameters
        ----------
        config : EmailServerConfig
            Email server configuration with decrypted values.
        """
        self._config = config

    def can_handle(self, server_type: EmailServerType) -> bool:
        """Check if this strategy can handle the given server type.

        Parameters
        ----------
        server_type : EmailServerType
            Email server type.

        Returns
        -------
        bool
            True if this strategy should handle the configuration.
        """
        if server_type != EmailServerType.SMTP:
            return False
        # Treat missing/empty password as "no-auth" flow.
        return not self._config.smtp_password

    def send(
        self,
        *,
        to_email: str,
        subject: str,
        message: str,
        attachment_path: Path,
    ) -> None:
        """Send email via SMTP without authentication.

        Parameters
        ----------
        to_email : str
            Recipient email address.
        subject : str
            Email subject.
        message : str
            Email message body (plain text).
        attachment_path : Path
            Path to file to attach.

        Raises
        ------
        EmailServiceError
            If configuration is invalid or sending fails.
        """
        if not self._config.smtp_host:
            msg = "smtp_host_required"
            raise EmailServiceError(msg)

        if not self._config.smtp_from_email:
            msg = "smtp_from_email_required"
            raise EmailServiceError(msg)

        port: int = self._config.smtp_port or 587
        # Security-first defaults:
        # - port 465 implies SSL
        # - port 587 implies STARTTLS
        # Explicit flags can still force behavior on other ports.
        use_ssl: bool = bool(self._config.smtp_use_ssl) or port == 465
        use_tls: bool = (not use_ssl) and (
            bool(self._config.smtp_use_tls) or port == 587
        )

        email_msg = EmailMessage()
        email_msg["From"] = self._config.smtp_from_email
        email_msg["To"] = to_email
        email_msg["Subject"] = subject
        email_msg.set_content(message or "")

        try:
            ctype, _ = guess_type(str(attachment_path))
            if ctype and "/" in ctype:
                maintype, subtype = ctype.split("/", 1)
            else:
                maintype, subtype = ("application", "octet-stream")

            attachment_bytes = attachment_path.read_bytes()
            email_msg.add_attachment(
                attachment_bytes,
                maintype=maintype,
                subtype=subtype,
                filename=attachment_path.name,
            )
        except OSError as exc:
            msg = f"failed_to_prepare_attachment: {exc!s}"
            raise EmailServiceError(msg) from exc

        smtp: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        try:
            logger.debug(
                "Connecting to SMTP server %s:%s (ssl=%s, starttls=%s)",
                self._config.smtp_host,
                port,
                use_ssl,
                use_tls,
            )
            if use_ssl:
                smtp = smtplib.SMTP_SSL(self._config.smtp_host, port, timeout=30)
            else:
                smtp = smtplib.SMTP(self._config.smtp_host, port, timeout=30)

            # Some servers expect EHLO/HELO before MAIL FROM.
            smtp.ehlo()

            if use_tls:
                smtp.starttls()
                smtp.ehlo()

            smtp.send_message(email_msg)
            logger.info("Email sent successfully to %s (no-auth SMTP)", to_email)
        except (
            OSError,
            smtplib.SMTPException,
            socket.gaierror,
            TimeoutError,
            ssl.SSLError,
        ) as exc:
            msg = f"failed_to_send_email: {exc}"
            raise EmailServiceError(msg) from exc
        finally:
            if smtp is not None:
                with contextlib.suppress(smtplib.SMTPException, OSError, ssl.SSLError):
                    smtp.quit()


class GmailEmailSenderStrategy(EmailSenderStrategy):
    """Strategy for sending emails via Gmail OAuth2."""

    def __init__(self, config: EmailServerConfig) -> None:
        """Initialize Gmail email sender strategy.

        Parameters
        ----------
        config : EmailServerConfig
            Email server configuration with decrypted credentials.
        """
        self._config = config

    def can_handle(self, server_type: EmailServerType) -> bool:
        """Check if this strategy can handle Gmail server type."""
        return server_type == EmailServerType.GMAIL

    def send(
        self,
        *,
        to_email: str,
        subject: str,
        message: str,
        attachment_path: Path,
    ) -> None:
        """Send email via Gmail API.

        Parameters
        ----------
        to_email : str
            Recipient email address.
        subject : str
            Email subject.
        message : str
            Email message body.
        attachment_path : Path
            Path to file to attach.

        Raises
        ------
        EmailServiceError
            If Gmail configuration is invalid or sending fails.
        """
        if not self._config.gmail_token:
            msg = "gmail_token_required"
            raise EmailServiceError(msg)

        # For Gmail, py-ezmail uses OAuth2 token
        # Extract token information from gmail_token dict
        token_data = self._config.gmail_token
        if not isinstance(token_data, dict):
            msg = "invalid_gmail_token_format"
            raise EmailServiceError(msg)

        # Get email from token (usually stored in token)
        # For Gmail OAuth, we need the email address associated with the token
        gmail_email = token_data.get("email") or token_data.get("user_email")
        if not gmail_email:
            msg = "gmail_email_not_found_in_token"
            raise EmailServiceError(msg)

        # Get OAuth2 access token
        access_token = token_data.get("access_token")
        if not access_token:
            msg = "gmail_access_token_not_found"
            raise EmailServiceError(msg)

        # Prepare Gmail SMTP configuration
        smtp = {
            "server": "smtp.gmail.com",
            "port": 587,
        }

        # Prepare sender with OAuth2 authentication
        sender = {
            "email": gmail_email,
            "auth_value": access_token,
            "auth_type": "oauth2",
        }

        try:
            with EzSender(smtp, sender) as ez:
                ez.subject = subject
                ez.add_text(message)
                ez.add_attachment(str(attachment_path))
                ez.send([to_email])
        except Exception as exc:
            msg = f"failed_to_send_email_via_gmail: {exc}"
            raise EmailServiceError(msg) from exc


class EmailSenderStrategyFactory:
    """Factory for creating email sender strategies.

    Follows Factory pattern to create appropriate strategy based on server type.
    """

    AVAILABLE_STRATEGIES: ClassVar[tuple[type[EmailSenderStrategy], ...]] = (
        NoAuthSmtpEmailSenderStrategy,
        SmtpEmailSenderStrategy,
        GmailEmailSenderStrategy,
    )

    @classmethod
    def create(cls, config: EmailServerConfig) -> EmailSenderStrategy:
        """Create appropriate email sender strategy for the given config.

        Parameters
        ----------
        config : EmailServerConfig
            Email server configuration.

        Returns
        -------
        EmailSenderStrategy
            Email sender strategy instance.

        Raises
        ------
        EmailServiceError
            If no strategy can handle the server type.
        """
        if config.server_type == EmailServerType.GMAIL:
            return GmailEmailSenderStrategy(config)

        if config.server_type == EmailServerType.SMTP:
            # If no password is set, treat it as "no-auth" flow. This must not
            # depend on list ordering.
            if not config.smtp_password:
                return NoAuthSmtpEmailSenderStrategy(config)
            return SmtpEmailSenderStrategy(config)

        msg = f"unsupported_server_type: {config.server_type}"
        raise EmailServiceError(msg)


class EmailService:
    """Service for sending emails using configured email server.

    Supports both SMTP and Gmail server types.
    Uses py-ezmail library for email sending.
    Uses Strategy pattern to decouple sending logic from service.

    Parameters
    ----------
    config : EmailServerConfig
        Email server configuration with decrypted credentials.
    """

    def __init__(self, config: EmailServerConfig) -> None:
        """Initialize email service with configuration.

        Parameters
        ----------
        config : EmailServerConfig
            Email server configuration with decrypted credentials.
        """
        self._config = config
        self._sender_strategy = EmailSenderStrategyFactory.create(config)

    def send_ebook(
        self,
        *,
        to_email: str,
        book_title: str,
        book_file_path: Path,
        preferred_format: str | None = None,
        author: str | None = None,
    ) -> None:
        """Send an e-book file to the specified email address.

        Parameters
        ----------
        to_email : str
            Recipient email address (e-reader device email).
        book_title : str
            Book title for email subject and message.
        book_file_path : Path
            Path to the e-book file to attach.
        preferred_format : str | None
            Preferred format name (e.g., 'EPUB', 'MOBI') for display.
        author : str | None
            Author name used when constructing the attachment filename.

        Raises
        ------
        EmailServiceError
            If email server is not enabled, configuration is invalid,
            or sending fails.
        ValueError
            If file does not exist, email size exceeds limit,
            or attachment preparation fails.
        """
        if not self._config.enabled:
            msg = "email_server_not_enabled"
            raise EmailServiceError(msg)

        try:
            TypeAdapter(EmailStr).validate_python(to_email)
        except ValidationError as exc:
            msg = f"invalid_email_address: {to_email}"
            raise ValueError(msg) from exc

        if not book_file_path.exists():
            msg = f"book_file_not_found: {book_file_path}"
            raise ValueError(msg)

        # Check file size against max_email_size_mb
        file_size_mb = book_file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self._config.max_email_size_mb:
            msg = (
                f"file_too_large: {file_size_mb:.2f}MB exceeds "
                f"limit of {self._config.max_email_size_mb}MB"
            )
            raise ValueError(msg)

        # Prepare email subject and message
        format_str = f" ({preferred_format})" if preferred_format else ""
        subject = f"{book_title}{format_str}"
        message = f"Please find your e-book '{book_title}' attached."

        # Build a sanitized attachment filename: "author - title.ext"
        # Fallbacks:
        # - If author is missing, use title only.
        # - If neither is available, use "Unknown Author - Unknown Book.ext".
        if preferred_format:
            extension: str | None = preferred_format.lower()
        elif book_file_path.suffix:
            extension = book_file_path.suffix.lstrip(".").lower()
        else:
            extension = None

        attachment_filename = build_attachment_filename(
            author=author,
            title=book_title,
            extension=extension,
        )

        logger.info(
            "Sending '%s' to %s via %s",
            book_title,
            to_email,
            self._sender_strategy.__class__.__name__,
        )
        logger.debug(
            "Attachment source=%s size_mb=%.2f max_mb=%s",
            book_file_path,
            file_size_mb,
            self._config.max_email_size_mb,
        )

        # Use a per-send temporary directory to avoid filename collisions when
        # multiple sends happen concurrently (e.g., background workers).
        with tempfile.TemporaryDirectory(prefix="bookcard_email_attachments_") as tmp:
            temp_dir = Path(tmp)
            temp_path = temp_dir / attachment_filename

            try:
                shutil.copy2(book_file_path, temp_path)
            except OSError as exc:
                msg = f"failed_to_prepare_attachment: {exc!s}"
                raise ValueError(msg) from exc

            # Delegate to strategy with sanitized attachment path
            self._sender_strategy.send(
                to_email=to_email,
                subject=subject,
                message=message,
                attachment_path=temp_path,
            )

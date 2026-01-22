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

"""Tests for email service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import EmailServerConfig, EmailServerType
from bookcard.services.email_service import (
    EmailSenderStrategyFactory,
    EmailService,
    EmailServiceError,
    GmailEmailSenderStrategy,
    NoAuthSmtpEmailSenderStrategy,
    SmtpEmailSenderStrategy,
)


@pytest.fixture
def smtp_config() -> EmailServerConfig:
    """Create a test SMTP email server configuration."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_from_email="sender@example.com",
        smtp_username="user@example.com",
        smtp_password="password123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def gmail_config() -> EmailServerConfig:
    """Create a test Gmail email server configuration."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.GMAIL,
        enabled=True,
        gmail_token={
            "access_token": "token123",
            "email": "test@gmail.com",
            "user_email": "test@gmail.com",
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def test_file(tmp_path: Path) -> Path:
    """Create a test file for email attachments."""
    test_file = tmp_path / "test.epub"
    test_file.write_text("test content")
    return test_file


# Tests for SmtpEmailSenderStrategy.send (lines 140-175)
def test_smtp_send_missing_host(smtp_config: EmailServerConfig) -> None:
    """Test SmtpEmailSenderStrategy.send raises error when smtp_host is missing (covers line 140-142)."""
    smtp_config.smtp_host = None
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with pytest.raises(EmailServiceError, match="smtp_host_required"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=Path("/tmp/test.epub"),
        )


def test_smtp_send_missing_from_email(smtp_config: EmailServerConfig) -> None:
    """Test SmtpEmailSenderStrategy.send raises error when smtp_from_email is missing (covers line 144-146)."""
    smtp_config.smtp_from_email = None
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with pytest.raises(EmailServiceError, match="smtp_from_email_required"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=Path("/tmp/test.epub"),
        )


def test_smtp_send_with_username_and_password(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test SmtpEmailSenderStrategy.send with username and password (covers lines 160-162)."""
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        mock_ez_sender.assert_called_once()
        smtp_call = mock_ez_sender.call_args[0][0]
        sender_call = mock_ez_sender.call_args[0][1]

        assert smtp_call["server"] == "smtp.example.com"
        assert smtp_call["port"] == 587
        assert sender_call["email"] == "user@example.com"
        assert sender_call["password"] == "password123"

        mock_ez.subject = "Test Subject"
        mock_ez.add_text.assert_called_once_with("Test message")
        mock_ez.add_attachment.assert_called_once_with(str(test_file))
        mock_ez.send.assert_called_once_with(["recipient@example.com"])


def test_smtp_send_with_password_only(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test SmtpEmailSenderStrategy.send with password only (covers lines 163-165)."""
    smtp_config.smtp_username = None
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        sender_call = mock_ez_sender.call_args[0][1]
        assert sender_call["email"] == "sender@example.com"
        assert sender_call["password"] == "password123"


def test_smtp_send_without_credentials(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test SmtpEmailSenderStrategy.send without credentials (covers lines 155-157)."""
    smtp_config.smtp_username = None
    smtp_config.smtp_password = None
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        sender_call = mock_ez_sender.call_args[0][1]
        assert sender_call["email"] == "sender@example.com"
        assert "password" not in sender_call


def test_smtp_send_default_port(
    smtp_config: EmailServerConfig, test_file: Path
) -> None:
    """Test SmtpEmailSenderStrategy.send uses default port 587 when port is None (covers line 151)."""
    smtp_config.smtp_port = None
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        smtp_call = mock_ez_sender.call_args[0][0]
        assert smtp_call["port"] == 587


def test_smtp_send_exception_handling(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test SmtpEmailSenderStrategy.send handles exceptions (covers lines 173-175)."""
    strategy = SmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez_sender.side_effect = Exception("Connection failed")

        with pytest.raises(EmailServiceError, match="failed_to_send_email"):
            strategy.send(
                to_email="recipient@example.com",
                subject="Test Subject",
                message="Test message",
                attachment_path=test_file,
            )


def test_noauth_smtp_strategy_can_handle_when_password_missing(
    smtp_config: EmailServerConfig,
) -> None:
    """Test NoAuthSmtpEmailSenderStrategy.can_handle when password is missing."""
    smtp_config.smtp_password = None
    strategy = NoAuthSmtpEmailSenderStrategy(smtp_config)

    assert strategy.can_handle(EmailServerType.SMTP) is True
    assert strategy.can_handle(EmailServerType.GMAIL) is False


def test_noauth_smtp_send_does_not_login(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test NoAuthSmtpEmailSenderStrategy.send does not perform SMTP login."""
    smtp_config.smtp_password = None
    smtp_config.smtp_username = "user@example.com"
    strategy = NoAuthSmtpEmailSenderStrategy(smtp_config)

    with patch("bookcard.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_conn = MagicMock()
        mock_smtp.return_value = mock_conn

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        # Ensure no login attempt is made in no-auth flow.
        mock_conn.login.assert_not_called()
        mock_conn.send_message.assert_called_once()


def test_strategy_factory_prefers_noauth_strategy_when_password_missing(
    smtp_config: EmailServerConfig,
) -> None:
    """Test EmailSenderStrategyFactory chooses no-auth SMTP strategy when password is missing."""
    smtp_config.smtp_password = None
    strategy = EmailSenderStrategyFactory.create(smtp_config)
    assert isinstance(strategy, NoAuthSmtpEmailSenderStrategy)


# Tests for GmailEmailSenderStrategy (lines 189, 193, 221-266)
def test_gmail_sender_strategy_init(gmail_config: EmailServerConfig) -> None:
    """Test GmailEmailSenderStrategy initialization (covers line 189)."""
    strategy = GmailEmailSenderStrategy(gmail_config)

    assert strategy._config is gmail_config


def test_gmail_sender_strategy_can_handle(gmail_config: EmailServerConfig) -> None:
    """Test GmailEmailSenderStrategy.can_handle (covers line 193)."""
    strategy = GmailEmailSenderStrategy(gmail_config)

    assert strategy.can_handle(EmailServerType.GMAIL) is True
    assert strategy.can_handle(EmailServerType.SMTP) is False


def test_gmail_send_missing_token(
    gmail_config: EmailServerConfig, test_file: Path
) -> None:
    """Test GmailEmailSenderStrategy.send raises error when token is missing (covers lines 221-223)."""
    gmail_config.gmail_token = None
    strategy = GmailEmailSenderStrategy(gmail_config)

    with pytest.raises(EmailServiceError, match="gmail_token_required"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=test_file,
        )


def test_gmail_send_invalid_token_format(
    gmail_config: EmailServerConfig, test_file: Path
) -> None:
    """Test GmailEmailSenderStrategy.send raises error when token is not a dict (covers lines 227-230)."""
    gmail_config.gmail_token = "not_a_dict"
    strategy = GmailEmailSenderStrategy(gmail_config)

    with pytest.raises(EmailServiceError, match="invalid_gmail_token_format"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=test_file,
        )


def test_gmail_send_missing_email_in_token(
    gmail_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test GmailEmailSenderStrategy.send raises error when email not in token (covers lines 234-237)."""
    gmail_config.gmail_token = {"access_token": "token123"}
    strategy = GmailEmailSenderStrategy(gmail_config)

    with pytest.raises(EmailServiceError, match="gmail_email_not_found_in_token"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=test_file,
        )


def test_gmail_send_uses_user_email_fallback(
    gmail_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test GmailEmailSenderStrategy.send uses user_email when email not present (covers line 234)."""
    gmail_config.gmail_token = {
        "access_token": "token123",
        "user_email": "fallback@gmail.com",
    }
    strategy = GmailEmailSenderStrategy(gmail_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        sender_call = mock_ez_sender.call_args[0][1]
        assert sender_call["email"] == "fallback@gmail.com"


def test_gmail_send_missing_access_token(
    gmail_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test GmailEmailSenderStrategy.send raises error when access_token is missing (covers lines 240-243)."""
    gmail_config.gmail_token = {"email": "test@gmail.com"}
    strategy = GmailEmailSenderStrategy(gmail_config)

    with pytest.raises(EmailServiceError, match="gmail_access_token_not_found"):
        strategy.send(
            to_email="recipient@example.com",
            subject="Test",
            message="Test message",
            attachment_path=test_file,
        )


def test_gmail_send_success(gmail_config: EmailServerConfig, test_file: Path) -> None:
    """Test GmailEmailSenderStrategy.send successfully sends email (covers lines 245-263)."""
    strategy = GmailEmailSenderStrategy(gmail_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez = MagicMock()
        mock_ez_sender.return_value.__enter__.return_value = mock_ez

        strategy.send(
            to_email="recipient@example.com",
            subject="Test Subject",
            message="Test message",
            attachment_path=test_file,
        )

        smtp_call = mock_ez_sender.call_args[0][0]
        sender_call = mock_ez_sender.call_args[0][1]

        assert smtp_call["server"] == "smtp.gmail.com"
        assert smtp_call["port"] == 587
        assert sender_call["email"] == "test@gmail.com"
        assert sender_call["auth_value"] == "token123"
        assert sender_call["auth_type"] == "oauth2"

        mock_ez.subject = "Test Subject"
        mock_ez.add_text.assert_called_once_with("Test message")
        mock_ez.add_attachment.assert_called_once_with(str(test_file))
        mock_ez.send.assert_called_once_with(["recipient@example.com"])


def test_gmail_send_exception_handling(
    gmail_config: EmailServerConfig, test_file: Path
) -> None:
    """Test GmailEmailSenderStrategy.send handles exceptions (covers lines 264-266)."""
    strategy = GmailEmailSenderStrategy(gmail_config)

    with patch("bookcard.services.email_service.EzSender") as mock_ez_sender:
        mock_ez_sender.side_effect = Exception("Gmail API error")

        with pytest.raises(EmailServiceError, match="failed_to_send_email_via_gmail"):
            strategy.send(
                to_email="recipient@example.com",
                subject="Test Subject",
                message="Test message",
                attachment_path=test_file,
            )


# Tests for EmailSenderStrategyFactory.create error (lines 304-305)
def test_strategy_factory_unsupported_type(smtp_config: EmailServerConfig) -> None:
    """Test EmailSenderStrategyFactory.create raises error for unsupported type (covers lines 304-305)."""
    smtp_config.server_type = "UNSUPPORTED"  # type: ignore[assignment]

    with pytest.raises(EmailServiceError, match="unsupported_server_type"):
        EmailSenderStrategyFactory.create(smtp_config)


# Tests for EmailService.send_ebook (lines 365-423)
def test_send_ebook_server_disabled(
    smtp_config: EmailServerConfig, test_file: Path
) -> None:
    """Test EmailService.send_ebook raises error when server is disabled (covers lines 365-367)."""
    smtp_config.enabled = False
    service = EmailService(smtp_config)

    with pytest.raises(EmailServiceError, match="email_server_not_enabled"):
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=test_file,
        )


def test_send_ebook_file_not_found(smtp_config: EmailServerConfig) -> None:
    """Test EmailService.send_ebook raises error when file not found (covers lines 369-371)."""
    service = EmailService(smtp_config)
    nonexistent_file = Path("/nonexistent/file.epub")

    with pytest.raises(ValueError, match="book_file_not_found"):
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=nonexistent_file,
        )


def test_send_ebook_file_too_large(
    smtp_config: EmailServerConfig, tmp_path: Path
) -> None:
    """Test EmailService.send_ebook raises error when file too large (covers lines 373-380)."""
    smtp_config.max_email_size_mb = 1.0
    service = EmailService(smtp_config)

    # Create a file larger than the limit
    large_file = tmp_path / "large.epub"
    large_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

    with pytest.raises(ValueError, match="file_too_large"):
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=large_file,
        )


def test_send_ebook_success(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test EmailService.send_ebook successfully sends email (covers lines 365-423)."""
    service = EmailService(smtp_config)

    with patch.object(service._sender_strategy, "send") as mock_send:
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=test_file,
            preferred_format="EPUB",
            author="Test Author",
        )

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["to_email"] == "recipient@example.com"
        assert call_kwargs["subject"] == "Test Book (EPUB)"
        assert "Test Book" in call_kwargs["message"]
        assert call_kwargs["attachment_path"].name.startswith("Test Author - Test Book")


def test_send_ebook_without_preferred_format(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test EmailService.send_ebook without preferred format (covers lines 383-385)."""
    service = EmailService(smtp_config)

    with patch.object(service._sender_strategy, "send") as mock_send:
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=test_file,
        )

        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["subject"] == "Test Book"


def test_send_ebook_attachment_preparation_failure(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test EmailService.send_ebook handles attachment preparation failure (covers lines 406-410)."""
    service = EmailService(smtp_config)

    with patch("shutil.copy2") as mock_copy:
        mock_copy.side_effect = OSError("Permission denied")

        with pytest.raises(ValueError, match="failed_to_prepare_attachment"):
            service.send_ebook(
                to_email="recipient@example.com",
                book_title="Test Book",
                book_file_path=test_file,
            )


def test_send_ebook_cleanup_temp_file(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test EmailService.send_ebook cleans up temp file (covers lines 420-423)."""
    service = EmailService(smtp_config)

    with patch.object(service._sender_strategy, "send") as mock_send:
        service.send_ebook(
            to_email="recipient@example.com",
            book_title="Test Book",
            book_file_path=test_file,
        )

        # Get the temp path from the call
        call_kwargs = mock_send.call_args[1]
        temp_path = call_kwargs["attachment_path"]

        # File should be cleaned up
        assert not temp_path.exists()


def test_send_ebook_cleanup_on_error(
    smtp_config: EmailServerConfig,
    test_file: Path,
) -> None:
    """Test EmailService.send_ebook cleans up temp file even on error (covers lines 420-423)."""
    service = EmailService(smtp_config)

    with patch.object(service._sender_strategy, "send") as mock_send:
        mock_send.side_effect = EmailServiceError("Send failed")

        with pytest.raises(EmailServiceError):
            service.send_ebook(
                to_email="recipient@example.com",
                book_title="Test Book",
                book_file_path=test_file,
            )

        # Get the temp path from the call
        call_kwargs = mock_send.call_args[1]
        temp_path = call_kwargs["attachment_path"]

        # File should still be cleaned up
        assert not temp_path.exists()


# Tests for build_attachment_filename utility function
@pytest.mark.parametrize(
    ("author", "title", "extension", "expected_start"),
    [
        ("Author One", "Test Book", "epub", "Author One - Test Book"),
        ("Author One", "Test Book", None, "Author One - Test Book"),
        (None, "Test Book", "epub", "Test Book"),
        ("Author One", None, "epub", "Author One - Unknown Book"),
        (None, None, "epub", "Unknown Author - Unknown Book"),
        ("", "", "epub", "Unknown Author - Unknown Book"),
    ],
)
def test_build_attachment_filename(
    author: str | None,
    title: str | None,
    extension: str | None,
    expected_start: str,
) -> None:
    """Test build_attachment_filename utility function."""
    from bookcard.services.email_utils import build_attachment_filename

    result = build_attachment_filename(
        author=author,
        title=title,
        extension=extension,
    )

    assert result.startswith(expected_start)
    if extension:
        assert result.endswith(f".{extension.lower()}")


def test_build_attachment_filename_sanitizes_unicode() -> None:
    """Test build_attachment_filename sanitizes unicode."""
    from bookcard.services.email_utils import build_attachment_filename

    result = build_attachment_filename(
        author="José",
        title="Café",
        extension="epub",
    )

    # Should normalize unicode characters
    assert "Jos" in result or "Caf" in result


def test_build_attachment_filename_removes_invalid_chars() -> None:
    """Test build_attachment_filename removes invalid characters."""
    from bookcard.services.email_utils import build_attachment_filename

    result = build_attachment_filename(
        author="Author/With\\Invalid:Chars",
        title="Book*Name?",
        extension="epub",
    )

    # Should only contain allowed characters
    allowed_chars = set(" -_.(),&'")
    for char in result:
        assert char.isalnum() or char in allowed_chars or char == "."


def test_build_attachment_filename_truncates_long_names() -> None:
    """Test build_attachment_filename truncates long names."""
    from bookcard.services.email_utils import build_attachment_filename

    long_title = "A" * 200
    result = build_attachment_filename(
        author=None,
        title=long_title,
        extension="epub",
    )

    # Should be truncated to max 150 chars + extension
    assert len(result) <= 150 + len(".epub")


def test_build_attachment_filename_handles_empty_after_sanitization() -> None:
    """Test build_attachment_filename handles empty after sanitization."""
    from bookcard.services.email_utils import build_attachment_filename

    # Use only characters that will be completely removed by sanitization
    # Allowed chars are: space, -, _, ., (, ), &, ,, ', +
    # Use characters like @#$%^[]{}|;:'\"<>?/~` that are NOT in allowed_chars
    # After normalization and filtering, if nothing remains, should use default
    # Note: The code checks `if not sanitized:` after strip, so we need to ensure
    # the result after strip is empty (not just whitespace/punctuation)
    result = build_attachment_filename(
        author="   ",
        title="   ",
        extension="epub",
    )

    # After strip(" ."), if empty, should fall back to default
    # But if only spaces/dots remain, they get stripped and result is empty
    assert result == "Unknown Author - Unknown Book.epub"


def test_build_attachment_filename_empty_after_sanitization_triggers_fallback() -> None:
    """Test build_attachment_filename falls back to default when sanitized is empty."""
    from bookcard.services.email_utils import build_attachment_filename

    # To trigger fallback, we need sanitized to be empty after all processing
    # If we provide only title (no author), base = title_part
    # Use only special characters that are not in allowed_chars
    # Allowed chars are: space, -, _, ., (, ), &, ,, ', +
    # After filtering, if nothing remains, sanitized is empty, triggering fallback
    result = build_attachment_filename(
        author=None,  # No author
        title="...",  # Only dots, which are in allowed_chars but get stripped
        extension="epub",
    )

    # After normalization and filtering, dots remain (they're in allowed_chars)
    # After strip(" ."), dots are removed, leaving empty string
    # This triggers fallback to default_base
    assert result == "Unknown Author - Unknown Book.epub"


def test_build_attachment_filename_strips_extension_dot() -> None:
    """Test build_attachment_filename strips leading dot from extension."""
    from bookcard.services.email_utils import build_attachment_filename

    result = build_attachment_filename(
        author="Author",
        title="Book",
        extension=".epub",
    )

    assert result.endswith(".epub")
    assert ".epub" not in result[:-5]  # No double dots

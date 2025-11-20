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

"""Tests for EmailSendTask to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.config import EmailServerConfig, EmailServerType, Library
from fundamental.services.email_service import EmailServiceError
from fundamental.services.tasks.email_send_task import (
    EmailSendTask,
    _raise_email_server_not_configured,
    _raise_no_library_configured,
)
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session."""
    return DummySession()


@pytest.fixture
def worker_context(session: DummySession) -> dict[str, Any]:
    """Create worker context for task execution."""
    update_progress = MagicMock()
    return {
        "session": session,
        "task_service": MagicMock(),
        "update_progress": update_progress,
    }


@pytest.fixture
def base_metadata() -> dict[str, object]:
    """Create base metadata for EmailSendTask."""
    return {
        "book_id": 1,
        "to_email": "test@example.com",
        "file_format": "EPUB",
        "encryption_key": "test-key",
    }


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def email_config() -> EmailServerConfig:
    """Create a test email config."""
    return EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestHelperFunctions:
    """Test helper functions."""

    def test_raise_no_library_configured(self) -> None:
        """Test _raise_no_library_configured raises ValueError."""
        with pytest.raises(ValueError, match="No active library configured"):
            _raise_no_library_configured()

    def test_raise_email_server_not_configured(self) -> None:
        """Test _raise_email_server_not_configured raises ValueError."""
        with pytest.raises(ValueError, match="email_server_not_configured_or_disabled"):
            _raise_email_server_not_configured()


class TestEmailSendTaskInit:
    """Test EmailSendTask initialization."""

    @pytest.mark.parametrize(
        ("metadata", "expected_error", "error_match"),
        [
            ({}, ValueError, "book_id is required"),
            ({"book_id": None}, ValueError, "book_id is required"),
            ({"book_id": "not-int"}, TypeError, "book_id must be an integer"),
            ({"book_id": 1}, ValueError, "encryption_key is required"),
            (
                {"book_id": 1, "encryption_key": None},
                ValueError,
                "encryption_key is required",
            ),
            (
                {"book_id": 1, "encryption_key": ""},
                ValueError,
                "encryption_key is required",
            ),
            (
                {"book_id": 1, "encryption_key": 123},
                TypeError,
                "encryption_key must be a string",
            ),
        ],
    )
    def test_init_validation_errors(
        self,
        metadata: dict[str, object],
        expected_error: type[Exception],
        error_match: str,
    ) -> None:
        """Test __init__ raises appropriate errors for invalid metadata."""
        with pytest.raises(expected_error, match=error_match):
            EmailSendTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_success(self, base_metadata: dict[str, object]) -> None:
        """Test __init__ sets attributes correctly."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)
        assert task.book_id == 1
        assert task.to_email == "test@example.com"
        assert task.file_format == "EPUB"
        assert task.encryption_key == "test-key"

    def test_init_optional_fields(self) -> None:
        """Test __init__ handles optional fields."""
        metadata = {
            "book_id": 1,
            "encryption_key": "test-key",
        }
        task = EmailSendTask(task_id=1, user_id=1, metadata=metadata)
        assert task.book_id == 1
        assert task.to_email is None
        assert task.file_format is None
        assert task.encryption_key == "test-key"


class TestEmailSendTaskRun:
    """Test EmailSendTask.run method."""

    @pytest.fixture
    def mock_library_service(self, library: Library) -> MagicMock:
        """Create mock library service."""
        service = MagicMock()
        service.get_active_library.return_value = library
        return service

    @pytest.fixture
    def mock_email_config_service(self, email_config: EmailServerConfig) -> MagicMock:
        """Create mock email config service."""
        service = MagicMock()
        service.get_config.return_value = email_config
        return service

    @pytest.fixture
    def mock_book_service(self) -> MagicMock:
        """Create mock book service."""
        service = MagicMock()
        service.send_book.return_value = None
        return service

    def test_run_success(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
        mock_email_config_service: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test run completes successfully."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService",
                return_value=mock_email_config_service,
            ),
            patch("fundamental.services.tasks.email_send_task.EmailService"),
            patch(
                "fundamental.services.tasks.email_send_task.BookService",
                return_value=mock_book_service,
            ),
        ):
            task.run(worker_context)

        # Verify progress updates
        update_progress = worker_context["update_progress"]
        assert update_progress.call_count == 5
        update_progress.assert_any_call(0.1)
        update_progress.assert_any_call(0.2)
        update_progress.assert_any_call(0.3)
        update_progress.assert_any_call(0.4)
        update_progress.assert_any_call(1.0)

        # Verify book service was called
        mock_book_service.send_book.assert_called_once()
        call_kwargs = mock_book_service.send_book.call_args[1]
        assert call_kwargs["book_id"] == 1
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["to_email"] == "test@example.com"
        assert call_kwargs["file_format"] == "EPUB"

    def test_run_cancelled_before_processing(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run returns early if cancelled before processing."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)
        task.mark_cancelled()

        task.run(worker_context)

        # Should not update progress
        update_progress = worker_context["update_progress"]
        update_progress.assert_not_called()

    def test_run_no_library_configured(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run raises ValueError when no library configured."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService"
            ) as mock_library_service,
        ):
            mock_library_service.return_value.get_active_library.return_value = None

            with pytest.raises(ValueError, match="No active library configured"):
                task.run(worker_context)

    def test_run_email_server_not_configured(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
    ) -> None:
        """Test run raises ValueError when email server not configured."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService"
            ) as mock_email_config_service,
        ):
            # Return None or disabled config
            mock_email_config_service.return_value.get_config.return_value = None

            with pytest.raises(
                ValueError, match="email_server_not_configured_or_disabled"
            ):
                task.run(worker_context)

    def test_run_email_server_disabled(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
    ) -> None:
        """Test run raises ValueError when email server is disabled."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        disabled_config = EmailServerConfig(
            id=1,
            server_type=EmailServerType.SMTP,
            enabled=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService"
            ) as mock_email_config_service,
        ):
            mock_email_config_service.return_value.get_config.return_value = (
                disabled_config
            )

            with pytest.raises(
                ValueError, match="email_server_not_configured_or_disabled"
            ):
                task.run(worker_context)

    @pytest.mark.parametrize(
        ("progress_value", "cancelled_after"),
        [
            (0.1, False),  # Not cancelled
            (0.2, True),  # Cancelled after library found
            (0.3, True),  # Cancelled after email service ready
            (0.4, True),  # Cancelled after book service ready
        ],
    )
    def test_run_cancelled_at_different_stages(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
        mock_email_config_service: MagicMock,
        progress_value: float,
        cancelled_after: bool,
    ) -> None:
        """Test run handles cancellation at different stages."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        update_progress = worker_context["update_progress"]

        def cancel_after_progress(progress: float) -> None:
            """Cancel task after specific progress value."""
            if progress == progress_value:
                task.mark_cancelled()

        update_progress.side_effect = cancel_after_progress

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService",
                return_value=mock_email_config_service,
            ),
            patch("fundamental.services.tasks.email_send_task.EmailService"),
            patch(
                "fundamental.services.tasks.email_send_task.BookService"
            ) as mock_book_service,
        ):
            task.run(worker_context)

            # If cancelled early, book service should not be called
            if cancelled_after:
                mock_book_service.return_value.send_book.assert_not_called()

    def test_run_email_service_error(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
        mock_email_config_service: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test run raises EmailServiceError when email service fails."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        mock_book_service.send_book.side_effect = EmailServiceError("Email send failed")

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService",
                return_value=mock_email_config_service,
            ),
            patch("fundamental.services.tasks.email_send_task.EmailService"),
            patch(
                "fundamental.services.tasks.email_send_task.BookService",
                return_value=mock_book_service,
            ),
            pytest.raises(EmailServiceError, match="Email send failed"),
        ):
            task.run(worker_context)

    def test_run_generic_exception(
        self,
        base_metadata: dict[str, object],
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
        mock_email_config_service: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test run raises generic Exception when unexpected error occurs."""
        task = EmailSendTask(task_id=1, user_id=1, metadata=base_metadata)

        mock_book_service.send_book.side_effect = RuntimeError("Unexpected error")

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService",
                return_value=mock_email_config_service,
            ),
            patch("fundamental.services.tasks.email_send_task.EmailService"),
            patch(
                "fundamental.services.tasks.email_send_task.BookService",
                return_value=mock_book_service,
            ),
            pytest.raises(RuntimeError, match="Unexpected error"),
        ):
            task.run(worker_context)

    def test_run_with_none_email_and_format(
        self,
        worker_context: dict[str, MagicMock],
        mock_library_service: MagicMock,
        mock_email_config_service: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test run handles None email and format."""
        metadata = {
            "book_id": 1,
            "encryption_key": "test-key",
        }
        task = EmailSendTask(task_id=1, user_id=1, metadata=metadata)

        with (
            patch("fundamental.services.tasks.email_send_task.LibraryRepository"),
            patch(
                "fundamental.services.tasks.email_send_task.LibraryService",
                return_value=mock_library_service,
            ),
            patch("fundamental.services.tasks.email_send_task.DataEncryptor"),
            patch(
                "fundamental.services.tasks.email_send_task.EmailConfigService",
                return_value=mock_email_config_service,
            ),
            patch("fundamental.services.tasks.email_send_task.EmailService"),
            patch(
                "fundamental.services.tasks.email_send_task.BookService",
                return_value=mock_book_service,
            ),
        ):
            task.run(worker_context)

        # Verify book service was called with None values
        mock_book_service.send_book.assert_called_once()
        call_kwargs = mock_book_service.send_book.call_args[1]
        assert call_kwargs["book_id"] == 1
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["to_email"] is None
        assert call_kwargs["file_format"] is None

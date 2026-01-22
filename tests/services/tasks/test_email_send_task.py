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
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest

from bookcard.models.config import EmailServerConfig, EmailServerType, Library
from bookcard.models.core import Book
from bookcard.repositories import BookWithFullRelations
from bookcard.services.email_service import EmailService, EmailServiceError
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.email_send import EmailSendTask
from bookcard.services.tasks.email_send.dependencies import EmailSendDependencies
from bookcard.services.tasks.exceptions import (
    EmailServerNotConfiguredError,
    LibraryNotConfiguredError,
)

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def worker_context(session: DummySession) -> WorkerContext:
    """Create worker context for task execution."""
    return WorkerContext(
        session=session,  # type: ignore[arg-type]
        task_service=MagicMock(),
        update_progress=MagicMock(),
    )


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


@pytest.fixture
def book_with_rels() -> BookWithFullRelations:
    """Create a test book with relations."""
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Test Author",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    return BookWithFullRelations(
        book=book,
        authors=["Test Author"],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[{"format": "EPUB", "size": 1000, "name": "test"}],
    )


@pytest.fixture
def mock_dependencies(
    library: Library,
    email_config: EmailServerConfig,
    book_with_rels: BookWithFullRelations,
) -> EmailSendDependencies:
    """Create mock dependencies for EmailSendTask."""
    # Mock library provider
    library_provider = MagicMock()
    library_provider.get_active_library.return_value = library

    # Mock email service factory
    email_service = EmailService(email_config)
    email_service_factory = MagicMock()
    email_service_factory.create.return_value = email_service

    # Mock book service
    book_service = MagicMock()
    book_service.get_book_full.return_value = book_with_rels
    book_service.send_book.return_value = None

    # Mock book service factory
    book_service_factory = MagicMock()
    book_service_factory.create.return_value = book_service

    # Mock preparation service
    from bookcard.services.tasks.email_send.domain import SendPreparation

    preparation = SendPreparation(
        book_title="Test Book",
        attachment_filename="Test_Author_-_Test_Book.epub",
        resolved_format="EPUB",
        book_with_rels=book_with_rels,
    )
    preparation_service = MagicMock()
    preparation_service.prepare.return_value = preparation

    # Mock preprocessing pipeline
    preprocessing_pipeline = MagicMock()
    preprocessing_pipeline.execute.return_value = None

    return EmailSendDependencies(
        library_provider=library_provider,
        email_service_factory=email_service_factory,
        book_service_factory=book_service_factory,
        preparation_service=preparation_service,
        preprocessing_pipeline=preprocessing_pipeline,
    )


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
        assert task._request.book_id.value == 1
        assert task._request.email_target.address == "test@example.com"
        assert task._request.file_format.value == "EPUB"
        assert task._request.encryption_key.value == "test-key"

    def test_init_optional_fields(self) -> None:
        """Test __init__ handles optional fields."""
        metadata = {
            "book_id": 1,
            "encryption_key": "test-key",
        }
        task = EmailSendTask(task_id=1, user_id=1, metadata=metadata)
        assert task._request.book_id.value == 1
        assert task._request.email_target.address is None
        assert task._request.file_format.value is None
        assert task._request.encryption_key.value == "test-key"


class TestEmailSendTaskRun:
    """Test EmailSendTask.run method."""

    def test_run_success(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run completes successfully."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )

        task.run(worker_context)

        # Verify progress updates (6 steps: library, email, book, prepare, preprocess, send)
        assert worker_context.update_progress.call_count == 6

        # Verify library provider was called
        library_provider = cast("MagicMock", mock_dependencies.library_provider)
        library_provider.get_active_library.assert_called_once()

        # Verify email service factory was called
        email_service_factory = cast(
            "MagicMock", mock_dependencies.email_service_factory
        )
        email_service_factory.create.assert_called_once()

        # Verify book service factory was called
        book_service_factory = cast("MagicMock", mock_dependencies.book_service_factory)
        book_service_factory.create.assert_called_once()

        # Verify preparation service was called
        preparation_service = cast("MagicMock", mock_dependencies.preparation_service)
        preparation_service.prepare.assert_called_once()

        # Verify preprocessing pipeline was called
        preprocessing_pipeline = cast(
            "MagicMock", mock_dependencies.preprocessing_pipeline
        )
        preprocessing_pipeline.execute.assert_called_once()

        # Verify book service send_book was called
        book_service = book_service_factory.create.return_value
        book_service.send_book.assert_called_once()
        call_kwargs = book_service.send_book.call_args[1]
        assert call_kwargs["book_id"] == 1
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["to_email"] == "test@example.com"
        assert call_kwargs["file_format"] == "EPUB"

        # Verify metadata was set
        assert task.metadata["book_title"] == "Test Book"
        assert task.metadata["attachment_filename"] == "Test_Author_-_Test_Book.epub"

    def test_run_cancelled_before_processing(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run handles cancellation before processing."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )
        task.mark_cancelled()

        task.run(worker_context)

        # Should log cancellation but not raise
        worker_context.update_progress.assert_not_called()

    def test_run_no_library_configured(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run raises LibraryNotConfiguredError when no library configured."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )

        library_provider = cast("MagicMock", mock_dependencies.library_provider)
        library_provider.get_active_library.side_effect = LibraryNotConfiguredError

        with pytest.raises(LibraryNotConfiguredError):
            task.run(worker_context)

    def test_run_email_server_not_configured(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run raises EmailServerNotConfiguredError when email server not configured."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )

        email_service_factory = cast(
            "MagicMock", mock_dependencies.email_service_factory
        )
        email_service_factory.create.side_effect = EmailServerNotConfiguredError

        with pytest.raises(EmailServerNotConfiguredError):
            task.run(worker_context)

    def test_run_email_service_error(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run raises EmailServiceError when email service fails."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )

        book_service_factory = cast("MagicMock", mock_dependencies.book_service_factory)
        book_service = book_service_factory.create.return_value
        book_service.send_book.side_effect = EmailServiceError("Email send failed")

        with pytest.raises(EmailServiceError, match="Email send failed"):
            task.run(worker_context)

    def test_run_generic_exception(
        self,
        base_metadata: dict[str, object],
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run raises generic Exception when unexpected error occurs."""
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=base_metadata, dependencies=mock_dependencies
        )

        book_service_factory = cast("MagicMock", mock_dependencies.book_service_factory)
        book_service = book_service_factory.create.return_value
        book_service.send_book.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(RuntimeError, match="Unexpected error"):
            task.run(worker_context)

    def test_run_with_none_email_and_format(
        self,
        worker_context: WorkerContext,
        mock_dependencies: EmailSendDependencies,
    ) -> None:
        """Test run handles None email and format."""
        metadata = {
            "book_id": 1,
            "encryption_key": "test-key",
        }
        task = EmailSendTask(
            task_id=1, user_id=1, metadata=metadata, dependencies=mock_dependencies
        )

        task.run(worker_context)

        # Verify book service was called with expected values
        book_service_factory = cast("MagicMock", mock_dependencies.book_service_factory)
        book_service = book_service_factory.create.return_value
        book_service.send_book.assert_called_once()
        call_kwargs = book_service.send_book.call_args[1]
        assert call_kwargs["book_id"] == 1
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["to_email"] is None
        # Format is resolved by preparation service
        assert call_kwargs["file_format"] == "EPUB"

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

"""Tests for EmailSendTask preprocessing pipelines."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import EPUBFixerConfig, Library
from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.repositories import BookWithFullRelations
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.email_send import EmailSendTask
from bookcard.services.tasks.email_send.dependencies import EmailSendDependencies
from bookcard.services.tasks.email_send.preprocessing import (
    PreprocessingContext,
    PreprocessingPipeline,
)
from bookcard.services.tasks.exceptions import TaskCancelledError

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
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
        auto_metadata_enforcement=True,
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


class TestPreprocessingPipeline:
    """Test preprocessing pipeline directly."""

    def test_epub_fix_enabled_and_runs(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
        session: DummySession,
    ) -> None:
        """Test EPUB fix runs when enabled and format is EPUB."""
        # Setup EPUB fixer config
        epub_config = EPUBFixerConfig(id=1, enabled=True)
        session.add_exec_result([epub_config])

        # Mock Calibre DB query for EPUB format
        mock_calibre_repo = MagicMock()
        mock_calibre_session = MagicMock()
        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            mock_calibre_session
        )
        mock_calibre_session.exec.return_value.first.return_value = (
            book_with_rels.book,
            Data(book=1, format="EPUB", uncompressed_size=1000, name="test"),
        )

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        with (
            patch(
                "bookcard.services.tasks.email_send.preprocessing.CalibreBookRepository",
                return_value=mock_calibre_repo,
            ),
            patch(
                "bookcard.services.tasks.email_send.preprocessing.LibraryPathResolver"
            ) as mock_resolver,
            patch(
                "bookcard.services.tasks.email_send.preprocessing.EPUBFixerService"
            ) as mock_fixer_service,
        ):
            mock_resolver.return_value.get_book_file_path.return_value = "/path/to/epub"
            mock_fixer_service.return_value.process_epub_file.return_value = MagicMock(
                id=1
            )

            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            # Verify fix was executed
            mock_fixer_service.return_value.process_epub_file.assert_called_once()
            call_kwargs = mock_fixer_service.return_value.process_epub_file.call_args[1]
            assert call_kwargs["book_id"] == 1
            assert call_kwargs["file_path"] == "/path/to/epub"

    def test_epub_fix_disabled_globally(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
        session: DummySession,
    ) -> None:
        """Test EPUB fix skipped when disabled globally."""
        # Setup EPUB fixer config (disabled)
        epub_config = EPUBFixerConfig(id=1, enabled=False)
        session.add_exec_result([epub_config])

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        with patch(
            "bookcard.services.tasks.email_send.preprocessing.EPUBFixerService"
        ) as mock_fixer:
            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            mock_fixer.return_value.process_epub_file.assert_not_called()

    def test_epub_fix_skipped_non_epub(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
    ) -> None:
        """Test EPUB fix skipped when format is not EPUB."""

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="MOBI",
            check_cancellation=check_cancellation,
        )

        with patch(
            "bookcard.services.tasks.email_send.preprocessing.EPUBFixerService"
        ) as mock_fixer:
            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            mock_fixer.return_value.process_epub_file.assert_not_called()

    def test_metadata_enforcement_runs(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
    ) -> None:
        """Test metadata enforcement runs when enabled."""
        library.auto_metadata_enforcement = True

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        with patch(
            "bookcard.services.tasks.email_send.preprocessing.MetadataEnforcementTriggerService"
        ) as mock_trigger:
            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            mock_trigger.return_value.trigger_enforcement_if_enabled.assert_called_once_with(
                book_id=1,
                book_with_rels=book_with_rels,
                user_id=1,
            )

    def test_metadata_enforcement_disabled(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
    ) -> None:
        """Test metadata enforcement skipped when disabled."""
        library.auto_metadata_enforcement = False

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        with patch(
            "bookcard.services.tasks.email_send.preprocessing.MetadataEnforcementTriggerService"
        ) as mock_trigger:
            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            mock_trigger.return_value.trigger_enforcement_if_enabled.assert_not_called()

    def test_preprocessing_graceful_failure(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
        session: DummySession,
    ) -> None:
        """Test preprocessing continues on error."""
        # Enable EPUB fix
        epub_config = EPUBFixerConfig(id=1, enabled=True)
        session.add_exec_result([epub_config])

        def check_cancellation() -> None:
            """No-op cancellation check."""

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        # Mock Calibre repo to raise error
        with (
            patch(
                "bookcard.services.tasks.email_send.preprocessing.CalibreBookRepository",
                side_effect=Exception("DB Error"),
            ),
            patch(
                "bookcard.services.tasks.email_send.preprocessing.MetadataEnforcementTriggerService"
            ) as mock_trigger,
        ):
            # Should not raise exception
            pipeline = PreprocessingPipeline.default()
            pipeline.execute(context)

            # Metadata enforcement should still run
            mock_trigger.return_value.trigger_enforcement_if_enabled.assert_called_once()

    def test_cancellation_during_preprocessing(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
    ) -> None:
        """Test cancellation check during preprocessing."""
        cancelled = False

        def check_cancellation() -> None:
            """Raise cancellation error."""
            nonlocal cancelled
            if cancelled:
                raise TaskCancelledError(1)

        context = PreprocessingContext(
            session=worker_context.session,
            library=library,
            book_with_rels=book_with_rels,
            book_id=1,
            user_id=1,
            resolved_format="EPUB",
            check_cancellation=check_cancellation,
        )

        cancelled = True

        pipeline = PreprocessingPipeline.default()
        with pytest.raises(TaskCancelledError):
            pipeline.execute(context)


class TestEmailSendTaskPreprocessing:
    """Test EmailSendTask with preprocessing through full execution."""

    def test_preprocessing_runs_during_execution(
        self,
        worker_context: WorkerContext,
        library: Library,
        book_with_rels: BookWithFullRelations,
        session: DummySession,
    ) -> None:
        """Test preprocessing runs during full task execution."""
        # Setup EPUB fixer config
        epub_config = EPUBFixerConfig(id=1, enabled=True)
        session.add_exec_result([epub_config])

        # Create mock dependencies
        library_provider = MagicMock()
        library_provider.get_active_library.return_value = library

        email_service = MagicMock()
        email_service_factory = MagicMock()
        email_service_factory.create.return_value = email_service

        book_service = MagicMock()
        book_service.get_book_full.return_value = book_with_rels
        book_service.send_book.return_value = None

        book_service_factory = MagicMock()
        book_service_factory.create.return_value = book_service

        from bookcard.services.tasks.email_send.domain import SendPreparation

        preparation = SendPreparation(
            book_title="Test Book",
            attachment_filename="test.epub",
            resolved_format="EPUB",
            book_with_rels=book_with_rels,
        )
        preparation_service = MagicMock()
        preparation_service.prepare.return_value = preparation

        # Use real pipeline to test integration
        preprocessing_pipeline = PreprocessingPipeline.default()

        dependencies = EmailSendDependencies(
            library_provider=library_provider,
            email_service_factory=email_service_factory,
            book_service_factory=book_service_factory,
            preparation_service=preparation_service,
            preprocessing_pipeline=preprocessing_pipeline,
        )

        task = EmailSendTask(
            task_id=1,
            user_id=1,
            metadata={
                "book_id": 1,
                "encryption_key": "key",
                "to_email": "test@example.com",
            },
            dependencies=dependencies,
        )

        # Mock Calibre repository and services
        with (
            patch(
                "bookcard.services.tasks.email_send.preprocessing.CalibreBookRepository"
            ) as mock_calibre_repo,
            patch(
                "bookcard.services.tasks.email_send.preprocessing.LibraryPathResolver"
            ) as mock_resolver,
            patch(
                "bookcard.services.tasks.email_send.preprocessing.EPUBFixerService"
            ) as mock_fixer,
            patch(
                "bookcard.services.tasks.email_send.preprocessing.MetadataEnforcementTriggerService"
            ) as mock_trigger,
        ):
            mock_calibre_session = MagicMock()
            mock_calibre_repo.return_value.get_session.return_value.__enter__.return_value = mock_calibre_session
            mock_calibre_session.exec.return_value.first.return_value = (
                book_with_rels.book,
                Data(book=1, format="EPUB", uncompressed_size=1000, name="test"),
            )
            mock_resolver.return_value.get_book_file_path.return_value = "/path/to/epub"
            mock_fixer.return_value.process_epub_file.return_value = MagicMock(id=1)

            task.run(worker_context)

            # Verify preprocessing was executed
            mock_fixer.return_value.process_epub_file.assert_called_once()
            mock_trigger.return_value.trigger_enforcement_if_enabled.assert_called_once()

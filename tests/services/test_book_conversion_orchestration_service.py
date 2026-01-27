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

"""Tests for BookConversionOrchestrationService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.models.conversion import (
    BookConversion,
    ConversionStatus,
)
from bookcard.models.tasks import TaskType
from bookcard.services.book_conversion_orchestration_service import (
    BookConversionOrchestrationService,
    ConversionListResult,
)
from bookcard.services.book_service import BookService
from bookcard.services.tasks.base import TaskRunner

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/path/metadata.db",
        library_root="/test/path",
    )


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock BookService."""
    return MagicMock(spec=BookService)


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock TaskRunner."""
    runner = MagicMock(spec=TaskRunner)
    runner.enqueue.return_value = 123
    return runner


@pytest.fixture
def mock_book_with_formats() -> MagicMock:
    """Create a mock book with formats."""
    book = MagicMock()
    book.formats = [
        {"format": "MOBI"},
        {"format": "EPUB"},
    ]
    return book


@pytest.fixture
def mock_conversion_service() -> MagicMock:
    """Create a mock conversion service."""
    service = MagicMock()
    service.check_existing_conversion.return_value = None
    return service


@pytest.fixture
def orchestration_service(
    session: DummySession,
    library: Library,
    mock_book_service: MagicMock,
    mock_task_runner: MagicMock,
    mock_conversion_service: MagicMock,
) -> BookConversionOrchestrationService:
    """Create BookConversionOrchestrationService instance."""
    with patch(
        "bookcard.services.book_conversion_orchestration_service.create_conversion_service"
    ) as mock_create:
        mock_create.return_value = mock_conversion_service
        return BookConversionOrchestrationService(
            session=session,  # type: ignore[arg-type]
            book_service=mock_book_service,
            library=library,
            task_runner=mock_task_runner,
        )


class TestInit:
    """Test __init__ method."""

    def test_init_with_task_runner(
        self,
        session: DummySession,
        library: Library,
        mock_book_service: MagicMock,
        mock_task_runner: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initialization with task runner (covers lines 117-121)."""
        with patch(
            "bookcard.services.book_conversion_orchestration_service.create_conversion_service"
        ) as mock_create:
            mock_create.return_value = mock_conversion_service
            service = BookConversionOrchestrationService(
                session=session,  # type: ignore[arg-type]
                book_service=mock_book_service,
                library=library,
                task_runner=mock_task_runner,
            )

            assert service._session == session
            assert service._book_service == mock_book_service
            assert service._library == library
            assert service._task_runner == mock_task_runner
            assert service._conversion_service is not None

    def test_init_without_task_runner(
        self,
        session: DummySession,
        library: Library,
        mock_book_service: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initialization without task runner."""
        with patch(
            "bookcard.services.book_conversion_orchestration_service.create_conversion_service"
        ) as mock_create:
            mock_create.return_value = mock_conversion_service
            service = BookConversionOrchestrationService(
                session=session,  # type: ignore[arg-type]
                book_service=mock_book_service,
                library=library,
                task_runner=None,
            )

            assert service._task_runner is None


class TestInitiateConversion:
    """Test initiate_conversion method."""

    def test_initiate_conversion_book_not_found(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
    ) -> None:
        """Test initiate_conversion when book not found (covers lines 159-162)."""
        mock_book_service.get_book_full.return_value = None

        with pytest.raises(ValueError, match="book_not_found"):
            orchestration_service.initiate_conversion(
                book_id=1,
                source_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

    def test_initiate_conversion_existing_completed(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initiate_conversion with existing completed conversion (covers lines 165-186)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats

        existing_conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            original_file_path="/test/path.mobi",
            converted_file_path="/test/path.epub",
            status=ConversionStatus.COMPLETED,
            completed_at=datetime.now(UTC),
        )

        mock_conversion_service.check_existing_conversion.return_value = (
            existing_conversion
        )

        result = orchestration_service.initiate_conversion(
            book_id=1,
            source_format="MOBI",
            target_format="EPUB",
            user_id=1,
        )

        assert result.task_id == 0
        assert result.existing_conversion == existing_conversion
        assert result.message is not None
        assert "already been converted" in result.message

    def test_initiate_conversion_existing_no_completed_at(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initiate_conversion with existing conversion without completed_at (covers lines 173-177)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats

        existing_conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            original_file_path="/test/path.mobi",
            converted_file_path="/test/path.epub",
            status=ConversionStatus.COMPLETED,
            completed_at=None,
        )

        mock_conversion_service.check_existing_conversion.return_value = (
            existing_conversion
        )

        result = orchestration_service.initiate_conversion(
            book_id=1,
            source_format="MOBI",
            target_format="EPUB",
            user_id=1,
        )

        assert result.task_id == 0
        assert result.message is not None
        assert "previously" in result.message

    def test_initiate_conversion_source_format_not_found(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initiate_conversion when source format not found (covers lines 189-197)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats
        mock_conversion_service.check_existing_conversion.return_value = None

        with pytest.raises(ValueError, match="source_format_not_found"):
            orchestration_service.initiate_conversion(
                book_id=1,
                source_format="AZW3",
                target_format="EPUB",
                user_id=1,
            )

    def test_initiate_conversion_target_format_exists(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initiate_conversion when target format already exists (covers lines 199-213)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats
        mock_conversion_service.check_existing_conversion.return_value = None

        result = orchestration_service.initiate_conversion(
            book_id=1,
            source_format="MOBI",
            target_format="EPUB",
            user_id=1,
        )

        assert result.task_id == 0
        assert result.existing_conversion is None
        assert result.message is not None
        assert "already has the" in result.message

    def test_initiate_conversion_task_runner_unavailable(
        self,
        session: DummySession,
        library: Library,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test initiate_conversion when task runner unavailable (covers lines 216-218)."""
        with patch(
            "bookcard.services.book_conversion_orchestration_service.create_conversion_service"
        ) as mock_create:
            mock_create.return_value = mock_conversion_service
            service = BookConversionOrchestrationService(
                session=session,  # type: ignore[arg-type]
                book_service=mock_book_service,
                library=library,
                task_runner=None,
            )

            mock_book_service.get_book_full.return_value = mock_book_with_formats
            mock_conversion_service.check_existing_conversion.return_value = None
            mock_book_with_formats.formats = [{"format": "MOBI"}]

        with pytest.raises(RuntimeError, match="Task runner not available"):
            service.initiate_conversion(
                book_id=1,
                source_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

    def test_initiate_conversion_success(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
        mock_task_runner: MagicMock,
        mock_conversion_service: MagicMock,
    ) -> None:
        """Test successful initiate_conversion (covers lines 221-238)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats
        mock_conversion_service.check_existing_conversion.return_value = None
        mock_book_with_formats.formats = [{"format": "MOBI"}]
        mock_task_runner.enqueue.return_value = 123

        result = orchestration_service.initiate_conversion(
            book_id=1,
            source_format="MOBI",
            target_format="EPUB",
            user_id=1,
        )

        assert result.task_id == 123
        assert result.existing_conversion is None
        assert result.message is None

        mock_task_runner.enqueue.assert_called_once_with(
            task_type=TaskType.BOOK_CONVERT,
            payload={
                "book_id": 1,
                "source_format": "MOBI",
                "target_format": "EPUB",
            },
            user_id=1,
            metadata={
                "task_type": TaskType.BOOK_CONVERT,
                "book_id": 1,
                "source_format": "MOBI",
                "target_format": "EPUB",
                "conversion_method": "manual",
            },
        )


class TestGetConversions:
    """Test get_conversions method."""

    def test_get_conversions_book_not_found(
        self,
        orchestration_service: BookConversionOrchestrationService,
        mock_book_service: MagicMock,
    ) -> None:
        """Test get_conversions when book not found (covers lines 268-271)."""
        mock_book_service.get_book_full.return_value = None

        with pytest.raises(ValueError, match="book_not_found"):
            orchestration_service.get_conversions(
                book_id=1,
                page=1,
                page_size=10,
            )

    def test_get_conversions_success(
        self,
        orchestration_service: BookConversionOrchestrationService,
        session: DummySession,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
    ) -> None:
        """Test successful get_conversions (covers lines 273-299)."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats

        conversions = [
            BookConversion(
                id=1,
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                original_file_path="/test/path.mobi",
                converted_file_path="/test/path.epub",
                status=ConversionStatus.COMPLETED,
            ),
            BookConversion(
                id=2,
                book_id=1,
                original_format="AZW3",
                target_format="EPUB",
                original_file_path="/test/path.azw3",
                converted_file_path="/test/path2.epub",
                status=ConversionStatus.COMPLETED,
            ),
        ]

        session._exec_results = [conversions, conversions]

        result = orchestration_service.get_conversions(
            book_id=1,
            page=1,
            page_size=10,
        )

        assert isinstance(result, ConversionListResult)
        assert len(result.conversions) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1

    def test_get_conversions_pagination(
        self,
        orchestration_service: BookConversionOrchestrationService,
        session: DummySession,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
    ) -> None:
        """Test get_conversions with pagination."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats

        all_conversions = [
            BookConversion(
                id=i,
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                original_file_path=f"/test/path{i}.mobi",
                converted_file_path=f"/test/path{i}.epub",
                status=ConversionStatus.COMPLETED,
            )
            for i in range(1, 26)
        ]

        session._exec_results = [all_conversions, all_conversions[:10]]

        result = orchestration_service.get_conversions(
            book_id=1,
            page=1,
            page_size=10,
        )

        assert len(result.conversions) == 10
        assert result.total == 25
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 3

    def test_get_conversions_empty(
        self,
        orchestration_service: BookConversionOrchestrationService,
        session: DummySession,
        mock_book_service: MagicMock,
        mock_book_with_formats: MagicMock,
    ) -> None:
        """Test get_conversions with no conversions."""
        mock_book_service.get_book_full.return_value = mock_book_with_formats

        session._exec_results = [[], []]

        result = orchestration_service.get_conversions(
            book_id=1,
            page=1,
            page_size=10,
        )

        assert len(result.conversions) == 0
        assert result.total == 0
        assert result.total_pages == 0

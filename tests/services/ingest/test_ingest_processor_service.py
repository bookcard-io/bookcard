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

"""Tests for ingest processor service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from fundamental.models.config import Library
from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.models.metadata import MetadataRecord
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.repositories.ingest_repository import (
    IngestAuditRepository,
    IngestHistoryRepository,
)
from fundamental.services.author_exceptions import NoActiveLibraryError
from fundamental.services.book_service import BookService
from fundamental.services.ingest.exceptions import (
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)
from fundamental.services.ingest.file_discovery_service import FileGroup
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_processor_service import IngestProcessorService
from fundamental.services.ingest.metadata_extraction import ExtractedMetadata
from fundamental.services.ingest.metadata_fetch_service import MetadataFetchService
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a dummy database session."""
    return DummySession()


@pytest.fixture
def mock_config_service() -> MagicMock:
    """Create a mock IngestConfigService."""
    service = MagicMock(spec=IngestConfigService)
    service.get_enabled_providers.return_value = ["openlibrary", "google"]
    service.get_merge_strategy.return_value = "merge_best"
    return service


@pytest.fixture
def mock_history_repo() -> MagicMock:
    """Create a mock IngestHistoryRepository."""
    return MagicMock(spec=IngestHistoryRepository)


@pytest.fixture
def mock_audit_repo() -> MagicMock:
    """Create a mock IngestAuditRepository."""
    return MagicMock(spec=IngestAuditRepository)


@pytest.fixture
def mock_library_repo() -> MagicMock:
    """Create a mock LibraryRepository."""
    repo = MagicMock(spec=LibraryRepository)
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )
    repo.get_active.return_value = library
    return repo


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock BookService."""
    service = MagicMock(spec=BookService)
    service.add_book.return_value = 123
    return service


@pytest.fixture
def mock_book_service_factory(
    mock_book_service: MagicMock,
) -> MagicMock:
    """Create a mock book service factory."""

    def factory(library: Library) -> BookService:
        return mock_book_service

    return factory  # type: ignore[return-value]


@pytest.fixture
def mock_metadata_fetch_service() -> MagicMock:
    """Create a mock MetadataFetchService."""
    return MagicMock(spec=MetadataFetchService)


@pytest.fixture
def service(
    session: DummySession,
    mock_config_service: MagicMock,
    mock_history_repo: MagicMock,
    mock_audit_repo: MagicMock,
    mock_library_repo: MagicMock,
    mock_book_service_factory: MagicMock,
    mock_metadata_fetch_service: MagicMock,
) -> IngestProcessorService:
    """Create IngestProcessorService with mocked dependencies."""
    return IngestProcessorService(
        session=session,  # type: ignore[valid-type]
        config_service=mock_config_service,
        history_repo=mock_history_repo,
        audit_repo=mock_audit_repo,
        library_repo=mock_library_repo,
        book_service_factory=mock_book_service_factory,
        metadata_fetch_service=mock_metadata_fetch_service,
    )


@pytest.fixture
def service_defaults(session: DummySession) -> IngestProcessorService:
    """Create IngestProcessorService with default dependencies."""
    return IngestProcessorService(session=session)  # type: ignore[valid-type]


@pytest.fixture
def file_group(temp_dir: Path) -> FileGroup:
    """Create a FileGroup instance."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    return FileGroup(
        book_key="test_book",
        files=[file_path],
        metadata_hint={"title": "Test Book", "authors": ["Test Author"]},
    )


@pytest.fixture
def file_group_empty(temp_dir: Path) -> FileGroup:
    """Create a FileGroup with no files."""
    return FileGroup(
        book_key="empty_book",
        files=[],
        metadata_hint={},
    )


@pytest.fixture
def ingest_history() -> IngestHistory:
    """Create an IngestHistory instance."""
    return IngestHistory(
        id=1,
        file_path="/tmp/book.epub",
        status=IngestStatus.PENDING,
        ingest_metadata={
            "book_key": "test_book",
            "file_count": 1,
            "files": ["/tmp/book.epub"],
        },
    )


@pytest.fixture
def metadata_record() -> MetadataRecord:
    """Create a MetadataRecord instance."""
    return MetadataRecord(
        source_id="openlibrary",
        external_id="OL123456",
        title="Test Book",
        authors=["Test Author"],
        url="https://example.com/book",
        description="A test book",
        cover_url="https://example.com/cover.jpg",
        series="Test Series",
        series_index=1,
        publisher="Test Publisher",
        published_date="2020-01-01",
        identifiers={"isbn": "1234567890"},
    )


class TestInit:
    """Test IngestProcessorService initialization."""

    def test_init_with_all_deps(
        self,
        session: DummySession,
        mock_config_service: MagicMock,
        mock_history_repo: MagicMock,
        mock_audit_repo: MagicMock,
        mock_library_repo: MagicMock,
        mock_book_service_factory: MagicMock,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test initialization with all dependencies provided."""
        service = IngestProcessorService(
            session=session,  # type: ignore[valid-type]
            config_service=mock_config_service,
            history_repo=mock_history_repo,
            audit_repo=mock_audit_repo,
            library_repo=mock_library_repo,
            book_service_factory=mock_book_service_factory,
            metadata_fetch_service=mock_metadata_fetch_service,
        )
        assert service._session == session
        assert service._config_service == mock_config_service
        assert service._history_repo == mock_history_repo
        assert service._audit_repo == mock_audit_repo
        assert service._library_repo == mock_library_repo
        assert service._book_service_factory == mock_book_service_factory
        assert service._metadata_fetch_service == mock_metadata_fetch_service

    def test_init_with_defaults(self, session: DummySession) -> None:
        """Test initialization with default dependencies."""
        service = IngestProcessorService(session=session)  # type: ignore[valid-type]
        assert service._session == session
        assert isinstance(service._config_service, IngestConfigService)
        assert isinstance(service._history_repo, IngestHistoryRepository)
        assert isinstance(service._audit_repo, IngestAuditRepository)
        assert isinstance(service._library_repo, LibraryRepository)
        assert callable(service._book_service_factory)
        assert service._metadata_fetch_service is None


class TestProcessFileGroup:
    """Test process_file_group method."""

    def test_process_file_group_success(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
        mock_history_repo: MagicMock,
        mock_audit_repo: MagicMock,
    ) -> None:
        """Test successful file group processing."""

        def mock_refresh(history: IngestHistory) -> None:
            if history.id is None:
                history.id = 1

        service._session.refresh = mock_refresh  # type: ignore[assignment]
        mock_history_repo.add.return_value = None

        history_id = service.process_file_group(file_group, user_id=42)

        assert history_id == 1
        mock_history_repo.add.assert_called_once()
        mock_audit_repo.log_action.assert_called_once()
        assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_process_file_group_with_user_id(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
    ) -> None:
        """Test file group processing with user ID."""

        def mock_refresh(history: IngestHistory) -> None:
            if history.id is None:
                history.id = 1

        service._session.refresh = mock_refresh  # type: ignore[assignment]

        history_id = service.process_file_group(file_group, user_id=99)

        assert history_id == 1

    def test_process_file_group_empty_files(
        self,
        service: IngestProcessorService,
        file_group_empty: FileGroup,
    ) -> None:
        """Test file group processing with empty files."""

        def mock_refresh(history: IngestHistory) -> None:
            if history.id is None:
                history.id = 1

        service._session.refresh = mock_refresh  # type: ignore[assignment]

        history_id = service.process_file_group(file_group_empty)

        assert history_id == 1

    def test_process_file_group_creation_error(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
    ) -> None:
        """Test file group processing with creation error."""
        history = IngestHistory(
            id=None,  # Simulate creation failure
            file_path=str(file_group.files[0]),
            status=IngestStatus.PENDING,
        )
        service._session.add(history)
        # Don't flush to simulate creation failure

        with pytest.raises(IngestHistoryCreationError):
            service.process_file_group(file_group)


class TestFetchAndStoreMetadata:
    """Test fetch_and_store_metadata method."""

    def test_fetch_and_store_metadata_success(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
        mock_history_repo: MagicMock,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test successful metadata fetch and store."""
        mock_history_repo.get.return_value = ingest_history
        mock_metadata_fetch_service.fetch_metadata.return_value = metadata_record

        result = service.fetch_and_store_metadata(
            history_id=1, metadata_hint={"title": "Hint"}
        )

        assert result is not None
        assert result["title"] == "Test Book"
        assert result["authors"] == ["Test Author"]
        mock_metadata_fetch_service.fetch_metadata.assert_called_once()
        assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_fetch_and_store_metadata_no_hint(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
        mock_history_repo: MagicMock,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test metadata fetch without hint."""
        mock_history_repo.get.return_value = ingest_history
        mock_metadata_fetch_service.fetch_metadata.return_value = metadata_record

        result = service.fetch_and_store_metadata(history_id=1)

        assert result is not None

    def test_fetch_and_store_metadata_not_found(
        self,
        service: IngestProcessorService,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test metadata fetch when history not found."""
        mock_history_repo.get.return_value = None

        with pytest.raises(IngestHistoryNotFoundError):
            service.fetch_and_store_metadata(history_id=999)

    def test_fetch_and_store_metadata_no_result(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test metadata fetch when no metadata found."""
        mock_history_repo.get.return_value = ingest_history
        mock_metadata_fetch_service.fetch_metadata.return_value = None

        result = service.fetch_and_store_metadata(history_id=1)

        assert result is None

    def test_fetch_and_store_metadata_creates_service(
        self,
        service_defaults: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
        mock_config_service: MagicMock,
    ) -> None:
        """Test metadata fetch creates service when None."""
        service_defaults._config_service = mock_config_service
        # Mock the history repo's get method
        service_defaults._history_repo.get = MagicMock(return_value=ingest_history)  # type: ignore[method-assign]

        with patch(
            "fundamental.services.ingest.ingest_processor_service.MetadataFetchService"
        ) as mock_fetch_class:
            mock_fetch_instance = MagicMock()
            mock_fetch_instance.fetch_metadata.return_value = metadata_record
            mock_fetch_class.create_default.return_value = mock_fetch_instance

            result = service_defaults.fetch_and_store_metadata(history_id=1)

            assert result is not None
            mock_fetch_class.create_default.assert_called_once()
            assert service_defaults._session.commit_count > 0  # type: ignore[attr-defined]

    def test_fetch_and_store_metadata_empty_metadata(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
        mock_history_repo: MagicMock,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test metadata fetch with empty ingest_metadata."""
        ingest_history.ingest_metadata = None
        mock_history_repo.get.return_value = ingest_history
        mock_metadata_fetch_service.fetch_metadata.return_value = metadata_record

        result = service.fetch_and_store_metadata(history_id=1)

        assert result is not None
        assert ingest_history.ingest_metadata is not None
        assert "fetched_metadata" in ingest_history.ingest_metadata


class TestAddBookToLibrary:
    """Test add_book_to_library method."""

    @pytest.mark.parametrize(
        ("title", "author_name", "expected_title", "expected_author"),
        [
            (None, None, "Extracted Title", "Extracted Author"),
            ("Provided Title", None, "Provided Title", "Extracted Author"),
            (None, "Provided Author", "Extracted Title", "Provided Author"),
            ("Provided Title", "Provided Author", "Provided Title", "Provided Author"),
        ],
    )
    def test_add_book_to_library_with_params(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        temp_dir: Path,
        title: str | None,
        author_name: str | None,
        expected_title: str,
        expected_author: str,
        mock_history_repo: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test adding book with various title/author combinations."""
        file_path = temp_dir / "book.epub"
        file_path.touch()
        mock_history_repo.get.return_value = ingest_history
        mock_book_service.add_book.return_value = 456

        with patch(
            "fundamental.services.ingest.ingest_processor_service.extract_metadata"
        ) as mock_extract:
            mock_extract.return_value = ExtractedMetadata(
                title="Extracted Title",
                authors=["Extracted Author"],
            )

            book_id = service.add_book_to_library(
                history_id=1,
                file_path=file_path,
                file_format="epub",
                title=title,
                author_name=author_name,
            )

            assert book_id == 456
            mock_book_service.add_book.assert_called_once_with(
                file_path=file_path,
                file_format="epub",
                title=expected_title,
                author_name=expected_author,
                pubdate=None,
            )

    def test_add_book_to_library_updates_history(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        temp_dir: Path,
        mock_history_repo: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test adding book updates history with book_id."""
        file_path = temp_dir / "book.epub"
        file_path.touch()
        ingest_history.book_id = None
        mock_history_repo.get.return_value = ingest_history
        mock_book_service.add_book.return_value = 789

        with patch(
            "fundamental.services.ingest.ingest_processor_service.extract_metadata"
        ) as mock_extract:
            mock_extract.return_value = ExtractedMetadata(
                title="Test",
                authors=["Author"],
            )

            book_id = service.add_book_to_library(
                history_id=1,
                file_path=file_path,
                file_format="epub",
            )

            assert book_id == 789
            assert ingest_history.book_id == 789
            assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_add_book_to_library_history_has_book_id(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        temp_dir: Path,
        mock_history_repo: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test adding book when history already has book_id."""
        file_path = temp_dir / "book.epub"
        file_path.touch()
        ingest_history.book_id = 999
        mock_history_repo.get.return_value = ingest_history
        mock_book_service.add_book.return_value = 789

        with patch(
            "fundamental.services.ingest.ingest_processor_service.extract_metadata"
        ) as mock_extract:
            mock_extract.return_value = ExtractedMetadata(
                title="Test",
                authors=["Author"],
            )

            book_id = service.add_book_to_library(
                history_id=1,
                file_path=file_path,
                file_format="epub",
            )

            assert book_id == 789
            # book_id should not be updated if already set
            assert ingest_history.book_id == 999

    def test_add_book_to_library_history_not_found(
        self,
        service: IngestProcessorService,
        temp_dir: Path,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test adding book when history not found."""
        file_path = temp_dir / "book.epub"
        file_path.touch()
        mock_history_repo.get.return_value = None

        with pytest.raises(IngestHistoryNotFoundError):
            service.add_book_to_library(
                history_id=999,
                file_path=file_path,
                file_format="epub",
            )

    def test_add_book_to_library_no_active_library(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        temp_dir: Path,
        mock_history_repo: MagicMock,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test adding book when no active library."""
        file_path = temp_dir / "book.epub"
        file_path.touch()
        mock_history_repo.get.return_value = ingest_history
        mock_library_repo.get_active.return_value = None

        with pytest.raises(NoActiveLibraryError):
            service.add_book_to_library(
                history_id=1,
                file_path=file_path,
                file_format="epub",
            )

    def test_add_book_to_library_fallback_title(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        temp_dir: Path,
        mock_history_repo: MagicMock,
        mock_book_service: MagicMock,
    ) -> None:
        """Test adding book with fallback to filename."""
        file_path = temp_dir / "my_book.epub"
        file_path.touch()
        mock_history_repo.get.return_value = ingest_history

        with patch(
            "fundamental.services.ingest.ingest_processor_service.extract_metadata"
        ) as mock_extract:
            mock_extract.return_value = ExtractedMetadata(
                title="my_book",
                authors=[],
            )

            service.add_book_to_library(
                history_id=1,
                file_path=file_path,
                file_format="epub",
            )

            mock_extract.assert_called_once_with(
                ingest_history, fallback_title="my_book"
            )


class TestSetBookCover:
    """Test set_book_cover method."""

    def test_set_book_cover_success(
        self,
        service: IngestProcessorService,
        mock_book_service: MagicMock,
    ) -> None:
        """Test successful cover setting."""
        with patch(
            "fundamental.services.book_cover_service.BookCoverService"
        ) as mock_cover_class:
            mock_cover_service = MagicMock()
            mock_cover_class.return_value = mock_cover_service

            service.set_book_cover(
                book_id=123, cover_url="https://example.com/cover.jpg"
            )

            mock_cover_class.assert_called_once_with(mock_book_service)
            mock_cover_service.save_cover_from_url.assert_called_once_with(
                123, "https://example.com/cover.jpg"
            )

    @pytest.mark.parametrize(
        "exception",
        [
            ValueError("Invalid URL"),
            RuntimeError("Network error"),
            OSError("File error"),
        ],
    )
    def test_set_book_cover_exceptions(
        self,
        service: IngestProcessorService,
        exception: Exception,
        mock_book_service: MagicMock,
    ) -> None:
        """Test cover setting handles exceptions gracefully."""
        with patch(
            "fundamental.services.book_cover_service.BookCoverService"
        ) as mock_cover_class:
            mock_cover_service = MagicMock()
            mock_cover_service.save_cover_from_url.side_effect = exception
            mock_cover_class.return_value = mock_cover_service

            # Should not raise
            service.set_book_cover(
                book_id=123, cover_url="https://example.com/cover.jpg"
            )

            mock_cover_class.assert_called_once_with(mock_book_service)
            mock_cover_service.save_cover_from_url.assert_called_once()

    def test_set_book_cover_no_active_library(
        self,
        service: IngestProcessorService,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test cover setting when no active library."""
        mock_library_repo.get_active.return_value = None

        with pytest.raises(NoActiveLibraryError):
            service.set_book_cover(
                book_id=123, cover_url="https://example.com/cover.jpg"
            )


class TestUpdateHistoryStatus:
    """Test update_history_status method."""

    @pytest.mark.parametrize(
        ("status", "error_message", "should_set_started", "should_set_completed"),
        [
            (IngestStatus.PENDING, None, False, False),
            (IngestStatus.PROCESSING, None, True, False),
            (IngestStatus.PROCESSING, "Error", True, False),
            (IngestStatus.COMPLETED, None, False, True),
            (IngestStatus.FAILED, "Error message", False, True),
        ],
    )
    def test_update_history_status(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        status: IngestStatus,
        error_message: str | None,
        should_set_started: bool,
        should_set_completed: bool,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test updating history status with various statuses."""
        ingest_history.started_at = None
        ingest_history.completed_at = None
        mock_history_repo.get.return_value = ingest_history

        service.update_history_status(
            history_id=1,
            status=status,
            error_message=error_message,
        )

        assert ingest_history.status == status
        if error_message:
            assert ingest_history.error_message == error_message
        if should_set_started:
            assert ingest_history.started_at is not None
        if should_set_completed:
            assert ingest_history.completed_at is not None
        assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_update_history_status_processing_already_started(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test updating to PROCESSING when already started."""
        existing_started = datetime(2020, 1, 1, tzinfo=UTC)
        ingest_history.started_at = existing_started
        mock_history_repo.get.return_value = ingest_history

        service.update_history_status(history_id=1, status=IngestStatus.PROCESSING)

        assert ingest_history.started_at == existing_started

    def test_update_history_status_not_found(
        self,
        service: IngestProcessorService,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test updating status when history not found."""
        mock_history_repo.get.return_value = None

        with pytest.raises(IngestHistoryNotFoundError):
            service.update_history_status(history_id=999, status=IngestStatus.COMPLETED)


class TestFinalizeHistory:
    """Test finalize_history method."""

    def test_finalize_history_success(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test successful history finalization."""
        ingest_history.ingest_metadata = None
        mock_history_repo.get.return_value = ingest_history

        service.finalize_history(history_id=1, book_ids=[100, 200, 300])

        assert ingest_history.status == IngestStatus.COMPLETED
        assert ingest_history.book_id == 100
        assert ingest_history.completed_at is not None
        assert ingest_history.ingest_metadata is not None
        assert ingest_history.ingest_metadata["book_ids"] == [100, 200, 300]
        assert service._session.commit_count > 0

    def test_finalize_history_empty_book_ids(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test finalization with empty book_ids."""
        mock_history_repo.get.return_value = ingest_history

        service.finalize_history(history_id=1, book_ids=[])

        assert ingest_history.status == IngestStatus.COMPLETED
        assert ingest_history.book_id is None

    def test_finalize_history_existing_metadata(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test finalization with existing metadata."""
        ingest_history.ingest_metadata = {"existing": "data"}
        mock_history_repo.get.return_value = ingest_history

        service.finalize_history(history_id=1, book_ids=[500])

        assert ingest_history.ingest_metadata["existing"] == "data"
        assert ingest_history.ingest_metadata["book_ids"] == [500]

    def test_finalize_history_not_found(
        self,
        service: IngestProcessorService,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test finalization when history not found."""
        mock_history_repo.get.return_value = None

        with pytest.raises(IngestHistoryNotFoundError):
            service.finalize_history(history_id=999, book_ids=[100])


class TestGetHistory:
    """Test get_history method."""

    def test_get_history_success(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test successful history retrieval."""
        mock_history_repo.get.return_value = ingest_history

        result = service.get_history(history_id=1)

        assert result == ingest_history
        mock_history_repo.get.assert_called_once_with(1)

    def test_get_history_not_found(
        self,
        service: IngestProcessorService,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test history retrieval when not found."""
        mock_history_repo.get.return_value = None

        with pytest.raises(IngestHistoryNotFoundError):
            service.get_history(history_id=999)


class TestPrivateHelpers:
    """Test private helper methods."""

    def test_get_active_library_or_raise_success(
        self,
        service: IngestProcessorService,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test getting active library successfully."""
        library = Library(
            id=1,
            name="Test",
            calibre_db_path="/path",
            calibre_db_file="metadata.db",
            is_active=True,
        )
        mock_library_repo.get_active.return_value = library

        result = service._get_active_library_or_raise()

        assert result == library

    def test_get_active_library_or_raise_not_found(
        self,
        service: IngestProcessorService,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test getting active library when none exists."""
        mock_library_repo.get_active.return_value = None

        with pytest.raises(NoActiveLibraryError):
            service._get_active_library_or_raise()

    def test_save_history(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
    ) -> None:
        """Test saving history record."""
        service._save_history(ingest_history)

        assert ingest_history in service._session.added  # type: ignore[attr-defined]
        assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_create_history_from_file_group(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
    ) -> None:
        """Test creating history from file group."""
        history = service._create_history_from_file_group(file_group, user_id=42)

        assert history.status == IngestStatus.PENDING
        assert history.user_id == 42
        assert history.ingest_metadata is not None
        assert history.ingest_metadata["book_key"] == "test_book"
        assert history.ingest_metadata["file_count"] == 1

    def test_create_history_from_file_group_no_user(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
    ) -> None:
        """Test creating history without user_id."""
        history = service._create_history_from_file_group(file_group, user_id=None)

        assert history.user_id is None

    def test_persist_history_success(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        mock_history_repo: MagicMock,
    ) -> None:
        """Test persisting history successfully."""

        def mock_refresh(history: IngestHistory) -> None:
            if history.id is None:
                history.id = 1

        service._session.refresh = mock_refresh  # type: ignore[assignment]

        history_id = service._persist_history(ingest_history)

        assert history_id == 1
        mock_history_repo.add.assert_called_once_with(ingest_history)
        assert service._session.commit_count > 0  # type: ignore[attr-defined]

    def test_persist_history_creation_error(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
    ) -> None:
        """Test persisting history with creation error."""
        ingest_history.id = None
        service._session.add(ingest_history)
        # Don't flush to simulate creation failure

        with pytest.raises(IngestHistoryCreationError):
            service._persist_history(ingest_history)

    def test_log_file_group_audit(
        self,
        service: IngestProcessorService,
        file_group: FileGroup,
        mock_audit_repo: MagicMock,
    ) -> None:
        """Test logging file group audit."""
        service._log_file_group_audit(file_group, history_id=1, user_id=42)

        mock_audit_repo.log_action.assert_called_once()
        call_args = mock_audit_repo.log_action.call_args
        assert call_args.kwargs["action"] == "file_group_discovered"
        assert call_args.kwargs["history_id"] == 1
        assert call_args.kwargs["user_id"] == 42

    def test_log_file_group_audit_empty_files(
        self,
        service: IngestProcessorService,
        file_group_empty: FileGroup,
        mock_audit_repo: MagicMock,
    ) -> None:
        """Test logging audit with empty files."""
        service._log_file_group_audit(file_group_empty, history_id=1, user_id=None)

        mock_audit_repo.log_action.assert_called_once()
        call_args = mock_audit_repo.log_action.call_args
        # Path() when converted to string gives '.' not ''
        assert call_args.kwargs["file_path"] in ("", ".")

    def test_get_metadata_fetch_service_existing(
        self,
        service: IngestProcessorService,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test getting existing metadata fetch service."""
        result = service._get_metadata_fetch_service()

        assert result == mock_metadata_fetch_service

    def test_get_metadata_fetch_service_creates(
        self,
        service_defaults: IngestProcessorService,
        mock_config_service: MagicMock,
    ) -> None:
        """Test creating metadata fetch service when None."""
        service_defaults._config_service = mock_config_service

        with patch(
            "fundamental.services.ingest.ingest_processor_service.MetadataFetchService"
        ) as mock_fetch_class:
            mock_fetch_instance = MagicMock()
            mock_fetch_class.create_default.return_value = mock_fetch_instance

            result = service_defaults._get_metadata_fetch_service()

            assert result == mock_fetch_instance
            mock_fetch_class.create_default.assert_called_once()

    def test_fetch_metadata_record(
        self,
        service: IngestProcessorService,
        metadata_record: MetadataRecord,
        mock_metadata_fetch_service: MagicMock,
    ) -> None:
        """Test fetching metadata record."""
        mock_metadata_fetch_service.fetch_metadata.return_value = metadata_record
        extracted = ExtractedMetadata(
            title="Test",
            authors=["Author"],
            isbn="123",
        )

        result = service._fetch_metadata_record(extracted)

        assert result == metadata_record
        mock_metadata_fetch_service.fetch_metadata.assert_called_once()

    def test_store_fetched_metadata(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
    ) -> None:
        """Test storing fetched metadata."""
        ingest_history.ingest_metadata = None

        result = service._store_fetched_metadata(ingest_history, metadata_record)

        assert isinstance(result, dict)
        assert result["title"] == "Test Book"
        assert ingest_history.ingest_metadata is not None
        assert "fetched_metadata" in ingest_history.ingest_metadata
        assert service._session.commit_count > 0

    def test_store_fetched_metadata_existing(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
    ) -> None:
        """Test storing metadata with existing ingest_metadata."""
        ingest_history.ingest_metadata = {"existing": "data"}

        service._store_fetched_metadata(ingest_history, metadata_record)

        assert ingest_history.ingest_metadata["existing"] == "data"
        assert "fetched_metadata" in ingest_history.ingest_metadata

    def test_metadata_record_to_dict(
        self,
        service: IngestProcessorService,
        metadata_record: MetadataRecord,
    ) -> None:
        """Test converting metadata record to dict."""
        result = service._metadata_record_to_dict(metadata_record)

        assert isinstance(result, dict)
        assert result["title"] == "Test Book"
        assert result["authors"] == ["Test Author"]
        assert result["description"] == "A test book"
        assert result["cover_url"] == "https://example.com/cover.jpg"
        assert result["series"] == "Test Series"
        assert result["series_index"] == 1
        assert result["publisher"] == "Test Publisher"
        assert result["published_date"] == "2020-01-01"
        assert result["identifiers"] == {"isbn": "1234567890"}

    def test_log_metadata_fetch_audit(
        self,
        service: IngestProcessorService,
        ingest_history: IngestHistory,
        metadata_record: MetadataRecord,
        mock_audit_repo: MagicMock,
    ) -> None:
        """Test logging metadata fetch audit."""
        service._log_metadata_fetch_audit(ingest_history, metadata_record)

        mock_audit_repo.log_action.assert_called_once()
        call_args = mock_audit_repo.log_action.call_args
        assert call_args.kwargs["action"] == "metadata_fetched"
        assert call_args.kwargs["file_path"] == ingest_history.file_path
        assert call_args.kwargs["metadata"]["source"] == "openlibrary"
        assert call_args.kwargs["history_id"] == ingest_history.id

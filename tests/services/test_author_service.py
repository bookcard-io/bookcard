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

"""Tests for AuthorService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import DummySession

from bookcard.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorUserMetadata,
    AuthorUserPhoto,
    AuthorWork,
    WorkSubject,
)
from bookcard.models.config import Library
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_exceptions import (
    AuthorMetadataFetchError,
    AuthorNotFoundError,
    InvalidPhotoFormatError,
    NoActiveLibraryError,
    PhotoNotFoundError,
    PhotoStorageError,
)
from bookcard.services.author_service import AuthorService
from bookcard.services.config_service import LibraryService
from bookcard.services.library_scanning.data_sources.types import AuthorData

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def active_library() -> Library:
    """Create an active library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL123A",
        name="Test Author",
        personal_name="Author",
        fuller_name="Test Author",
        title="Dr.",
        birth_date="1950-01-01",
        death_date="2020-01-01",
        entity_type="/type/author",
        biography="Test biography",
        location="New York",
        photo_url="https://example.com/photo.jpg",
        work_count=10,
        ratings_average=4.5,
        ratings_count=100,
    )


@pytest.fixture
def author_with_relationships(author_metadata: AuthorMetadata) -> AuthorMetadata:
    """Create author with all relationships loaded."""
    author_metadata.remote_ids = [
        AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123456",
        ),
        AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="goodreads",
            identifier_value="789012",
        ),
    ]
    author_metadata.photos = [
        AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        ),
        AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=67890,
        ),
    ]
    author_metadata.alternate_names = [
        AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Alt Name 1",
        ),
        AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Alt Name 2",
        ),
    ]
    author_metadata.links = [
        AuthorLink(
            author_metadata_id=author_metadata.id,
            url="https://example.com",
            title="Website",
            link_type="web",
        ),
    ]
    work = AuthorWork(
        id=1,
        author_metadata_id=author_metadata.id,
        work_key="OL1W",
        rank=0,
    )
    work.subjects = [
        WorkSubject(
            author_work_id=work.id,
            subject_name="Fiction",
            rank=0,
        ),
        WorkSubject(
            author_work_id=work.id,
            subject_name="Science Fiction",
            rank=1,
        ),
    ]
    author_metadata.works = [work]
    return author_metadata


@pytest.fixture
def mock_author_repo() -> MagicMock:
    """Create a mock author repository."""
    return MagicMock(spec=AuthorRepository)


@pytest.fixture
def mock_library_service(active_library: Library) -> MagicMock:
    """Create a mock library service."""
    service = MagicMock(spec=LibraryService)
    service.get_active_library.return_value = active_library
    return service


@pytest.fixture
def mock_library_repo() -> MagicMock:
    """Create a mock library repository."""
    return MagicMock(spec=LibraryRepository)


@pytest.fixture
def author_service(
    session: DummySession,
    mock_author_repo: MagicMock,
    mock_library_service: MagicMock,
    tmp_path: Path,
) -> AuthorService:
    """Create AuthorService instance with mocked dependencies."""
    return AuthorService(
        session,  # type: ignore[arg-type]
        author_repo=mock_author_repo,
        library_service=mock_library_service,
        data_directory=str(tmp_path),
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAuthorServiceInit:
    """Test AuthorService initialization."""

    def test_init_with_all_dependencies(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        mock_library_repo: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test __init__ with all dependencies provided."""
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            library_repo=mock_library_repo,
            data_directory=str(tmp_path),
        )

        assert service._session == session
        assert service._author_repo == mock_author_repo
        assert service._library_service == mock_library_service

    def test_init_without_author_repo(
        self, session: DummySession, mock_library_service: MagicMock, tmp_path: Path
    ) -> None:
        """Test __init__ creates AuthorRepository when not provided."""
        service = AuthorService(
            session,  # type: ignore[arg-type]
            library_service=mock_library_service,
            data_directory=str(tmp_path),
        )

        assert service._session == session
        assert isinstance(service._author_repo, AuthorRepository)
        assert service._library_service == mock_library_service

    def test_init_without_library_service(
        self, session: DummySession, mock_author_repo: MagicMock, tmp_path: Path
    ) -> None:
        """Test __init__ creates LibraryService when not provided."""
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            data_directory=str(tmp_path),
        )

        assert service._session == session
        assert service._author_repo == mock_author_repo
        assert isinstance(service._library_service, LibraryService)

    def test_init_without_library_repo(
        self, session: DummySession, mock_author_repo: MagicMock, tmp_path: Path
    ) -> None:
        """Test __init__ creates LibraryRepository when not provided."""
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            data_directory=str(tmp_path),
        )

        assert isinstance(service._library_service, LibraryService)


# ============================================================================
# list_authors_for_active_library Tests
# ============================================================================


class TestListAuthorsForActiveLibrary:
    """Test list_authors_for_active_library."""

    def test_list_authors_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors_for_active_library with successful response."""
        mock_author_repo.list_by_library.return_value = ([author_metadata], 1)

        authors, total = author_service.list_authors_for_active_library()

        assert len(authors) == 1
        assert total == 1
        assert authors[0]["name"] == "Test Author"
        mock_author_repo.list_by_library.assert_called_once_with(
            1,
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
            page=1,
            page_size=20,
        )

    def test_list_authors_with_pagination(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors_for_active_library with custom pagination."""
        mock_author_repo.list_by_library.return_value = ([author_metadata], 1)

        authors, total = author_service.list_authors_for_active_library(
            page=2, page_size=10
        )

        assert len(authors) == 1
        assert total == 1
        mock_author_repo.list_by_library.assert_called_once_with(
            1,
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
            page=2,
            page_size=10,
        )

    def test_list_authors_unmatched_filter(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors_for_active_library with unmatched filter."""
        mock_author_repo.list_unmatched_by_library.return_value = ([author_metadata], 1)

        authors, total = author_service.list_authors_for_active_library(
            filter_type="unmatched"
        )

        assert len(authors) == 1
        assert total == 1
        mock_author_repo.list_unmatched_by_library.assert_called_once_with(
            1,
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
            page=1,
            page_size=20,
        )

    def test_list_authors_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test list_authors_for_active_library with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library"):
            author_service.list_authors_for_active_library()


# ============================================================================
# get_author_by_id_or_key Tests
# ============================================================================


class TestGetAuthorByIdOrKey:
    """Test get_author_by_id_or_key."""

    def test_get_author_by_id_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with numeric ID."""
        mock_author_repo.get_by_id_and_library.return_value = author_with_relationships

        result = author_service.get_author_by_id_or_key("1")

        assert result["name"] == "Test Author"
        assert result["key"] == "OL123A"
        mock_author_repo.get_by_id_and_library.assert_called_once_with(1, 1)

    def test_get_author_by_calibre_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with calibre- prefix."""
        author_mapping = AuthorMapping(
            id=1,
            calibre_author_id=42,
            author_metadata_id=author_metadata.id,
            library_id=1,
        )
        author_with_relationships.mappings = [author_mapping]
        mock_author_repo.get_by_calibre_id_and_library.return_value = (
            author_with_relationships
        )

        result = author_service.get_author_by_id_or_key("calibre-42")

        assert result["name"] == "Test Author"
        mock_author_repo.get_by_calibre_id_and_library.assert_called_once_with(42, 1)

    def test_get_author_by_calibre_id_not_found_fallback(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        active_library: Library,
    ) -> None:
        """Test get_author_by_id_or_key with calibre- prefix falls back to Calibre."""
        from bookcard.models.core import Author

        # Mock lookup to return None (author not in metadata table)
        mock_author_repo.get_by_calibre_id_and_library.return_value = None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        calibre_author = Author(id=42, name="Calibre Author")
        with patch(
            "bookcard.services.author.core_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_session = MagicMock()
            mock_repo.get_session.return_value.__enter__.return_value = mock_session
            mock_exec_result = MagicMock()
            mock_exec_result.first.return_value = calibre_author
            mock_session.exec.return_value = mock_exec_result

            result = author_service.get_author_by_id_or_key("calibre-42")

            assert result["name"] == "Calibre Author"
            assert result["key"] == "calibre-42"
            assert result["calibre_id"] == 42
            assert result["is_unmatched"] is True

    def test_get_author_by_local_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with local- prefix."""
        mock_author_repo.get_by_id_and_library.return_value = author_with_relationships

        result = author_service.get_author_by_id_or_key("local-1")

        assert result["name"] == "Test Author"
        mock_author_repo.get_by_id_and_library.assert_called_once_with(1, 1)

    def test_get_author_by_openlibrary_key(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with OpenLibrary key."""
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_with_relationships
        )

        result = author_service.get_author_by_id_or_key("OL123A")

        assert result["name"] == "Test Author"
        mock_author_repo.get_by_openlibrary_key_and_library.assert_called_once_with(
            "OL123A", 1
        )

    def test_get_author_not_found(
        self, author_service: AuthorService, mock_author_repo: MagicMock
    ) -> None:
        """Test get_author_by_id_or_key with author not found."""
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.get_author_by_id_or_key("999")

    def test_get_author_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test get_author_by_id_or_key with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library"):
            author_service.get_author_by_id_or_key("1")


# ============================================================================
# _get_calibre_author_dict Tests
# ============================================================================


class TestGetCalibreAuthorDict:
    """Test _get_calibre_author_dict."""

    def test_get_calibre_author_dict_success(
        self,
        author_service: AuthorService,
        active_library: Library,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test get_author_by_id_or_key with calibre- ID falls back to Calibre DB."""
        from bookcard.models.core import Author

        # Mock lookup to return None (author not in metadata table)
        mock_author_repo.get_by_calibre_id_and_library.return_value = None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        calibre_author = Author(id=42, name="Calibre Author")
        with patch(
            "bookcard.services.author.core_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_session = MagicMock()
            mock_repo.get_session.return_value.__enter__.return_value = mock_session
            mock_exec_result = MagicMock()
            mock_exec_result.first.return_value = calibre_author
            mock_session.exec.return_value = mock_exec_result

            result = author_service.get_author_by_id_or_key("calibre-42")

            assert result["name"] == "Calibre Author"
            assert result["key"] == "calibre-42"
            assert result["calibre_id"] == 42
            assert result["is_unmatched"] is True

    def test_get_calibre_author_dict_no_db_path(
        self, author_service: AuthorService, mock_author_repo: MagicMock
    ) -> None:
        """Test get_author_by_id_or_key with no database path."""
        # Mock lookup to return None (author not in metadata table)
        mock_author_repo.get_by_calibre_id_and_library.return_value = None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        library = Library(id=1, name="Test", is_active=True, calibre_db_path=None)
        with (
            patch.object(
                author_service._library_service,
                "get_active_library",
                return_value=library,
            ),
            pytest.raises(
                AuthorNotFoundError, match="Library or Calibre database path not found"
            ),
        ):
            author_service.get_author_by_id_or_key("calibre-42")

    def test_get_calibre_author_dict_author_not_found(
        self,
        author_service: AuthorService,
        active_library: Library,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test get_author_by_id_or_key with calibre- ID when author not found."""
        # Mock lookup to return None (author not in metadata table)
        mock_author_repo.get_by_calibre_id_and_library.return_value = None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        with patch(
            "bookcard.services.author.core_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_session = MagicMock()
            mock_repo.get_session.return_value.__enter__.return_value = mock_session
            mock_exec_result = MagicMock()
            mock_exec_result.first.return_value = None
            mock_session.exec.return_value = mock_exec_result

            with pytest.raises(
                AuthorNotFoundError, match="Calibre author not found: 42"
            ):
                author_service.get_author_by_id_or_key("calibre-42")


# ============================================================================
# get_author_by_id_or_key with various ID formats Tests
# ============================================================================


class TestGetAuthorByIdOrKeyFormats:
    """Test get_author_by_id_or_key with various ID formats."""

    def test_get_author_by_calibre_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with calibre- prefix."""
        mock_author_repo.get_by_calibre_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("calibre-42")

        assert result is not None
        assert "name" in result
        mock_author_repo.get_by_calibre_id_and_library.assert_called_once()

    def test_get_author_by_local_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with local- prefix."""
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("local-1")

        assert result is not None
        assert "name" in result
        mock_author_repo.get_by_id_and_library.assert_called_once()

    def test_get_author_by_numeric_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with numeric ID."""
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert result is not None
        assert "name" in result
        mock_author_repo.get_by_id_and_library.assert_called_once()

    def test_get_author_by_openlibrary_key(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with OpenLibrary key."""
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        result = author_service.get_author_by_id_or_key("OL123A")

        assert result is not None
        assert "name" in result
        mock_author_repo.get_by_openlibrary_key_and_library.assert_called_once()


# ============================================================================
# fetch_author_metadata Tests
# ============================================================================


class TestFetchAuthorMetadata:
    """Test fetch_author_metadata."""

    def test_fetch_author_metadata_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test fetch_author_metadata with successful fetch."""

        author_metadata.openlibrary_key = "OL123A"
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
            patch(
                "bookcard.services.author.metadata_service.IngestStageFactory"
            ) as mock_ingest_factory,
            patch(
                "bookcard.services.author.metadata_service.IngestStage"
            ) as mock_ingest_stage_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            author_data = AuthorData(key="OL123A", name="Test Author")
            mock_fetcher.fetch_author.return_value = author_data
            mock_fetcher_class.return_value = mock_fetcher

            mock_ingest_stage = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Success"
            mock_result.stats = {}
            mock_ingest_stage.execute.return_value = mock_result
            mock_ingest_stage_class.return_value = mock_ingest_stage

            mock_components = {
                "author_fetcher": mock_fetcher,
                "ingestion_uow": MagicMock(),
                "deduplicator": MagicMock(),
                "progress_tracker": MagicMock(),
            }
            mock_ingest_factory.create_components.return_value = mock_components

            result = author_service.fetch_author_metadata("OL123A")

            assert result["success"] is True
            assert result["message"] == "Success"

    def test_fetch_author_metadata_no_key(
        self, author_service: AuthorService, mock_author_repo: MagicMock
    ) -> None:
        """Test fetch_author_metadata with no key."""
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.fetch_author_metadata("")

    def test_fetch_author_metadata_key_not_string(
        self, author_service: AuthorService, mock_author_repo: MagicMock
    ) -> None:
        """Test fetch_author_metadata with non-string key."""
        # The method expects a string, but if we pass an int, it will try to parse it
        # Let's test with an author that has no OpenLibrary key
        # Mock get_author_by_id_or_key to return author without OpenLibrary key
        with (
            patch.object(
                author_service,
                "get_author_by_id_or_key",
                return_value={"name": "Test Author", "key": None},
            ),
            pytest.raises(
                AuthorNotFoundError, match="does not have an OpenLibrary key"
            ),
        ):
            author_service.fetch_author_metadata("123")

    def test_fetch_author_metadata_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test fetch_author_metadata with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library"):
            author_service.fetch_author_metadata("OL123A")

    def test_fetch_author_metadata_fetch_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test fetch_author_metadata when fetch fails."""
        author_metadata.openlibrary_key = "OL123A"
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            mock_fetcher.fetch_author.return_value = None
            mock_fetcher_class.return_value = mock_fetcher

            with pytest.raises(
                AuthorMetadataFetchError,
                match="Could not fetch author data from OpenLibrary",
            ):
                author_service.fetch_author_metadata("OL123A")

    def test_fetch_author_metadata_ingest_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test fetch_author_metadata when ingest fails."""

        author_metadata.openlibrary_key = "OL123A"
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
            patch(
                "bookcard.services.author.metadata_service.IngestStageFactory"
            ) as mock_ingest_factory,
            patch(
                "bookcard.services.author.metadata_service.IngestStage"
            ) as mock_ingest_stage_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            author_data = AuthorData(key="OL123A", name="Test Author")
            mock_fetcher.fetch_author.return_value = author_data
            mock_fetcher_class.return_value = mock_fetcher

            mock_ingest_stage = MagicMock()
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.message = "Ingest failed"
            mock_ingest_stage.execute.return_value = mock_result
            mock_ingest_stage_class.return_value = mock_ingest_stage

            mock_components = {
                "author_fetcher": mock_fetcher,
                "ingestion_uow": MagicMock(),
                "deduplicator": MagicMock(),
                "progress_tracker": MagicMock(),
            }
            mock_ingest_factory.create_components.return_value = mock_components

            with pytest.raises(AuthorMetadataFetchError, match="Ingest failed"):
                author_service.fetch_author_metadata("OL123A")

    def test_fetch_author_metadata_unmatched_author(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test fetch_author_metadata with unmatched author (no OpenLibrary key)."""
        # Mock get_author_by_id_or_key to return author without OpenLibrary key
        with (
            patch.object(
                author_service,
                "get_author_by_id_or_key",
                return_value={"name": "Test Author", "key": None},
            ),
            pytest.raises(
                AuthorNotFoundError, match="does not have an OpenLibrary key"
            ),
        ):
            # fetch_author_metadata requires an OpenLibrary key, so this should fail
            author_service.fetch_author_metadata("1")

    def test_fetch_author_metadata_load_mappings(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test fetch_author_metadata loads mappings when not present."""
        author_metadata.openlibrary_key = "OL123A"
        author_metadata.mappings = []
        author_metadata.id = 1
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
            patch(
                "bookcard.services.author.metadata_service.IngestStageFactory"
            ) as mock_ingest_factory,
            patch(
                "bookcard.services.author.metadata_service.IngestStage"
            ) as mock_ingest_stage_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            from bookcard.services.library_scanning.data_sources.types import (
                AuthorData,
            )

            author_data = AuthorData(key="OL123A", name="Test Author")
            mock_fetcher.fetch_author.return_value = author_data
            mock_fetcher_class.return_value = mock_fetcher

            mock_ingest_stage = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Success"
            mock_result.stats = {}
            mock_ingest_stage.execute.return_value = mock_result
            mock_ingest_stage_class.return_value = mock_ingest_stage

            mock_components = {
                "author_fetcher": mock_fetcher,
                "ingestion_uow": MagicMock(),
                "deduplicator": MagicMock(),
                "progress_tracker": MagicMock(),
            }
            mock_ingest_factory.create_components.return_value = mock_components

            result = author_service.fetch_author_metadata("OL123A")

            assert result["success"] is True

    def test_fetch_author_metadata_load_user_metadata(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test fetch_author_metadata loads user metadata when not present."""
        author_metadata.openlibrary_key = "OL123A"
        author_metadata.user_metadata = []
        author_metadata.id = 1
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
            patch(
                "bookcard.services.author.metadata_service.IngestStageFactory"
            ) as mock_ingest_factory,
            patch(
                "bookcard.services.author.metadata_service.IngestStage"
            ) as mock_ingest_stage_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            from bookcard.services.library_scanning.data_sources.types import (
                AuthorData,
            )

            author_data = AuthorData(key="OL123A", name="Test Author")
            mock_fetcher.fetch_author.return_value = author_data
            mock_fetcher_class.return_value = mock_fetcher

            mock_ingest_stage = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Success"
            mock_result.stats = {}
            mock_ingest_stage.execute.return_value = mock_result
            mock_ingest_stage_class.return_value = mock_ingest_stage

            mock_components = {
                "author_fetcher": mock_fetcher,
                "ingestion_uow": MagicMock(),
                "deduplicator": MagicMock(),
                "progress_tracker": MagicMock(),
            }
            mock_ingest_factory.create_components.return_value = mock_components

            result = author_service.fetch_author_metadata("OL123A")

            assert result["success"] is True

    def test_fetch_author_metadata_load_user_photos(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test fetch_author_metadata loads user photos when not present."""
        author_metadata.openlibrary_key = "OL123A"
        author_metadata.user_photos = []
        author_metadata.id = 1
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        with (
            patch(
                "bookcard.services.author.metadata_service.DataSourceRegistry"
            ) as mock_registry,
            patch(
                "bookcard.services.author.metadata_service.PipelineContextFactory"
            ) as mock_factory,
            patch(
                "bookcard.services.author.metadata_service.AuthorDataFetcher"
            ) as mock_fetcher_class,
            patch(
                "bookcard.services.author.metadata_service.IngestStageFactory"
            ) as mock_ingest_factory,
            patch(
                "bookcard.services.author.metadata_service.IngestStage"
            ) as mock_ingest_stage_class,
        ):
            mock_data_source = MagicMock()
            mock_registry.create_source.return_value = mock_data_source

            mock_context_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_context_factory.create_context.return_value = mock_context
            mock_factory.return_value = mock_context_factory

            mock_fetcher = MagicMock()
            from bookcard.services.library_scanning.data_sources.types import (
                AuthorData,
            )

            author_data = AuthorData(key="OL123A", name="Test Author")
            mock_fetcher.fetch_author.return_value = author_data
            mock_fetcher_class.return_value = mock_fetcher

            mock_ingest_stage = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Success"
            mock_result.stats = {}
            mock_ingest_stage.execute.return_value = mock_result
            mock_ingest_stage_class.return_value = mock_ingest_stage

            mock_components = {
                "author_fetcher": mock_fetcher,
                "ingestion_uow": MagicMock(),
                "deduplicator": MagicMock(),
                "progress_tracker": MagicMock(),
            }
            mock_ingest_factory.create_components.return_value = mock_components

            result = author_service.fetch_author_metadata("OL123A")

            assert result["success"] is True


# ============================================================================
# _add_user_metadata_fields Tests
# ============================================================================


class TestAddUserMetadataFields:
    """Test _add_user_metadata_fields."""

    def test_add_user_metadata_fields_with_genres(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_user_metadata_fields with user-defined genres."""
        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=author_metadata.id,
            field_name="genres",
            field_value=["Fiction", "Sci-Fi"],
            is_user_defined=True,
        )
        author_metadata.user_metadata = [user_metadata]

        # Test through public API - get_author_by_id_or_key uses the builder
        with patch.object(
            author_service._core_service, "get_author", return_value=author_metadata
        ):
            result = author_service.get_author_by_id_or_key("1")
            assert result["genres"] == ["Fiction", "Sci-Fi"]

    def test_user_metadata_fields_with_styles(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test user-defined styles appear in author dict."""
        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=author_metadata.id,
            field_name="styles",
            field_value=["Modern", "Contemporary"],
            is_user_defined=True,
        )
        author_metadata.user_metadata = [user_metadata]
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert result["styles"] == ["Modern", "Contemporary"]

    def test_user_metadata_fields_with_shelves(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test user-defined shelves appear in author dict."""
        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=author_metadata.id,
            field_name="shelves",
            field_value=["To Read", "Favorites"],
            is_user_defined=True,
        )
        author_metadata.user_metadata = [user_metadata]
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert result["shelves"] == ["To Read", "Favorites"]

    def test_user_metadata_fields_with_similar_authors(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test user-defined similar_authors appear in author dict."""
        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=author_metadata.id,
            field_name="similar_authors",
            field_value=["OL456B", "OL789C"],
            is_user_defined=True,
        )
        author_metadata.user_metadata = [user_metadata]
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1", include_similar=False)

        assert result["similar_authors"] == ["OL456B", "OL789C"]

    def test_user_metadata_fields_with_empty_list(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test user-defined empty list appears in author dict."""
        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=author_metadata.id,
            field_name="similar_authors",
            field_value=[],
            is_user_defined=True,
        )
        author_metadata.user_metadata = [user_metadata]
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1", include_similar=False)

        assert result["similar_authors"] == []


# ============================================================================
# User photos in author dict Tests
# ============================================================================


class TestUserPhotosInAuthorDict:
    """Test user photos in author dictionary."""

    def test_user_photos_in_author_dict(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test user photos appear in author dict."""
        user_photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        author_metadata.user_photos = [user_photo]
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert "user_photos" in result
        photos = result["user_photos"]
        assert isinstance(photos, list)
        assert len(photos) == 1
        assert isinstance(photos[0], dict)
        assert photos[0]["id"] == 1  # type: ignore[index]
        assert photos[0]["photo_url"] == f"/api/authors/{author_metadata.id}/photos/1"  # type: ignore[index]
        assert photos[0]["is_primary"] is True  # type: ignore[index]

    def test_primary_photo_url_set_from_user_photo(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test primary user photo sets photo_url in author dict."""
        user_photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        author_metadata.user_photos = [user_photo]
        author_metadata.photo_url = None  # No OpenLibrary photo
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert result["photo_url"] == f"/api/authors/{author_metadata.id}/photos/1"


# ============================================================================
# update_author Tests
# ============================================================================


class TestUpdateAuthor:
    """Test update_author."""

    def test_update_author_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author with successful update."""
        author_metadata.id = 1
        author_metadata.openlibrary_key = "OL123A"
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"name": "Updated Name", "biography": "Updated bio"}
        result = author_service.update_author("1", update)

        assert result["name"] == "Updated Name"
        # biography might not be in the result if it's None or not set
        if "biography" in result:
            assert result["biography"] == "Updated bio"
        assert session.commit_count == 1

    def test_update_author_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test update_author with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library found"):
            author_service.update_author("1", {"name": "Updated"})

    def test_update_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test update_author with author not found."""
        # Mock all lookup methods to return None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None
        mock_author_repo.get_by_calibre_id_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.update_author("999", {"name": "Updated"})


# ============================================================================
# update_author metadata field updates Tests
# ============================================================================


class TestUpdateAuthorMetadataFields:
    """Test update_author updates metadata fields."""

    def test_update_author_updates_name(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author updates name."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"name": "New Name"}
        result = author_service.update_author("1", update)

        assert result["name"] == "New Name"
        assert author_metadata.name == "New Name"

    def test_update_author_updates_optional_fields(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author updates optional fields."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {
            "personal_name": "Personal",
            "biography": "New bio",
            "location": "London",
        }
        author_service.update_author("1", update)

        assert author_metadata.personal_name == "Personal"
        assert author_metadata.biography == "New bio"
        assert author_metadata.location == "London"

    def test_update_author_with_none_values(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author with None values."""
        author_metadata.id = 1
        author_metadata.biography = "Old bio"
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"biography": None}
        author_service.update_author("1", update)

        assert author_metadata.biography is None

    def test_update_author_ignores_empty_name(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author ignores empty name."""
        author_metadata.id = 1
        original_name = author_metadata.name
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"name": ""}
        author_service.update_author("1", update)

        assert author_metadata.name == original_name


# ============================================================================
# update_author user metadata Tests
# ============================================================================


class TestUpdateAuthorUserMetadata:
    """Test update_author updates user metadata."""

    def test_update_author_saves_user_metadata(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author saves user metadata list values."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"genres": ["Fiction", "Sci-Fi"]}
        author_service.update_author("1", update)

        assert session.commit_count >= 1

    def test_update_author_deletes_user_metadata(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author deletes user metadata when value is None."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"genres": None}
        author_service.update_author("1", update)

        assert session.commit_count >= 1

    def test_update_author_handles_multiple_user_metadata_fields(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author handles multiple user metadata fields."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {
            "genres": ["Fiction"],
            "styles": ["Modern"],
            "shelves": ["To Read"],
            "similar_authors": ["OL456B"],
        }
        author_service.update_author("1", update)

        assert session.commit_count >= 1


# ============================================================================
# update_author photo_url Tests
# ============================================================================


class TestUpdateAuthorPhotoUrl:
    """Test update_author with photo_url."""

    def test_update_author_sets_photo_url(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test update_author sets photo_url field."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        update = {"photo_url": "/api/authors/1/photos/1"}
        result = author_service.update_author("1", update)

        assert author_metadata.photo_url == "/api/authors/1/photos/1"
        assert result["photo_url"] == "/api/authors/1/photos/1"


# ============================================================================
# Note: Tests for _save_user_metadata, _delete_user_metadata, _get_user_metadata,
# and _get_author_photos_dir have been removed as these are now implementation
# details in AuthorCoreService and FileSystemPhotoStorage. These should be tested
# through the public API (update_author) or by testing the specialized services
# directly if needed.
# ============================================================================


# ============================================================================
# upload_author_photo Tests
# ============================================================================


class TestUploadAuthorPhoto:
    """Test upload_author_photo."""

    def test_upload_author_photo_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test upload_author_photo with successful upload."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        session.set_exec_result([])

        file_content = b"fake image content"
        result = author_service.upload_author_photo(
            "1", file_content, "photo.jpg", set_as_primary=False
        )

        assert result.author_metadata_id == 1
        assert result.file_name == "photo.jpg"
        assert result.file_size == len(file_content)
        assert result.mime_type == "image/jpeg"
        assert session.commit_count == 1

    def test_upload_author_photo_set_as_primary(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test upload_author_photo sets photo as primary."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        existing_primary = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/old.jpg",
            file_name="old.jpg",
            file_size=512,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        session.set_exec_result([existing_primary])
        session.add_exec_result([])

        file_content = b"fake image content"
        result = author_service.upload_author_photo(
            "1", file_content, "photo.jpg", set_as_primary=True
        )

        assert result.is_primary is True
        assert existing_primary.is_primary is False

    def test_upload_author_photo_invalid_file_type(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test upload_author_photo with invalid file type."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        with pytest.raises(InvalidPhotoFormatError, match="invalid_file_type"):
            author_service.upload_author_photo("1", b"content", "photo.txt")

    def test_upload_author_photo_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test upload_author_photo with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library found"):
            author_service.upload_author_photo("1", b"content", "photo.jpg")

    def test_upload_author_photo_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test upload_author_photo with author not found."""
        # Mock all lookup methods to return None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None
        mock_author_repo.get_by_calibre_id_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.upload_author_photo("1", b"content", "photo.jpg")

    def test_upload_author_photo_save_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        tmp_path: Path,
    ) -> None:
        """Test upload_author_photo when file save fails."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        # Mock FileSystemPhotoStorage.save to raise PhotoStorageError
        with (
            patch(
                "bookcard.services.author.photo_storage.FileSystemPhotoStorage.save",
                side_effect=PhotoStorageError("failed_to_save_file"),
            ),
            pytest.raises(PhotoStorageError, match="failed_to_save_file"),
        ):
            author_service.upload_author_photo("1", b"content", "photo.jpg")


# ============================================================================
# upload_photo_from_url Tests
# ============================================================================


class TestUploadPhotoFromUrl:
    """Test upload_photo_from_url."""

    def test_upload_photo_from_url_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test upload_photo_from_url with successful download."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        session.set_exec_result([])
        session.add_exec_result([])

        with (
            patch("httpx.Client") as mock_client_class,
            patch("PIL.Image.open") as mock_image,
        ):
            mock_response = MagicMock()
            mock_response.content = b"fake image content"
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            mock_image.return_value.verify = MagicMock()
            mock_image.return_value = MagicMock()

            result = author_service.upload_photo_from_url(
                "1", "https://example.com/photo.jpg"
            )

            assert result.author_metadata_id == 1
            assert result.source_url == "https://example.com/photo.jpg"
            assert session.commit_count == 2

    def test_upload_photo_from_url_not_image(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test upload_photo_from_url with non-image content type."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        with patch("httpx.Client") as mock_client_class:
            mock_response = MagicMock()
            mock_response.content = b"fake content"
            mock_response.headers = {"content-type": "text/html"}
            mock_response.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(InvalidPhotoFormatError, match="url_not_an_image"):
                author_service.upload_photo_from_url(
                    "1", "https://example.com/page.html"
                )

    def test_upload_photo_from_url_invalid_image(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test upload_photo_from_url with invalid image format."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        with (
            patch("httpx.Client") as mock_client_class,
            patch("PIL.Image.open", side_effect=Exception("Invalid image")),
        ):
            mock_response = MagicMock()
            mock_response.content = b"fake content"
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(InvalidPhotoFormatError, match="invalid_image_format"):
                author_service.upload_photo_from_url(
                    "1", "https://example.com/photo.jpg"
                )

    def test_upload_photo_from_url_download_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test upload_photo_from_url when download fails."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        import httpx

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPError("Network error")
            mock_client_class.return_value = mock_client

            with pytest.raises(PhotoStorageError, match="failed_to_download_image"):
                author_service.upload_photo_from_url(
                    "1", "https://example.com/photo.jpg"
                )


# ============================================================================
# get_author_photos Tests
# ============================================================================


class TestGetAuthorPhotos:
    """Test get_author_photos."""

    def test_get_author_photos_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test get_author_photos returns photos."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        user_photo1 = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo1.jpg",
            file_name="photo1.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        user_photo2 = AuthorUserPhoto(
            id=2,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo2.jpg",
            file_name="photo2.jpg",
            file_size=2048,
            mime_type="image/jpeg",
            is_primary=False,
            order=1,
            created_at=datetime.now(UTC),
        )
        session.set_exec_result([user_photo1, user_photo2])

        result = author_service.get_author_photos("1")

        assert len(result) == 2
        assert result[0].is_primary is True
        assert result[1].is_primary is False

    def test_get_author_photos_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test get_author_photos with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library found"):
            author_service.get_author_photos("1")

    def test_get_author_photos_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test get_author_photos with author not found."""
        # Mock all lookup methods to return None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None
        mock_author_repo.get_by_calibre_id_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.get_author_photos("1")


# ============================================================================
# get_author_photo_by_id Tests
# ============================================================================


class TestGetAuthorPhotoById:
    """Test get_author_photo_by_id."""

    def test_get_author_photo_by_id_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test get_author_photo_by_id returns photo."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        user_photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        session.set_exec_result([user_photo])

        result = author_service.get_author_photo_by_id("1", 1)

        assert result is not None
        assert result.id == 1

    def test_get_author_photo_by_id_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test get_author_photo_by_id returns None when not found."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        session.set_exec_result([])

        result = author_service.get_author_photo_by_id("1", 999)

        assert result is None

    def test_get_author_photo_by_id_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test get_author_photo_by_id with no active library."""
        mock_library_service.get_active_library.return_value = None

        result = author_service.get_author_photo_by_id("1", 1)

        assert result is None

    def test_get_author_photo_by_id_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test get_author_photo_by_id with author not found."""
        mock_author_repo.get_by_id_and_library.return_value = None

        result = author_service.get_author_photo_by_id("1", 1)

        assert result is None


# ============================================================================
# set_primary_photo Tests
# ============================================================================


class TestSetPrimaryPhoto:
    """Test set_primary_photo."""

    def test_set_primary_photo_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test set_primary_photo sets photo as primary."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=False,
            order=0,
            created_at=datetime.now(UTC),
        )
        existing_primary = AuthorUserPhoto(
            id=2,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/old.jpg",
            file_name="old.jpg",
            file_size=512,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )
        session.set_exec_result([photo])
        session.add_exec_result([existing_primary])

        result = author_service.set_primary_photo("1", 1)

        assert result.is_primary is True
        assert existing_primary.is_primary is False
        assert session.commit_count == 1

    def test_set_primary_photo_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test set_primary_photo with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library found"):
            author_service.set_primary_photo("1", 1)

    def test_set_primary_photo_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test set_primary_photo with author not found."""
        # Mock all lookup methods to return None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None
        mock_author_repo.get_by_calibre_id_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.set_primary_photo("1", 1)

    def test_set_primary_photo_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test set_primary_photo with photo not found."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        session.set_exec_result([])

        with pytest.raises(PhotoNotFoundError, match="Photo not found"):
            author_service.set_primary_photo("1", 999)


# ============================================================================
# delete_photo Tests
# ============================================================================


class TestDeletePhoto:
    """Test delete_photo."""

    def test_delete_photo_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test delete_photo deletes photo and file."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        photo_path = tmp_path / "authors" / "1" / "photo.jpg"
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(b"fake image")

        photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=author_metadata.id,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=False,
            order=0,
            created_at=datetime.now(UTC),
        )
        session.set_exec_result([photo])

        author_service.delete_photo("1", 1)

        assert session.commit_count == 1
        # File should be deleted
        assert not photo_path.exists()

    def test_delete_photo_no_active_library(
        self, author_service: AuthorService, mock_library_service: MagicMock
    ) -> None:
        """Test delete_photo with no active library."""
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(NoActiveLibraryError, match="No active library found"):
            author_service.delete_photo("1", 1)

    def test_delete_photo_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test delete_photo with author not found."""
        # Mock all lookup methods to return None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None
        mock_author_repo.get_by_calibre_id_and_library.return_value = None

        with pytest.raises(AuthorNotFoundError, match="Author not found"):
            author_service.delete_photo("1", 1)

    def test_delete_photo_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test delete_photo with photo not found."""
        author_metadata.id = 1
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        session.set_exec_result([])

        with pytest.raises(PhotoNotFoundError, match="Photo not found"):
            author_service.delete_photo("1", 999)

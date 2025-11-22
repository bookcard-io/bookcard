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

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorWork,
    WorkSubject,
)
from fundamental.models.config import Library
from fundamental.repositories.author_repository import AuthorRepository
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.author_service import AuthorService
from fundamental.services.config_service import LibraryService
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.pipeline.base import StageResult
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session."""
    return DummySession()


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

        _authors, total = author_service.list_authors_for_active_library(
            page=2, page_size=10
        )

        assert total == 1
        mock_author_repo.list_by_library.assert_called_once_with(
            1,
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
            page=2,
            page_size=10,
        )

    def test_list_authors_no_active_library(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test list_authors_for_active_library raises ValueError when no active library."""
        mock_library_service.get_active_library.return_value = None
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            data_directory=str(tmp_path),
        )

        with pytest.raises(ValueError, match="No active library found"):
            service.list_authors_for_active_library()

    def test_list_authors_active_library_no_id(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test list_authors_for_active_library raises ValueError when library has no ID."""
        library = Library(
            id=None,
            name="Test Library",
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
        )
        mock_library_service.get_active_library.return_value = library
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            data_directory=str(tmp_path),
        )

        with pytest.raises(ValueError, match="No active library found"):
            service.list_authors_for_active_library()


# ============================================================================
# get_author_by_id_or_key Tests
# ============================================================================


class TestGetAuthorByIdOrKey:
    """Test get_author_by_id_or_key."""

    def test_get_author_by_id(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with numeric ID."""
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1")

        assert result["name"] == "Test Author"
        assert result["key"] == "OL123A"
        mock_author_repo.get_by_id_and_library.assert_called_once_with(1, 1)

    def test_get_author_by_openlibrary_key(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key with OpenLibrary key."""
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        result = author_service.get_author_by_id_or_key("OL123A")

        assert result["name"] == "Test Author"
        mock_author_repo.get_by_openlibrary_key_and_library.assert_called_once_with(
            "OL123A", 1
        )

    def test_get_author_with_similar_authors(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key includes similar authors."""
        similar_author = AuthorMetadata(
            id=2,
            openlibrary_key="OL456A",
            name="Similar Author",
        )
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        mock_author_repo.get_similar_authors_in_library.return_value = [similar_author]

        result = author_service.get_author_by_id_or_key("1", include_similar=True)

        assert "similar_authors" in result
        similar_authors = result["similar_authors"]
        assert isinstance(similar_authors, list)
        assert len(similar_authors) == 1
        assert isinstance(similar_authors[0], dict)
        assert similar_authors[0]["name"] == "Similar Author"  # type: ignore[index]

    def test_get_author_without_similar_authors(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key excludes similar authors when requested."""
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1", include_similar=False)

        assert "similar_authors" not in result

    def test_get_author_no_active_library(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test get_author_by_id_or_key raises ValueError when no active library."""
        mock_library_service.get_active_library.return_value = None
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            data_directory=str(tmp_path),
        )

        with pytest.raises(ValueError, match="No active library found"):
            service.get_author_by_id_or_key("1")

    def test_get_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test get_author_by_id_or_key raises ValueError when author not found."""
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        with pytest.raises(ValueError, match="Author not found"):
            author_service.get_author_by_id_or_key("999")

    def test_get_author_similar_not_in_library(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key filters similar authors not in library."""
        similar_author = AuthorMetadata(id=3, openlibrary_key="OL789A", name="Similar")
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        # get_similar_authors_in_library already filters by library, so only returns authors in library
        mock_author_repo.get_similar_authors_in_library.return_value = [similar_author]

        result = author_service.get_author_by_id_or_key("1", include_similar=True)

        assert "similar_authors" in result
        similar_authors = result["similar_authors"]
        assert isinstance(similar_authors, list)
        assert len(similar_authors) == 1
        assert isinstance(similar_authors[0], dict)
        assert similar_authors[0]["name"] == "Similar"  # type: ignore[index]

    def test_get_author_similar_author_not_found(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key handles similar author not found."""
        mock_author_repo.get_by_id_and_library.return_value = author_metadata
        # get_similar_authors_in_library returns empty list when no similar authors found
        mock_author_repo.get_similar_authors_in_library.return_value = []

        result = author_service.get_author_by_id_or_key("1", include_similar=True)

        similar_authors = result.get("similar_authors", [])
        assert not similar_authors or len(similar_authors) == 0  # type: ignore[arg-type]

    def test_get_author_no_id_for_similar(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author_by_id_or_key skips similar authors when author has no ID."""
        author_metadata.id = None
        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = author_service.get_author_by_id_or_key("1", include_similar=True)

        assert "similar_authors" not in result


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
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test fetch_author_metadata with successful fetch."""
        # Mock get_author_by_id_or_key
        author_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"key": "OL123A", "name": "Test Author"}
        )

        # Mock data source and fetcher
        mock_data_source = MagicMock()
        mock_author_data = AuthorData(
            key="OL123A",
            name="Test Author",
            biography="Updated biography",
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_author.return_value = mock_author_data

        # Mock ingest stage
        mock_ingest_stage = MagicMock()
        mock_result = StageResult(
            success=True,
            message="Success",
            stats={"authors_processed": 1},
        )
        mock_ingest_stage.execute.return_value = mock_result

        # Mock factory methods
        mock_components = {
            "author_fetcher": mock_fetcher,
            "ingestion_uow": MagicMock(),
            "deduplicator": MagicMock(),
            "progress_tracker": MagicMock(),
        }

        with (
            patch(
                "fundamental.services.author_service.DataSourceRegistry.create_source",
                return_value=mock_data_source,
            ),
            patch(
                "fundamental.services.author_service.AuthorDataFetcher",
                return_value=mock_fetcher,
            ),
            patch(
                "fundamental.services.author_service.IngestStageFactory.create_components",
                return_value=mock_components,
            ),
            patch(
                "fundamental.services.author_service.IngestStage",
                return_value=mock_ingest_stage,
            ),
            patch(
                "fundamental.services.author_service.PipelineContextFactory",
            ) as mock_factory_class,
        ):
            mock_factory = MagicMock()
            mock_context = MagicMock()
            mock_context.match_results = []
            mock_factory.create_context.return_value = mock_context
            mock_factory_class.return_value = mock_factory

            result = author_service.fetch_author_metadata("1")

            assert result["success"] is True
            assert result["message"] == "Success"
            assert result["stats"] == {"authors_processed": 1}

    def test_fetch_author_metadata_no_key(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test fetch_author_metadata raises ValueError when author has no OpenLibrary key."""
        author_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"name": "Test Author"}  # No key
        )

        with pytest.raises(ValueError, match="Author does not have an OpenLibrary key"):
            author_service.fetch_author_metadata("1")

    def test_fetch_author_metadata_key_not_string(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test fetch_author_metadata raises ValueError when key is not a string."""
        author_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"key": 12345}  # Not a string
        )

        with pytest.raises(ValueError, match="Author does not have an OpenLibrary key"):
            author_service.fetch_author_metadata("1")

    def test_fetch_author_metadata_no_active_library(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test fetch_author_metadata raises ValueError when no active library."""
        mock_library_service.get_active_library.return_value = None
        service = AuthorService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            data_directory=str(tmp_path),
        )
        service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"key": "OL123A", "name": "Test Author"}
        )

        with pytest.raises(ValueError, match="No active library found"):
            service.fetch_author_metadata("1")

    def test_fetch_author_metadata_fetch_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test fetch_author_metadata raises ValueError when fetch fails."""
        author_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"key": "OL123A", "name": "Test Author"}
        )

        mock_data_source = MagicMock()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_author.return_value = None

        with (
            patch(
                "fundamental.services.author_service.DataSourceRegistry.create_source",
                return_value=mock_data_source,
            ),
            patch(
                "fundamental.services.author_service.AuthorDataFetcher",
                return_value=mock_fetcher,
            ),
            patch(
                "fundamental.services.author_service.PipelineContextFactory",
            ),
            pytest.raises(ValueError, match="Could not fetch author data"),
        ):
            author_service.fetch_author_metadata("1")

    def test_fetch_author_metadata_ingest_failed(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test fetch_author_metadata raises ValueError when ingest fails."""
        author_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
            return_value={"key": "OL123A", "name": "Test Author"}
        )

        mock_data_source = MagicMock()
        mock_author_data = AuthorData(key="OL123A", name="Test Author")
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_author.return_value = mock_author_data

        mock_ingest_stage = MagicMock()
        mock_result = StageResult(
            success=False,
            message="Ingest failed",
            stats={},
        )
        mock_ingest_stage.execute.return_value = mock_result

        mock_components = {
            "author_fetcher": mock_fetcher,
            "ingestion_uow": MagicMock(),
            "deduplicator": MagicMock(),
            "progress_tracker": MagicMock(),
        }

        with (
            patch(
                "fundamental.services.author_service.DataSourceRegistry.create_source",
                return_value=mock_data_source,
            ),
            patch(
                "fundamental.services.author_service.AuthorDataFetcher",
                return_value=mock_fetcher,
            ),
            patch(
                "fundamental.services.author_service.IngestStageFactory.create_components",
                return_value=mock_components,
            ),
            patch(
                "fundamental.services.author_service.IngestStage",
                return_value=mock_ingest_stage,
            ),
            patch(
                "fundamental.services.author_service.PipelineContextFactory",
            ),
            pytest.raises(ValueError, match="Ingest failed"),
        ):
            author_service.fetch_author_metadata("1")


# ============================================================================
# _get_similar_authors Tests
# ============================================================================


class TestGetSimilarAuthors:
    """Test _get_similar_authors."""

    def test_get_similar_authors_success(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_similar_authors returns similar authors in library."""
        similar_author = AuthorMetadata(
            id=2,
            openlibrary_key="OL456A",
            name="Similar Author",
        )
        mock_author_repo.get_similar_authors_in_library.return_value = [similar_author]

        result = author_service._get_similar_authors(1, 1)

        assert len(result) == 1
        assert result[0]["name"] == "Similar Author"

    def test_get_similar_authors_filters_by_library(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_similar_authors filters authors not in library."""
        similar_author = AuthorMetadata(id=3, openlibrary_key="OL789A", name="Similar")
        # get_similar_authors_in_library already filters by library
        mock_author_repo.get_similar_authors_in_library.return_value = [similar_author]

        result = author_service._get_similar_authors(1, 1)

        assert len(result) == 1
        assert result[0]["name"] == "Similar"

    def test_get_similar_authors_with_limit(
        self,
        author_service: AuthorService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_similar_authors respects limit."""
        similar_authors = [
            AuthorMetadata(id=2, openlibrary_key="OL456A", name="Similar 2"),
            AuthorMetadata(id=3, openlibrary_key="OL789A", name="Similar 3"),
            AuthorMetadata(id=4, openlibrary_key="OL012A", name="Similar 4"),
        ]
        # Repository should return only up to limit
        mock_author_repo.get_similar_authors_in_library.return_value = similar_authors

        result = author_service._get_similar_authors(1, 1, limit=3)

        assert len(result) == 3
        mock_author_repo.get_similar_authors_in_library.assert_called_once_with(
            1, 1, limit=3
        )


# ============================================================================
# _build_remote_ids_dict Tests
# ============================================================================


class TestBuildRemoteIdsDict:
    """Test _build_remote_ids_dict."""

    def test_build_remote_ids_dict(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _build_remote_ids_dict builds correct dictionary."""
        result = author_service._build_remote_ids_dict(author_with_relationships)

        assert result == {"viaf": "123456", "goodreads": "789012"}

    def test_build_remote_ids_dict_empty(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_remote_ids_dict with no remote IDs."""
        author_metadata.remote_ids = []
        result = author_service._build_remote_ids_dict(author_metadata)

        assert result == {}


# ============================================================================
# _build_photos_list Tests
# ============================================================================


class TestBuildPhotosList:
    """Test _build_photos_list."""

    def test_build_photos_list(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _build_photos_list builds correct list."""
        result = author_service._build_photos_list(author_with_relationships)

        assert result == [12345, 67890]

    def test_build_photos_list_filters_invalid(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_photos_list filters invalid photo IDs."""
        author_metadata.photos = [
            AuthorPhoto(
                author_metadata_id=author_metadata.id,
                openlibrary_photo_id=12345,
            ),
            AuthorPhoto(
                author_metadata_id=author_metadata.id,
                openlibrary_photo_id=-1,
            ),
            AuthorPhoto(
                author_metadata_id=author_metadata.id,
                openlibrary_photo_id=0,
            ),
            AuthorPhoto(
                author_metadata_id=author_metadata.id,
                openlibrary_photo_id=None,
            ),
        ]
        result = author_service._build_photos_list(author_metadata)

        assert result == [12345]

    def test_build_photos_list_empty(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_photos_list with no photos."""
        author_metadata.photos = []
        result = author_service._build_photos_list(author_metadata)

        assert result == []


# ============================================================================
# _build_links_list Tests
# ============================================================================


class TestBuildLinksList:
    """Test _build_links_list."""

    def test_build_links_list(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _build_links_list builds correct list."""
        result = author_service._build_links_list(author_with_relationships)

        assert len(result) == 1
        assert result[0]["url"] == "https://example.com"
        assert result[0]["title"] == "Website"
        assert result[0]["type"] == {"key": "web"}

    def test_build_links_list_empty_title(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_links_list handles empty title."""
        author_metadata.links = [
            AuthorLink(
                author_metadata_id=author_metadata.id,
                url="https://example.com",
                title=None,
            ),
        ]
        result = author_service._build_links_list(author_metadata)

        assert result[0]["title"] == ""

    def test_build_links_list_no_type(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_links_list handles missing link type."""
        author_metadata.links = [
            AuthorLink(
                author_metadata_id=author_metadata.id,
                url="https://example.com",
                title="Website",
                link_type=None,
            ),
        ]
        result = author_service._build_links_list(author_metadata)

        assert result[0]["type"] == {"key": "/type/link"}


# ============================================================================
# _build_subjects_list Tests
# ============================================================================


class TestBuildSubjectsList:
    """Test _build_subjects_list."""

    def test_build_subjects_list(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _build_subjects_list builds sorted unique list."""
        result = author_service._build_subjects_list(author_with_relationships)

        assert result == ["Fiction", "Science Fiction"]

    def test_build_subjects_list_deduplicates(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_subjects_list deduplicates subjects."""
        work1 = AuthorWork(
            id=1,
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
        )
        work1.subjects = [
            WorkSubject(author_work_id=work1.id, subject_name="Fiction", rank=0),
        ]
        work2 = AuthorWork(
            id=2,
            author_metadata_id=author_metadata.id,
            work_key="OL2W",
        )
        work2.subjects = [
            WorkSubject(author_work_id=work2.id, subject_name="Fiction", rank=0),
        ]
        author_metadata.works = [work1, work2]

        result = author_service._build_subjects_list(author_metadata)

        assert result == ["Fiction"]

    def test_build_subjects_list_empty(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_subjects_list with no works."""
        author_metadata.works = []
        result = author_service._build_subjects_list(author_metadata)

        assert result == []


# ============================================================================
# _build_bio_dict Tests
# ============================================================================


class TestBuildBioDict:
    """Test _build_bio_dict."""

    @pytest.mark.parametrize(
        ("biography", "expected"),
        [
            (None, None),
            ("", None),
            ("Test biography", {"type": "/type/text", "value": "Test biography"}),
        ],
    )
    def test_build_bio_dict(
        self,
        biography: str | None,
        expected: dict[str, str] | None,
        author_service: AuthorService,
    ) -> None:
        """Test _build_bio_dict."""
        result = author_service._build_bio_dict(biography)

        assert result == expected


# ============================================================================
# _build_author_dict Tests
# ============================================================================


class TestBuildAuthorDict:
    """Test _build_author_dict."""

    def test_build_author_dict_full(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _build_author_dict with full author data."""
        result = author_service._build_author_dict(author_with_relationships)

        assert result["name"] == "Test Author"
        assert result["key"] == "OL123A"
        assert "bio" in result
        assert "remote_ids" in result
        assert "photos" in result
        assert "alternate_names" in result
        assert "links" in result
        assert "genres" in result

    def test_build_author_dict_unmatched(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_author_dict with unmatched author."""
        # Unmatched authors have id=None and a _calibre_id attribute
        author_metadata.id = None
        object.__setattr__(author_metadata, "_calibre_id", 123)
        object.__setattr__(author_metadata, "openlibrary_key", "")

        result = author_service._build_author_dict(author_metadata)

        assert result["name"] == "Test Author"
        assert result["key"] == "calibre-123"
        assert result.get("is_unmatched") is True
        assert result["location"] == "Local Library (Unmatched)"

    def test_build_author_dict_minimal(
        self, author_service: AuthorService, author_metadata: AuthorMetadata
    ) -> None:
        """Test _build_author_dict with minimal author data."""
        author_metadata.biography = None
        author_metadata.remote_ids = []
        author_metadata.photos = []
        author_metadata.alternate_names = []
        author_metadata.links = []
        author_metadata.works = []

        result = author_service._build_author_dict(author_metadata)

        assert result["name"] == "Test Author"
        assert result["key"] == "OL123A"
        assert "bio" not in result
        assert "remote_ids" not in result


# ============================================================================
# _add_optional_fields Tests
# ============================================================================


class TestAddOptionalFields:
    """Test _add_optional_fields."""

    def test_add_optional_fields_all_present(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_optional_fields adds all fields when present."""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}
        bio = {"type": "/type/text", "value": "Test biography"}
        remote_ids = {"viaf": "123"}
        photos = [12345]
        alternate_names = ["Alt Name"]
        links = [
            {"url": "https://example.com", "title": "Website", "type": {"key": "web"}}
        ]
        subjects = ["Fiction"]

        author_service._add_optional_fields(
            author_data,
            author_metadata,
            bio,
            remote_ids,
            photos,
            alternate_names,
            links,  # type: ignore[arg-type,invalid-argument-type]
            subjects,
        )

        assert "bio" in author_data
        assert "remote_ids" in author_data
        assert "photos" in author_data
        assert "alternate_names" in author_data
        assert "links" in author_data
        assert "genres" in author_data

    def test_add_optional_fields_none_values(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_optional_fields skips None/empty values."""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}

        author_service._add_optional_fields(  # type: ignore[arg-type]
            author_data,
            author_metadata,
            None,  # bio
            {},  # remote_ids
            [],  # photos
            [],  # alternate_names
            [],  # links
            [],  # subjects
        )

        assert "bio" not in author_data
        assert "remote_ids" not in author_data
        assert "photos" not in author_data


# ============================================================================
# _add_author_metadata_fields Tests
# ============================================================================


class TestAddAuthorMetadataFields:
    """Test _add_author_metadata_fields."""

    def test_add_author_metadata_fields_all_present(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_author_metadata_fields adds all fields when present."""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}

        author_service._add_author_metadata_fields(author_data, author_metadata)

        assert author_data["personal_name"] == "Author"
        assert author_data["fuller_name"] == "Test Author"
        assert author_data["title"] == "Dr."
        assert author_data["birth_date"] == "1950-01-01"
        assert author_data["death_date"] == "2020-01-01"

    def test_add_author_metadata_fields_filters_none(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_author_metadata_fields filters out None values."""
        author_metadata.personal_name = None
        author_metadata.fuller_name = None
        author_metadata.title = None
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}

        author_service._add_author_metadata_fields(author_data, author_metadata)

        assert "personal_name" not in author_data
        assert "fuller_name" not in author_data
        assert "title" not in author_data

    def test_add_author_metadata_fields_filters_empty_string(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_author_metadata_fields filters out empty strings."""
        author_metadata.location = ""
        author_metadata.photo_url = ""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}

        author_service._add_author_metadata_fields(author_data, author_metadata)

        assert "location" not in author_data
        assert "photo_url" not in author_data


# ============================================================================
# _add_relationship_fields Tests
# ============================================================================


class TestAddRelationshipFields:
    """Test _add_relationship_fields."""

    def test_add_relationship_fields_all_present(
        self, author_service: AuthorService
    ) -> None:
        """Test _add_relationship_fields adds all fields when present."""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}
        bio = {"type": "/type/text", "value": "Test"}
        remote_ids = {"viaf": "123"}
        photos = [12345]
        alternate_names = ["Alt"]
        links = [
            {"url": "https://example.com", "title": "Website", "type": {"key": "web"}}
        ]
        subjects = ["Fiction"]

        author_service._add_relationship_fields(
            author_data,
            bio,
            remote_ids,
            photos,
            alternate_names,
            links,  # type: ignore[arg-type,invalid-argument-type]
            subjects,
        )

        assert author_data["bio"] == bio
        assert author_data["remote_ids"] == remote_ids
        assert author_data["photos"] == photos
        assert author_data["alternate_names"] == alternate_names
        assert author_data["links"] == links
        assert author_data["genres"] == subjects

    def test_add_relationship_fields_skips_none_empty(
        self, author_service: AuthorService
    ) -> None:
        """Test _add_relationship_fields skips None/empty values."""
        author_data: dict[str, object] = {"name": "Test Author", "key": "OL123A"}

        author_service._add_relationship_fields(  # type: ignore[arg-type]
            author_data, None, {}, [], [], [], []
        )

        assert "bio" not in author_data
        assert "remote_ids" not in author_data
        assert "photos" not in author_data


# ============================================================================
# _ensure_relationships_loaded Tests
# ============================================================================


class TestEnsureRelationshipsLoaded:
    """Test _ensure_relationships_loaded."""

    def test_ensure_relationships_loaded_all_missing(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test _ensure_relationships_loaded loads all missing relationships."""
        author_metadata.remote_ids = []
        author_metadata.photos = []
        author_metadata.alternate_names = []
        author_metadata.links = []
        author_metadata.works = []

        remote_id = AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123",
        )
        photo = AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        )
        alt_name = AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Alt Name",
        )
        link = AuthorLink(
            author_metadata_id=author_metadata.id,
            url="https://example.com",
            title="Website",
        )
        work = AuthorWork(
            id=1,
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
        )

        session.set_exec_result([remote_id])  # type: ignore[attr-defined]
        session.add_exec_result([photo])  # type: ignore[attr-defined]
        session.add_exec_result([alt_name])  # type: ignore[attr-defined]
        session.add_exec_result([link])  # type: ignore[attr-defined]
        session.add_exec_result([work])  # type: ignore[attr-defined]

        author_service._ensure_relationships_loaded(author_metadata)

        assert len(author_metadata.remote_ids) == 1
        assert len(author_metadata.photos) == 1
        assert len(author_metadata.alternate_names) == 1
        assert len(author_metadata.links) == 1
        assert len(author_metadata.works) == 1

    def test_ensure_relationships_loaded_all_present(
        self,
        author_service: AuthorService,
        author_with_relationships: AuthorMetadata,
    ) -> None:
        """Test _ensure_relationships_loaded skips loading when already present."""
        initial_remote_ids = author_with_relationships.remote_ids.copy()
        initial_photos = author_with_relationships.photos.copy()

        author_service._ensure_relationships_loaded(author_with_relationships)

        # Should not reload if already present
        assert author_with_relationships.remote_ids == initial_remote_ids
        assert author_with_relationships.photos == initial_photos

    def test_ensure_relationships_loaded_partial(
        self,
        author_service: AuthorService,
        author_metadata: AuthorMetadata,
        session: DummySession,
    ) -> None:
        """Test _ensure_relationships_loaded loads only missing relationships."""
        # Set some relationships, leave others empty
        author_metadata.remote_ids = [
            AuthorRemoteId(
                author_metadata_id=author_metadata.id,
                identifier_type="viaf",
                identifier_value="123",
            )
        ]
        author_metadata.photos = []
        author_metadata.alternate_names = []
        author_metadata.links = []
        author_metadata.works = []

        photo = AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        )
        session.set_exec_result([photo])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]

        author_service._ensure_relationships_loaded(author_metadata)

        assert len(author_metadata.remote_ids) == 1  # Already present
        assert len(author_metadata.photos) == 1  # Loaded
        assert len(author_metadata.alternate_names) == 0  # Empty result
        assert len(author_metadata.links) == 0  # Empty result
        assert len(author_metadata.works) == 0  # Empty result

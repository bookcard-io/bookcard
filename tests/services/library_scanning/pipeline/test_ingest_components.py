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

"""Tests for ingest_components to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorWork,
    WorkSubject,
)
from fundamental.services.library_scanning.data_sources.base import (
    DataSourceError,
    DataSourceNetworkError,
    DataSourceNotFoundError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.ingest_components import (
    AlternateNameService,
    AuthorAlternateNameRepository,
    AuthorDataFetcher,
    AuthorIngestionUnitOfWork,
    AuthorLinkRepository,
    AuthorLinkService,
    AuthorMetadataRepository,
    AuthorMetadataService,
    AuthorPhotoRepository,
    AuthorPhotoService,
    AuthorRemoteIdRepository,
    AuthorWorkRepository,
    AuthorWorkService,
    DirectAuthorSubjectStrategy,
    HybridSubjectStrategy,
    MatchResultDeduplicator,
    PhotoUrlBuilder,
    ProgressTracker,
    RemoteIdService,
    WorkBasedSubjectStrategy,
    WorkSubjectRepository,
)
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session."""
    return DummySession()


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Create a mock data source."""
    return MagicMock()


@pytest.fixture
def author_data() -> AuthorData:
    """Create sample author data."""
    return AuthorData(
        key="OL12345A",
        name="Test Author",
        personal_name="Author",
        fuller_name="Test Author",
        work_count=10,
        photo_ids=[12345, 67890],
        identifiers=IdentifierDict(viaf="123456", goodreads="789012"),
        alternate_names=["Author Test", "T. Author"],
        links=[{"url": "https://example.com", "title": "Website", "type": "web"}],
        subjects=["Fiction", "Science Fiction"],
    )


@pytest.fixture
def book_data() -> BookData:
    """Create sample book data."""
    return BookData(
        key="OL123W",
        title="Test Book",
        subjects=["Fiction", "Adventure"],
    )


@pytest.fixture
def match_result(author_data: AuthorData) -> MatchResult:
    """Create a match result."""
    return MatchResult(
        confidence_score=0.9,
        matched_entity=author_data,
        match_method="exact",
        calibre_author_id=1,
    )


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL12345A",
        name="Test Author",
        personal_name="Author",
        work_count=10,
    )


# ============================================================================
# AuthorDataFetcher Tests
# ============================================================================


class TestAuthorDataFetcher:
    """Test AuthorDataFetcher."""

    def test_fetch_author_success(
        self, mock_data_source: MagicMock, author_data: AuthorData
    ) -> None:
        """Test successful author fetch."""
        mock_data_source.get_author.return_value = author_data
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_author("OL12345A")

        assert result == author_data
        mock_data_source.get_author.assert_called_once_with("OL12345A")

    @pytest.mark.parametrize(
        "exception_class",
        [
            DataSourceNetworkError,
            DataSourceRateLimitError,
        ],
    )
    def test_fetch_author_network_error(
        self, mock_data_source: MagicMock, exception_class: type[Exception]
    ) -> None:
        """Test fetch_author raises network errors."""
        mock_data_source.get_author.side_effect = exception_class("Network error")
        fetcher = AuthorDataFetcher(mock_data_source)

        with pytest.raises(exception_class):
            fetcher.fetch_author("OL12345A")

    def test_fetch_author_not_found(self, mock_data_source: MagicMock) -> None:
        """Test fetch_author returns None when not found."""
        mock_data_source.get_author.side_effect = DataSourceNotFoundError("Not found")
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_author("OL12345A")

        assert result is None

    def test_fetch_author_works_with_method(self, mock_data_source: MagicMock) -> None:
        """Test fetch_author_works when method exists."""
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W", "OL2W"])
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_author_works("OL12345A", limit=10)

        assert result == ["OL1W", "OL2W"]
        mock_data_source.get_author_works.assert_called_once_with("OL12345A", limit=10)

    def test_fetch_author_works_without_method(
        self, mock_data_source: MagicMock
    ) -> None:
        """Test fetch_author_works when method doesn't exist."""
        # Remove the method if it exists
        if hasattr(mock_data_source, "get_author_works"):
            delattr(mock_data_source, "get_author_works")
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_author_works("OL12345A")

        assert result == []

    def test_fetch_author_works_without_limit(
        self, mock_data_source: MagicMock
    ) -> None:
        """Test fetch_author_works without limit."""
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W", "OL2W"])
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_author_works("OL12345A")

        assert result == ["OL1W", "OL2W"]
        mock_data_source.get_author_works.assert_called_once_with(
            "OL12345A", limit=None
        )

    def test_fetch_work_success(
        self, mock_data_source: MagicMock, book_data: BookData
    ) -> None:
        """Test successful work fetch."""
        mock_data_source.get_book.return_value = book_data
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_work("OL123W")

        assert result == book_data
        mock_data_source.get_book.assert_called_once_with("OL123W", skip_authors=True)

    def test_fetch_work_error(self, mock_data_source: MagicMock) -> None:
        """Test fetch_work returns None on error."""
        mock_data_source.get_book.side_effect = DataSourceError("Error")
        fetcher = AuthorDataFetcher(mock_data_source)

        result = fetcher.fetch_work("OL123W")

        assert result is None


# ============================================================================
# PhotoUrlBuilder Tests
# ============================================================================


class TestPhotoUrlBuilder:
    """Test PhotoUrlBuilder."""

    def test_build_url_default_base(self) -> None:
        """Test build_url with default base URL."""
        builder = PhotoUrlBuilder()

        result = builder.build_url(12345)

        assert result == "https://covers.openlibrary.org/a/id/12345-L.jpg"

    def test_build_url_custom_base(self) -> None:
        """Test build_url with custom base URL."""
        builder = PhotoUrlBuilder(base_url="https://example.com")

        result = builder.build_url(12345)

        assert result == "https://example.com/a/id/12345-L.jpg"

    @pytest.mark.parametrize(
        "size",
        [
            "S",
            "M",
            "L",
        ],
    )
    def test_build_url_different_sizes(self, size: str) -> None:
        """Test build_url with different sizes."""
        builder = PhotoUrlBuilder()

        result = builder.build_url(12345, size=size)

        assert result == f"https://covers.openlibrary.org/a/id/12345-{size}.jpg"


# ============================================================================
# Repository Tests
# ============================================================================


class TestAuthorMetadataRepository:
    """Test AuthorMetadataRepository."""

    def test_find_by_openlibrary_key_found(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test find_by_openlibrary_key when found."""
        session.add(author_metadata)
        session.flush()
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_openlibrary_key("OL12345A")

        assert result == author_metadata

    def test_find_by_openlibrary_key_not_found(self, session: DummySession) -> None:
        """Test find_by_openlibrary_key when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_openlibrary_key("OL12345A")

        assert result is None

    def test_create(self, session: DummySession, author_data: AuthorData) -> None:
        """Test create author metadata."""
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.create(author_data, photo_url="https://example.com/photo.jpg")

        assert result.name == author_data.name
        assert result.openlibrary_key == author_data.key
        assert result.photo_url == "https://example.com/photo.jpg"
        assert result in session.added  # type: ignore[attr-defined]

    def test_create_without_photo(
        self, session: DummySession, author_data: AuthorData
    ) -> None:
        """Test create author metadata without photo."""
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.create(author_data)

        assert result.name == author_data.name
        assert result.photo_url is None

    def test_update(
        self,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_data: AuthorData,
    ) -> None:
        """Test update author metadata."""
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        new_data = AuthorData(
            key="OL12345A",
            name="Updated Author",
            personal_name="Updated",
            work_count=20,
        )

        result = repo.update(
            author_metadata, new_data, photo_url="https://example.com/new.jpg"
        )

        assert result.name == "Updated Author"
        assert result.work_count == 20
        assert result.photo_url == "https://example.com/new.jpg"
        assert result.updated_at is not None

    def test_update_without_photo(
        self,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_data: AuthorData,
    ) -> None:
        """Test update author metadata without photo."""
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        new_data = AuthorData(
            key="OL12345A",
            name="Updated Author",
            personal_name="Updated",
            work_count=20,
        )
        author_metadata.photo_url = "https://example.com/old.jpg"

        result = repo.update(author_metadata, new_data)

        assert result.name == "Updated Author"
        assert result.photo_url == "https://example.com/old.jpg"


class TestAuthorPhotoRepository:
    """Test AuthorPhotoRepository."""

    def test_exists_true(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test exists returns True when photo exists."""
        assert author_metadata.id is not None
        photo = AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        )
        session.add(photo)
        session.flush()
        session.set_exec_result([photo])  # type: ignore[attr-defined]
        repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]

        result = repo.exists(author_metadata.id, 12345)

        assert result is True

    def test_exists_false(self, session: DummySession) -> None:
        """Test exists returns False when photo doesn't exist."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]

        result = repo.exists(1, 12345)

        assert result is False

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create photo."""
        photo = AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        )
        repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]

        result = repo.create(photo)

        assert result == photo
        assert result in session.added  # type: ignore[attr-defined]


class TestAuthorRemoteIdRepository:
    """Test AuthorRemoteIdRepository."""

    def test_find_by_type_found(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test find_by_type when found."""
        assert author_metadata.id is not None
        remote_id = AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123456",
        )
        session.add(remote_id)
        session.flush()
        session.set_exec_result([remote_id])  # type: ignore[attr-defined]
        repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_type(author_metadata.id, "viaf")

        assert result == remote_id

    def test_find_by_type_not_found(self, session: DummySession) -> None:
        """Test find_by_type when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_type(1, "viaf")

        assert result is None

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create remote ID."""
        remote_id = AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123456",
        )
        repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]

        result = repo.create(remote_id)

        assert result == remote_id
        assert result in session.added  # type: ignore[attr-defined]

    def test_update(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update remote ID."""
        remote_id = AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123456",
        )
        repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]

        result = repo.update(remote_id, "789012")

        assert result.identifier_value == "789012"


class TestAuthorAlternateNameRepository:
    """Test AuthorAlternateNameRepository."""

    def test_exists_true(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test exists returns True when name exists."""
        assert author_metadata.id is not None
        alt_name = AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Alt Name",
        )
        session.add(alt_name)
        session.flush()
        session.set_exec_result([alt_name])  # type: ignore[attr-defined]
        repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]

        result = repo.exists(author_metadata.id, "Alt Name")

        assert result is True

    def test_exists_false(self, session: DummySession) -> None:
        """Test exists returns False when name doesn't exist."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]

        result = repo.exists(1, "Alt Name")

        assert result is False

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create alternate name."""
        alt_name = AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Alt Name",
        )
        repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]

        result = repo.create(alt_name)

        assert result == alt_name
        assert result in session.added  # type: ignore[attr-defined]


class TestAuthorLinkRepository:
    """Test AuthorLinkRepository."""

    def test_exists_by_url_true(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test exists_by_url returns True when link exists."""
        assert author_metadata.id is not None
        link = AuthorLink(
            author_metadata_id=author_metadata.id,
            url="https://example.com",
            title="Website",
        )
        session.add(link)
        session.flush()
        session.set_exec_result([link])  # type: ignore[attr-defined]
        repo = AuthorLinkRepository(session)  # type: ignore[arg-type]

        result = repo.exists_by_url(author_metadata.id, "https://example.com")

        assert result is True

    def test_exists_by_url_false(self, session: DummySession) -> None:
        """Test exists_by_url returns False when link doesn't exist."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorLinkRepository(session)  # type: ignore[arg-type]

        result = repo.exists_by_url(1, "https://example.com")

        assert result is False

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create link."""
        link = AuthorLink(
            author_metadata_id=author_metadata.id,
            url="https://example.com",
            title="Website",
        )
        repo = AuthorLinkRepository(session)  # type: ignore[arg-type]

        result = repo.create(link)

        assert result == link
        assert result in session.added  # type: ignore[attr-defined]


class TestAuthorWorkRepository:
    """Test AuthorWorkRepository."""

    def test_find_by_author_id(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test find_by_author_id."""
        work1 = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        work2 = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL2W",
            rank=1,
        )
        session.set_exec_result([work1, work2])  # type: ignore[attr-defined]
        repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        assert author_metadata.id is not None

        result = repo.find_by_author_id(author_metadata.id)

        assert len(result) == 2
        assert work1 in result
        assert work2 in result

    def test_find_by_work_key_found(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test find_by_work_key when found."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        session.set_exec_result([work])  # type: ignore[attr-defined]
        repo = AuthorWorkRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_work_key("OL1W")

        assert result == work

    def test_find_by_work_key_not_found(self, session: DummySession) -> None:
        """Test find_by_work_key when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorWorkRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_work_key("OL1W")

        assert result is None

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create work."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        repo = AuthorWorkRepository(session)  # type: ignore[arg-type]

        result = repo.create(work)

        assert result == work
        assert result in session.added  # type: ignore[attr-defined]


class TestWorkSubjectRepository:
    """Test WorkSubjectRepository."""

    def test_exists_true(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test exists returns True when subject exists."""
        assert author_metadata.id is not None
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        assert work.id is not None
        subject = WorkSubject(
            author_work_id=work.id,
            subject_name="Fiction",
            rank=0,
        )
        session.add(subject)
        session.flush()
        session.set_exec_result([subject])  # type: ignore[attr-defined]
        repo = WorkSubjectRepository(session)  # type: ignore[arg-type]

        result = repo.exists(work.id, "Fiction")

        assert result is True

    def test_exists_false(self, session: DummySession) -> None:
        """Test exists returns False when subject doesn't exist."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = WorkSubjectRepository(session)  # type: ignore[arg-type]

        result = repo.exists(1, "Fiction")

        assert result is False

    def test_create(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test create subject."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        subject = WorkSubject(
            author_work_id=work.id,
            subject_name="Fiction",
            rank=0,
        )
        repo = WorkSubjectRepository(session)  # type: ignore[arg-type]

        result = repo.create(subject)

        assert result == subject
        assert result in session.added  # type: ignore[attr-defined]


# ============================================================================
# Service Tests
# ============================================================================


class TestAuthorPhotoService:
    """Test AuthorPhotoService."""

    def test_update_photos_new_photos(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_photos with new photos."""
        assert author_metadata.id is not None
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()
        service = AuthorPhotoService(photo_repo, url_builder)

        service.update_photos(author_metadata.id, [12345, 67890])

        assert len(session.added) == 2  # type: ignore[attr-defined]
        photos = [p for p in session.added if isinstance(p, AuthorPhoto)]  # type: ignore[attr-defined]
        assert len(photos) == 2
        assert photos[0].is_primary is True
        assert photos[1].is_primary is False
        assert photos[0].order == 0
        assert photos[1].order == 1

    def test_update_photos_existing_photo(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_photos skips existing photos."""
        assert author_metadata.id is not None
        existing_photo = AuthorPhoto(
            author_metadata_id=author_metadata.id,
            openlibrary_photo_id=12345,
        )
        session.add(existing_photo)
        session.flush()
        # First call returns existing photo (for 12345), second call returns None (for 67890)
        session.set_exec_result([existing_photo])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()
        service = AuthorPhotoService(photo_repo, url_builder)

        # Clear added list to only count new additions
        initial_count = len(session.added)  # type: ignore[attr-defined]
        service.update_photos(author_metadata.id, [12345, 67890])

        # Only new photo should be added
        assert len(session.added) == initial_count + 1  # type: ignore[attr-defined]
        new_photos = [
            p
            for p in session.added[initial_count:]
            if isinstance(p, AuthorPhoto)  # type: ignore[attr-defined]
        ]
        assert len(new_photos) == 1
        assert new_photos[0].openlibrary_photo_id == 67890


class TestRemoteIdService:
    """Test RemoteIdService."""

    def test_update_identifiers_new(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_identifiers with new identifiers."""
        assert author_metadata.id is not None
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        service = RemoteIdService(remote_id_repo)
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing IDs

        service.update_identifiers(
            author_metadata.id, {"viaf": "123456", "goodreads": "789012"}
        )

        assert len(session.added) == 2  # type: ignore[attr-defined]
        remote_ids = [r for r in session.added if isinstance(r, AuthorRemoteId)]  # type: ignore[attr-defined]
        assert len(remote_ids) == 2

    def test_update_identifiers_existing(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_identifiers updates existing identifier."""
        existing = AuthorRemoteId(
            author_metadata_id=author_metadata.id,
            identifier_type="viaf",
            identifier_value="123456",
        )
        session.add(existing)
        session.flush()
        # find_by_type should return the existing ID
        session.set_exec_result([existing])  # type: ignore[attr-defined]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        service = RemoteIdService(remote_id_repo)

        # Clear added list before update
        assert author_metadata.id is not None
        session.added.clear()  # type: ignore[attr-defined]
        service.update_identifiers(author_metadata.id, {"viaf": "999999"})

        assert existing.identifier_value == "999999"
        assert len(session.added) == 0  # type: ignore[attr-defined]  # No new IDs added


class TestAlternateNameService:
    """Test AlternateNameService."""

    def test_update_names_new(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_names with new names."""
        assert author_metadata.id is not None
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        service = AlternateNameService(alt_name_repo)
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing names

        service.update_names(author_metadata.id, ["Alt Name 1", "Alt Name 2"])

        assert len(session.added) == 2  # type: ignore[attr-defined]
        alt_names = [a for a in session.added if isinstance(a, AuthorAlternateName)]  # type: ignore[attr-defined]
        assert len(alt_names) == 2

    def test_update_names_existing(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_names skips existing names."""
        existing = AuthorAlternateName(
            author_metadata_id=author_metadata.id,
            name="Existing Name",
        )
        session.add(existing)
        session.flush()
        session.set_exec_result([existing])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # For "New Name" check
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        service = AlternateNameService(alt_name_repo)

        # Clear added list to only count new additions
        assert author_metadata.id is not None
        initial_count = len(session.added)  # type: ignore[attr-defined]
        service.update_names(author_metadata.id, ["Existing Name", "New Name"])

        # Only new name should be added
        assert len(session.added) == initial_count + 1  # type: ignore[attr-defined]
        new_alt_names = [
            a
            for a in session.added[initial_count:]  # type: ignore[attr-defined]
            if isinstance(a, AuthorAlternateName)
        ]
        assert len(new_alt_names) == 1
        assert new_alt_names[0].name == "New Name"


class TestAuthorLinkService:
    """Test AuthorLinkService."""

    def test_update_links_new(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_links with new links."""
        assert author_metadata.id is not None
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        service = AuthorLinkService(link_repo)
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing links

        service.update_links(
            author_metadata.id,
            [
                {"url": "https://example.com", "title": "Website", "type": "web"},
                {"url": "https://other.com", "title": "Other"},
            ],
        )

        assert len(session.added) == 2  # type: ignore[attr-defined]
        links = [link for link in session.added if isinstance(link, AuthorLink)]  # type: ignore[attr-defined]
        assert len(links) == 2

    def test_update_links_existing(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_links skips existing links."""
        existing = AuthorLink(
            author_metadata_id=author_metadata.id,
            url="https://example.com",
            title="Website",
        )
        session.add(existing)
        session.flush()
        session.set_exec_result([existing])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # For "https://new.com" check
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        service = AuthorLinkService(link_repo)

        # Clear added list to only count new additions
        assert author_metadata.id is not None
        initial_count = len(session.added)  # type: ignore[attr-defined]
        service.update_links(
            author_metadata.id,
            [
                {"url": "https://example.com", "title": "Website"},
                {"url": "https://new.com", "title": "New"},
            ],
        )

        # Only new link should be added
        assert len(session.added) == initial_count + 1  # type: ignore[attr-defined]
        new_links = [
            link
            for link in session.added[initial_count:]
            if isinstance(link, AuthorLink)  # type: ignore[attr-defined]
        ]
        assert len(new_links) == 1
        assert new_links[0].url == "https://new.com"

    def test_update_links_empty_url(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test update_links skips links with empty URL."""
        assert author_metadata.id is not None
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        service = AuthorLinkService(link_repo)
        session.set_exec_result([])  # type: ignore[attr-defined]

        service.update_links(
            author_metadata.id,
            [
                {"url": "", "title": "Empty"},
                {"url": "https://valid.com", "title": "Valid"},
            ],
        )

        # Only valid link should be added
        links = [link for link in session.added if isinstance(link, AuthorLink)]  # type: ignore[attr-defined]
        assert len(links) == 1
        assert links[0].url == "https://valid.com"


class TestAuthorMetadataService:
    """Test AuthorMetadataService."""

    def test_upsert_author_create(
        self, session: DummySession, author_data: AuthorData
    ) -> None:
        """Test upsert_author creates new author."""
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing author
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)

        service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )

        result = service.upsert_author(author_data)
        session.flush()

        assert result.name == author_data.name
        assert result.openlibrary_key == author_data.key
        assert result.id is not None

    def test_upsert_author_update(
        self,
        session: DummySession,
        author_data: AuthorData,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test upsert_author updates existing author."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)

        service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )

        result = service.upsert_author(author_data)
        session.flush()

        assert result.name == author_data.name
        assert result.updated_at is not None

    def test_upsert_author_no_id_raises(
        self, session: DummySession, author_data: AuthorData
    ) -> None:
        """Test upsert_author raises when author has no ID after create."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)

        service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )

        # Mock create to return author without ID
        created = AuthorMetadata(
            openlibrary_key=author_data.key,
            name=author_data.name,
        )
        created.id = None
        metadata_repo.create = MagicMock(return_value=created)  # type: ignore[assignment]

        with pytest.raises(RuntimeError, match="Author ID is None"):
            service.upsert_author(author_data)


class TestAuthorWorkService:
    """Test AuthorWorkService."""

    def test_persist_works_new(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_works with new works."""
        assert author_metadata.id is not None
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing works
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        result = service.persist_works(author_metadata.id, ["OL1W", "OL2W"])

        assert result == 2
        works = [w for w in session.added if isinstance(w, AuthorWork)]  # type: ignore[attr-defined]
        assert len(works) == 2

    def test_persist_works_existing(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_works skips existing works."""
        existing = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(existing)
        session.flush()
        session.set_exec_result([existing])  # type: ignore[attr-defined]  # find_by_author_id returns existing
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        # Clear added list to only count new additions
        assert author_metadata.id is not None
        initial_count = len(session.added)  # type: ignore[attr-defined]
        result = service.persist_works(author_metadata.id, ["OL1W", "OL2W"])

        assert result == 1  # Only one new work
        assert len(session.added) == initial_count + 1  # type: ignore[attr-defined]
        new_works = [
            w
            for w in session.added[initial_count:]
            if isinstance(w, AuthorWork)  # type: ignore[attr-defined]
        ]
        assert len(new_works) == 1
        assert new_works[0].work_key == "OL2W"

    def test_persist_works_empty(self, session: DummySession) -> None:
        """Test persist_works with empty list."""
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        result = service.persist_works(1, [])

        assert result == 0

    def test_persist_work_subjects_new(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_work_subjects with new subjects."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing subjects
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        result = service.persist_work_subjects(work, ["Fiction", "Adventure"])

        assert result == 2
        subjects = [s for s in session.added if isinstance(s, WorkSubject)]  # type: ignore[attr-defined]
        assert len(subjects) == 2

    def test_persist_work_subjects_existing(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_work_subjects skips existing subjects."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        existing_subject = WorkSubject(
            author_work_id=work.id,
            subject_name="Fiction",
            rank=0,
        )
        session.add(existing_subject)
        session.flush()
        session.set_exec_result([existing_subject])  # type: ignore[attr-defined]  # For "Fiction"
        session.add_exec_result([])  # type: ignore[attr-defined]  # For "Adventure"
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        # Clear added list to only count new additions
        initial_count = len(session.added)  # type: ignore[attr-defined]
        result = service.persist_work_subjects(work, ["Fiction", "Adventure"])

        assert result == 1  # Only one new subject
        assert len(session.added) == initial_count + 1  # type: ignore[attr-defined]
        new_subjects = [
            s
            for s in session.added[initial_count:]
            if isinstance(s, WorkSubject)  # type: ignore[attr-defined]
        ]
        assert len(new_subjects) == 1
        assert new_subjects[0].subject_name == "Adventure"

    def test_persist_work_subjects_empty(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_work_subjects with empty list."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        session.add(work)
        session.flush()
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        result = service.persist_work_subjects(work, [])

        assert result == 0

    def test_persist_work_subjects_no_work_id(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test persist_work_subjects returns 0 when work has no ID."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        work.id = None
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        service = AuthorWorkService(work_repo, subject_repo)

        result = service.persist_work_subjects(work, ["Fiction"])

        assert result == 0


# ============================================================================
# Strategy Tests
# ============================================================================


class TestDirectAuthorSubjectStrategy:
    """Test DirectAuthorSubjectStrategy."""

    def test_fetch_subjects_success(
        self, mock_data_source: MagicMock, author_data: AuthorData
    ) -> None:
        """Test fetch_subjects with subjects in author data."""
        mock_data_source.get_author.return_value = author_data
        fetcher = AuthorDataFetcher(mock_data_source)
        strategy = DirectAuthorSubjectStrategy(fetcher)

        result = strategy.fetch_subjects("OL12345A")

        assert result == ["Fiction", "Science Fiction"]

    def test_fetch_subjects_no_subjects(self, mock_data_source: MagicMock) -> None:
        """Test fetch_subjects when author has no subjects."""
        author_data = AuthorData(
            key="OL12345A",
            name="Test Author",
            work_count=10,
        )
        mock_data_source.get_author.return_value = author_data
        fetcher = AuthorDataFetcher(mock_data_source)
        strategy = DirectAuthorSubjectStrategy(fetcher)

        result = strategy.fetch_subjects("OL12345A")

        assert result == []

    def test_fetch_subjects_author_not_found(self, mock_data_source: MagicMock) -> None:
        """Test fetch_subjects when author not found."""
        mock_data_source.get_author.return_value = None
        fetcher = AuthorDataFetcher(mock_data_source)
        strategy = DirectAuthorSubjectStrategy(fetcher)

        result = strategy.fetch_subjects("OL12345A")

        assert result == []


class TestWorkBasedSubjectStrategy:
    """Test WorkBasedSubjectStrategy."""

    def test_fetch_subjects_success(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
        author_metadata: AuthorMetadata,
        book_data: BookData,
    ) -> None:
        """Test fetch_subjects from works."""
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W", "OL2W"])
        mock_data_source.get_book = MagicMock(return_value=book_data)
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )

        result = strategy.fetch_subjects("OL12345A", author_metadata)

        assert "Fiction" in result
        assert "Adventure" in result

    def test_fetch_subjects_no_works(
        self, session: DummySession, mock_data_source: MagicMock
    ) -> None:
        """Test fetch_subjects when author has no works."""
        mock_data_source.get_author_works = MagicMock(return_value=[])
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )

        result = strategy.fetch_subjects("OL12345A")

        assert result == []

    def test_fetch_subjects_with_limit(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
        author_metadata: AuthorMetadata,
        book_data: BookData,
    ) -> None:
        """Test fetch_subjects with max_works_per_author limit."""
        mock_data_source.get_author_works = MagicMock(
            return_value=["OL1W", "OL2W", "OL3W"]
        )
        mock_data_source.get_book = MagicMock(return_value=book_data)
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo, max_works_per_author=2
        )

        strategy.fetch_subjects("OL12345A", author_metadata)

        mock_data_source.get_author_works.assert_called_once_with("OL12345A", limit=2)

    def test_fetch_subjects_network_error_suppressed(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test fetch_subjects suppresses network errors."""
        mock_data_source.get_author_works.side_effect = DataSourceNetworkError(
            "Network error"
        )
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )

        result = strategy.fetch_subjects("OL12345A")

        assert result == []

    def test_fetch_subjects_rate_limit_error_suppressed(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test fetch_subjects suppresses rate limit errors."""
        mock_data_source.get_author_works.side_effect = DataSourceRateLimitError(
            "Rate limit"
        )
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )

        result = strategy.fetch_subjects("OL12345A")

        assert result == []

    def test_fetch_subjects_without_author_metadata(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
        book_data: BookData,
    ) -> None:
        """Test fetch_subjects without author metadata."""
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W"])
        mock_data_source.get_book = MagicMock(return_value=book_data)
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )

        result = strategy.fetch_subjects("OL12345A")

        assert len(result) > 0

    def test_fetch_subjects_persists_subjects_to_existing_work(
        self,
        session: DummySession,
        mock_data_source: MagicMock,
        author_metadata: AuthorMetadata,
        book_data: BookData,
    ) -> None:
        """Test fetch_subjects persists subjects when work exists in DB."""
        work = AuthorWork(
            author_metadata_id=author_metadata.id,
            work_key="OL1W",
            rank=0,
        )
        work.id = 1  # Ensure work has an ID
        session.add(work)
        session.flush()
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W"])
        mock_data_source.get_book = MagicMock(return_value=book_data)
        fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        strategy = WorkBasedSubjectStrategy(
            fetcher, work_service, work_repo, subject_repo
        )
        # First query is for persisting works (empty), second is find_by_work_key (returns work)
        session.set_exec_result([])  # type: ignore[attr-defined]  # No existing works when persisting
        session.add_exec_result([work])  # type: ignore[attr-defined]  # find_by_work_key returns work
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing subject "Fiction"
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing subject "Adventure"

        result = strategy.fetch_subjects("OL12345A", author_metadata)

        assert len(result) > 0
        # Verify subjects were persisted to the work
        subjects = [s for s in session.added if isinstance(s, WorkSubject)]  # type: ignore[attr-defined]
        assert len(subjects) > 0


class TestHybridSubjectStrategy:
    """Test HybridSubjectStrategy."""

    def test_fetch_subjects_direct_success(
        self, mock_data_source: MagicMock, author_data: AuthorData
    ) -> None:
        """Test fetch_subjects uses direct strategy when subjects found."""
        mock_data_source.get_author.return_value = author_data
        direct_fetcher = AuthorDataFetcher(mock_data_source)
        direct_strategy = DirectAuthorSubjectStrategy(direct_fetcher)
        work_strategy = MagicMock()
        strategy = HybridSubjectStrategy(direct_strategy, work_strategy)

        result = strategy.fetch_subjects("OL12345A")

        assert result == ["Fiction", "Science Fiction"]
        work_strategy.fetch_subjects.assert_not_called()

    def test_fetch_subjects_fallback_to_works(
        self, session: DummySession, mock_data_source: MagicMock
    ) -> None:
        """Test fetch_subjects falls back to work strategy when no direct subjects."""
        author_data = AuthorData(
            key="OL12345A",
            name="Test Author",
            work_count=10,
        )
        mock_data_source.get_author.return_value = author_data
        direct_fetcher = AuthorDataFetcher(mock_data_source)
        direct_strategy = DirectAuthorSubjectStrategy(direct_fetcher)

        work_fetcher = AuthorDataFetcher(mock_data_source)
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        work_service = AuthorWorkService(work_repo, subject_repo)
        work_strategy = WorkBasedSubjectStrategy(
            work_fetcher, work_service, work_repo, subject_repo
        )
        mock_data_source.get_author_works = MagicMock(return_value=[])
        strategy = HybridSubjectStrategy(direct_strategy, work_strategy)

        result = strategy.fetch_subjects("OL12345A")

        assert result == []


# ============================================================================
# Deduplication Tests
# ============================================================================


class TestMatchResultDeduplicator:
    """Test MatchResultDeduplicator."""

    def test_deduplicate_by_key_unique(self, author_data: AuthorData) -> None:
        """Test deduplicate_by_key with unique results."""
        match1 = MatchResult(
            confidence_score=0.9,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=1,
        )
        other_data = AuthorData(
            key="OL99999A",
            name="Other Author",
            work_count=5,
        )
        match2 = MatchResult(
            confidence_score=0.8,
            matched_entity=other_data,
            match_method="fuzzy",
            calibre_author_id=2,
        )
        deduplicator = MatchResultDeduplicator()

        unique, count = deduplicator.deduplicate_by_key([match1, match2])

        assert len(unique) == 2
        assert count == 0

    def test_deduplicate_by_key_duplicates(self, author_data: AuthorData) -> None:
        """Test deduplicate_by_key with duplicates."""
        match1 = MatchResult(
            confidence_score=0.9,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=1,
        )
        match2 = MatchResult(
            confidence_score=0.8,
            matched_entity=author_data,
            match_method="fuzzy",
            calibre_author_id=2,
        )
        deduplicator = MatchResultDeduplicator()

        unique, count = deduplicator.deduplicate_by_key([match1, match2])

        assert len(unique) == 1
        assert count == 1


# ============================================================================
# Progress Tracking Tests
# ============================================================================


class TestProgressTracker:
    """Test ProgressTracker."""

    def test_reset(self) -> None:
        """Test reset tracker."""
        tracker = ProgressTracker()
        tracker.reset(10)

        assert tracker._total == 10
        assert tracker._current == 0
        assert tracker._progress == 0.0

    def test_update(self) -> None:
        """Test update progress."""
        tracker = ProgressTracker()
        tracker.reset(10)
        tracker.update()

        assert tracker._current == 1
        assert tracker._progress == 0.1

    def test_update_zero_total(self) -> None:
        """Test update with zero total."""
        tracker = ProgressTracker()
        tracker.reset(0)
        tracker.update()

        assert tracker._current == 1
        assert tracker._progress == 0.0

    def test_progress_property(self) -> None:
        """Test progress property."""
        tracker = ProgressTracker()
        tracker.reset(10)
        tracker.update()
        tracker.update()

        assert tracker.progress == 0.2

    def test_current_property(self) -> None:
        """Test current property."""
        tracker = ProgressTracker()
        tracker.reset(10)
        tracker.update()

        assert tracker.current == 1


# ============================================================================
# Unit of Work Tests
# ============================================================================


class TestAuthorIngestionUnitOfWork:
    """Test AuthorIngestionUnitOfWork."""

    def test_ingest_author_success(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_data: AuthorData,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test ingest_author successfully."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        mock_data_source = MagicMock()
        mock_data_source.get_author_works = MagicMock(return_value=[])
        data_fetcher = AuthorDataFetcher(mock_data_source)

        uow = AuthorIngestionUnitOfWork(
            session,  # type: ignore[arg-type]
            author_service,
            work_service,
            data_fetcher=data_fetcher,
        )

        result = uow.ingest_author(match_result, author_data)
        session.flush()

        assert result.name == author_data.name

    def test_ingest_author_with_works(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_data: AuthorData,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test ingest_author with works."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        mock_data_source = MagicMock()
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W", "OL2W"])
        data_fetcher = AuthorDataFetcher(mock_data_source)

        uow = AuthorIngestionUnitOfWork(
            session,  # type: ignore[arg-type]
            author_service,
            work_service,
            data_fetcher=data_fetcher,
        )

        result = uow.ingest_author(match_result, author_data)
        session.flush()

        assert result.name == author_data.name

    def test_ingest_author_with_subject_strategy(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_data: AuthorData,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test ingest_author with subject strategy."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        mock_data_source = MagicMock()
        mock_data_source.get_author_works = MagicMock(return_value=["OL1W"])
        mock_data_source.get_book.return_value = BookData(
            key="OL1W",
            title="Test Book",
            subjects=["Fiction"],
        )
        data_fetcher = AuthorDataFetcher(mock_data_source)
        subject_strategy = WorkBasedSubjectStrategy(
            data_fetcher, work_service, work_repo, subject_repo
        )
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing works
        session.add_exec_result([])  # type: ignore[attr-defined]  # find_by_work_key returns None
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing subjects

        uow = AuthorIngestionUnitOfWork(
            session,  # type: ignore[arg-type]
            author_service,
            work_service,
            subject_strategy=subject_strategy,
            data_fetcher=data_fetcher,
        )

        result = uow.ingest_author(match_result, author_data)
        session.flush()

        assert result.name == author_data.name

    def test_ingest_author_exception_rollback(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_data: AuthorData,
    ) -> None:
        """Test ingest_author rolls back on exception."""
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        # Make upsert_author raise an exception
        author_service.upsert_author = MagicMock(side_effect=RuntimeError("Test error"))  # type: ignore[assignment]

        uow = AuthorIngestionUnitOfWork(
            session,  # type: ignore[arg-type]
            author_service,
            work_service,
        )

        with pytest.raises(RuntimeError, match="Test error"):
            uow.ingest_author(match_result, author_data)

    def test_ingest_author_no_data_fetcher(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_data: AuthorData,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test ingest_author without data fetcher."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        photo_repo = AuthorPhotoRepository(session)  # type: ignore[arg-type]
        remote_id_repo = AuthorRemoteIdRepository(session)  # type: ignore[arg-type]
        alt_name_repo = AuthorAlternateNameRepository(session)  # type: ignore[arg-type]
        link_repo = AuthorLinkRepository(session)  # type: ignore[arg-type]
        work_repo = AuthorWorkRepository(session)  # type: ignore[arg-type]
        subject_repo = WorkSubjectRepository(session)  # type: ignore[arg-type]
        url_builder = PhotoUrlBuilder()

        photo_service = AuthorPhotoService(photo_repo, url_builder)
        remote_id_service = RemoteIdService(remote_id_repo)
        alt_name_service = AlternateNameService(alt_name_repo)
        link_service = AuthorLinkService(link_repo)
        author_service = AuthorMetadataService(
            metadata_repo,
            photo_service,
            remote_id_service,
            alt_name_service,
            link_service,
            url_builder,
        )
        work_service = AuthorWorkService(work_repo, subject_repo)

        uow = AuthorIngestionUnitOfWork(
            session,  # type: ignore[arg-type]
            author_service,
            work_service,
        )

        result = uow.ingest_author(match_result, author_data)
        session.flush()

        assert result.name == author_data.name

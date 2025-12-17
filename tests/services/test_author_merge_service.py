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

"""Tests for AuthorMergeService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
    AuthorUserPhoto,
)
from bookcard.models.config import Library
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_merge.author_recommendation_service import (
    AuthorRecommendationService,
)
from bookcard.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from bookcard.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from bookcard.services.author_merge.calibre_repository_factory import (
    CalibreRepositoryFactory,
)
from bookcard.services.author_merge.merge_strategies import MergeStrategyFactory
from bookcard.services.author_merge.value_objects import RelationshipCounts
from bookcard.services.author_merge_service import AuthorMergeService
from bookcard.services.config_service import LibraryService

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_author_repo() -> MagicMock:
    """Create a mock author repository."""
    return MagicMock(spec=AuthorRepository)


@pytest.fixture
def mock_library_service() -> MagicMock:
    """Create a mock library service."""
    return MagicMock(spec=LibraryService)


@pytest.fixture
def mock_library_repo() -> MagicMock:
    """Create a mock library repository."""
    return MagicMock(spec=LibraryRepository)


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
    )


@pytest.fixture
def author_metadata2() -> AuthorMetadata:
    """Create second author metadata."""
    return AuthorMetadata(
        id=2,
        openlibrary_key="OL456A",
        name="Another Author",
    )


@pytest.fixture
def author_mapping() -> AuthorMapping:
    """Create sample author mapping."""
    return AuthorMapping(
        id=1,
        calibre_author_id=10,
        author_metadata_id=1,
        library_id=1,
        is_verified=False,
    )


@pytest.fixture
def author_mapping2() -> AuthorMapping:
    """Create second author mapping."""
    return AuthorMapping(
        id=2,
        calibre_author_id=20,
        author_metadata_id=2,
        library_id=1,
        is_verified=False,
    )


@pytest.fixture
def user_photo() -> AuthorUserPhoto:
    """Create sample user photo."""
    return AuthorUserPhoto(
        id=1,
        author_metadata_id=1,
        file_path="photos/author1.jpg",
        is_primary=True,
    )


@pytest.fixture
def merge_service(
    session: DummySession,
    mock_author_repo: MagicMock | None,
    mock_library_service: MagicMock | None,
    mock_library_repo: MagicMock | None,
) -> AuthorMergeService:
    """Create AuthorMergeService instance."""
    return AuthorMergeService(
        session=session,  # type: ignore[arg-type]
        author_repo=mock_author_repo,
        library_service=mock_library_service,
        library_repo=mock_library_repo,
        data_directory="/data",
    )


@pytest.fixture
def merge_service_no_deps(session: DummySession) -> AuthorMergeService:
    """Create AuthorMergeService without optional dependencies."""
    return AuthorMergeService(session=session, data_directory="/data")  # type: ignore[arg-type]


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAuthorMergeServiceInit:
    """Test AuthorMergeService initialization."""

    def test_init_with_all_dependencies(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test __init__ with all dependencies provided."""
        service = AuthorMergeService(
            session=session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
            library_repo=mock_library_repo,
            data_directory="/custom/data",
        )

        assert service._session == session
        assert service._author_repo == mock_author_repo
        assert service._library_service == mock_library_service
        assert isinstance(service._relationship_repo, AuthorRelationshipRepository)
        assert service._data_directory == "/custom/data"
        assert isinstance(service._calibre_repo_factory, CalibreRepositoryFactory)

    def test_init_without_author_repo(
        self,
        session: DummySession,
        mock_library_service: MagicMock,
    ) -> None:
        """Test __init__ creates AuthorRepository when not provided."""
        service = AuthorMergeService(
            session=session,  # type: ignore[arg-type]
            library_service=mock_library_service,
        )

        assert isinstance(service._author_repo, AuthorRepository)

    def test_init_without_library_service(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test __init__ creates LibraryService when not provided."""
        service = AuthorMergeService(
            session=session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_repo=mock_library_repo,
        )

        assert isinstance(service._library_service, LibraryService)

    def test_init_without_library_repo(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
    ) -> None:
        """Test __init__ creates LibraryRepository when not provided."""
        service = AuthorMergeService(
            session=session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
        )

        assert isinstance(service._library_service, LibraryService)

    def test_init_default_data_directory(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
    ) -> None:
        """Test __init__ uses default data directory when not provided."""
        service = AuthorMergeService(
            session=session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service,
        )

        assert service._data_directory == "/data"


# ============================================================================
# recommend_keep_author Tests
# ============================================================================


class TestRecommendKeepAuthor:
    """Test recommend_keep_author method."""

    def test_recommend_keep_author_success(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test recommend_keep_author with successful recommendation."""
        author_ids = ["1", "2"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For validate_same_library
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For validate_same_library
        session.add_exec_result([author_mapping])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For get_mapping_for_author
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For get_mapping_for_author
        session.add_exec_result([])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For get_photo_url (no user photos)
        session.add_exec_result([])  # type: ignore[attr-defined]  # type: ignore[attr-defined]  # For get_photo_url (no user photos)

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_calibre_author_service.get_book_count.return_value = 5
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                with patch(
                    "bookcard.services.author_merge_service.AuthorRecommendationService"
                ) as mock_rec_class:
                    mock_rec_service = MagicMock(spec=AuthorRecommendationService)
                    mock_rec_service.determine_best_author.return_value = (
                        author_metadata
                    )
                    mock_rec_service.calculate_metadata_score.return_value = 10
                    mock_rec_class.return_value = mock_rec_service

                    with patch.object(
                        merge_service._relationship_repo,
                        "get_relationship_counts",
                        return_value=RelationshipCounts(
                            alternate_names=0,
                            remote_ids=0,
                            photos=0,
                            links=0,
                            works=0,
                            work_subjects=0,
                            similarities=0,
                            user_metadata=0,
                            user_photos=0,
                        ),
                    ):
                        result = merge_service.recommend_keep_author(author_ids)

                        assert "recommended_keep_id" in result
                        assert "authors" in result
                        authors_list = result["authors"]
                        assert isinstance(authors_list, list)
                        assert len(authors_list) == 2

    def test_recommend_keep_author_less_than_two(
        self,
        merge_service: AuthorMergeService,
    ) -> None:
        """Test recommend_keep_author raises error with less than 2 authors."""
        author_ids = ["1"]

        with pytest.raises(ValueError, match="At least 2 authors required"):
            merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_no_active_library(
        self,
        merge_service: AuthorMergeService,
        mock_library_service: MagicMock,
    ) -> None:
        """Test recommend_keep_author raises error when no active library."""
        author_ids = ["1", "2"]
        merge_service._library_service = mock_library_service
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(ValueError, match="No active library found"):
            merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_library_no_id(
        self,
        merge_service: AuthorMergeService,
        mock_library_service: MagicMock,
        active_library: Library,
    ) -> None:
        """Test recommend_keep_author raises error when library has no ID."""
        author_ids = ["1", "2"]
        merge_service._library_service = mock_library_service
        active_library.id = None
        mock_library_service.get_active_library.return_value = active_library

        with pytest.raises(ValueError, match="No active library found"):
            merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
    ) -> None:
        """Test recommend_keep_author raises error when author not found."""
        author_ids = ["1", "999"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            AuthorMetadata(id=1, openlibrary_key="OL1A", name="Author 1"),
            None,
        ]

        with pytest.raises(ValueError, match="Author not found: 999"):
            merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_different_libraries(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test recommend_keep_author raises error when authors in different libraries."""
        author_ids = ["1", "2"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        session = merge_service._session
        # First author in library 1
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        # Second author in library 2
        different_mapping = AuthorMapping(
            id=2,
            calibre_author_id=20,
            author_metadata_id=2,
            library_id=2,
        )
        session.add_exec_result([different_mapping])  # type: ignore[attr-defined]

        with pytest.raises(
            ValueError, match="All authors must belong to the same library"
        ):
            merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_no_calibre_repo(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test recommend_keep_author raises error when Calibre repo cannot be created."""
        author_ids = ["1", "2"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]

        # The error should be raised when Calibre repo creation fails
        # But we need to mock get_relationship_counts to avoid errors during recommendation
        with patch.object(
            merge_service._relationship_repo,
            "get_relationship_counts",
            return_value=RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            ),
        ):
            # Patch the instance method, not the class
            merge_service._calibre_repo_factory.create = MagicMock(return_value=None)  # type: ignore[assignment]

            with pytest.raises(ValueError, match="Cannot access Calibre database"):
                merge_service.recommend_keep_author(author_ids)

    def test_recommend_keep_author_with_user_photos(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
        user_photo: AuthorUserPhoto,
    ) -> None:
        """Test recommend_keep_author with author having user photos."""
        author_ids = ["1", "2"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]
        # User photos for first author
        session.add_exec_result([user_photo])  # type: ignore[attr-defined]
        # No user photos for second author
        session.add_exec_result([])  # type: ignore[attr-defined]

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_calibre_author_service.get_book_count.return_value = 5
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                with patch(
                    "bookcard.services.author_merge_service.AuthorRecommendationService"
                ) as mock_rec_class:
                    mock_rec_service = MagicMock(spec=AuthorRecommendationService)
                    mock_rec_service.determine_best_author.return_value = (
                        author_metadata
                    )
                    mock_rec_service.calculate_metadata_score.return_value = 10
                    mock_rec_class.return_value = mock_rec_service

                    with patch.object(
                        merge_service._relationship_repo,
                        "get_relationship_counts",
                        return_value=RelationshipCounts(
                            alternate_names=0,
                            remote_ids=0,
                            photos=0,
                            links=0,
                            works=0,
                            work_subjects=0,
                            similarities=0,
                            user_metadata=0,
                            user_photos=0,
                        ),
                    ):
                        result = merge_service.recommend_keep_author(author_ids)

                        authors_list = result["authors"]
                        assert isinstance(authors_list, list)
                        assert authors_list[0]["photo_url"] == "/api/authors/1/photos/1"  # type: ignore[index]

    def test_recommend_keep_author_author_without_id(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test recommend_keep_author with author without ID."""
        author_ids = ["1", "2"]
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        author_metadata.id = None
        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping2])  # type: ignore[attr-defined]  # Only second author has mapping
        session.add_exec_result([])  # type: ignore[attr-defined]  # For get_mapping_for_author (first author)
        session.add_exec_result([  # type: ignore[attr-defined]
            author_mapping2
        ])  # For get_mapping_for_author (second author)
        session.add_exec_result([])  # type: ignore[attr-defined]  # For get_photo_url (first author)
        session.add_exec_result([])  # type: ignore[attr-defined]  # For get_photo_url (second author)

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_calibre_author_service.get_book_count.return_value = 5
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                with patch(
                    "bookcard.services.author_merge_service.AuthorRecommendationService"
                ) as mock_rec_class:
                    mock_rec_service = MagicMock(spec=AuthorRecommendationService)
                    mock_rec_service.determine_best_author.return_value = (
                        author_metadata2
                    )
                    mock_rec_service.calculate_metadata_score.return_value = 10
                    mock_rec_class.return_value = mock_rec_service

                    with patch.object(
                        merge_service._relationship_repo,
                        "get_relationship_counts",
                        return_value=RelationshipCounts(
                            alternate_names=0,
                            remote_ids=0,
                            photos=0,
                            links=0,
                            works=0,
                            work_subjects=0,
                            similarities=0,
                            user_metadata=0,
                            user_photos=0,
                        ),
                    ):
                        result = merge_service.recommend_keep_author(author_ids)

                        authors_list = result["authors"]
                        assert isinstance(authors_list, list)
                        assert authors_list[0]["id"] is None  # type: ignore[index]
                        assert authors_list[0]["relationship_counts"] == {}  # type: ignore[index]


# ============================================================================
# merge_authors Tests
# ============================================================================


class TestMergeAuthors:
    """Test merge_authors method."""

    def test_merge_authors_success(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test merge_authors with successful merge."""
        author_ids = ["1", "2"]
        keep_author_id = "1"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            author_metadata,  # keep_author lookup in _resolve_keep_author
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]  # For validate_same_library
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]  # For validate_same_library
        session.add_exec_result([author_mapping])  # type: ignore[attr-defined]  # For get_mapping (keep)
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]  # For get_mapping (merge)

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_calibre_author_service.get_book_count.return_value = 5
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                with patch(
                    "bookcard.services.author_merge_service.MergeStrategyFactory"
                ) as mock_strategy_factory_class:
                    mock_strategy_factory = MagicMock(spec=MergeStrategyFactory)
                    mock_strategy = MagicMock()
                    mock_strategy_factory.get_strategy.return_value = mock_strategy
                    mock_strategy_factory_class.return_value = mock_strategy_factory

                    result = merge_service.merge_authors(author_ids, keep_author_id)

                    assert result["id"] == "1"
                    assert result["key"] == "OL123A"
                    assert result["name"] == "Test Author"
                    assert session.commit_count == 1  # type: ignore[attr-defined]

    def test_merge_authors_less_than_two(
        self,
        merge_service: AuthorMergeService,
    ) -> None:
        """Test merge_authors raises error with less than 2 authors."""
        author_ids = ["1"]
        keep_author_id = "1"

        with pytest.raises(ValueError, match="At least 2 authors required"):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_no_active_library(
        self,
        merge_service: AuthorMergeService,
        mock_library_service: MagicMock,
    ) -> None:
        """Test merge_authors raises error when no active library."""
        author_ids = ["1", "2"]
        keep_author_id = "1"
        merge_service._library_service = mock_library_service
        mock_library_service.get_active_library.return_value = None

        with pytest.raises(ValueError, match="No active library found"):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_author_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
    ) -> None:
        """Test merge_authors raises error when author not found."""
        author_ids = ["1", "999"]
        keep_author_id = "1"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            AuthorMetadata(id=1, openlibrary_key="OL1A", name="Author 1"),
            None,
        ]

        with pytest.raises(ValueError, match="Author not found: 999"):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_keep_author_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test merge_authors raises error when keep author not found."""
        author_ids = ["1", "2"]
        keep_author_id = "999"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            None,  # keep_author lookup
        ]

        with pytest.raises(ValueError, match="Keep author not found: 999"):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_keep_author_not_in_list(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test merge_authors raises error when keep author not in merge list."""
        author_ids = ["1", "2"]
        keep_author_id = "3"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        keep_author = AuthorMetadata(id=3, openlibrary_key="OL3A", name="Keep Author")
        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            keep_author,  # keep_author lookup
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]

        with pytest.raises(
            ValueError, match="Keep author must be one of the authors to merge"
        ):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_no_calibre_repo(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test merge_authors raises error when Calibre repo cannot be created."""
        author_ids = ["1", "2"]
        keep_author_id = "1"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            author_metadata,  # keep_author lookup
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]

        # Patch the instance method, not the class
        merge_service._calibre_repo_factory.create = MagicMock(return_value=None)  # type: ignore[assignment]

        with pytest.raises(
            ValueError, match="Cannot access Calibre database for merge"
        ):
            merge_service.merge_authors(author_ids, keep_author_id)

    def test_merge_authors_missing_mapping(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test merge_authors skips merge when mapping is missing."""
        author_ids = ["1", "2"]
        keep_author_id = "1"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            author_metadata,  # keep_author lookup
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]  # For validate_same_library
        session.add_exec_result([  # type: ignore[attr-defined]
            author_mapping
        ])  # For validate_same_library (second author)
        session.add_exec_result([author_mapping])  # type: ignore[attr-defined]  # For get_mapping (keep)
        session.add_exec_result([])  # type: ignore[attr-defined]  # For get_mapping (merge) - not found

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                result = merge_service.merge_authors(author_ids, keep_author_id)

                # Should still return keep author even if merge is skipped
                assert result["id"] == "1"

    def test_merge_authors_author_without_id(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test merge_authors skips merge when author has no ID."""
        author_ids = ["1", "2"]
        keep_author_id = "1"
        merge_service._author_repo = mock_author_repo
        merge_service._library_service = mock_library_service

        author_metadata2.id = None
        mock_library_service.get_active_library.return_value = active_library
        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
            author_metadata,  # keep_author lookup
        ]

        session = merge_service._session
        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]  # For validate_same_library

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                result = merge_service.merge_authors(author_ids, keep_author_id)

                # Should still return keep author even if merge is skipped
                assert result["id"] == "1"


# ============================================================================
# _resolve_authors Tests
# ============================================================================


class TestResolveAuthors:
    """Test _resolve_authors method."""

    def test_resolve_authors_success(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test _resolve_authors with successful resolution."""
        author_ids = ["1", "2"]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            author_metadata2,
        ]

        result = merge_service._resolve_authors(author_ids, library_id)

        assert len(result) == 2
        assert result[0] == author_metadata
        assert result[1] == author_metadata2

    def test_resolve_authors_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _resolve_authors raises error when author not found."""
        author_ids = ["1", "999"]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.side_effect = [
            author_metadata,
            None,
        ]

        with pytest.raises(ValueError, match="Author not found: 999"):
            merge_service._resolve_authors(author_ids, library_id)


# ============================================================================
# _resolve_keep_author Tests
# ============================================================================


class TestResolveKeepAuthor:
    """Test _resolve_keep_author method."""

    def test_resolve_keep_author_success(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test _resolve_keep_author with successful resolution."""
        keep_author_id = "1"
        authors = [author_metadata, author_metadata2]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = merge_service._resolve_keep_author(keep_author_id, authors, library_id)

        assert result == author_metadata

    def test_resolve_keep_author_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test _resolve_keep_author raises error when not found."""
        keep_author_id = "999"
        authors = [author_metadata, author_metadata2]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.return_value = None

        with pytest.raises(ValueError, match="Keep author not found: 999"):
            merge_service._resolve_keep_author(keep_author_id, authors, library_id)

    def test_resolve_keep_author_not_in_list(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test _resolve_keep_author raises error when not in merge list."""
        keep_author_id = "3"
        authors = [author_metadata, author_metadata2]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        keep_author = AuthorMetadata(id=3, openlibrary_key="OL3A", name="Keep Author")
        mock_author_repo.get_by_id_and_library.return_value = keep_author

        with pytest.raises(
            ValueError, match="Keep author must be one of the authors to merge"
        ):
            merge_service._resolve_keep_author(keep_author_id, authors, library_id)

    def test_resolve_keep_author_authors_without_id(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _resolve_keep_author with authors without IDs."""
        keep_author_id = "1"
        author_without_id = AuthorMetadata(
            id=None, openlibrary_key="OL2A", name="Author 2"
        )
        authors = [author_metadata, author_without_id]
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = merge_service._resolve_keep_author(keep_author_id, authors, library_id)

        assert result == author_metadata


# ============================================================================
# _get_merge_authors Tests
# ============================================================================


class TestGetMergeAuthors:
    """Test _get_merge_authors method."""

    def test_get_merge_authors_success(
        self,
        merge_service: AuthorMergeService,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
    ) -> None:
        """Test _get_merge_authors excludes keep author."""
        authors = [author_metadata, author_metadata2]
        keep_author = author_metadata

        result = merge_service._get_merge_authors(authors, keep_author)

        assert len(result) == 1
        assert result[0] == author_metadata2

    def test_get_merge_authors_multiple(
        self,
        merge_service: AuthorMergeService,
    ) -> None:
        """Test _get_merge_authors with multiple authors."""
        author1 = AuthorMetadata(id=1, openlibrary_key="OL1A", name="Author 1")
        author2 = AuthorMetadata(id=2, openlibrary_key="OL2A", name="Author 2")
        author3 = AuthorMetadata(id=3, openlibrary_key="OL3A", name="Author 3")
        authors = [author1, author2, author3]
        keep_author = author1

        result = merge_service._get_merge_authors(authors, keep_author)

        assert len(result) == 2
        assert author2 in result
        assert author3 in result
        assert author1 not in result


# ============================================================================
# _validate_same_library Tests
# ============================================================================


class TestValidateSameLibrary:
    """Test _validate_same_library method."""

    def test_validate_same_library_success(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
        author_mapping2: AuthorMapping,
    ) -> None:
        """Test _validate_same_library with authors in same library."""
        authors = [author_metadata, author_metadata2]

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([author_mapping2])  # type: ignore[attr-defined]

        # Should not raise
        merge_service._validate_same_library(authors)

    def test_validate_same_library_different_libraries(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _validate_same_library raises error with different libraries."""
        authors = [author_metadata, author_metadata2]

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        different_mapping = AuthorMapping(
            id=2,
            calibre_author_id=20,
            author_metadata_id=2,
            library_id=2,
        )
        session.add_exec_result([different_mapping])  # type: ignore[attr-defined]

        with pytest.raises(
            ValueError, match="All authors must belong to the same library"
        ):
            merge_service._validate_same_library(authors)

    def test_validate_same_library_no_mapping(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_metadata2: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _validate_same_library with author without mapping."""
        authors = [author_metadata, author_metadata2]

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # No mapping for second author

        # Should not raise if authors don't have mappings
        merge_service._validate_same_library(authors)

    def test_validate_same_library_author_without_id(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _validate_same_library with author without ID."""
        author_without_id = AuthorMetadata(
            id=None, openlibrary_key="OL2A", name="Author 2"
        )
        authors = [author_metadata, author_without_id]

        mapping = AuthorMapping(
            id=1,
            calibre_author_id=10,
            author_metadata_id=author_metadata.id,
            library_id=1,
        )
        session.set_exec_result([mapping])  # type: ignore[attr-defined]  # For first author (has ID)
        # Second author has no ID, so no query for it

        # Should not raise if author has no ID
        merge_service._validate_same_library(authors)


# ============================================================================
# _get_mapping_for_author Tests
# ============================================================================


class TestGetMappingForAuthor:
    """Test _get_mapping_for_author method."""

    def test_get_mapping_for_author_success(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _get_mapping_for_author with found mapping."""
        author_metadata_id = 1
        library_id = 1

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]

        result = merge_service._get_mapping_for_author(author_metadata_id, library_id)

        assert result == author_mapping

    def test_get_mapping_for_author_not_found(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
    ) -> None:
        """Test _get_mapping_for_author returns None when not found."""
        author_metadata_id = 999
        library_id = 1

        session.set_exec_result([])

        result = merge_service._get_mapping_for_author(author_metadata_id, library_id)

        assert result is None

    def test_get_mapping_for_author_none_id(
        self,
        merge_service: AuthorMergeService,
    ) -> None:
        """Test _get_mapping_for_author returns None when author_metadata_id is None."""
        author_metadata_id = None
        library_id = 1

        result = merge_service._get_mapping_for_author(author_metadata_id, library_id)

        assert result is None


# ============================================================================
# _lookup_author Tests
# ============================================================================


class TestLookupAuthor:
    """Test _lookup_author method."""

    def test_lookup_author_by_calibre_prefix(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with calibre- prefix."""
        author_id = "calibre-10"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_calibre_id_and_library.return_value = author_metadata

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata
        mock_author_repo.get_by_calibre_id_and_library.assert_called_once_with(
            10, library_id
        )

    def test_lookup_author_by_calibre_prefix_invalid(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with invalid calibre- prefix falls through."""
        author_id = "calibre-invalid"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        # Should fall through to OpenLibrary key lookup
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata

    def test_lookup_author_by_local_prefix(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with local- prefix."""
        author_id = "local-1"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata
        mock_author_repo.get_by_id_and_library.assert_called_once_with(1, library_id)

    def test_lookup_author_by_local_prefix_invalid(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with invalid local- prefix falls through."""
        author_id = "local-invalid"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        # Should fall through to OpenLibrary key lookup
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata

    def test_lookup_author_by_integer_id(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with integer ID."""
        author_id = "1"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_id_and_library.return_value = author_metadata

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata
        mock_author_repo.get_by_id_and_library.assert_called_once_with(1, library_id)

    def test_lookup_author_by_openlibrary_key(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _lookup_author with OpenLibrary key."""
        author_id = "OL123A"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_openlibrary_key_and_library.return_value = (
            author_metadata
        )

        result = merge_service._lookup_author(author_id, library_id)

        assert result == author_metadata
        mock_author_repo.get_by_openlibrary_key_and_library.assert_called_once_with(
            author_id, library_id
        )

    def test_lookup_author_not_found(
        self,
        merge_service: AuthorMergeService,
        mock_author_repo: MagicMock,
    ) -> None:
        """Test _lookup_author returns None when not found."""
        author_id = "OL999A"
        library_id = 1
        merge_service._author_repo = mock_author_repo

        mock_author_repo.get_by_calibre_id_and_library.return_value = None
        mock_author_repo.get_by_id_and_library.return_value = None
        mock_author_repo.get_by_openlibrary_key_and_library.return_value = None

        result = merge_service._lookup_author(author_id, library_id)

        assert result is None


# ============================================================================
# _get_photo_url_for_author Tests
# ============================================================================


class TestGetPhotoUrlForAuthor:
    """Test _get_photo_url_for_author method."""

    def test_get_photo_url_for_author_with_photo_url(
        self,
        merge_service: AuthorMergeService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with existing photo_url."""
        author_metadata.photo_url = "https://example.com/photo.jpg"

        result = merge_service._get_photo_url_for_author(author_metadata)

        assert result == "https://example.com/photo.jpg"

    def test_get_photo_url_for_author_with_primary_user_photo(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
        user_photo: AuthorUserPhoto,
    ) -> None:
        """Test _get_photo_url_for_author with primary user photo."""
        author_metadata.photo_url = None

        session.set_exec_result([user_photo])

        result = merge_service._get_photo_url_for_author(author_metadata)

        assert result == "/api/authors/1/photos/1"

    def test_get_photo_url_for_author_with_first_user_photo(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with first user photo (no primary)."""
        author_metadata.photo_url = None

        photo = AuthorUserPhoto(
            id=2,
            author_metadata_id=1,
            file_path="photos/author1.jpg",
            is_primary=False,
        )
        session.set_exec_result([photo])  # type: ignore[attr-defined]

        result = merge_service._get_photo_url_for_author(author_metadata)

        assert result == "/api/authors/1/photos/2"

    def test_get_photo_url_for_author_no_photos(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with no photos."""
        author_metadata.photo_url = None

        session.set_exec_result([])

        result = merge_service._get_photo_url_for_author(author_metadata)

        assert result is None

    def test_get_photo_url_for_author_no_id(
        self,
        merge_service: AuthorMergeService,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with author without ID."""
        author_metadata.id = None
        author_metadata.photo_url = None

        result = merge_service._get_photo_url_for_author(author_metadata)

        assert result is None

    def test_get_photo_url_for_author_primary_photo_no_id(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with primary photo that has no ID."""
        author_metadata.photo_url = None

        photo = AuthorUserPhoto(
            id=None,
            author_metadata_id=1,
            file_path="photos/author1.jpg",
            is_primary=True,
        )
        session.set_exec_result([photo])  # type: ignore[attr-defined]

        result = merge_service._get_photo_url_for_author(author_metadata)

        # Should fall back to first photo, but it also has no ID
        assert result is None

    def test_get_photo_url_for_author_multiple_photos(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_photo_url_for_author with multiple user photos."""
        author_metadata.photo_url = None

        photo1 = AuthorUserPhoto(
            id=1,
            author_metadata_id=1,
            file_path="photos/photo1.jpg",
            is_primary=False,
        )
        photo2 = AuthorUserPhoto(
            id=2,
            author_metadata_id=1,
            file_path="photos/photo2.jpg",
            is_primary=True,
        )
        session.set_exec_result([photo1, photo2])  # type: ignore[attr-defined]

        result = merge_service._get_photo_url_for_author(author_metadata)

        # Should use primary photo
        assert result == "/api/authors/1/photos/2"


# ============================================================================
# _get_book_count_for_author Tests
# ============================================================================


class TestGetBookCountForAuthor:
    """Test _get_book_count_for_author method."""

    def test_get_book_count_for_author_with_service(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _get_book_count_for_author with provided service."""
        library_id = 1
        merge_service._session = session  # type: ignore[assignment]

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]

        mock_calibre_author_service = MagicMock()
        mock_calibre_author_service.get_book_count.return_value = 10

        result = merge_service._get_book_count_for_author(
            author_metadata, library_id, mock_calibre_author_service
        )

        assert result == 10
        mock_calibre_author_service.get_book_count.assert_called_once_with(10)

    def test_get_book_count_for_author_no_mapping(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _get_book_count_for_author returns 0 when no mapping."""
        library_id = 1
        merge_service._session = session  # type: ignore[assignment]

        session.set_exec_result([])

        result = merge_service._get_book_count_for_author(
            author_metadata, library_id, None
        )

        assert result == 0

    def test_get_book_count_for_author_create_service(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _get_book_count_for_author creates service when not provided."""
        library_id = 1
        merge_service._session = session  # type: ignore[assignment]
        merge_service._library_service = mock_library_service

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]

        mock_library_service.get_active_library.return_value = active_library

        with patch(
            "bookcard.services.author_merge_service.CalibreRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock(spec=CalibreRepositoryFactory)
            mock_calibre_repo = MagicMock()
            mock_calibre_author_service = MagicMock(spec=CalibreAuthorService)
            mock_calibre_author_service.get_book_count.return_value = 5
            mock_factory.create.return_value = mock_calibre_repo
            mock_factory_class.return_value = mock_factory

            with patch(
                "bookcard.services.author_merge_service.CalibreAuthorService"
            ) as mock_service_class:
                mock_service_class.return_value = mock_calibre_author_service

                result = merge_service._get_book_count_for_author(
                    author_metadata, library_id, None
                )

                assert result == 5

    def test_get_book_count_for_author_no_active_library(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        mock_library_service: MagicMock,
        author_metadata: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _get_book_count_for_author returns 0 when no active library."""
        library_id = 1
        merge_service._session = session  # type: ignore[assignment]
        merge_service._library_service = mock_library_service

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]

        mock_library_service.get_active_library.return_value = None

        result = merge_service._get_book_count_for_author(
            author_metadata, library_id, None
        )

        assert result == 0

    def test_get_book_count_for_author_no_calibre_repo(
        self,
        merge_service: AuthorMergeService,
        session: DummySession,
        mock_library_service: MagicMock,
        active_library: Library,
        author_metadata: AuthorMetadata,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _get_book_count_for_author returns 0 when Calibre repo cannot be created."""
        library_id = 1
        merge_service._session = session  # type: ignore[assignment]
        merge_service._library_service = mock_library_service

        session.set_exec_result([author_mapping])  # type: ignore[attr-defined]

        mock_library_service.get_active_library.return_value = active_library

        # Patch the instance method, not the class
        merge_service._calibre_repo_factory.create = MagicMock(return_value=None)  # type: ignore[assignment]

        # When repo is None, the method should return 0 without creating service
        result = merge_service._get_book_count_for_author(
            author_metadata, library_id, None
        )

        assert result == 0

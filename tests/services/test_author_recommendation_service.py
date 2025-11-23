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

"""Tests for AuthorRecommendationService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.services.author_merge.author_recommendation_service import (
    AuthorRecommendationService,
)
from fundamental.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from fundamental.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from fundamental.services.author_merge.value_objects import (
    AuthorScore,
    RelationshipCounts,
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
def mock_relationship_repo() -> MagicMock:
    """Create a mock relationship repository."""
    return MagicMock(spec=AuthorRelationshipRepository)


@pytest.fixture
def mock_calibre_author_service() -> MagicMock:
    """Create a mock Calibre author service."""
    return MagicMock(spec=CalibreAuthorService)


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL123A",
        name="Test Author",
    )


@pytest.fixture
def author_metadata_full() -> AuthorMetadata:
    """Create author metadata with all fields populated."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL123A",
        name="Test Author",
        biography="Test biography",
        birth_date="1950-01-01",
        death_date="2020-01-01",
        location="New York",
        photo_url="https://example.com/photo.jpg",
        work_count=10,
        ratings_count=100,
        top_work="Test Work",
    )


@pytest.fixture
def author_mapping() -> AuthorMapping:
    """Create sample author mapping."""
    return AuthorMapping(
        id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        library_id=1,
        is_verified=False,
    )


@pytest.fixture
def verified_mapping() -> AuthorMapping:
    """Create verified author mapping."""
    return AuthorMapping(
        id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        library_id=1,
        is_verified=True,
    )


@pytest.fixture
def recommendation_service(
    mock_relationship_repo: MagicMock,
    mock_calibre_author_service: MagicMock | None,
) -> AuthorRecommendationService:
    """Create AuthorRecommendationService instance."""
    return AuthorRecommendationService(
        relationship_repo=mock_relationship_repo,
        calibre_author_service=mock_calibre_author_service,
    )


@pytest.fixture
def recommendation_service_no_calibre(
    mock_relationship_repo: MagicMock,
) -> AuthorRecommendationService:
    """Create AuthorRecommendationService without Calibre service."""
    return AuthorRecommendationService(relationship_repo=mock_relationship_repo)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAuthorRecommendationServiceInit:
    """Test AuthorRecommendationService initialization."""

    def test_init_with_calibre_service(
        self,
        mock_relationship_repo: MagicMock,
        mock_calibre_author_service: MagicMock,
    ) -> None:
        """Test __init__ with Calibre service provided."""
        service = AuthorRecommendationService(
            relationship_repo=mock_relationship_repo,
            calibre_author_service=mock_calibre_author_service,
        )

        assert service._relationship_repo == mock_relationship_repo
        assert service._calibre_author_service == mock_calibre_author_service

    def test_init_without_calibre_service(
        self,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test __init__ without Calibre service."""
        service = AuthorRecommendationService(relationship_repo=mock_relationship_repo)

        assert service._relationship_repo == mock_relationship_repo
        assert service._calibre_author_service is None


# ============================================================================
# determine_best_author Tests
# ============================================================================


class TestDetermineBestAuthor:
    """Test determine_best_author method."""

    def test_determine_best_author_single_author(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test determine_best_author with single author."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service.determine_best_author(
            authors=[author_metadata],
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result == author_metadata

    def test_determine_best_author_multiple_authors_first_best(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test determine_best_author with multiple authors, first is best."""
        library_id = 1
        author2 = AuthorMetadata(id=2, openlibrary_key="OL456A", name="Author 2")

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            if author.id == 1:
                return 10
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service.determine_best_author(
            authors=[author_metadata, author2],
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result == author_metadata

    def test_determine_best_author_multiple_authors_second_best(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test determine_best_author with multiple authors, second is best."""
        library_id = 1
        author2 = AuthorMetadata(id=2, openlibrary_key="OL456A", name="Author 2")

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            if author.id == 2:
                return 10
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service.determine_best_author(
            authors=[author_metadata, author2],
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result == author2

    def test_determine_best_author_with_verified_mapping(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        verified_mapping: AuthorMapping,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test determine_best_author prefers verified mapping."""
        library_id = 1
        author2 = AuthorMetadata(id=2, openlibrary_key="OL456A", name="Author 2")

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            if author_id == 1:
                return verified_mapping
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service.determine_best_author(
            authors=[author_metadata, author2],
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result == author_metadata

    def test_determine_best_author_with_user_photos(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test determine_best_author considers user photos."""
        library_id = 1
        author2 = AuthorMetadata(id=2, openlibrary_key="OL456A", name="Author 2")

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        def get_relationship_counts(author_id: int) -> RelationshipCounts:
            if author_id == 2:
                return RelationshipCounts(
                    alternate_names=0,
                    remote_ids=0,
                    photos=0,
                    links=0,
                    works=0,
                    work_subjects=0,
                    similarities=0,
                    user_metadata=0,
                    user_photos=3,
                )
            return RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )

        mock_relationship_repo.get_relationship_counts.side_effect = (
            get_relationship_counts
        )

        result = recommendation_service.determine_best_author(
            authors=[author_metadata, author2],
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result == author2


# ============================================================================
# calculate_metadata_score Tests
# ============================================================================


class TestCalculateMetadataScore:
    """Test calculate_metadata_score method."""

    @pytest.mark.parametrize(
        (
            "biography",
            "birth_date",
            "death_date",
            "location",
            "photo_url",
            "work_count",
            "ratings_count",
            "top_work",
            "expected",
        ),
        [
            (None, None, None, None, None, None, None, None, 0),
            ("Bio", None, None, None, None, None, None, None, 10),
            (None, "1950-01-01", None, None, None, None, None, None, 5),
            (None, None, "2020-01-01", None, None, None, None, None, 5),
            (None, None, None, "New York", None, None, None, None, 5),
            (
                None,
                None,
                None,
                None,
                "https://example.com/photo.jpg",
                None,
                None,
                None,
                10,
            ),
            (None, None, None, None, None, 10, None, None, 5),
            (None, None, None, None, None, 0, None, None, 0),
            (None, None, None, None, None, None, 100, None, 5),
            (None, None, None, None, None, None, 0, None, 0),
            (None, None, None, None, None, None, None, "Test Work", 5),
            (
                "Bio",
                "1950-01-01",
                "2020-01-01",
                "NY",
                "https://photo.jpg",
                10,
                100,
                "Work",
                50,
            ),
        ],
    )
    def test_calculate_metadata_score(
        self,
        biography: str | None,
        birth_date: str | None,
        death_date: str | None,
        location: str | None,
        photo_url: str | None,
        work_count: int | None,
        ratings_count: int | None,
        top_work: str | None,
        expected: int,
        recommendation_service: AuthorRecommendationService,
    ) -> None:
        """Test calculate_metadata_score with various field combinations."""
        author = AuthorMetadata(
            id=1,
            openlibrary_key="OL123A",
            name="Test Author",
            biography=biography,
            birth_date=birth_date,
            death_date=death_date,
            location=location,
            photo_url=photo_url,
            work_count=work_count,
            ratings_count=ratings_count,
            top_work=top_work,
        )

        result = recommendation_service.calculate_metadata_score(author)

        assert result == expected


# ============================================================================
# _calculate_score Tests
# ============================================================================


class TestCalculateScore:
    """Test _calculate_score method."""

    def test_calculate_score_basic(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with basic author."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service._calculate_score(
            author=author_metadata,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert isinstance(result, AuthorScore)
        assert result.book_count == 5
        assert result.is_verified is False
        assert result.metadata_completeness == 0
        assert result.user_photos_count == 0
        assert result.total == 500  # 5 books * 100

    def test_calculate_score_with_verified_mapping(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        verified_mapping: AuthorMapping,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with verified mapping."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return verified_mapping

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service._calculate_score(
            author=author_metadata,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result.is_verified is True
        assert result.total == 550  # 500 (books) + 50 (verified)

    def test_calculate_score_with_metadata(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata_full: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with full metadata."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=0,
            )
        )

        result = recommendation_service._calculate_score(
            author=author_metadata_full,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result.metadata_completeness == 50
        assert result.total == 550  # 500 (books) + 50 (metadata)

    def test_calculate_score_with_user_photos(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata: AuthorMetadata,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with user photos."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=3,
            )
        )

        result = recommendation_service._calculate_score(
            author=author_metadata,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result.user_photos_count == 3
        assert result.total == 545  # 500 (books) + 45 (3 photos * 15)

    def test_calculate_score_author_without_id(
        self,
        recommendation_service: AuthorRecommendationService,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with author without ID."""
        library_id = 1
        author = AuthorMetadata(id=None, openlibrary_key="OL123A", name="Test Author")

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return None

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 5

        result = recommendation_service._calculate_score(
            author=author,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result.user_photos_count == 0
        mock_relationship_repo.get_relationship_counts.assert_not_called()

    def test_calculate_score_all_factors(
        self,
        recommendation_service: AuthorRecommendationService,
        author_metadata_full: AuthorMetadata,
        verified_mapping: AuthorMapping,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test _calculate_score with all factors combined."""
        library_id = 1

        def get_mapping(author_id: int | None, lib_id: int) -> AuthorMapping | None:
            return verified_mapping

        def get_book_count(author: AuthorMetadata, lib_id: int) -> int:
            return 10

        mock_relationship_repo.get_relationship_counts.return_value = (
            RelationshipCounts(
                alternate_names=0,
                remote_ids=0,
                photos=0,
                links=0,
                works=0,
                work_subjects=0,
                similarities=0,
                user_metadata=0,
                user_photos=2,
            )
        )

        result = recommendation_service._calculate_score(
            author=author_metadata_full,
            library_id=library_id,
            get_mapping=get_mapping,
            get_book_count=get_book_count,
        )

        assert result.book_count == 10
        assert result.is_verified is True
        assert result.metadata_completeness == 50
        assert result.user_photos_count == 2
        assert (
            result.total == 1130
        )  # 1000 (books) + 50 (verified) + 50 (metadata) + 30 (photos)

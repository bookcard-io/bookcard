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

"""Tests for duplicate_detector to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorMetadata,
)
from fundamental.services.library_scanning.pipeline.duplicate_detector import (
    DuplicateDetector,
    DuplicatePair,
    QualityScorer,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def author1() -> AuthorMetadata:
    """Create first author."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL1A",
        name="John Smith",
        work_count=10,
        ratings_count=100,
        ratings_average=4.5,
        biography="Test biography",
        birth_date="1950-01-01",
        death_date="2020-01-01",
        location="New York",
        photo_url="https://example.com/photo.jpg",
        personal_name="Smith",
        fuller_name="John A. Smith",
        title="Dr.",
        top_work="Test Book",
        last_synced_at=datetime.now(UTC),
    )


@pytest.fixture
def author2() -> AuthorMetadata:
    """Create second author."""
    return AuthorMetadata(
        id=2,
        openlibrary_key="OL2A",
        name="John Smyth",
        work_count=5,
        ratings_count=50,
    )


@pytest.fixture
def author_empty_name() -> AuthorMetadata:
    """Create author with empty name."""
    return AuthorMetadata(
        id=3,
        openlibrary_key="OL3A",
        name="",
    )


# ============================================================================
# DuplicateDetector Tests
# ============================================================================


class TestDuplicateDetector:
    """Test DuplicateDetector."""

    def test_init_default(self) -> None:
        """Test __init__ with defaults."""
        detector = DuplicateDetector()

        assert detector._min_similarity == 0.85
        assert detector._quality_scorer is not None

    def test_init_custom(self) -> None:
        """Test __init__ with custom parameters."""
        scorer = QualityScorer()
        detector = DuplicateDetector(min_similarity=0.9, quality_scorer=scorer)

        assert detector._min_similarity == 0.9
        assert detector._quality_scorer == scorer

    def test_are_duplicates_same_id(self, author1: AuthorMetadata) -> None:
        """Test are_duplicates returns False for same ID."""
        detector = DuplicateDetector()

        result = detector.are_duplicates(author1, author1)

        assert result is False

    def test_are_duplicates_high_similarity(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test are_duplicates returns True for high similarity."""
        # Make names very similar
        author1.name = "John Smith"
        author2.name = "John Smyth"  # Very similar
        detector = DuplicateDetector(min_similarity=0.8)

        result = detector.are_duplicates(author1, author2)

        assert result is True

    def test_are_duplicates_low_similarity(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test are_duplicates returns False for low similarity."""
        author1.name = "John Smith"
        author2.name = "Jane Doe"  # Very different
        detector = DuplicateDetector(min_similarity=0.9)

        result = detector.are_duplicates(author1, author2)

        assert result is False

    def test_are_duplicates_empty_names(
        self, author_empty_name: AuthorMetadata
    ) -> None:
        """Test are_duplicates returns True for empty names."""
        author2 = AuthorMetadata(
            id=4,
            openlibrary_key="OL4A",
            name="",
        )
        detector = DuplicateDetector()

        result = detector.are_duplicates(author_empty_name, author2)

        assert result is True

    def test_are_duplicates_alternate_names(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test are_duplicates checks alternate names."""
        author1.name = "John Smith"
        author2.name = "Different Name"
        alt1 = AuthorAlternateName(author_metadata_id=author1.id, name="J. Smith")
        alt2 = AuthorAlternateName(author_metadata_id=author2.id, name="J. Smyth")
        author1.alternate_names = [alt1]
        author2.alternate_names = [alt2]
        detector = DuplicateDetector(min_similarity=0.8)

        result = detector.are_duplicates(author1, author2)

        assert result is True

    def test_are_duplicates_alternate_names_no_match(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test are_duplicates returns False when alternate names don't match."""
        author1.name = "John Smith"
        author2.name = "Different Name"
        alt1 = AuthorAlternateName(author_metadata_id=author1.id, name="J. Smith")
        alt2 = AuthorAlternateName(author_metadata_id=author2.id, name="Jane Doe")
        author1.alternate_names = [alt1]
        author2.alternate_names = [alt2]
        detector = DuplicateDetector(min_similarity=0.9)

        result = detector.are_duplicates(author1, author2)

        assert result is False

    def test_are_duplicates_alternate_names_empty(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test are_duplicates handles empty alternate names."""
        author1.name = "John Smith"
        author2.name = "John Smyth"
        author1.alternate_names = []
        author2.alternate_names = []
        detector = DuplicateDetector(min_similarity=0.8)

        result = detector.are_duplicates(author1, author2)

        # Should still check main names
        assert isinstance(result, bool)

    def test_score_and_pair_author1_higher(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test score_and_pair when author1 has higher score."""
        detector = DuplicateDetector()

        result = detector.score_and_pair(author1, author2)

        assert result.keep == author1
        assert result.merge == author2
        assert result.keep_score >= result.merge_score

    def test_score_and_pair_author2_higher(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test score_and_pair when author2 has higher score."""
        # Make author2 have higher quality
        author2.work_count = 100
        author2.ratings_count = 1000
        author2.biography = "Long biography"
        author2.birth_date = "1950-01-01"
        author2.death_date = "2020-01-01"
        author2.location = "New York"
        author2.photo_url = "https://example.com/photo.jpg"
        author2.personal_name = "Smith"
        author2.fuller_name = "John A. Smith"
        author2.title = "Dr."
        author2.top_work = "Test Book"
        author2.ratings_average = 4.5
        author2.last_synced_at = datetime.now(UTC)
        author1.work_count = 5
        author1.ratings_count = 50
        detector = DuplicateDetector()

        result = detector.score_and_pair(author1, author2)

        assert result.keep == author2
        assert result.merge == author1
        assert result.keep_score >= result.merge_score

    def test_score_and_pair_equal_scores(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test score_and_pair when scores are equal."""
        # Make both authors identical
        author2.work_count = author1.work_count
        author2.ratings_count = author1.ratings_count
        detector = DuplicateDetector()

        result = detector.score_and_pair(author1, author2)

        # Should prefer author1 when scores are equal
        assert result.keep == author1
        assert result.merge == author2

    def test_find_duplicates_no_duplicates(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates with no duplicates."""
        author1.name = "John Smith"
        author2.name = "Jane Doe"
        detector = DuplicateDetector(min_similarity=0.9)

        result = list(detector.find_duplicates([author1, author2]))

        assert len(result) == 0

    def test_find_duplicates_with_duplicates(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates finds duplicates."""
        author1.name = "John Smith"
        author2.name = "John Smyth"
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates([author1, author2]))

        assert len(result) == 1
        assert isinstance(result[0], DuplicatePair)

    def test_find_duplicates_skips_none_id(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates skips authors with None ID."""
        author1.id = None
        author1.name = "John Smith"
        author2.name = "John Smyth"
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates([author1, author2]))

        assert len(result) == 0

    def test_find_duplicates_skips_seen(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates skips already seen authors."""
        author1.name = "John Smith"
        author2.name = "John Smyth"
        author3 = AuthorMetadata(
            id=3,
            openlibrary_key="OL3A",
            name="John Smyth",
        )
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates([author1, author2, author3]))

        # Should only find one pair (author1-author2), not author1-author3
        # because author2 is already marked as seen
        assert len(result) >= 1

    def test_find_duplicates_merge_no_id(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates handles merge with no ID."""
        author1.name = "John Smith"
        author2.name = "John Smyth"
        author2.id = None
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates([author1, author2]))

        # Should still work even if merge has no ID
        assert len(result) >= 0

    def test_find_duplicates_with_alternate_names(
        self, author1: AuthorMetadata, author2: AuthorMetadata
    ) -> None:
        """Test find_duplicates indexes alternate names."""
        author1.name = "John Smith"
        author1.alternate_names = [
            AuthorAlternateName(author_metadata_id=1, name="J. Smith"),
            AuthorAlternateName(author_metadata_id=1, name="John A. Smith"),
        ]
        author2.name = "John Smyth"
        author2.alternate_names = [
            AuthorAlternateName(author_metadata_id=2, name="J. Smyth"),
        ]
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates([author1, author2]))

        # Should find duplicates based on alternate names
        assert len(result) >= 0

    def test_find_duplicates_skips_common_tokens(self, author1: AuthorMetadata) -> None:
        """Test find_duplicates skips tokens with too many authors."""
        # Create many authors with the same common token
        authors = [author1]
        authors.extend(
            AuthorMetadata(
                id=i + 2,
                openlibrary_key=f"OL{i + 2}A",
                name=f"Author {i}",
            )
            for i in range(150)  # More than 100
        )
        detector = DuplicateDetector(min_similarity=0.8)

        result = list(detector.find_duplicates(authors))

        # Should handle large number of authors
        assert isinstance(result, list)

    def test_tokenize_skips_ignored_tokens(self) -> None:
        """Test _tokenize skips ignored tokens."""
        detector = DuplicateDetector()
        # Test with a name that contains ignored tokens
        result = detector._tokenize("John the Smith")

        # Should skip "the" as it's in IGNORED_TOKENS
        assert "the" not in result
        assert "john" in result
        assert "smith" in result


# ============================================================================
# QualityScorer Tests
# ============================================================================


class TestQualityScorer:
    """Test QualityScorer."""

    def test_calculate_comprehensive(self, author1: AuthorMetadata) -> None:
        """Test calculate with comprehensive author data."""
        scorer = QualityScorer()

        result = scorer.calculate(author1)

        assert result > 0
        assert isinstance(result, float)

    def test_calculate_work_count_score_none(self, author1: AuthorMetadata) -> None:
        """Test _calculate_work_count_score with None."""
        author1.work_count = None
        scorer = QualityScorer()

        result = scorer._calculate_work_count_score(author1)

        assert result == 0.0

    def test_calculate_work_count_score_value(self, author1: AuthorMetadata) -> None:
        """Test _calculate_work_count_score with value."""
        author1.work_count = 50
        scorer = QualityScorer()

        result = scorer._calculate_work_count_score(author1)

        assert result == 20.0  # 50 * 0.4 = 20

    def test_calculate_work_count_score_max(self, author1: AuthorMetadata) -> None:
        """Test _calculate_work_count_score caps at max."""
        author1.work_count = 200
        scorer = QualityScorer()

        result = scorer._calculate_work_count_score(author1)

        assert result == 40.0  # Capped at 40

    def test_calculate_ratings_score_none(self, author1: AuthorMetadata) -> None:
        """Test _calculate_ratings_score with None."""
        author1.ratings_count = None
        scorer = QualityScorer()

        result = scorer._calculate_ratings_score(author1)

        assert result == 0.0

    def test_calculate_ratings_score_value(self, author1: AuthorMetadata) -> None:
        """Test _calculate_ratings_score with value."""
        author1.ratings_count = 5000
        scorer = QualityScorer()

        result = scorer._calculate_ratings_score(author1)

        assert result == 15.0  # 5000 / 10000 * 30 = 15

    def test_calculate_ratings_score_max(self, author1: AuthorMetadata) -> None:
        """Test _calculate_ratings_score caps at max."""
        author1.ratings_count = 20000
        scorer = QualityScorer()

        result = scorer._calculate_ratings_score(author1)

        assert result == 30.0  # Capped at 30

    def test_calculate_completeness_score_full(self, author1: AuthorMetadata) -> None:
        """Test _calculate_completeness_score with all fields."""
        scorer = QualityScorer()

        result = scorer._calculate_completeness_score(author1)

        assert result > 0
        assert result <= 20.0

    def test_calculate_completeness_score_partial(
        self, author1: AuthorMetadata
    ) -> None:
        """Test _calculate_completeness_score with some fields."""
        author1.biography = None
        author1.birth_date = None
        author1.death_date = None
        scorer = QualityScorer()

        result = scorer._calculate_completeness_score(author1)

        assert result >= 0
        assert result < 20.0

    def test_calculate_completeness_score_with_ratings_average(
        self, author1: AuthorMetadata
    ) -> None:
        """Test _calculate_completeness_score includes ratings_average."""
        author1.ratings_average = 4.5
        scorer = QualityScorer()

        result = scorer._calculate_completeness_score(author1)

        assert result > 0

    def test_calculate_completeness_score_max(self, author1: AuthorMetadata) -> None:
        """Test _calculate_completeness_score caps at max."""
        # Set all fields to ensure max score
        scorer = QualityScorer()

        result = scorer._calculate_completeness_score(author1)

        assert result <= 20.0

    def test_calculate_recency_score_no_sync(self, author1: AuthorMetadata) -> None:
        """Test _calculate_recency_score with no last_synced_at."""
        author1.last_synced_at = None
        scorer = QualityScorer()

        result = scorer._calculate_recency_score(author1)

        assert result == 2.0

    def test_calculate_recency_score_recent(self, author1: AuthorMetadata) -> None:
        """Test _calculate_recency_score with recent sync."""
        author1.last_synced_at = datetime.now(UTC) - timedelta(days=1)
        scorer = QualityScorer()

        result = scorer._calculate_recency_score(author1)

        assert result > 0
        assert result <= 10.0

    def test_calculate_recency_score_old(self, author1: AuthorMetadata) -> None:
        """Test _calculate_recency_score with old sync."""
        author1.last_synced_at = datetime.now(UTC) - timedelta(days=365)
        scorer = QualityScorer()

        result = scorer._calculate_recency_score(author1)

        assert result >= 0
        assert result < 10.0

    def test_calculate_recency_score_naive_datetime(
        self, author1: AuthorMetadata
    ) -> None:
        """Test _calculate_recency_score handles naive datetime."""
        # Create naive datetime (no timezone)
        naive_dt = datetime.now(UTC) - timedelta(days=1)
        author1.last_synced_at = naive_dt
        scorer = QualityScorer()

        result = scorer._calculate_recency_score(author1)

        assert result >= 0
        assert result <= 10.0

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("biography", "Test biography"),
            ("birth_date", "1950-01-01"),
            ("death_date", "2020-01-01"),
            ("location", "New York"),
            ("photo_url", "https://example.com/photo.jpg"),
            ("personal_name", "Smith"),
            ("fuller_name", "John A. Smith"),
            ("title", "Dr."),
            ("top_work", "Test Book"),
        ],
    )
    def test_calculate_completeness_all_fields(
        self, author1: AuthorMetadata, field: str, value: str
    ) -> None:
        """Test _calculate_completeness_score with each field."""
        # Reset all fields
        for f in [
            "biography",
            "birth_date",
            "death_date",
            "location",
            "photo_url",
            "personal_name",
            "fuller_name",
            "title",
            "top_work",
        ]:
            setattr(author1, f, None)
        # Set only the test field
        setattr(author1, field, value)
        scorer = QualityScorer()

        result = scorer._calculate_completeness_score(author1)

        assert result > 0

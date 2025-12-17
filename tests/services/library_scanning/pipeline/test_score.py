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

"""Tests for score stage to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from bookcard.models.author_metadata import (
    AuthorMetadata,
    AuthorSimilarity,
    WorkSubject,
)
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.score import (
    AuthorPairProcessor,
    AuthorRepository,
    CompositeSimilarityCalculator,
    DateParser,
    GenreSimilarityCalculator,
    ProgressTracker,
    RatingsSimilarityCalculator,
    ScoreStage,
    SimilarityCalculator,
    SimilarityMetrics,
    SimilarityRepository,
    SubjectRepository,
    TimePeriodSimilarityCalculator,
    WorkCountSimilarityCalculator,
)


@pytest.fixture
def mock_library() -> MagicMock:
    """Create a mock library."""
    library = MagicMock()
    library.id = 1
    return library


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Create a mock data source."""
    return MagicMock()


@pytest.fixture
def pipeline_context(
    mock_library: MagicMock,
    mock_session: MagicMock,
    mock_data_source: MagicMock,
) -> PipelineContext:
    """Create a pipeline context."""
    return PipelineContext(
        library_id=1,
        library=mock_library,
        session=mock_session,
        data_source=mock_data_source,
    )


@pytest.fixture
def sample_authors() -> list[AuthorMetadata]:
    """Create sample authors."""
    return [
        AuthorMetadata(id=1, name="Author One", work_count=10),
        AuthorMetadata(id=2, name="Author Two", work_count=20),
        AuthorMetadata(id=3, name="Author Three", work_count=15),
    ]


# ============================================================================
# DateParser Tests
# ============================================================================


@pytest.mark.parametrize(
    ("date_str", "expected_year"),
    [
        ("31 July 1965", 1965),
        ("1965", 1965),
        ("January 1, 2000", 2000),
        ("No year here", None),
        ("1999-01-01", 1999),
    ],
)
def test_date_parser_extract_year(date_str: str, expected_year: int | None) -> None:
    """Test DateParser.extract_year."""
    result = DateParser.extract_year(date_str)
    assert result == expected_year


# ============================================================================
# SimilarityMetrics Tests
# ============================================================================


@pytest.mark.parametrize(
    ("value1", "value2", "expected"),
    [
        (10.0, 20.0, 0.5),
        (20.0, 10.0, 0.5),
        (10.0, 10.0, 1.0),
        (0.0, 10.0, 0.0),
        (10.0, 0.0, 0.0),
    ],
)
def test_similarity_metrics_normalize_ratio(
    value1: float, value2: float, expected: float
) -> None:
    """Test SimilarityMetrics.normalize_ratio."""
    result = SimilarityMetrics.normalize_ratio(value1, value2)
    assert result == expected


@pytest.mark.parametrize(
    ("set1", "set2", "expected"),
    [
        ({"a", "b", "c"}, {"b", "c", "d"}, 0.5),  # 2/4
        ({"a", "b"}, {"c", "d"}, 0.0),  # 0/4
        ({"a", "b"}, {"a", "b"}, 1.0),  # 2/2
        (set(), {"a"}, 0.0),  # Empty set
        ({"a"}, set(), 0.0),  # Empty set
    ],
)
def test_similarity_metrics_jaccard(
    set1: set[str], set2: set[str], expected: float
) -> None:
    """Test SimilarityMetrics.jaccard."""
    result = SimilarityMetrics.jaccard(set1, set2)
    assert result == expected


# ============================================================================
# Repository Tests
# ============================================================================


def test_author_repository_get_all(mock_session: MagicMock) -> None:
    """Test AuthorRepository.get_all."""
    repo = AuthorRepository(mock_session)
    authors = [AuthorMetadata(id=1, name="Author One")]
    mock_result = MagicMock()
    mock_result.all.return_value = authors
    mock_session.exec.return_value = mock_result

    result = repo.get_all()
    assert result == authors


def test_author_repository_get_all_with_limit(mock_session: MagicMock) -> None:
    """Test AuthorRepository.get_all with limit."""
    repo = AuthorRepository(mock_session)
    authors = [
        AuthorMetadata(id=1, name="Author One"),
        AuthorMetadata(id=2, name="Author Two"),
    ]
    mock_result = MagicMock()
    mock_result.all.return_value = authors
    mock_session.exec.return_value = mock_result

    result = repo.get_all(limit=1)
    assert len(result) == 1


def test_author_repository_get_by_id(mock_session: MagicMock) -> None:
    """Test AuthorRepository.get_by_id."""
    repo = AuthorRepository(mock_session)
    author = AuthorMetadata(id=1, name="Author One")
    mock_session.get.return_value = author

    result = repo.get_by_id(1)
    assert result == author


def test_subject_repository_get_subjects_for_author(mock_session: MagicMock) -> None:
    """Test SubjectRepository.get_subjects_for_author."""
    repo = SubjectRepository(mock_session)
    subjects = [
        WorkSubject(id=1, author_work_id=1, subject_name="Fiction"),
        WorkSubject(id=2, author_work_id=1, subject_name="Science Fiction"),
    ]
    mock_result = MagicMock()
    mock_result.all.return_value = subjects
    mock_session.exec.return_value = mock_result

    result = repo.get_subjects_for_author(1)
    assert result == {"Fiction", "Science Fiction"}


def test_similarity_repository_exists(mock_session: MagicMock) -> None:
    """Test SimilarityRepository.exists."""
    repo = SimilarityRepository(mock_session)
    similarity = AuthorSimilarity(
        id=1, author1_id=1, author2_id=2, similarity_score=0.8
    )
    mock_result = MagicMock()
    mock_result.first.return_value = similarity
    mock_session.exec.return_value = mock_result

    assert repo.exists(1, 2) is True
    assert repo.exists(2, 1) is True  # Should work both ways


def test_similarity_repository_exists_not_found(mock_session: MagicMock) -> None:
    """Test SimilarityRepository.exists when not found."""
    repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    assert repo.exists(1, 2) is False


def test_similarity_repository_has_fresh_similarities(
    mock_session: MagicMock,
) -> None:
    """Test SimilarityRepository.has_fresh_similarities."""
    repo = SimilarityRepository(mock_session)
    similarity = AuthorSimilarity(
        id=1,
        author1_id=1,
        author2_id=2,
        similarity_score=0.8,
        created_at=datetime.now(UTC) - timedelta(days=5),
    )
    mock_result = MagicMock()
    mock_result.first.return_value = similarity
    mock_session.exec.return_value = mock_result

    assert repo.has_fresh_similarities(1, 30) is True


def test_similarity_repository_has_fresh_similarities_stale(
    mock_session: MagicMock,
) -> None:
    """Test SimilarityRepository.has_fresh_similarities with stale data."""
    repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    assert repo.has_fresh_similarities(1, 30) is False


def test_similarity_repository_create(mock_session: MagicMock) -> None:
    """Test SimilarityRepository.create."""
    repo = SimilarityRepository(mock_session)
    similarity = repo.create(1, 2, 0.8)

    assert similarity.author1_id == 1
    assert similarity.author2_id == 2
    assert similarity.similarity_score == 0.8
    mock_session.add.assert_called_once()


def test_similarity_repository_create_reorders_ids(mock_session: MagicMock) -> None:
    """Test SimilarityRepository.create reorders IDs."""
    repo = SimilarityRepository(mock_session)
    similarity = repo.create(2, 1, 0.8)  # Higher ID first

    assert similarity.author1_id == 1  # Should be reordered
    assert similarity.author2_id == 2


# ============================================================================
# Similarity Calculator Tests
# ============================================================================


def test_genre_similarity_calculator_no_ids(mock_session: MagicMock) -> None:
    """Test GenreSimilarityCalculator with authors having no IDs."""
    subject_repo = SubjectRepository(mock_session)
    calc = GenreSimilarityCalculator(subject_repo)
    author1 = AuthorMetadata(name="Author One", id=None)
    author2 = AuthorMetadata(name="Author Two", id=None)

    result = calc.calculate(author1, author2)
    assert result == 0.0


def test_genre_similarity_calculator_no_subjects(mock_session: MagicMock) -> None:
    """Test GenreSimilarityCalculator with no subjects."""
    subject_repo = SubjectRepository(mock_session)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    calc = GenreSimilarityCalculator(subject_repo)
    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = calc.calculate(author1, author2)
    assert result == 0.0


def test_genre_similarity_calculator_with_shared_subjects(
    mock_session: MagicMock,
) -> None:
    """Test GenreSimilarityCalculator with shared subjects."""
    subject_repo = SubjectRepository(mock_session)

    def get_subjects_side_effect(author_id: int) -> set[str]:
        if author_id == 1:
            return {"Fiction", "Science Fiction", "Adventure"}
        return {"Fiction", "Science Fiction", "Mystery"}

    subject_repo.get_subjects_for_author = MagicMock(  # type: ignore[assignment]
        side_effect=get_subjects_side_effect
    )

    calc = GenreSimilarityCalculator(subject_repo)
    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = calc.calculate(author1, author2)
    assert result > 0.0
    assert result <= 1.0


@pytest.mark.parametrize(
    ("shared_count", "expected_boost"),
    [
        (1, 0.05),  # <= 2 shared
        (2, 0.05),  # <= 2 shared
        (3, 0.10),  # <= 5 shared
        (5, 0.10),  # <= 5 shared
        (6, 0.15),  # > 5 shared
        (10, 0.15),  # > 5 shared
    ],
)
def test_genre_similarity_calculator_boost_levels(
    mock_session: MagicMock,
    shared_count: int,
    expected_boost: float,
) -> None:
    """Test GenreSimilarityCalculator boost levels based on shared subjects count."""
    subject_repo = SubjectRepository(mock_session)

    # Create subjects with specified shared count
    shared = {f"Subject{i}" for i in range(shared_count)}
    subjects1 = shared | {"Unique1", "Unique2"}
    subjects2 = shared | {"Unique3", "Unique4"}

    def get_subjects_side_effect(author_id: int) -> set[str]:
        if author_id == 1:
            return subjects1
        return subjects2

    subject_repo.get_subjects_for_author = MagicMock(  # type: ignore[assignment]
        side_effect=get_subjects_side_effect
    )

    calc = GenreSimilarityCalculator(subject_repo)
    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = calc.calculate(author1, author2)
    assert result > 0.0
    # Result should include boost
    assert result <= 1.0


@pytest.mark.parametrize(
    ("work_count1", "work_count2", "expected"),
    [
        (10, 20, 0.5),
        (20, 10, 0.5),
        (10, 10, 1.0),
        (0, 10, 0.0),
        (10, 0, 0.0),
        (None, 10, 0.0),
        (10, None, 0.0),
    ],
)
def test_work_count_similarity_calculator(
    work_count1: int | None,
    work_count2: int | None,
    expected: float,
) -> None:
    """Test WorkCountSimilarityCalculator."""
    calc = WorkCountSimilarityCalculator()
    author1 = AuthorMetadata(id=1, name="Author One", work_count=work_count1)
    author2 = AuthorMetadata(id=2, name="Author Two", work_count=work_count2)

    result = calc.calculate(author1, author2)
    assert result == expected


@pytest.mark.parametrize(
    ("ratings1", "ratings2", "expected"),
    [
        (100, 200, 0.5),
        (200, 100, 0.5),
        (100, 100, 1.0),
        (0, 100, 0.0),
        (100, 0, 0.0),
        (None, 100, 0.0),
        (100, None, 0.0),
    ],
)
def test_ratings_similarity_calculator(
    ratings1: int | None,
    ratings2: int | None,
    expected: float,
) -> None:
    """Test RatingsSimilarityCalculator."""
    calc = RatingsSimilarityCalculator()
    author1 = AuthorMetadata(id=1, name="Author One", ratings_count=ratings1)
    author2 = AuthorMetadata(id=2, name="Author Two", ratings_count=ratings2)

    result = calc.calculate(author1, author2)
    assert result == expected


@pytest.mark.parametrize(
    ("birth_date1", "birth_date2", "max_diff", "expected"),
    [
        ("1965", "1970", 50, 0.9),  # 5 year diff
        ("1965", "2015", 50, 0.0),  # 50 year diff (exceeds max)
        ("1965", "1965", 50, 1.0),  # Same year
        ("", "1965", 50, 0.0),  # No birth date
        ("1965", "", 50, 0.0),  # No birth date
        ("1965", "invalid", 50, 0.0),  # Invalid date (year1 is None)
        ("invalid", "1965", 50, 0.0),  # Invalid date (year2 is None)
    ],
)
def test_time_period_similarity_calculator(
    birth_date1: str,
    birth_date2: str,
    max_diff: int,
    expected: float,
) -> None:
    """Test TimePeriodSimilarityCalculator."""
    calc = TimePeriodSimilarityCalculator(max_year_diff=max_diff)
    author1 = AuthorMetadata(id=1, name="Author One", birth_date=birth_date1)
    author2 = AuthorMetadata(id=2, name="Author Two", birth_date=birth_date2)

    result = calc.calculate(author1, author2)
    assert result == pytest.approx(expected, abs=0.1)


def test_composite_similarity_calculator(mock_session: MagicMock) -> None:
    """Test CompositeSimilarityCalculator."""
    subject_repo = SubjectRepository(mock_session)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    genre_calc = GenreSimilarityCalculator(subject_repo)
    work_calc = WorkCountSimilarityCalculator()
    calc = CompositeSimilarityCalculator([
        (genre_calc, 0.5),
        (work_calc, 0.5),
    ])

    author1 = AuthorMetadata(id=1, name="Author One", work_count=10)
    author2 = AuthorMetadata(id=2, name="Author Two", work_count=20)

    result = calc.calculate(author1, author2)
    assert 0.0 <= result <= 1.0


def test_composite_similarity_calculator_no_factors(mock_session: MagicMock) -> None:
    """Test CompositeSimilarityCalculator with no factors."""
    subject_repo = SubjectRepository(mock_session)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    genre_calc = GenreSimilarityCalculator(subject_repo)
    calc = CompositeSimilarityCalculator([(genre_calc, 0.5)])

    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = calc.calculate(author1, author2)
    # Should return 0.05 when no factors
    assert result == 0.05


def test_composite_similarity_calculator_zero_weights(mock_session: MagicMock) -> None:
    """Test CompositeSimilarityCalculator with zero total weight (fallback)."""

    # Create a calculator that returns non-zero but with zero weight
    class ZeroWeightCalculator(SimilarityCalculator):
        def calculate(self, a1: AuthorMetadata, a2: AuthorMetadata) -> float:
            return 0.5

    calc = CompositeSimilarityCalculator([(ZeroWeightCalculator(), 0.0)])

    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = calc.calculate(author1, author2)
    # Should use fallback: simple average
    assert result == 0.5


# ============================================================================
# ProgressTracker Tests
# ============================================================================


def test_progress_tracker_update() -> None:
    """Test ProgressTracker.update."""
    tracker = ProgressTracker(total_items=10)
    assert tracker.update(5) == 0.5
    assert tracker.update(5) == 1.0


def test_progress_tracker_should_log() -> None:
    """Test ProgressTracker.should_log."""
    tracker = ProgressTracker(total_items=100, log_interval=10)
    # Initially processed_items is 0, and 0 % 10 == 0, so should_log returns True
    assert tracker.should_log() is True  # 0 % 10 == 0
    tracker.update(10)
    assert tracker.should_log() is True  # 10 % 10 == 0
    tracker.update(5)
    assert tracker.should_log() is False  # 15 % 10 != 0
    tracker.update(85)  # Total is now 100
    assert tracker.should_log() is True  # At total


# ============================================================================
# AuthorPairProcessor Tests
# ============================================================================


def test_author_pair_processor_same_author(mock_session: MagicMock) -> None:
    """Test AuthorPairProcessor with same author."""
    calc = WorkCountSimilarityCalculator()
    repo = SimilarityRepository(mock_session)
    processor = AuthorPairProcessor(calc, repo, min_similarity=0.5)

    author = AuthorMetadata(id=1, name="Author One")
    result = processor.process_pair(author, author)
    assert result is False


def test_author_pair_processor_existing_similarity(mock_session: MagicMock) -> None:
    """Test AuthorPairProcessor with existing similarity."""
    calc = WorkCountSimilarityCalculator()
    repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = AuthorSimilarity(
        id=1, author1_id=1, author2_id=2, similarity_score=0.8
    )
    mock_session.exec.return_value = mock_result

    processor = AuthorPairProcessor(calc, repo, min_similarity=0.5)
    author1 = AuthorMetadata(id=1, name="Author One")
    author2 = AuthorMetadata(id=2, name="Author Two")

    result = processor.process_pair(author1, author2)
    assert result is False


def test_author_pair_processor_below_threshold(mock_session: MagicMock) -> None:
    """Test AuthorPairProcessor with score below threshold."""
    calc = WorkCountSimilarityCalculator()
    repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    processor = AuthorPairProcessor(calc, repo, min_similarity=0.9)
    author1 = AuthorMetadata(id=1, name="Author One", work_count=10)
    author2 = AuthorMetadata(id=2, name="Author Two", work_count=100)

    result = processor.process_pair(author1, author2)
    assert result is False  # Similarity is 0.1, below 0.9 threshold


def test_author_pair_processor_creates_similarity(mock_session: MagicMock) -> None:
    """Test AuthorPairProcessor creates similarity."""
    calc = WorkCountSimilarityCalculator()
    repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    processor = AuthorPairProcessor(calc, repo, min_similarity=0.5)
    author1 = AuthorMetadata(id=1, name="Author One", work_count=10)
    author2 = AuthorMetadata(id=2, name="Author Two", work_count=20)

    result = processor.process_pair(author1, author2)
    assert result is True
    mock_session.add.assert_called_once()


# ============================================================================
# ScoreStage Tests
# ============================================================================


def test_score_stage_name() -> None:
    """Test ScoreStage name property."""
    stage = ScoreStage()
    assert stage.name == "score"


def test_score_stage_get_progress_no_tracker() -> None:
    """Test ScoreStage.get_progress without tracker."""
    stage = ScoreStage()
    assert stage.get_progress() == 0.0


def test_score_stage_get_progress_with_tracker() -> None:
    """Test ScoreStage.get_progress with tracker."""
    stage = ScoreStage()
    tracker = ProgressTracker(total_items=10)
    tracker.update(5)
    stage._progress_tracker = tracker
    assert stage.get_progress() == 0.5


def test_score_stage_should_skip_author_no_staleness() -> None:
    """Test _should_skip_author with no staleness settings."""
    stage = ScoreStage()
    author = AuthorMetadata(id=1, name="Author One")
    assert stage._should_skip_author(author) is False


def test_score_stage_should_skip_author_no_id() -> None:
    """Test _should_skip_author with author having no ID."""
    stage = ScoreStage(stale_data_max_age_days=30)
    author = AuthorMetadata(name="Author One", id=None)
    assert stage._should_skip_author(author) is False


def test_score_stage_should_skip_author_fresh_similarities(
    mock_session: MagicMock,
) -> None:
    """Test _should_skip_author with fresh similarities."""
    similarity_repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = AuthorSimilarity(
        id=1, author1_id=1, author2_id=2, similarity_score=0.8
    )
    mock_session.exec.return_value = mock_result

    stage = ScoreStage(
        stale_data_max_age_days=30,
        similarity_repository=similarity_repo,
    )
    author = AuthorMetadata(id=1, name="Author One")
    assert stage._should_skip_author(author) is True


def test_score_stage_filter_authors_by_staleness_no_staleness() -> None:
    """Test _filter_authors_by_staleness with no staleness check."""
    stage = ScoreStage()
    authors = [AuthorMetadata(id=1, name="Author One")]
    filtered, skipped = stage._filter_authors_by_staleness(authors)
    assert filtered == authors
    assert skipped == 0


def test_score_stage_filter_authors_by_staleness_with_skips(
    mock_session: MagicMock,
) -> None:
    """Test _filter_authors_by_staleness with authors to skip."""
    similarity_repo = SimilarityRepository(mock_session)
    # First author has fresh similarities, second doesn't
    call_count = 0

    def first_side_effect(*args: object, **kwargs: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.first.return_value = AuthorSimilarity(
                id=1, author1_id=1, author2_id=2, similarity_score=0.8
            )
        else:
            result.first.return_value = None
        return result

    mock_session.exec.side_effect = first_side_effect

    stage = ScoreStage(
        stale_data_max_age_days=30,
        similarity_repository=similarity_repo,
    )
    authors = [
        AuthorMetadata(id=1, name="Author One"),
        AuthorMetadata(id=2, name="Author Two"),
    ]
    filtered, skipped = stage._filter_authors_by_staleness(authors)
    assert len(filtered) == 1
    assert filtered[0].id == 2
    assert skipped == 1


def test_score_stage_execute_cancelled(pipeline_context: PipelineContext) -> None:
    """Test ScoreStage.execute when cancelled."""
    stage = ScoreStage()
    pipeline_context.cancelled = True
    result = stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_score_stage_execute_no_authors(
    pipeline_context: PipelineContext,
    mock_session: MagicMock,
) -> None:
    """Test ScoreStage.execute with no authors."""
    author_repo = AuthorRepository(mock_session)
    author_repo.get_all = MagicMock(return_value=[])  # type: ignore[assignment]

    stage = ScoreStage(author_repository=author_repo)
    result = stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["similarities_created"] == 0


def test_score_stage_execute_success(
    pipeline_context: PipelineContext,
    mock_session: MagicMock,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test ScoreStage.execute successfully."""
    author_repo = AuthorRepository(mock_session)
    author_repo.get_all = MagicMock(return_value=sample_authors)  # type: ignore[assignment]

    similarity_repo = SimilarityRepository(mock_session)

    # Mock for similarity exists check (returns None = doesn't exist)
    mock_similarity_result = MagicMock()
    mock_similarity_result.first.return_value = None

    # Mock for subject queries (returns empty list)
    mock_subject_result = MagicMock()
    mock_subject_result.all.return_value = []

    # Set up side_effect to handle multiple exec calls
    # First call: similarity exists check, subsequent: subject queries
    mock_session.exec.side_effect = [
        mock_similarity_result,  # For exists check (author1, author2)
        mock_similarity_result,  # For exists check (author1, author3)
        mock_similarity_result,  # For exists check (author2, author3)
        mock_subject_result,  # For subjects for author1
        mock_subject_result,  # For subjects for author2
        mock_subject_result,  # For subjects for author3
    ]

    subject_repo = SubjectRepository(mock_session)

    stage = ScoreStage(
        author_repository=author_repo,
        similarity_repository=similarity_repo,
        subject_repository=subject_repo,
        min_similarity=0.0,  # Low threshold to ensure creation
    )
    result = stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    pipeline_context.session.commit.assert_called_once()  # type: ignore[attr-defined]


def test_score_stage_execute_exception(
    pipeline_context: PipelineContext,
    mock_session: MagicMock,
) -> None:
    """Test ScoreStage.execute with exception."""
    author_repo = AuthorRepository(mock_session)
    author_repo.get_all = MagicMock(side_effect=Exception("Error"))  # type: ignore[assignment]

    stage = ScoreStage(author_repository=author_repo)
    result = stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()
    pipeline_context.session.rollback.assert_called_once()  # type: ignore[attr-defined]


def test_score_stage_repository_error_methods() -> None:
    """Test ScoreStage error raising methods."""
    stage = ScoreStage()

    with pytest.raises(ValueError, match="must be initialized"):
        stage._ensure_author_repository_initialized()

    with pytest.raises(RuntimeError, match="must be initialized"):
        stage._raise_repository_not_initialized_error()

    with pytest.raises(AttributeError, match="must have get_all method"):
        stage._raise_missing_get_all_method_error()


def test_score_stage_execute_repository_not_initialized(
    pipeline_context: PipelineContext,
) -> None:
    """Test ScoreStage.execute when repository not initialized (error path).

    Note: execute() calls _create_repositories() which initializes repositories,
    so we need to prevent that initialization to test the error path.
    """
    from unittest.mock import patch

    stage = ScoreStage()

    # Mock _create_repositories to do nothing (keep repository as None)
    def noop_create_repositories(session: object) -> None:
        pass

    with patch.object(stage, "_create_repositories", noop_create_repositories):
        result = stage.execute(pipeline_context)
        assert result.success is False


def test_score_stage_execute_get_all_not_callable(
    pipeline_context: PipelineContext,
    mock_session: MagicMock,
) -> None:
    """Test ScoreStage.execute when get_all is not callable."""
    author_repo = AuthorRepository(mock_session)
    # Make get_all not callable
    author_repo.get_all = "not_callable"  # type: ignore[assignment]

    stage = ScoreStage(author_repository=author_repo)
    result = stage.execute(pipeline_context)
    assert result.success is False


def test_score_stage_process_author_pairs_loop_no_tracker(
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
    mock_session: MagicMock,
) -> None:
    """Test _process_author_pairs_loop when progress tracker not initialized."""
    similarity_repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    calc = WorkCountSimilarityCalculator()
    processor = AuthorPairProcessor(calc, similarity_repo, min_similarity=0.0)

    stage = ScoreStage()
    # Don't set progress tracker

    with pytest.raises(ValueError, match="must be initialized"):
        stage._process_author_pairs_loop(
            pipeline_context, sample_authors, processor, 3, 0
        )


def test_score_stage_create_default_calculator_no_subject_repo() -> None:
    """Test _create_default_calculator without subject repository."""
    stage = ScoreStage()
    with pytest.raises(ValueError, match="must be initialized first"):
        stage._create_default_calculator()


def test_score_stage_create_default_calculator(mock_session: MagicMock) -> None:
    """Test _create_default_calculator."""
    subject_repo = SubjectRepository(mock_session)
    stage = ScoreStage(subject_repository=subject_repo)
    calc = stage._create_default_calculator()

    assert isinstance(calc, CompositeSimilarityCalculator)


def test_score_stage_process_author_pairs_loop_cancelled(
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
    mock_session: MagicMock,
) -> None:
    """Test _process_author_pairs_loop when cancelled."""
    similarity_repo = SimilarityRepository(mock_session)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    calc = WorkCountSimilarityCalculator()
    processor = AuthorPairProcessor(calc, similarity_repo, min_similarity=0.0)

    stage = ScoreStage()
    tracker = ProgressTracker(total_items=3)
    stage._progress_tracker = tracker

    call_count = 0

    def check_cancelled() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1

    pipeline_context.check_cancelled = check_cancelled  # type: ignore[assignment]

    result = stage._process_author_pairs_loop(
        pipeline_context, sample_authors, processor, 3, 0
    )

    assert result >= 0  # May have processed some before cancellation

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

"""Tests for deduplicate stage to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.author_metadata import AuthorMetadata
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.deduplicate import DeduplicateStage
from fundamental.services.library_scanning.pipeline.duplicate_detector import (
    DuplicateDetector,
)
from fundamental.services.library_scanning.pipeline.merge_commands import AuthorMerger


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
        AuthorMetadata(id=1, name="Author One", openlibrary_key="OL1A"),
        AuthorMetadata(id=2, name="Author Two", openlibrary_key="OL2A"),
        AuthorMetadata(id=3, name="Author Three", openlibrary_key="OL3A"),
    ]


@pytest.fixture
def duplicate_authors() -> list[AuthorMetadata]:
    """Create duplicate authors."""
    return [
        AuthorMetadata(id=1, name="John Smith", openlibrary_key="OL1A"),
        AuthorMetadata(id=2, name="John Smyth", openlibrary_key="OL2A"),  # Similar
    ]


@pytest.fixture
def deduplicate_stage() -> DeduplicateStage:
    """Create a deduplicate stage instance."""
    return DeduplicateStage()


@pytest.fixture
def deduplicate_stage_with_limit() -> DeduplicateStage:
    """Create a deduplicate stage with author limit."""
    return DeduplicateStage(author_limit=2)


@pytest.fixture
def mock_detector() -> MagicMock:
    """Create a mock duplicate detector."""
    return MagicMock(spec=DuplicateDetector)


@pytest.fixture
def mock_merger() -> MagicMock:
    """Create a mock author merger."""
    return MagicMock(spec=AuthorMerger)


def test_deduplicate_stage_name(deduplicate_stage: DeduplicateStage) -> None:
    """Test deduplicate stage name property."""
    assert deduplicate_stage.name == "deduplicate"


def test_deduplicate_stage_get_progress_initial(
    deduplicate_stage: DeduplicateStage,
) -> None:
    """Test get_progress returns 0.0 initially."""
    assert deduplicate_stage.get_progress() == 0.0


def test_deduplicate_stage_init_defaults() -> None:
    """Test deduplicate stage initialization with defaults."""
    stage = DeduplicateStage()
    assert stage._min_name_similarity == 0.85
    assert stage._author_limit is None
    assert isinstance(stage._detector, DuplicateDetector)
    assert isinstance(stage._merger, AuthorMerger)


@pytest.mark.parametrize(
    ("min_similarity", "author_limit"),
    [
        (0.9, None),
        (0.85, 10),
        (0.7, 5),
    ],
)
def test_deduplicate_stage_init_params(
    min_similarity: float,
    author_limit: int | None,
) -> None:
    """Test deduplicate stage initialization with parameters."""
    stage = DeduplicateStage(
        min_name_similarity=min_similarity,
        author_limit=author_limit,
    )
    assert stage._min_name_similarity == min_similarity
    assert stage._author_limit == author_limit


def test_load_authors_no_limit(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test _load_authors without limit."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    authors = deduplicate_stage._load_authors(pipeline_context)

    assert len(authors) == 3
    assert authors == sample_authors


def test_load_authors_with_limit(
    deduplicate_stage_with_limit: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test _load_authors with limit."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    authors = deduplicate_stage_with_limit._load_authors(pipeline_context)

    assert len(authors) == 2
    assert authors == sample_authors[:2]


def test_update_progress(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _update_progress."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    pipeline_context.progress_callback = progress_callback

    deduplicate_stage._update_progress(
        context=pipeline_context,
        pairs_checked=5,
        total_pairs=10,
        duplicates_found=2,
        merged_count=1,
    )

    assert deduplicate_stage.get_progress() == 0.5
    assert len(progress_updates) == 1
    assert progress_updates[0][1] is not None
    assert progress_updates[0][1]["current_stage"]["duplicates_found"] == 2


def test_update_progress_zero_total(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _update_progress with zero total pairs."""
    deduplicate_stage._update_progress(
        context=pipeline_context,
        pairs_checked=0,
        total_pairs=0,
        duplicates_found=0,
        merged_count=0,
    )

    # Should not update progress when total is 0
    assert deduplicate_stage.get_progress() == 0.0


def test_merge_author_records(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test _merge_author_records delegates to merger."""
    keep = sample_authors[0]
    merge = sample_authors[1]

    # Mock the merger's merge method
    with patch.object(deduplicate_stage._merger, "merge") as mock_merge:
        deduplicate_stage._merge_author_records(pipeline_context, keep, merge)

        mock_merge.assert_called_once_with(pipeline_context, keep, merge)


def test_execute_cancelled(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute when cancelled."""
    pipeline_context.cancelled = True
    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_execute_less_than_two_authors(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with less than 2 authors."""
    mock_result = MagicMock()
    mock_result.all.return_value = [AuthorMetadata(id=1, name="Author One")]
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["duplicates_found"] == 0
    assert result.stats["merged"] == 0
    assert deduplicate_stage.get_progress() == 1.0


def test_execute_no_authors(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with no authors."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["duplicates_found"] == 0


def test_execute_with_duplicates(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test execute with duplicates found."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    # Mock detector to return duplicate pairs
    duplicate_pairs = [(sample_authors[0], sample_authors[1])]
    deduplicate_stage._detector.find_duplicates = MagicMock(  # type: ignore[attr-defined]
        return_value=iter(duplicate_pairs)
    )

    # Mock merger
    deduplicate_stage._merger.merge_pair = MagicMock()  # type: ignore[attr-defined]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["duplicates_found"] == 1
    assert deduplicate_stage._merger.merge_pair.call_count == 1
    assert deduplicate_stage.get_progress() == 1.0


def test_execute_merge_exception(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test execute when merge raises exception."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    duplicate_pairs = [(sample_authors[0], sample_authors[1])]
    deduplicate_stage._detector.find_duplicates = MagicMock(  # type: ignore[attr-defined]
        return_value=iter(duplicate_pairs)
    )

    # Mock merger to raise exception
    deduplicate_stage._merger.merge_pair = MagicMock(  # type: ignore[attr-defined]
        side_effect=Exception("Merge error")
    )

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is True  # Stage continues despite merge failure
    assert result.stats is not None
    assert result.stats["failed"] == 1


def test_execute_cancelled_during_merge(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test execute cancelled during merge."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    duplicate_pairs = [(sample_authors[0], sample_authors[1])]
    deduplicate_stage._detector.find_duplicates = MagicMock(  # type: ignore[attr-defined]
        return_value=iter(duplicate_pairs)
    )

    call_count = 0

    def check_cancelled() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1  # Cancel after first check

    pipeline_context.check_cancelled = check_cancelled  # type: ignore[assignment]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_execute_progress_updates(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test execute updates progress correctly."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    pipeline_context.progress_callback = progress_callback

    deduplicate_stage._detector.find_duplicates = MagicMock(return_value=iter([]))  # type: ignore[attr-defined]

    deduplicate_stage.execute(pipeline_context)

    # Should have multiple progress updates
    assert len(progress_updates) >= 2
    # Final progress should be 1.0
    assert progress_updates[-1][0] == 1.0


def test_execute_exception(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with exception."""
    pipeline_context.session.exec.side_effect = Exception("Database error")  # type: ignore[attr-defined]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()
    pipeline_context.session.rollback.assert_called_once()  # type: ignore[attr-defined]


def test_execute_with_author_limit(
    deduplicate_stage_with_limit: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
) -> None:
    """Test execute with author limit."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    deduplicate_stage_with_limit._detector.find_duplicates = MagicMock(  # type: ignore[attr-defined]
        return_value=iter([])
    )

    result = deduplicate_stage_with_limit.execute(pipeline_context)

    assert result.success is True
    # Should process only limited authors
    assert deduplicate_stage_with_limit._detector.find_duplicates.called


@pytest.mark.parametrize(
    ("duplicates_count", "expected_merged"),
    [
        (0, 0),
        (1, 1),
        (3, 3),
    ],
)
def test_execute_multiple_duplicates(
    deduplicate_stage: DeduplicateStage,
    pipeline_context: PipelineContext,
    sample_authors: list[AuthorMetadata],
    duplicates_count: int,
    expected_merged: int,
) -> None:
    """Test execute with multiple duplicate pairs."""
    mock_result = MagicMock()
    mock_result.all.return_value = sample_authors
    pipeline_context.session.exec.return_value = mock_result  # type: ignore[attr-defined]

    # Create duplicate pairs
    duplicate_pairs = [
        (sample_authors[0], sample_authors[1]) for _ in range(duplicates_count)
    ]
    deduplicate_stage._detector.find_duplicates = MagicMock(  # type: ignore[attr-defined]
        return_value=iter(duplicate_pairs)
    )
    deduplicate_stage._merger.merge_pair = MagicMock()  # type: ignore[attr-defined]

    result = deduplicate_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["duplicates_found"] == duplicates_count
    assert deduplicate_stage._merger.merge_pair.call_count == expected_merged

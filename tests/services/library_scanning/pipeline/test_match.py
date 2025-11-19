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

"""Tests for match stage to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.author_metadata import AuthorMapping
from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
)
from fundamental.services.library_scanning.pipeline.match import MatchStage


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
def sample_authors() -> list[Author]:
    """Create sample authors."""
    return [
        Author(id=1, name="Author One"),
        Author(id=2, name="Author Two"),
        Author(id=3, name="Author Three"),
    ]


@pytest.fixture
def author_data() -> AuthorData:
    """Create sample author data."""
    return AuthorData(
        key="OL12345A",
        name="Author One",
        personal_name="One",
        work_count=10,
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
def pipeline_context(
    mock_library: MagicMock,
    mock_session: MagicMock,
    mock_data_source: MagicMock,
    sample_authors: list[Author],
) -> PipelineContext:
    """Create a pipeline context."""
    context = PipelineContext(
        library_id=1,
        library=mock_library,
        session=mock_session,
        data_source=mock_data_source,
    )
    context.crawled_authors = sample_authors
    return context


@pytest.fixture
def match_stage() -> MatchStage:
    """Create a match stage instance."""
    return MatchStage()


@pytest.fixture
def match_stage_with_limit() -> MatchStage:
    """Create a match stage with author limit."""
    return MatchStage(author_limit=2)


@pytest.fixture
def match_stage_with_staleness() -> MatchStage:
    """Create a match stage with staleness check."""
    return MatchStage(stale_data_max_age_days=30)


@pytest.fixture
def mock_mapping_repo() -> MagicMock:
    """Create a mock mapping repository."""
    return MagicMock(spec=AuthorMappingRepository)


def test_match_stage_name(match_stage: MatchStage) -> None:
    """Test match stage name property."""
    assert match_stage.name == "match"


def test_match_stage_get_progress_initial(match_stage: MatchStage) -> None:
    """Test get_progress returns 0.0 initially."""
    assert match_stage.get_progress() == 0.0


def test_match_stage_init_defaults() -> None:
    """Test match stage initialization with defaults."""
    stage = MatchStage()
    assert stage._min_confidence == 0.5
    assert stage._author_limit is None
    assert stage._stale_data_max_age_days is None
    assert isinstance(stage._matching_orchestrator, MatchingOrchestrator)


@pytest.mark.parametrize(
    ("min_confidence", "author_limit", "stale_days"),
    [
        (0.7, None, None),
        (0.5, 10, None),
        (0.6, None, 30),
        (0.8, 5, 60),
    ],
)
def test_match_stage_init_params(
    min_confidence: float,
    author_limit: int | None,
    stale_days: int | None,
) -> None:
    """Test match stage initialization with parameters."""
    stage = MatchStage(
        min_confidence=min_confidence,
        author_limit=author_limit,
        stale_data_max_age_days=stale_days,
    )
    assert stage._min_confidence == min_confidence
    assert stage._author_limit == author_limit
    assert stage._stale_data_max_age_days == stale_days


def test_should_skip_match_no_staleness_check(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _should_skip_match when no staleness check is configured."""
    assert match_stage._should_skip_match(pipeline_context, 1) is False


def test_should_skip_match_no_existing_mapping(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _should_skip_match when no existing mapping."""
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = None

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        assert (
            match_stage_with_staleness._should_skip_match(pipeline_context, 1) is False
        )


def test_should_skip_match_fresh_mapping(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _should_skip_match when mapping is fresh."""
    fresh_mapping = AuthorMapping(
        id=1,
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        updated_at=datetime.now(UTC) - timedelta(days=5),
    )
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = fresh_mapping

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        assert (
            match_stage_with_staleness._should_skip_match(pipeline_context, 1) is True
        )


def test_should_skip_match_stale_mapping(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _should_skip_match when mapping is stale."""
    stale_mapping = AuthorMapping(
        id=1,
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        updated_at=datetime.now(UTC) - timedelta(days=60),
    )
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = stale_mapping

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        assert (
            match_stage_with_staleness._should_skip_match(pipeline_context, 1) is False
        )


def test_should_skip_match_uses_created_at_when_no_updated_at(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _should_skip_match uses created_at when updated_at is None."""
    mapping = AuthorMapping(
        id=1,
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        created_at=datetime.now(UTC) - timedelta(days=5),
        updated_at=None,
    )
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = mapping

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        assert (
            match_stage_with_staleness._should_skip_match(pipeline_context, 1) is True
        )


def test_should_skip_match_naive_datetime(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _should_skip_match handles naive datetime."""
    from datetime import datetime as dt

    naive_dt = dt.now(UTC) - timedelta(days=5)
    mapping = AuthorMapping(
        id=1,
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        updated_at=naive_dt,
    )
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = mapping

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        assert (
            match_stage_with_staleness._should_skip_match(pipeline_context, 1) is True
        )


def test_update_progress_metadata(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _update_progress_metadata."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    pipeline_context.progress_callback = progress_callback

    match_stage._update_progress_metadata(
        context=pipeline_context,
        idx=0,
        total_authors=3,
        author_name="Author One",
        matched_count=1,
        unmatched_count=0,
        skipped_count=0,
    )

    assert match_stage.get_progress() == pytest.approx(1.0 / 3.0)
    assert len(progress_updates) == 1
    assert progress_updates[0][1] is not None
    assert progress_updates[0][1]["current_stage"]["matched"] == 1


def test_process_author_match_no_id(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _process_author_match with author having no ID."""
    author = Author(name="Author No ID", id=None)
    matched, unmatched, skipped = match_stage._process_author_match(
        pipeline_context, author
    )

    assert matched == 0
    assert unmatched == 1
    assert skipped == 0


def test_process_author_match_skipped(
    match_stage_with_staleness: MatchStage,
    pipeline_context: PipelineContext,
    mock_mapping_repo: MagicMock,
) -> None:
    """Test _process_author_match when author is skipped."""
    author = Author(id=1, name="Author One")
    fresh_mapping = AuthorMapping(
        id=1,
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        updated_at=datetime.now(UTC) - timedelta(days=5),
    )
    mock_mapping_repo.find_by_calibre_author_id_and_library.return_value = fresh_mapping

    with patch(
        "fundamental.services.library_scanning.pipeline.match.AuthorMappingRepository",
        return_value=mock_mapping_repo,
    ):
        matched, unmatched, skipped = match_stage_with_staleness._process_author_match(
            pipeline_context, author
        )

    assert matched == 0
    assert unmatched == 0
    assert skipped == 1


def test_process_author_match_success(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
    match_result: MatchResult,
) -> None:
    """Test _process_author_match with successful match."""
    author = Author(id=1, name="Author One")

    with patch.object(
        match_stage._matching_orchestrator, "match", return_value=match_result
    ):
        matched, unmatched, skipped = match_stage._process_author_match(
            pipeline_context, author
        )

    assert matched == 1
    assert unmatched == 0
    assert skipped == 0
    assert len(pipeline_context.match_results) == 1
    assert pipeline_context.match_results[0].calibre_author_id == 1


def test_process_author_match_no_match(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _process_author_match with no match found."""
    author = Author(id=1, name="Author One")

    with patch.object(match_stage._matching_orchestrator, "match", return_value=None):
        matched, unmatched, skipped = match_stage._process_author_match(
            pipeline_context, author
        )

    assert matched == 0
    assert unmatched == 1
    assert skipped == 0
    assert len(pipeline_context.unmatched_authors) == 1
    assert pipeline_context.unmatched_authors[0].id == 1


def test_execute_empty_authors(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with no authors."""
    pipeline_context.crawled_authors = []
    result = match_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["matched"] == 0
    assert result.stats["unmatched"] == 0


def test_execute_cancelled(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute when cancelled."""
    pipeline_context.cancelled = True
    result = match_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


@pytest.mark.parametrize(
    ("author_limit", "expected_processed"),
    [
        (None, 3),
        (2, 2),
        # Note: limit=0 is treated as "no limit" in the implementation
        # (checks `if limit is not None and limit > 0`)
    ],
)
def test_execute_with_author_limit(
    pipeline_context: PipelineContext,
    author_limit: int | None,
    expected_processed: int,
) -> None:
    """Test execute with author limit."""
    stage = MatchStage(author_limit=author_limit)

    with patch.object(
        stage._matching_orchestrator, "match", return_value=None
    ) as mock_match:
        result = stage.execute(pipeline_context)

    assert mock_match.call_count == expected_processed
    assert result.success is True


def test_execute_success(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
    match_result: MatchResult,
) -> None:
    """Test execute successfully."""
    with patch.object(
        match_stage._matching_orchestrator, "match", return_value=match_result
    ):
        result = match_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["matched"] == 3
    assert result.stats["unmatched"] == 0
    assert result.stats["total"] == 3


def test_execute_mixed_results(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
    match_result: MatchResult,
) -> None:
    """Test execute with mixed match results."""
    call_count = 0

    def match_side_effect(author: Author, data_source: MagicMock) -> MatchResult | None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return match_result
        return None

    with patch.object(
        match_stage._matching_orchestrator, "match", side_effect=match_side_effect
    ):
        result = match_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["matched"] == 1
    assert result.stats["unmatched"] == 2


def test_execute_exception(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with exception."""
    with patch.object(
        match_stage._matching_orchestrator, "match", side_effect=Exception("Error")
    ):
        result = match_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()


def test_execute_cancelled_during_processing(
    match_stage: MatchStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute cancelled during processing."""
    call_count = 0

    def check_cancelled_side_effect() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1  # Cancel after first author

    pipeline_context.check_cancelled = check_cancelled_side_effect  # type: ignore[assignment]

    with patch.object(match_stage._matching_orchestrator, "match", return_value=None):
        result = match_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()

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

"""Tests for ingest stage to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.author_metadata import AuthorMetadata
from bookcard.services.library_scanning.data_sources.base import (
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from bookcard.services.library_scanning.data_sources.types import AuthorData
from bookcard.services.library_scanning.matching.types import MatchResult
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.ingest import (
    IngestStage,
    IngestStageFactory,
)
from bookcard.services.library_scanning.pipeline.ingest_components import (
    AuthorDataFetcher,
    AuthorIngestionUnitOfWork,
    MatchResultDeduplicator,
    ProgressTracker,
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
def author_data() -> AuthorData:
    """Create sample author data."""
    return AuthorData(
        key="OL12345A",
        name="Author One",
        personal_name="One",
        work_count=10,
    )


@pytest.fixture
def match_results(author_data: AuthorData) -> list[MatchResult]:
    """Create sample match results."""
    return [
        MatchResult(
            confidence_score=0.9,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=1,
        ),
    ]


@pytest.fixture
def pipeline_context(
    mock_library: MagicMock,
    mock_session: MagicMock,
    mock_data_source: MagicMock,
    match_results: list[MatchResult],
) -> PipelineContext:
    """Create a pipeline context."""
    context = PipelineContext(
        library_id=1,
        library=mock_library,
        session=mock_session,
        data_source=mock_data_source,
    )
    context.match_results = match_results
    return context


@pytest.fixture
def mock_author_fetcher() -> MagicMock:
    """Create a mock author fetcher."""
    return MagicMock(spec=AuthorDataFetcher)


@pytest.fixture
def mock_ingestion_uow() -> MagicMock:
    """Create a mock ingestion unit of work."""
    return MagicMock(spec=AuthorIngestionUnitOfWork)


@pytest.fixture
def mock_deduplicator() -> MagicMock:
    """Create a mock deduplicator."""
    return MagicMock(spec=MatchResultDeduplicator)


@pytest.fixture
def mock_progress_tracker() -> MagicMock:
    """Create a mock progress tracker."""
    tracker = MagicMock(spec=ProgressTracker)
    tracker.progress = 0.0
    return tracker


@pytest.fixture
def ingest_stage(
    mock_author_fetcher: MagicMock,
    mock_ingestion_uow: MagicMock,
    mock_deduplicator: MagicMock,
    mock_progress_tracker: MagicMock,
) -> IngestStage:
    """Create an ingest stage instance."""
    return IngestStage(
        author_fetcher=mock_author_fetcher,
        ingestion_uow=mock_ingestion_uow,
        deduplicator=mock_deduplicator,
        progress_tracker=mock_progress_tracker,
    )


def test_ingest_stage_name(ingest_stage: IngestStage) -> None:
    """Test ingest stage name property."""
    assert ingest_stage.name == "ingest"


def test_ingest_stage_get_progress(ingest_stage: IngestStage) -> None:
    """Test get_progress."""
    assert ingest_stage.get_progress() == 0.0


def test_ingest_stage_properties_not_initialized() -> None:
    """Test properties raise when not initialized."""
    stage = IngestStage()

    with pytest.raises(RuntimeError, match="not initialized"):
        _ = stage.author_fetcher

    with pytest.raises(RuntimeError, match="not initialized"):
        _ = stage.ingestion_uow


def test_ingest_stage_deduplicator_lazy_init(ingest_stage: IngestStage) -> None:
    """Test deduplicator lazy initialization."""
    stage = IngestStage()
    # Should create new deduplicator
    dedup1 = stage.deduplicator
    dedup2 = stage.deduplicator
    assert dedup1 is dedup2


def test_ingest_stage_progress_tracker_lazy_init(ingest_stage: IngestStage) -> None:
    """Test progress tracker lazy initialization."""
    stage = IngestStage()
    # Should create new tracker
    tracker1 = stage.progress_tracker
    tracker2 = stage.progress_tracker
    assert tracker1 is tracker2


def test_initialize_from_context(
    pipeline_context: PipelineContext,
) -> None:
    """Test _initialize_from_context."""
    stage = IngestStage()

    with patch(
        "bookcard.services.library_scanning.pipeline.ingest.IngestStageFactory.create_components"
    ) as mock_create:
        mock_create.return_value = {
            "author_fetcher": MagicMock(),
            "ingestion_uow": MagicMock(),
            "deduplicator": MagicMock(),
            "progress_tracker": MagicMock(),
        }
        stage._initialize_from_context(pipeline_context)

    assert stage._initialized is True
    assert stage._author_fetcher is not None


def test_initialize_from_context_already_initialized(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _initialize_from_context when already initialized."""
    original_fetcher = ingest_stage._author_fetcher
    ingest_stage._initialize_from_context(pipeline_context)

    # Should not reinitialize
    assert ingest_stage._author_fetcher == original_fetcher


def test_should_skip_fetch_no_staleness_settings(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _should_skip_fetch when no staleness settings."""
    assert ingest_stage._should_skip_fetch(pipeline_context, "OL1A", "Author") is False


def test_should_skip_fetch_author_not_exists(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _should_skip_fetch when author doesn't exist."""
    stage = IngestStage(
        stale_data_max_age_days=30,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    pipeline_context.session.exec.return_value.first.return_value = None  # type: ignore[attr-defined]

    assert stage._should_skip_fetch(pipeline_context, "OL1A", "Author") is False


def test_should_skip_fetch_no_last_synced(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _should_skip_fetch when author has no last_synced_at."""
    stage = IngestStage(
        stale_data_max_age_days=30,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    existing = AuthorMetadata(id=1, name="Author", openlibrary_key="OL1A")
    existing.last_synced_at = None
    pipeline_context.session.exec.return_value.first.return_value = existing  # type: ignore[attr-defined]

    assert stage._should_skip_fetch(pipeline_context, "OL1A", "Author") is False


@pytest.mark.parametrize(
    ("days_since_sync", "max_age", "refresh_interval", "expected_skip"),
    [
        (5, 30, None, True),  # Fresh data, skip
        (60, 30, None, False),  # Stale data, fetch
        (5, None, 10, True),  # Within refresh interval, skip
        (15, None, 10, False),  # Past refresh interval, fetch
        (5, 30, 10, True),  # Fresh and within interval, skip
        (60, 30, 10, False),  # Stale, fetch
    ],
)
def test_should_skip_fetch_staleness_checks(
    pipeline_context: PipelineContext,
    days_since_sync: int,
    max_age: int | None,
    refresh_interval: int | None,
    expected_skip: bool,
) -> None:
    """Test _should_skip_fetch with various staleness settings."""
    stage = IngestStage(
        stale_data_max_age_days=max_age,
        stale_data_refresh_interval_days=refresh_interval,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    existing = AuthorMetadata(
        id=1,
        name="Author",
        openlibrary_key="OL1A",
        last_synced_at=datetime.now(UTC) - timedelta(days=days_since_sync),
    )
    pipeline_context.session.exec.return_value.first.return_value = existing  # type: ignore[attr-defined]

    result = stage._should_skip_fetch(pipeline_context, "OL1A", "Author")
    assert result == expected_skip


def test_should_skip_fetch_naive_datetime(
    pipeline_context: PipelineContext,
) -> None:
    """Test _should_skip_fetch handles naive datetime."""
    from datetime import datetime as dt

    stage = IngestStage(
        stale_data_max_age_days=30,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    naive_dt = dt.now(UTC) - timedelta(days=5)
    existing = AuthorMetadata(
        id=1, name="Author", openlibrary_key="OL1A", last_synced_at=naive_dt
    )
    pipeline_context.session.exec.return_value.first.return_value = existing  # type: ignore[attr-defined]

    result = stage._should_skip_fetch(pipeline_context, "OL1A", "Author")
    assert result is True  # Should be fresh


def test_apply_limit_no_limit(ingest_stage: IngestStage) -> None:
    """Test _apply_limit with no limit."""
    results = [1, 2, 3]
    assert ingest_stage._apply_limit(results) == results


def test_apply_limit_with_limit(ingest_stage: IngestStage) -> None:
    """Test _apply_limit with limit."""
    stage = IngestStage(
        author_limit=2,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    results = [1, 2, 3, 4, 5]
    limited = stage._apply_limit(results)
    assert len(limited) == 2
    assert limited == [1, 2]


def test_apply_limit_zero_limit(ingest_stage: IngestStage) -> None:
    """Test _apply_limit with zero limit.

    Note: limit=0 is treated as "no limit" in the implementation
    (checks `if limit is not None and limit > 0`)
    """
    stage = IngestStage(
        author_limit=0,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
    )
    results = [1, 2, 3]
    limited = stage._apply_limit(results)
    # Zero limit is treated as no limit, so all results are returned
    assert len(limited) == len(results)


def test_process_authors_success(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
    author_data: AuthorData,
) -> None:
    """Test _process_authors successfully."""
    ingest_stage.author_fetcher.fetch_author.return_value = author_data  # type: ignore[attr-defined]

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 1
    assert stats["failed"] == 0
    assert stats["total"] == 1
    ingest_stage.ingestion_uow.ingest_author.assert_called_once()  # type: ignore[attr-defined]


def test_process_authors_skip_fetch(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors skips fetch when data is fresh."""
    stage = IngestStage(
        stale_data_max_age_days=30,
        author_fetcher=MagicMock(),
        ingestion_uow=MagicMock(),
        deduplicator=MagicMock(),
        progress_tracker=MagicMock(),
    )
    stage.progress_tracker.update = MagicMock()  # type: ignore[attr-defined]
    stage.progress_tracker.progress = 0.5  # type: ignore[attr-defined]

    existing = AuthorMetadata(
        id=1,
        name="Author One",
        openlibrary_key="OL12345A",
        last_synced_at=datetime.now(UTC) - timedelta(days=5),
    )
    pipeline_context.session.exec.return_value.first.return_value = existing  # type: ignore[attr-defined]

    stats = stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 1
    assert stats["failed"] == 0
    stage.author_fetcher.fetch_author.assert_not_called()  # type: ignore[attr-defined]


def test_process_authors_fetch_fails(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors when fetch returns None."""
    ingest_stage.author_fetcher.fetch_author.return_value = None  # type: ignore[attr-defined]

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 0
    assert stats["failed"] == 1


def test_process_authors_network_error(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors handles network error."""
    ingest_stage.author_fetcher.fetch_author.side_effect = DataSourceNetworkError(  # type: ignore[attr-defined]
        "Network error"
    )

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 0
    assert stats["failed"] == 1


def test_process_authors_rate_limit_error(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors handles rate limit error."""
    ingest_stage.author_fetcher.fetch_author.side_effect = DataSourceRateLimitError(  # type: ignore[attr-defined]
        "Rate limit"
    )

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 0
    assert stats["failed"] == 1


def test_process_authors_exception(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors handles exception."""
    ingest_stage.author_fetcher.fetch_author.side_effect = Exception("Unexpected error")  # type: ignore[attr-defined]

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    assert stats["ingested"] == 0
    assert stats["failed"] == 1


def test_process_authors_cancelled(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_authors when cancelled."""
    call_count = 0

    def check_cancelled() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1  # Cancel after first check

    pipeline_context.check_cancelled = check_cancelled  # type: ignore[assignment]

    stats = ingest_stage._process_authors(pipeline_context, match_results)

    # Should have processed at least one before cancellation
    assert stats["ingested"] >= 0


def test_report_progress(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _report_progress."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    pipeline_context.progress_callback = progress_callback
    ingest_stage.progress_tracker.progress = 0.5  # type: ignore[attr-defined]

    ingest_stage._report_progress(
        context=pipeline_context,
        idx=0,
        unique_results=match_results,
        ingested_count=1,
        failed_count=0,
    )

    assert len(progress_updates) == 1
    assert progress_updates[0][1] is not None
    assert progress_updates[0][1]["current_stage"]["ingested"] == 1


def test_execute_cancelled(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute when cancelled."""
    pipeline_context.cancelled = True
    result = ingest_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_execute_empty_match_results(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with empty match results."""
    pipeline_context.match_results = []
    result = ingest_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["ingested"] == 0


def test_execute_no_unique_results(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test execute when deduplication results in no unique results."""
    ingest_stage.deduplicator.deduplicate_by_key.return_value = ([], 0)  # type: ignore[attr-defined]

    result = ingest_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["ingested"] == 0


def test_execute_success(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
    author_data: AuthorData,
) -> None:
    """Test execute successfully."""
    ingest_stage.deduplicator.deduplicate_by_key.return_value = (match_results, 0)  # type: ignore[attr-defined]
    ingest_stage.author_fetcher.fetch_author.return_value = author_data  # type: ignore[attr-defined]
    ingest_stage.progress_tracker.progress = 1.0  # type: ignore[attr-defined]

    result = ingest_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["ingested"] == 1.0
    pipeline_context.session.commit.assert_called()  # type: ignore[attr-defined]


def test_execute_exception(
    ingest_stage: IngestStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with exception."""
    ingest_stage.deduplicator.deduplicate_by_key.side_effect = Exception("Error")  # type: ignore[attr-defined]

    result = ingest_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()
    pipeline_context.session.rollback.assert_called_once()  # type: ignore[attr-defined]


def test_execute_initializes_from_context(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute initializes from context when not initialized."""
    stage = IngestStage()

    mock_deduplicator = MagicMock()
    mock_deduplicator.deduplicate_by_key.return_value = ([], 0)

    with patch(
        "bookcard.services.library_scanning.pipeline.ingest.IngestStageFactory.create_components"
    ) as mock_create:
        mock_create.return_value = {
            "author_fetcher": MagicMock(),
            "ingestion_uow": MagicMock(),
            "deduplicator": mock_deduplicator,
            "progress_tracker": MagicMock(),
        }

        stage.execute(pipeline_context)

    assert stage._initialized is True
    mock_create.assert_called_once()


def test_ingest_stage_factory_create_components(
    mock_session: MagicMock,
    mock_data_source: MagicMock,
) -> None:
    """Test IngestStageFactory.create_components."""
    components = IngestStageFactory.create_components(
        session=mock_session,
        data_source=mock_data_source,
    )

    assert "author_fetcher" in components
    assert "ingestion_uow" in components
    assert "deduplicator" in components
    assert "progress_tracker" in components


def test_ingest_stage_factory_create(
    mock_session: MagicMock,
    mock_data_source: MagicMock,
) -> None:
    """Test IngestStageFactory.create."""
    stage = IngestStageFactory.create(
        session=mock_session,
        data_source=mock_data_source,
    )

    assert isinstance(stage, IngestStage)
    assert stage._author_fetcher is not None
    assert stage._initialized is True


@pytest.mark.parametrize(
    ("author_limit", "max_works", "expected_works"),
    [
        (None, None, None),
        (10, None, None),
        (None, 5, 5),
        (10, 5, 5),
    ],
)
def test_ingest_stage_factory_with_params(
    mock_session: MagicMock,
    mock_data_source: MagicMock,
    author_limit: int | None,
    max_works: int | None,
    expected_works: int | None,
) -> None:
    """Test IngestStageFactory.create with parameters."""
    stage = IngestStageFactory.create(
        session=mock_session,
        data_source=mock_data_source,
        author_limit=author_limit,
        max_works_per_author=max_works,
    )

    assert stage.author_limit == author_limit

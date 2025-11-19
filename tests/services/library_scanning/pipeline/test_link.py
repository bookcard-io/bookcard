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

"""Tests for link stage to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.link import (
    LinkStage,
    LinkStageFactory,
)
from fundamental.services.library_scanning.pipeline.link_components import (
    MappingService,
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
        MatchResult(
            confidence_score=0.8,
            matched_entity=author_data,
            match_method="fuzzy",
            calibre_author_id=2,
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
def mock_mapping_service() -> MagicMock:
    """Create a mock mapping service."""
    return MagicMock(spec=MappingService)


@pytest.fixture
def link_stage(mock_mapping_service: MagicMock) -> LinkStage:
    """Create a link stage instance."""
    return LinkStage(mapping_service=mock_mapping_service)


@pytest.fixture
def link_stage_with_limit(mock_mapping_service: MagicMock) -> LinkStage:
    """Create a link stage with author limit."""
    return LinkStage(mapping_service=mock_mapping_service, author_limit=1)


def test_link_stage_name(link_stage: LinkStage) -> None:
    """Test link stage name property."""
    assert link_stage.name == "link"


def test_link_stage_get_progress_initial(link_stage: LinkStage) -> None:
    """Test get_progress returns 0.0 initially."""
    assert link_stage.get_progress() == 0.0


def test_link_stage_mapping_service_property(
    link_stage: LinkStage,
    mock_mapping_service: MagicMock,
) -> None:
    """Test mapping_service property."""
    assert link_stage.mapping_service == mock_mapping_service


def test_link_stage_mapping_service_not_initialized() -> None:
    """Test mapping_service property raises when not initialized."""
    stage = LinkStage()
    with pytest.raises(RuntimeError, match="not initialized"):
        _ = stage.mapping_service


def test_link_stage_init_with_service(mock_mapping_service: MagicMock) -> None:
    """Test link stage initialization with mapping service."""
    stage = LinkStage(mapping_service=mock_mapping_service)
    assert stage._mapping_service == mock_mapping_service
    assert stage._initialized is True


def test_link_stage_init_without_service() -> None:
    """Test link stage initialization without mapping service."""
    stage = LinkStage()
    assert stage._mapping_service is None
    assert stage._initialized is False


def test_initialize_from_context(
    pipeline_context: PipelineContext,
) -> None:
    """Test _initialize_from_context."""
    stage = LinkStage()

    with patch(
        "fundamental.services.library_scanning.pipeline.link.LinkStageFactory.create_components"
    ) as mock_create:
        mock_create.return_value = {"mapping_service": MagicMock()}
        stage._initialize_from_context(pipeline_context)

    assert stage._initialized is True
    assert stage._mapping_service is not None


def test_initialize_from_context_already_initialized(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test _initialize_from_context when already initialized."""
    original_service = link_stage._mapping_service
    link_stage._initialize_from_context(pipeline_context)

    # Should not reinitialize
    assert link_stage._mapping_service == original_service


def test_prepare_match_results_no_limit(
    link_stage: LinkStage,
    match_results: list[MatchResult],
) -> None:
    """Test _prepare_match_results without limit."""
    result = link_stage._prepare_match_results(match_results)
    assert result == match_results
    assert len(result) == 2


def test_prepare_match_results_with_limit(
    link_stage_with_limit: LinkStage,
    match_results: list[MatchResult],
) -> None:
    """Test _prepare_match_results with limit."""
    result = link_stage_with_limit._prepare_match_results(match_results)
    assert len(result) == 1
    assert result == match_results[:1]


def test_prepare_match_results_zero_limit(
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _prepare_match_results with zero limit.

    Note: limit=0 is treated as "no limit" in the implementation
    (checks `if limit is not None and limit > 0`)
    """
    stage = LinkStage(author_limit=0)
    result = stage._prepare_match_results(match_results)
    # Zero limit is treated as no limit, so all results are returned
    assert len(result) == len(match_results)


def test_process_mappings(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test _process_mappings."""
    with patch(
        "fundamental.services.library_scanning.pipeline.link.MappingBatchProcessor"
    ) as mock_processor_class:
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        statistics = link_stage._process_mappings(pipeline_context, match_results)

        assert statistics is not None
        mock_processor.process_batch.assert_called_once()
        assert link_stage._progress_reporter is not None


def test_create_empty_result(link_stage: LinkStage) -> None:
    """Test _create_empty_result."""
    result = link_stage._create_empty_result()

    assert result.success is True
    assert result.stats is not None
    assert result.stats["mappings_created"] == 0


def test_create_success_result(link_stage: LinkStage) -> None:
    """Test _create_success_result."""
    from fundamental.services.library_scanning.pipeline.link_components import (
        LinkingStatistics,
    )

    statistics = LinkingStatistics()
    statistics.mappings_created = 5
    statistics.mappings_updated = 2

    result = link_stage._create_success_result(statistics)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["mappings_created"] == 5.0
    assert result.stats["mappings_updated"] == 2.0


def test_execute_cancelled(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute when cancelled."""
    pipeline_context.cancelled = True
    result = link_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_execute_empty_match_results(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with empty match results."""
    pipeline_context.match_results = []
    result = link_stage.execute(pipeline_context)

    assert result.success is True
    assert result.stats is not None
    assert result.stats["mappings_created"] == 0


def test_execute_success(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
) -> None:
    """Test execute successfully."""
    with patch(
        "fundamental.services.library_scanning.pipeline.link.MappingBatchProcessor"
    ) as mock_processor_class:
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = link_stage.execute(pipeline_context)

        assert result.success is True
        assert result.stats is not None
        pipeline_context.session.commit.assert_called_once()  # type: ignore[attr-defined]


def test_execute_exception(
    link_stage: LinkStage,
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with exception."""
    with patch(
        "fundamental.services.library_scanning.pipeline.link.MappingBatchProcessor",
        side_effect=Exception("Processing error"),
    ):
        result = link_stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()
    pipeline_context.session.rollback.assert_called_once()  # type: ignore[attr-defined]


def test_execute_initializes_from_context(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute initializes from context when not initialized."""
    stage = LinkStage()

    with (
        patch(
            "fundamental.services.library_scanning.pipeline.link.LinkStageFactory.create_components"
        ) as mock_create,
        patch(
            "fundamental.services.library_scanning.pipeline.link.MappingBatchProcessor"
        ) as mock_processor_class,
    ):
        mock_create.return_value = {"mapping_service": MagicMock()}
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        stage.execute(pipeline_context)

    assert stage._initialized is True
    mock_create.assert_called_once()


def test_link_stage_factory_create_components(mock_session: MagicMock) -> None:
    """Test LinkStageFactory.create_components."""
    components = LinkStageFactory.create_components(session=mock_session)

    assert "mapping_service" in components
    assert isinstance(components["mapping_service"], MappingService)


def test_link_stage_factory_create(mock_session: MagicMock) -> None:
    """Test LinkStageFactory.create."""
    stage = LinkStageFactory.create(session=mock_session)

    assert isinstance(stage, LinkStage)
    assert stage._mapping_service is not None
    assert stage._initialized is True


@pytest.mark.parametrize(
    ("author_limit", "expected_count"),
    [
        (None, 2),
        (1, 1),
        # Note: limit=0 is treated as "no limit" in the implementation
        # (checks `if limit is not None and limit > 0`)
    ],
)
def test_execute_with_author_limit(
    pipeline_context: PipelineContext,
    match_results: list[MatchResult],
    author_limit: int | None,
    expected_count: int,
) -> None:
    """Test execute with author limit."""
    stage = LinkStage(author_limit=author_limit)

    with (
        patch(
            "fundamental.services.library_scanning.pipeline.link.LinkStageFactory.create_components"
        ) as mock_create,
        patch(
            "fundamental.services.library_scanning.pipeline.link.MappingBatchProcessor"
        ) as mock_processor_class,
    ):
        mock_create.return_value = {"mapping_service": MagicMock()}
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        stage.execute(pipeline_context)

        # Check that batch processor was called with limited results
        call_args = mock_processor.process_batch.call_args
        assert call_args is not None
        batch_results = call_args[0][0]
        assert len(batch_results) == expected_count

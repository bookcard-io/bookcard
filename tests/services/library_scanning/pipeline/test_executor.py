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

"""Tests for pipeline executor to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.executor import PipelineExecutor


class MockStage(PipelineStage):
    """Mock pipeline stage for testing."""

    def __init__(
        self,
        name: str,
        success: bool = True,
        message: str = "Success",
        stats: dict | None = None,
        raise_exception: bool = False,
    ) -> None:
        """Initialize mock stage."""
        self._name = name
        self._success = success
        self._message = message
        self._stats = stats or {}
        self._raise_exception = raise_exception
        self._progress = 0.0

    @property
    def name(self) -> str:
        """Get stage name."""
        return self._name

    def get_progress(self) -> float:
        """Get progress."""
        return self._progress

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute stage."""
        if self._raise_exception:
            raise Exception("Stage error")  # noqa: TRY002
        return StageResult(
            success=self._success,
            message=self._message,
            stats=self._stats,
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
def success_stage() -> MockStage:
    """Create a successful mock stage."""
    return MockStage(name="success_stage", success=True)


@pytest.fixture
def failure_stage() -> MockStage:
    """Create a failing mock stage."""
    return MockStage(name="failure_stage", success=False, message="Failed")


@pytest.fixture
def exception_stage() -> MockStage:
    """Create a stage that raises exception."""
    return MockStage(name="exception_stage", raise_exception=True)


def test_executor_init_no_callback() -> None:
    """Test executor initialization without callback."""
    stages = [MockStage(name="stage1")]
    executor = PipelineExecutor(stages=stages)
    assert executor.stages == stages
    assert executor.progress_callback is None
    assert executor._current_stage_index == 0


def test_executor_init_with_callback() -> None:
    """Test executor initialization with callback."""
    stages = [MockStage(name="stage1")]
    callback = MagicMock()
    executor = PipelineExecutor(stages=stages, progress_callback=callback)
    assert executor.stages == stages
    assert executor.progress_callback == callback


def test_execute_single_stage_success(
    pipeline_context: PipelineContext,
    success_stage: MockStage,
) -> None:
    """Test execute with single successful stage."""
    executor = PipelineExecutor(stages=[success_stage])
    result = executor.execute(pipeline_context)

    assert result["success"] is True
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 1
    assert isinstance(result["stage_results"][0], dict)
    assert "stage" in result["stage_results"][0]
    assert "success" in result["stage_results"][0]
    assert "message" in result["stage_results"][0]
    assert "stats" in result["stage_results"][0]
    assert result["stage_results"][0]["stage"] == "success_stage"  # type: ignore[index]
    assert result["stage_results"][0]["success"] is True  # type: ignore[index]
    assert result["stage_results"][0]["message"] is not None  # type: ignore[index]
    assert result["stage_results"][0]["stats"] is not None  # type: ignore[index]


def test_execute_multiple_stages_all_success(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with multiple successful stages."""
    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=True),
        MockStage(name="stage3", success=True),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is True
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 3
    assert result["completed_stages"] == 3
    assert result["total_stages"] == 3


def test_execute_stage_failure_continues(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute continues after stage failure."""
    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=False, message="Failed"),
        MockStage(name="stage3", success=True),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is False  # Overall failure
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 3
    assert result["stage_results"][1]["success"] is False  # type: ignore[index]
    assert result["stage_results"][1]["message"] is not None  # type: ignore[index]
    assert result["stage_results"][1]["stats"] is not None  # type: ignore[index]


def test_execute_stage_exception_continues(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute continues after stage exception."""
    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", raise_exception=True),
        MockStage(name="stage3", success=True),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is False
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 3
    assert result["stage_results"][1]["success"] is False  # type: ignore[index]
    assert result["stage_results"][1]["message"] is not None  # type: ignore[index]
    assert "Critical error" in result["stage_results"][1]["message"]  # type: ignore[index]


def test_execute_cancelled_at_start(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute cancelled at start."""
    stages = [MockStage(name="stage1")]
    executor = PipelineExecutor(stages=stages)
    pipeline_context.cancelled = True
    result = executor.execute(pipeline_context)

    assert result["success"] is False
    assert isinstance(result["message"], str)
    assert "cancelled" in result["message"].lower()
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 0
    assert result["completed_stages"] == 0


def test_execute_cancelled_during_execution(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute cancelled during execution."""
    call_count = 0

    def check_cancelled() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1  # Cancel after first stage

    pipeline_context.check_cancelled = check_cancelled  # type: ignore[assignment]

    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=True),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is False
    assert isinstance(result["message"], str)
    assert "cancelled" in result["message"].lower()
    assert result["completed_stages"] == 1


def test_execute_progress_callback(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with progress callback."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=True),
    ]
    executor = PipelineExecutor(stages=stages, progress_callback=progress_callback)
    result = executor.execute(pipeline_context)

    assert result["success"] is True
    # Should have progress updates for each stage completion
    assert len(progress_updates) >= 2
    # Final progress should be 1.0
    assert progress_updates[-1][0] == 1.0


def test_execute_progress_callback_stage_metadata(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute progress callback includes stage metadata."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    stages = [MockStage(name="stage1", success=True, stats={"count": 5})]
    executor = PipelineExecutor(stages=stages, progress_callback=progress_callback)
    executor.execute(pipeline_context)

    # Find stage completion metadata
    stage_metadata = None
    for _, metadata in progress_updates:
        if metadata and "current_stage" in metadata:
            stage_metadata = metadata["current_stage"]
            break

    assert stage_metadata is not None
    assert stage_metadata["name"] == "stage1"
    assert stage_metadata["status"] == "complete"
    assert stage_metadata["stats"] == {"count": 5}


def test_execute_progress_callback_stage_failed_metadata(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute progress callback includes failed stage metadata."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    stages = [MockStage(name="stage1", success=False, message="Failed")]
    executor = PipelineExecutor(stages=stages, progress_callback=progress_callback)
    executor.execute(pipeline_context)

    # Find stage completion metadata
    stage_metadata = None
    for _, metadata in progress_updates:
        if metadata and "current_stage" in metadata:
            stage_metadata = metadata["current_stage"]
            break

    assert stage_metadata is not None
    assert stage_metadata["status"] == "failed"


def test_create_progress_callback(
    pipeline_context: PipelineContext,
) -> None:
    """Test _create_progress_callback calculates overall progress."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=True),
    ]
    executor = PipelineExecutor(stages=stages, progress_callback=progress_callback)

    # Manually trigger progress callback
    callback = executor._create_progress_callback(total_stages=2)
    callback(0.5, {"test": "data"})  # 50% through first stage

    assert len(progress_updates) == 1
    # Should be 0.5 * (1/2) = 0.25 overall progress
    assert progress_updates[0][0] == pytest.approx(0.25)


def test_create_progress_callback_multiple_stages(
    pipeline_context: PipelineContext,
) -> None:
    """Test _create_progress_callback with multiple stages."""
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=True),
        MockStage(name="stage3", success=True),
    ]
    executor = PipelineExecutor(stages=stages, progress_callback=progress_callback)

    callback = executor._create_progress_callback(total_stages=3)
    executor._current_stage_index = 1  # Second stage
    callback(0.5, {"test": "data"})  # 50% through second stage

    assert len(progress_updates) == 1
    # Should be (1 * 1/3) + (0.5 * 1/3) = 0.5 overall progress
    assert progress_updates[0][0] == pytest.approx(0.5)


def test_execute_empty_stages(pipeline_context: PipelineContext) -> None:
    """Test execute with no stages."""
    executor = PipelineExecutor(stages=[])
    result = executor.execute(pipeline_context)

    assert result["success"] is True
    assert isinstance(result["stage_results"], list)
    assert len(result["stage_results"]) == 0
    assert result["completed_stages"] == 0
    assert result["total_stages"] == 0


def test_execute_all_stages_failed(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with all stages failing."""
    stages = [
        MockStage(name="stage1", success=False),
        MockStage(name="stage2", success=False),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is False
    assert result["message"] == "Pipeline completed: 0/2 stages successful"


def test_execute_partial_success(
    pipeline_context: PipelineContext,
) -> None:
    """Test execute with partial success."""
    stages = [
        MockStage(name="stage1", success=True),
        MockStage(name="stage2", success=False),
        MockStage(name="stage3", success=True),
    ]
    executor = PipelineExecutor(stages=stages)
    result = executor.execute(pipeline_context)

    assert result["success"] is False
    assert result["message"] == "Pipeline completed: 2/3 stages successful"

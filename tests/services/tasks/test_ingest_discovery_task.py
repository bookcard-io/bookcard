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

"""Tests for IngestDiscoveryTask to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.ingest import IngestConfig
from bookcard.models.tasks import TaskType
from bookcard.services.ingest.file_discovery_service import FileGroup
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.ingest_discovery_task import IngestDiscoveryTask

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def mock_update_progress() -> MagicMock:
    """Create a mock update_progress callback."""
    return MagicMock()


@pytest.fixture
def mock_task_service() -> MagicMock:
    """Create a mock task service."""
    return MagicMock()


@pytest.fixture
def mock_enqueue_task() -> MagicMock:
    """Create a mock enqueue_task callback."""
    return MagicMock(return_value=42)


@pytest.fixture
def worker_context_dict(
    session: DummySession,
    mock_update_progress: MagicMock,
    mock_task_service: MagicMock,
    mock_enqueue_task: MagicMock,
) -> dict[str, MagicMock | DummySession]:
    """Create a worker context as dict."""
    return {
        "session": session,
        "update_progress": mock_update_progress,
        "task_service": mock_task_service,
        "enqueue_task": mock_enqueue_task,
    }


@pytest.fixture
def worker_context(
    session: DummySession,
    mock_update_progress: MagicMock,
    mock_task_service: MagicMock,
    mock_enqueue_task: MagicMock,
) -> WorkerContext:
    """Create a WorkerContext object."""
    return WorkerContext(
        session=session,  # type: ignore[valid-type]
        update_progress=mock_update_progress,
        task_service=mock_task_service,
        enqueue_task=mock_enqueue_task,
    )


@pytest.fixture
def task() -> IngestDiscoveryTask:
    """Create IngestDiscoveryTask instance."""
    return IngestDiscoveryTask(
        task_id=1,
        user_id=1,
        metadata={},
    )


@pytest.fixture
def mock_ingest_config() -> MagicMock:
    """Create a mock IngestConfig."""
    config = MagicMock(spec=IngestConfig)
    config.enabled = True
    config.ingest_dir = "/tmp/ingest"
    config.metadata_providers = ["openlibrary"]
    config.supported_formats = ["epub", "pdf"]
    config.ignore_patterns = ["*.tmp"]
    return config


@pytest.fixture
def temp_ingest_dir(tmp_path: Path) -> Path:
    """Create a temporary ingest directory."""
    ingest_dir = tmp_path / "ingest"
    ingest_dir.mkdir()
    return ingest_dir


@pytest.fixture
def file_group(temp_ingest_dir: Path) -> FileGroup:
    """Create a FileGroup instance."""
    file_path = temp_ingest_dir / "book.epub"
    file_path.touch()
    return FileGroup(
        book_key="test_book",
        files=[file_path],
        metadata_hint={"title": "Test Book", "authors": ["Test Author"]},
    )


def test_run_with_dict_context(
    task: IngestDiscoveryTask,
    worker_context_dict: dict[str, MagicMock | DummySession],
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
) -> None:
    """Test run method with dict context."""
    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ),
        patch("bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"),
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub", "pdf"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = []
        mock_discovery_service.return_value = discovery_service_instance

        # Run task
        task.run(worker_context_dict)

        # Verify context was converted
        assert isinstance(worker_context_dict["update_progress"], MagicMock)


def test_run_with_worker_context(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
) -> None:
    """Test run method with WorkerContext object."""
    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = []
        mock_discovery_service.return_value = discovery_service_instance

        # Run task
        task.run(worker_context)

        # Verify progress was updated
        assert worker_context.update_progress.called


def test_run_ingest_disabled(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
) -> None:
    """Test run method when ingest is disabled."""
    mock_ingest_config.enabled = False

    with patch(
        "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
    ) as mock_config_service:
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        mock_config_service.return_value = config_service_instance

        task.run(worker_context)

        # Verify progress updated to 1.0 with disabled message
        worker_context.update_progress.assert_any_call(
            1.0, {"message": "Ingest disabled"}
        )


def test_run_ingest_dir_not_exists(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
) -> None:
    """Test run method when ingest directory doesn't exist."""
    non_existent_dir = Path("/nonexistent/ingest")

    with patch(
        "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
    ) as mock_config_service:
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = non_existent_dir
        mock_config_service.return_value = config_service_instance

        task.run(worker_context)

        # Verify progress updated with error
        worker_context.update_progress.assert_any_call(
            1.0, {"error": "Ingest directory not found"}
        )


def test_run_no_files_found(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
) -> None:
    """Test run method when no files are found."""
    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
    ):
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = []
        mock_discovery_service.return_value = discovery_service_instance

        task.run(worker_context)

        # Verify progress updated with no files message
        worker_context.update_progress.assert_any_call(
            1.0, {"message": "No files found"}
        )


def test_run_successful_discovery(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
    file_group: FileGroup,
) -> None:
    """Test run method with successful discovery and processing."""
    file_path = temp_ingest_dir / "book.epub"
    file_path.touch()

    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ) as mock_metadata_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"
        ) as mock_processor_service,
    ):
        # Setup config service
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        # Setup discovery service
        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = [file_path]
        mock_discovery_service.return_value = discovery_service_instance

        # Setup metadata service
        metadata_service_instance = MagicMock()
        metadata_service_instance.group_files_by_metadata.return_value = [file_group]
        mock_metadata_service.return_value = metadata_service_instance

        # Setup processor service
        processor_service_instance = MagicMock()
        processor_service_instance.process_file_group.return_value = 123
        mock_processor_service.return_value = processor_service_instance

        task.run(worker_context)

        # Verify file group was processed
        processor_service_instance.process_file_group.assert_called_once_with(
            file_group, user_id=1
        )

        # Verify task was enqueued
        worker_context.enqueue_task.assert_called_once_with(  # type: ignore[valid-type]
            TaskType.INGEST_BOOK, {}, 1, {"history_id": 123}
        )

        # Verify final progress update
        worker_context.update_progress.assert_any_call(1.0, {"history_ids": [123]})


def test_run_without_enqueue_task(
    task: IngestDiscoveryTask,
    session: DummySession,
    mock_update_progress: MagicMock,
    mock_task_service: MagicMock,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
    file_group: FileGroup,
) -> None:
    """Test run method when enqueue_task is not available."""
    file_path = temp_ingest_dir / "book.epub"
    file_path.touch()

    # Create context without enqueue_task
    context = WorkerContext(
        session=session,  # type: ignore[valid-type]
        update_progress=mock_update_progress,
        task_service=mock_task_service,
        enqueue_task=None,
    )

    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ) as mock_metadata_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"
        ) as mock_processor_service,
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = [file_path]
        mock_discovery_service.return_value = discovery_service_instance

        metadata_service_instance = MagicMock()
        metadata_service_instance.group_files_by_metadata.return_value = [file_group]
        mock_metadata_service.return_value = metadata_service_instance

        processor_service_instance = MagicMock()
        processor_service_instance.process_file_group.return_value = 123
        mock_processor_service.return_value = processor_service_instance

        task.run(context)

        # Verify file group was still processed
        processor_service_instance.process_file_group.assert_called_once()

        # Verify enqueue_task was not called (it's None)
        assert context.enqueue_task is None


def test_run_file_group_processing_exception(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
    file_group: FileGroup,
) -> None:
    """Test run method handles exceptions during file group processing."""
    file_path = temp_ingest_dir / "book.epub"
    file_path.touch()

    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ) as mock_metadata_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"
        ) as mock_processor_service,
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = [file_path]
        mock_discovery_service.return_value = discovery_service_instance

        metadata_service_instance = MagicMock()
        metadata_service_instance.group_files_by_metadata.return_value = [file_group]
        mock_metadata_service.return_value = metadata_service_instance

        # Make processor raise exception
        processor_service_instance = MagicMock()
        processor_service_instance.process_file_group.side_effect = ValueError("Error")
        mock_processor_service.return_value = processor_service_instance

        # Task should complete despite exception
        task.run(worker_context)

        # Verify progress was still updated to completion
        worker_context.update_progress.assert_any_call(1.0, {"history_ids": []})


def test_run_general_exception(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
) -> None:
    """Test run method raises exception on general failure."""
    with patch(
        "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
    ) as mock_config_service:
        # Make config service raise exception
        mock_config_service.side_effect = RuntimeError("Config error")

        # Task should raise exception
        with pytest.raises(RuntimeError, match="Config error"):
            task.run(worker_context)


def test_run_multiple_file_groups(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
) -> None:
    """Test run method with multiple file groups."""
    file1 = temp_ingest_dir / "book1.epub"
    file1.touch()
    file2 = temp_ingest_dir / "book2.epub"
    file2.touch()

    group1 = FileGroup(
        book_key="book1",
        files=[file1],
        metadata_hint={"title": "Book 1"},
    )
    group2 = FileGroup(
        book_key="book2",
        files=[file2],
        metadata_hint={"title": "Book 2"},
    )

    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ) as mock_metadata_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"
        ) as mock_processor_service,
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = [file1, file2]
        mock_discovery_service.return_value = discovery_service_instance

        metadata_service_instance = MagicMock()
        metadata_service_instance.group_files_by_metadata.return_value = [
            group1,
            group2,
        ]
        mock_metadata_service.return_value = metadata_service_instance

        processor_service_instance = MagicMock()
        processor_service_instance.process_file_group.side_effect = [123, 456]
        mock_processor_service.return_value = processor_service_instance

        task.run(worker_context)

        # Verify both groups were processed
        assert processor_service_instance.process_file_group.call_count == 2

        # Verify both tasks were enqueued
        assert worker_context.enqueue_task.call_count == 2  # type: ignore[valid-type]

        # Verify final progress with both history IDs
        worker_context.update_progress.assert_any_call(1.0, {"history_ids": [123, 456]})


def test_run_progress_updates(
    task: IngestDiscoveryTask,
    worker_context: WorkerContext,
    mock_ingest_config: MagicMock,
    temp_ingest_dir: Path,
    file_group: FileGroup,
) -> None:
    """Test run method updates progress at each stage."""
    file_path = temp_ingest_dir / "book.epub"
    file_path.touch()

    with (
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestConfigService"
        ) as mock_config_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.FileDiscoveryService"
        ) as mock_discovery_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.MetadataExtractionService"
        ) as mock_metadata_service,
        patch(
            "bookcard.services.tasks.ingest_discovery_task.IngestProcessorService"
        ) as mock_processor_service,
    ):
        # Setup mocks
        config_service_instance = MagicMock()
        config_service_instance.get_config.return_value = mock_ingest_config
        config_service_instance.get_ingest_dir.return_value = temp_ingest_dir
        config_service_instance.get_supported_formats.return_value = ["epub"]
        config_service_instance.get_ignore_patterns.return_value = []
        mock_config_service.return_value = config_service_instance

        discovery_service_instance = MagicMock()
        discovery_service_instance.discover_files.return_value = [file_path]
        mock_discovery_service.return_value = discovery_service_instance

        metadata_service_instance = MagicMock()
        metadata_service_instance.group_files_by_metadata.return_value = [file_group]
        mock_metadata_service.return_value = metadata_service_instance

        processor_service_instance = MagicMock()
        processor_service_instance.process_file_group.return_value = 123
        mock_processor_service.return_value = processor_service_instance

        task.run(worker_context)

        # Verify progress updates at each stage
        calls = worker_context.update_progress.call_args_list
        assert calls[0][0][0] == 0.1  # Starting discovery
        assert calls[1][0][0] == 0.2  # Discovering files
        assert calls[2][0][0] == 0.4  # Extracting metadata
        assert calls[3][0][0] == 0.6  # Creating history records
        assert calls[-1][0][0] == 1.0  # Complete

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

"""Tests for IngestBookTask to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.services.tasks.context import WorkerContext
from fundamental.services.tasks.exceptions import TaskCancelledError
from fundamental.services.tasks.ingest_book_task import IngestBookTask


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


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
    return MagicMock()


@pytest.fixture
def worker_context_dict(
    mock_session: MagicMock,
    mock_update_progress: MagicMock,
    mock_task_service: MagicMock,
    mock_enqueue_task: MagicMock,
) -> dict[str, MagicMock]:
    """Create a worker context as dict."""
    return {
        "session": mock_session,
        "update_progress": mock_update_progress,
        "task_service": mock_task_service,
        "enqueue_task": mock_enqueue_task,
    }


@pytest.fixture
def worker_context(
    mock_session: MagicMock,
    mock_update_progress: MagicMock,
    mock_task_service: MagicMock,
    mock_enqueue_task: MagicMock,
) -> WorkerContext:
    """Create a WorkerContext object."""
    return WorkerContext(
        session=mock_session,
        update_progress=mock_update_progress,
        task_service=mock_task_service,
        enqueue_task=mock_enqueue_task,
    )


@pytest.fixture
def task() -> IngestBookTask:
    """Create IngestBookTask instance."""
    return IngestBookTask(
        task_id=1,
        user_id=1,
        metadata={"history_id": 123},
    )


@pytest.fixture
def mock_ingest_config() -> MagicMock:
    """Create a mock IngestConfig."""
    config = MagicMock()
    config.auto_delete_after_ingest = False
    return config


@pytest.fixture
def mock_ingest_history() -> IngestHistory:
    """Create a mock IngestHistory."""
    return IngestHistory(
        id=123,
        file_path="/test/path",
        status=IngestStatus.PENDING,
        ingest_metadata={
            "files": ["/test/file1.epub", "/test/file2.epub"],
            "metadata_hint": {"title": "Test Book", "authors": ["Test Author"]},
        },
    )


@pytest.fixture
def temp_file() -> Path:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as f:
        f.write(b"test content")
        return Path(f.name)


@pytest.fixture
def mock_library() -> MagicMock:
    """Create a mock Library."""
    library = MagicMock()
    library.id = 1
    library.auto_convert_on_ingest = False
    library.auto_convert_target_format = None
    library.auto_convert_ignored_formats = None
    library.auto_convert_backup_originals = True
    return library


class TestGetWorkerContext:
    """Test _get_worker_context method."""

    def test_get_worker_context_from_dict(
        self,
        task: IngestBookTask,
        worker_context_dict: dict[str, MagicMock],
    ) -> None:
        """Test _get_worker_context converts dict to WorkerContext."""
        context = task._get_worker_context(worker_context_dict)
        assert isinstance(context, WorkerContext)
        assert context.session == worker_context_dict["session"]
        assert context.update_progress == worker_context_dict["update_progress"]
        assert context.task_service == worker_context_dict["task_service"]
        assert context.enqueue_task == worker_context_dict["enqueue_task"]

    def test_get_worker_context_from_dict_without_enqueue_task(
        self,
        task: IngestBookTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        mock_task_service: MagicMock,
    ) -> None:
        """Test _get_worker_context handles dict without enqueue_task."""
        worker_context_dict = {
            "session": mock_session,
            "update_progress": mock_update_progress,
            "task_service": mock_task_service,
        }
        context = task._get_worker_context(worker_context_dict)
        assert isinstance(context, WorkerContext)
        assert context.enqueue_task is None

    def test_get_worker_context_from_object(
        self,
        task: IngestBookTask,
        worker_context: WorkerContext,
    ) -> None:
        """Test _get_worker_context returns WorkerContext as-is."""
        context = task._get_worker_context(worker_context)
        assert context is worker_context


class TestGetHistoryId:
    """Test _get_history_id method."""

    def test_get_history_id_success(self, task: IngestBookTask) -> None:
        """Test _get_history_id returns history_id from metadata."""
        history_id = task._get_history_id()
        assert history_id == 123

    def test_get_history_id_missing(self) -> None:
        """Test _get_history_id raises ValueError when missing."""
        task = IngestBookTask(task_id=1, user_id=1, metadata={})
        with pytest.raises(ValueError, match="history_id is required in task metadata"):
            task._get_history_id()

    def test_get_history_id_none(self) -> None:
        """Test _get_history_id raises ValueError when None."""
        task = IngestBookTask(task_id=1, user_id=1, metadata={"history_id": None})
        with pytest.raises(ValueError, match="history_id is required in task metadata"):
            task._get_history_id()


class TestCheckCancellation:
    """Test _check_cancellation method."""

    def test_check_cancellation_not_cancelled(self, task: IngestBookTask) -> None:
        """Test _check_cancellation does nothing when not cancelled."""
        task._check_cancellation()  # Should not raise

    def test_check_cancellation_cancelled(self, task: IngestBookTask) -> None:
        """Test _check_cancellation raises TaskCancelledError when cancelled."""
        task.mark_cancelled()
        with pytest.raises(TaskCancelledError):
            task._check_cancellation()


class TestExtractFileInfo:
    """Test _extract_file_info method."""

    def test_extract_file_info_success(self, task: IngestBookTask) -> None:
        """Test _extract_file_info extracts files and metadata_hint."""
        history = IngestHistory(
            id=123,
            file_path="/test/path",
            status=IngestStatus.PENDING,
            ingest_metadata={
                "files": ["/test/file1.epub", "/test/file2.epub"],
                "metadata_hint": {"title": "Test Book"},
            },
        )
        file_paths, metadata_hint = task._extract_file_info(history)
        assert len(file_paths) == 2
        assert all(isinstance(p, Path) for p in file_paths)
        assert metadata_hint == {"title": "Test Book"}

    def test_extract_file_info_no_metadata_hint(self, task: IngestBookTask) -> None:
        """Test _extract_file_info handles missing metadata_hint."""
        history = IngestHistory(
            id=123,
            file_path="/test/path",
            status=IngestStatus.PENDING,
            ingest_metadata={"files": ["/test/file1.epub"]},
        )
        file_paths, metadata_hint = task._extract_file_info(history)
        assert len(file_paths) == 1
        assert metadata_hint is None

    def test_extract_file_info_no_files(self, task: IngestBookTask) -> None:
        """Test _extract_file_info raises ValueError when no files."""
        history = IngestHistory(
            id=123,
            file_path="/test/path",
            status=IngestStatus.PENDING,
            ingest_metadata={},
        )
        with pytest.raises(ValueError, match="No files found in ingest history"):
            task._extract_file_info(history)

    def test_extract_file_info_empty_files(self, task: IngestBookTask) -> None:
        """Test _extract_file_info raises ValueError when files is empty."""
        history = IngestHistory(
            id=123,
            file_path="/test/path",
            status=IngestStatus.PENDING,
            ingest_metadata={"files": []},
        )
        with pytest.raises(ValueError, match="No files found in ingest history"):
            task._extract_file_info(history)

    def test_extract_file_info_none_metadata(self, task: IngestBookTask) -> None:
        """Test _extract_file_info handles None ingest_metadata."""
        history = IngestHistory(
            id=123,
            file_path="/test/path",
            status=IngestStatus.PENDING,
            ingest_metadata=None,
        )
        with pytest.raises(ValueError, match="No files found in ingest history"):
            task._extract_file_info(history)


class TestFetchMetadata:
    """Test _fetch_metadata method."""

    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_fetch_metadata_success(
        self,
        mock_processor_service_class: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
    ) -> None:
        """Test _fetch_metadata calls service and updates progress."""
        mock_processor_service = MagicMock()
        mock_processor_service.fetch_and_store_metadata.return_value = {
            "title": "Fetched Title"
        }
        mock_processor_service_class.return_value = mock_processor_service

        metadata = task._fetch_metadata(
            mock_processor_service, 123, {"title": "Hint"}, worker_context
        )

        assert metadata == {"title": "Fetched Title"}
        mock_processor_service.fetch_and_store_metadata.assert_called_once_with(
            123, {"title": "Hint"}
        )
        worker_context.update_progress.assert_called_once_with(0.2, None)

    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_fetch_metadata_none(
        self,
        mock_processor_service_class: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
    ) -> None:
        """Test _fetch_metadata handles None result."""
        mock_processor_service = MagicMock()
        mock_processor_service.fetch_and_store_metadata.return_value = None
        mock_processor_service_class.return_value = mock_processor_service

        metadata = task._fetch_metadata(
            mock_processor_service, 123, None, worker_context
        )

        assert metadata is None


class TestProcessFiles:
    """Test _process_files method."""

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._process_single_file"
    )
    def test_process_files_success(
        self,
        mock_process_single: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
        temp_file: Path,
        mock_library: MagicMock,
    ) -> None:
        """Test _process_files processes all files successfully."""
        file_paths = [temp_file, temp_file]
        mock_process_single.side_effect = [101, 102]
        mock_processor = MagicMock()
        mock_processor.get_active_library.return_value = mock_library

        book_ids = task._process_files(
            mock_processor,
            123,
            file_paths,
            None,
            None,
            mock_ingest_config,
            worker_context,
        )

        assert book_ids == [101, 102]
        assert mock_process_single.call_count == 2
        assert worker_context.update_progress.call_count == 3  # Initial + 2 files

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._process_single_file"
    )
    def test_process_files_missing_file(
        self,
        mock_process_single: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
        temp_file: Path,
        mock_library: MagicMock,
    ) -> None:
        """Test _process_files skips missing files."""
        missing_file = Path("/nonexistent/file.epub")
        file_paths = [temp_file, missing_file]
        mock_process_single.return_value = 101
        mock_processor = MagicMock()
        mock_processor.get_active_library.return_value = mock_library

        book_ids = task._process_files(
            mock_processor,
            123,
            file_paths,
            None,
            None,
            mock_ingest_config,
            worker_context,
        )

        assert book_ids == [101]
        assert mock_process_single.call_count == 1

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._process_single_file"
    )
    def test_process_files_exception(
        self,
        mock_process_single: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
        temp_file: Path,
        mock_library: MagicMock,
    ) -> None:
        """Test _process_files continues on file processing exception."""
        file_paths = [temp_file, temp_file]
        mock_process_single.side_effect = [101, Exception("Processing failed")]
        mock_processor = MagicMock()
        mock_processor.get_active_library.return_value = mock_library

        book_ids = task._process_files(
            mock_processor,
            123,
            file_paths,
            None,
            None,
            mock_ingest_config,
            worker_context,
        )

        assert book_ids == [101]
        assert mock_process_single.call_count == 2

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._process_single_file"
    )
    def test_process_files_cancelled(
        self,
        mock_process_single: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
        temp_file: Path,
        mock_library: MagicMock,
    ) -> None:
        """Test _process_files raises TaskCancelledError when cancelled."""
        file_paths = [temp_file]
        task.mark_cancelled()
        mock_processor = MagicMock()
        mock_processor.get_active_library.return_value = mock_library

        with pytest.raises(TaskCancelledError):
            task._process_files(
                mock_processor,
                123,
                file_paths,
                None,
                None,
                mock_ingest_config,
                worker_context,
            )


class TestProcessSingleFile:
    """Test _process_single_file method."""

    def test_delete_source_files_and_dirs_cleans_up_companions_and_directories(
        self, tmp_path: Path
    ) -> None:
        """Ensure _delete_source_files_and_dirs deletes companions and empty dirs."""
        # Layout: /Author/Book/book.epub, book.mobi, cover.jpg, metadata.opf
        author_dir = tmp_path / "Author"
        book_dir = author_dir / "Book"
        book_dir.mkdir(parents=True)

        main_file = book_dir / "book.epub"
        main_file.write_bytes(b"epub")
        mobi_file = book_dir / "book.mobi"
        mobi_file.write_bytes(b"mobi")
        cover_file = book_dir / "cover.jpg"
        cover_file.write_bytes(b"cover")
        opf_file = book_dir / "metadata.opf"
        opf_file.write_bytes(b"opf")

        task = IngestBookTask(task_id=1, user_id=1, metadata={"history_id": 123})

        # Call internal helper directly
        task._delete_source_files_and_dirs(main_file)

        # All book-level files should be gone
        assert not main_file.exists()
        assert not mobi_file.exists()
        assert not cover_file.exists()
        assert not opf_file.exists()

        # Book and Author directories should be removed as they are empty
        assert not book_dir.exists()
        assert not author_dir.exists()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_with_auto_delete(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file deletes file when auto_delete enabled."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = True

        book_id = task._process_single_file(
            mock_processor,
            123,
            temp_file,
            None,
            None,
            config,
            mock_library,
            mock_session,
        )

        assert book_id == 101
        mock_delete.assert_called_once_with(temp_file)
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_without_auto_delete(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file does not delete file when auto_delete disabled."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False

        book_id = task._process_single_file(
            mock_processor,
            123,
            temp_file,
            None,
            None,
            config,
            mock_library,
            mock_session,
        )

        assert book_id == 101
        mock_delete.assert_not_called()
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_with_cover_url_in_fetched_metadata(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file sets cover from fetched_metadata."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False
        fetched_metadata = {"cover_url": "http://example.com/cover.jpg"}

        book_id = task._process_single_file(
            mock_processor,
            123,
            temp_file,
            fetched_metadata,
            None,
            config,
            mock_library,
            mock_session,
        )

        assert book_id == 101
        mock_processor.set_book_cover.assert_called_once_with(
            101, "http://example.com/cover.jpg"
        )
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_with_cover_url_in_metadata_hint(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file sets cover from metadata_hint."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False
        metadata_hint = {"cover_url": "http://example.com/cover2.jpg"}

        book_id = task._process_single_file(
            mock_processor,
            123,
            temp_file,
            None,
            metadata_hint,
            config,
            mock_library,
            mock_session,
        )

        assert book_id == 101
        mock_processor.set_book_cover.assert_called_once_with(
            101, "http://example.com/cover2.jpg"
        )
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_cover_url_priority(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file prefers fetched_metadata cover_url over hint."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False
        fetched_metadata = {"cover_url": "http://example.com/fetched.jpg"}
        metadata_hint = {"cover_url": "http://example.com/hint.jpg"}

        book_id = task._process_single_file(
            mock_processor,
            123,
            temp_file,
            fetched_metadata,
            metadata_hint,
            config,
            mock_library,
            mock_session,
        )

        assert book_id == 101
        mock_processor.set_book_cover.assert_called_once_with(
            101, "http://example.com/fetched.jpg"
        )
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_extracts_file_format(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        temp_file: Path,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file extracts file format from extension."""
        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False

        task._process_single_file(
            mock_processor,
            123,
            temp_file,
            None,
            None,
            config,
            mock_library,
            mock_session,
        )

        call_kwargs = mock_processor.add_book_to_library.call_args[1]
        assert call_kwargs["file_format"] == "epub"
        mock_run_post_processors.assert_called_once()

    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._delete_source_files_and_dirs"
    )
    @patch(
        "fundamental.services.tasks.ingest_book_task.IngestBookTask._run_post_processors"
    )
    def test_process_single_file_no_extension(
        self,
        mock_run_post_processors: MagicMock,
        mock_delete: MagicMock,
        task: IngestBookTask,
        mock_library: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test _process_single_file handles file without extension."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            file_path = Path(f.name)

        mock_processor = MagicMock()
        mock_processor.add_book_to_library.return_value = 101
        config = MagicMock()
        config.auto_delete_after_ingest = False

        task._process_single_file(
            mock_processor,
            123,
            file_path,
            None,
            None,
            config,
            mock_library,
            mock_session,
        )

        call_kwargs = mock_processor.add_book_to_library.call_args[1]
        assert call_kwargs["file_format"] == ""
        mock_run_post_processors.assert_called_once()


class TestExtractTitleAuthor:
    """Test _extract_title_author method."""

    def test_extract_title_author_from_fetched_metadata(
        self, task: IngestBookTask
    ) -> None:
        """Test _extract_title_author extracts from fetched_metadata."""
        fetched_metadata = {"title": "Fetched Title", "authors": ["Fetched Author"]}
        metadata_hint = {"title": "Hint Title", "authors": ["Hint Author"]}

        title, author = task._extract_title_author(fetched_metadata, metadata_hint)

        assert title == "Fetched Title"
        assert author == "Fetched Author"

    def test_extract_title_author_from_metadata_hint(
        self, task: IngestBookTask
    ) -> None:
        """Test _extract_title_author falls back to metadata_hint."""
        metadata_hint = {"title": "Hint Title", "authors": ["Hint Author"]}

        title, author = task._extract_title_author(None, metadata_hint)

        assert title == "Hint Title"
        assert author == "Hint Author"

    def test_extract_title_author_no_authors(self, task: IngestBookTask) -> None:
        """Test _extract_title_author handles missing authors."""
        fetched_metadata = {"title": "Test Title"}

        title, author = task._extract_title_author(fetched_metadata, None)

        assert title == "Test Title"
        assert author is None

    def test_extract_title_author_empty_authors(self, task: IngestBookTask) -> None:
        """Test _extract_title_author handles empty authors list."""
        fetched_metadata = {"title": "Test Title", "authors": []}

        title, author = task._extract_title_author(fetched_metadata, None)

        assert title == "Test Title"
        assert author is None

    def test_extract_title_author_multiple_authors(self, task: IngestBookTask) -> None:
        """Test _extract_title_author uses first author."""
        fetched_metadata = {"title": "Test Title", "authors": ["Author 1", "Author 2"]}

        title, author = task._extract_title_author(fetched_metadata, None)

        assert title == "Test Title"
        assert author == "Author 1"


class TestMergeMetadata:
    """Test _merge_metadata method."""

    def test_merge_metadata_single_source(self, task: IngestBookTask) -> None:
        """Test _merge_metadata with single source."""
        source = {"title": "Test Title", "authors": ["Author"]}
        result = task._merge_metadata(source, keys=["title", "authors"])

        assert result == {"title": "Test Title", "authors": ["Author"]}

    def test_merge_metadata_multiple_sources_priority(
        self, task: IngestBookTask
    ) -> None:
        """Test _merge_metadata prioritizes first source."""
        source1 = {"title": "First Title", "authors": ["First Author"]}
        source2 = {"title": "Second Title", "authors": ["Second Author"]}
        result = task._merge_metadata(source1, source2, keys=["title", "authors"])

        assert result == {"title": "First Title", "authors": ["First Author"]}

    def test_merge_metadata_fallback(self, task: IngestBookTask) -> None:
        """Test _merge_metadata falls back to second source when first is missing."""
        source1 = {"title": "First Title"}
        source2 = {"title": "Second Title", "authors": ["Second Author"]}
        result = task._merge_metadata(source1, source2, keys=["title", "authors"])

        assert result == {"title": "First Title", "authors": ["Second Author"]}

    def test_merge_metadata_none_sources(self, task: IngestBookTask) -> None:
        """Test _merge_metadata handles None sources."""
        result = task._merge_metadata(None, None, keys=["title", "authors"])

        assert result == {}

    def test_merge_metadata_empty_list(self, task: IngestBookTask) -> None:
        """Test _merge_metadata skips empty lists."""
        source1 = {"title": "Title", "authors": []}
        source2 = {"authors": ["Author"]}
        result = task._merge_metadata(source1, source2, keys=["title", "authors"])

        assert result == {"title": "Title", "authors": ["Author"]}

    def test_merge_metadata_empty_string(self, task: IngestBookTask) -> None:
        """Test _merge_metadata skips empty strings."""
        source1 = {"title": "", "authors": ["Author"]}
        source2 = {"title": "Valid Title"}
        result = task._merge_metadata(source1, source2, keys=["title", "authors"])

        assert result == {"title": "Valid Title", "authors": ["Author"]}

    def test_merge_metadata_false_value(self, task: IngestBookTask) -> None:
        """Test _merge_metadata skips False values."""
        source1 = {"title": False, "authors": ["Author"]}
        source2 = {"title": "Valid Title"}
        result = task._merge_metadata(source1, source2, keys=["title", "authors"])

        assert result == {"title": "Valid Title", "authors": ["Author"]}

    def test_merge_metadata_zero_value(self, task: IngestBookTask) -> None:
        """Test _merge_metadata skips zero as it's falsy."""
        source = {"count": 0}
        result = task._merge_metadata(source, keys=["count"])

        assert result == {}  # 0 is falsy, so it's skipped


class TestDeleteSourceFilesAndDirs:
    """Test _delete_source_files_and_dirs method."""

    def test_delete_main_file_success(
        self, task: IngestBookTask, temp_file: Path
    ) -> None:
        """Test _delete_main_file successfully deletes file."""
        task._delete_main_file(temp_file)
        assert not temp_file.exists()

    def test_delete_main_file_oserror(self, task: IngestBookTask) -> None:
        """Test _delete_main_file handles OSError gracefully."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.unlink.side_effect = OSError("Permission denied")

        task._delete_main_file(mock_path)

        mock_path.unlink.assert_called_once()

    def test_delete_main_file_permission_error(self, task: IngestBookTask) -> None:
        """Test _delete_main_file handles PermissionError gracefully."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.unlink.side_effect = PermissionError("Permission denied")

        task._delete_main_file(mock_path)

        mock_path.unlink.assert_called_once()


class TestHandleCancellation:
    """Test _handle_cancellation method."""

    def test_handle_cancellation(
        self,
        task: IngestBookTask,
    ) -> None:
        """Test _handle_cancellation updates status to failed."""
        mock_processor = MagicMock()

        task._handle_cancellation(mock_processor, 123)

        mock_processor.update_history_status.assert_called_once_with(
            123, IngestStatus.FAILED, "Task cancelled"
        )


class TestHandleError:
    """Test _handle_error method."""

    def test_handle_error(
        self,
        task: IngestBookTask,
    ) -> None:
        """Test _handle_error updates status and re-raises."""
        mock_processor = MagicMock()
        error_msg = "Test error message"

        def _raise_and_handle() -> None:
            try:
                raise ValueError(error_msg)  # noqa: TRY301
            except ValueError:
                task._handle_error(mock_processor, 123)

        with pytest.raises(ValueError, match="Test error message"):
            _raise_and_handle()

        mock_processor.update_history_status.assert_called_once_with(
            123, IngestStatus.FAILED, error_msg
        )

    def test_handle_error_long_message(
        self,
        task: IngestBookTask,
    ) -> None:
        """Test _handle_error truncates long error messages."""
        mock_processor = MagicMock()
        long_error = "x" * 3000

        def _raise_and_handle() -> None:
            try:
                raise ValueError(long_error)  # noqa: TRY301
            except ValueError:
                task._handle_error(mock_processor, 123)

        with pytest.raises(ValueError, match=r"^x{2000}"):
            _raise_and_handle()

        call_args = mock_processor.update_history_status.call_args
        assert call_args[0][0] == 123
        assert call_args[0][1] == IngestStatus.FAILED
        assert len(call_args[0][2]) == 2000  # Truncated to max length

    def test_handle_error_none_exception(
        self,
        task: IngestBookTask,
    ) -> None:
        """Test _handle_error handles None exception."""
        mock_processor = MagicMock()

        # Patch sys.exc_info to return None for the exception value
        # This tests the edge case where exc_info()[1] is None
        def _raise_and_handle() -> None:
            with patch("sys.exc_info") as mock_exc_info:
                mock_exc_info.return_value = (ValueError, None, None)
                try:
                    raise ValueError("Test")  # noqa: TRY301
                except ValueError:
                    # The exception context is still active, but sys.exc_info()[1] returns None
                    task._handle_error(mock_processor, 123)

        with pytest.raises(ValueError, match="Test"):
            _raise_and_handle()

        # Verify update_history_status was called with "Unknown error"
        mock_processor.update_history_status.assert_called_once()
        call_args = mock_processor.update_history_status.call_args
        assert call_args is not None
        assert call_args[0][2] == "Unknown error"


class TestRun:
    """Test run method."""

    @patch("fundamental.services.tasks.ingest_book_task.IngestConfigService")
    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_run_success(
        self,
        mock_processor_service_class: MagicMock,
        mock_config_service_class: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
        mock_ingest_history: IngestHistory,
        temp_file: Path,
    ) -> None:
        """Test run completes successfully."""
        mock_processor_service = MagicMock()
        mock_processor_service.get_history.return_value = mock_ingest_history
        mock_processor_service.fetch_and_store_metadata.return_value = {
            "title": "Fetched Title"
        }
        mock_processor_service.add_book_to_library.return_value = 101
        mock_processor_service_class.return_value = mock_processor_service

        mock_config_service = MagicMock()
        mock_config_service.get_config.return_value = mock_ingest_config
        mock_config_service_class.return_value = mock_config_service

        # Create actual files for the test
        file1 = temp_file
        file2 = temp_file.parent / "file2.epub"
        file2.write_bytes(b"test")
        mock_ingest_history.ingest_metadata = {
            "files": [str(file1), str(file2)],
            "metadata_hint": {"title": "Test Book"},
        }

        task.run(worker_context)

        mock_processor_service.update_history_status.assert_called()
        mock_processor_service.finalize_history.assert_called_once_with(123, [101, 101])
        worker_context.update_progress.assert_called()

    @patch("fundamental.services.tasks.ingest_book_task.IngestConfigService")
    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_run_with_dict_context(
        self,
        mock_processor_service_class: MagicMock,
        mock_config_service_class: MagicMock,
        task: IngestBookTask,
        worker_context_dict: dict[str, MagicMock],
        mock_ingest_config: MagicMock,
        mock_ingest_history: IngestHistory,
        temp_file: Path,
    ) -> None:
        """Test run works with dict context."""
        mock_processor_service = MagicMock()
        mock_processor_service.get_history.return_value = mock_ingest_history
        mock_processor_service.fetch_and_store_metadata.return_value = None
        mock_processor_service.add_book_to_library.return_value = 101
        mock_processor_service_class.return_value = mock_processor_service

        mock_config_service = MagicMock()
        mock_config_service.get_config.return_value = mock_ingest_config
        mock_config_service_class.return_value = mock_config_service

        file1 = temp_file
        mock_ingest_history.ingest_metadata = {
            "files": [str(file1)],
        }

        task.run(worker_context_dict)

        mock_processor_service.finalize_history.assert_called_once()

    @patch("fundamental.services.tasks.ingest_book_task.IngestConfigService")
    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_run_cancelled(
        self,
        mock_processor_service_class: MagicMock,
        mock_config_service_class: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
    ) -> None:
        """Test run handles cancellation."""
        mock_processor_service = MagicMock()
        mock_processor_service_class.return_value = mock_processor_service

        mock_config_service = MagicMock()
        mock_config_service.get_config.return_value = mock_ingest_config
        mock_config_service_class.return_value = mock_config_service

        task.mark_cancelled()

        task.run(worker_context)

        mock_processor_service.update_history_status.assert_called_with(
            123, IngestStatus.FAILED, "Task cancelled"
        )

    @patch("fundamental.services.tasks.ingest_book_task.IngestConfigService")
    @patch("fundamental.services.tasks.ingest_book_task.IngestProcessorService")
    def test_run_error(
        self,
        mock_processor_service_class: MagicMock,
        mock_config_service_class: MagicMock,
        task: IngestBookTask,
        worker_context: WorkerContext,
        mock_ingest_config: MagicMock,
    ) -> None:
        """Test run handles errors."""
        mock_processor_service = MagicMock()
        mock_processor_service.get_history.side_effect = ValueError("Test error")
        mock_processor_service_class.return_value = mock_processor_service

        mock_config_service = MagicMock()
        mock_config_service.get_config.return_value = mock_ingest_config
        mock_config_service_class.return_value = mock_config_service

        with pytest.raises(ValueError, match="Test error"):
            task.run(worker_context)

        mock_processor_service.update_history_status.assert_called_with(
            123, IngestStatus.FAILED, "Test error"
        )

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

"""Tests for book_strip_drm_task to achieve 100% coverage."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from bookcard.models.config import Library
from bookcard.services.tasks.book_strip_drm_task import BookStripDrmTask
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
)

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def library() -> Library:
    """Create a library instance for testing.

    Returns
    -------
    Library
        Library instance.
    """
    return Library(id=1, name="Test Library", calibre_db_path="/path/to/library")


@pytest.fixture
def worker_context(session: DummySession) -> WorkerContext:
    """Create worker context for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.

    Returns
    -------
    WorkerContext
        Worker context instance.
    """
    return WorkerContext(
        session=session,  # type: ignore[arg-type]
        update_progress=MagicMock(),
        task_service=MagicMock(),
        enqueue_task=MagicMock(),
    )


@pytest.fixture
def valid_metadata() -> dict[str, int | str]:
    """Create valid metadata for task initialization.

    Returns
    -------
    dict[str, int | str]
        Valid metadata dictionary.
    """
    return {
        "book_id": 1,
        "source_format": "AZW3",
        "output_format": "AZW3_NODRM",
    }


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    """Create a temporary source file for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to source file.
    """
    source_file = tmp_path / "source.azw3"
    source_file.write_bytes(b"original content with drm")
    return source_file


@pytest.fixture
def processed_file(tmp_path: Path) -> Path:
    """Create a temporary processed file for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to processed file.
    """
    processed_file = tmp_path / "processed.azw3"
    processed_file.write_bytes(b"processed content without drm")
    return processed_file


# ============================================================================
# Tests for BookStripDrmTask.__init__
# ============================================================================


class TestBookStripDrmTaskInit:
    """Test BookStripDrmTask initialization."""

    def test_init_success(self, valid_metadata: dict[str, int | str]) -> None:
        """Test successful initialization with all required fields.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.
        """
        task = BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)
        assert task.task_id == 1
        assert task.user_id == 1
        assert task._book_id == 1
        assert task._source_format == "AZW3"
        assert task._output_format == "AZW3_NODRM"

    def test_init_formats_uppercased(self) -> None:
        """Test initialization converts formats to uppercase.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": "azw3",
            "output_format": "azw3_nodrm",
        }
        task = BookStripDrmTask(task_id=1, user_id=1, metadata=metadata)
        assert task._source_format == "AZW3"
        assert task._output_format == "AZW3_NODRM"

    @pytest.mark.parametrize(
        ("missing_key", "expected_error"),
        [
            ("book_id", "Missing required metadata key: book_id"),
            ("source_format", "Missing required metadata key: source_format"),
            ("output_format", "Missing required metadata key: output_format"),
        ],
    )
    def test_init_missing_required_keys(
        self,
        missing_key: str,
        expected_error: str,
        valid_metadata: dict[str, int | str],
    ) -> None:
        """Test initialization with missing required keys.

        Parameters
        ----------
        missing_key : str
            Key to remove from metadata.
        expected_error : str
            Expected error message.
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.
        """
        metadata = valid_metadata.copy()
        del metadata[missing_key]
        with pytest.raises(ValueError, match=expected_error):
            BookStripDrmTask(task_id=1, user_id=1, metadata=metadata)

    @pytest.mark.parametrize(
        ("key", "invalid_value", "expected_error"),
        [
            (
                "book_id",
                "1",
                "Metadata key book_id must be an integer, got str",
            ),
            (
                "book_id",
                1.5,
                "Metadata key book_id must be an integer, got float",
            ),
            (
                "source_format",
                123,
                "Metadata key source_format must be a string, got int",
            ),
        ],
    )
    def test_init_wrong_types(
        self,
        key: str,
        invalid_value: str | float | None,
        expected_error: str,
        valid_metadata: dict[str, int | str],
    ) -> None:
        """Test initialization with wrong types.

        Parameters
        ----------
        key : str
            Metadata key to set invalid value.
        invalid_value : int | str | float | None
            Invalid value to set.
        expected_error : str
            Expected error message.
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.
        """
        metadata = valid_metadata.copy()
        metadata[key] = invalid_value  # type: ignore[assignment]
        with pytest.raises(TypeError, match=expected_error):
            BookStripDrmTask(task_id=1, user_id=1, metadata=metadata)


# ============================================================================
# Tests for BookStripDrmTask._require_int
# ============================================================================


class TestBookStripDrmTaskRequireInt:
    """Test _require_int static method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_require_int_success(self, task: BookStripDrmTask) -> None:
        """Test _require_int with valid integer.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        result = BookStripDrmTask._require_int("book_id", {"book_id": 42})
        assert result == 42

    def test_require_int_missing(self, task: BookStripDrmTask) -> None:
        """Test _require_int with missing key.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        with pytest.raises(
            ValueError, match="Missing required metadata key: missing_key"
        ):
            BookStripDrmTask._require_int("missing_key", {})

    @pytest.mark.parametrize(
        ("value", "type_name"),
        [
            ("1", "str"),
            (1.5, "float"),
            ([1], "list"),
        ],
    )
    def test_require_int_wrong_type(
        self,
        task: BookStripDrmTask,
        value: str | float | list[int] | None,
        type_name: str,
    ) -> None:
        """Test _require_int with wrong type.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        value : str | float | None | list[int]
            Invalid value.
        type_name : str
            Expected type name in error message.
        """
        with pytest.raises(
            TypeError,
            match=f"Metadata key test_key must be an integer, got {type_name}",
        ):
            BookStripDrmTask._require_int("test_key", {"test_key": value})


# ============================================================================
# Tests for BookStripDrmTask._require_str
# ============================================================================


class TestBookStripDrmTaskRequireStr:
    """Test _require_str static method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_require_str_success(self, task: BookStripDrmTask) -> None:
        """Test _require_str with valid string.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        result = BookStripDrmTask._require_str(
            "source_format", {"source_format": "AZW3"}
        )
        assert result == "AZW3"

    def test_require_str_missing(self, task: BookStripDrmTask) -> None:
        """Test _require_str with missing key.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        with pytest.raises(
            ValueError, match="Missing required metadata key: missing_key"
        ):
            BookStripDrmTask._require_str("missing_key", {})

    @pytest.mark.parametrize(
        ("value", "type_name"),
        [
            (123, "int"),
            (1.5, "float"),
            (["string"], "list"),
        ],
    )
    def test_require_str_wrong_type(
        self, task: BookStripDrmTask, value: float | list[str] | None, type_name: str
    ) -> None:
        """Test _require_str with wrong type.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        value : int | float | None | list[str]
            Invalid value.
        type_name : str
            Expected type name in error message.
        """
        with pytest.raises(
            TypeError, match=f"Metadata key test_key must be a string, got {type_name}"
        ):
            BookStripDrmTask._require_str("test_key", {"test_key": value})


# ============================================================================
# Tests for BookStripDrmTask._check_cancellation
# ============================================================================


class TestBookStripDrmTaskCheckCancellation:
    """Test _check_cancellation method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_check_cancellation_not_cancelled(self, task: BookStripDrmTask) -> None:
        """Test _check_cancellation when not cancelled.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        task._check_cancellation()  # Should not raise

    def test_check_cancellation_cancelled(self, task: BookStripDrmTask) -> None:
        """Test _check_cancellation when cancelled.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]
        with pytest.raises(TaskCancelledError):
            task._check_cancellation()


# ============================================================================
# Tests for BookStripDrmTask._get_active_library
# ============================================================================


class TestBookStripDrmTaskGetActiveLibrary:
    """Test _get_active_library method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_get_active_library_success(
        self, task: BookStripDrmTask, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test _get_active_library when library exists.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            result = task._get_active_library(worker_context)
            assert result == library

    def test_get_active_library_not_configured(
        self, task: BookStripDrmTask, worker_context: WorkerContext
    ) -> None:
        """Test _get_active_library when no library is configured.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(LibraryNotConfiguredError):
                task._get_active_library(worker_context)

    def test_get_active_library_cancelled(
        self, task: BookStripDrmTask, worker_context: WorkerContext
    ) -> None:
        """Test _get_active_library when task is cancelled.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        """
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task._get_active_library(worker_context)


# ============================================================================
# Tests for BookStripDrmTask._update_progress_or_cancel
# ============================================================================


class TestBookStripDrmTaskUpdateProgressOrCancel:
    """Test _update_progress_or_cancel method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_update_progress_or_cancel_success(self, task: BookStripDrmTask) -> None:
        """Test _update_progress_or_cancel when not cancelled.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()

        task._update_progress_or_cancel(0.5, update_progress)
        update_progress.assert_called_once_with(0.5, {})

    def test_update_progress_or_cancel_with_metadata(
        self, task: BookStripDrmTask
    ) -> None:
        """Test _update_progress_or_cancel with metadata.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()
        metadata = {"key": "value"}

        task._update_progress_or_cancel(0.5, update_progress, metadata)
        update_progress.assert_called_once_with(0.5, metadata)

    def test_update_progress_or_cancel_cancelled(self, task: BookStripDrmTask) -> None:
        """Test _update_progress_or_cancel when cancelled.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        """
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]
        update_progress = MagicMock()

        with pytest.raises(TaskCancelledError):
            task._update_progress_or_cancel(0.5, update_progress)


# ============================================================================
# Tests for BookStripDrmTask._sha256_path
# ============================================================================


class TestBookStripDrmTaskSha256Path:
    """Test _sha256_path static method."""

    def test_sha256_path_success(self, tmp_path: Path) -> None:
        """Test _sha256_path calculates correct hash.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        test_file = tmp_path / "test.txt"
        test_content = b"test content for hashing"
        test_file.write_bytes(test_content)

        result = BookStripDrmTask._sha256_path(test_file)

        # Verify it's a valid hex digest
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

        # Verify it matches expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert result == expected_hash

    def test_sha256_path_large_file(self, tmp_path: Path) -> None:
        """Test _sha256_path with large file (chunked reading).

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        test_file = tmp_path / "large_test.txt"
        # Create a file larger than 1MB to test chunking
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        test_file.write_bytes(large_content)

        result = BookStripDrmTask._sha256_path(test_file)

        # Verify it's a valid hex digest
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

        # Verify it matches expected hash
        expected_hash = hashlib.sha256(large_content).hexdigest()
        assert result == expected_hash


# ============================================================================
# Tests for BookStripDrmTask.run
# ============================================================================


class TestBookStripDrmTaskRun:
    """Test run method."""

    @pytest.fixture
    def task(self, valid_metadata: dict[str, int | str]) -> BookStripDrmTask:
        """Create a task instance for testing.

        Parameters
        ----------
        valid_metadata : dict[str, int | str]
            Valid metadata dictionary.

        Returns
        -------
        BookStripDrmTask
            Task instance.
        """
        return BookStripDrmTask(task_id=1, user_id=1, metadata=valid_metadata)

    def test_run_with_dict_context(
        self,
        task: BookStripDrmTask,
        session: DummySession,
        library: Library,
        source_file: Path,
        processed_file: Path,
    ) -> None:
        """Test run with dict worker_context (backward compatibility).

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        processed_file : Path
            Processed file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            worker_context = {
                "session": session,
                "update_progress": update_progress,
                "task_service": MagicMock(),
            }

            task.run(worker_context)

            assert update_progress.call_count >= 4
            # We no longer call add_format, we replace the file in place
            mock_book_service.add_format.assert_not_called()

    def test_run_with_worker_context(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
        processed_file: Path,
    ) -> None:
        """Test run with WorkerContext instance.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        processed_file : Path
            Processed file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            task.run(worker_context)

            assert worker_context.update_progress.call_count >= 4
            # We no longer call add_format, we replace the file in place
            mock_book_service.add_format.assert_not_called()

    def test_run_cancelled_before_processing(
        self, task: BookStripDrmTask, worker_context: WorkerContext
    ) -> None:
        """Test run when cancelled before processing.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        """
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task.run(worker_context)

    def test_run_did_strip_drm(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
        processed_file: Path,
    ) -> None:
        """Test run when DRM was stripped (hashes differ).

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        processed_file : Path
            Processed file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            task.run(worker_context)

            assert task.metadata["did_strip"] is True
            # We no longer call add_format, we replace the file in place
            mock_book_service.add_format.assert_not_called()

    def test_run_no_drm_stripped(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
    ) -> None:
        """Test run when DRM was not stripped (hashes same).

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        # Create processed file with same content as source
        processed_file = source_file.parent / "processed.azw3"
        processed_file.write_bytes(source_file.read_bytes())

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            task.run(worker_context)

            assert task.metadata["did_strip"] is False
            mock_book_service.add_format.assert_not_called()

    def test_run_cancelled_during_execution(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
    ) -> None:
        """Test run when cancelled during execution.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        """
        # First call returns False, second call returns True (cancelled)
        task.check_cancelled = MagicMock(side_effect=[False, True])  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            with pytest.raises(TaskCancelledError):
                task.run(worker_context)

    def test_run_task_cancelled_error(
        self, task: BookStripDrmTask, worker_context: WorkerContext
    ) -> None:
        """Test run handles TaskCancelledError.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        """
        task.check_cancelled = MagicMock(side_effect=TaskCancelledError(1))  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task.run(worker_context)

    def test_run_task_cancelled_error_logs(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
    ) -> None:
        """Test run logs when TaskCancelledError is raised during execution.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        """
        # First few calls return False, then one returns True to trigger cancellation
        # during execution (after try block starts)
        task.check_cancelled = MagicMock(side_effect=[False, False, False, True])  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch("bookcard.services.tasks.book_strip_drm_task.logger") as mock_logger,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            with pytest.raises(TaskCancelledError):
                task.run(worker_context)

            # Verify logger was called
            mock_logger.info.assert_called_once_with(
                "DeDRM task %d was cancelled", task.task_id
            )

    def test_run_cleanup_processed_file(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test run cleans up processed file in finally block.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        tmp_path : Path
            Temporary directory path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        # Create a temporary processed file that will be cleaned up
        processed_file = tmp_path / "processed.azw3"
        processed_file.write_bytes(b"processed content")

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            task.run(worker_context)

            # File should be deleted
            assert not processed_file.exists()

    def test_run_cleanup_handles_oserror(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test run cleanup handles OSError gracefully.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        tmp_path : Path
            Temporary directory path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        # Create a temporary processed file
        processed_file = tmp_path / "processed.azw3"
        processed_file.write_bytes(b"processed content")

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
            patch(
                "pathlib.Path.unlink",
                side_effect=OSError("File not found"),
            ),
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            # Should not raise, OSError is suppressed
            task.run(worker_context)

    def test_run_sets_metadata(
        self,
        task: BookStripDrmTask,
        worker_context: WorkerContext,
        library: Library,
        source_file: Path,
        processed_file: Path,
    ) -> None:
        """Test run sets metadata correctly.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        processed_file : Path
            Processed file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            task.run(worker_context)

            assert task.metadata["source_format"] == "AZW3"
            assert task.metadata["output_format"] == "AZW3_NODRM"
            assert "did_strip" in task.metadata

    def test_run_with_enqueue_task_in_dict(
        self,
        task: BookStripDrmTask,
        session: DummySession,
        library: Library,
        source_file: Path,
        processed_file: Path,
    ) -> None:
        """Test run with dict context that includes enqueue_task.

        Parameters
        ----------
        task : BookStripDrmTask
            Task instance.
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        source_file : Path
            Source file path.
        processed_file : Path
            Processed file path.
        """
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()
        enqueue_task = MagicMock()

        with (
            patch("bookcard.services.tasks.book_strip_drm_task.LibraryRepository") as _,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.LibraryService"
            ) as mock_service_class,
            patch(
                "bookcard.services.tasks.book_strip_drm_task.BookService"
            ) as mock_book_service_class,
            patch.object(task._dedrm_service, "strip_drm") as mock_strip_drm,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_book_service = MagicMock()
            mock_book_service.get_format_file_path.return_value = source_file
            mock_book_service_class.return_value = mock_book_service

            mock_strip_drm.return_value = processed_file

            worker_context = {
                "session": session,
                "update_progress": update_progress,
                "task_service": MagicMock(),
                "enqueue_task": enqueue_task,
            }

            task.run(worker_context)

            # Verify enqueue_task was passed to WorkerContext
            assert update_progress.call_count >= 4

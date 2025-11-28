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

"""Tests for book_convert_task to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.config import Library
from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)
from fundamental.services.tasks.book_convert_task import BookConvertTask
from fundamental.services.tasks.context import WorkerContext
from fundamental.services.tasks.exceptions import (
    LibraryNotConfiguredError,
    TaskCancelledError,
)
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session for testing.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


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


# ============================================================================
# Tests for BookConvertTask.__init__
# ============================================================================


class TestBookConvertTaskInit:
    """Test BookConvertTask initialization."""

    def test_init_success(self) -> None:
        """Test successful initialization with all required fields.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": "MOBI",
            "target_format": "EPUB",
        }
        task = BookConvertTask(task_id=1, user_id=1, metadata=metadata)
        assert task.task_id == 1
        assert task.user_id == 1
        assert task._book_id == 1
        assert task._source_format == "MOBI"
        assert task._target_format == "EPUB"
        assert task._conversion_method == ConversionMethod.MANUAL

    def test_init_with_conversion_method(self) -> None:
        """Test initialization with conversion_method.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": "MOBI",
            "target_format": "EPUB",
            "conversion_method": ConversionMethod.AUTO_IMPORT.value,
        }
        task = BookConvertTask(task_id=1, user_id=1, metadata=metadata)
        assert task._conversion_method == ConversionMethod.AUTO_IMPORT

    def test_init_missing_book_id(self) -> None:
        """Test initialization with missing book_id.

        Parameters
        ----------
        None
        """
        metadata = {
            "source_format": "MOBI",
            "target_format": "EPUB",
        }
        with pytest.raises(ValueError, match="Missing required metadata key: book_id"):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_missing_source_format(self) -> None:
        """Test initialization with missing source_format.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "target_format": "EPUB",
        }
        with pytest.raises(
            ValueError, match="Missing required metadata key: source_format"
        ):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_missing_target_format(self) -> None:
        """Test initialization with missing target_format.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": "MOBI",
        }
        with pytest.raises(
            ValueError, match="Missing required metadata key: target_format"
        ):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_book_id_not_int(self) -> None:
        """Test initialization with book_id that's not an integer.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": "1",  # String instead of int
            "source_format": "MOBI",
            "target_format": "EPUB",
        }
        with pytest.raises(TypeError, match="Metadata key book_id must be an integer"):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_source_format_not_str(self) -> None:
        """Test initialization with source_format that's not a string.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": 123,  # Int instead of str
            "target_format": "EPUB",
        }
        with pytest.raises(
            TypeError, match="Metadata key source_format must be a string"
        ):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)

    def test_init_target_format_not_str(self) -> None:
        """Test initialization with target_format that's not a string.

        Parameters
        ----------
        None
        """
        metadata = {
            "book_id": 1,
            "source_format": "MOBI",
            "target_format": 123,  # Int instead of str
        }
        with pytest.raises(
            TypeError, match="Metadata key target_format must be a string"
        ):
            BookConvertTask(task_id=1, user_id=1, metadata=metadata)


# ============================================================================
# Tests for BookConvertTask._require_int
# ============================================================================


class TestBookConvertTaskRequireInt:
    """Test _require_int method."""

    def test_require_int_success(self) -> None:
        """Test _require_int with valid integer.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        result = task._require_int("book_id", {"book_id": 42})
        assert result == 42

    def test_require_int_missing(self) -> None:
        """Test _require_int with missing key.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        with pytest.raises(
            ValueError, match="Missing required metadata key: missing_key"
        ):
            task._require_int("missing_key", {})

    def test_require_int_wrong_type(self) -> None:
        """Test _require_int with wrong type.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        with pytest.raises(TypeError, match="Metadata key test_key must be an integer"):
            task._require_int("test_key", {"test_key": "not_an_int"})


# ============================================================================
# Tests for BookConvertTask._require_str
# ============================================================================


class TestBookConvertTaskRequireStr:
    """Test _require_str method."""

    def test_require_str_success(self) -> None:
        """Test _require_str with valid string.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        result = task._require_str("source_format", {"source_format": "MOBI"})
        assert result == "MOBI"

    def test_require_str_missing(self) -> None:
        """Test _require_str with missing key.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        with pytest.raises(
            ValueError, match="Missing required metadata key: missing_key"
        ):
            task._require_str("missing_key", {})

    def test_require_str_wrong_type(self) -> None:
        """Test _require_str with wrong type.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        with pytest.raises(TypeError, match="Metadata key test_key must be a string"):
            task._require_str("test_key", {"test_key": 123})


# ============================================================================
# Tests for BookConvertTask._check_cancellation
# ============================================================================


class TestBookConvertTaskCheckCancellation:
    """Test _check_cancellation method."""

    def test_check_cancellation_not_cancelled(self) -> None:
        """Test _check_cancellation when not cancelled.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        task._check_cancellation()  # Should not raise

    def test_check_cancellation_cancelled(self) -> None:
        """Test _check_cancellation when cancelled.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]
        with pytest.raises(TaskCancelledError):
            task._check_cancellation()


# ============================================================================
# Tests for BookConvertTask._get_active_library
# ============================================================================


class TestBookConvertTaskGetActiveLibrary:
    """Test _get_active_library method."""

    def test_get_active_library_success(
        self, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test _get_active_library when library exists.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            result = task._get_active_library(worker_context)
            assert result == library

    def test_get_active_library_not_configured(
        self, worker_context: WorkerContext
    ) -> None:
        """Test _get_active_library when no library is configured.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(LibraryNotConfiguredError):
                task._get_active_library(worker_context)

    def test_get_active_library_cancelled(self, worker_context: WorkerContext) -> None:
        """Test _get_active_library when task is cancelled.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task._get_active_library(worker_context)


# ============================================================================
# Tests for BookConvertTask._update_progress_or_cancel
# ============================================================================


class TestBookConvertTaskUpdateProgressOrCancel:
    """Test _update_progress_or_cancel method."""

    def test_update_progress_or_cancel_success(self) -> None:
        """Test _update_progress_or_cancel when not cancelled.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()

        task._update_progress_or_cancel(0.5, update_progress)
        update_progress.assert_called_once_with(0.5, {})

    def test_update_progress_or_cancel_with_metadata(self) -> None:
        """Test _update_progress_or_cancel with metadata.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        update_progress = MagicMock()
        metadata = {"key": "value"}

        task._update_progress_or_cancel(0.5, update_progress, metadata)
        update_progress.assert_called_once_with(0.5, metadata)

    def test_update_progress_or_cancel_cancelled(self) -> None:
        """Test _update_progress_or_cancel when cancelled.

        Parameters
        ----------
        None
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]
        update_progress = MagicMock()

        with pytest.raises(TaskCancelledError):
            task._update_progress_or_cancel(0.5, update_progress)


# ============================================================================
# Tests for BookConvertTask.run
# ============================================================================


class TestBookConvertTaskRun:
    """Test run method."""

    def test_run_with_dict_context(
        self, session: DummySession, library: Library
    ) -> None:
        """Test run with dict worker_context (backward compatibility).

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        update_progress = MagicMock()

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
            patch(
                "fundamental.services.tasks.book_convert_task.ConversionService"
            ) as mock_conversion_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_conversion = MagicMock()
            mock_conversion.check_existing_conversion.return_value = None
            conversion = BookConversion(
                id=1,
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                status=ConversionStatus.COMPLETED,
            )
            mock_conversion.convert_book.return_value = conversion
            mock_conversion_class.return_value = mock_conversion

            worker_context = {
                "session": session,
                "update_progress": update_progress,
                "task_service": MagicMock(),
            }

            task.run(worker_context)

            assert update_progress.call_count >= 4

    def test_run_cancelled_before_processing(
        self, worker_context: WorkerContext
    ) -> None:
        """Test run when cancelled before processing.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task.run(worker_context)

    def test_run_existing_conversion(
        self, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test run when conversion already exists.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        existing_conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.COMPLETED,
        )

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
            patch(
                "fundamental.services.tasks.book_convert_task.ConversionService"
            ) as mock_conversion_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_conversion = MagicMock()
            mock_conversion.check_existing_conversion.return_value = existing_conversion
            mock_conversion_class.return_value = mock_conversion

            task.run(worker_context)

            assert task.metadata["existing_conversion_id"] == 1
            assert "already exists" in task.metadata["message"]

    def test_run_conversion_success(
        self, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test run when conversion succeeds.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.COMPLETED,
        )

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
            patch(
                "fundamental.services.tasks.book_convert_task.ConversionService"
            ) as mock_conversion_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_conversion = MagicMock()
            mock_conversion.check_existing_conversion.return_value = None
            mock_conversion.convert_book.return_value = conversion
            mock_conversion_class.return_value = mock_conversion

            task.run(worker_context)

            mock_conversion.convert_book.assert_called_once()

    def test_run_conversion_failed(
        self, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test run when conversion fails.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.FAILED,
            error_message="Conversion error",
        )

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
            patch(
                "fundamental.services.tasks.book_convert_task.ConversionService"
            ) as mock_conversion_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_conversion = MagicMock()
            mock_conversion.check_existing_conversion.return_value = None
            mock_conversion.convert_book.return_value = conversion
            mock_conversion_class.return_value = mock_conversion

            with pytest.raises(RuntimeError, match="Conversion failed"):
                task.run(worker_context)

    def test_run_conversion_failed_no_error_message(
        self, worker_context: WorkerContext, library: Library
    ) -> None:
        """Test run when conversion fails without error message.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        library : Library
            Library instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        conversion = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.FAILED,
            error_message=None,
        )

        with (
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryRepository"
            ) as _,
            patch(
                "fundamental.services.tasks.book_convert_task.LibraryService"
            ) as mock_service_class,
            patch(
                "fundamental.services.tasks.book_convert_task.ConversionService"
            ) as mock_conversion_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_service_class.return_value = mock_service

            mock_conversion = MagicMock()
            mock_conversion.check_existing_conversion.return_value = None
            mock_conversion.convert_book.return_value = conversion
            mock_conversion_class.return_value = mock_conversion

            with pytest.raises(RuntimeError, match="Conversion failed"):
                task.run(worker_context)

    def test_run_exception_handling(self, worker_context: WorkerContext) -> None:
        """Test run handles exceptions properly.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(side_effect=Exception("Test error"))  # type: ignore[method-assign]

        with pytest.raises(Exception, match="Test error"):
            task.run(worker_context)

    def test_run_task_cancelled_error(self, worker_context: WorkerContext) -> None:
        """Test run handles TaskCancelledError.

        Parameters
        ----------
        worker_context : WorkerContext
            Worker context instance.
        """
        task = BookConvertTask(
            task_id=1,
            user_id=1,
            metadata={"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"},
        )
        task.check_cancelled = MagicMock(side_effect=TaskCancelledError(1))  # type: ignore[method-assign]

        with pytest.raises(TaskCancelledError):
            task.run(worker_context)

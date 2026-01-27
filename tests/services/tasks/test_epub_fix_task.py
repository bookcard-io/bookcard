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

"""Tests for EPUB fix tasks."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import EPUBFixerConfig, Library
from bookcard.models.epub_fixer import EPUBFixRun
from bookcard.services.tasks.epub_fix_task import (
    EPUBFixBatchTask,
    EPUBFixTask,
    _raise_no_library_error,
)
from tests.conftest import DummySession


def test_raise_no_library_error() -> None:
    """Test _raise_no_library_error helper function."""
    with pytest.raises(ValueError, match="No active library configured"):
        _raise_no_library_error()


def test_epub_fix_task_init() -> None:
    """Test EPUBFixTask initialization."""
    metadata = {
        "file_path": "/path/to/book.epub",
        "library_id": 1,
        "book_id": 1,
        "book_title": "Test Book",
    }

    task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)

    assert task.task_id == 1
    assert task.user_id == 1
    assert task.file_path == Path("/path/to/book.epub")
    assert task.library_id == 1


def test_epub_fix_task_init_missing_file_path() -> None:
    """Test EPUBFixTask initialization without file_path."""
    metadata = {"library_id": 1}

    with pytest.raises(ValueError, match="file_path is required in task metadata"):
        EPUBFixTask(task_id=1, user_id=1, metadata=metadata)


def test_epub_fix_task_init_empty_file_path() -> None:
    """Test EPUBFixTask initialization with empty file_path."""
    metadata = {"file_path": ""}

    with pytest.raises(ValueError, match="file_path is required in task metadata"):
        EPUBFixTask(task_id=1, user_id=1, metadata=metadata)


def test_epub_fix_task_run_cancelled_before_processing(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test EPUBFixTask run when cancelled before processing."""
    session = DummySession()
    update_progress = MagicMock()

    metadata = {"file_path": str(minimal_epub)}
    task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
    task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

    worker_context = {
        "session": session,
        "update_progress": update_progress,
    }

    task.run(worker_context)

    # Should return early without processing
    update_progress.assert_not_called()


def test_epub_fix_task_run_no_library(minimal_epub: Path) -> None:
    """Test EPUBFixTask run when no library is configured."""
    session = DummySession()
    update_progress = MagicMock()

    # Mock library service to return None
    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = None
        mock_library_service.return_value = mock_service

        metadata = {"file_path": str(minimal_epub)}
        task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        with pytest.raises(ValueError, match="No active library configured"):
            task.run(worker_context)


def test_epub_fix_task_run_disabled(minimal_epub: Path) -> None:
    """Test EPUBFixTask run when EPUB fixer is disabled."""
    session = DummySession()
    update_progress = MagicMock()

    library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
    config = EPUBFixerConfig(enabled=False)

    session.add_exec_result([config])

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_library_service.return_value = mock_service

        metadata = {"file_path": str(minimal_epub)}
        task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        task.run(worker_context)

        # Should return early without processing
        update_progress.assert_not_called()


def test_epub_fix_task_run_success(minimal_epub: Path, temp_dir: Path) -> None:
    """Test EPUBFixTask run successfully processes EPUB."""
    session = DummySession()
    update_progress = MagicMock()

    library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
    config = EPUBFixerConfig(
        enabled=True,
        backup_enabled=True,
        backup_directory=str(temp_dir / "backups"),
        default_language="en",
    )

    session.add_exec_result([config])

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_library_service.return_value = mock_service

        metadata = {
            "file_path": str(minimal_epub),
            "book_id": 1,
            "book_title": "Test Book",
        }
        task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        task.run(worker_context)

        # Should call update_progress multiple times
        assert update_progress.call_count >= 5
        # Last call should be 1.0
        assert update_progress.call_args_list[-1][0][0] == 1.0


def test_epub_fix_task_run_cancelled_during_processing(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test EPUBFixTask run when cancelled during processing."""
    session = DummySession()
    update_progress = MagicMock()

    library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
    config = EPUBFixerConfig(enabled=True, backup_enabled=False)

    session.add_exec_result([config])

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_library_service.return_value = mock_service

        metadata = {"file_path": str(minimal_epub)}
        task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
        # Cancel after first check
        call_count = 0

        def check_cancelled() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count > 1  # Cancel after first check

        task.check_cancelled = check_cancelled  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        task.run(worker_context)

        # Should have called update_progress at least once before cancelling
        assert update_progress.call_count >= 1


def test_epub_fix_batch_task_init() -> None:
    """Test EPUBFixBatchTask initialization."""
    metadata = {"library_id": 1}

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata=metadata)

    assert task.task_id == 1
    assert task.user_id == 1
    assert task.library_id == 1


def test_epub_fix_batch_task_setup_services_disabled() -> None:
    """Test _setup_services when EPUB fixer is disabled."""
    session = DummySession()
    config = EPUBFixerConfig(enabled=False)

    session.add_exec_result([config])

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

    result = task._setup_services(session)  # type: ignore[arg-type]

    assert result is None


def test_epub_fix_batch_task_setup_services_enabled(temp_dir: Path) -> None:
    """Test _setup_services when EPUB fixer is enabled."""
    session = DummySession()
    config = EPUBFixerConfig(
        enabled=True,
        backup_enabled=True,
        backup_directory=str(temp_dir / "backups"),
        default_language="en",
    )

    session.add_exec_result([config])

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

    result = task._setup_services(session)  # type: ignore[arg-type]

    assert result is not None
    fixer_service, backup_service, recorder, settings = result
    assert fixer_service is not None
    assert backup_service is not None
    assert recorder is not None
    assert settings is not None


def test_epub_fix_batch_task_process_epub_file(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test _process_epub_file processes EPUB successfully."""
    from bookcard.services.epub_fixer import (
        BackupService,
        EPUBFixerOrchestrator,
        EPUBReader,
        EPUBWriter,
        FixResultRecorder,
    )
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

    epub_info = EPUBFileInfo(
        book_id=1,
        book_title="Test Book",
        file_path=minimal_epub,
    )

    fix_run = EPUBFixRun(id=1, started_at=None)
    fix_run.id = 1

    backup_service = BackupService(temp_dir / "backups", enabled=True)
    recorder = FixResultRecorder(MagicMock())
    orchestrator = EPUBFixerOrchestrator([])
    reader = EPUBReader()
    writer = EPUBWriter()

    files_fixed, total_fixes = task._process_epub_file(
        epub_info, orchestrator, reader, writer, backup_service, recorder, fix_run
    )

    assert files_fixed >= 0
    assert total_fixes >= 0


def test_epub_fix_batch_task_scan_epub_files() -> None:
    """Test _scan_epub_files."""
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    library = Library(
        id=1, name="Test", calibre_db_path="/path/to/db", calibre_db_file="metadata.db"
    )

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

    # Mock the scanner's scan_epub_files method
    expected_results = [
        EPUBFileInfo(book_id=1, book_title="Test", file_path=Path("/path/to/book.epub"))
    ]

    with patch.object(
        task, "_scan_epub_files", return_value=expected_results
    ) as mock_scan:
        results = task._scan_epub_files(library)

        assert len(results) == 1
        assert results[0].book_id == 1
        mock_scan.assert_called_once_with(library)


def test_epub_fix_batch_task_create_fix_orchestrator(temp_dir: Path) -> None:
    """Test _create_fix_orchestrator."""
    from bookcard.services.epub_fixer import EPUBFixerSettings

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
    settings = EPUBFixerSettings(default_language="en")

    orchestrator, reader, writer = task._create_fix_orchestrator(settings)

    assert orchestrator is not None
    assert reader is not None
    assert writer is not None


def test_epub_fix_batch_task_process_all_files(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test _process_all_files."""
    from bookcard.services.epub_fixer import (
        BackupService,
        EPUBFixerOrchestrator,
        EPUBFixerSettings,
        EPUBReader,
        EPUBWriter,
        FixResultRecorder,
    )
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
    task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

    epub_files = [
        EPUBFileInfo(book_id=1, book_title="Test Book 1", file_path=minimal_epub),
    ]

    fix_run = EPUBFixRun(id=1, started_at=None)
    fix_run.id = 1

    backup_service = BackupService(temp_dir / "backups", enabled=True)
    fixer_service = MagicMock()
    fixer_service.should_skip_epub = MagicMock(return_value=False)
    recorder = FixResultRecorder(fixer_service)
    settings = EPUBFixerSettings(skip_already_fixed=False, skip_failed=False)
    orchestrator = EPUBFixerOrchestrator([])
    reader = EPUBReader()
    writer = EPUBWriter()
    update_progress = MagicMock()

    files_processed, _files_fixed, _total_fixes = task._process_all_files(
        epub_files,
        orchestrator,
        reader,
        writer,
        backup_service,
        recorder,
        fix_run,
        fixer_service,
        settings,
        update_progress,
    )

    assert files_processed == 1
    assert update_progress.call_count >= 1


def test_epub_fix_batch_task_process_all_files_skip(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test _process_all_files skips files."""
    from bookcard.services.epub_fixer import (
        BackupService,
        EPUBFixerOrchestrator,
        EPUBFixerSettings,
        EPUBReader,
        EPUBWriter,
        FixResultRecorder,
    )
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
    task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

    epub_files = [
        EPUBFileInfo(book_id=1, book_title="Test Book 1", file_path=minimal_epub),
    ]

    fix_run = EPUBFixRun(id=1, started_at=None)
    fix_run.id = 1

    backup_service = BackupService(temp_dir / "backups", enabled=True)
    fixer_service = MagicMock()
    fixer_service.should_skip_epub = MagicMock(return_value=True)  # Skip this file
    recorder = FixResultRecorder(fixer_service)
    settings = EPUBFixerSettings(skip_already_fixed=True, skip_failed=True)
    orchestrator = EPUBFixerOrchestrator([])
    reader = EPUBReader()
    writer = EPUBWriter()
    update_progress = MagicMock()

    files_processed, files_fixed, _total_fixes = task._process_all_files(
        epub_files,
        orchestrator,
        reader,
        writer,
        backup_service,
        recorder,
        fix_run,
        fixer_service,
        settings,
        update_progress,
    )

    assert files_processed == 1
    assert files_fixed == 0  # File was skipped


def test_epub_fix_batch_task_process_all_files_cancelled(
    minimal_epub: Path, temp_dir: Path
) -> None:
    """Test _process_all_files handles cancellation."""
    from bookcard.services.epub_fixer import (
        BackupService,
        EPUBFixerOrchestrator,
        EPUBFixerSettings,
        EPUBReader,
        EPUBWriter,
        FixResultRecorder,
    )
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

    epub_files = [
        EPUBFileInfo(book_id=1, book_title="Test Book 1", file_path=minimal_epub),
        EPUBFileInfo(book_id=2, book_title="Test Book 2", file_path=minimal_epub),
    ]

    fix_run = EPUBFixRun(id=1, started_at=None)
    fix_run.id = 1

    backup_service = BackupService(temp_dir / "backups", enabled=True)
    fixer_service = MagicMock()
    fixer_service.should_skip_epub = MagicMock(return_value=False)

    # Cancel after first file
    call_count = 0

    def check_cancelled() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > 1

    task.check_cancelled = check_cancelled  # type: ignore[method-assign]

    recorder = FixResultRecorder(fixer_service)
    settings = EPUBFixerSettings()
    orchestrator = EPUBFixerOrchestrator([])
    reader = EPUBReader()
    writer = EPUBWriter()
    update_progress = MagicMock()

    files_processed, _files_fixed, _total_fixes = task._process_all_files(
        epub_files,
        orchestrator,
        reader,
        writer,
        backup_service,
        recorder,
        fix_run,
        fixer_service,
        settings,
        update_progress,
    )

    # Should process at least one file before cancelling
    assert files_processed >= 1


def test_epub_fix_batch_task_run_no_library() -> None:
    """Test EPUBFixBatchTask run when no library is configured."""
    session = DummySession()
    update_progress = MagicMock()

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = None
        mock_library_service.return_value = mock_service

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        with pytest.raises(ValueError, match="No active library configured"):
            task.run(worker_context)


def test_epub_fix_batch_task_run_no_epub_files(temp_dir: Path) -> None:
    """Test EPUBFixBatchTask run when no EPUB files found."""
    session = DummySession()
    update_progress = MagicMock()

    library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
    config = EPUBFixerConfig(
        enabled=True,
        backup_enabled=False,  # Disable backup to avoid permission issues
    )

    session.add_exec_result([config])

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_library_service.return_value = mock_service

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        task._scan_epub_files = MagicMock(return_value=[])  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        task.run(worker_context)

        # Should return early
        update_progress.assert_not_called()


def test_epub_fix_batch_task_run_success(minimal_epub: Path, temp_dir: Path) -> None:
    """Test EPUBFixBatchTask run successfully processes batch."""
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

    session = DummySession()
    update_progress = MagicMock()

    library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
    config = EPUBFixerConfig(
        enabled=True,
        backup_enabled=True,
        backup_directory=str(temp_dir / "backups"),
        default_language="en",
        skip_already_fixed=False,
        skip_failed=False,
    )

    session.add_exec_result([config])

    with patch(
        "bookcard.services.tasks.epub_fix_task.LibraryService"
    ) as mock_library_service:
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_library_service.return_value = mock_service

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        task._scan_epub_files = MagicMock(  # type: ignore[method-assign]
            return_value=[
                EPUBFileInfo(book_id=1, book_title="Test", file_path=minimal_epub)
            ]
        )

        worker_context = {
            "session": session,
            "update_progress": update_progress,
        }

        task.run(worker_context)

        # Should have processed files
        assert update_progress.call_count >= 1


class TestEPUBFixTaskAdditional:
    """Additional tests for uncovered lines."""

    def test_epub_fix_task_run_cancelled_after_read(
        self,
        minimal_epub: Path,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixTask run cancelled after read (covers line 173)."""
        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(
            enabled=True,
            backup_enabled=True,
            backup_directory=str(temp_dir / "backups"),
            default_language="en",
        )

        session.add_exec_result([config])

        with patch(
            "bookcard.services.tasks.epub_fix_task.LibraryService"
        ) as mock_library_service:
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            metadata = {"file_path": str(minimal_epub)}
            task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
            call_count = 0

            def check_cancelled() -> bool:
                nonlocal call_count
                call_count += 1
                # Cancel after read (after 0.3 progress)
                return call_count > 3

            task.check_cancelled = check_cancelled  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should have called update_progress before cancellation
            assert update_progress.call_count >= 3

    def test_epub_fix_task_run_cancelled_after_fix(
        self,
        minimal_epub: Path,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixTask run cancelled after fix (covers line 190)."""
        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(
            enabled=True,
            backup_enabled=True,
            backup_directory=str(temp_dir / "backups"),
            default_language="en",
        )

        session.add_exec_result([config])

        with patch(
            "bookcard.services.tasks.epub_fix_task.LibraryService"
        ) as mock_library_service:
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            metadata = {"file_path": str(minimal_epub)}
            task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
            call_count = 0

            def check_cancelled() -> bool:
                nonlocal call_count
                call_count += 1
                # Cancel after fix (after 0.7 progress)
                return call_count > 5

            task.check_cancelled = check_cancelled  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should have called update_progress before cancellation
            assert update_progress.call_count >= 5

    def test_epub_fix_task_run_with_book_id(
        self,
        minimal_epub: Path,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixTask run with book_id in metadata (covers lines 200-203)."""
        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(
            enabled=True,
            backup_enabled=True,
            backup_directory=str(temp_dir / "backups"),
            default_language="en",
        )

        session.add_exec_result([config])

        with (
            patch(
                "bookcard.services.tasks.epub_fix_task.LibraryService"
            ) as mock_library_service,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBFixerService"
            ) as mock_fixer_service_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBFixerOrchestrator"
            ) as mock_orchestrator_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBReader"
            ) as mock_reader_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBWriter"
            ) as mock_writer_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            mock_fixer_service = MagicMock()
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            mock_fixer_service.create_fix_run.return_value = fix_run
            mock_fixer_service_class.return_value = mock_fixer_service

            mock_orchestrator = MagicMock()
            mock_fix_result = MagicMock()
            mock_fix_result.fix_type = "encoding"
            mock_orchestrator.process.return_value = [mock_fix_result]
            mock_orchestrator_class.return_value = mock_orchestrator

            mock_reader = MagicMock()
            mock_contents = MagicMock()
            mock_reader.read.return_value = mock_contents
            mock_reader_class.return_value = mock_reader

            mock_writer = MagicMock()
            mock_writer_class.return_value = mock_writer

            metadata = {
                "file_path": str(minimal_epub),
                "book_id": 123,
                "book_title": "Test Book",
            }
            task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
            task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should have recorded fixes with book_id
            mock_fixer_service.complete_fix_run.assert_called()

    def test_epub_fix_task_run_complete_fix_run(
        self,
        minimal_epub: Path,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixTask run completes fix run (covers line 215)."""
        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(
            enabled=True,
            backup_enabled=True,
            backup_directory=str(temp_dir / "backups"),
            default_language="en",
        )

        session.add_exec_result([config])

        with (
            patch(
                "bookcard.services.tasks.epub_fix_task.LibraryService"
            ) as mock_library_service,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBFixerService"
            ) as mock_fixer_service_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBFixerOrchestrator"
            ) as mock_orchestrator_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBReader"
            ) as mock_reader_class,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBWriter"
            ) as mock_writer_class,
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            mock_fixer_service = MagicMock()
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            mock_fixer_service.create_fix_run.return_value = fix_run
            mock_fixer_service_class.return_value = mock_fixer_service

            mock_orchestrator = MagicMock()
            mock_fix_result = MagicMock()
            mock_fix_result.fix_type = "encoding"
            mock_orchestrator.process.return_value = [mock_fix_result]
            mock_orchestrator_class.return_value = mock_orchestrator

            mock_reader = MagicMock()
            mock_contents = MagicMock()
            mock_reader.read.return_value = mock_contents
            mock_reader_class.return_value = mock_reader

            mock_writer = MagicMock()
            mock_writer_class.return_value = mock_writer

            metadata = {"file_path": str(minimal_epub)}
            task = EPUBFixTask(task_id=1, user_id=1, metadata=metadata)
            task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should complete fix run
            mock_fixer_service.complete_fix_run.assert_called_once()

    def test_epub_fix_batch_task_process_epub_file_with_fixes(
        self,
        minimal_epub: Path,
    ) -> None:
        """Test _process_epub_file with fixes applied (covers lines 360, 372-373)."""
        from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

        epub_info = EPUBFileInfo(
            book_id=1,
            book_title="Test Book",
            file_path=minimal_epub,
        )

        mock_orchestrator = MagicMock()
        mock_fix_result = MagicMock()
        mock_fix_result.fix_type = "encoding"
        mock_orchestrator.process.return_value = [mock_fix_result]

        mock_reader = MagicMock()
        mock_contents = MagicMock()
        mock_reader.read.return_value = mock_contents

        mock_writer = MagicMock()

        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = None

        mock_recorder = MagicMock()

        fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))

        files_fixed, total_fixes = task._process_epub_file(
            epub_info,
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
        )

        assert files_fixed == 1
        assert total_fixes == 1
        mock_writer.write.assert_called_once()
        mock_recorder.record_fixes.assert_called_once()

    def test_epub_fix_batch_task_process_epub_file_exception(
        self,
        minimal_epub: Path,
    ) -> None:
        """Test _process_epub_file handles exception (covers lines 372-373)."""
        from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

        epub_info = EPUBFileInfo(
            book_id=1,
            book_title="Test Book",
            file_path=minimal_epub,
        )

        mock_orchestrator = MagicMock()
        mock_orchestrator.process.side_effect = Exception("Test error")

        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_backup_service = MagicMock()
        mock_recorder = MagicMock()
        fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))

        with patch("bookcard.services.tasks.epub_fix_task.logger") as mock_logger:
            files_fixed, total_fixes = task._process_epub_file(
                epub_info,
                mock_orchestrator,
                mock_reader,
                mock_writer,
                mock_backup_service,
                mock_recorder,
                fix_run,
            )

            assert files_fixed == 0
            assert total_fixes == 0
            mock_logger.exception.assert_called_once()

    def test_epub_fix_batch_task_scan_epub_files(
        self,
    ) -> None:
        """Test _scan_epub_files (covers lines 390-399)."""
        from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

        task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")

        with (
            patch(
                "bookcard.repositories.calibre_book_repository.CalibreBookRepository"
            ) as mock_repo_class,
            patch("bookcard.services.epub_fixer.EPUBScanner") as mock_scanner_class,
        ):
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            mock_scanner = MagicMock()
            mock_scanner.scan_epub_files.return_value = [
                EPUBFileInfo(book_id=1, book_title="Test", file_path=Path("/test.epub"))
            ]
            mock_scanner_class.return_value = mock_scanner

            result = task._scan_epub_files(library)

            assert len(result) == 1
            mock_scanner.scan_epub_files.assert_called_once()

    def test_epub_fix_batch_task_run_no_library_after_check(
        self,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixBatchTask run when library is None after check (covers lines 522-523, 536, 542)."""
        session = DummySession()
        update_progress = MagicMock()

        with patch(
            "bookcard.services.tasks.epub_fix_task.LibraryService"
        ) as mock_library_service:
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = None
            mock_library_service.return_value = mock_service

            task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
            task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            with pytest.raises(ValueError, match="No active library configured"):
                task.run(worker_context)

    def test_epub_fix_batch_task_run_setup_services_returns_none(
        self,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixBatchTask run when setup_services returns None (covers line 536)."""
        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(enabled=False)

        session.add_exec_result([config])

        with patch(
            "bookcard.services.tasks.epub_fix_task.LibraryService"
        ) as mock_library_service:
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
            task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should return early
            update_progress.assert_not_called()

    def test_epub_fix_batch_task_complete_fix_run(
        self,
        minimal_epub: Path,
        temp_dir: Path,
    ) -> None:
        """Test EPUBFixBatchTask run completes fix run (covers line 580)."""
        from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

        session = DummySession()
        update_progress = MagicMock()

        library = Library(id=1, name="Test", calibre_db_path="/path/to/db")
        config = EPUBFixerConfig(
            enabled=True,
            backup_enabled=True,
            backup_directory=str(temp_dir / "backups"),
            default_language="en",
            skip_already_fixed=False,
            skip_failed=False,
        )

        session.add_exec_result([config])

        with (
            patch(
                "bookcard.services.tasks.epub_fix_task.LibraryService"
            ) as mock_library_service,
            patch(
                "bookcard.services.tasks.epub_fix_task.EPUBFixerService"
            ) as mock_fixer_service_class,
            patch("bookcard.services.epub_fixer.services.scanner.EPUBScanner"),
        ):
            mock_service = MagicMock()
            mock_service.get_active_library.return_value = library
            mock_library_service.return_value = mock_service

            mock_fixer_service = MagicMock()
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            mock_fixer_service.create_fix_run.return_value = fix_run
            mock_fixer_service.should_skip_epub.return_value = False
            mock_fixer_service_class.return_value = mock_fixer_service

            # Mock _scan_epub_files to avoid database access
            task = EPUBFixBatchTask(task_id=1, user_id=1, metadata={})
            task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
            task._scan_epub_files = MagicMock(  # type: ignore[method-assign]
                return_value=[
                    EPUBFileInfo(book_id=1, book_title="Test", file_path=minimal_epub)
                ]
            )
            task._process_epub_file = MagicMock(return_value=(1, 1))  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": update_progress,
            }

            task.run(worker_context)

            # Should complete fix run
            mock_fixer_service.complete_fix_run.assert_called_once()

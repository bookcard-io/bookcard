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

"""Tests for epub_fix_daily_scan_task to achieve 100% coverage."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from bookcard.models.epub_fixer import EPUBFixRun
from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo
from bookcard.services.tasks.epub_fix_daily_scan_task import EPUBFixDailyScanTask
from bookcard.services.tasks.exceptions import LibraryNotConfiguredError
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
def scheduled_tasks_config() -> ScheduledTasksConfig:
    """Create scheduled tasks config for testing.

    Returns
    -------
    ScheduledTasksConfig
        Scheduled tasks config instance.
    """
    return ScheduledTasksConfig(id=1, epub_fixer_daily_scan=True, library_id=1)


@pytest.fixture
def epub_fixer_config(tmp_path: Path) -> EPUBFixerConfig:
    """Create EPUB fixer config for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    EPUBFixerConfig
        EPUB fixer config instance.
    """
    return EPUBFixerConfig(
        id=1,
        enabled=True,
        library_id=1,
        backup_enabled=True,
        backup_directory=str(tmp_path / "backups"),
        default_language="en",
    )


@pytest.fixture
def epub_file_info(tmp_path: Path) -> EPUBFileInfo:
    """Create EPUB file info for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    EPUBFileInfo
        EPUB file info instance.
    """
    file_path = tmp_path / "book.epub"
    file_path.touch()
    return EPUBFileInfo(
        book_id=1,
        book_title="Test Book",
        file_path=file_path,
    )


@pytest.fixture
def fix_run() -> EPUBFixRun:
    """Create fix run for testing.

    Returns
    -------
    EPUBFixRun
        Fix run instance.
    """
    return EPUBFixRun(id=1, user_id=1, library_id=1)


# ============================================================================
# Tests for EPUBFixDailyScanTask
# ============================================================================


class TestEPUBFixDailyScanTaskInit:
    """Test EPUBFixDailyScanTask initialization."""

    def test_init_with_library_id(self) -> None:
        """Test initialization with library_id in metadata.

        Parameters
        ----------
        None
        """
        metadata = {"library_id": 1}
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata=metadata)
        assert task.task_id == 1
        assert task.user_id == 1
        assert task.library_id == 1

    def test_init_without_library_id(self) -> None:
        """Test initialization without library_id in metadata.

        Parameters
        ----------
        None
        """
        metadata = {}
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata=metadata)
        assert task.task_id == 1
        assert task.user_id == 1
        assert task.library_id is None


class TestEPUBFixDailyScanTaskCheckDailyScanEnabled:
    """Test _check_daily_scan_enabled method."""

    @pytest.mark.parametrize(
        ("config", "expected"),
        [
            (None, False),
            (
                ScheduledTasksConfig(id=1, epub_fixer_daily_scan=False, library_id=1),
                False,
            ),
            (
                ScheduledTasksConfig(id=1, epub_fixer_daily_scan=True, library_id=1),
                True,
            ),
        ],
    )
    def test_check_daily_scan_enabled(
        self,
        session: DummySession,
        config: ScheduledTasksConfig | None,
        expected: bool,
    ) -> None:
        """Test _check_daily_scan_enabled with various configs.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        config : ScheduledTasksConfig | None
            Scheduled tasks config or None.
        expected : bool
            Expected result.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        session.add_exec_result([config])
        result = task._check_daily_scan_enabled(session)  # type: ignore[arg-type]
        assert result == expected


class TestEPUBFixDailyScanTaskSetupServices:
    """Test _setup_services method."""

    def test_setup_services_daily_scan_disabled(self, session: DummySession) -> None:
        """Test _setup_services when daily scan is disabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        session.add_exec_result([None])  # No scheduled config
        result = task._setup_services(session)  # type: ignore[arg-type]
        assert result is None

    def test_setup_services_epub_fixer_disabled(
        self,
        session: DummySession,
        scheduled_tasks_config: ScheduledTasksConfig,
    ) -> None:
        """Test _setup_services when EPUB fixer is disabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([None])  # No EPUB config
        result = task._setup_services(session)  # type: ignore[arg-type]
        assert result is None

    def test_setup_services_epub_fixer_enabled_false(
        self,
        session: DummySession,
        scheduled_tasks_config: ScheduledTasksConfig,
    ) -> None:
        """Test _setup_services when EPUB fixer enabled is False.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        epub_config = EPUBFixerConfig(id=1, enabled=False, library_id=1)
        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_config])
        result = task._setup_services(session)  # type: ignore[arg-type]
        assert result is None

    def test_setup_services_success_with_backup(
        self,
        session: DummySession,
        scheduled_tasks_config: ScheduledTasksConfig,
        epub_fixer_config: EPUBFixerConfig,
        tmp_path: Path,
    ) -> None:
        """Test _setup_services when all conditions are met with backup.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        epub_fixer_config : EPUBFixerConfig
            EPUB fixer config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_fixer_config])
        result = task._setup_services(session)  # type: ignore[arg-type]
        assert result is not None
        fixer_service, backup_service, recorder, settings = result
        assert fixer_service is not None
        assert backup_service is not None
        assert recorder is not None
        assert settings is not None

    def test_setup_services_success_without_backup(
        self,
        session: DummySession,
        scheduled_tasks_config: ScheduledTasksConfig,
        tmp_path: Path,
    ) -> None:
        """Test _setup_services when backup is disabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        epub_config = EPUBFixerConfig(
            id=1,
            enabled=True,
            library_id=1,
            backup_enabled=False,
            backup_directory=str(tmp_path / "backups"),
            default_language="en",
        )
        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_config])
        result = task._setup_services(session)  # type: ignore[arg-type]
        assert result is not None
        fixer_service, backup_service, recorder, settings = result
        assert fixer_service is not None
        assert backup_service is not None
        assert recorder is not None
        assert settings is not None


class TestEPUBFixDailyScanTaskScanEPUBFiles:
    """Test _scan_epub_files method."""

    def test_scan_epub_files(
        self, library: Library, epub_file_info: EPUBFileInfo
    ) -> None:
        """Test _scan_epub_files scans library.

        Parameters
        ----------
        library : Library
            Library instance.
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})

        with (
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.CalibreBookRepository"
            ) as mock_repo_class,
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.EPUBScanner"
            ) as mock_scanner_class,
        ):
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_scanner = MagicMock()
            mock_scanner.scan_epub_files.return_value = [epub_file_info]
            mock_scanner_class.return_value = mock_scanner

            result = task._scan_epub_files(library)
            assert result == [epub_file_info]
            mock_scanner.scan_epub_files.assert_called_once()
            mock_repo_class.assert_called_once_with(
                library.calibre_db_path, library.calibre_db_file
            )


class TestEPUBFixDailyScanTaskProcessEPUBFile:
    """Test _process_epub_file method."""

    def test_process_epub_file_success(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
        tmp_path: Path,
    ) -> None:
        """Test _process_epub_file successfully processes file.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})

        mock_orchestrator = MagicMock()
        mock_fix_result = MagicMock()
        mock_orchestrator.process.return_value = [mock_fix_result]

        mock_reader = MagicMock()
        mock_contents = MagicMock()
        mock_reader.read.return_value = mock_contents

        mock_writer = MagicMock()

        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = tmp_path / "backup.epub"

        mock_recorder = MagicMock()

        fix_run.id = 1

        files_fixed, total_fixes = task._process_epub_file(
            epub_file_info,
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
        )

        assert files_fixed == 1
        assert total_fixes == 1
        mock_writer.write.assert_called_once_with(
            mock_contents, epub_file_info.file_path
        )
        mock_recorder.record_fixes.assert_called_once()

    def test_process_epub_file_no_fixes(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
        tmp_path: Path,
    ) -> None:
        """Test _process_epub_file when no fixes are needed.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})

        mock_orchestrator = MagicMock()
        mock_orchestrator.process.return_value = []  # No fixes

        mock_reader = MagicMock()
        mock_contents = MagicMock()
        mock_reader.read.return_value = mock_contents

        mock_writer = MagicMock()

        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = tmp_path / "backup.epub"

        mock_recorder = MagicMock()

        fix_run.id = 1

        files_fixed, total_fixes = task._process_epub_file(
            epub_file_info,
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
        )

        assert files_fixed == 0
        assert total_fixes == 0
        mock_writer.write.assert_not_called()
        mock_recorder.record_fixes.assert_not_called()

    def test_process_epub_file_exception(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
        tmp_path: Path,
    ) -> None:
        """Test _process_epub_file handles exceptions.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})

        mock_orchestrator = MagicMock()
        mock_reader = MagicMock()
        mock_reader.read.side_effect = Exception("Read error")

        mock_writer = MagicMock()
        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = tmp_path / "backup.epub"
        mock_recorder = MagicMock()

        files_fixed, total_fixes = task._process_epub_file(
            epub_file_info,
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
        )

        assert files_fixed == 0
        assert total_fixes == 0

    def test_process_epub_file_no_fix_run_id(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
        tmp_path: Path,
    ) -> None:
        """Test _process_epub_file when fix_run.id is None.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})

        mock_orchestrator = MagicMock()
        mock_fix_result = MagicMock()
        mock_orchestrator.process.return_value = [mock_fix_result]

        mock_reader = MagicMock()
        mock_contents = MagicMock()
        mock_reader.read.return_value = mock_contents

        mock_writer = MagicMock()

        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = tmp_path / "backup.epub"

        mock_recorder = MagicMock()

        fix_run.id = None

        files_fixed, total_fixes = task._process_epub_file(
            epub_file_info,
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
        )

        assert files_fixed == 1
        assert total_fixes == 1
        mock_recorder.record_fixes.assert_not_called()


class TestEPUBFixDailyScanTaskProcessAllFiles:
    """Test _process_all_files method."""

    def test_process_all_files_success(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
        tmp_path: Path,
    ) -> None:
        """Test _process_all_files successfully processes all files.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        mock_orchestrator = MagicMock()
        mock_fix_result = MagicMock()
        mock_orchestrator.process.return_value = [mock_fix_result]

        mock_reader = MagicMock()
        mock_contents = MagicMock()
        mock_reader.read.return_value = mock_contents

        mock_writer = MagicMock()

        mock_backup_service = MagicMock()
        mock_backup_service.create_backup.return_value = tmp_path / "backup.epub"

        mock_recorder = MagicMock()
        fix_run.id = 1

        mock_fixer_service = MagicMock()
        mock_fixer_service.should_skip_epub.return_value = False

        mock_settings = MagicMock()
        mock_settings.skip_already_fixed = False
        mock_settings.skip_failed = False

        update_progress = MagicMock()

        files_processed, files_fixed, total_fixes = task._process_all_files(
            [epub_file_info],
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
            mock_fixer_service,
            mock_settings,
            update_progress,
        )

        assert files_processed == 1
        assert files_fixed == 1
        assert total_fixes == 1
        assert update_progress.call_count == 1

    def test_process_all_files_skipped(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
    ) -> None:
        """Test _process_all_files when file is skipped.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        mock_orchestrator = MagicMock()
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_backup_service = MagicMock()
        mock_recorder = MagicMock()

        mock_fixer_service = MagicMock()
        mock_fixer_service.should_skip_epub.return_value = True

        mock_settings = MagicMock()
        mock_settings.skip_already_fixed = True
        mock_settings.skip_failed = False

        update_progress = MagicMock()

        files_processed, files_fixed, total_fixes = task._process_all_files(
            [epub_file_info],
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
            mock_fixer_service,
            mock_settings,
            update_progress,
        )

        assert files_processed == 1
        assert files_fixed == 0
        assert total_fixes == 0

    def test_process_all_files_cancelled(
        self,
        epub_file_info: EPUBFileInfo,
        fix_run: EPUBFixRun,
    ) -> None:
        """Test _process_all_files when task is cancelled.

        Parameters
        ----------
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        fix_run : EPUBFixRun
            Fix run instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        mock_orchestrator = MagicMock()
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_backup_service = MagicMock()
        mock_recorder = MagicMock()

        mock_fixer_service = MagicMock()
        mock_fixer_service.should_skip_epub.return_value = False

        mock_settings = MagicMock()
        mock_settings.skip_already_fixed = False
        mock_settings.skip_failed = False

        update_progress = MagicMock()

        files_processed, files_fixed, total_fixes = task._process_all_files(
            [epub_file_info],
            mock_orchestrator,
            mock_reader,
            mock_writer,
            mock_backup_service,
            mock_recorder,
            fix_run,
            mock_fixer_service,
            mock_settings,
            update_progress,
        )

        assert files_processed == 0
        assert files_fixed == 0
        assert total_fixes == 0


class TestEPUBFixDailyScanTaskRun:
    """Test run method."""

    def test_run_cancelled_before_processing(self, session: DummySession) -> None:
        """Test run when cancelled before processing.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=True)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": MagicMock(),
        }

        task.run(worker_context)

    def test_run_setup_services_returns_none(self, session: DummySession) -> None:
        """Test run when _setup_services returns None.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]
        task._setup_services = MagicMock(return_value=None)  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": MagicMock(),
        }

        task.run(worker_context)

    def test_run_no_library(
        self,
        session: DummySession,
        scheduled_tasks_config: ScheduledTasksConfig,
        epub_fixer_config: EPUBFixerConfig,
        tmp_path: Path,
    ) -> None:
        """Test run when no library is configured.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        epub_fixer_config : EPUBFixerConfig
            EPUB fixer config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_fixer_config])

        with patch(
            "bookcard.services.tasks.epub_fix_daily_scan_task.resolve_task_library",
            side_effect=LibraryNotConfiguredError(),
        ):
            worker_context = {
                "session": session,
                "update_progress": MagicMock(),
            }

            with pytest.raises(LibraryNotConfiguredError):
                task.run(worker_context)

    def test_run_no_epub_files(
        self,
        session: DummySession,
        library: Library,
        scheduled_tasks_config: ScheduledTasksConfig,
        epub_fixer_config: EPUBFixerConfig,
        tmp_path: Path,
    ) -> None:
        """Test run when no EPUB files are found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        epub_fixer_config : EPUBFixerConfig
            EPUB fixer config.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_fixer_config])

        with patch(
            "bookcard.services.tasks.epub_fix_daily_scan_task.resolve_task_library",
            return_value=library,
        ):
            task._scan_epub_files = MagicMock(return_value=[])  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": MagicMock(),
            }

            task.run(worker_context)

    def test_run_success(
        self,
        session: DummySession,
        library: Library,
        epub_file_info: EPUBFileInfo,
        scheduled_tasks_config: ScheduledTasksConfig,
        epub_fixer_config: EPUBFixerConfig,
        tmp_path: Path,
    ) -> None:
        """Test run successfully processes EPUB files.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        epub_fixer_config : EPUBFixerConfig
            EPUB fixer config.
        tmp_path : Path
            Temporary directory path.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_fixer_config])

        with (
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.resolve_task_library",
                return_value=library,
            ),
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.EPUBFixerService"
            ) as mock_fixer_service_class,
        ):
            mock_fixer_service = MagicMock()
            mock_fix_run = EPUBFixRun(id=1, user_id=1, library_id=1)
            mock_fixer_service.create_fix_run.return_value = mock_fix_run
            mock_fixer_service.should_skip_epub.return_value = False
            mock_fixer_service_class.return_value = mock_fixer_service

            task._scan_epub_files = MagicMock(return_value=[epub_file_info])  # type: ignore[method-assign]
            task._process_all_files = MagicMock(  # type: ignore[method-assign]
                return_value=(1, 1, 1)
            )

            worker_context = {
                "session": session,
                "update_progress": MagicMock(),
            }

            task.run(worker_context)

            mock_fixer_service.complete_fix_run.assert_called_once()

    def test_run_uses_library_id_from_metadata(
        self,
        session: DummySession,
        library: Library,
        epub_file_info: EPUBFileInfo,
        scheduled_tasks_config: ScheduledTasksConfig,
        epub_fixer_config: EPUBFixerConfig,
        tmp_path: Path,
    ) -> None:
        """Test that library_id from metadata is forwarded to the resolver.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        epub_file_info : EPUBFileInfo
            EPUB file info instance.
        scheduled_tasks_config : ScheduledTasksConfig
            Scheduled tasks config.
        epub_fixer_config : EPUBFixerConfig
            EPUB fixer config.
        tmp_path : Path
            Temporary directory path.
        """
        metadata = {"library_id": 42}
        task = EPUBFixDailyScanTask(task_id=1, user_id=7, metadata=metadata)
        task.check_cancelled = MagicMock(return_value=False)  # type: ignore[method-assign]

        session.add_exec_result([scheduled_tasks_config])
        session.add_exec_result([epub_fixer_config])

        with (
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.resolve_task_library",
                return_value=library,
            ) as mock_resolve,
            patch(
                "bookcard.services.tasks.epub_fix_daily_scan_task.EPUBFixerService"
            ) as mock_fixer_service_class,
        ):
            mock_fixer_service = MagicMock()
            mock_fix_run = EPUBFixRun(id=1, user_id=7, library_id=42)
            mock_fixer_service.create_fix_run.return_value = mock_fix_run
            mock_fixer_service_class.return_value = mock_fixer_service

            task._scan_epub_files = MagicMock(return_value=[epub_file_info])  # type: ignore[method-assign]
            task._process_all_files = MagicMock(return_value=(1, 1, 1))  # type: ignore[method-assign]

            worker_context = {
                "session": session,
                "update_progress": MagicMock(),
            }

            task.run(worker_context)

            mock_resolve.assert_called_once_with(session, metadata, 7)

    def test_run_exception(
        self,
        session: DummySession,
    ) -> None:
        """Test run handles exceptions.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        task = EPUBFixDailyScanTask(task_id=1, user_id=1, metadata={})
        task.check_cancelled = MagicMock(side_effect=Exception("Test error"))  # type: ignore[method-assign]

        worker_context = {
            "session": session,
            "update_progress": MagicMock(),
        }

        with pytest.raises(Exception, match="Test error"):
            task.run(worker_context)

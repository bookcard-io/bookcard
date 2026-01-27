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

"""EPUB fix daily scan task implementation.

Handles scheduled daily scanning and fixing of EPUB files in the library.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

if TYPE_CHECKING:
    from bookcard.models.config import Library
    from bookcard.models.epub_fixer import EPUBFixRun
    from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo

from bookcard.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from bookcard.models.epub_fixer import EPUBFixRun
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.epub_fixer import (
    BackupService,
    EPUBFixerOrchestrator,
    EPUBFixerSettings,
    EPUBReader,
    EPUBWriter,
    FixResultRecorder,
    LanguageFix,
    NullBackupService,
)
from bookcard.services.epub_fixer.core.fixes import (
    BodyIdLinkFix,
    EncodingFix,
    StrayImageFix,
)
from bookcard.services.epub_fixer.services.scanner import EPUBFileInfo, EPUBScanner
from bookcard.services.epub_fixer_service import EPUBFixerService
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


def _raise_no_library_error() -> None:
    """Raise error for missing active library."""
    msg = "No active library configured"
    raise ValueError(msg)


class EPUBFixDailyScanTask(BaseTask):
    """Task for daily scheduled EPUB fixing.

    Scans library and fixes problematic EPUB files based on scheduled tasks config.
    Only runs if epub_fixer_daily_scan is enabled in ScheduledTasksConfig.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize EPUB fix daily scan task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task (typically system user).
        metadata : dict[str, Any]
            Task metadata (may be empty for scheduled tasks).
        """
        super().__init__(task_id, user_id, metadata)
        self.library_id = metadata.get("library_id")

    def _check_daily_scan_enabled(self, session: Session) -> bool:
        """Check if daily scan is enabled in configuration.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        bool
            True if daily scan is enabled, False otherwise.
        """
        stmt = select(ScheduledTasksConfig).limit(1)
        scheduled_config = session.exec(stmt).first()
        if scheduled_config is None:
            return False
        return scheduled_config.epub_fixer_daily_scan

    def _setup_services(
        self, session: Session
    ) -> (
        tuple[
            EPUBFixerService,
            BackupService | NullBackupService,
            FixResultRecorder,
            EPUBFixerSettings,
        ]
        | None
    ):
        """Set up services for daily scan processing.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        tuple[EPUBFixerService, BackupService | NullBackupService, FixResultRecorder, EPUBFixerSettings] | None
            Tuple of services, or None if disabled.
        """
        # Check if daily scan is enabled
        if not self._check_daily_scan_enabled(session):
            logger.info("EPUB fixer daily scan is disabled, skipping")
            return None

        # Get EPUB fixer configuration
        stmt = select(EPUBFixerConfig).limit(1)
        epub_config = session.exec(stmt).first()
        if not epub_config or not epub_config.enabled:
            logger.info("EPUB fixer is disabled, skipping daily scan")
            return None

        settings = EPUBFixerSettings.from_config_model(epub_config)

        # Initialize services
        fixer_service = EPUBFixerService(session)
        backup_service: BackupService | NullBackupService = (
            BackupService(settings.backup_directory, settings.backup_enabled)
            if settings.backup_enabled
            else NullBackupService()
        )
        recorder = FixResultRecorder(fixer_service)

        return fixer_service, backup_service, recorder, settings

    def _scan_epub_files(self, library: Library) -> list[EPUBFileInfo]:
        """Scan library for EPUB files.

        Parameters
        ----------
        library : Library
            Library configuration.

        Returns
        -------
        list[EPUBFileInfo]
            List of EPUB file information.
        """
        calibre_repo = CalibreBookRepository(
            library.calibre_db_path, library.calibre_db_file
        )
        scanner = EPUBScanner(library, calibre_repo)
        return scanner.scan_epub_files()

    def _process_epub_file(
        self,
        epub_info: EPUBFileInfo,
        orchestrator: EPUBFixerOrchestrator,
        reader: EPUBReader,
        writer: EPUBWriter,
        backup_service: BackupService | NullBackupService,
        recorder: FixResultRecorder,
        fix_run: EPUBFixRun,
    ) -> tuple[int, int]:
        """Process a single EPUB file.

        Parameters
        ----------
        epub_info : EPUBFileInfo
            EPUB file information.
        orchestrator : EPUBFixerOrchestrator
            Fix orchestrator.
        reader : EPUBReader
            EPUB reader.
        writer : EPUBWriter
            EPUB writer.
        backup_service : BackupService | NullBackupService
            Backup service.
        recorder : FixResultRecorder
            Fix result recorder.
        fix_run : EPUBFixRun
            Fix run record.

        Returns
        -------
        tuple[int, int]
            Tuple of (files_fixed, total_fixes).
        """
        files_fixed = 0
        total_fixes = 0
        try:
            backup_path = backup_service.create_backup(epub_info.file_path)
            contents = reader.read(epub_info.file_path)
            fix_results = orchestrator.process(contents)
            if fix_results:
                writer.write(contents, epub_info.file_path)
                if fix_run.id is not None:
                    recorder.record_fixes(
                        run_id=fix_run.id,
                        book_id=epub_info.book_id,
                        book_title=epub_info.book_title,
                        file_path=str(epub_info.file_path),
                        fix_results=fix_results,
                        original_file_path=backup_path,
                        backup_created=backup_path is not None,
                    )
                files_fixed = 1
                total_fixes = len(fix_results)
        except Exception:
            logger.exception("Error fixing EPUB %s", epub_info.file_path)

        return files_fixed, total_fixes

    def _process_all_files(
        self,
        epub_files: list[EPUBFileInfo],
        orchestrator: EPUBFixerOrchestrator,
        reader: EPUBReader,
        writer: EPUBWriter,
        backup_service: BackupService | NullBackupService,
        recorder: FixResultRecorder,
        fix_run: EPUBFixRun,
        fixer_service: EPUBFixerService,
        settings: EPUBFixerSettings,
        update_progress: Callable[[float], None],
    ) -> tuple[int, int, int]:
        """Process all EPUB files in daily scan.

        Parameters
        ----------
        epub_files : list[EPUBFileInfo]
            List of EPUB files to process.
        orchestrator : EPUBFixerOrchestrator
            Fix orchestrator.
        reader : EPUBReader
            EPUB reader.
        writer : EPUBWriter
            EPUB writer.
        backup_service : BackupService | NullBackupService
            Backup service.
        recorder : FixResultRecorder
            Fix result recorder.
        fix_run : EPUBFixRun
            Fix run record.
        fixer_service : EPUBFixerService
            EPUB fixer service.
        settings : EPUBFixerSettings
            EPUB fixer settings.
        update_progress : Callable[[float], None]
            Progress update callback.

        Returns
        -------
        tuple[int, int, int]
            Tuple of (files_processed, files_fixed, total_fixes).
        """
        total_files = len(epub_files)
        files_processed = 0
        files_fixed = 0
        total_fixes = 0

        for epub_info in epub_files:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled during daily scan", self.task_id)
                break

            # Check if should skip
            if fixer_service.should_skip_epub(
                str(epub_info.file_path),
                skip_already_fixed=settings.skip_already_fixed,
                skip_failed=settings.skip_failed,
            ):
                files_processed += 1
                update_progress(
                    files_processed / total_files if total_files > 0 else 1.0
                )
                continue

            # Process file
            file_fixed, file_fixes = self._process_epub_file(
                epub_info,
                orchestrator,
                reader,
                writer,
                backup_service,
                recorder,
                fix_run,
            )
            files_fixed += file_fixed
            total_fixes += file_fixes
            files_processed += 1
            update_progress(files_processed / total_files if total_files > 0 else 1.0)

        return files_processed, files_fixed, total_fixes

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute EPUB fix daily scan task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress: Callable[[float], None] = worker_context["update_progress"]

        try:
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Check if daily scan is enabled and get services
            result = self._setup_services(session)
            if result is None:
                logger.info("Daily scan disabled or EPUB fixer disabled, skipping")
                return
            fixer_service, backup_service, recorder, settings = result

            # Get active library
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            library = library_service.get_active_library()

            if library is None:
                _raise_no_library_error()

            # Scan for EPUB files
            # Type narrowing: library is not None after check
            # Use type: ignore since we've already checked for None
            epub_files = self._scan_epub_files(library)  # type: ignore[arg-type]

            if not epub_files:
                logger.info("No EPUB files found in library for daily scan")
                return

            # Create fix run (not manually triggered, is bulk operation)
            library_id = self.library_id or (library.id if library else None)
            fix_run = fixer_service.create_fix_run(
                user_id=self.user_id,
                library_id=library_id,
                manually_triggered=False,  # Scheduled task, not manual
                is_bulk_operation=True,
                backup_enabled=settings.backup_enabled,
            )

            # Create orchestrator and I/O components
            fixes = [
                BodyIdLinkFix(),
                LanguageFix(default_language=settings.default_language),
                StrayImageFix(),
                EncodingFix(),
            ]
            orchestrator = EPUBFixerOrchestrator(fixes)
            reader = EPUBReader()
            writer = EPUBWriter()

            # Process all files
            files_processed, files_fixed, total_fixes = self._process_all_files(
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

            # Complete fix run
            if fix_run.id is not None:
                fixer_service.complete_fix_run(
                    run_id=fix_run.id,
                    total_files_processed=files_processed,
                    total_files_fixed=files_fixed,
                    total_fixes_applied=total_fixes,
                )

            logger.info(
                "Task %s: Daily scan completed - %d/%d files fixed, %d fixes applied",
                self.task_id,
                files_fixed,
                files_processed,
                total_fixes,
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

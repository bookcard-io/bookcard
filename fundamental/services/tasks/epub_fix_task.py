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

"""EPUB fix task implementations.

Handles single file and batch EPUB fixing with full audit trail.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

if TYPE_CHECKING:
    from fundamental.models.config import Library
    from fundamental.models.epub_fixer import EPUBFixRun
    from fundamental.services.epub_fixer.services.scanner import EPUBFileInfo

from fundamental.models.config import EPUBFixerConfig, Library
from fundamental.models.epub_fixer import EPUBFixRun
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.config_service import LibraryService
from fundamental.services.epub_fixer import (
    BackupService,
    EPUBFixerOrchestrator,
    EPUBFixerSettings,
    EPUBReader,
    EPUBWriter,
    FixResultRecorder,
    LanguageFix,
    NullBackupService,
)
from fundamental.services.epub_fixer.core.fixes import (
    BodyIdLinkFix,
    EncodingFix,
    StrayImageFix,
)
from fundamental.services.epub_fixer.services.scanner import EPUBFileInfo
from fundamental.services.epub_fixer_service import EPUBFixerService
from fundamental.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


def _raise_no_library_error() -> None:
    """Raise error for missing active library.

    Raises
    ------
    ValueError
        Always raises with message about missing library.
    """
    msg = "No active library configured"
    raise ValueError(msg)


class EPUBFixTask(BaseTask):
    """Task for fixing a single EPUB file.

    Handles EPUB fixing with progress tracking and audit trail.
    All dependencies injected via constructor (IOC).
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize EPUB fix task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing file_path, library_id, etc.
        """
        super().__init__(task_id, user_id, metadata)
        file_path_str = metadata.get("file_path", "")
        if not file_path_str:
            msg = "file_path is required in task metadata"
            raise ValueError(msg)
        self.file_path = Path(file_path_str)
        self.library_id = metadata.get("library_id")

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute EPUB fix task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Get library
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            library = library_service.get_active_library()

            if library is None:
                _raise_no_library_error()

            # Get EPUB fixer configuration
            stmt = select(EPUBFixerConfig).limit(1)
            epub_config = session.exec(stmt).first()
            if not epub_config or not epub_config.enabled:
                logger.info("EPUB fixer is disabled, skipping fix")
                return

            settings = EPUBFixerSettings.from_config_model(epub_config)

            # Initialize services with dependency injection
            fixer_service = EPUBFixerService(session)
            backup_service = (
                BackupService(settings.backup_directory, settings.backup_enabled)
                if settings.backup_enabled
                else NullBackupService()
            )
            recorder = FixResultRecorder(fixer_service)

            # Create fix run
            library_id = self.library_id or (library.id if library else None)
            fix_run = fixer_service.create_fix_run(
                user_id=self.user_id,
                library_id=library_id,
                manually_triggered=True,
                is_bulk_operation=False,
                backup_enabled=settings.backup_enabled,
            )

            update_progress(0.1)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Create backup
            backup_path = backup_service.create_backup(self.file_path)
            update_progress(0.2)

            # Read EPUB
            reader = EPUBReader()
            contents = reader.read(self.file_path)
            update_progress(0.3)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Create orchestrator with fixes
            fixes = [
                BodyIdLinkFix(),
                LanguageFix(default_language=settings.default_language),
                StrayImageFix(),
                EncodingFix(),
            ]
            orchestrator = EPUBFixerOrchestrator(fixes)

            # Apply fixes
            fix_results = orchestrator.process(contents)
            update_progress(0.7)

            # Check if cancelled
            if self.check_cancelled():
                return

            # Write EPUB
            writer = EPUBWriter()
            writer.write(contents, self.file_path)
            update_progress(0.9)

            # Record fixes
            if fix_results and fix_run.id is not None:
                # Get book_id from metadata if available
                book_id = self.metadata.get("book_id")
                book_title = self.metadata.get("book_title", self.file_path.stem)

                recorder.record_fixes(
                    run_id=fix_run.id,
                    book_id=book_id,
                    book_title=book_title,
                    file_path=str(self.file_path),
                    fix_results=fix_results,
                    original_file_path=backup_path,
                    backup_created=backup_path is not None,
                )

            # Complete fix run
            if fix_run.id is not None:
                fixer_service.complete_fix_run(
                    run_id=fix_run.id,
                    total_files_processed=1,
                    total_files_fixed=1 if fix_results else 0,
                    total_fixes_applied=len(fix_results),
                )

            update_progress(1.0)

            logger.info(
                "Task %s: EPUB %s fixed successfully (%d fixes applied)",
                self.task_id,
                self.file_path,
                len(fix_results),
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise


class EPUBFixBatchTask(BaseTask):
    """Task for batch EPUB fixing.

    Scans library and fixes multiple EPUB files with progress tracking.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize EPUB fix batch task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing library_id, etc.
        """
        super().__init__(task_id, user_id, metadata)
        self.library_id = metadata.get("library_id")

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
        """Set up services for batch processing.

        Parameters
        ----------
        session : Session
            Database session.
        library : Any
            Library configuration.

        Returns
        -------
        tuple[EPUBFixerService | None, Any, FixResultRecorder | None, EPUBFixerSettings | None]
            Tuple of (fixer_service, backup_service, recorder, settings).
        """
        # Get EPUB fixer configuration
        stmt = select(EPUBFixerConfig).limit(1)
        epub_config = session.exec(stmt).first()
        if not epub_config or not epub_config.enabled:
            logger.info("EPUB fixer is disabled, skipping batch fix")
            return None, None, None, None  # type: ignore[return-value]

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
        epub_info : Any
            EPUB file information.
        orchestrator : EPUBFixerOrchestrator
            Fix orchestrator.
        reader : EPUBReader
            EPUB reader.
        writer : EPUBWriter
            EPUB writer.
        backup_service : Any
            Backup service.
        recorder : FixResultRecorder
            Fix result recorder.
        fix_run : Any
            Fix run record.

        Returns
        -------
        tuple[int, int]
            Tuple of (files_fixed, total_fixes).
        """
        files_fixed = 0
        total_fixes = 0

        try:
            # Create backup
            backup_path = backup_service.create_backup(epub_info.file_path)

            # Read EPUB
            contents = reader.read(epub_info.file_path)

            # Apply fixes
            fix_results = orchestrator.process(contents)

            # Write EPUB if fixes were applied
            if fix_results:
                writer.write(contents, epub_info.file_path)

                # Record fixes
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
        from fundamental.repositories.calibre_book_repository import (
            CalibreBookRepository,
        )
        from fundamental.services.epub_fixer import EPUBScanner

        calibre_repo = CalibreBookRepository(
            library.calibre_db_path, library.calibre_db_file
        )
        scanner = EPUBScanner(library, calibre_repo)
        return scanner.scan_epub_files()

    def _create_fix_orchestrator(
        self, settings: EPUBFixerSettings
    ) -> tuple[EPUBFixerOrchestrator, EPUBReader, EPUBWriter]:
        """Create fix orchestrator and I/O components.

        Parameters
        ----------
        settings : EPUBFixerSettings
            EPUB fixer settings.

        Returns
        -------
        tuple[EPUBFixerOrchestrator, EPUBReader, EPUBWriter]
            Tuple of orchestrator, reader, and writer.
        """
        fixes = [
            BodyIdLinkFix(),
            LanguageFix(default_language=settings.default_language),
            StrayImageFix(),
            EncodingFix(),
        ]
        orchestrator = EPUBFixerOrchestrator(fixes)
        reader = EPUBReader()
        writer = EPUBWriter()
        return orchestrator, reader, writer

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
        """Process all EPUB files in batch.

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
        update_progress : Any
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
                logger.info("Task %s cancelled during batch processing", self.task_id)
                break

            # Check if should skip
            if fixer_service.should_skip_epub(
                str(epub_info.file_path),
                skip_already_fixed=settings.skip_already_fixed,
                skip_failed=settings.skip_failed,
            ):
                files_processed += 1
                update_progress(files_processed / total_files)
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
            update_progress(files_processed / total_files)

        return files_processed, files_fixed, total_fixes

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute EPUB fix batch task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Get library
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            library = library_service.get_active_library()

            if library is None:
                _raise_no_library_error()

            # Set up services
            result = self._setup_services(session)
            if result is None:
                return
            fixer_service, backup_service, recorder, settings = result

            # Scan for EPUB files
            # library is guaranteed to be not None after _raise_no_library_error check
            if library is None:
                _raise_no_library_error()
            # Type narrowing: library is not None after check
            # Use type: ignore since we've already checked for None
            epub_files = self._scan_epub_files(library)  # type: ignore[arg-type]

            if not epub_files:
                logger.info("No EPUB files found in library")
                return

            # Create fix run
            library_id = self.library_id or (library.id if library else None)  # type: ignore[union-attr]
            fix_run = fixer_service.create_fix_run(
                user_id=self.user_id,
                library_id=library_id,
                manually_triggered=True,
                is_bulk_operation=True,
                backup_enabled=settings.backup_enabled,
            )

            # Create orchestrator
            orchestrator, reader, writer = self._create_fix_orchestrator(settings)

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
                "Task %s: Batch fix completed - %d/%d files fixed, %d fixes applied",
                self.task_id,
                files_fixed,
                files_processed,
                total_fixes,
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

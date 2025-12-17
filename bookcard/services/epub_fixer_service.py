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

"""Service for managing EPUB fixer operations and audit trails.

Provides business logic for creating fix runs, recording fixes,
and querying fix history.
"""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from bookcard.models.config import EPUBFixerConfig
from bookcard.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from bookcard.repositories.epub_fixer_repository import (
    EPUBFixRepository,
    EPUBFixRunRepository,
)

logger = logging.getLogger(__name__)


class EPUBFixerService:
    """Service for managing EPUB fixer operations.

    Provides methods for creating fix runs, recording individual fixes,
    and querying fix history and statistics.

    Parameters
    ----------
    session : Session
        Database session for EPUB fixer operations.
    run_repo : EPUBFixRunRepository | None
        Repository for fix runs. If None, creates a new instance.
    fix_repo : EPUBFixRepository | None
        Repository for individual fixes. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        run_repo: EPUBFixRunRepository | None = None,
        fix_repo: EPUBFixRepository | None = None,
    ) -> None:
        """Initialize EPUB fixer service.

        Parameters
        ----------
        session : Session
            Database session.
        run_repo : EPUBFixRunRepository | None
            Fix run repository. If None, creates a new instance.
        fix_repo : EPUBFixRepository | None
            Fix repository. If None, creates a new instance.
        """
        self._session = session
        self._run_repo = run_repo or EPUBFixRunRepository(session)
        self._fix_repo = fix_repo or EPUBFixRepository(session)

    def create_fix_run(
        self,
        user_id: int | None = None,
        library_id: int | None = None,
        manually_triggered: bool = False,
        is_bulk_operation: bool = False,
        backup_enabled: bool = False,
    ) -> EPUBFixRun:
        """Create a new EPUB fix run.

        Parameters
        ----------
        user_id : int | None
            User who triggered the fix (None for automatic).
        library_id : int | None
            Library ID if library-specific.
        manually_triggered : bool
            Whether the fix was manually triggered (default: False).
        is_bulk_operation : bool
            Whether this is a bulk operation (default: False).
        backup_enabled : bool
            Whether backups are enabled (default: False).

        Returns
        -------
        EPUBFixRun
            Created fix run instance.
        """
        fix_run = EPUBFixRun(
            user_id=user_id,
            library_id=library_id,
            manually_triggered=manually_triggered,
            is_bulk_operation=is_bulk_operation,
            backup_enabled=backup_enabled,
            started_at=datetime.now(UTC),
        )
        self._run_repo.add(fix_run)
        self._session.commit()
        self._session.refresh(fix_run)
        return fix_run

    def complete_fix_run(
        self,
        run_id: int,
        total_files_processed: int,
        total_files_fixed: int,
        total_fixes_applied: int,
        error_message: str | None = None,
    ) -> EPUBFixRun:
        """Complete a fix run with statistics.

        Parameters
        ----------
        run_id : int
            Fix run ID.
        total_files_processed : int
            Total number of files processed.
        total_files_fixed : int
            Number of files that had fixes applied.
        total_fixes_applied : int
            Total number of individual fixes applied.
        error_message : str | None
            Error message if run failed (default: None).

        Returns
        -------
        EPUBFixRun
            Updated fix run instance.

        Raises
        ------
        ValueError
            If fix run not found.
        """
        fix_run = self._run_repo.get(run_id)
        if fix_run is None:
            msg = f"Fix run {run_id} not found"
            raise ValueError(msg)

        fix_run.total_files_processed = total_files_processed
        fix_run.total_files_fixed = total_files_fixed
        fix_run.total_fixes_applied = total_fixes_applied
        fix_run.completed_at = datetime.now(UTC)
        if error_message:
            fix_run.error_message = error_message

        self._session.commit()
        self._session.refresh(fix_run)
        return fix_run

    def record_fix(
        self,
        run_id: int,
        book_id: int | None,
        book_title: str,
        file_path: str,
        fix_type: EPUBFixType,
        fix_description: str,
        file_name: str | None = None,
        original_value: str | None = None,
        fixed_value: str | None = None,
        original_file_path: str | None = None,
        backup_created: bool = False,
    ) -> EPUBFix:
        """Record an individual fix applied to a book.

        Parameters
        ----------
        run_id : int
            Fix run ID.
        book_id : int | None
            Book ID from Calibre database.
        book_title : str
            Book title.
        file_path : str
            Path to the EPUB file that was fixed.
        fix_type : EPUBFixType
            Type of fix applied.
        fix_description : str
            Human-readable description of the fix.
        file_name : str | None
            Filename within EPUB that was fixed (default: None).
        original_value : str | None
            Original value before fix (default: None).
        fixed_value : str | None
            New value after fix (default: None).
        original_file_path : str | None
            Path to backup of original file (default: None).
        backup_created : bool
            Whether backup was created (default: False).

        Returns
        -------
        EPUBFix
            Created fix record.
        """
        epub_fix = EPUBFix(
            run_id=run_id,
            book_id=book_id,
            book_title=book_title,
            file_path=file_path,
            original_file_path=original_file_path,
            fix_type=fix_type,
            fix_description=fix_description,
            file_name=file_name,
            original_value=original_value,
            fixed_value=fixed_value,
            backup_created=backup_created,
            applied_at=datetime.now(UTC),
        )
        self._fix_repo.add(epub_fix)
        return epub_fix

    def get_fix_run(self, run_id: int) -> EPUBFixRun | None:
        """Get a fix run by ID.

        Parameters
        ----------
        run_id : int
            Fix run ID.

        Returns
        -------
        EPUBFixRun | None
            Fix run if found, None otherwise.
        """
        return self._run_repo.get(run_id)

    def get_fixes_for_run(self, run_id: int) -> list[EPUBFix]:
        """Get all fixes for a specific run.

        Parameters
        ----------
        run_id : int
            Fix run ID.

        Returns
        -------
        list[EPUBFix]
            List of fixes for the run.
        """
        return self._fix_repo.get_by_run(run_id)

    def get_fixes_for_book(
        self,
        book_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EPUBFix]:
        """Get all fixes for a specific book.

        Parameters
        ----------
        book_id : int
            Book ID.
        limit : int
            Maximum number of records to return (default: 100).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[EPUBFix]
            List of fixes for the book.
        """
        return self._fix_repo.get_by_book(book_id, limit=limit, offset=offset)

    def get_fixes_for_file_path(
        self,
        file_path: str,
        limit: int = 100,
    ) -> list[EPUBFix]:
        """Get all fixes for a specific file path.

        Parameters
        ----------
        file_path : str
            File path.
        limit : int
            Maximum number of records to return (default: 100).

        Returns
        -------
        list[EPUBFix]
            List of fixes for the file.
        """
        return self._fix_repo.get_by_file_path(file_path, limit=limit)

    def get_recent_runs(
        self,
        limit: int = 20,
        manually_triggered: bool | None = None,
    ) -> list[EPUBFixRun]:
        """Get recent fix runs.

        Parameters
        ----------
        limit : int
            Maximum number of records to return (default: 20).
        manually_triggered : bool | None
            Optional filter for manually triggered runs.

        Returns
        -------
        list[EPUBFixRun]
            List of recent fix runs.
        """
        return self._run_repo.get_recent_runs(
            limit=limit, manually_triggered=manually_triggered
        )

    def get_runs_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EPUBFixRun]:
        """Get fix runs for a specific user.

        Parameters
        ----------
        user_id : int
            User ID.
        limit : int
            Maximum number of records to return (default: 50).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[EPUBFixRun]
            List of fix runs for the user.
        """
        return self._run_repo.get_by_user(user_id, limit=limit, offset=offset)

    def get_runs_by_library(
        self,
        library_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EPUBFixRun]:
        """Get fix runs for a specific library.

        Parameters
        ----------
        library_id : int
            Library ID.
        limit : int
            Maximum number of records to return (default: 50).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[EPUBFixRun]
            List of fix runs for the library.
        """
        return self._run_repo.get_by_library(library_id, limit=limit, offset=offset)

    def get_statistics(
        self,
        user_id: int | None = None,
        library_id: int | None = None,
    ) -> dict[str, int | float]:
        """Get statistics for fix runs.

        Parameters
        ----------
        user_id : int | None
            Optional user ID to filter by.
        library_id : int | None
            Optional library ID to filter by.

        Returns
        -------
        dict[str, int | float]
            Dictionary with statistics.
        """
        return self._run_repo.get_statistics(user_id=user_id, library_id=library_id)

    def get_fix_statistics_by_type(
        self,
        run_id: int | None = None,
        book_id: int | None = None,
    ) -> dict[str, int]:
        """Get statistics grouped by fix type.

        Parameters
        ----------
        run_id : int | None
            Optional run ID to filter by.
        book_id : int | None
            Optional book ID to filter by.

        Returns
        -------
        dict[str, int]
            Dictionary mapping fix type to count.
        """
        return self._fix_repo.get_fix_statistics_by_type(run_id=run_id, book_id=book_id)

    def get_recent_fixes(
        self,
        limit: int = 50,
        fix_type: EPUBFixType | None = None,
    ) -> list[EPUBFix]:
        """Get recent fixes.

        Parameters
        ----------
        limit : int
            Maximum number of records to return (default: 50).
        fix_type : EPUBFixType | None
            Optional filter by fix type.

        Returns
        -------
        list[EPUBFix]
            List of recent fixes.
        """
        return self._fix_repo.get_recent_fixes(limit=limit, fix_type=fix_type)

    def get_incomplete_runs(self) -> list[EPUBFixRun]:
        """Get all incomplete fix runs.

        Returns
        -------
        list[EPUBFixRun]
            List of incomplete fix runs (completed_at is None).
        """
        return self._run_repo.get_incomplete_runs()

    def should_skip_epub(
        self,
        file_path: str,
        skip_already_fixed: bool = True,
        skip_failed: bool = True,
    ) -> bool:
        """Check if EPUB should be skipped.

        Parameters
        ----------
        file_path : str
            Path to EPUB file.
        skip_already_fixed : bool
            Whether to skip already fixed EPUBs (default: True).
        skip_failed : bool
            Whether to skip previously failed EPUBs (default: True).

        Returns
        -------
        bool
            True if EPUB should be skipped, False otherwise.
        """
        # Check for recent successful fixes
        if skip_already_fixed:
            recent_fixes = self._fix_repo.get_by_file_path(file_path, limit=1)
            if recent_fixes:
                # Check if there's a successful fix in the last 30 days
                thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
                for fix in recent_fixes:
                    if fix.applied_at >= thirty_days_ago:
                        # Check if the run was successful (no error)
                        run = self._run_repo.get(fix.run_id)
                        if run and not run.error_message and run.completed_at:
                            return True

        # Check for recent failed fixes
        if skip_failed:
            recent_fixes = self._fix_repo.get_by_file_path(file_path, limit=1)
            if recent_fixes:
                # Check if there's a failed fix in the last 7 days
                seven_days_ago = datetime.now(UTC) - timedelta(days=7)
                for fix in recent_fixes:
                    run = self._run_repo.get(fix.run_id)
                    if (
                        run
                        and run.error_message
                        and run.completed_at
                        and run.completed_at >= seven_days_ago
                    ):
                        return True

        return False

    def process_epub_file(
        self,
        file_path: str | Path,
        book_id: int | None = None,
        book_title: str | None = None,
        user_id: int | None = None,
        library_id: int | None = None,
        manually_triggered: bool = False,
    ) -> EPUBFixRun:
        """Process single EPUB file with full audit trail.

        Parameters
        ----------
        file_path : str | Path
            Path to EPUB file.
        book_id : int | None
            Book ID from Calibre database (default: None).
        book_title : str | None
            Book title (default: None, will use filename).
        user_id : int | None
            User ID who triggered the fix (default: None).
        library_id : int | None
            Library ID (default: None).
        manually_triggered : bool
            Whether fix was manually triggered (default: False).

        Returns
        -------
        EPUBFixRun
            Fix run record.

        Raises
        ------
        FileNotFoundError
            If EPUB file does not exist.
        """
        from pathlib import Path

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

        file_path = Path(file_path)
        if not file_path.exists():
            msg = f"EPUB file not found: {file_path}"
            raise FileNotFoundError(msg)

        # Get configuration
        stmt = select(EPUBFixerConfig).limit(1)
        epub_config = self._session.exec(stmt).first()
        if not epub_config:
            # Create default config
            settings = EPUBFixerSettings()
        else:
            settings = EPUBFixerSettings.from_config_model(epub_config)

        # Create fix run
        fix_run = self.create_fix_run(
            user_id=user_id,
            library_id=library_id,
            manually_triggered=manually_triggered,
            is_bulk_operation=False,
            backup_enabled=settings.backup_enabled,
        )

        # Initialize services
        backup_service = (
            BackupService(settings.backup_directory, settings.backup_enabled)
            if settings.backup_enabled
            else NullBackupService()
        )
        recorder = FixResultRecorder(self)
        reader = EPUBReader()
        writer = EPUBWriter()

        # Create backup
        backup_path = backup_service.create_backup(file_path)

        # Read EPUB
        contents = reader.read(file_path)

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

        # Write EPUB if fixes were applied
        if fix_results:
            writer.write(contents, file_path)

        # Record fixes
        if fix_results and fix_run.id is not None:
            book_title = book_title or file_path.stem
            recorder.record_fixes(
                run_id=fix_run.id,
                book_id=book_id,
                book_title=book_title,
                file_path=str(file_path),
                fix_results=fix_results,
                original_file_path=backup_path,
                backup_created=backup_path is not None,
            )

        # Complete fix run
        if fix_run.id is not None:
            self.complete_fix_run(
                run_id=fix_run.id,
                total_files_processed=1,
                total_files_fixed=1 if fix_results else 0,
                total_fixes_applied=len(fix_results),
            )

        return fix_run

    def rollback_fix_run(self, run_id: int) -> EPUBFixRun:
        """Rollback a fix run by restoring files from backup.

        Parameters
        ----------
        run_id : int
            Fix run ID to rollback.

        Returns
        -------
        EPUBFixRun
            Updated fix run record.

        Raises
        ------
        ValueError
            If fix run not found or cannot be rolled back.
        """
        from bookcard.services.epub_fixer import BackupService

        fix_run = self._run_repo.get(run_id)
        if fix_run is None:
            msg = f"Fix run {run_id} not found"
            raise ValueError(msg)

        # Check if run can be rolled back (completed within last 24 hours)
        if fix_run.completed_at:
            twenty_four_hours_ago = datetime.now(UTC) - timedelta(hours=24)
            if fix_run.completed_at < twenty_four_hours_ago:
                msg = f"Fix run {run_id} is too old to rollback (completed more than 24 hours ago)"
                raise ValueError(msg)

        # Get all fixes for this run
        fixes = self._fix_repo.get_by_run(run_id)

        # Restore files from backup
        backup_service = BackupService(
            Path("/config/processed_books/fixed_originals"), enabled=True
        )
        restored_count = 0

        for fix in fixes:
            if fix.original_file_path and fix.backup_created:
                try:
                    if backup_service.restore_backup(
                        fix.original_file_path, fix.file_path
                    ):
                        restored_count += 1
                        # Mark fix as rolled back in description
                        fix.fix_description = f"[ROLLED BACK] {fix.fix_description}"
                        self._session.add(fix)
                except (OSError, ValueError) as e:
                    logger.warning(
                        "Failed to restore backup for %s: %s", fix.file_path, e
                    )

        # Mark run as cancelled
        fix_run.cancelled_at = datetime.now(UTC)
        fix_run.error_message = (
            f"Rolled back: {restored_count}/{len(fixes)} files restored"
        )

        self._session.commit()
        self._session.refresh(fix_run)

        return fix_run

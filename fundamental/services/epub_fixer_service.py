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

from datetime import UTC, datetime

from sqlmodel import Session

from fundamental.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from fundamental.repositories.epub_fixer_repository import (
    EPUBFixRepository,
    EPUBFixRunRepository,
)


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

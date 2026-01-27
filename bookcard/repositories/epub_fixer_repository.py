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

"""Repository layer for EPUB fixer persistence operations.

Provides data access for EPUB fix runs and individual fixes.
"""

from sqlalchemy import desc, func
from sqlmodel import Session, select

from bookcard.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from bookcard.repositories.base import Repository


class EPUBFixRunRepository(Repository[EPUBFixRun]):
    """Repository for EPUBFixRun entities.

    Provides CRUD operations and specialized queries for EPUB fix runs.
    """

    def __init__(self, session: Session) -> None:
        """Initialize EPUB fix run repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, EPUBFixRun)

    def get_by_user(
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
            List of fix runs for the user, ordered by created_at descending.
        """
        stmt = (
            select(EPUBFixRun)
            .where(EPUBFixRun.user_id == user_id)
            .order_by(desc(EPUBFixRun.created_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

    def get_by_library(
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
            List of fix runs for the library, ordered by created_at descending.
        """
        stmt = (
            select(EPUBFixRun)
            .where(EPUBFixRun.library_id == library_id)
            .order_by(desc(EPUBFixRun.created_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

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
            List of recent fix runs, ordered by created_at descending.
        """
        stmt = select(EPUBFixRun)
        if manually_triggered is not None:
            stmt = stmt.where(EPUBFixRun.manually_triggered == manually_triggered)
        stmt = stmt.order_by(desc(EPUBFixRun.created_at)).limit(limit)  # type: ignore[invalid-argument-type]
        return list(self._session.exec(stmt).all())

    def get_incomplete_runs(self) -> list[EPUBFixRun]:
        """Get all incomplete fix runs (completed_at is None).

        Returns
        -------
        list[EPUBFixRun]
            List of incomplete fix runs.
        """
        stmt = select(EPUBFixRun).where(
            EPUBFixRun.completed_at.is_(None)  # type: ignore[attr-defined]
        )
        return list(self._session.exec(stmt).all())

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
            Dictionary with statistics:
            - total_runs: Total number of runs
            - total_files_processed: Total files processed
            - total_files_fixed: Total files fixed
            - total_fixes_applied: Total fixes applied
            - avg_files_per_run: Average files per run
            - avg_fixes_per_file: Average fixes per file
        """
        stmt = select(
            func.count(EPUBFixRun.id).label("total_runs"),
            func.sum(EPUBFixRun.total_files_processed).label("total_files_processed"),
            func.sum(EPUBFixRun.total_files_fixed).label("total_files_fixed"),
            func.sum(EPUBFixRun.total_fixes_applied).label("total_fixes_applied"),
        )
        if user_id is not None:
            stmt = stmt.where(EPUBFixRun.user_id == user_id)
        if library_id is not None:
            stmt = stmt.where(EPUBFixRun.library_id == library_id)

        result = self._session.exec(stmt).first()
        if result is None:
            return {
                "total_runs": 0,
                "total_files_processed": 0,
                "total_files_fixed": 0,
                "total_fixes_applied": 0,
                "avg_files_per_run": 0.0,
                "avg_fixes_per_file": 0.0,
            }

        # Access Row attributes using getattr for type safety
        total_runs = getattr(result, "total_runs", None) or 0
        total_files_processed = getattr(result, "total_files_processed", None) or 0
        total_files_fixed = getattr(result, "total_files_fixed", None) or 0
        total_fixes_applied = getattr(result, "total_fixes_applied", None) or 0

        avg_files_per_run = (
            total_files_processed / total_runs if total_runs > 0 else 0.0
        )
        avg_fixes_per_file = (
            total_fixes_applied / total_files_fixed if total_files_fixed > 0 else 0.0
        )

        return {
            "total_runs": total_runs,
            "total_files_processed": total_files_processed,
            "total_files_fixed": total_files_fixed,
            "total_fixes_applied": total_fixes_applied,
            "avg_files_per_run": avg_files_per_run,
            "avg_fixes_per_file": avg_fixes_per_file,
        }


class EPUBFixRepository(Repository[EPUBFix]):
    """Repository for EPUBFix entities.

    Provides CRUD operations and specialized queries for individual fixes.
    """

    def __init__(self, session: Session) -> None:
        """Initialize EPUB fix repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        super().__init__(session, EPUBFix)

    def get_by_run(self, run_id: int) -> list[EPUBFix]:
        """Get all fixes for a specific run.

        Parameters
        ----------
        run_id : int
            Fix run ID.

        Returns
        -------
        list[EPUBFix]
            List of fixes for the run, ordered by applied_at.
        """
        stmt = (
            select(EPUBFix).where(EPUBFix.run_id == run_id).order_by(EPUBFix.applied_at)  # type: ignore[invalid-argument-type]
        )
        return list(self._session.exec(stmt).all())

    def get_by_book(
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
            List of fixes for the book, ordered by applied_at descending.
        """
        stmt = (
            select(EPUBFix)
            .where(EPUBFix.book_id == book_id)
            .order_by(desc(EPUBFix.applied_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

    def get_by_file_path(
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
            List of fixes for the file, ordered by applied_at descending.
        """
        stmt = (
            select(EPUBFix)
            .where(EPUBFix.file_path == file_path)
            .order_by(desc(EPUBFix.applied_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_by_fix_type(
        self,
        fix_type: EPUBFixType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EPUBFix]:
        """Get fixes by type.

        Parameters
        ----------
        fix_type : EPUBFixType
            Type of fix.
        limit : int
            Maximum number of records to return (default: 100).
        offset : int
            Number of records to skip (default: 0).

        Returns
        -------
        list[EPUBFix]
            List of fixes of the specified type, ordered by applied_at descending.
        """
        stmt = (
            select(EPUBFix)
            .where(EPUBFix.fix_type == fix_type)
            .order_by(desc(EPUBFix.applied_at))  # type: ignore[invalid-argument-type]
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.exec(stmt).all())

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
        stmt = select(
            EPUBFix.fix_type,
            func.count(EPUBFix.id).label("count"),
        ).group_by(EPUBFix.fix_type)

        if run_id is not None:
            stmt = stmt.where(EPUBFix.run_id == run_id)
        if book_id is not None:
            stmt = stmt.where(EPUBFix.book_id == book_id)

        results = self._session.exec(stmt).all()
        return {
            str(getattr(result, "fix_type", "")): getattr(result, "count", 0)
            for result in results
        }

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
            List of recent fixes, ordered by applied_at descending.
        """
        stmt = select(EPUBFix)
        if fix_type is not None:
            stmt = stmt.where(EPUBFix.fix_type == fix_type)
        stmt = stmt.order_by(desc(EPUBFix.applied_at)).limit(limit)  # type: ignore[invalid-argument-type]
        return list(self._session.exec(stmt).all())

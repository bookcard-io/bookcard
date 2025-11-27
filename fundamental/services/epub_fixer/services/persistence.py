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

"""Persistence service for recording fix results.

Separates persistence concerns from EPUB processing logic.
"""

from fundamental.models.epub_fixer import EPUBFix
from fundamental.services.epub_fixer.core.epub import FixResult
from fundamental.services.epub_fixer_service import EPUBFixerService


class FixResultRecorder:
    """Service for recording fix results to database.

    Separates persistence from processing logic.
    Uses EPUBFixerService internally for database operations.

    Parameters
    ----------
    fixer_service : EPUBFixerService
        EPUB fixer service for database operations.
    """

    def __init__(self, fixer_service: EPUBFixerService) -> None:
        """Initialize fix result recorder.

        Parameters
        ----------
        fixer_service : EPUBFixerService
            EPUB fixer service.
        """
        self._fixer_service = fixer_service

    def record_fix(
        self,
        run_id: int,
        book_id: int | None,
        book_title: str,
        file_path: str,
        fix_result: FixResult,
        original_file_path: str | None = None,
        backup_created: bool = False,
    ) -> EPUBFix:
        """Record a single fix result.

        Parameters
        ----------
        run_id : int
            Fix run ID.
        book_id : int | None
            Book ID from Calibre database.
        book_title : str
            Book title.
        file_path : str
            Path to EPUB file.
        fix_result : FixResult
            Fix result to record.
        original_file_path : str | None
            Path to backup file (default: None).
        backup_created : bool
            Whether backup was created (default: False).

        Returns
        -------
        EPUBFix
            Created fix record.
        """
        return self._fixer_service.record_fix(
            run_id=run_id,
            book_id=book_id,
            book_title=book_title,
            file_path=file_path,
            fix_type=fix_result.fix_type,
            fix_description=fix_result.description,
            file_name=fix_result.file_name,
            original_value=fix_result.original_value,
            fixed_value=fix_result.fixed_value,
            original_file_path=original_file_path,
            backup_created=backup_created,
        )

    def record_fixes(
        self,
        run_id: int,
        book_id: int | None,
        book_title: str,
        file_path: str,
        fix_results: list[FixResult],
        original_file_path: str | None = None,
        backup_created: bool = False,
    ) -> list[EPUBFix]:
        """Record multiple fix results.

        Parameters
        ----------
        run_id : int
            Fix run ID.
        book_id : int | None
            Book ID from Calibre database.
        book_title : str
            Book title.
        file_path : str
            Path to EPUB file.
        fix_results : list[FixResult]
            List of fix results to record.
        original_file_path : str | None
            Path to backup file (default: None).
        backup_created : bool
            Whether backup was created (default: False).

        Returns
        -------
        list[EPUBFix]
            List of created fix records.
        """
        fixes: list[EPUBFix] = []

        for fix_result in fix_results:
            fix = self.record_fix(
                run_id=run_id,
                book_id=book_id,
                book_title=book_title,
                file_path=file_path,
                fix_result=fix_result,
                original_file_path=original_file_path,
                backup_created=backup_created,
            )
            fixes.append(fix)

        return fixes

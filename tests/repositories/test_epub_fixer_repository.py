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

"""Tests for EPUB fixer repository to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from bookcard.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from bookcard.repositories.epub_fixer_repository import (
    EPUBFixRepository,
    EPUBFixRunRepository,
)
from tests.repositories.test_base_repository import MockSession


class MockResultWithFirst[T]:
    """Mock query result with first() method support."""

    def __init__(self, items: list[T]) -> None:
        self._items = items

    def all(self) -> list[T]:
        """Return all items."""
        return self._items

    def first(self) -> T | None:
        """Return first item or None if empty."""
        return self._items[0] if self._items else None


# Patch MockSession to return MockResultWithFirst for statistics queries
class MockSessionWithFirst(MockSession):
    """Extended MockSession that supports first() method."""

    def __init__(self) -> None:
        """Initialize extended mock session."""
        super().__init__()

    def exec(self, stmt: Any) -> MockResultWithFirst:  # noqa: ANN401
        """Execute statement and return result with first() support."""
        return MockResultWithFirst(self._next_exec_result)


@pytest.fixture
def session() -> MockSessionWithFirst:
    """Create a mock session."""
    return MockSessionWithFirst()


@pytest.fixture
def fix_run_repo(session: MockSessionWithFirst) -> EPUBFixRunRepository:
    """Create EPUBFixRunRepository instance."""
    return EPUBFixRunRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def fix_repo(session: MockSessionWithFirst) -> EPUBFixRepository:
    """Create EPUBFixRepository instance."""
    return EPUBFixRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def fix_run() -> EPUBFixRun:
    """Create an EPUBFixRun instance."""
    return EPUBFixRun(
        id=1,
        user_id=1,
        library_id=1,
        manually_triggered=True,
        is_bulk_operation=True,
        total_files_processed=10,
        total_files_fixed=8,
        total_fixes_applied=15,
        backup_enabled=True,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


@pytest.fixture
def fix_run_incomplete() -> EPUBFixRun:
    """Create an incomplete EPUBFixRun instance."""
    return EPUBFixRun(
        id=2,
        user_id=2,
        library_id=2,
        manually_triggered=False,
        is_bulk_operation=False,
        total_files_processed=5,
        total_files_fixed=0,
        total_fixes_applied=0,
        backup_enabled=False,
        started_at=datetime.now(UTC),
        completed_at=None,
    )


@pytest.fixture
def epub_fix(fix_run: EPUBFixRun) -> EPUBFix:
    """Create an EPUBFix instance."""
    return EPUBFix(
        id=1,
        run_id=fix_run.id or 1,
        book_id=100,
        book_title="Test Book",
        file_path="/path/to/book.epub",
        original_file_path="/path/to/book.epub.bak",
        fix_type=EPUBFixType.ENCODING,
        fix_description="Fixed encoding",
        file_name="content.opf",
        original_value="iso-8859-1",
        fixed_value="utf-8",
        backup_created=True,
        applied_at=datetime.now(UTC),
    )


class TestEPUBFixRunRepositoryInit:
    """Test EPUBFixRunRepository initialization."""

    def test_init(self, session: MockSession) -> None:
        """Test repository initialization."""
        repo = EPUBFixRunRepository(session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == EPUBFixRun


class TestEPUBFixRunRepositoryGetByUser:
    """Test get_by_user method."""

    @pytest.mark.parametrize(
        ("user_id", "limit", "offset", "expected_count"),
        [
            (1, 50, 0, 2),
            (1, 10, 0, 2),
            (1, 1, 0, 1),
            (1, 50, 1, 1),
            (2, 50, 0, 1),
        ],
    )
    def test_get_by_user(
        self,
        fix_run_repo: EPUBFixRunRepository,
        session: MockSessionWithFirst,
        fix_run: EPUBFixRun,
        fix_run_incomplete: EPUBFixRun,
        user_id: int,
        limit: int,
        offset: int,
        expected_count: int,
    ) -> None:
        """Test get_by_user with various parameters."""
        # Setup: user 1 has both runs, user 2 has incomplete run
        fix_run.user_id = 1
        fix_run_incomplete.user_id = 2

        # Create additional run for user 1 to test offset/limit
        fix_run2 = EPUBFixRun(
            id=3,
            user_id=1,
            library_id=1,
            manually_triggered=False,
            is_bulk_operation=False,
            total_files_processed=3,
            total_files_fixed=2,
            total_fixes_applied=4,
        )

        # Set up results based on user_id - mock returns filtered results
        if user_id == 1:
            # User 1 has fix_run and fix_run2
            all_results = [fix_run, fix_run2]
            # Apply offset and limit in mock (simulating SQL behavior)
            filtered_results = all_results[offset : offset + limit]
        else:
            # User 2 only has incomplete run
            filtered_results = [fix_run_incomplete][offset : offset + limit]

        session.set_exec_result(filtered_results)

        result = fix_run_repo.get_by_user(user_id=user_id, limit=limit, offset=offset)
        assert len(result) == expected_count
        if result:
            assert all(run.user_id == user_id for run in result)

    def test_get_by_user_empty(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSessionWithFirst
    ) -> None:
        """Test get_by_user returns empty list when no results."""
        session.set_exec_result([])
        result = fix_run_repo.get_by_user(user_id=999)
        assert result == []


class TestEPUBFixRunRepositoryGetByLibrary:
    """Test get_by_library method."""

    @pytest.mark.parametrize(
        ("library_id", "limit", "offset"),
        [
            (1, 50, 0),
            (1, 10, 5),
            (2, 20, 0),
        ],
    )
    def test_get_by_library(
        self,
        fix_run_repo: EPUBFixRunRepository,
        session: MockSessionWithFirst,
        fix_run: EPUBFixRun,
        library_id: int,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_by_library with various parameters."""
        fix_run.library_id = library_id
        session.set_exec_result([fix_run])
        result = fix_run_repo.get_by_library(
            library_id=library_id, limit=limit, offset=offset
        )
        assert len(result) == 1
        assert result[0].library_id == library_id

    def test_get_by_library_empty(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_by_library returns empty list when no results."""
        session.set_exec_result([])
        result = fix_run_repo.get_by_library(library_id=999)
        assert result == []


class TestEPUBFixRunRepositoryGetRecentRuns:
    """Test get_recent_runs method."""

    @pytest.mark.parametrize(
        ("limit", "manually_triggered", "expected_count"),
        [
            (20, None, 2),
            (10, True, 1),
            (10, False, 1),
            (1, None, 1),
        ],
    )
    def test_get_recent_runs(
        self,
        fix_run_repo: EPUBFixRunRepository,
        session: MockSessionWithFirst,
        fix_run: EPUBFixRun,
        fix_run_incomplete: EPUBFixRun,
        limit: int,
        manually_triggered: bool | None,
        expected_count: int,
    ) -> None:
        """Test get_recent_runs with various parameters."""
        # Setup: fix_run is manually triggered, fix_run_incomplete is not
        fix_run.manually_triggered = True
        fix_run_incomplete.manually_triggered = False

        # Filter results based on manually_triggered parameter
        if manually_triggered is True:
            filtered_results = [fix_run][:limit]
        elif manually_triggered is False:
            filtered_results = [fix_run_incomplete][:limit]
        else:
            # None means return all, but limit applies
            filtered_results = [fix_run, fix_run_incomplete][:limit]

        session.set_exec_result(filtered_results)
        result = fix_run_repo.get_recent_runs(
            limit=limit, manually_triggered=manually_triggered
        )
        assert len(result) == expected_count

    def test_get_recent_runs_empty(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_recent_runs returns empty list when no results."""
        session.set_exec_result([])
        result = fix_run_repo.get_recent_runs()
        assert result == []


class TestEPUBFixRunRepositoryGetIncompleteRuns:
    """Test get_incomplete_runs method."""

    def test_get_incomplete_runs(
        self,
        fix_run_repo: EPUBFixRunRepository,
        session: MockSessionWithFirst,
        fix_run_incomplete: EPUBFixRun,
    ) -> None:
        """Test get_incomplete_runs returns runs with completed_at=None."""
        session.set_exec_result([fix_run_incomplete])
        result = fix_run_repo.get_incomplete_runs()
        assert len(result) == 1
        assert result[0].completed_at is None

    def test_get_incomplete_runs_empty(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_incomplete_runs returns empty list when no incomplete runs."""
        session.set_exec_result([])
        result = fix_run_repo.get_incomplete_runs()
        assert result == []


class TestEPUBFixRunRepositoryGetStatistics:
    """Test get_statistics method."""

    def test_get_statistics_no_filters(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_statistics without filters."""
        # Create a mock result row
        mock_result = MagicMock()
        mock_result.total_runs = 2
        mock_result.total_files_processed = 15
        mock_result.total_files_fixed = 8
        mock_result.total_fixes_applied = 15

        session.set_exec_result([mock_result])
        result = fix_run_repo.get_statistics()

        assert result["total_runs"] == 2
        assert result["total_files_processed"] == 15
        assert result["total_files_fixed"] == 8
        assert result["total_fixes_applied"] == 15
        assert result["avg_files_per_run"] == 7.5
        assert result["avg_fixes_per_file"] == 15 / 8

    @pytest.mark.parametrize(
        ("user_id", "library_id"),
        [
            (1, None),
            (None, 1),
            (1, 1),
        ],
    )
    def test_get_statistics_with_filters(
        self,
        fix_run_repo: EPUBFixRunRepository,
        session: MockSessionWithFirst,
        user_id: int | None,
        library_id: int | None,
    ) -> None:
        """Test get_statistics with user_id and/or library_id filters."""
        mock_result = MagicMock()
        mock_result.total_runs = 1
        mock_result.total_files_processed = 10
        mock_result.total_files_fixed = 8
        mock_result.total_fixes_applied = 12

        session.set_exec_result([mock_result])
        result = fix_run_repo.get_statistics(user_id=user_id, library_id=library_id)

        assert result["total_runs"] == 1
        assert result["avg_files_per_run"] == 10.0

    def test_get_statistics_no_result(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_statistics returns zeros when no result."""
        session.set_exec_result([None])
        result = fix_run_repo.get_statistics()

        assert result["total_runs"] == 0
        assert result["total_files_processed"] == 0
        assert result["total_files_fixed"] == 0
        assert result["total_fixes_applied"] == 0
        assert result["avg_files_per_run"] == 0.0
        assert result["avg_fixes_per_file"] == 0.0

    def test_get_statistics_zero_division(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_statistics handles zero division."""
        mock_result = MagicMock()
        mock_result.total_runs = 0
        mock_result.total_files_processed = 0
        mock_result.total_files_fixed = 0
        mock_result.total_fixes_applied = 0

        session.set_exec_result([mock_result])
        result = fix_run_repo.get_statistics()

        assert result["avg_files_per_run"] == 0.0
        assert result["avg_fixes_per_file"] == 0.0

    def test_get_statistics_none_values(
        self, fix_run_repo: EPUBFixRunRepository, session: MockSession
    ) -> None:
        """Test get_statistics handles None values in result."""
        mock_result = MagicMock()
        mock_result.total_runs = None
        mock_result.total_files_processed = None
        mock_result.total_files_fixed = None
        mock_result.total_fixes_applied = None

        session.set_exec_result([mock_result])
        result = fix_run_repo.get_statistics()

        assert result["total_runs"] == 0
        assert result["total_files_processed"] == 0
        assert result["total_files_fixed"] == 0
        assert result["total_fixes_applied"] == 0


class TestEPUBFixRepositoryInit:
    """Test EPUBFixRepository initialization."""

    def test_init(self, session: MockSession) -> None:
        """Test repository initialization."""
        repo = EPUBFixRepository(session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == EPUBFix


class TestEPUBFixRepositoryGetByRun:
    """Test get_by_run method."""

    def test_get_by_run(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        epub_fix: EPUBFix,
    ) -> None:
        """Test get_by_run returns fixes for a run."""
        session.set_exec_result([epub_fix])
        result = fix_repo.get_by_run(run_id=1)
        assert len(result) == 1
        assert result[0].run_id == 1

    def test_get_by_run_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_by_run returns empty list when no fixes."""
        session.set_exec_result([])
        result = fix_repo.get_by_run(run_id=999)
        assert result == []


class TestEPUBFixRepositoryGetByBook:
    """Test get_by_book method."""

    @pytest.mark.parametrize(
        ("book_id", "limit", "offset"),
        [
            (100, 100, 0),
            (100, 50, 0),
            (100, 10, 5),
            (200, 20, 0),
        ],
    )
    def test_get_by_book(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        epub_fix: EPUBFix,
        book_id: int,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_by_book with various parameters."""
        epub_fix.book_id = book_id
        session.set_exec_result([epub_fix])
        result = fix_repo.get_by_book(book_id=book_id, limit=limit, offset=offset)
        assert len(result) == 1
        assert result[0].book_id == book_id

    def test_get_by_book_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_by_book returns empty list when no fixes."""
        session.set_exec_result([])
        result = fix_repo.get_by_book(book_id=999)
        assert result == []


class TestEPUBFixRepositoryGetByFilePath:
    """Test get_by_file_path method."""

    @pytest.mark.parametrize(
        ("file_path", "limit"),
        [
            ("/path/to/book.epub", 100),
            ("/path/to/other.epub", 50),
            ("/path/to/book.epub", 10),
        ],
    )
    def test_get_by_file_path(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        epub_fix: EPUBFix,
        file_path: str,
        limit: int,
    ) -> None:
        """Test get_by_file_path with various parameters."""
        epub_fix.file_path = file_path
        session.set_exec_result([epub_fix])
        result = fix_repo.get_by_file_path(file_path=file_path, limit=limit)
        assert len(result) == 1
        assert result[0].file_path == file_path

    def test_get_by_file_path_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_by_file_path returns empty list when no fixes."""
        session.set_exec_result([])
        result = fix_repo.get_by_file_path(file_path="/nonexistent.epub")
        assert result == []


class TestEPUBFixRepositoryGetByFixType:
    """Test get_by_fix_type method."""

    @pytest.mark.parametrize(
        ("fix_type", "limit", "offset"),
        [
            (EPUBFixType.ENCODING, 100, 0),
            (EPUBFixType.BODY_ID_LINK, 50, 0),
            (EPUBFixType.LANGUAGE_TAG, 20, 5),
            (EPUBFixType.STRAY_IMG, 10, 0),
        ],
    )
    def test_get_by_fix_type(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        epub_fix: EPUBFix,
        fix_type: EPUBFixType,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_by_fix_type with various parameters."""
        epub_fix.fix_type = fix_type
        session.set_exec_result([epub_fix])
        result = fix_repo.get_by_fix_type(fix_type=fix_type, limit=limit, offset=offset)
        assert len(result) == 1
        assert result[0].fix_type == fix_type

    def test_get_by_fix_type_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_by_fix_type returns empty list when no fixes."""
        session.set_exec_result([])
        result = fix_repo.get_by_fix_type(fix_type=EPUBFixType.ENCODING)
        assert result == []


class TestEPUBFixRepositoryGetFixStatisticsByType:
    """Test get_fix_statistics_by_type method."""

    def test_get_fix_statistics_by_type_no_filters(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_fix_statistics_by_type without filters."""
        # Create mock results for grouped query
        mock_result1 = MagicMock()
        mock_result1.fix_type = EPUBFixType.ENCODING
        mock_result1.count = 5

        mock_result2 = MagicMock()
        mock_result2.fix_type = EPUBFixType.BODY_ID_LINK
        mock_result2.count = 3

        session.set_exec_result([mock_result1, mock_result2])
        result = fix_repo.get_fix_statistics_by_type()

        assert result["encoding"] == 5
        assert result["body_id_link"] == 3

    @pytest.mark.parametrize(
        ("run_id", "book_id"),
        [
            (1, None),
            (None, 100),
            (1, 100),
        ],
    )
    def test_get_fix_statistics_by_type_with_filters(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        run_id: int | None,
        book_id: int | None,
    ) -> None:
        """Test get_fix_statistics_by_type with run_id and/or book_id filters."""
        mock_result = MagicMock()
        mock_result.fix_type = EPUBFixType.LANGUAGE_TAG
        mock_result.count = 2

        session.set_exec_result([mock_result])
        result = fix_repo.get_fix_statistics_by_type(run_id=run_id, book_id=book_id)

        assert result["language_tag"] == 2

    def test_get_fix_statistics_by_type_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_fix_statistics_by_type returns empty dict when no results."""
        session.set_exec_result([])
        result = fix_repo.get_fix_statistics_by_type()
        assert result == {}


class TestEPUBFixRepositoryGetRecentFixes:
    """Test get_recent_fixes method."""

    @pytest.mark.parametrize(
        ("limit", "fix_type"),
        [
            (50, None),
            (20, EPUBFixType.ENCODING),
            (10, EPUBFixType.BODY_ID_LINK),
        ],
    )
    def test_get_recent_fixes(
        self,
        fix_repo: EPUBFixRepository,
        session: MockSessionWithFirst,
        epub_fix: EPUBFix,
        limit: int,
        fix_type: EPUBFixType | None,
    ) -> None:
        """Test get_recent_fixes with various parameters."""
        if fix_type:
            epub_fix.fix_type = fix_type
        session.set_exec_result([epub_fix])
        result = fix_repo.get_recent_fixes(limit=limit, fix_type=fix_type)
        assert len(result) == 1
        if fix_type:
            assert result[0].fix_type == fix_type

    def test_get_recent_fixes_empty(
        self, fix_repo: EPUBFixRepository, session: MockSession
    ) -> None:
        """Test get_recent_fixes returns empty list when no fixes."""
        session.set_exec_result([])
        result = fix_repo.get_recent_fixes()
        assert result == []

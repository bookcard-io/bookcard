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

"""Tests for EPUB fixer service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import DummySession

from bookcard.models.config import EPUBFixerConfig
from bookcard.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from bookcard.repositories.epub_fixer_repository import (
    EPUBFixRepository,
    EPUBFixRunRepository,
)
from bookcard.services.epub_fixer_service import EPUBFixerService


@pytest.fixture
def mock_run_repo() -> MagicMock:
    """Create a mock EPUBFixRunRepository."""
    return MagicMock(spec=EPUBFixRunRepository)


@pytest.fixture
def mock_fix_repo() -> MagicMock:
    """Create a mock EPUBFixRepository."""
    return MagicMock(spec=EPUBFixRepository)


@pytest.fixture
def service(
    session: DummySession, mock_run_repo: MagicMock, mock_fix_repo: MagicMock
) -> EPUBFixerService:
    """Create EPUBFixerService with mock repositories."""
    return EPUBFixerService(
        session=session,  # type: ignore[valid-type]
        run_repo=mock_run_repo,
        fix_repo=mock_fix_repo,  # type: ignore[valid-type]
    )


@pytest.fixture
def service_default_repo(session: DummySession) -> EPUBFixerService:
    """Create EPUBFixerService with default repositories."""
    return EPUBFixerService(session=session)  # type: ignore[valid-type]


@pytest.fixture
def fix_run() -> EPUBFixRun:
    """Create an EPUBFixRun instance."""
    return EPUBFixRun(
        id=1,
        user_id=1,
        library_id=1,
        manually_triggered=True,
        is_bulk_operation=False,
        total_files_processed=10,
        total_files_fixed=8,
        total_fixes_applied=15,
        backup_enabled=True,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
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
        fix_type=EPUBFixType.ENCODING,
        fix_description="Fixed encoding",
        applied_at=datetime.now(UTC),
    )


class TestEPUBFixerServiceInit:
    """Test EPUBFixerService initialization."""

    def test_init_with_repos(
        self,
        session: DummySession,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
    ) -> None:
        """Test initialization with provided repositories."""
        service = EPUBFixerService(
            session=session,  # type: ignore[valid-type]
            run_repo=mock_run_repo,
            fix_repo=mock_fix_repo,  # type: ignore[valid-type]
        )
        assert service._run_repo == mock_run_repo
        assert service._fix_repo == mock_fix_repo

    def test_init_without_repos(self, session: DummySession) -> None:
        """Test initialization without repositories (creates defaults)."""
        service = EPUBFixerService(session=session)  # type: ignore[valid-type]
        assert isinstance(service._run_repo, EPUBFixRunRepository)
        assert isinstance(service._fix_repo, EPUBFixRepository)


class TestEPUBFixerServiceCreateFixRun:
    """Test create_fix_run method."""

    @pytest.mark.parametrize(
        (
            "user_id",
            "library_id",
            "manually_triggered",
            "is_bulk_operation",
            "backup_enabled",
        ),
        [
            (None, None, False, False, False),
            (1, None, True, False, True),
            (None, 1, False, True, False),
            (1, 1, True, True, True),
        ],
    )
    def test_create_fix_run(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        session: DummySession,
        user_id: int | None,
        library_id: int | None,
        manually_triggered: bool,
        is_bulk_operation: bool,
        backup_enabled: bool,
    ) -> None:
        """Test create_fix_run with various parameters."""
        fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
        mock_run_repo.add.return_value = fix_run
        session.added.append(fix_run)

        result = service.create_fix_run(
            user_id=user_id,
            library_id=library_id,
            manually_triggered=manually_triggered,
            is_bulk_operation=is_bulk_operation,
            backup_enabled=backup_enabled,
        )

        assert result.user_id == user_id
        assert result.library_id == library_id
        assert result.manually_triggered == manually_triggered
        assert result.is_bulk_operation == is_bulk_operation
        assert result.backup_enabled == backup_enabled
        mock_run_repo.add.assert_called_once()
        assert session.commit_count > 0


class TestEPUBFixerServiceCompleteFixRun:
    """Test complete_fix_run method."""

    def test_complete_fix_run_success(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        session: DummySession,
    ) -> None:
        """Test complete_fix_run successfully completes a run."""
        mock_run_repo.get.return_value = fix_run

        result = service.complete_fix_run(
            run_id=1,
            total_files_processed=10,
            total_files_fixed=8,
            total_fixes_applied=15,
        )

        assert result.total_files_processed == 10
        assert result.total_files_fixed == 8
        assert result.total_fixes_applied == 15
        assert result.completed_at is not None
        assert session.commit_count > 0

    def test_complete_fix_run_with_error(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
    ) -> None:
        """Test complete_fix_run with error message."""
        mock_run_repo.get.return_value = fix_run

        result = service.complete_fix_run(
            run_id=1,
            total_files_processed=5,
            total_files_fixed=0,
            total_fixes_applied=0,
            error_message="Test error",
        )

        assert result.error_message == "Test error"

    def test_complete_fix_run_not_found(
        self, service: EPUBFixerService, mock_run_repo: MagicMock
    ) -> None:
        """Test complete_fix_run raises ValueError when run not found."""
        mock_run_repo.get.return_value = None

        with pytest.raises(ValueError, match="Fix run 999 not found"):
            service.complete_fix_run(
                run_id=999,
                total_files_processed=0,
                total_files_fixed=0,
                total_fixes_applied=0,
            )


class TestEPUBFixerServiceRecordFix:
    """Test record_fix method."""

    @pytest.mark.parametrize(
        (
            "file_name",
            "original_value",
            "fixed_value",
            "original_file_path",
            "backup_created",
        ),
        [
            (None, None, None, None, False),
            ("content.opf", "old", "new", "/backup.epub", True),
            ("chapter.html", None, None, None, False),
        ],
    )
    def test_record_fix(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        file_name: str | None,
        original_value: str | None,
        fixed_value: str | None,
        original_file_path: str | None,
        backup_created: bool,
    ) -> None:
        """Test record_fix with various parameters."""
        result = service.record_fix(
            run_id=1,
            book_id=100,
            book_title="Test Book",
            file_path="/path/to/book.epub",
            fix_type=EPUBFixType.ENCODING,
            fix_description="Fixed encoding",
            file_name=file_name,
            original_value=original_value,
            fixed_value=fixed_value,
            original_file_path=original_file_path,
            backup_created=backup_created,
        )

        assert result.run_id == 1
        assert result.book_id == 100
        assert result.fix_type == EPUBFixType.ENCODING
        mock_fix_repo.add.assert_called_once()

    @pytest.mark.parametrize("fix_type", list(EPUBFixType))
    def test_record_fix_all_types(
        self, service: EPUBFixerService, fix_type: EPUBFixType
    ) -> None:
        """Test record_fix with all fix types."""
        result = service.record_fix(
            run_id=1,
            book_id=None,
            book_title="Test Book",
            file_path="/path/to/book.epub",
            fix_type=fix_type,
            fix_description=f"Fixed {fix_type}",
        )
        assert result.fix_type == fix_type


class TestEPUBFixerServiceGetMethods:
    """Test getter methods."""

    def test_get_fix_run_found(
        self, service: EPUBFixerService, mock_run_repo: MagicMock, fix_run: EPUBFixRun
    ) -> None:
        """Test get_fix_run returns run when found."""
        mock_run_repo.get.return_value = fix_run
        result = service.get_fix_run(run_id=1)
        assert result == fix_run

    def test_get_fix_run_not_found(
        self, service: EPUBFixerService, mock_run_repo: MagicMock
    ) -> None:
        """Test get_fix_run returns None when not found."""
        mock_run_repo.get.return_value = None
        result = service.get_fix_run(run_id=999)
        assert result is None

    def test_get_fixes_for_run(
        self, service: EPUBFixerService, mock_fix_repo: MagicMock, epub_fix: EPUBFix
    ) -> None:
        """Test get_fixes_for_run delegates to repository."""
        mock_fix_repo.get_by_run.return_value = [epub_fix]
        result = service.get_fixes_for_run(run_id=1)
        assert result == [epub_fix]
        mock_fix_repo.get_by_run.assert_called_once_with(1)

    @pytest.mark.parametrize(
        ("book_id", "limit", "offset"),
        [
            (100, 100, 0),
            (200, 50, 10),
            (300, 20, 0),
        ],
    )
    def test_get_fixes_for_book(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        epub_fix: EPUBFix,
        book_id: int,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_fixes_for_book with various parameters."""
        mock_fix_repo.get_by_book.return_value = [epub_fix]
        result = service.get_fixes_for_book(book_id=book_id, limit=limit, offset=offset)
        assert result == [epub_fix]
        mock_fix_repo.get_by_book.assert_called_once_with(
            book_id, limit=limit, offset=offset
        )

    @pytest.mark.parametrize(
        ("file_path", "limit"),
        [
            ("/path/to/book.epub", 100),
            ("/path/to/other.epub", 50),
        ],
    )
    def test_get_fixes_for_file_path(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        epub_fix: EPUBFix,
        file_path: str,
        limit: int,
    ) -> None:
        """Test get_fixes_for_file_path with various parameters."""
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        result = service.get_fixes_for_file_path(file_path=file_path, limit=limit)
        assert result == [epub_fix]
        mock_fix_repo.get_by_file_path.assert_called_once_with(file_path, limit=limit)

    @pytest.mark.parametrize(
        ("limit", "manually_triggered"),
        [
            (20, None),
            (10, True),
            (10, False),
        ],
    )
    def test_get_recent_runs(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        limit: int,
        manually_triggered: bool | None,
    ) -> None:
        """Test get_recent_runs with various parameters."""
        mock_run_repo.get_recent_runs.return_value = [fix_run]
        result = service.get_recent_runs(
            limit=limit, manually_triggered=manually_triggered
        )
        assert result == [fix_run]
        mock_run_repo.get_recent_runs.assert_called_once_with(
            limit=limit, manually_triggered=manually_triggered
        )

    @pytest.mark.parametrize(
        ("user_id", "limit", "offset"),
        [
            (1, 50, 0),
            (2, 20, 10),
        ],
    )
    def test_get_runs_by_user(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        user_id: int,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_runs_by_user with various parameters."""
        mock_run_repo.get_by_user.return_value = [fix_run]
        result = service.get_runs_by_user(user_id=user_id, limit=limit, offset=offset)
        assert result == [fix_run]
        mock_run_repo.get_by_user.assert_called_once_with(
            user_id, limit=limit, offset=offset
        )

    @pytest.mark.parametrize(
        ("library_id", "limit", "offset"),
        [
            (1, 50, 0),
            (2, 20, 10),
        ],
    )
    def test_get_runs_by_library(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        library_id: int,
        limit: int,
        offset: int,
    ) -> None:
        """Test get_runs_by_library with various parameters."""
        mock_run_repo.get_by_library.return_value = [fix_run]
        result = service.get_runs_by_library(
            library_id=library_id, limit=limit, offset=offset
        )
        assert result == [fix_run]
        mock_run_repo.get_by_library.assert_called_once_with(
            library_id, limit=limit, offset=offset
        )

    def test_get_incomplete_runs(
        self, service: EPUBFixerService, mock_run_repo: MagicMock, fix_run: EPUBFixRun
    ) -> None:
        """Test get_incomplete_runs delegates to repository."""
        fix_run.completed_at = None
        mock_run_repo.get_incomplete_runs.return_value = [fix_run]
        result = service.get_incomplete_runs()
        assert result == [fix_run]
        mock_run_repo.get_incomplete_runs.assert_called_once()


class TestEPUBFixerServiceStatistics:
    """Test statistics methods."""

    @pytest.mark.parametrize(
        ("user_id", "library_id"),
        [
            (None, None),
            (1, None),
            (None, 1),
            (1, 1),
        ],
    )
    def test_get_statistics(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        user_id: int | None,
        library_id: int | None,
    ) -> None:
        """Test get_statistics with various filters."""
        stats = {
            "total_runs": 10,
            "total_files_processed": 100,
            "total_files_fixed": 80,
            "total_fixes_applied": 150,
            "avg_files_per_run": 10.0,
            "avg_fixes_per_file": 1.875,
        }
        mock_run_repo.get_statistics.return_value = stats
        result = service.get_statistics(user_id=user_id, library_id=library_id)
        assert result == stats
        mock_run_repo.get_statistics.assert_called_once_with(
            user_id=user_id, library_id=library_id
        )

    @pytest.mark.parametrize(
        ("run_id", "book_id"),
        [
            (None, None),
            (1, None),
            (None, 100),
            (1, 100),
        ],
    )
    def test_get_fix_statistics_by_type(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        run_id: int | None,
        book_id: int | None,
    ) -> None:
        """Test get_fix_statistics_by_type with various filters."""
        stats = {"encoding": 5, "body_id_link": 3}
        mock_fix_repo.get_fix_statistics_by_type.return_value = stats
        result = service.get_fix_statistics_by_type(run_id=run_id, book_id=book_id)
        assert result == stats
        mock_fix_repo.get_fix_statistics_by_type.assert_called_once_with(
            run_id=run_id, book_id=book_id
        )

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
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        epub_fix: EPUBFix,
        limit: int,
        fix_type: EPUBFixType | None,
    ) -> None:
        """Test get_recent_fixes with various parameters."""
        mock_fix_repo.get_recent_fixes.return_value = [epub_fix]
        result = service.get_recent_fixes(limit=limit, fix_type=fix_type)
        assert result == [epub_fix]
        mock_fix_repo.get_recent_fixes.assert_called_once_with(
            limit=limit, fix_type=fix_type
        )


class TestEPUBFixerServiceShouldSkipEpub:
    """Test should_skip_epub method."""

    def test_should_skip_epub_already_fixed_recent(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub returns True for recently fixed EPUB."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=1)
        fix_run.completed_at = datetime.now(UTC)
        fix_run.error_message = None
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = fix_run

        result = service.should_skip_epub("/path/to/book.epub", skip_already_fixed=True)
        assert result is True

    def test_should_skip_epub_already_fixed_old(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub returns False for old fix (>30 days)."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=31)
        fix_run.completed_at = datetime.now(UTC) - timedelta(days=31)
        fix_run.error_message = None
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = fix_run

        result = service.should_skip_epub("/path/to/book.epub", skip_already_fixed=True)
        assert result is False

    def test_should_skip_epub_failed_recent(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub returns True for recently failed EPUB."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=1)
        fix_run.completed_at = datetime.now(UTC) - timedelta(days=1)
        fix_run.error_message = "Test error"
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = fix_run

        result = service.should_skip_epub("/path/to/book.epub", skip_failed=True)
        assert result is True

    def test_should_skip_epub_failed_old(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub returns False for old failure (>7 days)."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=8)
        fix_run.completed_at = datetime.now(UTC) - timedelta(days=8)
        fix_run.error_message = "Test error"
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = fix_run

        result = service.should_skip_epub("/path/to/book.epub", skip_failed=True)
        assert result is False

    def test_should_skip_epub_no_fixes(
        self, service: EPUBFixerService, mock_fix_repo: MagicMock
    ) -> None:
        """Test should_skip_epub returns False when no fixes found."""
        mock_fix_repo.get_by_file_path.return_value = []
        result = service.should_skip_epub("/path/to/book.epub")
        assert result is False

    def test_should_skip_epub_skip_disabled(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub returns False when skip flags are disabled."""
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        result = service.should_skip_epub(
            "/path/to/book.epub", skip_already_fixed=False, skip_failed=False
        )
        assert result is False

    def test_should_skip_epub_run_not_found(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub handles missing run."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=1)
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = None

        result = service.should_skip_epub("/path/to/book.epub", skip_already_fixed=True)
        assert result is False

    def test_should_skip_epub_run_not_completed(
        self,
        service: EPUBFixerService,
        mock_fix_repo: MagicMock,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
    ) -> None:
        """Test should_skip_epub handles run without completed_at."""
        epub_fix.applied_at = datetime.now(UTC) - timedelta(days=1)
        fix_run.completed_at = None
        fix_run.error_message = None
        mock_fix_repo.get_by_file_path.return_value = [epub_fix]
        mock_run_repo.get.return_value = fix_run

        result = service.should_skip_epub("/path/to/book.epub", skip_already_fixed=True)
        assert result is False


class TestEPUBFixerServiceProcessEpubFile:
    """Test process_epub_file method."""

    def test_process_epub_file_not_found(
        self, service: EPUBFixerService, tmp_path: Path
    ) -> None:
        """Test process_epub_file raises FileNotFoundError when file doesn't exist."""
        non_existent = tmp_path / "nonexistent.epub"
        with pytest.raises(FileNotFoundError, match="EPUB file not found"):
            service.process_epub_file(non_existent)

    def test_process_epub_file_with_config(
        self,
        service: EPUBFixerService,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test process_epub_file with existing config."""
        epub_file = tmp_path / "book.epub"
        epub_file.touch()

        # Create config
        config = EPUBFixerConfig(
            id=1,
            enabled=True,
            backup_enabled=True,
            default_language="en",
        )
        session.set_exec_result([config])

        with (
            patch("bookcard.services.epub_fixer.EPUBFixerOrchestrator") as mock_orch,
            patch("bookcard.services.epub_fixer.EPUBReader") as mock_reader,
            patch("bookcard.services.epub_fixer.EPUBWriter") as mock_writer,
            patch("bookcard.services.epub_fixer.BackupService") as mock_backup,
            patch("bookcard.services.epub_fixer.FixResultRecorder") as mock_recorder,
        ):
            # Setup mocks
            mock_orch_instance = MagicMock()
            mock_orch_instance.process.return_value = []
            mock_orch.return_value = mock_orch_instance

            mock_reader_instance = MagicMock()
            mock_reader_instance.read.return_value = MagicMock()
            mock_reader.return_value = mock_reader_instance

            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.create_backup.return_value = tmp_path / "backup.epub"
            mock_backup.return_value = mock_backup_instance

            mock_recorder_instance = MagicMock()
            mock_recorder.return_value = mock_recorder_instance

            # Create fix run
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            session.added.append(fix_run)

            result = service.process_epub_file(epub_file)

            assert result is not None

    def test_process_epub_file_without_config(
        self,
        service: EPUBFixerService,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test process_epub_file without config (creates default)."""
        epub_file = tmp_path / "book.epub"
        epub_file.touch()

        # No config
        session.set_exec_result([None])

        with (
            patch("bookcard.services.epub_fixer.EPUBFixerOrchestrator") as mock_orch,
            patch("bookcard.services.epub_fixer.EPUBReader") as mock_reader,
            patch("bookcard.services.epub_fixer.EPUBWriter") as mock_writer,
            patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class,
            patch("bookcard.services.epub_fixer.NullBackupService") as mock_null_backup,
            patch("bookcard.services.epub_fixer.FixResultRecorder") as mock_recorder,
        ):
            # Setup mocks
            mock_orch_instance = MagicMock()
            mock_orch_instance.process.return_value = []
            mock_orch.return_value = mock_orch_instance

            mock_reader_instance = MagicMock()
            mock_reader_instance.read.return_value = MagicMock()
            mock_reader.return_value = mock_reader_instance

            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.create_backup.return_value = None
            mock_backup_class.return_value = mock_backup_instance
            mock_null_backup.return_value = mock_backup_instance

            mock_recorder_instance = MagicMock()
            mock_recorder.return_value = mock_recorder_instance

            # Create fix run
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            session.added.append(fix_run)

            result = service.process_epub_file(epub_file)

            assert result is not None

    def test_process_epub_file_with_fixes(
        self,
        service: EPUBFixerService,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test process_epub_file with fixes applied."""
        epub_file = tmp_path / "book.epub"
        epub_file.touch()

        session.set_exec_result([None])

        with (
            patch("bookcard.services.epub_fixer.EPUBFixerOrchestrator") as mock_orch,
            patch("bookcard.services.epub_fixer.EPUBReader") as mock_reader,
            patch("bookcard.services.epub_fixer.EPUBWriter") as mock_writer,
            patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class,
            patch("bookcard.services.epub_fixer.NullBackupService") as mock_null_backup,
            patch("bookcard.services.epub_fixer.FixResultRecorder") as mock_recorder,
        ):
            # Setup mocks
            mock_fix_result = MagicMock()
            mock_orch_instance = MagicMock()
            mock_orch_instance.process.return_value = [mock_fix_result]
            mock_orch.return_value = mock_orch_instance

            mock_reader_instance = MagicMock()
            mock_contents = MagicMock()
            mock_reader_instance.read.return_value = mock_contents
            mock_reader.return_value = mock_reader_instance

            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.create_backup.return_value = None
            mock_backup_class.return_value = mock_backup_instance
            mock_null_backup.return_value = mock_backup_instance

            mock_recorder_instance = MagicMock()
            mock_recorder.return_value = mock_recorder_instance

            # Mock create_fix_run to return a fix_run with an id
            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            with patch.object(service, "create_fix_run", return_value=fix_run):
                result = service.process_epub_file(epub_file, book_title="Custom Title")

                assert result is not None
                mock_writer_instance.write.assert_called_once()
                mock_recorder_instance.record_fixes.assert_called_once()

    def test_process_epub_file_path_string(
        self,
        service: EPUBFixerService,
        session: DummySession,
        tmp_path: Path,
    ) -> None:
        """Test process_epub_file accepts string path."""
        epub_file = tmp_path / "book.epub"
        epub_file.touch()

        session.set_exec_result([None])

        with (
            patch("bookcard.services.epub_fixer.EPUBFixerOrchestrator") as mock_orch,
            patch("bookcard.services.epub_fixer.EPUBReader") as mock_reader,
            patch("bookcard.services.epub_fixer.EPUBWriter") as mock_writer,
            patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class,
            patch("bookcard.services.epub_fixer.NullBackupService") as mock_null_backup,
            patch("bookcard.services.epub_fixer.FixResultRecorder") as mock_recorder,
        ):
            mock_orch_instance = MagicMock()
            mock_orch_instance.process.return_value = []
            mock_orch.return_value = mock_orch_instance

            mock_reader_instance = MagicMock()
            mock_reader_instance.read.return_value = MagicMock()
            mock_reader.return_value = mock_reader_instance

            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.create_backup.return_value = None
            mock_backup_class.return_value = mock_backup_instance
            mock_null_backup.return_value = mock_backup_instance

            mock_recorder_instance = MagicMock()
            mock_recorder.return_value = mock_recorder_instance

            fix_run = EPUBFixRun(id=1, started_at=datetime.now(UTC))
            session.added.append(fix_run)

            result = service.process_epub_file(str(epub_file))

            assert result is not None


class TestEPUBFixerServiceRollbackFixRun:
    """Test rollback_fix_run method."""

    def test_rollback_fix_run_success(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
        session: DummySession,
    ) -> None:
        """Test rollback_fix_run successfully rolls back."""
        fix_run.completed_at = datetime.now(UTC) - timedelta(hours=1)
        epub_fix.original_file_path = "/backup/book.epub"
        epub_fix.backup_created = True

        mock_run_repo.get.return_value = fix_run
        mock_fix_repo.get_by_run.return_value = [epub_fix]

        with patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class:
            mock_backup_instance = MagicMock()
            mock_backup_instance.restore_backup.return_value = True
            mock_backup_class.return_value = mock_backup_instance

            result = service.rollback_fix_run(run_id=1)

            assert result.cancelled_at is not None
            assert result.error_message is not None
            assert "Rolled back" in result.error_message
            assert session.commit_count > 0

    def test_rollback_fix_run_not_found(
        self, service: EPUBFixerService, mock_run_repo: MagicMock
    ) -> None:
        """Test rollback_fix_run raises ValueError when run not found."""
        mock_run_repo.get.return_value = None

        with pytest.raises(ValueError, match="Fix run 999 not found"):
            service.rollback_fix_run(run_id=999)

    def test_rollback_fix_run_too_old(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        fix_run: EPUBFixRun,
    ) -> None:
        """Test rollback_fix_run raises ValueError when run is too old."""
        fix_run.completed_at = datetime.now(UTC) - timedelta(hours=25)
        mock_run_repo.get.return_value = fix_run

        with pytest.raises(
            ValueError, match=r"too old to rollback.*completed more than 24 hours ago"
        ):
            service.rollback_fix_run(run_id=1)

    def test_rollback_fix_run_no_backup(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
        session: DummySession,
    ) -> None:
        """Test rollback_fix_run handles fixes without backup."""
        fix_run.completed_at = datetime.now(UTC) - timedelta(hours=1)
        epub_fix.original_file_path = None
        epub_fix.backup_created = False

        mock_run_repo.get.return_value = fix_run
        mock_fix_repo.get_by_run.return_value = [epub_fix]

        with patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class:
            mock_backup_instance = MagicMock()
            mock_backup_class.return_value = mock_backup_instance

            result = service.rollback_fix_run(run_id=1)

            # Should still mark as cancelled even if no backups
            assert result.cancelled_at is not None

    def test_rollback_fix_run_restore_fails(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
        session: DummySession,
    ) -> None:
        """Test rollback_fix_run handles restore failures."""
        fix_run.completed_at = datetime.now(UTC) - timedelta(hours=1)
        epub_fix.original_file_path = "/backup/book.epub"
        epub_fix.backup_created = True

        mock_run_repo.get.return_value = fix_run
        mock_fix_repo.get_by_run.return_value = [epub_fix]

        with patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class:
            mock_backup_instance = MagicMock()
            mock_backup_instance.restore_backup.side_effect = OSError("Restore failed")
            mock_backup_class.return_value = mock_backup_instance

            result = service.rollback_fix_run(run_id=1)

            # Should still mark as cancelled
            assert result.cancelled_at is not None

    def test_rollback_fix_run_restore_value_error(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
        session: DummySession,
    ) -> None:
        """Test rollback_fix_run handles ValueError during restore."""
        fix_run.completed_at = datetime.now(UTC) - timedelta(hours=1)
        epub_fix.original_file_path = "/backup/book.epub"
        epub_fix.backup_created = True

        mock_run_repo.get.return_value = fix_run
        mock_fix_repo.get_by_run.return_value = [epub_fix]

        with patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class:
            mock_backup_instance = MagicMock()
            mock_backup_instance.restore_backup.side_effect = ValueError("Invalid path")
            mock_backup_class.return_value = mock_backup_instance

            result = service.rollback_fix_run(run_id=1)

            # Should still mark as cancelled
            assert result.cancelled_at is not None

    def test_rollback_fix_run_not_completed(
        self,
        service: EPUBFixerService,
        mock_run_repo: MagicMock,
        mock_fix_repo: MagicMock,
        fix_run: EPUBFixRun,
        epub_fix: EPUBFix,
        session: DummySession,
    ) -> None:
        """Test rollback_fix_run handles run without completed_at."""
        fix_run.completed_at = None
        epub_fix.original_file_path = "/backup/book.epub"
        epub_fix.backup_created = True

        mock_run_repo.get.return_value = fix_run
        mock_fix_repo.get_by_run.return_value = [epub_fix]

        with patch("bookcard.services.epub_fixer.BackupService") as mock_backup_class:
            mock_backup_instance = MagicMock()
            mock_backup_instance.restore_backup.return_value = True
            mock_backup_class.return_value = mock_backup_instance

            # Should not raise error, just proceed with rollback
            result = service.rollback_fix_run(run_id=1)
            assert result.cancelled_at is not None

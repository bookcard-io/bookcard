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

"""Tests for ReadingService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from bookcard.models.reading import (
    ReadingProgress,
    ReadingSession,
    ReadStatus,
    ReadStatusEnum,
)
from bookcard.repositories.reading_repository import (
    AnnotationRepository,
    ReadingProgressRepository,
    ReadingSessionRepository,
    ReadStatusRepository,
)
from bookcard.services.reading_service import ReadingService

if TYPE_CHECKING:
    from tests.conftest import DummySession
else:
    from tests.conftest import DummySession  # noqa: TC001


@pytest.fixture
def progress_repo(session: DummySession) -> ReadingProgressRepository:
    """Create ReadingProgressRepository instance."""
    return ReadingProgressRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def session_repo(session: DummySession) -> ReadingSessionRepository:
    """Create ReadingSessionRepository instance."""
    return ReadingSessionRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def status_repo(session: DummySession) -> ReadStatusRepository:
    """Create ReadStatusRepository instance."""
    return ReadStatusRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def annotation_repo(session: DummySession) -> AnnotationRepository:
    """Create AnnotationRepository instance."""
    return AnnotationRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def reading_service(
    session: DummySession,
    progress_repo: ReadingProgressRepository,
    session_repo: ReadingSessionRepository,
    status_repo: ReadStatusRepository,
    annotation_repo: AnnotationRepository,
) -> ReadingService:
    """Create ReadingService instance."""
    return ReadingService(
        session,  # type: ignore[arg-type]
        progress_repo,
        session_repo,
        status_repo,
        annotation_repo,
    )


class TestUpdateProgress:
    """Test update_progress method."""

    def test_update_progress_create_new(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress creates new progress when none exists."""
        session.set_exec_result([])  # get_by_user_book_format returns None
        session.add_exec_result([])  # get_by_user_book for status returns None
        result = reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.5,
        )
        assert result.progress == 0.5
        assert result.user_id == 1
        assert result.book_id == 1
        assert result.format == "EPUB"
        assert result in session.added

    def test_update_progress_update_existing(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress updates existing progress."""
        existing = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.3,
        )
        session.set_exec_result([existing])
        session.add_exec_result([])  # get_by_user_book for first_opened check
        result = reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.7,
        )
        assert result.progress == 0.7
        assert result.id == 1

    def test_update_progress_with_cfi(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress with CFI."""
        session.set_exec_result([])
        session.add_exec_result([])  # get_by_user_book for first_opened check
        result = reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.5,
            cfi="epubcfi(/6/4[chap01ref]!/4/2/2[para05]/3:0)",
        )
        assert result.cfi == "epubcfi(/6/4[chap01ref]!/4/2/2[para05]/3:0)"

    def test_update_progress_with_page_number(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress with page number."""
        session.set_exec_result([])
        session.add_exec_result([])  # get_by_user_book for first_opened check
        result = reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="PDF",
            progress=0.5,
            page_number=50,
        )
        assert result.page_number == 50

    def test_update_progress_auto_mark_at_90(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress auto-marks as read at 90%."""
        session.set_exec_result([])  # No existing progress
        session.add_exec_result([])  # No existing status
        session.add_exec_result([])  # get_by_user_book for first_opened check
        result = reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.90,
        )
        assert result.progress == 0.90
        # Check that auto-mark was called (status should be created)
        assert len(session.added) > 0

    def test_update_progress_invalid_range(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress raises ValueError for invalid progress."""
        with pytest.raises(ValueError, match=r"Progress must be between 0.0 and 1.0"):
            reading_service.update_progress(
                user_id=1,
                library_id=1,
                book_id=1,
                book_format="EPUB",
                progress=1.5,
            )

    def test_update_progress_sets_first_opened(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test update_progress sets first_opened_at when progress > 0."""
        session.set_exec_result([])  # No existing progress
        session.add_exec_result([])  # No existing status
        reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.1,
        )
        # Check that first_opened_at was set
        assert len(session.added) > 0


class TestStartSession:
    """Test start_session method."""

    def test_start_session_creates_new(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test start_session creates new session."""
        session.set_exec_result([])  # No existing progress
        session.add_exec_result([])  # No existing status
        result = reading_service.start_session(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
        )
        assert result.user_id == 1
        assert result.book_id == 1
        assert result.format == "EPUB"
        assert result.progress_start == 0.0
        assert result.ended_at is None
        assert result in session.added

    def test_start_session_with_existing_progress(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test start_session uses existing progress."""
        existing_progress = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.5,
        )
        session.set_exec_result([existing_progress])
        session.add_exec_result([])  # No existing status
        result = reading_service.start_session(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
        )
        assert result.progress_start == 0.5


class TestEndSession:
    """Test end_session method."""

    def test_end_session_success(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test end_session ends a session successfully."""
        session_obj = ReadingSession(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            started_at=datetime.now(UTC),
            progress_start=0.3,
        )
        session._entities_by_class_and_id[ReadingSession] = {1: session_obj}
        # Mock the ReadStatus query that happens in _auto_mark_as_read
        session.add_exec_result([])  # No existing ReadStatus
        result = reading_service.end_session(session_id=1, progress_end=0.7)
        assert result.ended_at is not None
        assert result.progress_end == 0.7

    def test_end_session_not_found(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test end_session raises ValueError when session not found."""
        session._entities_by_class_and_id[ReadingSession] = {}
        with pytest.raises(ValueError, match="Reading session 999 not found"):
            reading_service.end_session(session_id=999, progress_end=0.7)

    def test_end_session_already_ended(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test end_session raises ValueError when already ended."""
        session_obj = ReadingSession(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            progress_start=0.3,
            progress_end=0.5,
        )
        session._entities_by_class_and_id[ReadingSession] = {1: session_obj}
        with pytest.raises(ValueError, match="Reading session 1 is already ended"):
            reading_service.end_session(session_id=1, progress_end=0.7)

    def test_end_session_auto_mark_at_90(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test end_session auto-marks as read at 90%."""
        session_obj = ReadingSession(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            started_at=datetime.now(UTC),
            progress_start=0.5,
        )
        session._entities_by_class_and_id[ReadingSession] = {1: session_obj}
        session.set_exec_result([])  # No existing status
        result = reading_service.end_session(session_id=1, progress_end=0.90)
        assert result.progress_end == 0.90


class TestMarkAsRead:
    """Test mark_as_read method."""

    def test_mark_as_read_create_new(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test mark_as_read creates new status."""
        session.set_exec_result([])  # No existing status
        session.add_exec_result([])  # No existing progress
        result = reading_service.mark_as_read(
            user_id=1,
            library_id=1,
            book_id=1,
            manual=True,
        )
        assert result.status == ReadStatusEnum.READ
        assert result.auto_marked is False
        assert result.marked_as_read_at is not None

    def test_mark_as_read_update_existing(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test mark_as_read updates existing status."""
        existing = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READING,
        )
        # First query: get_by_user_book_format (for ReadingProgress) - returns None
        session.set_exec_result([])  # No existing progress
        # Second query: get_by_user_book (for ReadStatus) - returns existing
        session.add_exec_result([existing])
        result = reading_service.mark_as_read(
            user_id=1,
            library_id=1,
            book_id=1,
            manual=True,
        )
        assert result.status == ReadStatusEnum.READ
        assert result.auto_marked is False


class TestMarkAsUnread:
    """Test mark_as_unread method."""

    def test_mark_as_unread_create_new(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test mark_as_unread creates new status."""
        session.set_exec_result([])
        result = reading_service.mark_as_unread(
            user_id=1,
            library_id=1,
            book_id=1,
        )
        assert result.status == ReadStatusEnum.NOT_READ
        assert result.marked_as_read_at is None
        assert result.auto_marked is False

    def test_mark_as_unread_update_existing(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test mark_as_unread updates existing status."""
        existing = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READ,
            marked_as_read_at=datetime.now(UTC),
            auto_marked=True,
            progress_when_marked=0.90,
        )
        session.set_exec_result([existing])
        result = reading_service.mark_as_unread(
            user_id=1,
            library_id=1,
            book_id=1,
        )
        assert result.status == ReadStatusEnum.NOT_READ
        assert result.marked_as_read_at is None
        assert result.auto_marked is False
        assert result.progress_when_marked is None


class TestGetProgress:
    """Test get_progress method."""

    def test_get_progress_found(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_progress returns progress when found."""
        progress = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.5,
        )
        session.set_exec_result([progress])
        result = reading_service.get_progress(1, 1, 1, "EPUB")
        assert result == progress

    def test_get_progress_not_found(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_progress returns None when not found."""
        session.set_exec_result([])
        result = reading_service.get_progress(1, 1, 1, "EPUB")
        assert result is None


class TestGetRecentReads:
    """Test get_recent_reads method."""

    def test_get_recent_reads(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_recent_reads returns recent reads."""
        reads = [
            ReadingProgress(
                id=i,
                user_id=1,
                library_id=1,
                book_id=i,
                book_format="EPUB",
                progress=0.5,
            )
            for i in range(1, 6)
        ]
        session.set_exec_result(reads)
        result = reading_service.get_recent_reads(1, 1, limit=5)
        assert len(result) == 5


class TestGetReadingHistory:
    """Test get_reading_history method."""

    def test_get_reading_history(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_reading_history returns sessions."""
        sessions = [
            ReadingSession(
                id=i,
                user_id=1,
                library_id=1,
                book_id=1,
                book_format="EPUB",
                started_at=datetime.now(UTC),
                progress_start=0.1 * i,
            )
            for i in range(1, 6)
        ]
        session.set_exec_result(sessions)
        result = reading_service.get_reading_history(1, 1, 1, limit=5)
        assert len(result) == 5


class TestGetReadStatus:
    """Test get_read_status method."""

    def test_get_read_status_found(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_read_status returns status when found."""
        status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READ,
        )
        session.set_exec_result([status])
        result = reading_service.get_read_status(1, 1, 1)
        assert result == status

    def test_get_read_status_not_found(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test get_read_status returns None when not found."""
        session.set_exec_result([])
        result = reading_service.get_read_status(1, 1, 1)
        assert result is None


class TestUpdateProgressOptionalParams:
    """Test update_progress with optional parameters on existing progress."""

    @pytest.mark.parametrize(
        ("param_name", "param_value", "expected_attr"),
        [
            ("cfi", "epubcfi(/6/4[chap01ref]!/4/2/2[para05]/3:0)", "cfi"),
            ("page_number", 50, "page_number"),
            ("device", "kindle-123", "device"),
        ],
    )
    def test_update_progress_existing_with_optional_params(
        self,
        reading_service: ReadingService,
        session: DummySession,
        param_name: str,
        param_value: str | int,
        expected_attr: str,
    ) -> None:
        """Test update_progress updates existing progress with optional params."""
        existing = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.3,
        )
        session.set_exec_result([existing])
        session.add_exec_result([])  # get_by_user_book for first_opened check

        # Call with appropriate parameter based on param_name to satisfy type checker
        if param_name == "cfi":
            result = reading_service.update_progress(
                user_id=1,
                library_id=1,
                book_id=1,
                book_format="EPUB",
                progress=0.7,
                cfi=str(param_value),
            )
        elif param_name == "page_number":
            result = reading_service.update_progress(
                user_id=1,
                library_id=1,
                book_id=1,
                book_format="EPUB",
                progress=0.7,
                page_number=int(param_value),
            )
        else:  # device
            result = reading_service.update_progress(
                user_id=1,
                library_id=1,
                book_id=1,
                book_format="EPUB",
                progress=0.7,
                device=str(param_value),
            )
        assert getattr(result, expected_attr) == param_value


class TestEndSessionInvalidProgress:
    """Test end_session with invalid progress values."""

    @pytest.mark.parametrize(
        ("progress_end", "expected_error"),
        [
            (-0.1, "Progress must be between 0.0 and 1.0, got -0.1"),
            (1.5, "Progress must be between 0.0 and 1.0, got 1.5"),
        ],
    )
    def test_end_session_invalid_progress_range(
        self,
        reading_service: ReadingService,
        session: DummySession,
        progress_end: float,
        expected_error: str,
    ) -> None:
        """Test end_session raises ValueError for invalid progress."""
        with pytest.raises(ValueError, match=expected_error):
            reading_service.end_session(session_id=1, progress_end=progress_end)


class TestMarkAsReadWithProgress:
    """Test mark_as_read with existing progress."""

    def test_mark_as_read_update_existing_with_progress(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test mark_as_read updates existing status with progress_when_marked."""
        existing_progress = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.75,
        )
        existing_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READING,
        )
        # First query: get_by_user_book_format (for ReadingProgress) - returns progress
        session.set_exec_result([existing_progress])
        # Second query: get_by_user_book (for ReadStatus) - returns existing
        session.add_exec_result([existing_status])
        result = reading_service.mark_as_read(
            user_id=1,
            library_id=1,
            book_id=1,
            manual=True,
        )
        assert result.status == ReadStatusEnum.READ
        assert result.auto_marked is False
        assert result.progress_when_marked == 0.75


class TestAutoMarkAsRead:
    """Test _auto_mark_as_read method edge cases."""

    def test_auto_mark_as_read_existing_not_read(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test _auto_mark_as_read updates existing status that is not READ."""
        existing_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READING,
        )
        # Call through update_progress to trigger auto-mark
        # Query order: 1) get_by_user_book_format (for progress), 2) get_by_user_book (for auto-mark), 3) get_by_user_book (for first_opened)
        session.set_exec_result([])  # get_by_user_book_format returns None (no existing progress)
        session.add_exec_result([
            existing_status
        ])  # get_by_user_book for auto-mark returns existing status
        session.add_exec_result([
            existing_status
        ])  # get_by_user_book for first_opened returns existing status
        reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.95,
        )
        assert existing_status.status == ReadStatusEnum.READ
        assert existing_status.auto_marked is True
        assert existing_status.progress_when_marked == 0.95
        assert existing_status.marked_as_read_at is not None


class TestEnsureFirstOpened:
    """Test _ensure_first_opened method edge cases."""

    def test_ensure_first_opened_existing_no_first_opened_not_read(
        self,
        reading_service: ReadingService,
        session: DummySession,
    ) -> None:
        """Test _ensure_first_opened sets first_opened_at and updates status."""
        existing_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.NOT_READ,
            first_opened_at=None,
        )
        # Query order: 1) get_by_user_book_format (for progress), 2) get_by_user_book (for first_opened)
        session.set_exec_result([])  # get_by_user_book_format returns None (no existing progress)
        session.add_exec_result([
            existing_status
        ])  # get_by_user_book for first_opened returns existing
        reading_service.update_progress(
            user_id=1,
            library_id=1,
            book_id=1,
            book_format="EPUB",
            progress=0.1,
        )
        assert existing_status.first_opened_at is not None
        assert existing_status.status == ReadStatusEnum.READING

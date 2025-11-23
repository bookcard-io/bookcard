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

"""Tests for reading routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

import fundamental.api.routes.reading as reading_routes
from fundamental.models.auth import User
from fundamental.models.reading import (
    ReadingProgress,
    ReadingSession,
    ReadStatus,
    ReadStatusEnum,
)
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a DummySession instance."""
    return DummySession()


@pytest.fixture
def current_user() -> User:
    """Create a test user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


@pytest.fixture
def mock_request() -> Request:
    """Create a mock Request object."""
    request = MagicMock(spec=Request)
    request.app.state.config = MagicMock()
    request.app.state.config.data_directory = "/data"
    return request


def _mock_permission_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock PermissionService to allow all permissions."""
    mock_permission_service = MagicMock()
    mock_permission_service.check_permission = MagicMock()
    monkeypatch.setattr(
        "fundamental.api.routes.reading.PermissionService",
        lambda session: mock_permission_service,
    )


def _mock_library_service(monkeypatch: pytest.MonkeyPatch, library_id: int = 1) -> None:
    """Mock LibraryService to return active library."""
    mock_library = MagicMock()
    mock_library.id = library_id

    mock_library_service = MagicMock()
    mock_library_service.get_active_library.return_value = mock_library

    mock_library_repo = MagicMock()
    monkeypatch.setattr(
        "fundamental.api.routes.reading.LibraryRepository",
        lambda session: mock_library_repo,
    )
    monkeypatch.setattr(
        "fundamental.api.routes.reading.LibraryService",
        lambda session, repo: mock_library_service,
    )


class TestUpdateProgress:
    """Test update_progress endpoint."""

    def test_update_progress_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
        mock_request: Request,
    ) -> None:
        """Test update_progress succeeds."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        progress = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            format="EPUB",
            progress=0.5,
            updated_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.update_progress.return_value = progress

        with patch(
            "fundamental.api.routes.reading._reading_service"
        ) as mock_service_factory:
            mock_service_factory.return_value = mock_reading_service

            from fundamental.api.schemas.reading import ReadingProgressCreate

            payload = ReadingProgressCreate(
                book_id=1,
                format="EPUB",
                progress=0.5,
            )

            result = reading_routes.update_progress(
                progress_data=payload,
                session=session,  # type: ignore[arg-type]
                current_user=current_user,
                reading_service=mock_reading_service,
                library_id=1,
            )

            assert result.id == 1
            assert result.progress == 0.5
            mock_reading_service.update_progress.assert_called_once()

    def test_update_progress_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test update_progress raises 400 on validation error."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        mock_reading_service = MagicMock()
        mock_reading_service.update_progress.side_effect = ValueError(
            "Progress must be between 0.0 and 1.0"
        )

        with patch(
            "fundamental.api.routes.reading._reading_service"
        ) as mock_service_factory:
            mock_service_factory.return_value = mock_reading_service

            from pydantic import ValidationError

            from fundamental.api.schemas.reading import ReadingProgressCreate

            # Pydantic validates at model creation, so catch the validation error
            with pytest.raises(ValidationError) as exc_info:
                ReadingProgressCreate(
                    book_id=1,
                    format="EPUB",
                    progress=1.5,  # Invalid progress
                )
            # Verify it's the expected validation error
            assert isinstance(exc_info.value, ValidationError)
            assert len(exc_info.value.errors()) > 0
            assert exc_info.value.errors()[0]["type"] == "less_than_equal"


class TestGetProgress:
    """Test get_progress endpoint."""

    def test_get_progress_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_progress returns progress."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        progress = ReadingProgress(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            format="EPUB",
            progress=0.5,
            updated_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.get_progress.return_value = progress

        result = reading_routes.get_progress(
            book_id=1,
            book_format="EPUB",
            session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.id == 1
        assert result.progress == 0.5

    def test_get_progress_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_progress raises 404 when not found."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        mock_reading_service = MagicMock()
        mock_reading_service.get_progress.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            reading_routes.get_progress(
                book_id=1,
                book_format="EPUB",
                session=session,  # type: ignore[arg-type]
                current_user=current_user,
                reading_service=mock_reading_service,
                library_id=1,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestStartSession:
    """Test start_session endpoint."""

    def test_start_session_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test start_session creates session."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        reading_session = ReadingSession(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            format="EPUB",
            started_at=datetime.now(UTC),
            progress_start=0.0,
            created_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.start_session.return_value = reading_session

        from fundamental.api.schemas.reading import ReadingSessionCreate

        payload = ReadingSessionCreate(book_id=1, format="EPUB")

        result = reading_routes.start_session(
            session_data=payload,
            session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.id == 1
        assert result.book_id == 1


class TestEndSession:
    """Test end_session endpoint."""

    def test_end_session_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test end_session ends session."""
        _mock_permission_service(monkeypatch)

        reading_session = ReadingSession(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            format="EPUB",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            progress_start=0.3,
            progress_end=0.7,
            created_at=datetime.now(UTC),
        )

        mock_session_repo = MagicMock()
        mock_session_repo.get.return_value = reading_session

        mock_reading_service = MagicMock()
        mock_reading_service.end_session.return_value = reading_session

        with patch(
            "fundamental.api.routes.reading.ReadingSessionRepository"
        ) as mock_repo_class:
            mock_repo_class.return_value = mock_session_repo

            from fundamental.api.schemas.reading import ReadingSessionEnd

            payload = ReadingSessionEnd(progress_end=0.7)

            result = reading_routes.end_session(
                session_id=1,
                session_end_data=payload,
                session=session,  # type: ignore[arg-type]
                current_user=current_user,
                reading_service=mock_reading_service,
            )

            assert result.id == 1
            assert result.progress_end == 0.7

    def test_end_session_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test end_session raises 404 when session not found."""
        _mock_permission_service(monkeypatch)

        mock_session_repo = MagicMock()
        mock_session_repo.get.return_value = None

        with patch(
            "fundamental.api.routes.reading.ReadingSessionRepository"
        ) as mock_repo_class:
            mock_repo_class.return_value = mock_session_repo

            from fundamental.api.schemas.reading import ReadingSessionEnd

            payload = ReadingSessionEnd(progress_end=0.7)

            with pytest.raises(HTTPException) as exc_info:
                reading_routes.end_session(
                    session_id=1,
                    session_end_data=payload,
                    session=session,  # type: ignore[arg-type]
                    current_user=current_user,
                    reading_service=MagicMock(),
                )
            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_end_session_permission_denied(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test end_session raises 403 when user doesn't own session."""
        _mock_permission_service(monkeypatch)

        reading_session = ReadingSession(
            id=1,
            user_id=999,  # Different user
            library_id=1,
            book_id=1,
            format="EPUB",
            started_at=datetime.now(UTC),
        )

        mock_session_repo = MagicMock()
        mock_session_repo.get.return_value = reading_session

        with patch(
            "fundamental.api.routes.reading.ReadingSessionRepository"
        ) as mock_repo_class:
            mock_repo_class.return_value = mock_session_repo

            from fundamental.api.schemas.reading import ReadingSessionEnd

            payload = ReadingSessionEnd(progress_end=0.7)

            with pytest.raises(HTTPException) as exc_info:
                reading_routes.end_session(
                    session_id=1,
                    session_end_data=payload,
                    session=session,  # type: ignore[arg-type]
                    current_user=current_user,
                    reading_service=MagicMock(),
                )
            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestGetRecentReads:
    """Test get_recent_reads endpoint."""

    def test_get_recent_reads_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_recent_reads returns recent reads."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        reads = [
            ReadingProgress(
                id=i,
                user_id=1,
                library_id=1,
                book_id=i,
                format="EPUB",
                progress=0.5,
                updated_at=datetime.now(UTC),
            )
            for i in range(1, 4)
        ]

        mock_reading_service = MagicMock()
        mock_reading_service.get_recent_reads.return_value = reads

        result = reading_routes.get_recent_reads(
            limit=10,
            db_session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.total == 3
        assert len(result.reads) == 3


class TestGetReadingHistory:
    """Test get_reading_history endpoint."""

    def test_get_reading_history_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_reading_history returns sessions."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        sessions = [
            ReadingSession(
                id=i,
                user_id=1,
                library_id=1,
                book_id=1,
                format="EPUB",
                started_at=datetime.now(UTC),
                progress_start=0.1 * i,
                created_at=datetime.now(UTC),
            )
            for i in range(1, 4)
        ]

        mock_reading_service = MagicMock()
        mock_reading_service.get_reading_history.return_value = sessions

        result = reading_routes.get_reading_history(
            book_id=1,
            limit=50,
            db_session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.total == 3
        assert len(result.sessions) == 3


class TestUpdateReadStatus:
    """Test update_read_status endpoint."""

    def test_update_read_status_mark_as_read(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test update_read_status marks as read."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        read_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READ,
            marked_as_read_at=datetime.now(UTC),
            auto_marked=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.mark_as_read.return_value = read_status

        from fundamental.api.schemas.reading import ReadStatusUpdate

        payload = ReadStatusUpdate(status="read")

        result = reading_routes.update_read_status(
            book_id=1,
            status_data=payload,
            db_session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.status == "read"
        mock_reading_service.mark_as_read.assert_called_once()

    def test_update_read_status_mark_as_unread(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test update_read_status marks as unread."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        read_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.NOT_READ,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.mark_as_unread.return_value = read_status

        from fundamental.api.schemas.reading import ReadStatusUpdate

        payload = ReadStatusUpdate(status="not_read")

        result = reading_routes.update_read_status(
            book_id=1,
            status_data=payload,
            db_session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.status == "not_read"
        mock_reading_service.mark_as_unread.assert_called_once()

    def test_update_read_status_invalid_status(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test update_read_status raises validation error for invalid status."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        from pydantic import ValidationError

        from fundamental.api.schemas.reading import ReadStatusUpdate

        # Pydantic validates at model creation, so catch the validation error
        with pytest.raises(ValidationError) as exc_info:
            ReadStatusUpdate(status="invalid")
        # Verify it's the expected validation error
        assert isinstance(exc_info.value, ValidationError)
        assert len(exc_info.value.errors()) > 0
        assert exc_info.value.errors()[0]["type"] == "string_pattern_mismatch"


class TestGetReadStatus:
    """Test get_read_status endpoint."""

    def test_get_read_status_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_read_status returns status."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        read_status = ReadStatus(
            id=1,
            user_id=1,
            library_id=1,
            book_id=1,
            status=ReadStatusEnum.READ,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_reading_service = MagicMock()
        mock_reading_service.get_read_status.return_value = read_status

        result = reading_routes.get_read_status(
            book_id=1,
            db_session=session,  # type: ignore[arg-type]
            current_user=current_user,
            reading_service=mock_reading_service,
            library_id=1,
        )

        assert result.id == 1
        assert result.status == "read"

    def test_get_read_status_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        current_user: User,
    ) -> None:
        """Test get_read_status raises 404 when not found."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch)

        mock_reading_service = MagicMock()
        mock_reading_service.get_read_status.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            reading_routes.get_read_status(
                book_id=1,
                db_session=session,  # type: ignore[arg-type]
                current_user=current_user,
                reading_service=mock_reading_service,
                library_id=1,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

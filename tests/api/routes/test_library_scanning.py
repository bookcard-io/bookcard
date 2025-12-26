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

"""Tests for library_scanning routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

import bookcard.api.routes.library_scanning as library_scanning
from bookcard.models.auth import User
from bookcard.models.library_scanning import LibraryScanState

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def admin_user() -> User:
    """Create an admin user."""
    return User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def mock_request() -> Request:
    """Create a mock Request with app state."""
    request = MagicMock(spec=Request)
    request.app.state = MagicMock()
    return request


class TestScanLibrary:
    """Test scan_library endpoint."""

    def test_scan_library_success(
        self,
        session: DummySession,
        admin_user: User,
        mock_request: Request,
    ) -> None:
        """Test scan_library succeeds (covers lines 95-130)."""
        mock_task_runner = MagicMock()
        mock_request.app.state.task_runner = mock_task_runner
        mock_task_runner.enqueue.return_value = 123

        request_data = library_scanning.ScanRequest(
            library_id=1,
            data_source_config={"name": "openlibrary", "kwargs": {}},
        )

        result = library_scanning.scan_library(
            request=request_data,
            http_request=mock_request,
            session=session,
            current_user=admin_user,
        )

        assert result.task_id == 123
        assert "Library scan job for library 1" in result.message

        # Verify call to task runner
        mock_task_runner.enqueue.assert_called_once()
        call_kwargs = mock_task_runner.enqueue.call_args[1]
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["metadata"]["library_id"] == 1
        assert call_kwargs["metadata"]["data_source_config"] == {
            "name": "openlibrary",
            "kwargs": {},
        }
        assert call_kwargs["metadata"]["task_type"] == "library_scan"

    def test_scan_library_without_data_source_config(
        self,
        session: DummySession,
        admin_user: User,
        mock_request: Request,
    ) -> None:
        """Test scan_library without data_source_config."""
        mock_task_runner = MagicMock()
        mock_request.app.state.task_runner = mock_task_runner
        mock_task_runner.enqueue.return_value = 123

        request_data = library_scanning.ScanRequest(library_id=1)

        result = library_scanning.scan_library(
            request=request_data,
            http_request=mock_request,
            session=session,
            current_user=admin_user,
        )

        assert result.task_id == 123

        # Verify default config usage
        mock_task_runner.enqueue.assert_called_once()
        call_kwargs = mock_task_runner.enqueue.call_args[1]
        assert call_kwargs["metadata"]["data_source_config"] == {
            "name": "openlibrary",
            "kwargs": {},
        }

    def test_scan_library_task_runner_not_available(
        self,
        session: DummySession,
        admin_user: User,
        mock_request: Request,
    ) -> None:
        """Test scan_library raises 503 when task runner not available."""
        # Ensure task_runner is not present or None
        mock_request.app.state.task_runner = None
        # Or if getattr defaults to None, simply not setting it might work depending on how mock_request is set up
        # The fixture sets app.state = MagicMock(), so getattr(..., "task_runner", None) will return the MagicMock attribute if accessed,
        # unless we explicitly delete it or set it to None.

        # Since app.state is a MagicMock, accessing .task_runner creates a new MagicMock by default.
        # We must explicitly set it to None to simulate missing service.
        del mock_request.app.state.task_runner

        request_data = library_scanning.ScanRequest(library_id=1)

        with pytest.raises(HTTPException) as exc_info:
            library_scanning.scan_library(
                request=request_data,
                http_request=mock_request,
                session=session,
                current_user=admin_user,
            )

        assert isinstance(exc_info.value, HTTPException)
        exc = exc_info.value
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Task runner not available" in exc.detail

    def test_scan_library_value_error(
        self,
        session: DummySession,
        admin_user: User,
        mock_request: Request,
    ) -> None:
        """Test scan_library handles ValueError."""
        mock_task_runner = MagicMock()
        mock_request.app.state.task_runner = mock_task_runner
        mock_task_runner.enqueue.side_effect = ValueError("Invalid library")

        request_data = library_scanning.ScanRequest(library_id=999)

        with pytest.raises(HTTPException) as exc_info:
            library_scanning.scan_library(
                request=request_data,
                http_request=mock_request,
                session=session,
                current_user=admin_user,
            )

        assert isinstance(exc_info.value, HTTPException)
        exc = exc_info.value
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == "Invalid library"

    def test_scan_library_generic_exception(
        self,
        session: DummySession,
        admin_user: User,
        mock_request: Request,
    ) -> None:
        """Test scan_library handles generic exceptions."""
        mock_task_runner = MagicMock()
        mock_request.app.state.task_runner = mock_task_runner
        mock_task_runner.enqueue.side_effect = RuntimeError("Unexpected error")

        request_data = library_scanning.ScanRequest(library_id=1)

        with pytest.raises(HTTPException) as exc_info:
            library_scanning.scan_library(
                request=request_data,
                http_request=mock_request,
                session=session,
                current_user=admin_user,
            )

        assert isinstance(exc_info.value, HTTPException)
        exc = exc_info.value
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to initiate scan" in exc.detail


class TestGetScanState:
    """Test get_scan_state endpoint."""

    def test_get_scan_state_success(
        self,
        session: DummySession,
        admin_user: User,
    ) -> None:
        """Test get_scan_state returns state when found (covers lines 162-172)."""
        scan_state = LibraryScanState(
            library_id=1,
            scan_status="completed",
            last_scan_at=datetime.now(UTC),
            books_scanned=100,
            authors_scanned=50,
        )

        with patch(
            "bookcard.api.routes.library_scanning.LibraryScanningService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_scan_state.return_value = scan_state
            mock_service_class.return_value = mock_service

            result = library_scanning.get_scan_state(
                library_id=1,
                session=session,
                _current_user=admin_user,
            )

            assert result is not None
            assert result.library_id == 1
            assert result.scan_status == "completed"
            assert result.books_scanned == 100
            assert result.authors_scanned == 50
            assert result.last_scan_at is not None

    def test_get_scan_state_not_found(
        self,
        session: DummySession,
        admin_user: User,
    ) -> None:
        """Test get_scan_state returns None when not found."""
        with patch(
            "bookcard.api.routes.library_scanning.LibraryScanningService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_scan_state.return_value = None
            mock_service_class.return_value = mock_service

            result = library_scanning.get_scan_state(
                library_id=999,
                session=session,
                _current_user=admin_user,
            )

            assert result is None

    def test_get_scan_state_without_last_scan_at(
        self,
        session: DummySession,
        admin_user: User,
    ) -> None:
        """Test get_scan_state handles None last_scan_at."""
        scan_state = LibraryScanState(
            library_id=1,
            scan_status="pending",
            last_scan_at=None,
            books_scanned=0,
            authors_scanned=0,
        )

        with patch(
            "bookcard.api.routes.library_scanning.LibraryScanningService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_scan_state.return_value = scan_state
            mock_service_class.return_value = mock_service

            result = library_scanning.get_scan_state(
                library_id=1,
                session=session,
                _current_user=admin_user,
            )

            assert result is not None
            assert result.last_scan_at is None

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

"""Tests for EPUB fixer routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

import fundamental.api.routes.epub_fixer as epub_fixer_routes
from fundamental.api.schemas.epub_fixer import (
    EPUBFixBatchRequest,
    EPUBFixSingleRequest,
)
from fundamental.models.auth import User
from fundamental.models.epub_fixer import EPUBFix, EPUBFixRun, EPUBFixType
from tests.conftest import DummySession


@pytest.fixture
def mock_user() -> User:
    """Create a mock user for testing.

    Returns
    -------
    User
        Mock user instance.
    """
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


@pytest.fixture
def admin_user() -> User:
    """Create a mock admin user for testing.

    Returns
    -------
    User
        Mock admin user instance.
    """
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock request with task runner.

    Returns
    -------
    MagicMock
        Mock request object.
    """
    request = MagicMock(spec=Request)
    request.app.state.task_runner = MagicMock()
    return request


@pytest.fixture
def mock_request_no_task_runner() -> MagicMock:
    """Create a mock request without task runner.

    Returns
    -------
    MagicMock
        Mock request object without task_runner.
    """
    request = MagicMock(spec=Request)
    request.app.state = MagicMock()
    delattr(request.app.state, "task_runner")
    return request


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


# ==================== _get_task_runner Tests ====================


@pytest.mark.parametrize(
    ("has_task_runner", "expected_result"),
    [
        (True, MagicMock()),
        (False, None),
    ],
)
def test_get_task_runner(
    has_task_runner: bool, expected_result: MagicMock | None
) -> None:
    """Test _get_task_runner returns task runner or None.

    Parameters
    ----------
    has_task_runner : bool
        Whether task runner exists in app state.
    expected_result : MagicMock | None
        Expected return value.
    """
    request = MagicMock(spec=Request)
    if has_task_runner:
        request.app.state.task_runner = MagicMock()
    else:
        request.app.state = MagicMock()
        delattr(request.app.state, "task_runner")

    result = epub_fixer_routes._get_task_runner(request)
    if has_task_runner:
        assert result is not None
    else:
        assert result is None


# ==================== fix_single_epub Tests ====================


def test_fix_single_epub_success(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test successful fix_single_epub endpoint (lines 107-141).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixSingleRequest(file_path="/path/to/book.epub")
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.return_value = 123

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        result = epub_fixer_routes.fix_single_epub(
            request_body,
            mock_request,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.task_id == 123
        assert "book.epub" in result.message
        mock_permission.check_permission.assert_called_once_with(
            mock_user, "books", "write"
        )
        mock_task_runner.enqueue.assert_called_once()


def test_fix_single_epub_with_optional_fields(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test fix_single_epub with optional fields (lines 123-128).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixSingleRequest(
        file_path="/path/to/book.epub",
        book_id=456,
        book_title="Test Book",
        library_id=789,
    )
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.return_value = 123

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        result = epub_fixer_routes.fix_single_epub(
            request_body,
            mock_request,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.task_id == 123
        call_kwargs = mock_task_runner.enqueue.call_args[1]
        assert call_kwargs["metadata"]["book_id"] == 456
        assert call_kwargs["metadata"]["book_title"] == "Test Book"
        assert call_kwargs["metadata"]["library_id"] == 789


def test_fix_single_epub_no_task_runner(
    mock_user: User, mock_request_no_task_runner: MagicMock, session: DummySession
) -> None:
    """Test fix_single_epub raises 503 when task runner unavailable (lines 112-116).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request_no_task_runner : MagicMock
        Mock request without task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixSingleRequest(file_path="/path/to/book.epub")

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.fix_single_epub(
                request_body,
                mock_request_no_task_runner,
                session,  # type: ignore[arg-type]
                mock_user,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Task runner not available" in exc.detail


def test_fix_single_epub_enqueue_exception(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test fix_single_epub handles enqueue exception (lines 142-147).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixSingleRequest(file_path="/path/to/book.epub")
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.side_effect = Exception("Queue full")

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.fix_single_epub(
                request_body,
                mock_request,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to create fix task" in exc.detail


# ==================== fix_batch_epub Tests ====================


def test_fix_batch_epub_success(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test successful fix_batch_epub endpoint (lines 183-212).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixBatchRequest()
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.return_value = 456

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        result = epub_fixer_routes.fix_batch_epub(
            request_body,
            mock_request,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.task_id == 456
        assert "batch fix task" in result.message
        mock_permission.check_permission.assert_called_once_with(
            mock_user, "books", "write"
        )
        mock_task_runner.enqueue.assert_called_once()


def test_fix_batch_epub_with_library_id(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test fix_batch_epub with library_id (lines 198-199).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixBatchRequest(library_id=789)
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.return_value = 456

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        epub_fixer_routes.fix_batch_epub(
            request_body,
            mock_request,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        call_kwargs = mock_task_runner.enqueue.call_args[1]
        assert call_kwargs["metadata"]["library_id"] == 789


def test_fix_batch_epub_no_task_runner(
    mock_user: User, mock_request_no_task_runner: MagicMock, session: DummySession
) -> None:
    """Test fix_batch_epub raises 503 when task runner unavailable (lines 187-192).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request_no_task_runner : MagicMock
        Mock request without task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixBatchRequest()

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.fix_batch_epub(
                request_body,
                mock_request_no_task_runner,
                session,  # type: ignore[arg-type]
                mock_user,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_fix_batch_epub_enqueue_exception(
    mock_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test fix_batch_epub handles enqueue exception (lines 213-218).

    Parameters
    ----------
    mock_user : User
        Mock user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    request_body = EPUBFixBatchRequest()
    mock_task_runner = mock_request.app.state.task_runner
    mock_task_runner.enqueue.side_effect = Exception("Queue full")

    with patch(
        "fundamental.api.routes.epub_fixer.PermissionService"
    ) as mock_permission_class:
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.fix_batch_epub(
                request_body,
                mock_request,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ==================== list_fix_runs Tests ====================


@pytest.mark.parametrize(
    ("is_admin", "page", "page_size"),
    [
        (False, 1, 50),
        (True, 1, 50),
        (True, 2, 25),
    ],
)
def test_list_fix_runs(
    is_admin: bool,
    page: int,
    page_size: int,
    mock_user: User,
    admin_user: User,
    session: DummySession,
) -> None:
    """Test list_fix_runs endpoint (lines 252-306).

    Parameters
    ----------
    is_admin : bool
        Whether user is admin.
    page : int
        Page number.
    page_size : int
        Page size.
    mock_user : User
        Regular user.
    admin_user : User
        Admin user.
    session : DummySession
        Dummy session.
    """
    user = admin_user if is_admin else mock_user
    mock_runs = [
        EPUBFixRun(
            id=1,
            user_id=user.id,
            total_files_processed=10,
            total_files_fixed=5,
            total_fixes_applied=8,
        )
    ]

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        if is_admin:
            mock_service.get_recent_runs.return_value = mock_runs * (
                page_size + (page - 1) * page_size
            )
        else:
            mock_service.get_runs_by_user.return_value = mock_runs
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.list_fix_runs(
            session,
            user,
            page,
            page_size,  # type: ignore[arg-type]
        )

        assert result.page == page
        assert result.page_size == page_size
        assert len(result.items) > 0


def test_list_fix_runs_pagination_estimation(
    admin_user: User, session: DummySession
) -> None:
    """Test list_fix_runs pagination estimation (lines 293-298).

    Parameters
    ----------
    admin_user : User
        Admin user.
    session : DummySession
        Dummy session.
    """
    page_size = 50
    mock_runs = [EPUBFixRun(id=i) for i in range(page_size)]

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_recent_runs.return_value = mock_runs
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.list_fix_runs(
            session,
            admin_user,
            1,
            page_size,  # type: ignore[arg-type]
        )

        # When len == page_size, total should be page_size * (page + 1)
        assert result.total == page_size * 2


# ==================== get_fix_run Tests ====================


def test_get_fix_run_success(mock_user: User, session: DummySession) -> None:
    """Test successful get_fix_run endpoint (lines 337-372).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(
        id=run_id,
        user_id=mock_user.id,
        total_files_processed=10,
        total_files_fixed=5,
    )

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.get_fix_run(
            run_id,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.id == run_id
        assert result.user_id == mock_user.id


def test_get_fix_run_not_found(mock_user: User, session: DummySession) -> None:
    """Test get_fix_run raises 404 when run not found (lines 343-347).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 999

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.get_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


def test_get_fix_run_access_denied(
    mock_user: User, admin_user: User, session: DummySession
) -> None:
    """Test get_fix_run raises 403 for non-admin accessing other user's run (lines 350-354).

    Parameters
    ----------
    mock_user : User
        Regular user.
    admin_user : User
        Admin user (owner of run).
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=admin_user.id)

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.get_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_403_FORBIDDEN


# ==================== get_fixes_for_run Tests ====================


def test_get_fixes_for_run_success(mock_user: User, session: DummySession) -> None:
    """Test successful get_fixes_for_run endpoint (lines 403-443).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=mock_user.id)
    mock_fixes = [
        EPUBFix(
            id=1,
            run_id=run_id,
            book_id=123,
            book_title="Test Book",
            file_path="/path/to/book.epub",
            fix_type=EPUBFixType.LANGUAGE_TAG,
            fix_description="Fixed language tag",
        )
    ]

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service.get_fixes_for_run.return_value = mock_fixes
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.get_fixes_for_run(
            run_id,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].book_title == "Test Book"


def test_get_fixes_for_run_not_found(mock_user: User, session: DummySession) -> None:
    """Test get_fixes_for_run raises 404 when run not found (lines 409-413).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 999

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.get_fixes_for_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


def test_get_fixes_for_run_access_denied(
    mock_user: User, admin_user: User, session: DummySession
) -> None:
    """Test get_fixes_for_run raises 403 for non-admin accessing other user's run (lines 416-420).

    Parameters
    ----------
    mock_user : User
        Regular user.
    admin_user : User
        Admin user (owner of run).
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=admin_user.id)

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.get_fixes_for_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_403_FORBIDDEN


# ==================== rollback_fix_run Tests ====================


def test_rollback_fix_run_success(mock_user: User, session: DummySession) -> None:
    """Test successful rollback_fix_run endpoint (lines 474-504).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=mock_user.id)
    mock_fixes = [
        EPUBFix(
            id=1,
            run_id=run_id,
            backup_created=True,
            original_file_path="/backup/path.epub",
        ),
        EPUBFix(
            id=2,
            run_id=run_id,
            backup_created=False,
        ),
    ]

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service.rollback_fix_run.return_value = mock_run
        mock_service.get_fixes_for_run.return_value = mock_fixes
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.rollback_fix_run(
            run_id,
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.run_id == run_id
        assert result.files_restored == 1  # Only one fix has backup_created=True


def test_rollback_fix_run_not_found(mock_user: User, session: DummySession) -> None:
    """Test rollback_fix_run raises 404 when run not found (lines 480-484).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 999

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.rollback_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


def test_rollback_fix_run_access_denied(
    mock_user: User, admin_user: User, session: DummySession
) -> None:
    """Test rollback_fix_run raises 403 for non-admin accessing other user's run (lines 487-491).

    Parameters
    ----------
    mock_user : User
        Regular user.
    admin_user : User
        Admin user (owner of run).
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=admin_user.id)

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.rollback_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_403_FORBIDDEN


def test_rollback_fix_run_value_error(mock_user: User, session: DummySession) -> None:
    """Test rollback_fix_run handles ValueError (lines 505-509).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=mock_user.id)

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service.rollback_fix_run.side_effect = ValueError("Cannot rollback")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.rollback_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_400_BAD_REQUEST


def test_rollback_fix_run_generic_exception(
    mock_user: User, session: DummySession
) -> None:
    """Test rollback_fix_run handles generic exception (lines 510-515).

    Parameters
    ----------
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    run_id = 1
    mock_run = EPUBFixRun(id=run_id, user_id=mock_user.id)

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_fix_run.return_value = mock_run
        mock_service.rollback_fix_run.side_effect = Exception("Database error")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            epub_fixer_routes.rollback_fix_run(
                run_id,
                session,
                mock_user,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ==================== get_fix_statistics Tests ====================


@pytest.mark.parametrize(
    ("fix_type_str", "should_skip"),
    [
        ("language_tag", False),
        ("invalid_type", True),
    ],
)
def test_get_fix_statistics(
    fix_type_str: str,
    should_skip: bool,
    mock_user: User,
    session: DummySession,
) -> None:
    """Test get_fix_statistics endpoint (lines 543-568).

    Parameters
    ----------
    fix_type_str : str
        Fix type string.
    should_skip : bool
        Whether invalid type should be skipped.
    mock_user : User
        Mock user.
    session : DummySession
        Dummy session.
    """
    stats = {
        "total_runs": 10,
        "total_files_processed": 100,
        "total_files_fixed": 50,
        "total_fixes_applied": 75,
    }
    fixes_by_type_raw = {fix_type_str: 25}

    with (
        patch(
            "fundamental.api.routes.epub_fixer.PermissionService"
        ) as mock_permission_class,
        patch(
            "fundamental.api.routes.epub_fixer.EPUBFixerService"
        ) as mock_service_class,
    ):
        mock_permission = MagicMock()
        mock_permission_class.return_value = mock_permission
        mock_service = MagicMock()
        mock_service.get_statistics.return_value = stats
        mock_service.get_fix_statistics_by_type.return_value = fixes_by_type_raw
        mock_service_class.return_value = mock_service

        result = epub_fixer_routes.get_fix_statistics(
            session,
            mock_user,  # type: ignore[arg-type]
        )

        assert result.total_runs == 10
        assert result.total_files_processed == 100
        assert result.total_files_fixed == 50
        assert result.total_fixes_applied == 75
        if not should_skip:
            assert len(result.fixes_by_type) > 0
        else:
            # Invalid types should be skipped
            assert len(result.fixes_by_type) == 0

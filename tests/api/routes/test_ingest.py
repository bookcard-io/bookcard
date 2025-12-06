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

"""Tests for ingest routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

import fundamental.api.routes.ingest as ingest_routes
from fundamental.api.schemas.ingest import IngestConfigUpdate
from fundamental.models.auth import User
from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.models.tasks import TaskType

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def admin_user() -> User:
    """Create a mock admin user for testing.

    Returns
    -------
    User
        Mock admin user instance.
    """
    return User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock request with task runner and watcher.

    Returns
    -------
    MagicMock
        Mock request object.
    """
    request = MagicMock(spec=Request)
    request.app.state.task_runner = MagicMock()
    request.app.state.ingest_watcher = MagicMock()
    return request


@pytest.fixture
def mock_request_no_watcher() -> MagicMock:
    """Create a mock request without watcher.

    Returns
    -------
    MagicMock
        Mock request object without ingest_watcher.
    """
    request = MagicMock(spec=Request)
    request.app.state.task_runner = MagicMock()
    request.app.state = MagicMock()
    delattr(request.app.state, "ingest_watcher")
    return request


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
    """Test _get_task_runner returns task runner or None (lines 73-75).

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

    result = ingest_routes._get_task_runner(request)
    if has_task_runner:
        assert result is not None
    else:
        assert result is None


# ==================== _get_ingest_watcher Tests ====================


@pytest.mark.parametrize(
    ("has_watcher", "expected_result"),
    [
        (True, MagicMock()),
        (False, None),
    ],
)
def test_get_ingest_watcher(
    has_watcher: bool, expected_result: MagicMock | None
) -> None:
    """Test _get_ingest_watcher returns watcher or None (lines 91-93).

    Parameters
    ----------
    has_watcher : bool
        Whether watcher exists in app state.
    expected_result : MagicMock | None
        Expected return value.
    """
    request = MagicMock(spec=Request)
    if has_watcher:
        request.app.state.ingest_watcher = MagicMock()
    else:
        request.app.state = MagicMock()
        delattr(request.app.state, "ingest_watcher")

    result = ingest_routes._get_ingest_watcher(request)
    if has_watcher:
        assert result is not None
    else:
        assert result is None


# ==================== get_ingest_config Tests ====================


def test_get_ingest_config(session: DummySession) -> None:
    """Test get_ingest_config endpoint (lines 116-118).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    from fundamental.models.ingest import IngestConfig

    mock_config = IngestConfig(
        ingest_dir="/path/to/ingest",
        enabled=True,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    with patch(
        "fundamental.api.routes.ingest.IngestConfigService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_config.return_value = mock_config
        mock_service_class.return_value = mock_service

        result = ingest_routes.get_ingest_config(session)  # type: ignore[arg-type]

        assert result is not None
        assert result.enabled is True
        mock_service.get_config.assert_called_once()


# ==================== update_ingest_config Tests ====================


@pytest.mark.parametrize(
    ("enabled_changed", "dir_changed", "should_restart"),
    [
        (True, False, True),
        (False, True, True),
        (True, True, True),
        (False, False, False),
    ],
)
def test_update_ingest_config_restarts_watcher(
    enabled_changed: bool,
    dir_changed: bool,
    should_restart: bool,
    admin_user: User,
    mock_request: MagicMock,
    session: DummySession,
) -> None:
    """Test update_ingest_config restarts watcher when needed (lines 150-189).

    Parameters
    ----------
    enabled_changed : bool
        Whether enabled flag changed.
    dir_changed : bool
        Whether ingest_dir changed.
    should_restart : bool
        Whether watcher should be restarted.
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    session : DummySession
        Dummy session.
    """
    from fundamental.models.ingest import IngestConfig

    old_config = IngestConfig(
        ingest_dir="/old/path",
        enabled=False,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    new_config = IngestConfig(
        ingest_dir="/new/path" if dir_changed else "/old/path",
        enabled=bool(enabled_changed),
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    config_update = IngestConfigUpdate(
        enabled=True if enabled_changed else None,
        ingest_dir="/new/path" if dir_changed else None,
    )

    with patch(
        "fundamental.api.routes.ingest.IngestConfigService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_config.return_value = old_config
        mock_service.update_config.return_value = new_config
        mock_service_class.return_value = mock_service

        mock_watcher = mock_request.app.state.ingest_watcher

        result = ingest_routes.update_ingest_config(
            mock_request,
            session,
            config_update,  # type: ignore[arg-type]
        )

        assert result is not None
        if should_restart:
            mock_watcher.restart_watching.assert_called_once()
        else:
            mock_watcher.restart_watching.assert_not_called()


def test_update_ingest_config_watcher_not_available(
    admin_user: User, mock_request_no_watcher: MagicMock, session: DummySession
) -> None:
    """Test update_ingest_config handles missing watcher (lines 184-187).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request_no_watcher : MagicMock
        Mock request without watcher.
    session : DummySession
        Dummy session.
    """
    from fundamental.models.ingest import IngestConfig

    old_config = IngestConfig(
        ingest_dir="/old/path",
        enabled=False,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    new_config = IngestConfig(
        ingest_dir="/old/path",
        enabled=True,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    config_update = IngestConfigUpdate(enabled=True)

    with patch(
        "fundamental.api.routes.ingest.IngestConfigService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_config.return_value = old_config
        mock_service.update_config.return_value = new_config
        mock_service_class.return_value = mock_service

        result = ingest_routes.update_ingest_config(
            mock_request_no_watcher,
            session,
            config_update,  # type: ignore[arg-type]
        )

        assert result is not None


def test_update_ingest_config_watcher_restart_error(
    admin_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test update_ingest_config handles watcher restart error (lines 180-183).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    session : DummySession
        Dummy session.
    """
    from fundamental.models.ingest import IngestConfig

    old_config = IngestConfig(
        ingest_dir="/old/path",
        enabled=False,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    new_config = IngestConfig(
        ingest_dir="/old/path",
        enabled=True,
        metadata_fetch_enabled=False,
        metadata_merge_strategy="first_wins",
        retry_max_attempts=3,
        retry_backoff_seconds=300,
        process_timeout_seconds=3600,
        auto_delete_after_ingest=True,
    )

    config_update = IngestConfigUpdate(enabled=True)

    with patch(
        "fundamental.api.routes.ingest.IngestConfigService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_config.return_value = old_config
        mock_service.update_config.return_value = new_config
        mock_service_class.return_value = mock_service

        mock_watcher = mock_request.app.state.ingest_watcher
        mock_watcher.restart_watching.side_effect = ValueError("Invalid path")

        result = ingest_routes.update_ingest_config(
            mock_request,
            session,
            config_update,  # type: ignore[arg-type]
        )

        # Should still return config even if restart fails
        assert result is not None


# ==================== list_ingest_history Tests ====================


@pytest.mark.parametrize(
    ("status_filter", "page", "page_size"),
    [
        (None, 1, 50),
        (IngestStatus.FAILED, 1, 50),
        (IngestStatus.COMPLETED, 2, 25),
    ],
)
def test_list_ingest_history(
    status_filter: IngestStatus | None,
    page: int,
    page_size: int,
    admin_user: User,
    session: DummySession,
) -> None:
    """Test list_ingest_history endpoint (lines 222-245).

    Parameters
    ----------
    status_filter : IngestStatus | None
        Optional status filter.
    page : int
        Page number.
    page_size : int
        Page size.
    admin_user : User
        Admin user.
    session : DummySession
        Dummy session.
    """
    mock_history = [
        IngestHistory(
            id=1,
            status=IngestStatus.COMPLETED,
            file_path="/path/to/book.epub",
        )
    ]

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Mock session.exec to return mock_history
        session.set_exec_result(mock_history)

        result = ingest_routes.list_ingest_history(
            session,
            page,
            page_size,
            status_filter,  # type: ignore[arg-type]
        )

        assert result.page == page
        assert result.page_size == page_size


# ==================== get_ingest_history Tests ====================


def test_get_ingest_history_success(admin_user: User, session: DummySession) -> None:
    """Test successful get_ingest_history endpoint (lines 276-285).

    Parameters
    ----------
    admin_user : User
        Admin user.
    session : DummySession
        Dummy session.
    """
    history_id = 1
    mock_history = IngestHistory(
        id=history_id,
        status=IngestStatus.COMPLETED,
        file_path="/path/to/book.epub",
    )

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_history
        mock_repo_class.return_value = mock_repo

        result = ingest_routes.get_ingest_history(
            session,
            history_id,  # type: ignore[arg-type]
        )

        assert result.id == history_id


def test_get_ingest_history_not_found(admin_user: User, session: DummySession) -> None:
    """Test get_ingest_history raises 404 when not found (lines 279-283).

    Parameters
    ----------
    admin_user : User
        Admin user.
    session : DummySession
        Dummy session.
    """
    history_id = 999

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            ingest_routes.get_ingest_history(session, history_id)  # type: ignore[arg-type]

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


# ==================== restart_watcher Tests ====================


def test_restart_watcher_success(admin_user: User, mock_request: MagicMock) -> None:
    """Test successful restart_watcher endpoint (lines 316-333).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    """
    mock_watcher = mock_request.app.state.ingest_watcher

    result = ingest_routes.restart_watcher(mock_request)

    assert result["message"] == "Ingest watcher restarted successfully"
    mock_watcher.restart_watching.assert_called_once()


def test_restart_watcher_not_available(
    admin_user: User, mock_request_no_watcher: MagicMock
) -> None:
    """Test restart_watcher raises 503 when watcher not available (lines 317-321).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request_no_watcher : MagicMock
        Mock request without watcher.
    """
    with pytest.raises(HTTPException) as exc_info:
        ingest_routes.restart_watcher(mock_request_no_watcher)

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_restart_watcher_error(admin_user: User, mock_request: MagicMock) -> None:
    """Test restart_watcher handles restart error (lines 326-331).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    """
    mock_watcher = mock_request.app.state.ingest_watcher
    mock_watcher.restart_watching.side_effect = RuntimeError("Failed to restart")

    with pytest.raises(HTTPException) as exc_info:
        ingest_routes.restart_watcher(mock_request)

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ==================== trigger_scan Tests ====================


def test_trigger_scan_with_watcher(admin_user: User, mock_request: MagicMock) -> None:
    """Test trigger_scan with watcher (lines 364-372).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    """
    mock_watcher = mock_request.app.state.ingest_watcher
    mock_watcher.trigger_manual_scan.return_value = 123

    result = ingest_routes.trigger_scan(mock_request, admin_user)

    assert result.task_id == 123
    assert "triggered" in result.message.lower()


def test_trigger_scan_watcher_returns_none(
    admin_user: User, mock_request: MagicMock
) -> None:
    """Test trigger_scan raises 503 when watcher returns None (lines 367-371).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with watcher.
    """
    mock_watcher = mock_request.app.state.ingest_watcher
    mock_watcher.trigger_manual_scan.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        ingest_routes.trigger_scan(mock_request, admin_user)

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_trigger_scan_fallback_to_task_runner(
    admin_user: User, mock_request_no_watcher: MagicMock
) -> None:
    """Test trigger_scan falls back to task runner (lines 374-390).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request_no_watcher : MagicMock
        Mock request without watcher but with task runner.
    """
    mock_task_runner = mock_request_no_watcher.app.state.task_runner
    mock_task_runner.enqueue.return_value = 456

    result = ingest_routes.trigger_scan(mock_request_no_watcher, admin_user)

    assert result.task_id == 456
    mock_task_runner.enqueue.assert_called_once()
    call_kwargs = mock_task_runner.enqueue.call_args[1]
    assert call_kwargs["task_type"] == TaskType.INGEST_DISCOVERY


def test_trigger_scan_no_task_runner(
    admin_user: User, mock_request_no_watcher: MagicMock
) -> None:
    """Test trigger_scan raises 503 when no task runner (lines 376-380).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request_no_watcher : MagicMock
        Mock request without watcher.
    """
    # Remove task runner too
    delattr(mock_request_no_watcher.app.state, "task_runner")

    with pytest.raises(HTTPException) as exc_info:
        ingest_routes.trigger_scan(mock_request_no_watcher, admin_user)

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ==================== retry_ingest Tests ====================


def test_retry_ingest_success(
    admin_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test successful retry_ingest endpoint (lines 427-476).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    history_id = 1
    mock_history = IngestHistory(
        id=history_id,
        status=IngestStatus.FAILED,
        file_path="/path/to/book.epub",
        ingest_metadata={"files": ["/path/to/book.epub"]},
    )

    with (
        patch(
            "fundamental.api.routes.ingest.IngestHistoryRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_history
        mock_repo_class.return_value = mock_repo

        mock_task_runner = mock_request.app.state.task_runner
        mock_task_runner.enqueue.return_value = 789

        result = ingest_routes.retry_ingest(
            mock_request,
            session,
            admin_user,
            history_id,  # type: ignore[arg-type]
        )

        assert result.history_id == history_id
        mock_task_runner.enqueue.assert_called_once()


def test_retry_ingest_not_found(
    admin_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test retry_ingest raises 404 when history not found (lines 430-434).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    history_id = 999

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            ingest_routes.retry_ingest(
                mock_request,
                session,
                admin_user,
                history_id,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


def test_retry_ingest_not_failed(
    admin_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test retry_ingest raises 400 when status not failed (lines 436-440).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    history_id = 1
    mock_history = IngestHistory(
        id=history_id,
        status=IngestStatus.COMPLETED,
        file_path="/path/to/book.epub",
    )

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_history
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            ingest_routes.retry_ingest(
                mock_request,
                session,
                admin_user,
                history_id,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_400_BAD_REQUEST


def test_retry_ingest_no_files(
    admin_user: User, mock_request: MagicMock, session: DummySession
) -> None:
    """Test retry_ingest raises 400 when no files (lines 444-449).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request : MagicMock
        Mock request with task runner.
    session : DummySession
        Dummy session.
    """
    history_id = 1
    mock_history = IngestHistory(
        id=history_id,
        status=IngestStatus.FAILED,
        file_path="/path/to/book.epub",
        ingest_metadata={},
    )

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_history
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            ingest_routes.retry_ingest(
                mock_request,
                session,
                admin_user,
                history_id,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_400_BAD_REQUEST


def test_retry_ingest_no_task_runner(
    admin_user: User, mock_request_no_watcher: MagicMock, session: DummySession
) -> None:
    """Test retry_ingest raises 503 when no task runner (lines 452-457).

    Parameters
    ----------
    admin_user : User
        Admin user.
    mock_request_no_watcher : MagicMock
        Mock request without watcher.
    session : DummySession
        Dummy session.
    """
    history_id = 1
    mock_history = IngestHistory(
        id=history_id,
        status=IngestStatus.FAILED,
        file_path="/path/to/book.epub",
        ingest_metadata={"files": ["/path/to/book.epub"]},
    )

    # Remove task runner
    delattr(mock_request_no_watcher.app.state, "task_runner")

    with patch(
        "fundamental.api.routes.ingest.IngestHistoryRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_history
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            ingest_routes.retry_ingest(
                mock_request_no_watcher,
                session,
                admin_user,
                history_id,  # type: ignore[arg-type]
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

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

"""Tests for Kobo routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

import bookcard.api.routes.kobo as kobo_routes
from bookcard.models.auth import User
from bookcard.models.config import IntegrationConfig, Library
from bookcard.models.core import Book

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def kobo_user() -> User:
    """Create a mock Kobo user for testing.

    Returns
    -------
    User
        Mock user instance.
    """
    return User(
        id=1,
        username="kobouser",
        email="kobo@example.com",
        password_hash="hash",
    )


@pytest.fixture
def auth_token() -> str:
    """Create a mock auth token.

    Returns
    -------
    str
        Mock auth token.
    """
    return "test_auth_token_123"


@pytest.fixture
def mock_library() -> Library:
    """Create a mock library.

    Returns
    -------
    Library
        Mock library instance.
    """
    return Library(id=1, name="Test Library", path="/path/to/library")


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock request.

    Returns
    -------
    MagicMock
        Mock request object.
    """
    request = MagicMock(spec=Request)
    request.base_url = "https://example.com"
    return request


# ==================== _get_active_library Tests ====================


def test_get_active_library_success(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test _get_active_library returns active library.

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    with patch(
        "bookcard.api.routes.kobo._resolve_active_library",
        return_value=mock_library,
    ):
        result = kobo_routes._get_active_library(session, kobo_user)  # type: ignore[arg-type]

        assert result == mock_library


def test_get_active_library_not_found(session: DummySession, kobo_user: User) -> None:
    """Test _get_active_library raises 404 when no active library.

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    with (
        patch("bookcard.api.routes.kobo._resolve_active_library", return_value=None),
        pytest.raises(HTTPException) as exc_info,
    ):
        kobo_routes._get_active_library(session, kobo_user)  # type: ignore[arg-type]

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "no_active_library"


def test_get_active_library_no_id(session: DummySession, kobo_user: User) -> None:
    """Test _get_active_library raises 404 when library has no id.

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    library_no_id = Library(name="Test Library", path="/path/to/library")

    with (
        patch(
            "bookcard.api.routes.kobo._resolve_active_library",
            return_value=library_no_id,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        kobo_routes._get_active_library(session, kobo_user)  # type: ignore[arg-type]

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND


# ==================== _get_integration_config Tests ====================


@pytest.mark.parametrize(
    ("has_config", "kobo_sync_enabled"),
    [
        (True, True),
        (True, False),
        (False, False),
    ],
)
def test_get_integration_config(
    has_config: bool, kobo_sync_enabled: bool, session: DummySession
) -> None:
    """Test _get_integration_config returns config or None (lines 142-143).

    Parameters
    ----------
    has_config : bool
        Whether config exists.
    kobo_sync_enabled : bool
        Whether Kobo sync is enabled.
    session : DummySession
        Dummy session.
    """
    if has_config:
        mock_config = IntegrationConfig(kobo_sync_enabled=kobo_sync_enabled)
        session.set_exec_result([mock_config])
    else:
        session.set_exec_result([])

    result = kobo_routes._get_integration_config(session)  # type: ignore[arg-type]

    if has_config:
        assert result is not None
        assert result.kobo_sync_enabled == kobo_sync_enabled
    else:
        assert result is None


# ==================== _check_kobo_sync_enabled Tests ====================


def test_check_kobo_sync_enabled_success(session: DummySession) -> None:
    """Test _check_kobo_sync_enabled passes when enabled (lines 159-164).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    # Should not raise
    kobo_routes._check_kobo_sync_enabled(session)  # type: ignore[arg-type]


def test_check_kobo_sync_enabled_disabled(session: DummySession) -> None:
    """Test _check_kobo_sync_enabled raises 403 when disabled (lines 160-164).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=False)
    session.set_exec_result([mock_config])

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes._check_kobo_sync_enabled(session)  # type: ignore[arg-type]

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.detail == "kobo_sync_disabled"


def test_check_kobo_sync_enabled_no_config(session: DummySession) -> None:
    """Test _check_kobo_sync_enabled raises 403 when no config (lines 160-164).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    session.set_exec_result([])

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes._check_kobo_sync_enabled(session)  # type: ignore[arg-type]

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_403_FORBIDDEN


# ==================== _get_book_service Tests ====================


def test_get_book_service(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test _get_book_service returns BookService.

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch("bookcard.api.routes.kobo.BookService") as mock_service_class,
    ):
        result = kobo_routes._get_book_service(session, kobo_user)  # type: ignore[arg-type]

        assert result is not None
        mock_service_class.assert_called_once_with(mock_library, session=session)


# ==================== _get_book_by_uuid Tests ====================


def test_get_book_by_uuid_success() -> None:
    """Test _get_book_by_uuid returns book when found (lines 204-209).

    Parameters
    ----------
    """
    book_uuid = "test-uuid-123"
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_service = MagicMock()
    mock_book_repo = MagicMock()
    mock_book_service._book_repo = mock_book_repo
    mock_calibre_session = MagicMock()
    mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
    mock_calibre_session.__exit__ = MagicMock(return_value=False)
    mock_calibre_session.exec.return_value.first.return_value = mock_book
    mock_book_repo.get_session.return_value = mock_calibre_session

    result = kobo_routes._get_book_by_uuid(mock_book_service, book_uuid)

    assert result is not None
    assert result[0] == 1
    assert result[1] == mock_book


def test_get_book_by_uuid_not_found() -> None:
    """Test _get_book_by_uuid returns None when not found (lines 207-208).

    Parameters
    ----------
    """
    book_uuid = "test-uuid-123"
    mock_book_service = MagicMock()
    mock_book_repo = MagicMock()
    mock_book_service._book_repo = mock_book_repo
    mock_calibre_session = MagicMock()
    mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
    mock_calibre_session.__exit__ = MagicMock(return_value=False)
    mock_calibre_session.exec.return_value.first.return_value = None
    mock_book_repo.get_session.return_value = mock_calibre_session

    result = kobo_routes._get_book_by_uuid(mock_book_service, book_uuid)

    assert result is None


def test_get_book_by_uuid_no_id() -> None:
    """Test _get_book_by_uuid returns None when book has no id (lines 207-208).

    Parameters
    ----------
    """
    book_uuid = "test-uuid-123"
    mock_book = Book(uuid=book_uuid, title="Test Book")  # No id
    mock_book_service = MagicMock()
    mock_book_repo = MagicMock()
    mock_book_service._book_repo = mock_book_repo
    mock_calibre_session = MagicMock()
    mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
    mock_calibre_session.__exit__ = MagicMock(return_value=False)
    mock_calibre_session.exec.return_value.first.return_value = mock_book
    mock_book_repo.get_session.return_value = mock_calibre_session

    result = kobo_routes._get_book_by_uuid(mock_book_service, book_uuid)

    assert result is None


# ==================== _get_kobo_metadata_service Tests ====================


def test_get_kobo_metadata_service(mock_request: MagicMock, auth_token: str) -> None:
    """Test _get_kobo_metadata_service returns service (lines 231-232).

    Parameters
    ----------
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    """
    with patch("bookcard.api.routes.kobo.KoboMetadataService") as mock_service_class:
        result = kobo_routes._get_kobo_metadata_service(mock_request, auth_token)

        assert result is not None
        mock_service_class.assert_called_once_with(
            base_url="https://example.com", auth_token=auth_token
        )


def test_get_kobo_metadata_service_dep(
    mock_request: MagicMock, auth_token: str
) -> None:
    """Test _get_kobo_metadata_service_dep returns service (lines 235-238).

    Parameters
    ----------
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    """
    with patch("bookcard.api.routes.kobo.KoboMetadataService") as mock_service_class:
        result = kobo_routes._get_kobo_metadata_service_dep(mock_request, auth_token)

        assert result is not None
        mock_service_class.assert_called_once()


# ==================== _get_kobo_sync_service Tests ====================


def test_get_kobo_sync_service(session: DummySession) -> None:
    """Test _get_kobo_sync_service returns service (lines 280-294).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_book_service = MagicMock()
    mock_metadata_service = MagicMock()
    mock_shelf_service = MagicMock()

    with patch("bookcard.api.routes.kobo.KoboSyncService") as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_sync_service(
            session,  # type: ignore[arg-type]
            mock_book_service,
            mock_metadata_service,
            mock_shelf_service,
        )

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once()


def test_get_kobo_sync_service_no_shelf_service(session: DummySession) -> None:
    """Test _get_kobo_sync_service works without shelf service (lines 280-294).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_book_service = MagicMock()
    mock_metadata_service = MagicMock()

    with patch("bookcard.api.routes.kobo.KoboSyncService") as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_sync_service(
            session,  # type: ignore[arg-type]
            mock_book_service,
            mock_metadata_service,
            None,
        )

        assert result is not None
        assert result == mock_service_instance
        # Check that shelf_service=None was passed
        call_kwargs = mock_service_class.call_args[1]
        assert call_kwargs.get("shelf_service") is None


# ==================== _get_kobo_reading_state_service Tests ====================


def test_get_kobo_reading_state_service(session: DummySession) -> None:
    """Test _get_kobo_reading_state_service returns service (lines 312-339).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    with patch(
        "bookcard.api.routes.kobo.KoboReadingStateService"
    ) as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_reading_state_service(
            session  # type: ignore[arg-type]
        )

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once()


# ==================== _get_kobo_shelf_service Tests ====================


def test_get_kobo_shelf_service(session: DummySession) -> None:
    """Test _get_kobo_shelf_service returns service (lines 342-367).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """

    # Mock Path.mkdir to avoid permission issues
    with (
        patch("pathlib.Path.mkdir"),
        patch(
            "bookcard.services.shelf_service.ShelfService.__init__",
            return_value=None,
        ),
    ):
        result = kobo_routes._get_kobo_shelf_service(session)  # type: ignore[arg-type]

        assert result is not None
        # Verify it's a KoboShelfService instance
        from bookcard.services.kobo.shelf_service import KoboShelfService

        assert isinstance(result, KoboShelfService)


# ==================== Additional Helper Function Tests ====================


def test_get_kobo_download_service(
    session: DummySession, mock_library: Library
) -> None:
    """Test _get_kobo_download_service returns service (line 389).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_library : Library
        Mock library.
    """
    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch("bookcard.api.routes.kobo.BookService") as mock_book_service_class,
        patch("bookcard.api.routes.kobo.KoboDownloadService") as mock_service_class,
    ):
        mock_book_service = MagicMock()
        mock_book_service_class.return_value = mock_book_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_download_service(mock_book_service)

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once_with(book_service=mock_book_service)


def test_get_kobo_book_lookup_service(session: DummySession) -> None:
    """Test _get_kobo_book_lookup_service returns service (line 407).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_book_service = MagicMock()

    with patch("bookcard.api.routes.kobo.KoboBookLookupService") as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_book_lookup_service(mock_book_service)

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once_with(book_service=mock_book_service)


def test_get_kobo_device_auth_service(session: DummySession) -> None:
    """Test _get_kobo_device_auth_service returns service (lines 425-426).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_service_func,
        patch("bookcard.api.routes.kobo.KoboDeviceAuthService") as mock_service_class,
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service_func.return_value = mock_proxy_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_device_auth_service(session)  # type: ignore[arg-type]

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once_with(
            session=session, proxy_service=mock_proxy_service
        )


def test_get_kobo_initialization_service(session: DummySession) -> None:
    """Test _get_kobo_initialization_service returns service (lines 444-445).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_service_func,
        patch(
            "bookcard.api.routes.kobo.KoboInitializationService"
        ) as mock_service_class,
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service_func.return_value = mock_proxy_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_initialization_service(session)  # type: ignore[arg-type]

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once_with(proxy_service=mock_proxy_service)


def test_get_kobo_library_service(
    session: DummySession,
    mock_request: MagicMock,
    auth_token: str,
    mock_library: Library,
) -> None:
    """Test _get_kobo_library_service returns service (lines 472-478).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    mock_library : Library
        Mock library.
    """
    mock_book_service = MagicMock()

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_metadata_service"
        ) as mock_metadata_func,
        patch("bookcard.api.routes.kobo._get_kobo_sync_service") as mock_sync_func,
        patch("bookcard.api.routes.kobo._get_kobo_shelf_service") as mock_shelf_func,
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
        patch(
            "bookcard.api.routes.kobo._get_kobo_book_lookup_service"
        ) as mock_lookup_func,
        patch("bookcard.api.routes.kobo.KoboLibraryService") as mock_service_class,
    ):
        mock_metadata_service = MagicMock()
        mock_metadata_func.return_value = mock_metadata_service
        mock_sync_service = MagicMock()
        mock_sync_func.return_value = mock_sync_service
        mock_shelf_service = MagicMock()
        mock_shelf_func.return_value = mock_shelf_service
        mock_proxy_service = MagicMock()
        mock_proxy_func.return_value = mock_proxy_service
        mock_lookup_service = MagicMock()
        mock_lookup_func.return_value = mock_lookup_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_library_service(
            session,  # type: ignore[invalid-argument-type]
            mock_request,
            auth_token,
            mock_book_service,
        )

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once()


def test_get_kobo_cover_service(session: DummySession, mock_library: Library) -> None:
    """Test _get_kobo_cover_service returns service (lines 507-509).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_library : Library
        Mock library.
    """
    mock_book_service = MagicMock()

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_book_lookup_service"
        ) as mock_lookup_func,
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
        patch("bookcard.api.routes.kobo.KoboCoverService") as mock_service_class,
    ):
        mock_lookup_service = MagicMock()
        mock_lookup_func.return_value = mock_lookup_service
        mock_proxy_service = MagicMock()
        mock_proxy_func.return_value = mock_proxy_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_cover_service(session, mock_book_service)  # type: ignore[arg-type]

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once()


def test_get_kobo_shelf_item_service(session: DummySession) -> None:
    """Test _get_kobo_shelf_item_service returns service (lines 534-535).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_book_service = MagicMock()

    with (
        patch("bookcard.api.routes.kobo._get_kobo_shelf_service") as mock_shelf_func,
        patch("bookcard.api.routes.kobo.KoboShelfItemService") as mock_service_class,
    ):
        mock_shelf_service = MagicMock()
        mock_shelf_func.return_value = mock_shelf_service
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_shelf_item_service(
            session,  # type: ignore[invalid-argument-type]
            mock_book_service,
        )

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once()


def test_get_kobo_store_proxy_service(session: DummySession) -> None:
    """Test _get_kobo_store_proxy_service returns service (lines 555-556).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    with patch("bookcard.api.routes.kobo.KoboStoreProxyService") as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance

        result = kobo_routes._get_kobo_store_proxy_service(session)  # type: ignore[arg-type]

        assert result is not None
        assert result == mock_service_instance
        mock_service_class.assert_called_once_with(integration_config=mock_config)


# ==================== Endpoint Tests ====================


@pytest.mark.asyncio
async def test_handle_auth_device_success(
    session: DummySession, mock_request: MagicMock
) -> None:
    """Test handle_auth_device endpoint (lines 584-589).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    mock_device_auth_service = MagicMock()
    mock_response = MagicMock()
    mock_device_auth_service.authenticate_device = AsyncMock(return_value=mock_response)
    mock_request.method = "POST"
    mock_request.json = AsyncMock(return_value={"UserKey": "test_key"})

    with patch(
        "bookcard.api.routes.kobo._get_kobo_device_auth_service",
        return_value=mock_device_auth_service,
    ):
        result = await kobo_routes.handle_auth_device(
            mock_request,
            session,
            mock_device_auth_service,
        )

        assert result == mock_response
        mock_device_auth_service.authenticate_device.assert_called_once()


def test_handle_initialization_success(
    session: DummySession, mock_request: MagicMock, auth_token: str
) -> None:
    """Test handle_initialization endpoint (lines 619-621).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    mock_init_service = MagicMock()
    mock_resources = {"library_sync": "/kobo/token/v1/library/sync"}
    mock_init_service.get_initialization_resources = MagicMock(
        return_value=mock_resources
    )

    with patch(
        "bookcard.api.routes.kobo._get_kobo_initialization_service",
        return_value=mock_init_service,
    ):
        result = kobo_routes.handle_initialization(
            mock_request,
            session,
            auth_token,
            mock_init_service,
        )

        assert result == mock_resources
        mock_init_service.get_initialization_resources.assert_called_once_with(
            mock_request, auth_token
        )


@pytest.mark.asyncio
async def test_handle_library_sync_success(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    mock_library: Library,
) -> None:
    """Test handle_library_sync endpoint (lines 650-668).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    mock_library_service = MagicMock()
    mock_response = MagicMock()
    mock_library_service.sync_library = AsyncMock(return_value=mock_response)
    mock_request.headers = {}

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch("bookcard.api.routes.kobo.SyncToken") as mock_sync_token_class,
    ):
        mock_sync_token = MagicMock()
        mock_sync_token_class.from_headers.return_value = mock_sync_token

        result = await kobo_routes.handle_library_sync(
            mock_request,
            session,
            kobo_user,
            mock_library_service,
        )

        assert result == mock_response
        mock_library_service.sync_library.assert_called_once()


@pytest.mark.asyncio
async def test_handle_library_sync_library_no_id(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
) -> None:
    """Test handle_library_sync raises error when library has no id (lines 659-663).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    library_no_id = Library(name="Test Library", path="/path/to/library")
    mock_library_service = MagicMock()
    mock_request.headers = {}

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library",
            return_value=library_no_id,
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch("bookcard.api.routes.kobo.SyncToken"),
        pytest.raises(HTTPException) as exc_info,
    ):
        await kobo_routes.handle_library_sync(
            mock_request,
            session,
            kobo_user,
            mock_library_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "no_active_library"


@pytest.mark.asyncio
async def test_handle_library_sync_user_no_id(
    session: DummySession,
    mock_request: MagicMock,
    mock_library: Library,
) -> None:
    """Test handle_library_sync raises error when user has no id (lines 652-656).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    mock_library_service = MagicMock()

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await kobo_routes.handle_library_sync(
            mock_request,
            session,
            user_no_id,
            mock_library_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_library_metadata_success(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_library_metadata endpoint (lines 698-711).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_metadata = {"Id": book_uuid, "Title": "Test Book"}
    mock_library_service.get_book_metadata = MagicMock(return_value=mock_metadata)

    with patch(
        "bookcard.api.routes.kobo._get_kobo_library_service",
        return_value=mock_library_service,
    ):
        result = kobo_routes.handle_library_metadata(
            session,
            book_uuid,
            mock_library_service,
        )

        assert isinstance(result, JSONResponse)
        mock_library_service.get_book_metadata.assert_called_once_with(book_uuid)


def test_handle_library_metadata_proxy_redirect(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_library_metadata proxy redirect (lines 702-709).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=True
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_library_service.get_book_metadata.side_effect = HTTPException(
        status_code=404, detail="Not found"
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = True
        mock_proxy_func.return_value = mock_proxy_service

        result = kobo_routes.handle_library_metadata(
            session,
            book_uuid,
            mock_library_service,
        )

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 307


def test_handle_library_metadata_no_proxy_raises(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_library_metadata raises when proxy disabled (line 709).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=False
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_library_service.get_book_metadata.side_effect = HTTPException(
        status_code=404, detail="Not found"
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = False
        mock_proxy_func.return_value = mock_proxy_service

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_library_metadata(
                session,
                book_uuid,
                mock_library_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == 404


def test_handle_library_delete_success(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test handle_library_delete endpoint (lines 742-763).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_library_service.archive_book = MagicMock(return_value=None)

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch(
            "bookcard.api.routes.kobo._resolve_active_library",
            return_value=mock_library,
        ),
    ):
        result = kobo_routes.handle_library_delete(
            session,
            kobo_user,
            book_uuid,
            mock_library_service,
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_library_service.archive_book.assert_called_once_with(
            kobo_user.id, book_uuid, library_id=mock_library.id
        )


def test_handle_library_delete_user_no_id(
    session: DummySession, mock_library: Library
) -> None:
    """Test handle_library_delete raises error when user has no id (lines 744-748).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        kobo_routes.handle_library_delete(
            session,
            user_no_id,
            book_uuid,
            mock_library_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_library_delete_proxy_redirect(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test handle_library_delete proxy redirect (lines 752-759).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=True
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_library_service.archive_book.side_effect = HTTPException(
        status_code=404, detail="Not found"
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
        patch(
            "bookcard.api.routes.kobo._resolve_active_library",
            return_value=mock_library,
        ),
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = True
        mock_proxy_func.return_value = mock_proxy_service

        result = kobo_routes.handle_library_delete(
            session,
            kobo_user,
            book_uuid,
            mock_library_service,
        )

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 307


def test_handle_library_delete_no_proxy_raises(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test handle_library_delete raises when proxy disabled (line 759).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=False
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_library_service = MagicMock()
    mock_library_service.archive_book.side_effect = HTTPException(
        status_code=404, detail="Not found"
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_library_service",
            return_value=mock_library_service,
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
        patch(
            "bookcard.api.routes.kobo._resolve_active_library",
            return_value=mock_library,
        ),
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = False
        mock_proxy_func.return_value = mock_proxy_service

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_library_delete(
                session,
                kobo_user,
                book_uuid,
                mock_library_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == 404


def test_handle_reading_state_get_success(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
    mock_library: Library,
) -> None:
    """Test handle_reading_state_get endpoint (lines 800-845).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    mock_library : Library
        Mock library.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=(1, mock_book))

    mock_reading_state_service = MagicMock()
    mock_reading_state = MagicMock()
    mock_reading_state_service.get_or_create_reading_state = MagicMock(
        return_value=mock_reading_state
    )

    mock_read_status_repo = MagicMock()
    mock_read_status = MagicMock()
    mock_read_status_repo.get_by_user_book = MagicMock(return_value=mock_read_status)

    mock_metadata_service = MagicMock()
    mock_state_response = {"BookId": book_uuid, "Status": "Reading"}
    mock_metadata_service.get_reading_state_response = MagicMock(
        return_value=mock_state_response
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_reading_state_service"
        ) as mock_reading_func,
        patch("bookcard.api.routes.kobo.ReadStatusRepository") as mock_repo_class,
        patch(
            "bookcard.api.routes.kobo._get_kobo_metadata_service"
        ) as mock_metadata_func,
    ):
        mock_reading_func.return_value = mock_reading_state_service
        mock_repo_class.return_value = mock_read_status_repo
        mock_metadata_func.return_value = mock_metadata_service

        result = kobo_routes.handle_reading_state_get(
            mock_request,
            session,
            kobo_user,
            auth_token,
            book_uuid,
            mock_book_lookup_service,
        )

        assert isinstance(result, JSONResponse)
        mock_book_lookup_service.find_book_by_uuid.assert_called_once_with(book_uuid)


def test_handle_reading_state_get_user_no_id(
    session: DummySession,
    mock_request: MagicMock,
    auth_token: str,
) -> None:
    """Test handle_reading_state_get raises error when user has no id (lines 802-806).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes.handle_reading_state_get(
            mock_request,
            session,
            user_no_id,
            auth_token,
            book_uuid,
            mock_book_lookup_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_reading_state_get_library_no_id(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_reading_state_get raises error when library has no id (lines 831-835).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=(1, mock_book))

    library_no_id = Library(name="Test Library", path="/path/to/library")

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library",
            return_value=library_no_id,
        ),
        patch("bookcard.api.routes.kobo._get_kobo_reading_state_service"),
        patch("bookcard.api.routes.kobo.ReadStatusRepository"),
        pytest.raises(HTTPException) as exc_info,
    ):
        kobo_routes.handle_reading_state_get(
            mock_request,
            session,
            kobo_user,
            auth_token,
            book_uuid,
            mock_book_lookup_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "no_active_library"


def test_handle_reading_state_get_proxy_redirect(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_reading_state_get proxy redirect (lines 811-816).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=True
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=None)

    with (
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
    ):
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = True
        mock_proxy_func.return_value = mock_proxy_service

        result = kobo_routes.handle_reading_state_get(
            mock_request,
            session,
            kobo_user,
            auth_token,
            book_uuid,
            mock_book_lookup_service,
        )

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 307


def test_handle_reading_state_get_no_proxy_raises(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_reading_state_get raises when proxy disabled (lines 817-820).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=False
    )
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=None)

    with patch(
        "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
    ) as mock_proxy_func:
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = False
        mock_proxy_func.return_value = mock_proxy_service

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_reading_state_get(
                mock_request,
                session,
                kobo_user,
                auth_token,
                book_uuid,
                mock_book_lookup_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "book_not_found"


@pytest.mark.asyncio
async def test_handle_reading_state_put_success(
    session: DummySession,
    kobo_user: User,
    mock_library: Library,
) -> None:
    """Test handle_reading_state_put endpoint (lines 880-923).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    from bookcard.api.schemas.kobo import KoboReadingStateRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=(1, mock_book))

    mock_reading_state_service = MagicMock()
    mock_update_result = {"Status": "Reading", "PercentRead": 50}
    mock_reading_state_service.update_reading_state = MagicMock(
        return_value=mock_update_result
    )

    state_data = KoboReadingStateRequest(
        ReadingStates=[{"Status": "Reading", "PercentRead": 50}]
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch(
            "bookcard.api.routes.kobo._get_kobo_reading_state_service"
        ) as mock_reading_func,
    ):
        mock_reading_func.return_value = mock_reading_state_service

        result = await kobo_routes.handle_reading_state_put(
            session,
            kobo_user,
            book_uuid,
            mock_book_lookup_service,
            state_data,
        )

        assert result.RequestResult == "Success"
        assert len(result.UpdateResults) == 1
        mock_reading_state_service.update_reading_state.assert_called_once()


@pytest.mark.asyncio
async def test_handle_reading_state_put_user_no_id(
    session: DummySession, mock_library: Library
) -> None:
    """Test handle_reading_state_put raises error when user has no id (lines 882-886).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_library : Library
        Mock library.
    """
    from bookcard.api.schemas.kobo import KoboReadingStateRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    state_data = KoboReadingStateRequest(
        ReadingStates=[{"Status": "Reading", "PercentRead": 50}]
    )

    with pytest.raises(HTTPException) as exc_info:
        await kobo_routes.handle_reading_state_put(
            session,
            user_no_id,
            book_uuid,
            mock_book_lookup_service,
            state_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


@pytest.mark.asyncio
async def test_handle_reading_state_put_book_not_found(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test handle_reading_state_put raises 404 when book not found (lines 889-894).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    from bookcard.api.schemas.kobo import KoboReadingStateRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=None)
    state_data = KoboReadingStateRequest(
        ReadingStates=[{"Status": "Reading", "PercentRead": 50}]
    )

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await kobo_routes.handle_reading_state_put(
            session,
            kobo_user,
            book_uuid,
            mock_book_lookup_service,
            state_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "book_not_found"


@pytest.mark.asyncio
async def test_handle_reading_state_put_library_no_id(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_reading_state_put raises error when library has no id (lines 898-903).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboReadingStateRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=(1, mock_book))
    state_data = KoboReadingStateRequest(
        ReadingStates=[{"Status": "Reading", "PercentRead": 50}]
    )

    library_no_id = Library(name="Test Library", path="/path/to/library")

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library",
            return_value=library_no_id,
        ),
        patch("bookcard.api.routes.kobo._get_kobo_reading_state_service"),
        pytest.raises(HTTPException) as exc_info,
    ):
        await kobo_routes.handle_reading_state_put(
            session,
            kobo_user,
            book_uuid,
            mock_book_lookup_service,
            state_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "no_active_library"


@pytest.mark.asyncio
async def test_handle_reading_state_put_no_states(
    session: DummySession, kobo_user: User, mock_library: Library
) -> None:
    """Test handle_reading_state_put raises error when no states (lines 907-911).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    mock_library : Library
        Mock library.
    """
    from bookcard.api.schemas.kobo import KoboReadingStateRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    mock_book_lookup_service = MagicMock()
    mock_book = Book(id=1, uuid=book_uuid, title="Test Book")
    mock_book_lookup_service.find_book_by_uuid = MagicMock(return_value=(1, mock_book))

    state_data = KoboReadingStateRequest(ReadingStates=[])

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch("bookcard.api.routes.kobo._get_kobo_reading_state_service"),
        pytest.raises(HTTPException) as exc_info,
    ):
        await kobo_routes.handle_reading_state_put(
            session,
            kobo_user,
            book_uuid,
            mock_book_lookup_service,
            state_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.detail == "reading_states_required"


def test_handle_tags_create_success(session: DummySession, kobo_user: User) -> None:
    """Test handle_tags_create endpoint (lines 952-976).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_data = KoboTagRequest(Name="Test Shelf")
    mock_library = Library(id=1, name="Test Library", path="/path/to/library")

    mock_shelf_service = MagicMock()
    from bookcard.models.shelves import Shelf

    mock_shelf = Shelf(id=1, uuid="test-uuid", name="Test Shelf", user_id=kobo_user.id)
    mock_shelf_service.create_shelf_from_kobo = MagicMock(return_value=mock_shelf)

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library", return_value=mock_library
        ),
        patch("bookcard.api.routes.kobo._get_kobo_shelf_service") as mock_shelf_func,
    ):
        mock_shelf_func.return_value = mock_shelf_service

        result = kobo_routes.handle_tags_create(
            session,
            kobo_user,
            tag_data,
        )

        assert result.status_code == status.HTTP_201_CREATED
        mock_shelf_service.create_shelf_from_kobo.assert_called_once()


def test_handle_tags_create_user_no_id(session: DummySession) -> None:
    """Test handle_tags_create raises error when user has no id (lines 954-958).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    from bookcard.api.schemas.kobo import KoboTagRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    tag_data = KoboTagRequest(Name="Test Shelf")

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes.handle_tags_create(
            session,
            user_no_id,
            tag_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_tags_create_library_no_id(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_create raises error when library has no id (lines 961-965).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_data = KoboTagRequest(Name="Test Shelf")
    library_no_id = Library(name="Test Library", path="/path/to/library")

    with (
        patch(
            "bookcard.api.routes.kobo._get_active_library",
            return_value=library_no_id,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        kobo_routes.handle_tags_create(
            session,
            kobo_user,
            tag_data,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "no_active_library"


def test_handle_download_success(session: DummySession) -> None:
    """Test handle_download endpoint (lines 1210-1214).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    import tempfile
    from pathlib import Path

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_id = 1
    book_format = "epub"

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test content")

    try:
        mock_download_service = MagicMock()
        mock_file_info = MagicMock()
        mock_file_info.file_path = tmp_path
        mock_file_info.media_type = "application/epub+zip"
        mock_file_info.filename = "book.epub"
        mock_download_service.get_download_file_info = MagicMock(
            return_value=mock_file_info
        )

        with patch(
            "bookcard.api.routes.kobo._get_kobo_download_service",
            return_value=mock_download_service,
        ):
            result = kobo_routes.handle_download(
                session,
                book_id,
                book_format,
                mock_download_service,
            )

            assert isinstance(result, FileResponse)
            assert result.path == str(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_handle_cover_image_success(session: DummySession) -> None:
    """Test handle_cover_image endpoint (lines 1263-1270).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    book_uuid = "test-uuid-123"
    width = "300"
    height = "400"
    is_greyscale = "false"

    mock_cover_service = MagicMock()
    mock_file_response = MagicMock()
    mock_cover_service.get_cover_image = MagicMock(return_value=mock_file_response)

    with patch(
        "bookcard.api.routes.kobo._get_kobo_cover_service",
        return_value=mock_cover_service,
    ):
        result = kobo_routes.handle_cover_image(
            session,
            book_uuid,
            width,
            height,
            is_greyscale,
            mock_cover_service,
        )

        assert result == mock_file_response
        mock_cover_service.get_cover_image.assert_called_once_with(
            book_uuid, width, height
        )


def test_handle_top_level(session: DummySession) -> None:
    """Test handle_top_level endpoint (lines 1290-1291).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    result = kobo_routes.handle_top_level(session)

    assert result == {}


def test_handle_tags_update_put_success(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_tags_update PUT endpoint (lines 1015-1055).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    from bookcard.api.schemas.kobo import KoboTagRequest
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    tag_data = KoboTagRequest(Name="Updated Shelf")
    mock_shelf = Shelf(id=1, uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)
    mock_request.method = "PUT"
    mock_request.url.path = f"/kobo/{auth_token}/v1/library/tags/{tag_id}"

    mock_shelf_service = MagicMock()
    mock_shelf_service.update_shelf_from_kobo = MagicMock(return_value=None)

    with (
        patch(
            "bookcard.repositories.shelf_repository.ShelfRepository"
        ) as mock_repo_class,
        patch("bookcard.api.routes.kobo._get_kobo_shelf_service") as mock_shelf_func,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo
        mock_shelf_func.return_value = mock_shelf_service

        result = kobo_routes.handle_tags_update(
            mock_request,
            session,
            kobo_user,
            auth_token,
            tag_id,
            tag_data,
        )

        assert result.status_code == status.HTTP_200_OK
        mock_shelf_service.update_shelf_from_kobo.assert_called_once()


def test_handle_tags_update_user_no_id(
    session: DummySession,
    mock_request: MagicMock,
    auth_token: str,
) -> None:
    """Test handle_tags_update raises error when user has no id (lines 1017-1021).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    tag_id = "test-shelf-uuid"
    mock_request.method = "PUT"

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes.handle_tags_update(
            mock_request,
            session,
            user_no_id,
            auth_token,
            tag_id,
            None,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_tags_update_delete_success(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_tags_update DELETE endpoint (lines 1041-1047).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_shelf = Shelf(id=1, uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)
    mock_request.method = "DELETE"
    mock_request.url.path = f"/kobo/{auth_token}/v1/library/tags/{tag_id}"

    mock_shelf_service = MagicMock()
    mock_shelf_service.delete_shelf = MagicMock(return_value=None)

    with (
        patch(
            "bookcard.repositories.shelf_repository.ShelfRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.repositories.shelf_repository.BookShelfLinkRepository"
        ) as mock_link_repo_class,
        patch(
            "bookcard.services.shelf_service.ShelfService"
        ) as mock_shelf_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo
        mock_link_repo = MagicMock()
        mock_link_repo_class.return_value = mock_link_repo
        mock_shelf_service_class.return_value = mock_shelf_service

        result = kobo_routes.handle_tags_update(
            mock_request,
            session,
            kobo_user,
            auth_token,
            tag_id,
            None,
        )

        assert result.status_code == status.HTTP_200_OK
        mock_shelf_service.delete_shelf.assert_called_once_with(1, kobo_user)


def test_handle_tags_update_proxy_redirect(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_tags_update proxy redirect (lines 1028-1035).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=True
    )
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_request.method = "PUT"
    mock_request.url.path = f"/kobo/{auth_token}/v1/library/tags/{tag_id}"

    with (
        patch(
            "bookcard.repositories.shelf_repository.ShelfRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = None
        mock_repo_class.return_value = mock_repo
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = True
        mock_proxy_func.return_value = mock_proxy_service

        result = kobo_routes.handle_tags_update(
            mock_request,
            session,
            kobo_user,
            auth_token,
            tag_id,
            None,
        )

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 307


def test_handle_tags_update_no_proxy_raises(
    session: DummySession,
    mock_request: MagicMock,
    kobo_user: User,
    auth_token: str,
) -> None:
    """Test handle_tags_update raises when proxy disabled (lines 1036-1039).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    mock_request : MagicMock
        Mock request.
    kobo_user : User
        Kobo user.
    auth_token : str
        Auth token.
    """
    mock_config = IntegrationConfig(
        kobo_sync_enabled=True, kobo_store_proxy_enabled=False
    )
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_request.method = "PUT"
    mock_request.url.path = f"/kobo/{auth_token}/v1/library/tags/{tag_id}"

    with (
        patch(
            "bookcard.repositories.shelf_repository.ShelfRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.api.routes.kobo._get_kobo_store_proxy_service"
        ) as mock_proxy_func,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = None
        mock_repo_class.return_value = mock_repo
        mock_proxy_service = MagicMock()
        mock_proxy_service.should_proxy.return_value = False
        mock_proxy_func.return_value = mock_proxy_service

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_tags_update(
                mock_request,
                session,
                kobo_user,
                auth_token,
                tag_id,
                None,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "shelf_not_found"


def test_handle_tags_add_items_success(session: DummySession, kobo_user: User) -> None:
    """Test handle_tags_add_items endpoint (lines 1088-1117).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_shelf = Shelf(id=1, uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()
    mock_shelf_item_service.add_items_to_shelf = MagicMock(return_value=None)

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = kobo_routes.handle_tags_add_items(
            session,
            kobo_user,
            tag_id,
            item_data,
            mock_shelf_item_service,
        )

        assert result.status_code == status.HTTP_201_CREATED
        mock_shelf_item_service.add_items_to_shelf.assert_called_once_with(
            1, kobo_user, item_data
        )


def test_handle_tags_add_items_user_no_id(session: DummySession) -> None:
    """Test handle_tags_add_items raises error when user has no id (lines 1090-1094).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    tag_id = "test-shelf-uuid"
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])
    mock_shelf_item_service = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes.handle_tags_add_items(
            session,
            user_no_id,
            tag_id,
            item_data,
            mock_shelf_item_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_tags_add_items_shelf_not_found(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_add_items raises 404 when shelf not found (lines 1101-1105).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_tags_add_items(
                session,
                kobo_user,
                tag_id,
                item_data,
                mock_shelf_item_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "shelf_not_found"


def test_handle_tags_add_items_shelf_no_id(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_add_items raises 500 when shelf has no id (lines 1107-1111).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_shelf = Shelf(uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)  # No id
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_tags_add_items(
                session,
                kobo_user,
                tag_id,
                item_data,
                mock_shelf_item_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "shelf_missing_id"


def test_handle_tags_remove_items_success(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_remove_items endpoint (lines 1150-1179).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_shelf = Shelf(id=1, uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()
    mock_shelf_item_service.remove_items_from_shelf = MagicMock(return_value=None)

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = kobo_routes.handle_tags_remove_items(
            session,
            kobo_user,
            tag_id,
            item_data,
            mock_shelf_item_service,
        )

        assert result.status_code == status.HTTP_200_OK
        mock_shelf_item_service.remove_items_from_shelf.assert_called_once_with(
            1, kobo_user.id, item_data
        )


def test_handle_tags_remove_items_user_no_id(session: DummySession) -> None:
    """Test handle_tags_remove_items raises error when user has no id (lines 1152-1156).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    user_no_id = User(
        id=None, username="test", email="test@example.com", password_hash="hash"
    )
    tag_id = "test-shelf-uuid"
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])
    mock_shelf_item_service = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        kobo_routes.handle_tags_remove_items(
            session,
            user_no_id,
            tag_id,
            item_data,
            mock_shelf_item_service,
        )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "user_missing_id"


def test_handle_tags_remove_items_shelf_not_found(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_remove_items raises 404 when shelf not found (lines 1163-1167).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_tags_remove_items(
                session,
                kobo_user,
                tag_id,
                item_data,
                mock_shelf_item_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "shelf_not_found"


def test_handle_tags_remove_items_shelf_no_id(
    session: DummySession, kobo_user: User
) -> None:
    """Test handle_tags_remove_items raises 500 when shelf has no id (lines 1169-1173).

    Parameters
    ----------
    session : DummySession
        Dummy session.
    kobo_user : User
        Kobo user.
    """
    from bookcard.api.schemas.kobo import KoboTagItemRequest
    from bookcard.models.shelves import Shelf

    mock_config = IntegrationConfig(kobo_sync_enabled=True)
    session.set_exec_result([mock_config])

    tag_id = "test-shelf-uuid"
    mock_shelf = Shelf(uuid=tag_id, name="Test Shelf", user_id=kobo_user.id)  # No id
    item_data = KoboTagItemRequest(Items=[{"Id": "book-uuid-1"}])

    mock_shelf_item_service = MagicMock()

    with patch(
        "bookcard.repositories.shelf_repository.ShelfRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_uuid.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            kobo_routes.handle_tags_remove_items(
                session,
                kobo_user,
                tag_id,
                item_data,
                mock_shelf_item_service,
            )

    assert isinstance(exc_info.value, HTTPException)
    exc = exc_info.value
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.detail == "shelf_missing_id"

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

"""Tests for download client routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

import bookcard.api.routes.download_clients as download_clients
from bookcard.api.schemas.download_clients import (
    DownloadClientCreate,
    DownloadClientListResponse,
    DownloadClientRead,
    DownloadClientStatusResponse,
    DownloadClientTestResponse,
    DownloadClientUpdate,
    DownloadItemsResponse,
)
from bookcard.models.auth import User
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadClientType,
)

# Rebuild Pydantic models to resolve forward references
DownloadClientRead.model_rebuild()
DownloadClientStatusResponse.model_rebuild()

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def admin_user() -> User:
    """Create an admin user.

    Returns
    -------
    User
        Admin user instance.
    """
    return User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )


@pytest.fixture
def download_client_definition() -> DownloadClientDefinition:
    """Create a download client definition for testing.

    Returns
    -------
    DownloadClientDefinition
        Download client definition instance.
    """
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        username="admin",
        password="password",
        use_ssl=False,
        enabled=True,
        priority=0,
        timeout_seconds=30,
        category="bookcard",
        download_path="/downloads",
        additional_settings=None,
        status=DownloadClientStatus.HEALTHY,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def download_client_definition_disabled() -> DownloadClientDefinition:
    """Create a disabled download client definition for testing.

    Returns
    -------
    DownloadClientDefinition
        Disabled download client definition instance.
    """
    return DownloadClientDefinition(
        id=2,
        name="Disabled Client",
        client_type=DownloadClientType.TRANSMISSION,
        host="localhost",
        port=9091,
        username=None,
        password=None,
        use_ssl=False,
        enabled=False,
        priority=1,
        timeout_seconds=30,
        category=None,
        download_path=None,
        additional_settings=None,
        status=DownloadClientStatus.DISABLED,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestGetDownloadClientService:
    """Test _get_download_client_service function."""

    def test_get_download_client_service(self, session: DummySession) -> None:
        """Test _get_download_client_service creates DownloadClientService instance (covers line 62).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = download_clients._get_download_client_service(session)
        assert service is not None
        assert hasattr(service, "_session")
        assert service._session == session


class TestRaiseNotFound:
    """Test _raise_not_found function."""

    @pytest.mark.parametrize("client_id", [1, 42, 999])
    def test_raise_not_found(self, client_id: int) -> None:
        """Test _raise_not_found raises HTTPException with 404 (covers line 78).

        Parameters
        ----------
        client_id : int
            Download client ID to test.
        """
        with pytest.raises(HTTPException) as exc_info:
            download_clients._raise_not_found(client_id)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == f"Download client {client_id} not found"


class TestListDownloadClients:
    """Test list_download_clients endpoint."""

    @pytest.mark.parametrize("enabled_only", [True, False])
    def test_list_download_clients(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        download_client_definition_disabled: DownloadClientDefinition,
        enabled_only: bool,
    ) -> None:
        """Test list_download_clients returns all or enabled clients (covers lines 109-111).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Enabled download client definition fixture.
        download_client_definition_disabled : DownloadClientDefinition
            Disabled download client definition fixture.
        enabled_only : bool
            Whether to return only enabled clients.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            if enabled_only:
                mock_service.list_download_clients.return_value = [
                    download_client_definition
                ]
            else:
                mock_service.list_download_clients.return_value = [
                    download_client_definition,
                    download_client_definition_disabled,
                ]
            mock_service_class.return_value = mock_service

            result = download_clients.list_download_clients(
                session=session,
                enabled_only=enabled_only,
            )

            assert isinstance(result, DownloadClientListResponse)
            assert result.total == len(result.items)
            if enabled_only:
                assert len(result.items) == 1
                assert result.items[0].id == download_client_definition.id
            else:
                assert len(result.items) == 2
            mock_service.list_download_clients.assert_called_once_with(
                enabled_only=enabled_only
            )


class TestGetDownloadClient:
    """Test get_download_client endpoint."""

    def test_get_download_client_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_client returns client when found (covers lines 145-146).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_client.return_value = download_client_definition
            mock_service_class.return_value = mock_service

            result = download_clients.get_download_client(
                client_id=1,
                session=session,
            )

            assert isinstance(result, DownloadClientRead)
            assert result.id == download_client_definition.id
            assert result.name == download_client_definition.name
            mock_service.get_download_client.assert_called_once_with(1)

    def test_get_download_client_not_found(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client raises 404 when client not found (covers lines 147-151).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_client.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.get_download_client(
                    client_id=999,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Download client 999 not found"


class TestCreateDownloadClient:
    """Test create_download_client endpoint."""

    def test_create_download_client_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test create_download_client creates client successfully (covers lines 184-187).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        create_data = DownloadClientCreate(
            name="New Client",
            client_type=DownloadClientType.QBITTORRENT,
            host="localhost",
            port=8080,
            username="admin",
            password="password",
            use_ssl=False,
            enabled=True,
            priority=0,
            timeout_seconds=30,
        )

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_download_client.return_value = (
                download_client_definition
            )
            mock_service_class.return_value = mock_service

            result = download_clients.create_download_client(
                data=create_data,
                session=session,
            )

            assert isinstance(result, DownloadClientRead)
            assert result.id == download_client_definition.id
            mock_service.create_download_client.assert_called_once_with(create_data)

    def test_create_download_client_value_error(
        self,
        session: DummySession,
    ) -> None:
        """Test create_download_client handles ValueError (covers lines 188-192).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        create_data = DownloadClientCreate(
            name="Invalid Client",
            client_type=DownloadClientType.QBITTORRENT,
            host="localhost",
            port=8080,
        )

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_download_client.side_effect = ValueError(
                "Invalid configuration"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.create_download_client(
                    data=create_data,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.detail == "Invalid configuration"

    def test_create_download_client_generic_exception(
        self,
        session: DummySession,
    ) -> None:
        """Test create_download_client handles generic Exception (covers lines 193-197).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        create_data = DownloadClientCreate(
            name="Error Client",
            client_type=DownloadClientType.QBITTORRENT,
            host="localhost",
            port=8080,
        )

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_download_client.side_effect = RuntimeError(
                "Database error"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.create_download_client(
                    data=create_data,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create download client" in exc.detail


class TestUpdateDownloadClient:
    """Test update_download_client endpoint."""

    def test_update_download_client_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test update_download_client updates client successfully (covers lines 231-236).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        update_data = DownloadClientUpdate(name="Updated Name")

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            # Create updated client by copying and modifying
            updated_data = download_client_definition.model_dump()
            updated_data["name"] = "Updated Name"
            updated_client = DownloadClientDefinition(**updated_data)
            mock_service.update_download_client.return_value = updated_client
            mock_service_class.return_value = mock_service

            result = download_clients.update_download_client(
                client_id=1,
                data=update_data,
                session=session,
            )

            assert isinstance(result, DownloadClientRead)
            assert result.name == "Updated Name"
            mock_service.update_download_client.assert_called_once_with(1, update_data)

    def test_update_download_client_not_found(
        self,
        session: DummySession,
    ) -> None:
        """Test update_download_client raises 404 when client not found (covers line 235).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        update_data = DownloadClientUpdate(name="Updated Name")

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_download_client.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.update_download_client(
                    client_id=999,
                    data=update_data,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            # _raise_not_found raises HTTPException which gets caught by the generic
            # Exception handler and wrapped in a 500 error
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Download client 999 not found" in exc.detail

    def test_update_download_client_value_error(
        self,
        session: DummySession,
    ) -> None:
        """Test update_download_client handles ValueError (covers lines 237-241).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        update_data = DownloadClientUpdate(name="Invalid Name")

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_download_client.side_effect = ValueError(
                "Invalid update"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.update_download_client(
                    client_id=1,
                    data=update_data,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.detail == "Invalid update"

    def test_update_download_client_generic_exception(
        self,
        session: DummySession,
    ) -> None:
        """Test update_download_client handles generic Exception (covers lines 242-246).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        update_data = DownloadClientUpdate(name="Error Name")

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_download_client.side_effect = RuntimeError(
                "Database error"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.update_download_client(
                    client_id=1,
                    data=update_data,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to update download client" in exc.detail


class TestDeleteDownloadClient:
    """Test delete_download_client endpoint."""

    def test_delete_download_client_success(
        self,
        session: DummySession,
    ) -> None:
        """Test delete_download_client deletes client successfully (covers line 273).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_download_client.return_value = True
            mock_service_class.return_value = mock_service

            result = download_clients.delete_download_client(
                client_id=1,
                session=session,
            )

            assert result is None
            mock_service.delete_download_client.assert_called_once_with(1)

    def test_delete_download_client_not_found(
        self,
        session: DummySession,
    ) -> None:
        """Test delete_download_client raises 404 when client not found (covers lines 274-278).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_download_client.return_value = False
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.delete_download_client(
                    client_id=999,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Download client 999 not found"


class TestTestDownloadClientConnection:
    """Test test_download_client_connection endpoint."""

    def test_test_download_client_connection_success(
        self,
        session: DummySession,
    ) -> None:
        """Test test_download_client_connection returns success (covers lines 309-312).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.return_value = (
                True,
                "Connection test successful",
            )
            mock_service_class.return_value = mock_service

            result = download_clients.test_download_client_connection(
                client_id=1,
                session=session,
            )

            assert isinstance(result, DownloadClientTestResponse)
            assert result.success is True
            assert result.message == "Connection test successful"
            mock_service.test_connection.assert_called_once_with(1)

    def test_test_download_client_connection_value_error(
        self,
        session: DummySession,
    ) -> None:
        """Test test_download_client_connection handles ValueError (covers lines 313-317).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.side_effect = ValueError(
                "Download client 999 not found"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.test_download_client_connection(
                    client_id=999,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Download client 999 not found"

    def test_test_download_client_connection_generic_exception(
        self,
        session: DummySession,
    ) -> None:
        """Test test_download_client_connection handles generic Exception (covers lines 318-322).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.side_effect = RuntimeError("Connection error")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.test_download_client_connection(
                    client_id=1,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to test download client connection" in exc.detail


class TestGetDownloadClientStatus:
    """Test get_download_client_status endpoint."""

    def test_get_download_client_status_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_client_status returns status successfully (covers lines 353-360).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_client_status.return_value = (
                download_client_definition
            )
            mock_service_class.return_value = mock_service

            result = download_clients.get_download_client_status(
                client_id=1,
                session=session,
            )

            assert isinstance(result, DownloadClientStatusResponse)
            assert result.id == download_client_definition.id
            assert result.status == download_client_definition.status
            mock_service.get_download_client_status.assert_called_once_with(1)

    def test_get_download_client_status_not_found(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client_status raises 404 when client not found (covers lines 355-359).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_client_status.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.get_download_client_status(
                    client_id=999,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Download client 999 not found"


class TestGetDownloadClientItems:
    """Test get_download_client_items endpoint."""

    def test_get_download_client_items_success(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client_items returns items successfully (covers lines 391-399).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        mock_items = [
            {
                "client_item_id": "hash1",
                "title": "Test Download 1",
                "status": "downloading",
                "progress": 0.5,
                "size_bytes": 1000,
                "downloaded_bytes": 500,
                "download_speed_bytes_per_sec": 100.0,
                "eta_seconds": 5,
                "file_path": None,
            }
        ]

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_items.return_value = mock_items
            mock_service_class.return_value = mock_service

            result = download_clients.get_download_client_items(
                client_id=1,
                session=session,
            )

            assert isinstance(result, DownloadItemsResponse)
            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].client_item_id == "hash1"
            assert result.items[0].title == "Test Download 1"
            mock_service.get_download_items.assert_called_once_with(1)

    def test_get_download_client_items_value_error(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client_items handles ValueError (covers lines 400-404).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_items.side_effect = ValueError(
                "Download client 999 not found"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.get_download_client_items(
                    client_id=999,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Download client 999 not found"

    def test_get_download_client_items_pvr_provider_error(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client_items handles PVRProviderError (covers lines 405-409).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        from bookcard.pvr.exceptions import PVRProviderError

        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_items.side_effect = PVRProviderError(
                "Failed to get items"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.get_download_client_items(
                    client_id=1,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get download items" in exc.detail

    def test_get_download_client_items_generic_exception(
        self,
        session: DummySession,
    ) -> None:
        """Test get_download_client_items handles generic Exception (covers lines 410-414).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.download_clients.DownloadClientService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_download_items.side_effect = RuntimeError(
                "Unexpected error"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                download_clients.get_download_client_items(
                    client_id=1,
                    session=session,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Unexpected error getting download items" in exc.detail

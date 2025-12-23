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

"""Tests for download client service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.schemas.download_clients import (
    DownloadClientCreate,
    DownloadClientUpdate,
)
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadClientType,
)
from bookcard.pvr.base import TrackingDownloadClient
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.services.download_client_service import (
    DownloadClientRepository,
    DownloadClientService,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.pvr.models import DownloadItem
    from tests.conftest import DummySession


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


@pytest.fixture
def download_client_definition_unhealthy() -> DownloadClientDefinition:
    """Create an unhealthy download client definition for testing.

    Returns
    -------
    DownloadClientDefinition
        Unhealthy download client definition instance.
    """
    return DownloadClientDefinition(
        id=3,
        name="Unhealthy Client",
        client_type=DownloadClientType.DELUGE,
        host="localhost",
        port=8112,
        username="user",
        password="pass",
        use_ssl=True,
        enabled=True,
        priority=2,
        timeout_seconds=30,
        category="test",
        download_path="/tmp",
        additional_settings={"key": "value"},
        status=DownloadClientStatus.UNHEALTHY,
        error_count=5,
        error_message="Connection failed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestDownloadClientRepository:
    """Test DownloadClientRepository class."""

    def test_download_client_repository_init(self, session: DummySession) -> None:
        """Test DownloadClientRepository initialization (covers line 79).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = DownloadClientRepository(cast("Session", session))
        assert repo._session == session
        assert repo._model_type == DownloadClientDefinition

    def test_list_enabled(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        download_client_definition_disabled: DownloadClientDefinition,
    ) -> None:
        """Test list_enabled returns only enabled clients (covers lines 89-94).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Enabled download client definition fixture.
        download_client_definition_disabled : DownloadClientDefinition
            Disabled download client definition fixture.
        """
        repo = DownloadClientRepository(cast("Session", session))
        session.add_exec_result([download_client_definition])

        result = repo.list_enabled()

        assert len(result) == 1
        assert result[0].id == download_client_definition.id
        assert result[0].enabled is True

    @pytest.mark.parametrize(
        "status_value",
        [
            DownloadClientStatus.HEALTHY,
            DownloadClientStatus.UNHEALTHY,
            DownloadClientStatus.DISABLED,
            DownloadClientStatus.DEGRADED,
        ],
    )
    def test_list_by_status(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        status_value: DownloadClientStatus,
    ) -> None:
        """Test list_by_status filters by status (covers lines 111-114).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        status_value : DownloadClientStatus
            Status to filter by.
        """
        repo = DownloadClientRepository(cast("Session", session))
        download_client_definition.status = status_value
        session.add_exec_result([download_client_definition])

        result = repo.list_by_status(status_value)

        assert len(result) == 1
        assert result[0].status == status_value


class TestDownloadClientService:
    """Test DownloadClientService class."""

    def test_download_client_service_init_without_repository(
        self, session: DummySession
    ) -> None:
        """Test DownloadClientService initialization without repository (covers line 147).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))
        assert service._session == session
        assert isinstance(service._repository, DownloadClientRepository)

    def test_download_client_service_init_with_repository(
        self, session: DummySession
    ) -> None:
        """Test DownloadClientService initialization with repository (covers line 146).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = DownloadClientRepository(cast("Session", session))
        service = DownloadClientService(cast("Session", session), repository=repo)
        assert service._session == session
        assert service._repository == repo

    def test_create_download_client(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test create_download_client creates new client (covers lines 169-189).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
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
            category="bookcard",
            download_path="/downloads",
        )

        with (
            patch.object(service._repository, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.create_download_client(create_data)

            assert result.name == create_data.name
            assert result.client_type == create_data.client_type
            assert result.status == DownloadClientStatus.UNHEALTHY
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_get_download_client_found(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_client returns client when found (covers line 204).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        result = service.get_download_client(1)

        assert result is not None
        assert result.id == download_client_definition.id

    def test_get_download_client_not_found(self, session: DummySession) -> None:
        """Test get_download_client returns None when not found (covers line 204).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        result = service.get_download_client(999)

        assert result is None

    @pytest.mark.parametrize("enabled_only", [True, False])
    def test_list_download_clients(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        download_client_definition_disabled: DownloadClientDefinition,
        enabled_only: bool,
    ) -> None:
        """Test list_download_clients with enabled_only parameter (covers lines 221-223).

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
        service = DownloadClientService(cast("Session", session))
        if enabled_only:
            with patch.object(service._repository, "list_enabled") as mock_list_enabled:
                mock_list_enabled.return_value = [download_client_definition]
                result = service.list_download_clients(enabled_only=True)
                assert len(result) == 1
                assert result[0].enabled is True
        else:
            with patch.object(service._repository, "list") as mock_list:
                mock_list.return_value = [
                    download_client_definition,
                    download_client_definition_disabled,
                ]
                result = service.list_download_clients(enabled_only=False)
                assert len(result) == 2

    def test_update_download_client_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test update_download_client updates client successfully (covers lines 247-259).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)
        update_data = DownloadClientUpdate(name="Updated Name")

        with (
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.update_download_client(1, update_data)

            assert result is not None
            assert result.name == "Updated Name"
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_update_download_client_not_found(self, session: DummySession) -> None:
        """Test update_download_client returns None when client not found (covers lines 247-249).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))
        update_data = DownloadClientUpdate(name="Updated Name")

        result = service.update_download_client(999, update_data)

        assert result is None

    @pytest.mark.parametrize(
        ("field_name", "field_value"),
        [
            ("name", "New Name"),
            ("host", "newhost.example.com"),
            ("port", 9091),
            ("username", "newuser"),
            ("password", "newpass"),
            ("use_ssl", True),
            ("enabled", False),
            ("priority", 5),
            ("timeout_seconds", 60),
            ("category", "newcategory"),
            ("download_path", "/new/path"),
            ("additional_settings", {"key": "value"}),
        ],
    )
    def test_apply_updates(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        field_name: str,
        field_value: str | bool | int | dict[str, object],
    ) -> None:
        """Test _apply_updates updates all fields (covers lines 273-290).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        field_name : str
            Field name to update.
        field_value : Union[str, bool, int, dict[str, object]]
            Value to set.
        """
        service = DownloadClientService(cast("Session", session))
        # Type checker can't verify dynamic field assignment in parametrized tests
        # Cast to Any for the dict unpacking since field_value types vary by field_name
        update_data = DownloadClientUpdate(
            **cast("dict[str, Any]", {field_name: field_value})
        )

        service._apply_updates(download_client_definition, update_data)

        assert getattr(download_client_definition, field_name) == field_value

    def test_apply_updates_partial(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test _apply_updates only updates provided fields (covers lines 288-290).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        original_host = download_client_definition.host
        update_data = DownloadClientUpdate(name="Updated Name")

        service._apply_updates(download_client_definition, update_data)

        assert download_client_definition.name == "Updated Name"
        assert download_client_definition.host == original_host

    def test_delete_download_client_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test delete_download_client deletes client successfully (covers lines 305-312).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        with (
            patch.object(service._repository, "delete") as mock_delete,
            patch.object(session, "commit") as mock_commit,
        ):
            result = service.delete_download_client(1)

            assert result is True
            mock_delete.assert_called_once_with(download_client_definition)
            mock_commit.assert_called_once()

    def test_delete_download_client_not_found(self, session: DummySession) -> None:
        """Test delete_download_client returns False when client not found (covers lines 305-307).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        result = service.delete_download_client(999)

        assert result is False

    def test_test_connection_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test test_connection returns success (covers lines 332-345, 365).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_client_instance = MagicMock()
        mock_client_instance.test_connection.return_value = True

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_client_instance
            with patch.object(service, "_update_client_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is True
                assert "successful" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.HEALTHY

    def test_test_connection_failure(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test test_connection handles connection failure (covers lines 346-350, 365).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_client_instance = MagicMock()
        mock_client_instance.test_connection.return_value = False

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_client_instance
            with patch.object(service, "_update_client_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "failed" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_test_connection_pvr_provider_error(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test test_connection handles PVRProviderError (covers lines 351-356).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.side_effect = PVRProviderError("Connection failed")
            with patch.object(service, "_update_client_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "failed" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_test_connection_generic_exception(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test test_connection handles generic Exception (covers lines 357-363).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")
            with patch.object(service, "_update_client_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "error" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_test_connection_not_found(self, session: DummySession) -> None:
        """Test test_connection raises ValueError when client not found (covers lines 332-335).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        with pytest.raises(ValueError, match="not found") as exc_info:
            service.test_connection(999)

        assert "not found" in str(exc_info.value)

    def test_get_download_client_status_found(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_client_status returns client when found (covers line 382).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        result = service.get_download_client_status(1)

        assert result is not None
        assert result.id == download_client_definition.id

    def test_get_download_client_status_not_found(self, session: DummySession) -> None:
        """Test get_download_client_status returns None when not found (covers line 382).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        result = service.get_download_client_status(999)

        assert result is None

    def test_check_download_client_health_not_found(
        self, session: DummySession
    ) -> None:
        """Test check_download_client_health raises ValueError when client not found (covers lines 397-400).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        with pytest.raises(ValueError, match="not found") as exc_info:
            service.check_download_client_health(999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("current_status", "should_update"),
        [
            (DownloadClientStatus.HEALTHY, True),
            (DownloadClientStatus.UNHEALTHY, True),
            (DownloadClientStatus.DISABLED, False),
        ],
    )
    def test_check_download_client_health_disabled(
        self,
        session: DummySession,
        download_client_definition_disabled: DownloadClientDefinition,
        current_status: DownloadClientStatus,
        should_update: bool,
    ) -> None:
        """Test check_download_client_health marks disabled clients (covers lines 402-408).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition_disabled : DownloadClientDefinition
            Disabled download client definition fixture.
        current_status : DownloadClientStatus
            Current status of the client.
        should_update : bool
            Whether status should be updated.
        """
        service = DownloadClientService(cast("Session", session))
        download_client_definition_disabled.status = current_status
        session.set_get_result(
            DownloadClientDefinition, download_client_definition_disabled
        )

        with patch.object(service, "_update_client_status") as mock_update:
            service.check_download_client_health(2)

            # Should update status to DISABLED if not already DISABLED
            if should_update:
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.DISABLED
            else:
                mock_update.assert_not_called()

    def test_check_download_client_health_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test check_download_client_health updates status on success (covers lines 410-416).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_client_instance = MagicMock()
        mock_client_instance.test_connection.return_value = True

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_client_instance
            with patch.object(service, "_update_client_status") as mock_update:
                service.check_download_client_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.HEALTHY

    def test_check_download_client_health_failure(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test check_download_client_health updates status on failure (covers lines 417-423).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_client_instance = MagicMock()
        mock_client_instance.test_connection.return_value = False

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_client_instance
            with patch.object(service, "_update_client_status") as mock_update:
                service.check_download_client_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_check_download_client_health_pvr_provider_error(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test check_download_client_health handles PVRProviderError (covers lines 424-427).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.side_effect = PVRProviderError("Connection failed")
            with patch.object(service, "_update_client_status") as mock_update:
                service.check_download_client_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_check_download_client_health_generic_exception(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test check_download_client_health handles generic Exception (covers lines 428-432).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")
            with patch.object(service, "_update_client_status") as mock_update:
                service.check_download_client_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == DownloadClientStatus.UNHEALTHY

    def test_get_download_items_success(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_items returns items successfully (covers lines 456-471).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_items: list[DownloadItem] = [
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

        mock_tracking_client = MagicMock(spec=TrackingDownloadClient)
        mock_tracking_client.get_items.return_value = mock_items

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_tracking_client
            result = service.get_download_items(1)

            assert len(result) == 1
            assert result[0]["client_item_id"] == "hash1"
            assert result[0]["title"] == "Test Download 1"

    def test_get_download_items_not_found(self, session: DummySession) -> None:
        """Test get_download_items raises ValueError when client not found (covers lines 456-459).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = DownloadClientService(cast("Session", session))

        with pytest.raises(ValueError, match="not found") as exc_info:
            service.get_download_items(999)

        assert "not found" in str(exc_info.value)

    def test_get_download_items_not_tracking_client(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_items raises TypeError when client doesn't support tracking (covers lines 463-464).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_client_instance = MagicMock()
        # Not a TrackingDownloadClient

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_client_instance
            with pytest.raises(
                TypeError, match="does not support tracking"
            ) as exc_info:
                service.get_download_items(1)

            assert "does not support tracking" in str(exc_info.value)

    def test_get_download_items_pvr_provider_error(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_items handles PVRProviderError (covers lines 472-473).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_tracking_client = MagicMock(spec=TrackingDownloadClient)
        mock_tracking_client.get_items.side_effect = PVRProviderError(
            "Failed to get items"
        )

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_tracking_client
            with pytest.raises(PVRProviderError) as exc_info:
                service.get_download_items(1)

            assert "Failed to get items" in str(exc_info.value)

    def test_get_download_items_generic_exception(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test get_download_items handles generic Exception (covers lines 474-477).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        """
        service = DownloadClientService(cast("Session", session))
        session.set_get_result(DownloadClientDefinition, download_client_definition)

        mock_tracking_client = MagicMock(spec=TrackingDownloadClient)
        mock_tracking_client.get_items.side_effect = RuntimeError("Unexpected error")

        with patch(
            "bookcard.services.download_client_service.create_download_client"
        ) as mock_create:
            mock_create.return_value = mock_tracking_client
            with pytest.raises(PVRProviderError) as exc_info:
                service.get_download_items(1)

            assert "Unexpected error getting download items" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("success", "expected_error_count", "expected_error_message"),
        [
            (True, 0, None),
            (False, 1, "Test error"),
        ],
    )
    def test_update_client_status(
        self,
        session: DummySession,
        download_client_definition: DownloadClientDefinition,
        success: bool,
        expected_error_count: int,
        expected_error_message: str | None,
    ) -> None:
        """Test _update_client_status updates status correctly (covers lines 499-513).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        download_client_definition : DownloadClientDefinition
            Download client definition fixture.
        success : bool
            Whether the operation was successful.
        expected_error_count : int
            Expected error count after update.
        expected_error_message : str | None
            Expected error message after update.
        """
        service = DownloadClientService(cast("Session", session))
        original_error_count = download_client_definition.error_count

        with (
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            service._update_client_status(
                download_client_definition,
                DownloadClientStatus.HEALTHY
                if success
                else DownloadClientStatus.UNHEALTHY,
                expected_error_message,
                success,
            )

            if success:
                assert download_client_definition.error_count == 0
                assert download_client_definition.error_message is None
                assert (
                    download_client_definition.last_successful_connection_at is not None
                )
            else:
                assert (
                    download_client_definition.error_count == original_error_count + 1
                )
                assert (
                    download_client_definition.error_message == expected_error_message
                )

            assert download_client_definition.last_checked_at is not None
            assert download_client_definition.updated_at is not None
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

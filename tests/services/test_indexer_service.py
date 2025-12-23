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

"""Tests for indexer service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.schemas.indexers import IndexerCreate, IndexerUpdate
from bookcard.models.pvr import (
    IndexerDefinition,
    IndexerProtocol,
    IndexerStatus,
    IndexerType,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.services.indexer_service import IndexerRepository, IndexerService

if TYPE_CHECKING:
    from sqlmodel import Session

    from tests.conftest import DummySession


@pytest.fixture
def indexer_definition() -> IndexerDefinition:
    """Create an indexer definition for testing.

    Returns
    -------
    IndexerDefinition
        Indexer definition instance.
    """
    return IndexerDefinition(
        id=1,
        name="Test Indexer",
        indexer_type=IndexerType.TORZNAB,
        protocol=IndexerProtocol.TORRENT,
        base_url="https://indexer.example.com",
        api_key="test-api-key",
        enabled=True,
        priority=0,
        timeout_seconds=30,
        retry_count=3,
        categories=[1000, 2000],
        status=IndexerStatus.HEALTHY,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def indexer_definition_disabled() -> IndexerDefinition:
    """Create a disabled indexer definition for testing.

    Returns
    -------
    IndexerDefinition
        Disabled indexer definition instance.
    """
    return IndexerDefinition(
        id=2,
        name="Disabled Indexer",
        indexer_type=IndexerType.NEWZNAB,
        protocol=IndexerProtocol.USENET,
        base_url="https://disabled.example.com",
        api_key="disabled-key",
        enabled=False,
        priority=1,
        timeout_seconds=30,
        retry_count=3,
        categories=None,
        status=IndexerStatus.DISABLED,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def indexer_definition_unhealthy() -> IndexerDefinition:
    """Create an unhealthy indexer definition for testing.

    Returns
    -------
    IndexerDefinition
        Unhealthy indexer definition instance.
    """
    return IndexerDefinition(
        id=3,
        name="Unhealthy Indexer",
        indexer_type=IndexerType.TORZNAB,
        protocol=IndexerProtocol.TORRENT,
        base_url="https://unhealthy.example.com",
        api_key="unhealthy-key",
        enabled=True,
        priority=2,
        timeout_seconds=30,
        retry_count=3,
        categories=[1000],
        status=IndexerStatus.UNHEALTHY,
        error_count=5,
        error_message="Connection failed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestIndexerRepository:
    """Test IndexerRepository class."""

    def test_indexer_repository_init(self, session: DummySession) -> None:
        """Test IndexerRepository initialization (covers line 55).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = IndexerRepository(cast("Session", session))
        assert repo._session == session
        assert repo._model_type == IndexerDefinition

    def test_list_enabled(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        indexer_definition_disabled: IndexerDefinition,
    ) -> None:
        """Test list_enabled returns only enabled indexers (covers lines 65-70).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Enabled indexer definition fixture.
        indexer_definition_disabled : IndexerDefinition
            Disabled indexer definition fixture.
        """
        repo = IndexerRepository(cast("Session", session))
        session.add_exec_result([indexer_definition])

        result = repo.list_enabled()

        assert len(result) == 1
        assert result[0].id == indexer_definition.id
        assert result[0].enabled is True

    @pytest.mark.parametrize(
        "status_value",
        [
            IndexerStatus.HEALTHY,
            IndexerStatus.UNHEALTHY,
            IndexerStatus.DISABLED,
            IndexerStatus.DEGRADED,
        ],
    )
    def test_list_by_status(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        status_value: IndexerStatus,
    ) -> None:
        """Test list_by_status filters by status (covers lines 85-86).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        status_value : IndexerStatus
            Status to filter by.
        """
        repo = IndexerRepository(cast("Session", session))
        indexer_definition.status = status_value
        session.add_exec_result([indexer_definition])

        result = repo.list_by_status(status_value)

        assert len(result) == 1
        assert result[0].status == status_value


class TestIndexerService:
    """Test IndexerService class."""

    def test_indexer_service_init_without_repository(
        self, session: DummySession
    ) -> None:
        """Test IndexerService initialization without repository (covers line 119).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))
        assert service._session == session
        assert isinstance(service._repository, IndexerRepository)

    def test_indexer_service_init_with_repository(self, session: DummySession) -> None:
        """Test IndexerService initialization with repository (covers line 118).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = IndexerRepository(cast("Session", session))
        service = IndexerService(cast("Session", session), repository=repo)
        assert service._session == session
        assert service._repository == repo

    def test_create_indexer(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test create_indexer creates new indexer (covers lines 139-157).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        create_data = IndexerCreate(
            name="New Indexer",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://new.example.com",
            api_key="new-key",
            enabled=True,
            priority=0,
            timeout_seconds=30,
            retry_count=3,
            categories=[1000, 2000],
        )

        with (
            patch.object(service._repository, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.create_indexer(create_data)

            assert result.name == create_data.name
            assert result.indexer_type == create_data.indexer_type
            assert result.status == IndexerStatus.UNHEALTHY
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_get_indexer_found(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test get_indexer returns indexer when found (covers line 172).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        result = service.get_indexer(1)

        assert result is not None
        assert result.id == indexer_definition.id

    def test_get_indexer_not_found(self, session: DummySession) -> None:
        """Test get_indexer returns None when not found (covers line 172).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))

        result = service.get_indexer(999)

        assert result is None

    @pytest.mark.parametrize("enabled_only", [True, False])
    def test_list_indexers(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        indexer_definition_disabled: IndexerDefinition,
        enabled_only: bool,
    ) -> None:
        """Test list_indexers with enabled_only parameter (covers lines 187-189).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Enabled indexer definition fixture.
        indexer_definition_disabled : IndexerDefinition
            Disabled indexer definition fixture.
        enabled_only : bool
            Whether to return only enabled indexers.
        """
        service = IndexerService(cast("Session", session))
        if enabled_only:
            with patch.object(service._repository, "list_enabled") as mock_list_enabled:
                mock_list_enabled.return_value = [indexer_definition]
                result = service.list_indexers(enabled_only=True)
                assert len(result) == 1
                assert result[0].enabled is True
        else:
            with patch.object(service._repository, "list") as mock_list:
                mock_list.return_value = [
                    indexer_definition,
                    indexer_definition_disabled,
                ]
                result = service.list_indexers(enabled_only=False)
                assert len(result) == 2

    def test_update_indexer_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test update_indexer updates indexer successfully (covers lines 213-225).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)
        update_data = IndexerUpdate(name="Updated Name")

        with (
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.update_indexer(1, update_data)

            assert result is not None
            assert result.name == "Updated Name"
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_update_indexer_not_found(self, session: DummySession) -> None:
        """Test update_indexer returns None when indexer not found (covers lines 213-215).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))
        update_data = IndexerUpdate(name="Updated Name")

        result = service.update_indexer(999, update_data)

        assert result is None

    @pytest.mark.parametrize(
        ("field_name", "field_value"),
        [
            ("name", "New Name"),
            ("base_url", "https://new.example.com"),
            ("api_key", "new-api-key"),
            ("enabled", False),
            ("priority", 5),
            ("timeout_seconds", 60),
            ("retry_count", 5),
            ("categories", [3000, 4000]),
            ("additional_settings", {"key": "value"}),
        ],
    )
    def test_apply_updates(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        field_name: str,
        field_value: str | bool | int | list[int] | dict[str, object],
    ) -> None:
        """Test _apply_updates updates all fields (covers lines 237-251).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        field_name : str
            Field name to update.
        field_value : Union[str, bool, int, list[int], dict[str, object]]
            Value to set.
        """
        service = IndexerService(cast("Session", session))
        # Type checker can't verify dynamic field assignment in parametrized tests
        # Cast to Any for the dict unpacking since field_value types vary by field_name
        update_data = IndexerUpdate(**cast("dict[str, Any]", {field_name: field_value}))

        service._apply_updates(indexer_definition, update_data)

        assert getattr(indexer_definition, field_name) == field_value

    def test_apply_updates_partial(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test _apply_updates only updates provided fields (covers lines 249-251).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        original_base_url = indexer_definition.base_url
        update_data = IndexerUpdate(name="Updated Name")

        service._apply_updates(indexer_definition, update_data)

        assert indexer_definition.name == "Updated Name"
        assert indexer_definition.base_url == original_base_url

    def test_delete_indexer_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test delete_indexer deletes indexer successfully (covers lines 266-273).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        with (
            patch.object(service._repository, "delete") as mock_delete,
            patch.object(session, "commit") as mock_commit,
        ):
            result = service.delete_indexer(1)

            assert result is True
            mock_delete.assert_called_once_with(indexer_definition)
            mock_commit.assert_called_once()

    def test_delete_indexer_not_found(self, session: DummySession) -> None:
        """Test delete_indexer returns False when indexer not found (covers lines 266-268).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))

        result = service.delete_indexer(999)

        assert result is False

    def test_test_connection_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test test_connection returns success (covers lines 293-304, 324).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.test_connection.return_value = True

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.return_value = mock_indexer_instance
            with patch.object(service, "_update_indexer_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is True
                assert "successful" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.HEALTHY

    def test_test_connection_failure(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test test_connection handles connection failure (covers lines 305-309, 324).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.test_connection.return_value = False

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.return_value = mock_indexer_instance
            with patch.object(service, "_update_indexer_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "failed" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    def test_test_connection_pvr_provider_error(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test test_connection handles PVRProviderError (covers lines 310-315).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.side_effect = PVRProviderError("Connection failed")
            with patch.object(service, "_update_indexer_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "failed" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    def test_test_connection_generic_exception(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test test_connection handles generic Exception (covers lines 316-322).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")
            with patch.object(service, "_update_indexer_status") as mock_update:
                success, message = service.test_connection(1)

                assert success is False
                assert "error" in message.lower()
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    def test_test_connection_not_found(self, session: DummySession) -> None:
        """Test test_connection raises ValueError when indexer not found (covers lines 293-296).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))

        with pytest.raises(ValueError, match="not found") as exc_info:
            service.test_connection(999)

        assert "not found" in str(exc_info.value)

    def test_get_indexer_status_found(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test get_indexer_status returns indexer when found (covers line 339).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        result = service.get_indexer_status(1)

        assert result is not None
        assert result.id == indexer_definition.id

    def test_get_indexer_status_not_found(self, session: DummySession) -> None:
        """Test get_indexer_status returns None when not found (covers line 339).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))

        result = service.get_indexer_status(999)

        assert result is None

    def test_check_indexer_health_not_found(self, session: DummySession) -> None:
        """Test check_indexer_health raises ValueError when indexer not found (covers lines 354-357).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = IndexerService(cast("Session", session))

        with pytest.raises(ValueError, match="not found") as exc_info:
            service.check_indexer_health(999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("current_status", "should_update"),
        [
            (IndexerStatus.HEALTHY, True),
            (IndexerStatus.UNHEALTHY, True),
            (IndexerStatus.DISABLED, False),
        ],
    )
    def test_check_indexer_health_disabled(
        self,
        session: DummySession,
        indexer_definition_disabled: IndexerDefinition,
        current_status: IndexerStatus,
        should_update: bool,
    ) -> None:
        """Test check_indexer_health marks disabled indexers (covers lines 359-365).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition_disabled : IndexerDefinition
            Disabled indexer definition fixture.
        current_status : IndexerStatus
            Current status of the indexer.
        should_update : bool
            Whether status should be updated.
        """
        service = IndexerService(cast("Session", session))
        indexer_definition_disabled.status = current_status
        session.set_get_result(IndexerDefinition, indexer_definition_disabled)

        with patch.object(service, "_update_indexer_status") as mock_update:
            service.check_indexer_health(2)

            # Should update status to DISABLED if not already DISABLED
            if should_update:
                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.DISABLED
            else:
                mock_update.assert_not_called()

    def test_check_indexer_health_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test check_indexer_health updates status on success (covers lines 367-371).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.test_connection.return_value = True

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.return_value = mock_indexer_instance
            with patch.object(service, "_update_indexer_status") as mock_update:
                service.check_indexer_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.HEALTHY

    def test_check_indexer_health_failure(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test check_indexer_health updates status on failure (covers lines 372-375).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.test_connection.return_value = False

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.return_value = mock_indexer_instance
            with patch.object(service, "_update_indexer_status") as mock_update:
                service.check_indexer_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    def test_check_indexer_health_pvr_provider_error(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test check_indexer_health handles PVRProviderError (covers lines 376-377).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.side_effect = PVRProviderError("Connection failed")
            with patch.object(service, "_update_indexer_status") as mock_update:
                service.check_indexer_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    def test_check_indexer_health_generic_exception(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
    ) -> None:
        """Test check_indexer_health handles generic Exception (covers lines 378-382).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        """
        service = IndexerService(cast("Session", session))
        session.set_get_result(IndexerDefinition, indexer_definition)

        with patch("bookcard.services.indexer_service.create_indexer") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")
            with patch.object(service, "_update_indexer_status") as mock_update:
                service.check_indexer_health(1)

                mock_update.assert_called_once()
                assert mock_update.call_args[0][1] == IndexerStatus.UNHEALTHY

    @pytest.mark.parametrize(
        ("success", "expected_error_count", "expected_error_message"),
        [
            (True, 0, None),
            (False, 1, "Test error"),
        ],
    )
    def test_update_indexer_status(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        success: bool,
        expected_error_count: int,
        expected_error_message: str | None,
    ) -> None:
        """Test _update_indexer_status updates status correctly (covers lines 404-418).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        success : bool
            Whether the operation was successful.
        expected_error_count : int
            Expected error count after update.
        expected_error_message : str | None
            Expected error message after update.
        """
        service = IndexerService(cast("Session", session))
        original_error_count = indexer_definition.error_count

        with (
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            service._update_indexer_status(
                indexer_definition,
                IndexerStatus.HEALTHY if success else IndexerStatus.UNHEALTHY,
                expected_error_message,
                success,
            )

            if success:
                assert indexer_definition.error_count == 0
                assert indexer_definition.error_message is None
                assert indexer_definition.last_successful_query_at is not None
            else:
                assert indexer_definition.error_count == original_error_count + 1
                assert indexer_definition.error_message == expected_error_message

            assert indexer_definition.last_checked_at is not None
            assert indexer_definition.updated_at is not None
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

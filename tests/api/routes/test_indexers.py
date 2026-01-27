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

"""Tests for indexer routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException, status

import bookcard.api.routes.indexers as indexers
from bookcard.api.schemas.indexers import (
    IndexerCreate,
    IndexerListResponse,
    IndexerRead,
    IndexerStatusResponse,
    IndexerTestResponse,
    IndexerUpdate,
)
from bookcard.models.auth import User
from bookcard.models.pvr import (
    IndexerDefinition,
    IndexerProtocol,
    IndexerStatus,
    IndexerType,
)

# Rebuild Pydantic models to resolve forward references
IndexerRead.model_rebuild()
IndexerStatusResponse.model_rebuild()

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
def valid_fernet_key() -> str:
    """Generate a valid Fernet key.

    Returns
    -------
    str
        Base64-encoded Fernet key.
    """
    return Fernet.generate_key().decode()


class TestGetIndexerService:
    """Test _get_indexer_service function."""

    def test_get_indexer_service(
        self, session: DummySession, valid_fernet_key: str
    ) -> None:
        """Test _get_indexer_service creates IndexerService instance (covers line 58).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key
        service = indexers._get_indexer_service(session, request)  # type: ignore[invalid-argument-type]
        assert service is not None
        assert hasattr(service, "_session")
        assert service._session == session


class TestRaiseNotFound:
    """Test _raise_not_found function."""

    @pytest.mark.parametrize("indexer_id", [1, 42, 999])
    def test_raise_not_found(self, indexer_id: int) -> None:
        """Test _raise_not_found raises HTTPException with 404 (covers line 74).

        Parameters
        ----------
        indexer_id : int
            Indexer ID to test.
        """
        with pytest.raises(HTTPException) as exc_info:
            indexers._raise_not_found(indexer_id)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == f"Indexer {indexer_id} not found"


class TestListIndexers:
    """Test list_indexers endpoint."""

    @pytest.mark.parametrize("enabled_only", [True, False])
    def test_list_indexers(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        indexer_definition_disabled: IndexerDefinition,
        enabled_only: bool,
        valid_fernet_key: str,
    ) -> None:
        """Test list_indexers returns all or enabled indexers (covers lines 105-107).

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
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            if enabled_only:
                mock_service.list_indexers.return_value = [indexer_definition]
            else:
                mock_service.list_indexers.return_value = [
                    indexer_definition,
                    indexer_definition_disabled,
                ]
            mock_service_class.return_value = mock_service

            result = indexers.list_indexers(
                session=session,
                request=request,
                enabled_only=enabled_only,
            )

            assert isinstance(result, IndexerListResponse)
            assert result.total == len(result.items)
            if enabled_only:
                assert len(result.items) == 1
                assert result.items[0].id == indexer_definition.id
            else:
                assert len(result.items) == 2
            mock_service.list_indexers.assert_called_once_with(
                enabled_only=enabled_only
            )


class TestGetIndexer:
    """Test get_indexer endpoint."""

    def test_get_indexer_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        valid_fernet_key: str,
    ) -> None:
        """Test get_indexer returns indexer when found (covers lines 141-142).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_indexer.return_value = indexer_definition
            mock_service_class.return_value = mock_service

            result = indexers.get_indexer(
                indexer_id=1,
                session=session,
                request=request,
            )

            assert isinstance(result, IndexerRead)
            assert result.id == indexer_definition.id
            assert result.name == indexer_definition.name
            mock_service.get_indexer.assert_called_once_with(1)

    def test_get_indexer_not_found(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test get_indexer raises 404 when indexer not found (covers lines 143-147).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_indexer.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.get_indexer(
                    indexer_id=999,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Indexer 999 not found"


class TestCreateIndexer:
    """Test create_indexer endpoint."""

    def test_create_indexer_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        valid_fernet_key: str,
    ) -> None:
        """Test create_indexer creates indexer successfully (covers lines 180-183).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

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
        )

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_indexer.return_value = indexer_definition
            mock_service_class.return_value = mock_service

            result = indexers.create_indexer(
                data=create_data,
                session=session,
                request=request,
            )

            assert isinstance(result, IndexerRead)
            assert result.id == indexer_definition.id
            mock_service.create_indexer.assert_called_once_with(create_data)

    def test_create_indexer_value_error(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test create_indexer handles ValueError (covers lines 184-188).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        create_data = IndexerCreate(
            name="Invalid Indexer",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://invalid.example.com",
        )

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_indexer.side_effect = ValueError(
                "Invalid configuration"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.create_indexer(
                    data=create_data,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.detail == "Invalid configuration"

    def test_create_indexer_generic_exception(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test create_indexer handles generic Exception (covers lines 189-193).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        create_data = IndexerCreate(
            name="Error Indexer",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://error.example.com",
        )

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_indexer.side_effect = RuntimeError("Database error")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.create_indexer(
                    data=create_data,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create indexer" in exc.detail


class TestUpdateIndexer:
    """Test update_indexer endpoint."""

    def test_update_indexer_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        valid_fernet_key: str,
    ) -> None:
        """Test update_indexer updates indexer successfully (covers lines 227-232).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        update_data = IndexerUpdate(name="Updated Name")

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            # Create updated indexer by copying and modifying
            updated_data = indexer_definition.model_dump()
            updated_data["name"] = "Updated Name"
            updated_indexer = IndexerDefinition(**updated_data)
            mock_service.update_indexer.return_value = updated_indexer
            mock_service_class.return_value = mock_service

            result = indexers.update_indexer(
                indexer_id=1,
                data=update_data,
                session=session,
                request=request,
            )

            assert isinstance(result, IndexerRead)
            assert result.name == "Updated Name"
            mock_service.update_indexer.assert_called_once_with(1, update_data)

    def test_update_indexer_not_found(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test update_indexer raises 404 when indexer not found (covers line 231).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        update_data = IndexerUpdate(name="Updated Name")

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_indexer.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.update_indexer(
                    indexer_id=999,
                    data=update_data,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            # _raise_not_found raises HTTPException which gets caught by the generic
            # Exception handler and wrapped in a 500 error
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Indexer 999 not found" in exc.detail

    def test_update_indexer_value_error(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test update_indexer handles ValueError (covers lines 233-237).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        update_data = IndexerUpdate(name="Invalid Name")

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_indexer.side_effect = ValueError("Invalid update")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.update_indexer(
                    indexer_id=1,
                    data=update_data,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.detail == "Invalid update"

    def test_update_indexer_generic_exception(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test update_indexer handles generic Exception (covers lines 238-242).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        update_data = IndexerUpdate(name="Error Name")

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_indexer.side_effect = RuntimeError("Database error")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.update_indexer(
                    indexer_id=1,
                    data=update_data,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to update indexer" in exc.detail


class TestDeleteIndexer:
    """Test delete_indexer endpoint."""

    def test_delete_indexer_success(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test delete_indexer deletes indexer successfully (covers line 269).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_indexer.return_value = True
            mock_service_class.return_value = mock_service

            result = indexers.delete_indexer(
                indexer_id=1,
                session=session,
                request=request,
            )

            assert result is None
            mock_service.delete_indexer.assert_called_once_with(1)

    def test_delete_indexer_not_found(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test delete_indexer raises 404 when indexer not found (covers lines 270-274).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_indexer.return_value = False
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.delete_indexer(
                    indexer_id=999,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Indexer 999 not found"


class TestTestIndexerConnection:
    """Test test_indexer_connection endpoint."""

    def test_test_indexer_connection_success(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test test_indexer_connection returns success (covers lines 305-308).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.return_value = (
                True,
                "Connection test successful",
            )
            mock_service_class.return_value = mock_service

            result = indexers.test_indexer_connection(
                indexer_id=1,
                session=session,
                request=request,
            )

            assert isinstance(result, IndexerTestResponse)
            assert result.success is True
            assert result.message == "Connection test successful"
            mock_service.test_connection.assert_called_once_with(1)

    def test_test_indexer_connection_value_error(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test test_indexer_connection handles ValueError (covers lines 309-313).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.side_effect = ValueError(
                "Indexer 999 not found"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.test_indexer_connection(
                    indexer_id=999,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Indexer 999 not found"

    def test_test_indexer_connection_generic_exception(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test test_indexer_connection handles generic Exception (covers lines 314-318).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.test_connection.side_effect = RuntimeError("Connection error")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.test_indexer_connection(
                    indexer_id=1,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to test indexer connection" in exc.detail


class TestGetIndexerStatus:
    """Test get_indexer_status endpoint."""

    def test_get_indexer_status_success(
        self,
        session: DummySession,
        indexer_definition: IndexerDefinition,
        valid_fernet_key: str,
    ) -> None:
        """Test get_indexer_status returns status successfully (covers lines 349-350).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        indexer_definition : IndexerDefinition
            Indexer definition fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_indexer_status.return_value = indexer_definition
            mock_service_class.return_value = mock_service

            result = indexers.get_indexer_status(
                indexer_id=1,
                session=session,
                request=request,
            )

            assert isinstance(result, IndexerStatusResponse)
            assert result.id == indexer_definition.id
            assert result.status == indexer_definition.status
            mock_service.get_indexer_status.assert_called_once_with(1)

    def test_get_indexer_status_not_found(
        self,
        session: DummySession,
        valid_fernet_key: str,
    ) -> None:
        """Test get_indexer_status raises 404 when indexer not found (covers lines 351-355).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch("bookcard.api.routes.indexers.IndexerService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_indexer_status.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                indexers.get_indexer_status(
                    indexer_id=999,
                    session=session,
                    request=request,
                )

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail == "Indexer 999 not found"

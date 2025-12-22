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

"""Tests for PVR factory functions."""

import pytest

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientType,
    IndexerDefinition,
    IndexerProtocol,
    IndexerType,
)
from bookcard.pvr.base import (
    BaseDownloadClient,
    BaseIndexer,
    PVRProviderError,
)
from bookcard.pvr.factory import (
    create_download_client,
    create_indexer,
    get_registered_download_client_types,
    get_registered_indexer_types,
    register_download_client,
    register_indexer,
)
from tests.pvr.conftest import MockDownloadClient, MockIndexer


class TestRegisterIndexer:
    """Test register_indexer function."""

    def test_register_indexer_success(
        self, indexer_type_and_protocol: tuple[IndexerType, IndexerProtocol]
    ) -> None:
        """Test successful indexer registration."""
        indexer_type, _ = indexer_type_and_protocol

        # Clear any existing registration
        from bookcard.pvr.factory import _indexer_registry

        if indexer_type in _indexer_registry:
            del _indexer_registry[indexer_type]

        register_indexer(indexer_type, MockIndexer)

        assert _indexer_registry[indexer_type] == MockIndexer

    def test_register_indexer_invalid_class(self) -> None:
        """Test register_indexer with invalid class (not subclass of BaseIndexer)."""

        class NotAnIndexer:
            pass

        with pytest.raises(TypeError, match="must subclass BaseIndexer"):
            register_indexer(
                IndexerType.TORZNAB,
                NotAnIndexer,  # type: ignore[arg-type]
            )

    def test_register_indexer_overwrite(self) -> None:
        """Test that register_indexer overwrites existing registration."""
        from bookcard.pvr.factory import _indexer_registry

        # Register first time
        register_indexer(IndexerType.TORZNAB, MockIndexer)
        assert _indexer_registry[IndexerType.TORZNAB] == MockIndexer

        # Register different class (should overwrite)
        class AnotherIndexer(MockIndexer):
            pass

        register_indexer(IndexerType.TORZNAB, AnotherIndexer)
        assert _indexer_registry[IndexerType.TORZNAB] == AnotherIndexer


class TestRegisterDownloadClient:
    """Test register_download_client function."""

    def test_register_download_client_success(
        self, download_client_type: DownloadClientType
    ) -> None:
        """Test successful download client registration."""
        # Clear any existing registration
        from bookcard.pvr.factory import _download_client_registry

        if download_client_type in _download_client_registry:
            del _download_client_registry[download_client_type]

        register_download_client(download_client_type, MockDownloadClient)

        assert _download_client_registry[download_client_type] == MockDownloadClient

    def test_register_download_client_invalid_class(self) -> None:
        """Test register_download_client with invalid class."""

        class NotAClient:
            pass

        with pytest.raises(TypeError, match="must subclass BaseDownloadClient"):
            register_download_client(
                DownloadClientType.QBITTORRENT,
                NotAClient,  # type: ignore[arg-type]
            )

    def test_register_download_client_overwrite(self) -> None:
        """Test that register_download_client overwrites existing registration."""
        from bookcard.pvr.factory import _download_client_registry

        # Register first time
        register_download_client(DownloadClientType.QBITTORRENT, MockDownloadClient)
        assert (
            _download_client_registry[DownloadClientType.QBITTORRENT]
            == MockDownloadClient
        )

        # Register different class (should overwrite)
        class AnotherClient(MockDownloadClient):
            pass

        register_download_client(DownloadClientType.QBITTORRENT, AnotherClient)
        assert (
            _download_client_registry[DownloadClientType.QBITTORRENT] == AnotherClient
        )


class TestCreateIndexer:
    """Test create_indexer function."""

    def test_create_indexer_success(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test successful indexer creation."""
        # Register the indexer type
        register_indexer(indexer_definition.indexer_type, MockIndexer)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, MockIndexer)
        assert isinstance(indexer, BaseIndexer)
        assert indexer.settings.base_url == indexer_definition.base_url
        assert indexer.settings.api_key == indexer_definition.api_key
        assert indexer.settings.timeout_seconds == indexer_definition.timeout_seconds
        assert indexer.settings.retry_count == indexer_definition.retry_count
        assert indexer.settings.categories == indexer_definition.categories
        assert indexer.enabled == indexer_definition.enabled

    def test_create_indexer_not_registered(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer with unregistered indexer type."""
        from bookcard.pvr.factory import _indexer_registry

        # Remove registration if exists
        if indexer_definition.indexer_type in _indexer_registry:
            del _indexer_registry[indexer_definition.indexer_type]

        with pytest.raises(PVRProviderError, match="not registered"):
            _ = create_indexer(indexer_definition)

    def test_create_indexer_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer with additional_settings."""
        register_indexer(indexer_definition.indexer_type, MockIndexer)

        # Add additional_settings that extend IndexerSettings
        indexer_definition.additional_settings = {
            "custom_field": "custom_value",
        }

        _ = create_indexer(indexer_definition)

    def test_create_indexer_creation_error(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer when indexer creation fails."""

        # Create a class that raises an error on instantiation
        class FailingIndexer(MockIndexer):
            def __init__(self, *args: object, **kwargs: object) -> None:  # type: ignore[override,misc]
                # Intentionally don't call super() to test error handling
                raise ValueError("Creation failed")

        register_indexer(indexer_definition.indexer_type, FailingIndexer)

        with pytest.raises(PVRProviderError, match="Failed to create indexer"):
            _ = create_indexer(indexer_definition)


class TestCreateDownloadClient:
    """Test create_download_client function."""

    def test_create_download_client_success(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test successful download client creation."""
        # Register the client type
        register_download_client(
            download_client_definition.client_type, MockDownloadClient
        )

        client = create_download_client(download_client_definition)

        assert isinstance(client, MockDownloadClient)
        assert isinstance(client, BaseDownloadClient)
        assert client.settings.host == download_client_definition.host
        assert client.settings.port == download_client_definition.port
        assert client.settings.username == download_client_definition.username
        assert client.settings.password == download_client_definition.password
        assert client.settings.use_ssl == download_client_definition.use_ssl
        assert (
            client.settings.timeout_seconds
            == download_client_definition.timeout_seconds
        )
        assert client.settings.category == download_client_definition.category
        assert client.settings.download_path == download_client_definition.download_path
        assert client.enabled == download_client_definition.enabled

    def test_create_download_client_not_registered(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test create_download_client with unregistered client type."""
        from bookcard.pvr.factory import _download_client_registry

        # Remove registration if exists
        if download_client_definition.client_type in _download_client_registry:
            del _download_client_registry[download_client_definition.client_type]

        with pytest.raises(PVRProviderError, match="not registered"):
            _ = create_download_client(download_client_definition)

    def test_create_download_client_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test create_download_client with additional_settings."""
        register_download_client(
            download_client_definition.client_type, MockDownloadClient
        )

        # Add additional_settings that extend DownloadClientSettings
        download_client_definition.additional_settings = {
            "custom_field": "custom_value",
        }

        _ = create_download_client(download_client_definition)

    def test_create_download_client_creation_error(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test create_download_client when client creation fails."""

        # Create a class that raises an error on instantiation
        class FailingClient(MockDownloadClient):
            def __init__(self, *args: object, **kwargs: object) -> None:  # type: ignore[override,misc]
                # Intentionally don't call super() to test error handling
                raise ValueError("Creation failed")

        register_download_client(download_client_definition.client_type, FailingClient)

        with pytest.raises(PVRProviderError, match="Failed to create download client"):
            _ = create_download_client(download_client_definition)


class TestGetRegisteredTypes:
    """Test get_registered_*_types functions."""

    def test_get_registered_indexer_types_empty(self) -> None:
        """Test get_registered_indexer_types with no registrations."""
        from bookcard.pvr.factory import _indexer_registry

        # Clear all registrations
        _indexer_registry.clear()

        types = get_registered_indexer_types()
        assert types == []

    def test_get_registered_indexer_types_with_registrations(self) -> None:
        """Test get_registered_indexer_types with registrations."""
        from bookcard.pvr.factory import _indexer_registry

        # Clear and register some types
        _indexer_registry.clear()
        register_indexer(IndexerType.TORZNAB, MockIndexer)
        register_indexer(IndexerType.NEWZNAB, MockIndexer)

        types = get_registered_indexer_types()
        assert IndexerType.TORZNAB in types
        assert IndexerType.NEWZNAB in types
        assert len(types) == 2

    def test_get_registered_download_client_types_empty(self) -> None:
        """Test get_registered_download_client_types with no registrations."""
        from bookcard.pvr.factory import _download_client_registry

        # Clear all registrations
        _download_client_registry.clear()

        types = get_registered_download_client_types()
        assert types == []

    def test_get_registered_download_client_types_with_registrations(self) -> None:
        """Test get_registered_download_client_types with registrations."""
        from bookcard.pvr.factory import _download_client_registry

        # Clear and register some types
        _download_client_registry.clear()
        register_download_client(DownloadClientType.QBITTORRENT, MockDownloadClient)
        register_download_client(DownloadClientType.TRANSMISSION, MockDownloadClient)

        types = get_registered_download_client_types()
        assert DownloadClientType.QBITTORRENT in types
        assert DownloadClientType.TRANSMISSION in types
        assert len(types) == 2

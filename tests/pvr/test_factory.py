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

from typing import TYPE_CHECKING, cast

import pytest

from bookcard.pvr.exceptions import PVRProviderError

if TYPE_CHECKING:
    from bookcard.pvr.download_clients.blackhole import (
        TorrentBlackholeSettings,
        UsenetBlackholeSettings,
    )
    from bookcard.pvr.download_clients.nzbget import NzbgetSettings
    from bookcard.pvr.download_clients.sabnzbd import SabnzbdSettings

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
    ManagedIndexer,
)
from bookcard.pvr.factory import (
    create_download_client,
    create_indexer,
)
from bookcard.pvr.registries import (
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
        from bookcard.pvr.registries.indexer_registry import _indexer_registry

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
        from bookcard.pvr.registries.indexer_registry import _indexer_registry

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
        from bookcard.pvr.registries.download_client_registry import (
            _download_client_registry,
        )

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
        from bookcard.pvr.registries.download_client_registry import (
            _download_client_registry,
        )

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
        # Use CUSTOM type to trigger generic creation logic that uses registered class
        indexer_definition.indexer_type = IndexerType.CUSTOM

        # Register the indexer type
        register_indexer(indexer_definition.indexer_type, MockIndexer)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, MockIndexer)
        assert isinstance(indexer._indexer, BaseIndexer)
        # ManagedIndexer delegates settings access
        assert indexer.settings.base_url == indexer_definition.base_url
        assert indexer.settings.api_key == indexer_definition.api_key
        assert indexer.settings.timeout_seconds == indexer_definition.timeout_seconds
        assert indexer.settings.retry_count == indexer_definition.retry_count
        assert indexer.settings.categories == indexer_definition.categories
        assert indexer.is_enabled() == indexer_definition.enabled

    def test_create_indexer_not_registered(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer with unregistered indexer type."""
        from bookcard.pvr.registries.indexer_registry import _indexer_registry

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
        # Use CUSTOM type to trigger generic creation logic
        indexer_definition.indexer_type = IndexerType.CUSTOM

        # Create a class that raises an error on instantiation
        class FailingIndexer(MockIndexer):
            def __init__(self, *args: object, **kwargs: object) -> None:
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
        from bookcard.pvr.registries.download_client_registry import (
            _download_client_registry,
        )

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
            def __init__(self, *args: object, **kwargs: object) -> None:
                # Intentionally don't call super() to test error handling
                raise ValueError("Creation failed")

        register_download_client(download_client_definition.client_type, FailingClient)

        with pytest.raises(PVRProviderError, match="Failed to create download client"):
            _ = create_download_client(download_client_definition)


class TestGetRegisteredTypes:
    """Test get_registered_*_types functions."""

    def test_get_registered_indexer_types_empty(self) -> None:
        """Test get_registered_indexer_types with no registrations."""
        from bookcard.pvr.registries.indexer_registry import _indexer_registry

        # Clear all registrations
        _indexer_registry.clear()

        types = get_registered_indexer_types()
        assert types == []

    def test_get_registered_indexer_types_with_registrations(self) -> None:
        """Test get_registered_indexer_types with registrations."""
        from bookcard.pvr.registries.indexer_registry import _indexer_registry

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
        from bookcard.pvr.registries.download_client_registry import (
            _download_client_registry,
        )

        # Clear all registrations
        _download_client_registry.clear()

        types = get_registered_download_client_types()
        assert types == []

    def test_get_registered_download_client_types_with_registrations(self) -> None:
        """Test get_registered_download_client_types with registrations."""
        from bookcard.pvr.registries.download_client_registry import (
            _download_client_registry,
        )

        # Clear and register some types
        _download_client_registry.clear()
        register_download_client(DownloadClientType.QBITTORRENT, MockDownloadClient)
        register_download_client(DownloadClientType.TRANSMISSION, MockDownloadClient)

        types = get_registered_download_client_types()
        assert DownloadClientType.QBITTORRENT in types
        assert DownloadClientType.TRANSMISSION in types
        assert len(types) == 2


class TestIndexerSettingsFactories:
    """Test indexer settings factory functions."""

    def test_create_torznab_settings_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_torznab_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_torznab_settings,
        )
        from bookcard.pvr.indexers.torznab import TorznabSettings

        indexer_definition.indexer_type = IndexerType.TORZNAB
        indexer_definition.additional_settings = {"api_path": "/custom/api"}

        settings = _create_torznab_settings(indexer_definition)
        assert isinstance(settings, TorznabSettings)
        assert settings.api_path == "/custom/api"

    def test_create_torznab_settings_without_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_torznab_settings without additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_torznab_settings,
        )
        from bookcard.pvr.indexers.torznab import TorznabSettings

        indexer_definition.indexer_type = IndexerType.TORZNAB
        indexer_definition.additional_settings = None

        settings = _create_torznab_settings(indexer_definition)
        assert isinstance(settings, TorznabSettings)
        assert settings.api_path == "/api"

    def test_create_newznab_settings_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_newznab_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_newznab_settings,
        )
        from bookcard.pvr.indexers.newznab import NewznabSettings

        indexer_definition.indexer_type = IndexerType.NEWZNAB
        indexer_definition.additional_settings = {"api_path": "/custom/api"}

        settings = _create_newznab_settings(indexer_definition)
        assert isinstance(settings, NewznabSettings)
        assert settings.api_path == "/custom/api"

    def test_create_newznab_settings_without_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_newznab_settings without additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_newznab_settings,
        )
        from bookcard.pvr.indexers.newznab import NewznabSettings

        indexer_definition.indexer_type = IndexerType.NEWZNAB
        indexer_definition.additional_settings = None

        settings = _create_newznab_settings(indexer_definition)
        assert isinstance(settings, NewznabSettings)
        assert settings.api_path == "/api"

    def test_create_torrent_rss_settings_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_torrent_rss_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_torrent_rss_settings,
        )
        from bookcard.pvr.indexers.torrent_rss import TorrentRssSettings

        indexer_definition.indexer_type = IndexerType.TORRENT_RSS
        indexer_definition.additional_settings = {
            "feed_url": "https://custom.feed.com/rss"
        }

        settings = _create_torrent_rss_settings(indexer_definition)
        assert isinstance(settings, TorrentRssSettings)
        assert settings.base_url == "https://custom.feed.com/rss"

    def test_create_torrent_rss_settings_without_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_torrent_rss_settings without additional_settings."""
        from bookcard.pvr.factory.settings_factories.indexer_settings import (
            _create_torrent_rss_settings,
        )
        from bookcard.pvr.indexers.torrent_rss import TorrentRssSettings

        indexer_definition.indexer_type = IndexerType.TORRENT_RSS
        indexer_definition.additional_settings = None

        settings = _create_torrent_rss_settings(indexer_definition)
        assert isinstance(settings, TorrentRssSettings)
        assert settings.base_url == indexer_definition.base_url

    def test_create_default_settings_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings with additional_settings."""
        from bookcard.pvr.factory.indexer_factory import _create_default_settings

        # Test with a field that exists on IndexerSettings
        indexer_definition.additional_settings = {
            "timeout_seconds": 60,
            "retry_count": 5,
        }

        settings = _create_default_settings(indexer_definition)
        assert settings.base_url == indexer_definition.base_url
        # These should be set via setattr
        assert settings.timeout_seconds == 60
        assert settings.retry_count == 5

    def test_create_default_settings_without_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings without additional_settings."""
        from bookcard.pvr.factory.indexer_factory import _create_default_settings

        indexer_definition.additional_settings = None

        settings = _create_default_settings(indexer_definition)
        assert settings.base_url == indexer_definition.base_url


class TestDownloadClientSettingsFactories:
    """Test download client settings factory functions."""

    @pytest.mark.parametrize(
        ("client_type", "additional_settings_key", "expected_value"),
        [
            (DownloadClientType.QBITTORRENT, "url_base", "/custom/base"),
            (DownloadClientType.TRANSMISSION, "url_base", "/custom/transmission"),
            (DownloadClientType.DELUGE, "url_base", "/custom/deluge"),
            (DownloadClientType.RTORRENT, "url_base", "/custom/rpc"),
            (DownloadClientType.UTORRENT, "url_base", "/custom/gui"),
            (DownloadClientType.ARIA2, "url_base", "/custom/jsonrpc"),
            (DownloadClientType.FLOOD, "url_base", "/custom/flood"),
            (DownloadClientType.HADOUKEN, "url_base", "/custom/hadouken"),
            (DownloadClientType.FREEBOX_DOWNLOAD, "url_base", "/custom/freebox"),
            (DownloadClientType.DOWNLOAD_STATION, "url_base", "/custom/webapi"),
            (DownloadClientType.NZBVORTEX, "url_base", "/custom/nzbvortex"),
            (DownloadClientType.VUZE, "url_base", "/custom/vuze"),
        ],
    )
    def test_create_client_settings_with_additional_settings(
        self,
        download_client_definition: DownloadClientDefinition,
        client_type: DownloadClientType,
        additional_settings_key: str,
        expected_value: str,
    ) -> None:
        """Test download client settings factories with additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_aria2_settings,
            _create_deluge_settings,
            _create_download_station_settings,
            _create_flood_settings,
            _create_freebox_download_settings,
            _create_hadouken_settings,
            _create_nzbvortex_settings,
            _create_qbittorrent_settings,
            _create_rtorrent_settings,
            _create_transmission_settings,
            _create_utorrent_settings,
            _create_vuze_settings,
        )

        download_client_definition.client_type = client_type
        download_client_definition.additional_settings = {
            additional_settings_key: expected_value
        }

        factory_map = {
            DownloadClientType.QBITTORRENT: _create_qbittorrent_settings,
            DownloadClientType.TRANSMISSION: _create_transmission_settings,
            DownloadClientType.DELUGE: _create_deluge_settings,
            DownloadClientType.RTORRENT: _create_rtorrent_settings,
            DownloadClientType.UTORRENT: _create_utorrent_settings,
            DownloadClientType.ARIA2: _create_aria2_settings,
            DownloadClientType.FLOOD: _create_flood_settings,
            DownloadClientType.HADOUKEN: _create_hadouken_settings,
            DownloadClientType.FREEBOX_DOWNLOAD: _create_freebox_download_settings,
            DownloadClientType.DOWNLOAD_STATION: _create_download_station_settings,
            DownloadClientType.NZBVORTEX: _create_nzbvortex_settings,
            DownloadClientType.VUZE: _create_vuze_settings,
        }

        factory = factory_map[client_type]
        settings = factory(download_client_definition)

        if hasattr(settings, "url_base") and settings.url_base is not None:
            assert settings.url_base == expected_value

    def test_create_sabnzbd_settings_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_sabnzbd_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_sabnzbd_settings,
        )

        download_client_definition.client_type = DownloadClientType.SABNZBD
        download_client_definition.additional_settings = {
            "url_base": "/custom/sabnzbd",
            "api_key": "test-api-key",
        }

        settings = cast(
            "SabnzbdSettings", _create_sabnzbd_settings(download_client_definition)
        )
        assert settings.url_base == "/custom/sabnzbd"
        assert settings.api_key == "test-api-key"

    def test_create_sabnzbd_settings_without_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_sabnzbd_settings without additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_sabnzbd_settings,
        )

        download_client_definition.client_type = DownloadClientType.SABNZBD
        download_client_definition.additional_settings = None

        settings = cast(
            "SabnzbdSettings", _create_sabnzbd_settings(download_client_definition)
        )
        assert settings.url_base is None
        assert settings.api_key is None

    def test_create_nzbget_settings_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_nzbget_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_nzbget_settings,
        )

        download_client_definition.client_type = DownloadClientType.NZBGET
        download_client_definition.additional_settings = {"url_base": "/custom/nzbget"}

        settings = cast(
            "NzbgetSettings", _create_nzbget_settings(download_client_definition)
        )
        assert settings.url_base == "/custom/nzbget"

    def test_create_nzbget_settings_without_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_nzbget_settings without additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_nzbget_settings,
        )

        download_client_definition.client_type = DownloadClientType.NZBGET
        download_client_definition.additional_settings = None

        settings = cast(
            "NzbgetSettings", _create_nzbget_settings(download_client_definition)
        )
        assert settings.url_base is None

    def test_create_torrent_blackhole_settings_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_torrent_blackhole_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_torrent_blackhole_settings,
        )

        download_client_definition.client_type = DownloadClientType.TORRENT_BLACKHOLE
        download_client_definition.additional_settings = {
            "torrent_folder": "/custom/torrents",
            "watch_folder": "/custom/watch",
            "save_magnet_files": True,
            "magnet_file_extension": ".mag",
        }

        settings = cast(
            "TorrentBlackholeSettings",
            _create_torrent_blackhole_settings(download_client_definition),
        )
        assert settings.torrent_folder == "/custom/torrents"
        assert settings.watch_folder == "/custom/watch"
        assert settings.save_magnet_files is True
        assert settings.magnet_file_extension == ".mag"

    def test_create_torrent_blackhole_settings_without_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_torrent_blackhole_settings without additional_settings."""
        import tempfile

        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_torrent_blackhole_settings,
        )

        download_client_definition.client_type = DownloadClientType.TORRENT_BLACKHOLE
        download_client_definition.additional_settings = None
        download_client_definition.download_path = None

        settings = cast(
            "TorrentBlackholeSettings",
            _create_torrent_blackhole_settings(download_client_definition),
        )
        assert settings.torrent_folder == f"{tempfile.gettempdir()}/torrents"
        assert settings.watch_folder == f"{tempfile.gettempdir()}/watch"
        assert settings.save_magnet_files is False
        assert settings.magnet_file_extension == ".magnet"

    def test_create_usenet_blackhole_settings_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_usenet_blackhole_settings with additional_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_usenet_blackhole_settings,
        )

        download_client_definition.client_type = DownloadClientType.USENET_BLACKHOLE
        download_client_definition.additional_settings = {
            "nzb_folder": "/custom/nzbs",
            "watch_folder": "/custom/watch",
        }

        settings = cast(
            "UsenetBlackholeSettings",
            _create_usenet_blackhole_settings(download_client_definition),
        )
        assert settings.nzb_folder == "/custom/nzbs"
        assert settings.watch_folder == "/custom/watch"

    def test_create_usenet_blackhole_settings_without_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_usenet_blackhole_settings without additional_settings."""
        import tempfile

        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_usenet_blackhole_settings,
        )

        download_client_definition.client_type = DownloadClientType.USENET_BLACKHOLE
        download_client_definition.additional_settings = None
        download_client_definition.download_path = None

        settings = cast(
            "UsenetBlackholeSettings",
            _create_usenet_blackhole_settings(download_client_definition),
        )
        assert settings.nzb_folder == f"{tempfile.gettempdir()}/nzbs"
        assert settings.watch_folder == f"{tempfile.gettempdir()}/watch"

    def test_create_pneumatic_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_pneumatic_settings."""
        from bookcard.pvr.factory.settings_factories.download_client_settings import (
            _create_pneumatic_settings,
        )

        download_client_definition.client_type = DownloadClientType.PNEUMATIC

        settings = _create_pneumatic_settings(download_client_definition)
        assert settings.host == download_client_definition.host
        assert settings.port == download_client_definition.port

    def test_create_default_download_client_settings_with_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_default_download_client_settings with additional_settings."""
        from bookcard.pvr.factory.download_client_factory import (
            _create_default_download_client_settings,
        )

        # Test with fields that exist on DownloadClientSettings
        download_client_definition.additional_settings = {
            "timeout_seconds": 60,
            "use_ssl": True,
        }

        settings = _create_default_download_client_settings(download_client_definition)
        assert settings.host == download_client_definition.host
        # These should be set via setattr
        assert settings.timeout_seconds == 60
        assert settings.use_ssl is True

    def test_create_default_download_client_settings_without_additional_settings(
        self, download_client_definition: DownloadClientDefinition
    ) -> None:
        """Test _create_default_download_client_settings without additional_settings."""
        from bookcard.pvr.factory.download_client_factory import (
            _create_default_download_client_settings,
        )

        download_client_definition.additional_settings = None

        settings = _create_default_download_client_settings(download_client_definition)
        assert settings.host == download_client_definition.host

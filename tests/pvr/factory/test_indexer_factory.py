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

"""Unit tests for indexer factory."""

from datetime import UTC
from unittest.mock import patch

import pytest

from bookcard.models.pvr import IndexerDefinition, IndexerType
from bookcard.pvr.base import IndexerSettings, ManagedIndexer
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.factory.indexer_factory import (
    _create_default_settings,
    create_indexer,
    register_indexer_settings_factory,
)
from bookcard.pvr.indexers.newznab import NewznabSettings
from bookcard.pvr.indexers.torrent_rss import TorrentRssSettings
from bookcard.pvr.indexers.torznab import TorznabSettings
from bookcard.pvr.registries.indexer_registry import register_indexer
from tests.pvr.conftest import MockIndexer

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def indexer_definition() -> IndexerDefinition:
    """Create an indexer definition for testing."""
    from datetime import datetime

    from bookcard.models.pvr import IndexerProtocol, IndexerStatus

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


# ============================================================================
# register_indexer_settings_factory Tests
# ============================================================================


class TestRegisterIndexerSettingsFactory:
    """Test cases for register_indexer_settings_factory function."""

    def test_register_indexer_settings_factory(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test registering an indexer settings factory."""
        from bookcard.pvr.factory.indexer_factory import _indexer_settings_factories

        def custom_factory(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(base_url=defn.base_url)

        # Clear any existing registration
        if IndexerType.TORZNAB in _indexer_settings_factories:
            del _indexer_settings_factories[IndexerType.TORZNAB]

        register_indexer_settings_factory(IndexerType.TORZNAB, custom_factory)

        assert IndexerType.TORZNAB in _indexer_settings_factories
        assert _indexer_settings_factories[IndexerType.TORZNAB] is custom_factory

    def test_register_indexer_settings_factory_overwrites(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test that registering a factory overwrites existing registration."""
        from bookcard.pvr.factory.indexer_factory import _indexer_settings_factories

        def factory1(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(base_url="factory1")

        def factory2(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(base_url="factory2")

        register_indexer_settings_factory(IndexerType.TORZNAB, factory1)
        assert _indexer_settings_factories[IndexerType.TORZNAB] is factory1

        register_indexer_settings_factory(IndexerType.TORZNAB, factory2)
        assert _indexer_settings_factories[IndexerType.TORZNAB] is factory2


# ============================================================================
# create_indexer Tests
# ============================================================================


class TestCreateIndexer:
    """Test cases for create_indexer function."""

    def test_create_indexer_torznab_with_torznab_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for TORZNAB when settings are already TorznabSettings."""
        from bookcard.pvr.indexers.torznab import TorznabIndexer

        indexer_definition.indexer_type = IndexerType.TORZNAB

        # Use a factory that returns TorznabSettings directly
        def torznab_factory(defn: IndexerDefinition) -> TorznabSettings:
            return TorznabSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.TORZNAB, torznab_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, TorznabIndexer)

    def test_create_indexer_torznab_with_non_torznab_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for TORZNAB when settings need conversion."""
        from bookcard.pvr.indexers.torznab import TorznabIndexer

        indexer_definition.indexer_type = IndexerType.TORZNAB

        # Use a factory that returns IndexerSettings (not TorznabSettings)
        # This should trigger the conversion logic on line 110
        def custom_factory(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.TORZNAB, custom_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, TorznabIndexer)

    def test_create_indexer_newznab_with_newznab_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for NEWZNAB when settings are already NewznabSettings."""
        from bookcard.pvr.indexers.newznab import NewznabIndexer

        indexer_definition.indexer_type = IndexerType.NEWZNAB

        # Use a factory that returns NewznabSettings directly
        def newznab_factory(defn: IndexerDefinition) -> NewznabSettings:
            return NewznabSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.NEWZNAB, newznab_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, NewznabIndexer)

    def test_create_indexer_newznab_with_non_newznab_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for NEWZNAB when settings need conversion."""
        from bookcard.pvr.indexers.newznab import NewznabIndexer

        indexer_definition.indexer_type = IndexerType.NEWZNAB

        # Use a factory that returns IndexerSettings (not NewznabSettings)
        # This should trigger the conversion logic on line 120
        def custom_factory(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.NEWZNAB, custom_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, NewznabIndexer)

    def test_create_indexer_torrent_rss_with_torrent_rss_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for TORRENT_RSS when settings are already TorrentRssSettings."""
        from bookcard.pvr.indexers.torrent_rss import TorrentRssIndexer

        indexer_definition.indexer_type = IndexerType.TORRENT_RSS

        # Use a factory that returns TorrentRssSettings directly
        def torrent_rss_factory(defn: IndexerDefinition) -> TorrentRssSettings:
            return TorrentRssSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.TORRENT_RSS, torrent_rss_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, TorrentRssIndexer)

    def test_create_indexer_torrent_rss_with_non_torrent_rss_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer for TORRENT_RSS when settings need conversion."""
        from bookcard.pvr.indexers.torrent_rss import TorrentRssIndexer

        indexer_definition.indexer_type = IndexerType.TORRENT_RSS

        # Use a factory that returns IndexerSettings (not TorrentRssSettings)
        # This should trigger the conversion logic on line 130
        def custom_factory(defn: IndexerDefinition) -> IndexerSettings:
            return IndexerSettings(
                base_url=defn.base_url,
                api_key=defn.api_key,
                timeout_seconds=defn.timeout_seconds,
                retry_count=defn.retry_count,
                categories=defn.categories,
            )

        register_indexer_settings_factory(IndexerType.TORRENT_RSS, custom_factory)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, TorrentRssIndexer)

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

    def test_create_indexer_creation_error(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer when indexer creation fails."""

        indexer_definition.indexer_type = IndexerType.TORZNAB

        # Register the indexer type first
        from bookcard.pvr.indexers.torznab import TorznabIndexer

        register_indexer(IndexerType.TORZNAB, TorznabIndexer)

        # Mock TorznabIndexer to raise an error on instantiation
        with patch(
            "bookcard.pvr.factory.indexer_factory.TorznabIndexer"
        ) as mock_torznab:
            mock_torznab.side_effect = ValueError("Creation failed")

            with pytest.raises(PVRProviderError, match="Failed to create indexer"):
                _ = create_indexer(indexer_definition)

    def test_create_indexer_custom_type(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer with CUSTOM indexer type (fallback path)."""
        indexer_definition.indexer_type = IndexerType.CUSTOM
        register_indexer(IndexerType.CUSTOM, MockIndexer)

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, MockIndexer)

    def test_create_indexer_uses_registered_settings_factory(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer uses registered settings factory."""
        indexer_definition.indexer_type = IndexerType.TORZNAB
        register_indexer(IndexerType.TORZNAB, MockIndexer)

        called = False

        def custom_factory(defn: IndexerDefinition) -> IndexerSettings:
            nonlocal called
            called = True
            return IndexerSettings(base_url=defn.base_url)

        register_indexer_settings_factory(IndexerType.TORZNAB, custom_factory)

        _ = create_indexer(indexer_definition)

        assert called is True

    def test_create_indexer_uses_default_settings_factory(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test create_indexer uses default settings factory when none registered."""
        indexer_definition.indexer_type = IndexerType.CUSTOM
        register_indexer(IndexerType.CUSTOM, MockIndexer)

        from bookcard.pvr.factory.indexer_factory import _indexer_settings_factories

        # Ensure no factory is registered
        if IndexerType.CUSTOM in _indexer_settings_factories:
            del _indexer_settings_factories[IndexerType.CUSTOM]

        indexer = create_indexer(indexer_definition)

        assert isinstance(indexer, ManagedIndexer)
        assert isinstance(indexer._indexer, MockIndexer)


# ============================================================================
# _create_default_settings Tests
# ============================================================================


class TestCreateDefaultSettings:
    """Test cases for _create_default_settings function."""

    def test_create_default_settings_basic(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings with basic fields."""
        settings = _create_default_settings(indexer_definition)

        assert isinstance(settings, IndexerSettings)
        assert settings.base_url == indexer_definition.base_url
        assert settings.api_key == indexer_definition.api_key
        assert settings.timeout_seconds == indexer_definition.timeout_seconds
        assert settings.retry_count == indexer_definition.retry_count
        assert settings.categories == indexer_definition.categories

    def test_create_default_settings_with_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings with additional_settings."""
        indexer_definition.additional_settings = {
            "timeout_seconds": 60,
            "retry_count": 5,
        }

        settings = _create_default_settings(indexer_definition)

        # Additional settings should override defaults
        assert settings.timeout_seconds == 60
        assert settings.retry_count == 5

    def test_create_default_settings_with_additional_settings_no_match(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings with additional_settings that don't match attributes."""
        indexer_definition.additional_settings = {
            "unknown_field": "value",
        }

        settings = _create_default_settings(indexer_definition)

        # Should not raise, just ignore unknown fields
        assert settings.base_url == indexer_definition.base_url
        assert not hasattr(settings, "unknown_field")

    def test_create_default_settings_without_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings without additional_settings."""
        indexer_definition.additional_settings = None

        settings = _create_default_settings(indexer_definition)

        assert isinstance(settings, IndexerSettings)
        assert settings.base_url == indexer_definition.base_url

    def test_create_default_settings_with_empty_additional_settings(
        self, indexer_definition: IndexerDefinition
    ) -> None:
        """Test _create_default_settings with empty additional_settings."""
        indexer_definition.additional_settings = {}

        settings = _create_default_settings(indexer_definition)

        assert isinstance(settings, IndexerSettings)
        assert settings.base_url == indexer_definition.base_url

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

"""Factory for creating PVR indexers from database definitions.

This module provides factory functions for creating indexers, following SRP
by separating indexer creation from download client creation.
"""

from collections.abc import Callable

from bookcard.models.pvr import IndexerDefinition, IndexerType
from bookcard.pvr.base import BaseIndexer, IndexerSettings, ManagedIndexer
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.indexers.newznab import (
    NewznabIndexer,
    NewznabParser,
    NewznabRequestGenerator,
    NewznabSettings,
)
from bookcard.pvr.indexers.torrent_rss import (
    TorrentRssIndexer,
    TorrentRssParser,
    TorrentRssRequestGenerator,
    TorrentRssSettings,
)
from bookcard.pvr.indexers.torznab import (
    TorznabIndexer,
    TorznabParser,
    TorznabRequestGenerator,
    TorznabSettings,
)
from bookcard.pvr.registries.indexer_registry import get_indexer_class

# Registry of indexer type to settings factory function
_indexer_settings_factories: dict[
    IndexerType, Callable[[IndexerDefinition], IndexerSettings]
] = {}


def register_indexer_settings_factory(
    indexer_type: IndexerType,
    factory: Callable[[IndexerDefinition], IndexerSettings],
) -> None:
    """Register a settings factory for an indexer type.

    Parameters
    ----------
    indexer_type : IndexerType
        Indexer type to register factory for.
    factory : Callable[[IndexerDefinition], IndexerSettings]
        Factory function that creates settings from definition.
    """
    _indexer_settings_factories[indexer_type] = factory


def create_indexer(indexer_def: IndexerDefinition) -> ManagedIndexer:
    """Create an indexer instance from a database definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition from database.

    Returns
    -------
    ManagedIndexer
        Managed indexer instance.

    Raises
    ------
    PVRProviderError
        If indexer type is not registered or creation fails.
    """
    indexer_class = get_indexer_class(indexer_def.indexer_type)
    if indexer_class is None:
        msg = f"Indexer type not registered: {indexer_def.indexer_type}"
        raise PVRProviderError(msg)

    # Get settings factory for this indexer type, or use default
    settings_factory = _indexer_settings_factories.get(
        indexer_def.indexer_type, _create_default_settings
    )
    settings = settings_factory(indexer_def)

    try:
        # Create and inject dependencies based on indexer type
        # This is where we handle the specific wiring for known indexer types
        # For unknown types (extensions), we rely on them either not needing extra args
        # or having a registered factory that handles this.
        # Ideally, we would have a more dynamic dependency injection system.

        indexer: BaseIndexer

        if indexer_def.indexer_type == IndexerType.TORZNAB:
            if not isinstance(settings, TorznabSettings):
                # Ensure settings are correct type
                settings = TorznabSettings(**settings.model_dump())

            request_generator = TorznabRequestGenerator(settings)
            parser = TorznabParser()
            indexer = TorznabIndexer(
                settings=settings, request_generator=request_generator, parser=parser
            )

        elif indexer_def.indexer_type == IndexerType.NEWZNAB:
            if not isinstance(settings, NewznabSettings):
                settings = NewznabSettings(**settings.model_dump())

            request_generator = NewznabRequestGenerator(settings)
            parser = NewznabParser()
            indexer = NewznabIndexer(
                settings=settings, request_generator=request_generator, parser=parser
            )

        elif indexer_def.indexer_type == IndexerType.TORRENT_RSS:
            if not isinstance(settings, TorrentRssSettings):
                settings = TorrentRssSettings(**settings.model_dump())

            request_generator = TorrentRssRequestGenerator(settings)
            parser = TorrentRssParser()
            indexer = TorrentRssIndexer(
                settings=settings, request_generator=request_generator, parser=parser
            )

        else:
            # Fallback for generic/other indexers that strictly follow BaseIndexer
            # without extra dependencies
            indexer = indexer_class(settings=settings)

        return ManagedIndexer(indexer, enabled=indexer_def.enabled)
    except Exception as e:
        msg = f"Failed to create indexer {indexer_def.name}: {e}"
        raise PVRProviderError(msg) from e


def _create_default_settings(indexer_def: IndexerDefinition) -> IndexerSettings:
    """Create default IndexerSettings from indexer definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition.

    Returns
    -------
    IndexerSettings
        IndexerSettings instance.
    """
    settings = IndexerSettings(
        base_url=indexer_def.base_url,
        api_key=indexer_def.api_key,
        timeout_seconds=indexer_def.timeout_seconds,
        retry_count=indexer_def.retry_count,
        categories=indexer_def.categories,
    )

    # Allow subclasses to extend settings with additional_settings
    if indexer_def.additional_settings:
        for key, value in indexer_def.additional_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    return settings

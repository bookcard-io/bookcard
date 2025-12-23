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

"""Settings factories for indexer types.

This module provides settings factory functions for indexer types, following SRP
by separating settings creation from factory logic.
"""

from bookcard.models.pvr import IndexerDefinition, IndexerType
from bookcard.pvr.base import IndexerSettings
from bookcard.pvr.factory.indexer_factory import register_indexer_settings_factory
from bookcard.pvr.indexers.newznab import NewznabSettings
from bookcard.pvr.indexers.torrent_rss import TorrentRssSettings
from bookcard.pvr.indexers.torznab import TorznabSettings


def _create_torznab_settings(indexer_def: IndexerDefinition) -> IndexerSettings:
    """Create TorznabSettings from indexer definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition.

    Returns
    -------
    IndexerSettings
        TorznabSettings instance.
    """
    api_path = "/api"
    if indexer_def.additional_settings:
        api_path = indexer_def.additional_settings.get("api_path", "/api")

    return TorznabSettings(
        base_url=indexer_def.base_url,
        api_key=indexer_def.api_key,
        timeout_seconds=indexer_def.timeout_seconds,
        retry_count=indexer_def.retry_count,
        categories=indexer_def.categories,
        api_path=str(api_path),
    )


def _create_newznab_settings(indexer_def: IndexerDefinition) -> IndexerSettings:
    """Create NewznabSettings from indexer definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition.

    Returns
    -------
    IndexerSettings
        NewznabSettings instance.
    """
    api_path = "/api"
    if indexer_def.additional_settings:
        api_path = indexer_def.additional_settings.get("api_path", "/api")

    return NewznabSettings(
        base_url=indexer_def.base_url,
        api_key=indexer_def.api_key,
        timeout_seconds=indexer_def.timeout_seconds,
        retry_count=indexer_def.retry_count,
        categories=indexer_def.categories,
        api_path=str(api_path),
    )


def _create_torrent_rss_settings(indexer_def: IndexerDefinition) -> IndexerSettings:
    """Create TorrentRssSettings from indexer definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition.

    Returns
    -------
    IndexerSettings
        TorrentRssSettings instance.
    """
    # Use base_url as feed_url if feed_url not in additional_settings
    feed_url: str = indexer_def.base_url
    if indexer_def.additional_settings:
        feed_url = str(indexer_def.additional_settings.get("feed_url", feed_url))

    return TorrentRssSettings(
        base_url=indexer_def.base_url,
        api_key=indexer_def.api_key,
        timeout_seconds=indexer_def.timeout_seconds,
        retry_count=indexer_def.retry_count,
        categories=indexer_def.categories,
        feed_url=str(feed_url),
    )


def _initialize_indexer_settings_factories() -> None:
    """Initialize the settings factory registry with built-in indexers."""
    register_indexer_settings_factory(IndexerType.TORZNAB, _create_torznab_settings)
    register_indexer_settings_factory(IndexerType.NEWZNAB, _create_newznab_settings)
    register_indexer_settings_factory(
        IndexerType.TORRENT_RSS, _create_torrent_rss_settings
    )


# Initialize on module load
_initialize_indexer_settings_factories()

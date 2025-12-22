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

"""Factory for creating PVR indexers and download clients from database definitions."""

import logging
from collections.abc import Callable

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientType,
    IndexerDefinition,
    IndexerType,
)
from bookcard.pvr.base import (
    BaseDownloadClient,
    BaseIndexer,
    DownloadClientSettings,
    IndexerSettings,
    PVRProviderError,
)
from bookcard.pvr.indexers.newznab import NewznabSettings
from bookcard.pvr.indexers.torrent_rss import TorrentRssSettings
from bookcard.pvr.indexers.torznab import TorznabSettings

logger = logging.getLogger(__name__)

# Registry of indexer type to class mapping
_indexer_registry: dict[IndexerType, type[BaseIndexer]] = {}

# Registry of download client type to class mapping
_download_client_registry: dict[DownloadClientType, type[BaseDownloadClient]] = {}

# Registry of indexer type to settings factory function
_indexer_settings_factories: dict[
    IndexerType, Callable[[IndexerDefinition], IndexerSettings]
] = {}


def register_indexer(
    indexer_type: IndexerType, indexer_class: type[BaseIndexer]
) -> None:
    """Register an indexer implementation class.

    Parameters
    ----------
    indexer_type : IndexerType
        Type of indexer (Torznab, Newznab, etc.).
    indexer_class : type[BaseIndexer]
        Indexer class to register.

    Raises
    ------
    TypeError
        If indexer_class is not a subclass of BaseIndexer.
    """
    if not issubclass(indexer_class, BaseIndexer):
        msg = f"Indexer class must subclass BaseIndexer: {indexer_class}"
        raise TypeError(msg)

    _indexer_registry[indexer_type] = indexer_class
    logger.info(
        "Registered indexer type: %s -> %s", indexer_type, indexer_class.__name__
    )


def register_download_client(
    client_type: DownloadClientType, client_class: type[BaseDownloadClient]
) -> None:
    """Register a download client implementation class.

    Parameters
    ----------
    client_type : DownloadClientType
        Type of download client (QBittorrent, Transmission, etc.).
    client_class : type[BaseDownloadClient]
        Download client class to register.

    Raises
    ------
    TypeError
        If client_class is not a subclass of BaseDownloadClient.
    """
    if not issubclass(client_class, BaseDownloadClient):
        msg = f"Download client class must subclass BaseDownloadClient: {client_class}"
        raise TypeError(msg)

    _download_client_registry[client_type] = client_class
    logger.info(
        "Registered download client type: %s -> %s", client_type, client_class.__name__
    )


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
    feed_url = indexer_def.base_url
    if indexer_def.additional_settings:
        feed_url = indexer_def.additional_settings.get("feed_url", feed_url)

    return TorrentRssSettings(
        base_url=indexer_def.base_url,
        api_key=indexer_def.api_key,
        timeout_seconds=indexer_def.timeout_seconds,
        retry_count=indexer_def.retry_count,
        categories=indexer_def.categories,
        feed_url=str(feed_url),
    )


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


def _initialize_settings_factories() -> None:
    """Initialize the settings factory registry with built-in indexers."""
    _indexer_settings_factories[IndexerType.TORZNAB] = _create_torznab_settings
    _indexer_settings_factories[IndexerType.NEWZNAB] = _create_newznab_settings
    _indexer_settings_factories[IndexerType.TORRENT_RSS] = _create_torrent_rss_settings


# Initialize factories on module load
_initialize_settings_factories()


def create_indexer(indexer_def: IndexerDefinition) -> BaseIndexer:
    """Create an indexer instance from a database definition.

    Parameters
    ----------
    indexer_def : IndexerDefinition
        Indexer definition from database.

    Returns
    -------
    BaseIndexer
        Indexer instance.

    Raises
    ------
    PVRProviderError
        If indexer type is not registered or creation fails.
    """
    indexer_class = _indexer_registry.get(indexer_def.indexer_type)
    if indexer_class is None:
        msg = f"Indexer type not registered: {indexer_def.indexer_type}"
        raise PVRProviderError(msg)

    # Get settings factory for this indexer type, or use default
    settings_factory = _indexer_settings_factories.get(
        indexer_def.indexer_type, _create_default_settings
    )
    settings = settings_factory(indexer_def)

    try:
        return indexer_class(settings=settings, enabled=indexer_def.enabled)
    except Exception as e:
        msg = f"Failed to create indexer {indexer_def.name}: {e}"
        raise PVRProviderError(msg) from e


def create_download_client(client_def: DownloadClientDefinition) -> BaseDownloadClient:
    """Create a download client instance from a database definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition from database.

    Returns
    -------
    BaseDownloadClient
        Download client instance.

    Raises
    ------
    PVRProviderError
        If client type is not registered or creation fails.
    """
    client_class = _download_client_registry.get(client_def.client_type)
    if client_class is None:
        msg = f"Download client type not registered: {client_def.client_type}"
        raise PVRProviderError(msg)

    # Create settings from client definition
    settings = DownloadClientSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
    )

    # Allow subclasses to extend settings with additional_settings
    if client_def.additional_settings:
        for key, value in client_def.additional_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    try:
        return client_class(settings=settings, enabled=client_def.enabled)
    except Exception as e:
        msg = f"Failed to create download client {client_def.name}: {e}"
        raise PVRProviderError(msg) from e


def get_registered_indexer_types() -> list[IndexerType]:
    """Get list of registered indexer types.

    Returns
    -------
    list[IndexerType]
        List of registered indexer types.
    """
    return list(_indexer_registry.keys())


def get_registered_download_client_types() -> list[DownloadClientType]:
    """Get list of registered download client types.

    Returns
    -------
    list[DownloadClientType]
        List of registered download client types.
    """
    return list(_download_client_registry.keys())

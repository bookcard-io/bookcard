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
import tempfile
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
from bookcard.pvr.download_clients.aria2 import (
    Aria2Client,
    Aria2Settings,
)
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeClient,
    TorrentBlackholeSettings,
    UsenetBlackholeClient,
    UsenetBlackholeSettings,
)
from bookcard.pvr.download_clients.deluge import (
    DelugeClient,
    DelugeSettings,
)
from bookcard.pvr.download_clients.download_station import (
    DownloadStationClient,
    DownloadStationSettings,
)
from bookcard.pvr.download_clients.flood import (
    FloodClient,
    FloodSettings,
)
from bookcard.pvr.download_clients.freebox_download import (
    FreeboxDownloadClient,
    FreeboxDownloadSettings,
)
from bookcard.pvr.download_clients.hadouken import (
    HadoukenClient,
    HadoukenSettings,
)
from bookcard.pvr.download_clients.nzbget import (
    NzbgetClient,
    NzbgetSettings,
)
from bookcard.pvr.download_clients.nzbvortex import (
    NzbvortexClient,
    NzbvortexSettings,
)
from bookcard.pvr.download_clients.pneumatic import (
    PneumaticClient,
    PneumaticSettings,
)
from bookcard.pvr.download_clients.qbittorrent import (
    QBittorrentClient,
    QBittorrentSettings,
)
from bookcard.pvr.download_clients.rtorrent import (
    RTorrentClient,
    RTorrentSettings,
)
from bookcard.pvr.download_clients.sabnzbd import (
    SabnzbdClient,
    SabnzbdSettings,
)
from bookcard.pvr.download_clients.transmission import (
    TransmissionClient,
    TransmissionSettings,
)
from bookcard.pvr.download_clients.utorrent import (
    UTorrentClient,
    UTorrentSettings,
)
from bookcard.pvr.download_clients.vuze import (
    VuzeClient,
    VuzeSettings,
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

# Registry of download client type to settings factory function
_download_client_settings_factories: dict[
    DownloadClientType, Callable[[DownloadClientDefinition], DownloadClientSettings]
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


def _create_qbittorrent_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create QBittorrentSettings from client definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition.

    Returns
    -------
    DownloadClientSettings
        QBittorrentSettings instance.
    """
    url_base: str | None = None
    if client_def.additional_settings:
        url_base_val = client_def.additional_settings.get("url_base")
        url_base = str(url_base_val) if url_base_val is not None else None

    return QBittorrentSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=url_base,
    )


def _create_transmission_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create TransmissionSettings from client definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition.

    Returns
    -------
    DownloadClientSettings
        TransmissionSettings instance.
    """
    url_base: str = "/transmission/"
    if client_def.additional_settings:
        url_base = str(client_def.additional_settings.get("url_base", "/transmission/"))

    return TransmissionSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base),
    )


def _create_torrent_blackhole_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create TorrentBlackholeSettings from client definition."""
    torrent_folder = client_def.download_path or f"{tempfile.gettempdir()}/torrents"
    watch_folder = client_def.download_path or f"{tempfile.gettempdir()}/watch"
    if client_def.additional_settings:
        torrent_folder = str(
            client_def.additional_settings.get("torrent_folder", torrent_folder)
        )
        watch_folder = str(
            client_def.additional_settings.get("watch_folder", watch_folder)
        )

    return TorrentBlackholeSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        watch_folder=watch_folder,
        torrent_folder=torrent_folder,
        save_magnet_files=client_def.additional_settings.get("save_magnet_files", False)
        if client_def.additional_settings
        else False,
        magnet_file_extension=str(
            client_def.additional_settings.get("magnet_file_extension", ".magnet")
        )
        if client_def.additional_settings
        else ".magnet",
    )


def _create_usenet_blackhole_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create UsenetBlackholeSettings from client definition."""
    nzb_folder = client_def.download_path or f"{tempfile.gettempdir()}/nzbs"
    watch_folder = client_def.download_path or f"{tempfile.gettempdir()}/watch"
    if client_def.additional_settings:
        nzb_folder = str(client_def.additional_settings.get("nzb_folder", nzb_folder))
        watch_folder = str(
            client_def.additional_settings.get("watch_folder", watch_folder)
        )

    return UsenetBlackholeSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        watch_folder=watch_folder,
        nzb_folder=nzb_folder,
    )


def _create_sabnzbd_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create SabnzbdSettings from client definition."""
    url_base = None
    api_key = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")
        api_key = client_def.additional_settings.get("api_key")

    return SabnzbdSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
        api_key=str(api_key) if api_key else None,
    )


def _create_nzbget_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create NzbgetSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return NzbgetSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_deluge_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create DelugeSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return DelugeSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_rtorrent_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create RTorrentSettings from client definition."""
    url_base = "/RPC2"
    if client_def.additional_settings:
        url_base = str(client_def.additional_settings.get("url_base", "/RPC2"))

    return RTorrentSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base),
    )


def _create_utorrent_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create UTorrentSettings from client definition."""
    url_base = "/gui"
    if client_def.additional_settings:
        url_base = str(client_def.additional_settings.get("url_base", "/gui"))

    return UTorrentSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base),
    )


def _create_aria2_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create Aria2Settings from client definition."""
    url_base = "/jsonrpc"
    if client_def.additional_settings:
        url_base = str(client_def.additional_settings.get("url_base", "/jsonrpc"))

    return Aria2Settings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base),
    )


def _create_flood_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create FloodSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return FloodSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_hadouken_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create HadoukenSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return HadoukenSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_freebox_download_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create FreeboxDownloadSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return FreeboxDownloadSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_download_station_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create DownloadStationSettings from client definition."""
    url_base = "/webapi"
    if client_def.additional_settings:
        url_base = str(client_def.additional_settings.get("url_base", "/webapi"))

    return DownloadStationSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base),
    )


def _create_nzbvortex_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create NzbvortexSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return NzbvortexSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_pneumatic_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create PneumaticSettings from client definition."""
    return PneumaticSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
    )


def _create_vuze_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create VuzeSettings from client definition."""
    url_base = None
    if client_def.additional_settings:
        url_base = client_def.additional_settings.get("url_base")

    return VuzeSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        url_base=str(url_base) if url_base else None,
    )


def _create_default_download_client_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create default DownloadClientSettings from client definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition.

    Returns
    -------
    DownloadClientSettings
        DownloadClientSettings instance.
    """
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

    return settings


def _initialize_indexer_settings_factories() -> None:
    """Initialize the settings factory registry with built-in indexers."""
    _indexer_settings_factories[IndexerType.TORZNAB] = _create_torznab_settings
    _indexer_settings_factories[IndexerType.NEWZNAB] = _create_newznab_settings
    _indexer_settings_factories[IndexerType.TORRENT_RSS] = _create_torrent_rss_settings


def _initialize_download_client_settings_factories() -> None:
    """Initialize the download client settings factory registry."""
    # Fully implemented clients
    _download_client_settings_factories[DownloadClientType.QBITTORRENT] = (
        _create_qbittorrent_settings
    )
    _download_client_settings_factories[DownloadClientType.TRANSMISSION] = (
        _create_transmission_settings
    )
    _download_client_settings_factories[DownloadClientType.TORRENT_BLACKHOLE] = (
        _create_torrent_blackhole_settings
    )
    _download_client_settings_factories[DownloadClientType.USENET_BLACKHOLE] = (
        _create_usenet_blackhole_settings
    )
    _download_client_settings_factories[DownloadClientType.SABNZBD] = (
        _create_sabnzbd_settings
    )
    _download_client_settings_factories[DownloadClientType.NZBGET] = (
        _create_nzbget_settings
    )
    _download_client_settings_factories[DownloadClientType.DELUGE] = (
        _create_deluge_settings
    )
    _download_client_settings_factories[DownloadClientType.RTORRENT] = (
        _create_rtorrent_settings
    )
    # Stub clients (can be extended)
    _download_client_settings_factories[DownloadClientType.UTORRENT] = (
        _create_utorrent_settings
    )
    _download_client_settings_factories[DownloadClientType.VUZE] = _create_vuze_settings
    _download_client_settings_factories[DownloadClientType.ARIA2] = (
        _create_aria2_settings
    )
    _download_client_settings_factories[DownloadClientType.FLOOD] = (
        _create_flood_settings
    )
    _download_client_settings_factories[DownloadClientType.HADOUKEN] = (
        _create_hadouken_settings
    )
    _download_client_settings_factories[DownloadClientType.FREEBOX_DOWNLOAD] = (
        _create_freebox_download_settings
    )
    _download_client_settings_factories[DownloadClientType.DOWNLOAD_STATION] = (
        _create_download_station_settings
    )
    _download_client_settings_factories[DownloadClientType.NZBVORTEX] = (
        _create_nzbvortex_settings
    )
    _download_client_settings_factories[DownloadClientType.PNEUMATIC] = (
        _create_pneumatic_settings
    )


def _initialize_download_client_registry() -> None:
    """Initialize the download client registry with built-in clients."""
    # Fully implemented clients
    register_download_client(DownloadClientType.QBITTORRENT, QBittorrentClient)
    register_download_client(DownloadClientType.TRANSMISSION, TransmissionClient)
    register_download_client(
        DownloadClientType.TORRENT_BLACKHOLE, TorrentBlackholeClient
    )
    register_download_client(DownloadClientType.USENET_BLACKHOLE, UsenetBlackholeClient)
    register_download_client(DownloadClientType.SABNZBD, SabnzbdClient)
    register_download_client(DownloadClientType.NZBGET, NzbgetClient)
    register_download_client(DownloadClientType.DELUGE, DelugeClient)
    register_download_client(DownloadClientType.RTORRENT, RTorrentClient)
    # Stub clients (can be extended)
    register_download_client(DownloadClientType.UTORRENT, UTorrentClient)
    register_download_client(DownloadClientType.VUZE, VuzeClient)
    register_download_client(DownloadClientType.ARIA2, Aria2Client)
    register_download_client(DownloadClientType.FLOOD, FloodClient)
    register_download_client(DownloadClientType.HADOUKEN, HadoukenClient)
    register_download_client(DownloadClientType.FREEBOX_DOWNLOAD, FreeboxDownloadClient)
    register_download_client(DownloadClientType.DOWNLOAD_STATION, DownloadStationClient)
    register_download_client(DownloadClientType.NZBVORTEX, NzbvortexClient)
    register_download_client(DownloadClientType.PNEUMATIC, PneumaticClient)


# Initialize factories on module load
_initialize_indexer_settings_factories()
_initialize_download_client_settings_factories()
_initialize_download_client_registry()


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

    # Get settings factory for this client type, or use default
    settings_factory = _download_client_settings_factories.get(
        client_def.client_type, _create_default_download_client_settings
    )
    settings = settings_factory(client_def)

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

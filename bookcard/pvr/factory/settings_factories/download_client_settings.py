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

"""Settings factories for download client types.

This module provides settings factory functions for download client types, following SRP
by separating settings creation from factory logic.
"""

import logging
import os
import tempfile
from contextlib import suppress

from sqlmodel import Session, select

from bookcard.database import create_db_engine
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientType,
    IndexerDefinition,
    IndexerType,
)
from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.aria2 import Aria2Settings
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeSettings,
    UsenetBlackholeSettings,
)
from bookcard.pvr.download_clients.deluge import DelugeSettings
from bookcard.pvr.download_clients.direct_http.settings import DirectHttpSettings
from bookcard.pvr.download_clients.download_station import DownloadStationSettings
from bookcard.pvr.download_clients.flood import FloodSettings
from bookcard.pvr.download_clients.freebox_download import FreeboxDownloadSettings
from bookcard.pvr.download_clients.hadouken import HadoukenSettings
from bookcard.pvr.download_clients.nzbget import NzbgetSettings
from bookcard.pvr.download_clients.nzbvortex import NzbvortexSettings
from bookcard.pvr.download_clients.pneumatic import PneumaticSettings
from bookcard.pvr.download_clients.qbittorrent import QBittorrentSettings
from bookcard.pvr.download_clients.rtorrent import RTorrentSettings
from bookcard.pvr.download_clients.sabnzbd import SabnzbdSettings
from bookcard.pvr.download_clients.transmission import TransmissionSettings
from bookcard.pvr.download_clients.utorrent import UTorrentSettings
from bookcard.pvr.download_clients.vuze import VuzeSettings
from bookcard.pvr.factory.download_client_factory import (
    register_download_client_settings_factory,
)
from bookcard.services.security import DataEncryptor

logger = logging.getLogger(__name__)


def _create_qbittorrent_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create QBittorrentSettings from client definition."""
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
    """Create TransmissionSettings from client definition."""
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


def _create_direct_http_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create DirectHttpSettings from client definition.

    Looks up enabled Anna's Archive indexers and uses their api_key
    as the donator_key if not explicitly set in additional_settings.
    """
    # Get aa_donator_key from additional_settings if set
    aa_donator_key = None
    if client_def.additional_settings:
        aa_donator_key = client_def.additional_settings.get("aa_donator_key")

    # If not set, look up from Anna's Archive indexers
    if not aa_donator_key:
        aa_donator_key = _get_annas_archive_api_key()

    return DirectHttpSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
        aa_donator_key=str(aa_donator_key) if aa_donator_key else None,
        flaresolverr_url=client_def.additional_settings.get("flaresolverr_url")
        if client_def.additional_settings
        else None,
        flaresolverr_path=str(
            client_def.additional_settings.get("flaresolverr_path", "/v1")
        )
        if client_def.additional_settings
        else "/v1",
        flaresolverr_timeout=int(
            client_def.additional_settings.get("flaresolverr_timeout", 60000)
        )
        if client_def.additional_settings
        else 60000,
        use_seleniumbase=bool(
            client_def.additional_settings.get("use_seleniumbase", True)
        )
        if client_def.additional_settings
        else True,
    )


def _get_annas_archive_api_key() -> str | None:
    """Get the api_key from the first enabled Anna's Archive indexer.

    Attempts to decrypt the API key if it's encrypted. Falls back to using
    the key as-is if decryption fails (e.g., plain text in development).

    Returns
    -------
    str | None
        Decrypted API key from the first enabled Anna's Archive indexer, or None if not found.
    """
    try:
        engine = create_db_engine()
        with Session(engine) as session:
            stmt = (
                select(IndexerDefinition)
                .where(IndexerDefinition.indexer_type == IndexerType.ANNAS_ARCHIVE)
                .where(IndexerDefinition.enabled == True)  # noqa: E712
                .where(IndexerDefinition.api_key != None)  # noqa: E711
                .order_by(IndexerDefinition.priority, IndexerDefinition.id)  # type: ignore[invalid-argument-type]
                .limit(1)
            )
            result = session.exec(stmt).first()
            if result and result.api_key:
                api_key = result.api_key
                # Try to decrypt if encryption key is available
                encryption_key = os.getenv("BOOKCARD_FERNET_KEY")
                if encryption_key:
                    try:
                        encryptor = DataEncryptor(encryption_key)
                        api_key = encryptor.decrypt(api_key)
                    except ValueError:
                        # Decryption failed, might be plain text - use as-is
                        logger.debug(
                            "Failed to decrypt API key for Anna's Archive indexer %s. Using as-is.",
                            result.id,
                        )
                return api_key
    except (ValueError, RuntimeError, OSError) as e:
        with suppress(Exception):
            logger.debug("Failed to look up Anna's Archive indexer api_key: %s", e)
    return None


def _initialize_download_client_settings_factories() -> None:
    """Initialize the download client settings factory registry."""
    # Fully implemented clients
    register_download_client_settings_factory(
        DownloadClientType.QBITTORRENT, _create_qbittorrent_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.TRANSMISSION, _create_transmission_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.TORRENT_BLACKHOLE, _create_torrent_blackhole_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.USENET_BLACKHOLE, _create_usenet_blackhole_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.SABNZBD, _create_sabnzbd_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.NZBGET, _create_nzbget_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.DELUGE, _create_deluge_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.RTORRENT, _create_rtorrent_settings
    )
    # Stub clients (can be extended)
    register_download_client_settings_factory(
        DownloadClientType.UTORRENT, _create_utorrent_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.VUZE, _create_vuze_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.ARIA2, _create_aria2_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.FLOOD, _create_flood_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.HADOUKEN, _create_hadouken_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.FREEBOX_DOWNLOAD, _create_freebox_download_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.DOWNLOAD_STATION, _create_download_station_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.NZBVORTEX, _create_nzbvortex_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.PNEUMATIC, _create_pneumatic_settings
    )
    register_download_client_settings_factory(
        DownloadClientType.DIRECT_HTTP, _create_direct_http_settings
    )


# Initialize on module load
_initialize_download_client_settings_factories()

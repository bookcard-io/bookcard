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

"""Download client registry initialization.

This module initializes the download client registry with built-in clients,
following SRP by separating registry initialization from factory logic.
"""

from bookcard.models.pvr import DownloadClientType
from bookcard.pvr.download_clients.aria2 import Aria2Client
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeClient,
    UsenetBlackholeClient,
)
from bookcard.pvr.download_clients.deluge import DelugeClient
from bookcard.pvr.download_clients.direct_http import DirectHttpClient
from bookcard.pvr.download_clients.download_station import DownloadStationClient
from bookcard.pvr.download_clients.flood import FloodClient
from bookcard.pvr.download_clients.freebox_download import FreeboxDownloadClient
from bookcard.pvr.download_clients.hadouken import HadoukenClient
from bookcard.pvr.download_clients.nzbget import NzbgetClient
from bookcard.pvr.download_clients.nzbvortex import NzbvortexClient
from bookcard.pvr.download_clients.pneumatic import PneumaticClient
from bookcard.pvr.download_clients.qbittorrent import QBittorrentClient
from bookcard.pvr.download_clients.rtorrent import RTorrentClient
from bookcard.pvr.download_clients.sabnzbd import SabnzbdClient
from bookcard.pvr.download_clients.transmission import TransmissionClient
from bookcard.pvr.download_clients.utorrent import UTorrentClient
from bookcard.pvr.download_clients.vuze import VuzeClient
from bookcard.pvr.registries import register_download_client


def _initialize_download_client_registry() -> None:
    """Initialize the download client registry with built-in clients."""
    # Fully implemented clients
    register_download_client(DownloadClientType.DIRECT_HTTP, DirectHttpClient)
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


# Initialize on module load
_initialize_download_client_registry()

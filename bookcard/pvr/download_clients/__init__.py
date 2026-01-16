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

"""Download client implementations for PVR system."""

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
from bookcard.pvr.download_clients.direct_http import (
    DirectHttpClient,
    DirectHttpSettings,
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

__all__ = [
    # Fully implemented clients
    "Aria2Client",
    "Aria2Settings",
    "DelugeClient",
    "DelugeSettings",
    "DirectHttpClient",
    "DirectHttpSettings",
    "DownloadStationClient",
    "DownloadStationSettings",
    "FloodClient",
    "FloodSettings",
    "FreeboxDownloadClient",
    "FreeboxDownloadSettings",
    "HadoukenClient",
    "HadoukenSettings",
    "NzbgetClient",
    "NzbgetSettings",
    "NzbvortexClient",
    "NzbvortexSettings",
    "PneumaticClient",
    "PneumaticSettings",
    "QBittorrentClient",
    "QBittorrentSettings",
    "RTorrentClient",
    "RTorrentSettings",
    "SabnzbdClient",
    "SabnzbdSettings",
    "TorrentBlackholeClient",
    "TorrentBlackholeSettings",
    "TransmissionClient",
    "TransmissionSettings",
    "UTorrentClient",
    "UTorrentSettings",
    "UsenetBlackholeClient",
    "UsenetBlackholeSettings",
    "VuzeClient",
    "VuzeSettings",
]

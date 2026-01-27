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

"""Client selection strategy for downloads.

Follows Strategy pattern to allow different client selection algorithms.
"""

from abc import ABC, abstractmethod

from bookcard.models.pvr import DownloadClientDefinition, DownloadClientType
from bookcard.pvr.models import ReleaseInfo


class DownloadClientSelector(ABC):
    """Abstract client selector.

    Follows Strategy pattern to allow different selection algorithms.
    """

    @abstractmethod
    def select(
        self, release: ReleaseInfo, clients: list[DownloadClientDefinition]
    ) -> DownloadClientDefinition | None:
        """Select appropriate download client for release.

        Parameters
        ----------
        release : ReleaseInfo
            Release to select client for.
        clients : list[DownloadClientDefinition]
            Available download clients.

        Returns
        -------
        DownloadClientDefinition | None
            Selected client or None if none suitable.
        """
        raise NotImplementedError


class FirstEnabledSelector(DownloadClientSelector):
    """Selects first enabled client (simple strategy)."""

    def select(
        self,
        release: ReleaseInfo,
        clients: list[DownloadClientDefinition],
    ) -> DownloadClientDefinition | None:
        """Select first enabled client.

        Parameters
        ----------
        release : ReleaseInfo
            Release to select client for (not used in this strategy).
        clients : list[DownloadClientDefinition]
            Available download clients.

        Returns
        -------
        DownloadClientDefinition | None
            First enabled client or None if no clients available.
        """
        # Release parameter is part of interface but not used in simple strategy
        _ = release
        return clients[0] if clients else None


class ProtocolBasedSelector(DownloadClientSelector):
    """Selects client based on release protocol (torrent vs usenet).

    Protocol support is determined dynamically from DownloadClientType enum values,
    making it resilient to new client additions without code changes.
    """

    @staticmethod
    def _get_client_protocols(client_type: DownloadClientType) -> set[str]:
        """Determine supported protocols for a client type.

        Parameters
        ----------
        client_type : DownloadClientType
            Client type to analyze.

        Returns
        -------
        set[str]
            Set of supported protocols: 'torrent', 'usenet', or both.
        """
        client_value = client_type.value.lower()

        # Universal clients that support both protocols
        if client_value == "download_station":
            return {"torrent", "usenet"}

        # Usenet clients - identified by 'nzb' in name or explicit usenet markers
        if (
            "nzb" in client_value
            or client_value == "pneumatic"
            or client_value == "usenet_blackhole"
        ):
            return {"usenet"}

        if client_value == "direct_http":
            return {"http"}

        # Torrent clients - everything else (including blackhole)
        # This includes: qbittorrent, transmission, deluge, rtorrent, utorrent,
        # vuze, aria2, flood, hadouken, freebox_download, torrent_blackhole
        return {"torrent"}

    def _determine_protocol(self, release: ReleaseInfo) -> str | None:
        """Determine protocol (torrent or usenet) from release information.

        Parameters
        ----------
        release : ReleaseInfo
            Release to analyze.

        Returns
        -------
        str | None
            'torrent', 'usenet', or None if cannot be determined.
        """
        # Check for magnet links (always torrents)
        if release.download_url.startswith("magnet:"):
            return "torrent"

        url_lower = release.download_url.lower()

        # Check for .nzb URLs that do NOT end with .nzb (e.g. query strings)
        # Example: "https://example.com/file.nzb?token=abc"  # noqa: ERA001
        if ".nzb" in url_lower and not url_lower.endswith(".nzb"):
            return "usenet"

        # Check seeders/leechers (torrents have these, usenet doesn't)
        if release.seeders is not None or release.leechers is not None:
            return "torrent"

        # Check download URL extension
        if url_lower.endswith((".torrent", ".magnet")):
            return "torrent"
        if url_lower.endswith(".nzb"):
            return "usenet"

        # Check for Anna's Archive HTTP downloads
        # If url doesn't match torrent/usenet patterns but is an HTTP url, treat as HTTP
        if release.download_url.startswith(("http:", "https:")):
            return "http"

        # Cannot determine protocol
        return None

    def _client_supports_protocol(
        self, client: DownloadClientDefinition, protocol: str
    ) -> bool:
        """Check if client supports the given protocol.

        Parameters
        ----------
        client : DownloadClientDefinition
            Client to check.
        protocol : str
            Protocol to check ('torrent' or 'usenet').

        Returns
        -------
        bool
            True if client supports the protocol, False otherwise.
        """
        supported_protocols = self._get_client_protocols(client.client_type)
        return protocol in supported_protocols

    def select(
        self, release: ReleaseInfo, clients: list[DownloadClientDefinition]
    ) -> DownloadClientDefinition | None:
        """Select client based on protocol.

        Parameters
        ----------
        release : ReleaseInfo
            Release to select client for.
        clients : list[DownloadClientDefinition]
            Available download clients.

        Returns
        -------
        DownloadClientDefinition | None
            Selected client or None if no suitable client found.
        """
        if not clients:
            return None

        # Determine protocol from release
        protocol = self._determine_protocol(release)

        # If protocol cannot be determined, fall back to first enabled client
        if protocol is None:
            return clients[0]

        # Filter clients by protocol support
        compatible_clients = [
            client
            for client in clients
            if self._client_supports_protocol(client, protocol)
        ]

        # Return first compatible client, or fall back to first client if none compatible
        return compatible_clients[0] if compatible_clients else clients[0]

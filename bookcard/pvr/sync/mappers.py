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

"""Mappers for Prowlarr sync operations."""

from typing import ClassVar

from bookcard.models.pvr import IndexerProtocol, IndexerType


class ProtocolMapper:
    """Maps Prowlarr protocols to internal types."""

    PROTOCOL_MAP: ClassVar[dict[str, tuple[IndexerProtocol, IndexerType]]] = {
        "torrent": (IndexerProtocol.TORRENT, IndexerType.TORZNAB),
        "usenet": (IndexerProtocol.USENET, IndexerType.NEWZNAB),
    }

    @classmethod
    def map_protocol(
        cls, protocol_str: str
    ) -> tuple[IndexerProtocol, IndexerType] | None:
        """Map Prowlarr protocol string to internal protocol and type.

        Parameters
        ----------
        protocol_str : str
            Protocol string from Prowlarr (e.g. 'torrent', 'usenet').

        Returns
        -------
        tuple[IndexerProtocol, IndexerType] | None
            Tuple of (Protocol, Type) or None if unknown.
        """
        return cls.PROTOCOL_MAP.get(protocol_str.lower())


class IndexerUrlBuilder:
    """Builds indexer URLs from Prowlarr data."""

    @staticmethod
    def build_url(base_url: str, prowlarr_id: int) -> str:
        """Build Prowlarr indexer proxy URL.

        Parameters
        ----------
        base_url : str
            Prowlarr base URL.
        prowlarr_id : int
            Indexer ID in Prowlarr.

        Returns
        -------
        str
            Constructed URL.
        """
        return f"{base_url.rstrip('/')}/{prowlarr_id}/api"

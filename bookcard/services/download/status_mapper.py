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

"""Status mapping strategy for download items.

Follows Strategy pattern to allow extensible status mapping.
"""

from abc import ABC, abstractmethod

from bookcard.models.pvr import DownloadItemStatus


class ClientStatusMapper(ABC):
    """Abstract status mapper for converting client statuses.

    Follows Strategy pattern to allow different mapping strategies.
    """

    @abstractmethod
    def map(self, client_status: str) -> DownloadItemStatus:
        """Map client status string to DownloadItemStatus.

        Parameters
        ----------
        client_status : str
            Client-specific status string.

        Returns
        -------
        DownloadItemStatus
            Mapped status enum.
        """
        raise NotImplementedError


class DefaultStatusMapper(ClientStatusMapper):
    """Default status mapper with standard mappings."""

    def __init__(self) -> None:
        """Initialize default status mapper."""
        self._status_map = {
            "downloading": DownloadItemStatus.DOWNLOADING,
            "paused": DownloadItemStatus.PAUSED,
            "stopped": DownloadItemStatus.PAUSED,
            "queued": DownloadItemStatus.QUEUED,
            "checking": DownloadItemStatus.QUEUED,
            "completed": DownloadItemStatus.COMPLETED,
            "seeding": DownloadItemStatus.SEEDING,
            "error": DownloadItemStatus.FAILED,
            "failed": DownloadItemStatus.FAILED,
            "removed": DownloadItemStatus.REMOVED,
            "stalled": DownloadItemStatus.STALLED,
        }

    def map(self, client_status: str) -> DownloadItemStatus:
        """Map client status string to DownloadItemStatus."""
        return self._status_map.get(
            client_status.lower(), DownloadItemStatus.DOWNLOADING
        )


class DownloadStatusMapper:
    """Utility class for download status operations.

    Provides constants and helper methods for status management.
    """

    TERMINAL_STATUSES = frozenset([
        DownloadItemStatus.COMPLETED,
        DownloadItemStatus.FAILED,
        DownloadItemStatus.REMOVED,
    ])

    @classmethod
    def is_terminal(cls, status: DownloadItemStatus) -> bool:
        """Check if status is terminal (no further tracking needed).

        Parameters
        ----------
        status : DownloadItemStatus
            Status to check.

        Returns
        -------
        bool
            True if status is terminal, False otherwise.
        """
        return status in cls.TERMINAL_STATUSES

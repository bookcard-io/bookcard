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

"""Factory for creating download clients.

Follows DIP by abstracting client creation.
"""

from abc import ABC, abstractmethod

from bookcard.models.pvr import DownloadClientDefinition
from bookcard.pvr.base import BaseDownloadClient


class DownloadClientFactory(ABC):
    """Abstract factory for creating download clients.

    Follows DIP by abstracting client creation.
    """

    @abstractmethod
    def create(self, definition: DownloadClientDefinition) -> BaseDownloadClient:
        """Create download client instance.

        Parameters
        ----------
        definition : DownloadClientDefinition
            Client definition.

        Returns
        -------
        TrackingDownloadClient | object
            Client instance.
        """
        raise NotImplementedError


class DefaultDownloadClientFactory(DownloadClientFactory):
    """Default factory using create_download_client."""

    def create(self, definition: DownloadClientDefinition) -> BaseDownloadClient:
        """Create download client using factory function."""
        from bookcard.pvr.factory.download_client_factory import (
            create_download_client,
        )

        return create_download_client(definition)

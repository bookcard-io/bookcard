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

"""Client for Prowlarr API interactions."""

import logging
from typing import Protocol

import httpx

from bookcard.pvr.sync.exceptions import ProwlarrConnectionError
from bookcard.pvr.sync.models import ProwlarrIndexerResponse

logger = logging.getLogger(__name__)


class ProwlarrClientInterface(Protocol):
    """Interface for Prowlarr client."""

    def test_connection(self) -> bool:
        """Test connection to Prowlarr."""
        ...

    def get_indexers(self) -> list[ProwlarrIndexerResponse]:
        """Get all indexers from Prowlarr."""
        ...


class ProwlarrClient:
    """Client for Prowlarr API interactions."""

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize Prowlarr client.

        Parameters
        ----------
        base_url : str
            Prowlarr base URL (e.g., http://localhost:9696).
        api_key : str
            Prowlarr API key.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key}

    def test_connection(self) -> bool:
        """Test connection to Prowlarr.

        Returns
        -------
        bool
            True if connection successful, False otherwise.
        """
        try:
            url = f"{self.base_url}/api/v1/system/status"
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to connect to Prowlarr")
            return False
        else:
            return True

    def get_indexers(self) -> list[ProwlarrIndexerResponse]:
        """Get all indexers from Prowlarr.

        Returns
        -------
        list[ProwlarrIndexerResponse]
            List of indexer definitions from Prowlarr.

        Raises
        ------
        ProwlarrConnectionError
            If connection fails.
        """
        url = f"{self.base_url}/api/v1/indexer"
        try:
            response = httpx.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return [ProwlarrIndexerResponse(**item) for item in data]
        except (httpx.HTTPError, ValueError) as e:
            msg = f"Failed to fetch indexers: {e}"
            logger.exception("Failed to fetch indexers from Prowlarr")
            raise ProwlarrConnectionError(msg) from e

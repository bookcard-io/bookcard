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

"""Base proxy class for download client API proxies.

This module provides a common base class for all download client proxies,
following DRY and SRP principles by centralizing common proxy functionality.
"""

from abc import ABC, abstractmethod

import httpx

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients._http_client import create_httpx_client


class BaseClientProxy(ABC):
    """Base class for download client API proxies.

    This class provides common functionality for all download client proxies,
    following DRY principles by centralizing HTTP client creation and common patterns.

    Attributes
    ----------
    settings : DownloadClientSettings
        Download client settings.
    base_url : str
        Base URL for the client API.
    """

    def __init__(self, settings: DownloadClientSettings, base_url: str) -> None:
        """Initialize base proxy.

        Parameters
        ----------
        settings : DownloadClientSettings
            Download client settings.
        base_url : str
            Base URL for the client API.
        """
        self.settings = settings
        self.base_url = base_url

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client.

        Returns
        -------
        httpx.Client
            Configured HTTP client.

        Notes
        -----
        Subclasses can override this method to customize client configuration.
        """
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=self._verify_ssl,
            follow_redirects=self._follow_redirects,
        )

    @property
    def _verify_ssl(self) -> bool:
        """Whether to verify SSL certificates.

        Returns
        -------
        bool
            True to verify SSL certificates (default: True).

        Notes
        -----
        Subclasses can override this property to disable SSL verification.
        """
        return True

    @property
    def _follow_redirects(self) -> bool:
        """Whether to follow redirects.

        Returns
        -------
        bool
            True to follow redirects (default: True).

        Notes
        -----
        Subclasses can override this property to disable redirect following.
        """
        return True

    @abstractmethod
    def authenticate(self, force: bool = False) -> None:
        """Authenticate with the client.

        Parameters
        ----------
        force : bool
            Force re-authentication even if already authenticated.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connectivity to the client.

        Returns
        -------
        bool
            True if connection test succeeds, False otherwise.

        Raises
        ------
        PVRProviderError
            If the connection test fails with a specific error.
        """
        raise NotImplementedError

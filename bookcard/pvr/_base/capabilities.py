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

"""Capability protocols for download clients.

This module defines Protocol classes for download client capabilities,
following ISP by allowing clients to implement only the capabilities they support.
"""

from typing import Protocol


class MagnetSupport(Protocol):
    """Protocol for clients that support magnet links."""

    def add_magnet(
        self,
        magnet_url: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link.

        Parameters
        ----------
        magnet_url : str
            Magnet link URL.
        title : str | None
            Optional title.
        category : str | None
            Category/tag to assign.
        download_path : str | None
            Download path.

        Returns
        -------
        str
            Client-specific item ID.
        """
        ...


class FileSupport(Protocol):
    """Protocol for clients that support file uploads."""

    def add_file(
        self,
        filepath: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file.

        Parameters
        ----------
        filepath : str
            Path to local file.
        title : str | None
            Optional title.
        category : str | None
            Category/tag to assign.
        download_path : str | None
            Download path.

        Returns
        -------
        str
            Client-specific item ID.
        """
        ...


class UrlSupport(Protocol):
    """Protocol for clients that support URL downloads."""

    def add_url(
        self,
        url: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL.

        Parameters
        ----------
        url : str
            HTTP/HTTPS URL.
        title : str | None
            Optional title.
        category : str | None
            Category/tag to assign.
        download_path : str | None
            Download path.

        Returns
        -------
        str
            Client-specific item ID.
        """
        ...

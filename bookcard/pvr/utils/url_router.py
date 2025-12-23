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

"""URL routing utilities for download clients.

This module provides URL routing functionality following SRP by separating
URL routing concerns from download client logic.
"""

from enum import Enum
from pathlib import Path

from bookcard.pvr.exceptions import PVRProviderError


class DownloadType(Enum):
    """Download type enumeration.

    Represents the type of download source (magnet, URL, or file).
    """

    MAGNET = "magnet"
    URL = "url"
    FILE = "file"


class DownloadUrlRouter:
    """Routes download URLs to appropriate download types.

    This class follows SRP by handling only URL routing logic, separating
    it from download client business logic.

    Examples
    --------
    >>> router = DownloadUrlRouter()
    >>> router.route(
    ...     "magnet:?xt=urn:btih:..."
    ... )
    <DownloadType.MAGNET: 'magnet'>
    >>> router.route(
    ...     "https://example.com/file.torrent"
    ... )
    <DownloadType.URL: 'url'>
    >>> router.route(
    ...     "/path/to/file.torrent"
    ... )
    <DownloadType.FILE: 'file'>
    """

    def route(self, download_url: str) -> DownloadType:
        """Route download URL to appropriate download type.

        Parameters
        ----------
        download_url : str
            Download URL, magnet link, or file path.

        Returns
        -------
        DownloadType
            The type of download (MAGNET, URL, or FILE).

        Raises
        ------
        PVRProviderError
            If the URL format is invalid or unrecognized.
        """
        if download_url.startswith("magnet:"):
            return DownloadType.MAGNET

        if download_url.startswith(("http://", "https://")):
            return DownloadType.URL

        if Path(download_url).is_file():
            return DownloadType.FILE

        msg = f"Invalid download URL: {download_url}"
        raise PVRProviderError(msg)

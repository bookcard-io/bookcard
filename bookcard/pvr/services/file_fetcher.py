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

"""File fetching service for PVR system.

This module provides file fetching functionality following SRP by
separating HTTP download logic from download client business logic.
"""

from pathlib import Path
from urllib.parse import urlparse

import httpx

from bookcard.pvr.error_handlers import handle_http_errors


class FileFetcher:
    """Service for fetching files from URLs.

    This class handles HTTP file downloads, following SRP by separating
    file fetching concerns from download client logic.

    Parameters
    ----------
    timeout : int
        Request timeout in seconds (default: 30).

    Examples
    --------
    >>> fetcher = (
    ...     FileFetcher(
    ...         timeout=30
    ...     )
    ... )
    >>> content = fetcher.fetch_content(
    ...     "https://example.com/file.torrent"
    ... )
    >>> (
    ...     content,
    ...     filename,
    ... ) = fetcher.fetch_with_filename(
    ...     "https://example.com/file.torrent",
    ...     "default.torrent",
    ... )
    """

    def __init__(self, timeout: int = 30) -> None:
        """Initialize file fetcher.

        Parameters
        ----------
        timeout : int
            Request timeout in seconds.
        """
        self.timeout = timeout

    def fetch_content(self, url: str) -> bytes:
        """Fetch file content from URL.

        Parameters
        ----------
        url : str
            URL to fetch from.

        Returns
        -------
        bytes
            File content.

        Raises
        ------
        PVRProviderError
            If fetching fails.
        """
        with (
            handle_http_errors(f"File fetch from {url}"),
            httpx.Client(timeout=self.timeout) as client,
        ):
            response = client.get(url)
            response.raise_for_status()
            return response.content

    def fetch_with_filename(self, url: str, default_name: str) -> tuple[bytes, str]:
        """Fetch content and infer filename.

        Parameters
        ----------
        url : str
            URL to fetch from.
        default_name : str
            Default filename if cannot be inferred from URL.

        Returns
        -------
        tuple[bytes, str]
            Tuple of (content, filename).

        Raises
        ------
        PVRProviderError
            If fetching fails.
        """
        content = self.fetch_content(url)

        # Try to extract filename from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).name or default_name

        return content, filename

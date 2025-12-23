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

"""Download strategies for PVR."""

from typing import Any, Protocol, runtime_checkable

from bookcard.pvr._base.capabilities import FileSupport, MagnetSupport, UrlSupport
from bookcard.pvr.base.interfaces import UrlRouterProtocol
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.url_router import DownloadType


@runtime_checkable
class DownloadStrategy(Protocol):
    """Protocol for download strategies."""

    def can_handle(self, url: str) -> bool:
        """Check if this strategy can handle the URL.

        Parameters
        ----------
        url : str
            Download URL.

        Returns
        -------
        bool
            True if strategy can handle the URL.
        """
        ...

    def add(
        self,
        client: Any,  # noqa: ANN401
        url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add download using this strategy.

        Parameters
        ----------
        client : Any
            Download client (must support required capability).
        url : str
            Download URL.
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


class MagnetStrategy:
    """Strategy for handling magnet links."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is a magnet link."""
        return url.startswith("magnet:")

    def add(
        self,
        client: Any,  # noqa: ANN401
        url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add magnet link to client."""
        if not isinstance(client, MagnetSupport):
            name = getattr(client, "client_name", "Client")
            msg = f"{name} does not support magnet links"
            raise PVRProviderError(msg)
        return client.add_magnet(url, title, category, download_path)


class UrlStrategy:
    """Strategy for handling HTTP/HTTPS URLs."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is http/https."""
        return url.startswith(("http:", "https:"))

    def add(
        self,
        client: Any,  # noqa: ANN401
        url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add URL to client."""
        if not isinstance(client, UrlSupport):
            name = getattr(client, "client_name", "Client")
            msg = f"{name} does not support URL downloads"
            raise PVRProviderError(msg)
        return client.add_url(url, title, category, download_path)


class FileStrategy:
    """Strategy for handling local files."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is a file path."""
        # Simple check for now, can be improved with router logic if needed
        return not (url.startswith(("magnet:", "http:", "https:")))

    def add(
        self,
        client: Any,  # noqa: ANN401
        url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add file to client."""
        if not isinstance(client, FileSupport):
            name = getattr(client, "client_name", "Client")
            msg = f"{name} does not support file uploads"
            raise PVRProviderError(msg)
        return client.add_file(url, title, category, download_path)


class DownloadStrategyRegistry:
    """Registry for download strategies."""

    def __init__(self, router: UrlRouterProtocol) -> None:
        """Initialize registry."""
        self._router = router
        self._strategies: dict[DownloadType, DownloadStrategy] = {
            DownloadType.MAGNET: MagnetStrategy(),
            DownloadType.URL: UrlStrategy(),
            DownloadType.FILE: FileStrategy(),
        }

    def register(self, download_type: DownloadType, strategy: DownloadStrategy) -> None:
        """Register a strategy for a download type."""
        self._strategies[download_type] = strategy

    def handle(
        self,
        client: Any,  # noqa: ANN401
        url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Handle download addition using registered strategies."""
        download_type = self._router.route(url)
        strategy = self._strategies.get(download_type)

        if not strategy:
            msg = f"No strategy found for download type: {download_type}"
            raise PVRProviderError(msg)

        return strategy.add(client, url, title, category, download_path)

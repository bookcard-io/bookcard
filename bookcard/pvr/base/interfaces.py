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

"""PVR Interfaces and Protocols.

This module defines the core interfaces and protocols for the PVR system,
allowing for loose coupling and better testability.
"""

from collections.abc import Sequence
from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from bookcard.pvr.models import DownloadItem, ReleaseInfo
from bookcard.pvr.utils.url_router import DownloadType


@runtime_checkable
class DownloadInitiator(Protocol):
    """Protocol for clients that can initiate downloads."""

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add a download to the client."""
        ...


@runtime_checkable
class DownloadTracker(Protocol):
    """Protocol for clients that can track active downloads."""

    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads."""
        ...


@runtime_checkable
class DownloadManager(Protocol):
    """Protocol for clients that can manage downloads."""

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from the client."""
        ...


@runtime_checkable
class ConnectionTestable(Protocol):
    """Protocol for clients that can test connectivity."""

    def test_connection(self) -> bool:
        """Test connectivity."""
        ...


@runtime_checkable
class IndexerCore(Protocol):
    """Core indexer operations protocol."""

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases."""
        ...

    def test_connection(self) -> bool:
        """Test connectivity."""
        ...


@runtime_checkable
class FileFetcherProtocol(Protocol):
    """Protocol for file fetcher services."""

    def fetch_content(self, url: str) -> bytes:
        """Fetch file content from URL."""
        ...

    def fetch_with_filename(self, url: str, default_name: str) -> tuple[bytes, str]:
        """Fetch content and infer filename."""
        ...


@runtime_checkable
class UrlRouterProtocol(Protocol):
    """Protocol for URL routing logic."""

    def route(self, download_url: str) -> DownloadType:
        """Route download URL to appropriate download type."""
        ...


@runtime_checkable
class HttpClientProtocol(Protocol):
    """Protocol for HTTP clients."""

    def get(self, url: str, **kwargs: Any) -> Any:  # noqa: ANN401
        """Perform HTTP GET request."""
        ...

    def post(self, url: str, **kwargs: Any) -> Any:  # noqa: ANN401
        """Perform HTTP POST request."""
        ...

    def __enter__(self) -> "HttpClientProtocol":
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        ...


@runtime_checkable
class RequestGeneratorProtocol(Protocol):
    """Protocol for indexer request generation."""

    def build_search_url(
        self,
        query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        categories: list[int] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> str:
        """Build search URL."""
        ...

    def build_rss_url(
        self,
        categories: list[int] | None = None,
        limit: int = 100,
    ) -> str:
        """Build RSS URL."""
        ...


@runtime_checkable
class ResponseParserProtocol(Protocol):
    """Protocol for indexer response parsing."""

    def parse_response(
        self, xml_content: bytes | str, indexer_id: int | None = None
    ) -> list[ReleaseInfo]:
        """Parse response content."""
        ...

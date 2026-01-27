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

"""Flood download client implementation.

Flood is a modern web UI for rTorrent, qBittorrent, and Transmission.
This implementation supports adding torrents, monitoring downloads,
and managing torrents via Flood's REST API.

Documentation: https://github.com/jesec/flood
"""

import base64
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from bookcard.pvr.base import (
    BaseDownloadClient,
    DownloadClientSettings,
)
from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.download_clients._http_client import (
    build_base_url,
    create_httpx_client,
    handle_httpx_exception,
)
from bookcard.pvr.error_handlers import handle_http_error_response
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)
from bookcard.pvr.models import DownloadItem
from bookcard.pvr.utils.status import DownloadStatus

logger = logging.getLogger(__name__)


class FloodSettings(DownloadClientSettings):
    """Settings for Flood download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    """

    url_base: str | None = None


class FloodProxy:
    """Low-level proxy for Flood REST API.

    Handles authentication, request building, and API communication.
    """

    def __init__(self, settings: FloodSettings) -> None:
        """Initialize Flood proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.api_url = urljoin(self.base_url.rstrip("/") + "/", "api")
        self._auth_cookies: dict[str, str] | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with Flood and get session cookies.

        Parameters
        ----------
        force : bool
            Force re-authentication.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._auth_cookies is not None:
            return

        if not self.settings.username or not self.settings.password:
            msg = "Flood requires username and password"
            raise PVRProviderAuthenticationError(msg)

        auth_url = urljoin(self.api_url.rstrip("/") + "/", "auth/authenticate")

        with self._get_client() as client:
            try:
                response = client.post(
                    auth_url,
                    json={
                        "username": self.settings.username,
                        "password": self.settings.password,
                    },
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code in (401, 403):
                    msg = "Flood authentication failed"
                    raise PVRProviderAuthenticationError(msg)

                response.raise_for_status()

                # Extract cookies from response
                self._auth_cookies = {}
                for cookie_item in response.cookies:
                    cookie_name = getattr(cookie_item, "name", None)
                    cookie_value = getattr(cookie_item, "value", None)
                    if cookie_name is not None and cookie_value is not None:
                        self._auth_cookies[str(cookie_name)] = str(cookie_value)

                logger.debug("Flood authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Flood authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Flood authentication")
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, "Flood authentication")

    def _execute_request(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        method : str
            HTTP method (GET, POST, DELETE).
        url : str
            Request URL.
        headers : dict[str, str]
            Request headers.
        json_data : dict[str, Any] | None
            Optional JSON request body.

        Returns
        -------
        httpx.Response
            HTTP response.

        Raises
        ------
        PVRProviderError
            If method is unsupported.
        """
        method_upper = method.upper()
        if method_upper == "GET":
            return client.get(
                url,
                headers=headers,
                cookies=self._auth_cookies,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "POST":
            return client.post(
                url,
                json=json_data,
                headers=headers,
                cookies=self._auth_cookies,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "DELETE":
            return client.delete(
                url,
                headers=headers,
                cookies=self._auth_cookies,
                timeout=self.settings.timeout_seconds,
            )
        msg = f"Unsupported HTTP method: {method}"
        raise PVRProviderError(msg)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, DELETE).
        endpoint : str
            API endpoint path.
        json_data : dict[str, Any] | None
            Optional JSON request body.

        Returns
        -------
        dict[str, Any]
            JSON response as dictionary.

        Raises
        ------
        PVRProviderError
            If request fails.
        """
        self._authenticate()

        url = urljoin(self.api_url.rstrip("/") + "/", endpoint.lstrip("/"))
        headers: dict[str, str] = {"Content-Type": "application/json"}

        with self._get_client() as client:
            try:
                response = self._execute_request(
                    client, method, url, headers, json_data
                )

                # Handle auth expiration
                if response.status_code in (401, 403):
                    logger.debug("Session expired, re-authenticating")
                    self._authenticate(force=True)
                    response = self._execute_request(
                        client, method, url, headers, json_data
                    )

                response.raise_for_status()

                return response.json() if response.content else {}

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Flood authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Flood API {method} {endpoint}")

        # Should be unreachable
        msg = f"Request failed: {method} {endpoint}"
        raise PVRProviderError(msg)

    def verify_auth(self) -> None:
        """Verify authentication."""
        self._request("GET", "auth/verify")

    def add_torrent_url(
        self, url: str, tags: list[str] | None = None, destination: str | None = None
    ) -> None:
        """Add torrent from URL or magnet link.

        Parameters
        ----------
        url : str
            Torrent URL or magnet link.
        tags : list[str] | None
            Optional tags.
        destination : str | None
            Optional download destination.
        """
        body: dict[str, Any] = {"urls": [url], "tags": tags or []}
        if destination:
            body["destination"] = destination

        self._request("POST", "torrents/add-urls", body)

    def add_torrent_file(
        self,
        _filename: str,
        file_content: bytes,
        tags: list[str] | None = None,
        destination: str | None = None,
    ) -> None:
        """Add torrent from file.

        Parameters
        ----------
        filename : str
            Torrent filename.
        file_content : bytes
            Torrent file content.
        tags : list[str] | None
            Optional tags.
        destination : str | None
            Optional download destination.
        """
        # Flood requires base64-encoded file content

        file_base64 = base64.b64encode(file_content).decode("utf-8")

        body: dict[str, Any] = {"files": [file_base64], "tags": tags or []}
        if destination:
            body["destination"] = destination

        self._request("POST", "torrents/add-files", body)

    def get_torrents(self) -> dict[str, dict[str, Any]]:
        """Get all torrents.

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary of torrents keyed by hash.
        """
        response = self._request("GET", "torrents")
        return response.get("torrents", {})

    def remove_torrent(self, hash_str: str, delete_data: bool = False) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        delete_data : bool
            Whether to delete downloaded data.
        """
        endpoint = f"torrents/{hash_str}"
        if delete_data:
            endpoint += "?deleteData=true"
        self._request("DELETE", endpoint)


class FloodClient(BaseDownloadClient):
    """Flood download client implementation.

    Implements BaseDownloadClient interface for Flood REST API.
    """

    def __init__(
        self,
        settings: FloodSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize Flood client.

        Parameters
        ----------
        settings : FloodSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to FloodSettings.
        file_fetcher : FileFetcherProtocol
            File fetcher service.
        url_router : UrlRouterProtocol
            URL router service.
        http_client_factory : Callable[[], HttpClientProtocol] | None
            HTTP client factory.
        enabled : bool
            Whether this client is enabled.
        """
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, FloodSettings
        ):
            flood_settings = FloodSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base=None,
            )
            settings = flood_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: FloodSettings = settings
        self._proxy = FloodProxy(self.settings)

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Flood"

    def _extract_hash_from_magnet(self, magnet_url: str) -> str:
        """Extract hash from magnet link.

        Parameters
        ----------
        magnet_url : str
            Magnet URL.

        Returns
        -------
        str
            Extracted hash or "pending".
        """
        for part in magnet_url.split("&"):
            if "xt=urn:btih:" in part:
                return part.split(":")[-1].upper()
        return "pending"

    def _build_tags(self, category: str | None) -> list[str] | None:
        """Build tags list from category.

        Parameters
        ----------
        category : str | None
            Category string.

        Returns
        -------
        list[str] | None
            Tags list or None.
        """
        cat = category or self.settings.category
        return [cat] if cat else None

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        tags = self._build_tags(category)
        destination = download_path or self.settings.download_path
        self._proxy.add_torrent_url(magnet_url, tags=tags, destination=destination)
        return self._extract_hash_from_magnet(magnet_url)

    def add_url(
        self,
        url: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        tags = self._build_tags(category)
        destination = download_path or self.settings.download_path
        self._proxy.add_torrent_url(url, tags=tags, destination=destination)
        return "pending"

    def add_file(
        self,
        filepath: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        filename = title or Path(filepath).name
        tags = self._build_tags(category)
        destination = download_path or self.settings.download_path
        self._proxy.add_torrent_file(
            filename, file_content, tags=tags, destination=destination
        )
        return "pending"

    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads.

        Returns
        -------
        Sequence[dict[str, str | int | float | None]]
            Sequence of download items.

        Raises
        ------
        PVRProviderError
            If fetching items fails.
        """
        if not self.is_enabled():
            return []

        try:
            torrents = self._proxy.get_torrents()

            items = []
            for hash_str, torrent in torrents.items():
                if not hash_str:
                    continue

                # Filter by tags if category is set
                if self.settings.category:
                    tags = torrent.get("tags", [])
                    if self.settings.category not in tags:
                        continue

                # Map Flood status to our status
                status = torrent.get("status", [])
                item_status = self._map_status_list_to_status(status)

                # Calculate progress
                bytes_done = torrent.get("bytesDone", 0)
                size_bytes = torrent.get("sizeBytes", 0)

                progress = 0.0
                if size_bytes and size_bytes > 0:
                    progress = bytes_done / size_bytes
                    if progress > 1.0:
                        progress = 1.0

                # Get download speed
                download_speed = torrent.get("downloadSpeed", 0)
                speed = int(download_speed) if download_speed > 0 else None

                # Get ETA
                eta = torrent.get("eta", -1)
                eta_seconds = int(eta) if eta > 0 else None

                item: DownloadItem = {
                    "client_item_id": str(hash_str).upper(),
                    "title": torrent.get("name", ""),
                    "status": item_status,
                    "progress": progress,
                    "size_bytes": int(size_bytes) if size_bytes else None,
                    "downloaded_bytes": int(bytes_done) if bytes_done else None,
                    "download_speed_bytes_per_sec": speed,
                    "eta_seconds": eta_seconds,
                    "file_path": torrent.get("directory", ""),
                }
                items.append(item)

        except Exception as e:
            msg = f"Failed to get downloads from Flood: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Flood.

        Parameters
        ----------
        client_item_id : str
            Torrent hash.
        delete_files : bool
            Whether to delete downloaded files.

        Returns
        -------
        bool
            True if removal succeeded.

        Raises
        ------
        PVRProviderError
            If removal fails.
        """
        if not self.is_enabled():
            msg = "Flood client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(client_item_id.lower(), delete_files)
        except Exception as e:
            msg = f"Failed to remove download from Flood: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Flood.

        Returns
        -------
        bool
            True if connection test succeeds.

        Raises
        ------
        PVRProviderError
            If the connection test fails.
        """
        try:
            self._proxy.verify_auth()
        except Exception as e:
            msg = f"Failed to connect to Flood: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_status_list_to_status(self, status: list[str]) -> str:
        """Map Flood status array to standardized status.

        Parameters
        ----------
        status : list[str]
            Flood status array.

        Returns
        -------
        str
            Standardized status string.
        """
        if not status:
            return DownloadStatus.QUEUED
        if "seeding" in status or "complete" in status:
            return DownloadStatus.COMPLETED
        if "error" in status:
            return DownloadStatus.FAILED
        if "paused" in status:
            return DownloadStatus.PAUSED
        if "downloading" in status or "active" in status:
            return DownloadStatus.DOWNLOADING
        return DownloadStatus.QUEUED

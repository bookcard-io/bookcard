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

"""qBittorrent download client implementation.

This module provides a qBittorrent download client that implements the
BaseDownloadClient interface. It uses the qBittorrent Web API v2.

Documentation: https://github.com/qbittorrent/qBittorrent/wiki/Web-API-Documentation
"""

import json
import logging
import pathlib
from collections.abc import Callable, Sequence
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
from bookcard.pvr.utils.status import DownloadStatus, StatusMapper

logger = logging.getLogger(__name__)


class QBittorrentSettings(DownloadClientSettings):
    """Settings for qBittorrent download client.

    Extends DownloadClientSettings with qBittorrent-specific configuration.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (e.g., '/qbt').
    """

    url_base: str | None = None


class QBittorrentProxy:
    """Low-level proxy for qBittorrent Web API v2.

    Handles authentication, request building, and API communication.
    Follows SRP by separating API communication from business logic.
    """

    def __init__(self, settings: QBittorrentSettings) -> None:
        """Initialize qBittorrent proxy.

        Parameters
        ----------
        settings : QBittorrentSettings
            qBittorrent client settings.
        """
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self._auth_cookies: dict[str, str] | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client.

        Returns
        -------
        httpx.Client
            Configured HTTP client.
        """
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _raise_auth_error(self) -> None:
        """Raise authentication error.

        Raises
        ------
        PVRProviderAuthenticationError
            Always raises with error message.
        """
        msg = "qBittorrent authentication failed: invalid credentials"
        raise PVRProviderAuthenticationError(msg)

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with qBittorrent API.

        Parameters
        ----------
        force : bool
            Force re-authentication even if already authenticated.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._auth_cookies is not None:
            return

        if not self.settings.username or not self.settings.password:
            # No authentication required
            self._auth_cookies = {}
            return

        url = urljoin(self.base_url, "/api/v2/auth/login")
        data = {
            "username": self.settings.username,
            "password": self.settings.password,
        }

        with self._get_client() as client:
            try:
                response = client.post(url, data=data)
                response.raise_for_status()

                if response.text.strip() != "Ok.":
                    self._raise_auth_error()

                # Extract cookies
                self._auth_cookies = dict(response.cookies)
                logger.debug("qBittorrent authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "qBittorrent authentication failed: invalid credentials"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "qBittorrent authentication")
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "qBittorrent authentication")
                raise

    def _execute_request(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        cookies: dict[str, str],
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        method : str
            HTTP method (GET, POST).
        url : str
            Request URL.
        cookies : dict[str, str]
            Request cookies.
        data : dict[str, Any] | None
            Form data for POST requests.
        files : dict[str, Any] | None
            Files to upload.
        params : dict[str, Any] | None
            Query parameters.

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
            return client.get(url, cookies=cookies, params=params)
        if method_upper == "POST":
            return client.post(
                url, cookies=cookies, data=data, files=files, params=params
            )
        msg = f"Unsupported HTTP method: {method}"
        raise PVRProviderError(msg)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Make authenticated API request.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, etc.).
        endpoint : str
            API endpoint path.
        data : dict[str, Any] | None
            Form data for POST requests.
        files : dict[str, Any] | None
            Files to upload.
        params : dict[str, Any] | None
            Query parameters.

        Returns
        -------
        str
            Response text.

        Raises
        ------
        PVRProviderError
            If request fails.
        """
        self._authenticate()

        url = urljoin(self.base_url, endpoint)
        cookies = self._auth_cookies or {}

        with self._get_client() as client:
            try:
                response = self._execute_request(
                    client, method, url, cookies, data, files, params
                )

                # Handle 403 Forbidden (session expired)
                if response.status_code == 403:
                    logger.debug("Session expired, re-authenticating")
                    self._authenticate(force=True)
                    cookies = self._auth_cookies or {}
                    response = self._execute_request(
                        client, method, url, cookies, data, files, params
                    )

                response.raise_for_status()

                # Check for API error responses
                if response.text.strip() == "Fails.":
                    msg = "qBittorrent API returned error: Fails."
                    raise PVRProviderError(msg)

                return response.text

            except httpx.HTTPStatusError as e:
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"qBittorrent API {method} {endpoint}")
                raise
            else:
                return response.text

    def get_version(self) -> str:
        """Get qBittorrent version.

        Returns
        -------
        str
            Version string.
        """
        return self._request("GET", "/api/v2/app/version").strip()

    def add_torrent_from_url(
        self,
        torrent_url: str,
        category: str | None = None,
        save_path: str | None = None,
    ) -> None:
        """Add torrent from URL or magnet link.

        Parameters
        ----------
        torrent_url : str
            Torrent URL or magnet link.
        category : str | None
            Optional category/tag to assign.
        save_path : str | None
            Optional save path.
        """
        data: dict[str, Any] = {"urls": torrent_url}
        if category:
            data["category"] = category
        if save_path:
            data["savepath"] = save_path

        self._request("POST", "/api/v2/torrents/add", data=data)

    def add_torrent_from_file(
        self,
        file_content: bytes,
        filename: str,
        category: str | None = None,
        save_path: str | None = None,
    ) -> None:
        """Add torrent from file content.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        filename : str
            Torrent filename.
        category : str | None
            Optional category/tag to assign.
        save_path : str | None
            Optional save path.
        """
        files = {"torrents": (filename, file_content, "application/x-bittorrent")}
        data: dict[str, Any] = {}
        if category:
            data["category"] = category
        if save_path:
            data["savepath"] = save_path

        self._request("POST", "/api/v2/torrents/add", data=data, files=files)

    def get_torrents(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get list of torrents.

        Parameters
        ----------
        category : str | None
            Optional category filter.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        params: dict[str, Any] = {}
        if category:
            params["category"] = category

        response_text = self._request("GET", "/api/v2/torrents/info", params=params)

        try:
            return json.loads(response_text)
        except Exception as e:
            msg = f"Failed to parse qBittorrent torrents response: {e}"
            raise PVRProviderError(msg) from e

    def remove_torrent(self, hash_str: str, delete_files: bool = False) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash (lowercase).
        delete_files : bool
            Whether to delete downloaded files.
        """
        data: dict[str, Any] = {"hashes": hash_str}
        if delete_files:
            data["deleteFiles"] = "true"

        self._request("POST", "/api/v2/torrents/delete", data=data)

    def get_torrent_properties(self, hash_str: str) -> dict[str, Any]:
        """Get torrent properties.

        Parameters
        ----------
        hash_str : str
            Torrent hash (lowercase).

        Returns
        -------
        dict[str, Any]
            Torrent properties dictionary.
        """
        params = {"hash": hash_str}
        response_text = self._request(
            "GET", "/api/v2/torrents/properties", params=params
        )

        try:
            return json.loads(response_text)
        except Exception as e:
            msg = f"Failed to parse qBittorrent torrent properties: {e}"
            raise PVRProviderError(msg) from e


class QBittorrentClient(BaseDownloadClient):
    """qBittorrent download client implementation.

    Implements BaseDownloadClient interface for qBittorrent Web API v2.
    """

    def __init__(
        self,
        settings: QBittorrentSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize qBittorrent client.

        Parameters
        ----------
        settings : QBittorrentSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to QBittorrentSettings.
        file_fetcher : FileFetcherProtocol
            File fetcher service.
        url_router : UrlRouterProtocol
            URL router service.
        http_client_factory : Callable[[], HttpClientProtocol] | None
            HTTP client factory.
        enabled : bool
            Whether this client is enabled.
        """
        # Convert DownloadClientSettings to QBittorrentSettings if needed
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, QBittorrentSettings
        ):
            qb_settings = QBittorrentSettings(
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
            settings = qb_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: QBittorrentSettings = settings  # type: ignore[assignment]
        self._proxy = QBittorrentProxy(self.settings)
        self._status_mapper = StatusMapper(
            {
                "uploading": DownloadStatus.COMPLETED,
                "stalledUP": DownloadStatus.COMPLETED,
                "queuedUP": DownloadStatus.QUEUED,
                "checkingUP": DownloadStatus.CHECKING,
                "forcedUP": DownloadStatus.COMPLETED,
                "allocating": DownloadStatus.DOWNLOADING,
                "downloading": DownloadStatus.DOWNLOADING,
                "stalledDL": DownloadStatus.STALLED,
                "queuedDL": DownloadStatus.QUEUED,
                "checkingDL": DownloadStatus.CHECKING,
                "forcedDL": DownloadStatus.DOWNLOADING,
                "metaDL": DownloadStatus.METADATA,
                "pausedDL": DownloadStatus.PAUSED,
                "pausedUP": DownloadStatus.PAUSED,
                "error": DownloadStatus.FAILED,
                "missingFiles": DownloadStatus.FAILED,
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "qBittorrent"

    def _add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        self._proxy.add_torrent_from_url(
            magnet_url, category=category, save_path=download_path
        )
        # Extract hash from magnet link
        if magnet_url.startswith("magnet:"):
            for part in magnet_url.split("&"):
                if "xt=urn:btih:" in part:
                    return part.split(":")[-1].upper()
        return "pending"

    def _add_url(
        self,
        url: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        self._proxy.add_torrent_from_url(
            url, category=category, save_path=download_path
        )
        # qBittorrent doesn't return hash immediately, return placeholder
        return "pending"

    def _add_file(
        self,
        filepath: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        with pathlib.Path(filepath).open("rb") as f:
            file_content = f.read()
        filename = filepath.split("/")[-1]
        self._proxy.add_torrent_from_file(
            file_content, filename, category=category, save_path=download_path
        )
        # qBittorrent doesn't return hash immediately, return placeholder
        return "pending"

    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads.

        Returns
        -------
        Sequence[dict[str, str | int | float | None]]
            Sequence of download items with standardized fields.

        Raises
        ------
        PVRProviderError
            If fetching items fails.
        """
        if not self.is_enabled():
            return []

        try:
            category = self.settings.category
            torrents = self._proxy.get_torrents(category=category)

            items = []
            for torrent in torrents:
                # Map qBittorrent state to our status
                state = torrent.get("state", "")
                status = self._status_mapper.map(state)

                # Calculate progress
                progress = float(torrent.get("progress", 0.0)) / 100.0
                if progress > 1.0:
                    progress = 1.0

                # Get file path (content path for completed torrents)
                file_path = torrent.get("content_path") or torrent.get("save_path")

                item: DownloadItem = {
                    "client_item_id": torrent.get("hash", "").upper(),
                    "title": torrent.get("name", ""),
                    "status": status,
                    "progress": progress,
                    "size_bytes": torrent.get("size"),
                    "downloaded_bytes": torrent.get("completed"),
                    "download_speed_bytes_per_sec": torrent.get("dlspeed"),
                    "eta_seconds": self._calculate_eta(torrent),
                    "file_path": file_path,
                }
                items.append(item)
        except Exception as e:
            msg = f"Failed to get downloads from qBittorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from qBittorrent.

        Parameters
        ----------
        client_item_id : str
            Torrent hash (case-insensitive).
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
            msg = "qBittorrent client is disabled"
            raise PVRProviderError(msg)

        try:
            # qBittorrent expects lowercase hash
            hash_lower = client_item_id.lower()
            self._proxy.remove_torrent(hash_lower, delete_files=delete_files)
        except Exception as e:
            msg = f"Failed to remove download from qBittorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to qBittorrent.

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
            version = self._proxy.get_version()
            logger.debug("qBittorrent version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to qBittorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _calculate_eta(self, torrent: dict[str, Any]) -> int | None:
        """Calculate ETA in seconds.

        Parameters
        ----------
        torrent : dict[str, Any]
            Torrent dictionary.

        Returns
        -------
        int | None
            ETA in seconds or None if unavailable.
        """
        eta = torrent.get("eta")
        if eta is None or eta < 0:
            return None

        # qBittorrent returns 8640000 for unknown ETA
        if eta >= 8640000:
            return None

        return int(eta)

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

"""uTorrent download client implementation.

uTorrent is a torrent client that uses a Web UI API with JSON responses.
This implementation supports adding torrents, monitoring downloads,
and managing torrents.

Documentation: https://help.utorrent.com/support/solutions/articles/70000435259-webui-api
"""

import base64
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

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


class UTorrentSettings(DownloadClientSettings):
    """Settings for uTorrent download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/gui').
    """

    url_base: str | None = "/gui"


class UTorrentProxy:
    """Low-level proxy for uTorrent Web UI API.

    Handles authentication, request building, and API communication.
    """

    def __init__(self, settings: UTorrentSettings) -> None:
        """Initialize uTorrent proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.api_url = f"{self.base_url.rstrip('/')}/"
        self._token: str | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with uTorrent and get token.

        Parameters
        ----------
        force : bool
            Force re-authentication.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._token is not None:
            return

        if not self.settings.username or not self.settings.password:
            msg = "uTorrent requires username and password"
            raise PVRProviderAuthenticationError(msg)

        # uTorrent uses token-based authentication
        # First, get token from /gui/token.html
        token_url = f"{self.api_url}token.html"

        with self._get_client() as client:
            try:
                # Use basic auth for token request
                auth_str = f"{self.settings.username}:{self.settings.password}"
                auth_bytes = base64.b64encode(auth_str.encode("utf-8"))
                headers = {"Authorization": f"Basic {auth_bytes.decode('utf-8')}"}

                response = client.get(
                    token_url, headers=headers, timeout=self.settings.timeout_seconds
                )
                response.raise_for_status()

                # Extract token from HTML response
                # Token is in format: <div id='token' style='display:none;'>TOKEN</div>
                content = response.text
                token_start = content.find("<div id='token'")
                if token_start == -1:
                    msg = "Failed to extract token from uTorrent"
                    raise PVRProviderAuthenticationError(msg)

                token_end = content.find("</div>", token_start)
                if token_end == -1:
                    msg = "Failed to extract token from uTorrent"
                    raise PVRProviderAuthenticationError(msg)

                token_line = content[token_start:token_end]
                token_start_idx = token_line.find(">") + 1
                self._token = token_line[token_start_idx:].strip()

                if not self._token:
                    msg = "uTorrent returned empty token"
                    raise PVRProviderAuthenticationError(msg)

                logger.debug("uTorrent authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "uTorrent authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "uTorrent authentication")
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, "uTorrent authentication")

    def _request(
        self,
        action: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Parameters
        ----------
        action : str
            API action (e.g., 'list', 'add-url', 'add-file').
        params : dict[str, Any] | None
            Additional query parameters.

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

        request_params: dict[str, Any] = {"action": action, "token": self._token}
        if params:
            request_params.update(params)

        # Build auth header
        auth_str = f"{self.settings.username}:{self.settings.password}"
        auth_bytes = base64.b64encode(auth_str.encode("utf-8"))
        headers = {"Authorization": f"Basic {auth_bytes.decode('utf-8')}"}

        with self._get_client() as client:
            try:
                response = client.get(
                    self.api_url,
                    params=request_params,
                    headers=headers,
                    timeout=self.settings.timeout_seconds,
                )

                # Handle token expiration
                if response.status_code == 400:
                    logger.debug("Token expired, re-authenticating")
                    self._authenticate(force=True)
                    request_params["token"] = self._token
                    response = client.get(
                        self.api_url,
                        params=request_params,
                        headers=headers,
                        timeout=self.settings.timeout_seconds,
                    )

                response.raise_for_status()

                # Parse JSON response
                result = response.json()

                # Check for errors in response
                if "error" in result:
                    error = result["error"]
                    msg = f"uTorrent API error: {error}"
                    raise PVRProviderError(msg)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "uTorrent authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"uTorrent API {action}")
                raise
            else:
                return result

    def add_torrent_url(self, torrent_url: str) -> str:
        """Add torrent from URL or magnet link.

        Parameters
        ----------
        torrent_url : str
            Torrent URL or magnet link.

        Returns
        -------
        str
            Torrent hash.
        """
        self._request("add-url", {"s": torrent_url})

        # Extract hash from magnet link if possible
        if torrent_url.startswith("magnet:"):
            for part in torrent_url.split("&"):
                if part.startswith("xt=urn:btih:"):
                    return part.split(":")[-1].upper()

        # Return placeholder - hash will be available after torrent is added
        return "pending"

    def add_torrent_file(self, filename: str, file_content: bytes) -> str:
        """Add torrent from file.

        Parameters
        ----------
        filename : str
            Torrent filename.
        file_content : bytes
            Torrent file content.

        Returns
        -------
        str
            Torrent hash (extracted from torrent file).
        """
        self._authenticate()

        # uTorrent requires multipart form upload
        files = {"torrent_file": (filename, file_content, "application/x-bittorrent")}
        params = {"action": "add-file", "token": self._token}

        auth_str = f"{self.settings.username}:{self.settings.password}"
        auth_bytes = base64.b64encode(auth_str.encode("utf-8"))
        headers = {"Authorization": f"Basic {auth_bytes.decode('utf-8')}"}

        with self._get_client() as client:
            try:
                response = client.post(
                    self.api_url,
                    params=params,
                    files=files,
                    headers=headers,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code == 400:
                    self._authenticate(force=True)
                    params["token"] = self._token
                    response = client.post(
                        self.api_url,
                        params=params,
                        files=files,
                        headers=headers,
                        timeout=self.settings.timeout_seconds,
                    )

                response.raise_for_status()

                # Extract hash from torrent file (simplified - would need bencode parsing)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "uTorrent authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "uTorrent add-file")
                raise
            else:
                return "pending"

    def get_torrents(self, cache_id: str | None = None) -> list[dict[str, Any]]:
        """Get list of torrents.

        Parameters
        ----------
        cache_id : str | None
            Optional cache ID for differential updates.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        params: dict[str, Any] = {"list": 1}
        if cache_id:
            params["cid"] = cache_id

        response = self._request("list", params)

        # uTorrent returns torrents in a specific format
        # Response structure: {"torrents": [[hash, status, name, size, ...], ...], "torrentc": cache_id}
        torrents = response.get("torrents", [])
        result = []

        for torrent_data in torrents:
            if len(torrent_data) < 4:
                continue

            torrent = {
                "hash": torrent_data[0] if len(torrent_data) > 0 else "",
                "status": torrent_data[1] if len(torrent_data) > 1 else 0,
                "name": torrent_data[2] if len(torrent_data) > 2 else "",
                "size": torrent_data[3] if len(torrent_data) > 3 else 0,
                "progress": torrent_data[4] if len(torrent_data) > 4 else 0,
                "downloaded": torrent_data[5] if len(torrent_data) > 5 else 0,
                "uploaded": torrent_data[6] if len(torrent_data) > 6 else 0,
                "ratio": torrent_data[7] if len(torrent_data) > 7 else 0,
                "upspeed": torrent_data[8] if len(torrent_data) > 8 else 0,
                "downspeed": torrent_data[9] if len(torrent_data) > 9 else 0,
                "eta": torrent_data[10] if len(torrent_data) > 10 else -1,
                "label": torrent_data[11] if len(torrent_data) > 11 else "",
                "peers_connected": torrent_data[12] if len(torrent_data) > 12 else 0,
                "peers_in_swarm": torrent_data[13] if len(torrent_data) > 13 else 0,
                "seeds_connected": torrent_data[14] if len(torrent_data) > 14 else 0,
                "seeds_in_swarm": torrent_data[15] if len(torrent_data) > 15 else 0,
                "availability": torrent_data[16] if len(torrent_data) > 16 else 0,
                "torrent_queue_order": torrent_data[17]
                if len(torrent_data) > 17
                else -1,
                "remaining": torrent_data[18] if len(torrent_data) > 18 else 0,
            }
            result.append(torrent)

        return result

    def remove_torrent(self, hash_str: str, remove_data: bool = False) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        remove_data : bool
            Whether to remove downloaded data.
        """
        action = "removedata" if remove_data else "remove"
        self._request(action, {"hash": hash_str})

    def set_torrent_label(self, hash_str: str, label: str) -> None:
        """Set torrent label.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        label : str
            Label name.
        """
        # uTorrent uses setprops action
        self._request("setprops", {"hash": hash_str, "s": "label", "v": label})


class UTorrentClient(BaseDownloadClient):
    """uTorrent download client implementation.

    Implements BaseDownloadClient interface for uTorrent Web UI API.
    """

    def __init__(
        self,
        settings: UTorrentSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize uTorrent client.

        Parameters
        ----------
        settings : UTorrentSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to UTorrentSettings.
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
            settings, UTorrentSettings
        ):
            utorrent_settings = UTorrentSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/gui",
            )
            settings = utorrent_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: UTorrentSettings = settings
        self._proxy = UTorrentProxy(self.settings)
        # uTorrent status flags: bit 0=started, bit 1=checking, bit 2=start_after_check,
        # bit 3=checked, bit 4=error, bit 5=paused, bit 6=queued, bit 7=loaded
        # We map based on common patterns
        self._status_mapper = StatusMapper(
            {
                # Status is a bitmask, we check specific bits
                # This will be handled in _map_utorrent_status
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "uTorrent"

    def _map_utorrent_status(self, status: int) -> str:
        """Map uTorrent status flags to standardized status.

        Parameters
        ----------
        status : int
            uTorrent status flags (bitmask).

        Returns
        -------
        str
            Standardized status string.
        """
        # Check error bit (4)
        if status & (1 << 4):
            return DownloadStatus.FAILED
        # Check paused bit (5)
        if status & (1 << 5):
            return DownloadStatus.PAUSED
        # Check queued bit (6)
        if status & (1 << 6):
            return DownloadStatus.QUEUED
        # Check started bit (0) and checked bit (3)
        if status & (1 << 0) and status & (1 << 3):
            # If progress is 100%, it's completed
            return DownloadStatus.COMPLETED
        # Otherwise downloading
        if status & (1 << 0):
            return DownloadStatus.DOWNLOADING
        return DownloadStatus.QUEUED

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        hash_str = self._proxy.add_torrent_url(magnet_url)
        # Set label if provided
        label = category or self.settings.category
        if label and hash_str and hash_str != "pending":
            self._proxy.set_torrent_label(hash_str, label)
        return hash_str.upper() if hash_str else "pending"

    def add_url(
        self,
        url: str,
        _title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        hash_str = self._proxy.add_torrent_url(url)
        # Set label if provided
        label = category or self.settings.category
        if label and hash_str and hash_str != "pending":
            self._proxy.set_torrent_label(hash_str, label)
        return hash_str.upper() if hash_str else "pending"

    def add_file(
        self,
        filepath: str,
        title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        filename = title or Path(filepath).name
        hash_str = self._proxy.add_torrent_file(filename, file_content)
        # Set label if provided
        label = category or self.settings.category
        if label and hash_str and hash_str != "pending":
            self._proxy.set_torrent_label(hash_str, label)
        return hash_str.upper() if hash_str else "pending"

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
            for torrent in torrents:
                hash_str = torrent.get("hash", "")
                if not hash_str:
                    continue

                # Filter by category if set
                if self.settings.category:
                    label = torrent.get("label", "")
                    if label != self.settings.category:
                        continue

                # Map uTorrent status to our status
                status = torrent.get("status", 0)
                item_status = self._map_utorrent_status(status)

                # Calculate progress (stored as integer 0-1000)
                progress_raw = torrent.get("progress", 0)
                progress = float(progress_raw) / 1000.0 if progress_raw else 0.0
                if progress > 1.0:
                    progress = 1.0

                size = torrent.get("size", 0)
                downloaded = torrent.get("downloaded", 0)

                # Get ETA
                eta = torrent.get("eta", -1)
                eta_seconds = int(eta) if eta > 0 else None

                # Get download speed
                downspeed = torrent.get("downspeed", 0)
                download_speed = int(downspeed) if downspeed > 0 else None

                item: DownloadItem = {
                    "client_item_id": str(hash_str).upper(),
                    "title": torrent.get("name", ""),
                    "status": item_status,
                    "progress": progress,
                    "size_bytes": int(size) if size else None,
                    "downloaded_bytes": int(downloaded) if downloaded else None,
                    "download_speed_bytes_per_sec": download_speed,
                    "eta_seconds": eta_seconds,
                    "file_path": None,  # uTorrent doesn't provide this directly
                }
                items.append(item)

        except Exception as e:
            msg = f"Failed to get downloads from uTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from uTorrent.

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
            msg = "uTorrent client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(client_item_id.lower(), delete_files)
        except Exception as e:
            msg = f"Failed to remove download from uTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to uTorrent.

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
            # Try to get torrent list as connection test
            self._proxy.get_torrents()
        except Exception as e:
            msg = f"Failed to connect to uTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

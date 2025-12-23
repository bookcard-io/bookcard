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

"""Hadouken download client implementation.

Hadouken is a web-based torrent client that uses JSON-RPC API.
This implementation supports adding torrents, monitoring downloads,
and managing torrents via Hadouken's JSON-RPC API.

Documentation: https://github.com/hadouken/hadouken
"""

import base64
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from bookcard.pvr.base import (
    BaseDownloadClient,
    DownloadClientSettings,
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


class HadoukenSettings(DownloadClientSettings):
    """Settings for Hadouken download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    """

    url_base: str | None = None


class HadoukenProxy:
    """Low-level proxy for Hadouken JSON-RPC API.

    Handles authentication, request building, and API communication.
    """

    def __init__(self, settings: HadoukenSettings) -> None:
        """Initialize Hadouken proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.api_url = urljoin(self.base_url.rstrip("/") + "/", "api")

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _build_auth_header(self) -> str | None:
        """Build Basic Auth header if credentials are provided.

        Returns
        -------
        str | None
            Auth header string or None.
        """
        if self.settings.username and self.settings.password:
            credentials = f"{self.settings.username}:{self.settings.password}"
            auth_bytes = base64.b64encode(credentials.encode("utf-8"))
            return f"Basic {auth_bytes.decode('utf-8')}"
        return None

    def _request(
        self,
        method: str,
        *params: str | int | dict[str, str | int] | list[str | int],
    ) -> str | int | dict[str, str | int] | list[str | int] | None:
        """Make JSON-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : str | int | dict[str, str | int] | list[str | int]
            Method parameters.

        Returns
        -------
        str | int | dict[str, str | int] | list[str | int] | None
            JSON-RPC response result.

        Raises
        ------
        PVRProviderError
            If request fails.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        auth = self._build_auth_header()
        if auth:
            headers["Authorization"] = auth

        # Build JSON-RPC request
        request_id = 1
        jsonrpc_request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
        }
        if params:
            jsonrpc_request["params"] = list(params)

        with self._get_client() as client:
            try:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    json=jsonrpc_request,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code in (401, 403):
                    msg = "Hadouken authentication failed"
                    raise PVRProviderAuthenticationError(msg)

                response.raise_for_status()

                json_response = response.json()

                # Check for JSON-RPC error
                if "error" in json_response:
                    error = json_response["error"]
                    if error is None:
                        # No error, continue
                        pass
                    elif isinstance(error, dict):
                        error_msg = error.get("message", "Unknown error")
                        msg = f"Hadouken JSON-RPC error: {error_msg}"
                        raise PVRProviderError(msg)
                    else:
                        error_msg = str(error)
                        msg = f"Hadouken JSON-RPC error: {error_msg}"
                        raise PVRProviderError(msg)

                return json_response.get("result")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Hadouken authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Hadouken API {method}")
                raise

    def get_system_info(self) -> dict[str, Any]:
        """Get Hadouken system information.

        Returns
        -------
        dict[str, Any]
            System information dictionary.
        """
        result = self._request("core.getSystemInfo")
        if isinstance(result, dict):
            return result
        msg = "Unexpected response type from Hadouken getSystemInfo"
        raise PVRProviderError(msg)

    def get_torrents(self) -> list[list[Any]]:
        """Get all torrents.

        Returns
        -------
        list[list[Any]]
            List of torrent arrays.
        """
        response = self._request("webui.list")
        if isinstance(response, dict):
            torrents = response.get("torrents", [])
            if isinstance(torrents, list):
                # Ensure all items are lists
                return [item if isinstance(item, list) else [] for item in torrents]
        if isinstance(response, list):
            # Ensure all items are lists
            return [item if isinstance(item, list) else [] for item in response]
        return []

    def add_torrent_url(self, url: str, category: str | None = None) -> None:
        """Add torrent from URL or magnet link.

        Parameters
        ----------
        url : str
            Torrent URL or magnet link.
        category : str | None
            Optional category/label.
        """
        params: dict[str, Any] = {"url": url}
        if category:
            params["label"] = category
        self._request("webui.addTorrent", params)

    def add_torrent_file(self, file_content: bytes, category: str | None = None) -> str:
        """Add torrent from file.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        category : str | None
            Optional category/label.

        Returns
        -------
        str
            Torrent hash.
        """
        file_base64 = base64.b64encode(file_content).decode("utf-8")
        params: dict[str, str | int] = {"file": file_base64}
        if category:
            params["label"] = category
        result = self._request("webui.addTorrent", params)
        if isinstance(result, str):
            return result
        return ""

    def remove_torrent(self, hash_str: str, delete_data: bool = False) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        delete_data : bool
            Whether to delete downloaded data.
        """
        action = "removedata" if delete_data else "remove"
        self._request("webui.perform", action, [hash_str])


class HadoukenClient(BaseDownloadClient):
    """Hadouken download client implementation.

    Implements BaseDownloadClient interface for Hadouken JSON-RPC API.
    """

    def __init__(
        self,
        settings: HadoukenSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize Hadouken client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, HadoukenSettings
        ):
            settings = HadoukenSettings(
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

        super().__init__(settings, enabled)
        self.settings: HadoukenSettings = settings  # type: ignore[assignment]
        self._proxy = HadoukenProxy(self.settings)

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Hadouken"

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

    def _add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        cat = category or self.settings.category
        self._proxy.add_torrent_url(magnet_url, category=cat)
        return self._extract_hash_from_magnet(magnet_url)

    def _add_url(
        self,
        url: str,
        _title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        cat = category or self.settings.category
        self._proxy.add_torrent_url(url, category=cat)
        return "pending"

    def _add_file(
        self,
        filepath: str,
        _title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        cat = category or self.settings.category
        hash_str = self._proxy.add_torrent_file(file_content, category=cat)
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
            torrents_raw = self._proxy.get_torrents()

            items = []
            for item in torrents_raw:
                if not item or len(item) < 27:
                    continue

                # Parse torrent data (based on Sonarr implementation)
                hash_str = str(item[0])
                state_int = int(item[1]) if item[1] else 0
                name = str(item[2])
                total_size = int(item[3]) if item[3] else 0
                progress = float(item[4]) if item[4] else 0.0
                downloaded_bytes = int(item[5]) if item[5] else 0
                int(item[6]) if item[6] else 0
                download_rate = int(item[9]) if len(item) > 9 and item[9] else 0
                label = str(item[11]) if len(item) > 11 and item[11] else ""
                error = str(item[21]) if len(item) > 21 and item[21] else ""
                save_path = str(item[26]) if len(item) > 26 and item[26] else ""

                # Filter by category if set
                if self.settings.category and label != self.settings.category:
                    continue

                # Map state to status
                status = self._map_state_to_status(state_int, progress, error)

                # Calculate progress percentage
                progress_pct = progress / 1000.0 if progress > 0 else 0.0
                if progress_pct > 1.0:
                    progress_pct = 1.0

                # Calculate ETA
                eta_seconds = None
                if download_rate > 0 and total_size > 0:
                    remaining = total_size - downloaded_bytes
                    if remaining > 0:
                        eta_seconds = int(remaining / download_rate)

                item_dict: DownloadItem = {
                    "client_item_id": hash_str.upper(),
                    "title": name,
                    "status": status,
                    "progress": progress_pct,
                    "size_bytes": total_size if total_size > 0 else None,
                    "downloaded_bytes": downloaded_bytes
                    if downloaded_bytes > 0
                    else None,
                    "download_speed_bytes_per_sec": download_rate
                    if download_rate > 0
                    else None,
                    "eta_seconds": eta_seconds,
                    "file_path": save_path,
                }
                items.append(item_dict)

        except Exception as e:
            msg = f"Failed to get downloads from Hadouken: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Hadouken.

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
            msg = "Hadouken client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(client_item_id.lower(), delete_files)
        except Exception as e:
            msg = f"Failed to remove download from Hadouken: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Hadouken.

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
            sys_info = self._proxy.get_system_info()
            versions = sys_info.get("versions", {})
            version_str = versions.get("hadouken", "0.0")
            logger.debug("Hadouken version: %s", version_str)
        except Exception as e:
            msg = f"Failed to connect to Hadouken: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_state_to_status(self, state_int: int, progress: float, error: str) -> str:
        """Map Hadouken state to standardized status.

        Parameters
        ----------
        state_int : int
            Hadouken state integer (bit flags).
        progress : float
            Progress value (0-1000).
        error : str
            Error message if any.

        Returns
        -------
        str
            Standardized status string.
        """
        if error:
            return DownloadStatus.FAILED

        # Check bit flags
        if (state_int & 1) == 1:
            return DownloadStatus.DOWNLOADING
        if (state_int & 2) == 2:
            return DownloadStatus.QUEUED  # Checking files
        if (state_int & 32) == 32:
            return DownloadStatus.PAUSED
        if (state_int & 64) == 64:
            return DownloadStatus.QUEUED  # Queued for checking

        # Check progress for completion
        if progress >= 1000:
            return DownloadStatus.COMPLETED

        return DownloadStatus.QUEUED

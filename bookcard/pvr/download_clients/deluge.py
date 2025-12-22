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

"""Deluge download client implementation.

Deluge is a torrent client that uses JSON-RPC API (via WebUI or daemon).
This implementation supports adding torrents, monitoring downloads,
and managing torrents.

Documentation: https://deluge.readthedocs.io/en/latest/reference/rpc.html
"""

import base64
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import urljoin

import httpx

from bookcard.pvr.base import (
    BaseDownloadClient,
    DownloadClientSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
    handle_http_error_response,
)
from bookcard.pvr.download_clients._http_client import (
    build_base_url,
    create_httpx_client,
    handle_httpx_exception,
)

logger = logging.getLogger(__name__)


class DelugeSettings(DownloadClientSettings):
    """Settings for Deluge download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    """

    url_base: str | None = None


class DelugeProxy:
    """Low-level proxy for Deluge JSON-RPC API.

    Handles authentication, JSON-RPC request building, and API communication.
    """

    def __init__(self, settings: DelugeSettings) -> None:
        """Initialize Deluge proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = urljoin(self.base_url.rstrip("/") + "/", "json")
        self._session_id: str | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with Deluge daemon.

        Parameters
        ----------
        force : bool
            Force re-authentication.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._session_id is not None:
            return

        if not self.settings.username or not self.settings.password:
            msg = "Deluge requires username and password"
            raise PVRProviderAuthenticationError(msg)

        # Authenticate
        auth_request: dict[str, Any] = {
            "method": "auth.login",
            "params": [self.settings.password],
            "id": 1,
        }

        with self._get_client() as client:
            try:
                response = client.post(
                    self.rpc_url,
                    json=auth_request,
                    timeout=self.settings.timeout_seconds,
                )
                response.raise_for_status()

                result = response.json()
                if result.get("error"):
                    msg = "Deluge authentication failed"
                    raise PVRProviderAuthenticationError(msg)

                self._session_id = result.get("result")
                if not self._session_id:
                    msg = "Deluge authentication failed: no session ID"
                    raise PVRProviderAuthenticationError(msg)

                logger.debug("Deluge authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Deluge authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Deluge authentication")
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, "Deluge authentication")

    def _handle_rpc_error(
        self,
        result: dict[str, Any],
        rpc_request: dict[str, Any],
        cookies: dict[str, str],
        client: httpx.Client,
    ) -> dict[str, Any]:
        """Handle RPC error, retrying authentication if needed.

        Parameters
        ----------
        result : dict[str, Any]
            RPC response result.
        rpc_request : dict[str, Any]
            Original RPC request.
        cookies : dict[str, str]
            Cookies dict to update.
        client : httpx.Client
            HTTP client.

        Returns
        -------
        dict[str, Any]
            Updated result after retry.

        Raises
        ------
        PVRProviderError
            If error persists after retry.
        """
        error = result["error"]
        error_code = error.get("code", 0)
        if error_code in (1, 2):  # Authentication errors
            self._authenticate(force=True)
            if self._session_id:
                cookies["_session_id"] = self._session_id
            response = client.post(
                self.rpc_url,
                json=rpc_request,
                cookies=cookies,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()

        if result.get("error"):
            error_msg = error.get("message", "Unknown error")
            msg = f"Deluge RPC error: {error_msg}"
            raise PVRProviderError(msg)
        return result

    def _make_rpc_request(
        self,
        rpc_request: dict[str, Any],
        cookies: dict[str, str],
        client: httpx.Client,
    ) -> httpx.Response:
        """Make RPC request with session handling.

        Parameters
        ----------
        rpc_request : dict[str, Any]
            RPC request dict.
        cookies : dict[str, str]
            Cookies dict.
        client : httpx.Client
            HTTP client.

        Returns
        -------
        httpx.Response
            HTTP response.
        """
        response = client.post(
            self.rpc_url,
            json=rpc_request,
            cookies=cookies,
            timeout=self.settings.timeout_seconds,
        )

        # Handle session expiration
        if response.status_code == 403:
            logger.debug("Session expired, re-authenticating")
            self._authenticate(force=True)
            if self._session_id:
                cookies["_session_id"] = self._session_id
            response = client.post(
                self.rpc_url,
                json=rpc_request,
                cookies=cookies,
                timeout=self.settings.timeout_seconds,
            )

        return response

    def _request(
        self, method: str, *args: str | float | bool | list[Any] | dict[str, Any] | None
    ) -> str | int | float | bool | list[Any] | dict[str, Any] | None:
        """Make JSON-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *args : Union[str, int, float, bool, None, list[Any], dict[str, Any]]
            Method arguments.

        Returns
        -------
        Union[str, int, float, bool, None, list[Any], dict[str, Any]]
            RPC response result.
        """
        self._authenticate()

        rpc_request: dict[str, Any] = {
            "method": method,
            "params": list(args),
            "id": 1,
        }

        # Add session ID to cookies or headers
        cookies: dict[str, str] = {}
        if self._session_id:
            cookies["_session_id"] = self._session_id

        with self._get_client() as client:
            try:
                response = self._make_rpc_request(rpc_request, cookies, client)
                response.raise_for_status()

                result = response.json()

                # Check for RPC errors
                if result.get("error"):
                    result = self._handle_rpc_error(
                        result, rpc_request, cookies, client
                    )

                return result.get("result")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Deluge authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, f"Deluge RPC {method}")

    def get_version(self) -> str:
        """Get Deluge version."""
        return str(self._request("daemon.info"))

    def add_torrent_magnet(
        self, magnet_link: str, options: dict[str, Any] | None = None
    ) -> str:
        """Add torrent from magnet link.

        Parameters
        ----------
        magnet_link : str
            Magnet link.
        options : dict[str, Any] | None
            Optional torrent options.

        Returns
        -------
        str
            Torrent hash.
        """
        if options is None:
            options = {}

        hash_str = self._request("core.add_torrent_magnet", magnet_link, options)
        return str(hash_str)

    def add_torrent_file(
        self, filename: str, file_content: bytes, options: dict[str, Any] | None = None
    ) -> str:
        """Add torrent from file.

        Parameters
        ----------
        filename : str
            Torrent filename.
        file_content : bytes
            Torrent file content.
        options : dict[str, Any] | None
            Optional torrent options.

        Returns
        -------
        str
            Torrent hash.
        """
        if options is None:
            options = {}

        # Encode file content as base64
        file_base64 = base64.b64encode(file_content).decode("utf-8")

        hash_str = self._request(
            "core.add_torrent_file", filename, file_base64, options
        )
        return str(hash_str)

    def get_torrents(self) -> list[dict[str, Any]]:
        """Get all torrents.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        # Use web.update_ui for better performance
        fields = [
            "hash",
            "name",
            "state",
            "progress",
            "eta",
            "message",
            "is_finished",
            "save_path",
            "total_size",
            "total_done",
            "time_added",
            "active_time",
            "ratio",
            "is_auto_managed",
            "stop_at_ratio",
            "remove_at_ratio",
            "stop_ratio",
        ]

        filter_dict: dict[str, Any] = {}
        result = self._request("web.update_ui", fields, filter_dict)

        if not result or not isinstance(result, dict) or "torrents" not in result:
            return []

        torrents = result["torrents"]
        return list(torrents.values()) if isinstance(torrents, dict) else torrents

    def get_torrents_by_label(self, label: str) -> list[dict[str, Any]]:
        """Get torrents by label.

        Parameters
        ----------
        label : str
            Label name.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        filter_dict: dict[str, Any] = {"label": label}
        fields = [
            "hash",
            "name",
            "state",
            "progress",
            "eta",
            "message",
            "is_finished",
            "save_path",
            "total_size",
            "total_done",
            "time_added",
            "active_time",
            "ratio",
        ]

        result = self._request("web.update_ui", fields, filter_dict)

        if not result or not isinstance(result, dict) or "torrents" not in result:
            return []

        torrents = result["torrents"]
        return list(torrents.values()) if isinstance(torrents, dict) else torrents

    def remove_torrent(self, hash_str: str, remove_data: bool = False) -> bool:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        remove_data : bool
            Whether to remove downloaded data.

        Returns
        -------
        bool
            True if successful.
        """
        return bool(self._request("core.remove_torrent", hash_str, remove_data))

    def set_torrent_label(self, hash_str: str, label: str) -> None:
        """Set torrent label.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        label : str
            Label name.
        """
        self._request("label.set_torrent", hash_str, label)


class DelugeClient(BaseDownloadClient):
    """Deluge download client implementation.

    Implements BaseDownloadClient interface for Deluge JSON-RPC API.
    """

    def __init__(
        self,
        settings: DelugeSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize Deluge client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, DelugeSettings
        ):
            deluge_settings = DelugeSettings(
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
            settings = deluge_settings

        super().__init__(settings, enabled)
        self.settings: DelugeSettings = settings  # type: ignore[assignment]
        self._proxy = DelugeProxy(self.settings)

    def _raise_invalid_url_error(self, download_url: str) -> NoReturn:
        """Raise error for invalid download URL.

        Parameters
        ----------
        download_url : str
            Invalid download URL.

        Raises
        ------
        PVRProviderError
            Always raises with error message.
        """
        msg = f"Invalid download URL: {download_url}"
        raise PVRProviderError(msg)

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add a download to Deluge.

        Parameters
        ----------
        download_url : str
            URL, magnet link, or file path.
        title : str | None
            Optional title.
        category : str | None
            Optional category (label in Deluge).
        download_path : str | None
            Optional download path.

        Returns
        -------
        str
            Torrent hash.

        Raises
        ------
        PVRProviderError
            If adding the download fails.
        """
        if not self.is_enabled():
            msg = "Deluge client is disabled"
            raise PVRProviderError(msg)

        try:
            # Build options
            options: dict[str, Any] = {
                "add_paused": False,
                "remove_at_ratio": False,
            }

            if download_path or self.settings.download_path:
                options["download_location"] = (
                    download_path or self.settings.download_path
                )

            # Add torrent
            if download_url.startswith("magnet:"):
                hash_str = self._proxy.add_torrent_magnet(download_url, options)
            elif download_url.startswith("http"):
                # Download torrent file first
                import httpx

                with httpx.Client() as client:
                    response = client.get(download_url, timeout=30)
                    response.raise_for_status()
                    file_content = response.content
                    filename = (
                        title or download_url.split("/")[-1] or "download.torrent"
                    )
                    hash_str = self._proxy.add_torrent_file(
                        filename, file_content, options
                    )
            elif Path(download_url).is_file():
                file_content = Path(download_url).read_bytes()
                filename = title or Path(download_url).name
                hash_str = self._proxy.add_torrent_file(filename, file_content, options)
            else:
                self._raise_invalid_url_error(download_url)

            # Set label if provided
            label = category or self.settings.category
            if label:
                self._proxy.set_torrent_label(hash_str, label)

            return hash_str.upper()

        except Exception as e:
            msg = f"Failed to add download to Deluge: {e}"
            raise PVRProviderError(msg) from e

    def get_items(self) -> Sequence[dict[str, str | int | float | None]]:
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
            # Get torrents (filter by category if set)
            if self.settings.category:
                torrents = self._proxy.get_torrents_by_label(self.settings.category)
            else:
                torrents = self._proxy.get_torrents()

            items = []
            for torrent in torrents:
                hash_str = torrent.get("hash", "")
                if not hash_str:
                    continue

                # Map Deluge state to our status
                state = torrent.get("state", "")
                status = self._map_state_to_status(state)

                # Calculate progress
                progress = float(torrent.get("progress", 0.0)) / 100.0
                if progress > 1.0:
                    progress = 1.0

                total_size = torrent.get("total_size", 0)
                total_done = torrent.get("total_done", 0)

                # Get ETA
                eta = torrent.get("eta", -1)
                eta_seconds = int(eta) if eta > 0 else None

                item = {
                    "client_item_id": str(hash_str).upper(),
                    "title": torrent.get("name", ""),
                    "status": status,
                    "progress": progress,
                    "size_bytes": total_size,
                    "downloaded_bytes": total_done,
                    "download_speed_bytes_per_sec": None,  # Not directly available
                    "eta_seconds": eta_seconds,
                    "file_path": torrent.get("save_path"),
                }
                items.append(item)

        except Exception as e:
            msg = f"Failed to get downloads from Deluge: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Deluge.

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
            msg = "Deluge client is disabled"
            raise PVRProviderError(msg)

        try:
            return self._proxy.remove_torrent(client_item_id.lower(), delete_files)

        except Exception as e:
            msg = f"Failed to remove download from Deluge: {e}"
            raise PVRProviderError(msg) from e

    def test_connection(self) -> bool:
        """Test connectivity to Deluge.

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
            logger.debug("Deluge version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to Deluge: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_state_to_status(self, state: str) -> str:
        """Map Deluge state to standardized status.

        Parameters
        ----------
        state : str
            Deluge state string.

        Returns
        -------
        str
            Standardized status string.
        """
        # Deluge states: Downloading, Seeding, Paused, Checking, Queued, Error, etc.
        if state in ("Seeding", "seeding"):
            return "completed"
        if state in ("Downloading", "downloading"):
            return "downloading"
        if state in ("Paused", "paused"):
            return "paused"
        if state in ("Queued", "queued", "Checking", "checking"):
            return "queued"
        if state in ("Error", "error"):
            return "failed"
        return "downloading"

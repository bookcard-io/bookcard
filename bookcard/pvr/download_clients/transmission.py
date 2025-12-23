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

"""Transmission download client implementation.

This module provides a Transmission download client that implements the
BaseDownloadClient interface. It uses the Transmission RPC API.

Documentation: https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
"""

import base64
import json
import logging
import pathlib
from collections.abc import Sequence
from contextlib import suppress
from typing import Any

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


class TransmissionSettings(DownloadClientSettings):
    """Settings for Transmission download client.

    Extends DownloadClientSettings with Transmission-specific configuration.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/transmission/').
    """

    url_base: str | None = "/transmission/"


class TransmissionProxy:
    """Low-level proxy for Transmission RPC API.

    Handles authentication, JSON-RPC request building, and API communication.
    Follows SRP by separating API communication from business logic.
    """

    def __init__(self, settings: TransmissionSettings) -> None:
        """Initialize Transmission proxy.

        Parameters
        ----------
        settings : TransmissionSettings
            Transmission client settings.
        """
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = f"{self.base_url.rstrip('/')}/rpc"
        self._session_id: str | None = None

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
            follow_redirects=False,  # Transmission may redirect
        )

    def _handle_409_response(self, response: httpx.Response) -> None:
        """Handle 409 Conflict response and extract session ID.

        Parameters
        ----------
        response : httpx.Response
            HTTP response with 409 status.

        Raises
        ------
        PVRProviderAuthenticationError
            If session ID is not found.
        """
        session_id = response.headers.get("X-Transmission-Session-Id")
        if not session_id:
            msg = "Transmission did not return session ID"
            raise PVRProviderAuthenticationError(msg)
        self._session_id = session_id
        logger.debug("Transmission authentication succeeded")

    def _handle_200_response(self, response: httpx.Response) -> None:
        """Handle 200 OK response (authentication might not be required).

        Parameters
        ----------
        response : httpx.Response
            HTTP response with 200 status.
        """
        with suppress(Exception):
            data = response.json()
            if data.get("result") == "success":
                # No session ID needed
                self._session_id = ""

    def _build_auth_header(self) -> str | None:
        """Build Basic Auth header if credentials are provided.

        Returns
        -------
        str | None
            Auth header string or None.
        """
        if self.settings.username and self.settings.password:
            from base64 import b64encode

            credentials = f"{self.settings.username}:{self.settings.password}"
            auth_bytes = b64encode(credentials.encode("utf-8"))
            return f"Basic {auth_bytes.decode('utf-8')}"
        return None

    def _handle_auth_response(self, response: httpx.Response) -> None:
        """Handle authentication response based on status code.

        Parameters
        ----------
        response : httpx.Response
            Authentication response.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if response.status_code == 409:
            self._handle_409_response(response)
            return

        if response.status_code == 401:
            msg = "Transmission authentication failed: invalid credentials"
            raise PVRProviderAuthenticationError(msg)

        if response.status_code == 403:
            msg = "Transmission authentication failed: access forbidden"
            raise PVRProviderAuthenticationError(msg)

        # If we get here, authentication might not be required
        if response.status_code == 200:
            self._handle_200_response(response)
            return

        # Unexpected response
        msg = f"Transmission authentication failed: HTTP {response.status_code}"
        raise PVRProviderAuthenticationError(msg)

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with Transmission RPC API.

        Transmission uses session-based authentication via X-Transmission-Session-Id header.

        Parameters
        ----------
        force : bool
            Force re-authentication even if already authenticated.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._session_id is not None:
            return

        auth = self._build_auth_header()

        # Make initial request to get session ID
        headers: dict[str, str] = {}
        if auth:
            headers["Authorization"] = auth

        with self._get_client() as client:
            try:
                # First request will return 409 Conflict with session ID
                response = client.post(self.rpc_url, headers=headers, json={})
                self._handle_auth_response(response)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Transmission authentication failed: invalid credentials"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Transmission authentication")
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, "Transmission authentication")

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers.

        Returns
        -------
        dict[str, str]
            Headers dictionary with auth and session ID.
        """
        headers: dict[str, str] = {}
        if self.settings.username and self.settings.password:
            credentials = f"{self.settings.username}:{self.settings.password}"
            auth_bytes = base64.b64encode(credentials.encode("utf-8"))
            headers["Authorization"] = f"Basic {auth_bytes.decode('utf-8')}"

        if self._session_id:
            headers["X-Transmission-Session-Id"] = self._session_id

        return headers

    def _parse_rpc_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON-RPC response and check for errors.

        Parameters
        ----------
        response : httpx.Response
            HTTP response.

        Returns
        -------
        dict[str, Any]
            Parsed RPC response.

        Raises
        ------
        PVRProviderError
            If parsing fails or response contains error.
        """
        # Parse JSON response
        try:
            rpc_response = response.json()
        except json.JSONDecodeError as e:
            msg = f"Failed to parse Transmission RPC response: {e}"
            raise PVRProviderError(msg) from e

        # Check for RPC errors
        if rpc_response.get("result") != "success":
            error = rpc_response.get("result", "unknown error")
            msg = f"Transmission RPC error: {error}"
            raise PVRProviderError(msg)

        return rpc_response

    def _request(
        self, method: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated RPC request.

        Parameters
        ----------
        method : str
            RPC method name (e.g., 'torrent-get').
        arguments : dict[str, Any] | None
            RPC method arguments.

        Returns
        -------
        dict[str, Any]
            RPC response dictionary.

        Raises
        ------
        PVRProviderError
            If request fails.
        """
        self._authenticate()

        headers = self._build_auth_headers()

        # Build JSON-RPC request
        rpc_request: dict[str, Any] = {"method": method}
        if arguments:
            rpc_request["arguments"] = arguments

        with self._get_client() as client:
            try:
                response = client.post(
                    self.rpc_url,
                    headers=headers,
                    json=rpc_request,
                    timeout=self.settings.timeout_seconds,
                )

                # Handle 409 Conflict (session expired)
                if response.status_code == 409:
                    logger.debug("Session expired, re-authenticating")
                    self._authenticate(force=True)
                    headers = self._build_auth_headers()
                    response = client.post(
                        self.rpc_url,
                        headers=headers,
                        json=rpc_request,
                        timeout=self.settings.timeout_seconds,
                    )

                response.raise_for_status()
                rpc_response = self._parse_rpc_response(response)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Transmission authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Transmission RPC {method}")
                raise
            else:
                return rpc_response

    def get_version(self) -> str:
        """Get Transmission version.

        Returns
        -------
        str
            Version string.
        """
        response = self._request("session-get")
        return response.get("arguments", {}).get("version", "unknown")

    def add_torrent_from_url(
        self, torrent_url: str, download_dir: str | None = None, paused: bool = False
    ) -> dict[str, Any]:
        """Add torrent from URL or magnet link.

        Parameters
        ----------
        torrent_url : str
            Torrent URL or magnet link.
        download_dir : str | None
            Optional download directory.
        paused : bool
            Whether to add torrent in paused state.

        Returns
        -------
        dict[str, Any]
            RPC response with torrent information.
        """
        arguments: dict[str, Any] = {
            "filename": torrent_url,
            "paused": paused,
        }
        if download_dir:
            arguments["download-dir"] = download_dir

        return self._request("torrent-add", arguments)

    def add_torrent_from_file(
        self,
        file_content: bytes,
        download_dir: str | None = None,
        paused: bool = False,
    ) -> dict[str, Any]:
        """Add torrent from file content.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        download_dir : str | None
            Optional download directory.
        paused : bool
            Whether to add torrent in paused state.

        Returns
        -------
        dict[str, Any]
            RPC response with torrent information.
        """
        # Encode file content as base64
        metainfo = base64.b64encode(file_content).decode("utf-8")

        arguments: dict[str, Any] = {
            "metainfo": metainfo,
            "paused": paused,
        }
        if download_dir:
            arguments["download-dir"] = download_dir

        return self._request("torrent-add", arguments)

    def get_torrents(
        self, ids: list[str] | None = None, fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get list of torrents.

        Parameters
        ----------
        ids : list[str] | None
            Optional list of torrent IDs (hashes) to filter.
        fields : list[str] | None
            Optional list of fields to retrieve.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        if fields is None:
            fields = [
                "id",
                "hashString",
                "name",
                "downloadDir",
                "totalSize",
                "leftUntilDone",
                "isFinished",
                "eta",
                "status",
                "uploadedEver",
                "downloadedEver",
                "seedRatioLimit",
                "seedRatioMode",
                "seedIdleLimit",
                "seedIdleMode",
                "files",
                "labels",
            ]

        arguments: dict[str, Any] = {"fields": fields}
        if ids:
            arguments["ids"] = ids

        response = self._request("torrent-get", arguments)
        return response.get("arguments", {}).get("torrents", [])

    def remove_torrent(self, hash_str: str, delete_files: bool = False) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        delete_files : bool
            Whether to delete downloaded files.
        """
        arguments: dict[str, Any] = {
            "ids": [hash_str],
            "delete-local-data": delete_files,
        }
        self._request("torrent-remove", arguments)


class TransmissionClient(BaseDownloadClient):
    """Transmission download client implementation.

    Implements BaseDownloadClient interface for Transmission RPC API.
    """

    def __init__(
        self,
        settings: TransmissionSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize Transmission client.

        Parameters
        ----------
        settings : TransmissionSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to TransmissionSettings.
        enabled : bool
            Whether this client is enabled.
        """
        # Convert DownloadClientSettings to TransmissionSettings if needed
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, TransmissionSettings
        ):
            trans_settings = TransmissionSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/transmission/",
            )
            settings = trans_settings

        super().__init__(settings, enabled)
        self.settings: TransmissionSettings = settings  # type: ignore[assignment]
        self._proxy = TransmissionProxy(self.settings)

    def add_download(
        self,
        download_url: str,
        _title: str | None = None,
        _category: str | None = None,
        download_path: str | None = None,
    ) -> str:
        """Add a download to Transmission.

        Parameters
        ----------
        download_url : str
            URL or magnet link for the download.
        title : str | None
            Optional title (not used by Transmission API).
        category : str | None
            Optional category/tag (Transmission uses labels).
        download_path : str | None
            Optional custom download path.

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
            msg = "Transmission client is disabled"
            raise PVRProviderError(msg)

        def _raise_hash_error() -> None:
            """Raise error when hash is not found."""
            msg = "Failed to get torrent hash from Transmission response"
            raise PVRProviderError(msg)

        try:
            # Use download_path from settings if not provided
            path = download_path or self.settings.download_path

            # Add torrent
            if download_url.startswith(("magnet:", "http")):
                response = self._proxy.add_torrent_from_url(
                    download_url, download_dir=path
                )
            else:
                # Assume it's a file path - read and upload
                with pathlib.Path(download_url).open("rb") as f:
                    file_content = f.read()
                response = self._proxy.add_torrent_from_file(
                    file_content, download_dir=path
                )

            # Extract hash from response
            torrent = response.get("arguments", {}).get("torrent-added", {})
            if not torrent:
                # Try torrent-duplicate
                torrent = response.get("arguments", {}).get("torrent-duplicate", {})

            hash_str = torrent.get("hashString", "")
            if not hash_str and download_url.startswith("magnet:"):
                # Extract hash from magnet link as fallback
                for part in download_url.split("&"):
                    if "xt=urn:btih:" in part:
                        hash_str = part.split(":")[-1].upper()
                        break

            if not hash_str:
                _raise_hash_error()

            return hash_str.upper()

        except Exception as e:
            msg = f"Failed to add download to Transmission: {e}"
            raise PVRProviderError(msg) from e

    def get_items(self) -> Sequence[dict[str, str | int | float | None]]:
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
            torrents = self._proxy.get_torrents()

            items = []
            for torrent in torrents:
                # Map Transmission status to our status
                status_code = torrent.get("status", 0)
                status = self._map_status_to_status(status_code)

                # Calculate progress
                total_size = torrent.get("totalSize", 0)
                left_until_done = torrent.get("leftUntilDone", 0)
                progress = 1.0 - left_until_done / total_size if total_size > 0 else 0.0

                # Get download directory
                download_dir = torrent.get("downloadDir", "")

                # Calculate download speed (not directly available, estimate from ETA)
                download_speed = None
                eta = torrent.get("eta", -1)
                if eta > 0 and left_until_done > 0:
                    download_speed = left_until_done / eta

                item = {
                    "client_item_id": torrent.get("hashString", "").upper(),
                    "title": torrent.get("name", ""),
                    "status": status,
                    "progress": progress,
                    "size_bytes": total_size,
                    "downloaded_bytes": total_size - left_until_done,
                    "download_speed_bytes_per_sec": download_speed,
                    "eta_seconds": eta if eta > 0 else None,
                    "file_path": download_dir,
                }
                items.append(item)
        except Exception as e:
            msg = f"Failed to get downloads from Transmission: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Transmission.

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
            msg = "Transmission client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(
                client_item_id.lower(), delete_files=delete_files
            )
        except Exception as e:
            msg = f"Failed to remove download from Transmission: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Transmission.

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
            logger.debug("Transmission version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to Transmission: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_status_to_status(self, status_code: int) -> str:
        """Map Transmission status code to standardized status.

        Parameters
        ----------
        status_code : int
            Transmission status code.

        Returns
        -------
        str
            Standardized status string.

        Notes
        -----
        Transmission status codes:
        - 0: Stopped
        - 1: Check waiting
        - 2: Checking
        - 3: Download waiting
        - 4: Downloading
        - 5: Seed waiting
        - 6: Seeding
        """
        # Completed states (seeding)
        if status_code == 6:
            return "completed"

        # Downloading
        if status_code == 4:
            return "downloading"

        # Queued states
        if status_code in (1, 2, 3, 5):
            return "queued"

        # Stopped (paused)  # noqa: ERA001
        if status_code == 0:
            return "paused"

        # Default to downloading
        return "downloading"

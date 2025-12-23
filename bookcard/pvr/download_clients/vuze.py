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

"""Vuze download client implementation.

Vuze is a BitTorrent client that uses Transmission RPC API.
This implementation supports adding torrents, monitoring downloads,
and managing torrents via Vuze's Transmission-compatible RPC API.

Note: Vuze uses the same RPC API as Transmission, so this implementation
is based on the Transmission client with Vuze-specific adjustments.
"""

import base64
import json
import logging
import pathlib
from collections.abc import Callable, Sequence
from contextlib import suppress
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


class VuzeSettings(DownloadClientSettings):
    """Settings for Vuze download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    """

    url_base: str | None = None


class VuzeProxy:
    """Low-level proxy for Vuze Transmission RPC API.

    Handles authentication, JSON-RPC request building, and API communication.
    Vuze uses the same RPC API as Transmission.
    """

    def __init__(self, settings: VuzeSettings) -> None:
        """Initialize Vuze proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = f"{self.base_url.rstrip('/')}/rpc"
        self._session_id: str | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=False,
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
            session_id = response.headers.get("X-Transmission-Session-Id")
            if not session_id:
                msg = "Vuze did not return session ID"
                raise PVRProviderAuthenticationError(msg)
            self._session_id = session_id
            logger.debug("Vuze authentication succeeded")
            return

        if response.status_code == 401:
            msg = "Vuze authentication failed: invalid credentials"
            raise PVRProviderAuthenticationError(msg)

        if response.status_code == 403:
            msg = "Vuze authentication failed: access forbidden"
            raise PVRProviderAuthenticationError(msg)

        # If we get here, authentication might not be required
        if response.status_code == 200:
            with suppress(Exception):
                data = response.json()
                if data.get("result") == "success":
                    self._session_id = ""
                    return

        # Unexpected response
        msg = f"Vuze authentication failed: HTTP {response.status_code}"
        raise PVRProviderAuthenticationError(msg)

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with Vuze RPC API.

        Vuze uses session-based authentication via X-Transmission-Session-Id header.

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
                    msg = "Vuze authentication failed: invalid credentials"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Vuze authentication")
            except (httpx.TimeoutException, httpx.RequestError, ValueError) as e:
                handle_httpx_exception(e, "Vuze authentication")

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
        try:
            rpc_response = response.json()
        except json.JSONDecodeError as e:
            msg = f"Failed to parse Vuze RPC response: {e}"
            raise PVRProviderError(msg) from e

        if rpc_response.get("result") != "success":
            error = rpc_response.get("result", "unknown error")
            msg = f"Vuze RPC error: {error}"
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
                    msg = "Vuze authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Vuze RPC {method}")
                raise
            else:
                return rpc_response

    def get_protocol_version(self) -> str:
        """Get Vuze protocol version.

        Returns
        -------
        str
            Protocol version string.
        """
        response = self._request("session-get")
        return str(response.get("arguments", {}).get("version", "0"))

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
                "files",
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


class VuzeClient(BaseDownloadClient):
    """Vuze download client implementation.

    Implements BaseDownloadClient interface for Vuze Transmission RPC API.
    """

    def __init__(
        self,
        settings: VuzeSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize Vuze client.

        Parameters
        ----------
        settings : VuzeSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to VuzeSettings.
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
            settings, VuzeSettings
        ):
            settings = VuzeSettings(
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

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: VuzeSettings = settings  # type: ignore[assignment]
        self._proxy = VuzeProxy(self.settings)
        # Vuze uses Transmission RPC API, same status codes
        self._status_mapper = StatusMapper(
            {
                6: DownloadStatus.COMPLETED,  # Seeding
                4: DownloadStatus.DOWNLOADING,  # Downloading
                1: DownloadStatus.QUEUED,  # Check waiting
                2: DownloadStatus.CHECKING,  # Checking
                3: DownloadStatus.QUEUED,  # Download waiting
                5: DownloadStatus.QUEUED,  # Seed waiting
                0: DownloadStatus.PAUSED,  # Stopped
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Vuze"

    def _extract_hash_from_response(
        self, response: dict[str, Any], magnet_url: str | None = None
    ) -> str:
        """Extract hash from Vuze response.

        Parameters
        ----------
        response : dict[str, Any]
            Vuze API response.
        magnet_url : str | None
            Optional magnet URL for fallback extraction.

        Returns
        -------
        str
            Torrent hash.

        Raises
        ------
        PVRProviderError
            If hash cannot be extracted.
        """
        torrent = response.get("arguments", {}).get("torrent-added", {})
        if not torrent:
            torrent = response.get("arguments", {}).get("torrent-duplicate", {})

        hash_str = torrent.get("hashString", "")
        if not hash_str and magnet_url:
            # Extract hash from magnet link as fallback
            for part in magnet_url.split("&"):
                if "xt=urn:btih:" in part:
                    hash_str = part.split(":")[-1].upper()
                    break

        if not hash_str:
            msg = "Failed to get torrent hash from Vuze response"
            raise PVRProviderError(msg)

        return hash_str.upper()

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        path = download_path or self.settings.download_path
        response = self._proxy.add_torrent_from_url(magnet_url, download_dir=path)
        return self._extract_hash_from_response(response, magnet_url)

    def add_url(
        self,
        url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        path = download_path or self.settings.download_path
        response = self._proxy.add_torrent_from_url(url, download_dir=path)
        return self._extract_hash_from_response(response)

    def add_file(
        self,
        filepath: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        with pathlib.Path(filepath).open("rb") as f:
            file_content = f.read()
        path = download_path or self.settings.download_path
        response = self._proxy.add_torrent_from_file(file_content, download_dir=path)
        return self._extract_hash_from_response(response)

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
            torrents = self._proxy.get_torrents()

            items = []
            for torrent in torrents:
                # Map Vuze status to our status
                status_code = torrent.get("status", 0)
                status = self._status_mapper.map(status_code)

                # Calculate progress
                total_size = torrent.get("totalSize", 0)
                left_until_done = torrent.get("leftUntilDone", 0)
                progress = 1.0 - left_until_done / total_size if total_size > 0 else 0.0

                # Get download directory
                download_dir = torrent.get("downloadDir", "")
                torrent_name = torrent.get("name", "")

                # Vuze has similar behavior as uTorrent:
                # - A multi-file torrent is downloaded in a job folder
                # - A single-file torrent is downloaded in the root folder
                file_path = download_dir
                files = torrent.get("files", [])
                if len(files) > 1 or (files and files[0].get("name") == torrent_name):
                    # Multi-file torrent or file matches torrent name
                    file_path = download_dir
                elif torrent_name:
                    # Single-file torrent
                    file_path = (
                        f"{download_dir}/{torrent_name}"
                        if download_dir
                        else torrent_name
                    )

                # Calculate download speed (estimate from ETA)
                download_speed = None
                eta = torrent.get("eta", -1)
                if eta > 0 and left_until_done > 0:
                    download_speed = left_until_done / eta

                item: DownloadItem = {
                    "client_item_id": torrent.get("hashString", "").upper(),
                    "title": torrent_name,
                    "status": status,
                    "progress": progress,
                    "size_bytes": total_size,
                    "downloaded_bytes": total_size - left_until_done,
                    "download_speed_bytes_per_sec": download_speed,
                    "eta_seconds": eta if eta > 0 else None,
                    "file_path": file_path,
                }
                items.append(item)
        except Exception as e:
            msg = f"Failed to get downloads from Vuze: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Vuze.

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
            msg = "Vuze client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(
                client_item_id.lower(), delete_files=delete_files
            )
        except Exception as e:
            msg = f"Failed to remove download from Vuze: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Vuze.

        Returns
        -------
        bool
            True if connection test succeeds.

        Raises
        ------
        PVRProviderError
            If the connection test fails.
        """

        def _raise_version_error(version: str) -> None:
            """Raise error for unsupported version."""
            msg = f"Vuze protocol version {version} is too old (minimum: 14)"
            raise PVRProviderError(msg)

        try:
            version = self._proxy.get_protocol_version()
            version_int = int(version) if version.isdigit() else 0
            if version_int < 14:
                _raise_version_error(version)
            logger.debug("Vuze protocol version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to Vuze: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

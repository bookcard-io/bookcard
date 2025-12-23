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

"""Freebox Download client implementation.

Freebox Download is a download manager for Freebox routers.
This implementation supports adding downloads, monitoring downloads,
and managing downloads via Freebox API with HMAC-SHA1 authentication.

Documentation: https://dev.freebox.fr/sdk/os/download/
"""

import base64
import hashlib
import hmac
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
from bookcard.pvr.utils.status import DownloadStatus, StatusMapper

logger = logging.getLogger(__name__)


class FreeboxDownloadSettings(DownloadClientSettings):
    """Settings for Freebox Download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/api/v1/').
    api_url : str | None
        API URL path (default: '/api/v1/').
    app_id : str | None
        Freebox App ID.
    app_token : str | None
        Freebox App Token.
    """

    url_base: str | None = "/api/v1/"
    api_url: str | None = "/api/v1/"
    app_id: str | None = None
    app_token: str | None = None


class FreeboxDownloadProxy:
    """Low-level proxy for Freebox Download API.

    Handles HMAC-SHA1 authentication, request building, and API communication.
    """

    def __init__(self, settings: FreeboxDownloadSettings) -> None:
        """Initialize Freebox Download proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, None
        )
        api_url = settings.api_url or settings.url_base or "/api/v1/"
        self.api_url = urljoin(self.base_url.rstrip("/") + "/", api_url.lstrip("/"))
        self._session_token: str | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _get_challenge(self) -> str:
        """Get authentication challenge from Freebox API.

        Returns
        -------
        str
            Challenge string.

        Raises
        ------
        PVRProviderError
            If challenge request fails.
        """
        url = urljoin(self.api_url, "login")
        with self._get_client() as client:
            try:
                response = client.get(url, timeout=self.settings.timeout_seconds)
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    msg = "Failed to get Freebox challenge"
                    raise PVRProviderError(msg)

                return data.get("result", {}).get("challenge", "")

            except httpx.HTTPStatusError as e:
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "Freebox challenge")
                raise

    def _compute_password(self, challenge: str) -> str:
        """Compute password using HMAC-SHA1.

        Parameters
        ----------
        challenge : str
            Challenge string from API.

        Returns
        -------
        str
            Computed password (hex string).
        """
        if not self.settings.app_token:
            msg = "Freebox App Token is required"
            raise PVRProviderAuthenticationError(msg)

        hmac_obj = hmac.new(
            self.settings.app_token.encode("ascii"),
            challenge.encode("ascii"),
            hashlib.sha1,
        )
        return hmac_obj.hexdigest()

    def authenticate(self, force: bool = False) -> None:
        """Authenticate with Freebox API and get session token.

        Parameters
        ----------
        force : bool
            Force re-authentication.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        if not force and self._session_token is not None:
            return

        if not self.settings.app_id or not self.settings.app_token:
            msg = "Freebox App ID and App Token are required"
            raise PVRProviderAuthenticationError(msg)

        # Get challenge
        challenge = self._get_challenge()

        # Compute password
        password = self._compute_password(challenge)

        # Authenticate
        url = urljoin(self.api_url, "login/session")
        body = {
            "app_id": self.settings.app_id,
            "password": password,
        }

        with self._get_client() as client:
            try:
                response = client.post(
                    url,
                    json=body,
                    headers={"Content-Type": "application/json"},
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code in (401, 403):
                    msg = "Freebox authentication failed"
                    raise PVRProviderAuthenticationError(msg)

                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    error = data.get("error_code", "unknown")
                    msg = f"Freebox authentication failed: {error}"
                    raise PVRProviderAuthenticationError(msg)

                self._session_token = data.get("result", {}).get("session_token")
                if not self._session_token:
                    msg = "Freebox did not return session token"
                    raise PVRProviderAuthenticationError(msg)

                logger.debug("Freebox authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Freebox authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Freebox authentication")
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "Freebox authentication")
                raise

    def _execute_http_method(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP method request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        method : str
            HTTP method (GET, POST, PUT, DELETE).
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
                url, headers=headers, timeout=self.settings.timeout_seconds
            )
        if method_upper == "POST":
            return client.post(
                url,
                json=json_data,
                headers=headers,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "PUT":
            return client.put(
                url,
                json=json_data,
                headers=headers,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "DELETE":
            return client.delete(
                url, headers=headers, timeout=self.settings.timeout_seconds
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
            HTTP method (GET, POST, PUT, DELETE).
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
        self.authenticate()

        url = urljoin(self.api_url.rstrip("/") + "/", endpoint.lstrip("/"))
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Fbx-App-Auth": self._session_token or "",
        }

        with self._get_client() as client:
            try:
                response = self._execute_http_method(
                    client, method, url, headers, json_data
                )

                # Handle auth expiration
                if response.status_code in (401, 403):
                    logger.debug("Session expired, re-authenticating")
                    self.authenticate(force=True)
                    headers["X-Fbx-App-Auth"] = self._session_token or ""
                    response = self._execute_http_method(
                        client, method, url, headers, json_data
                    )

                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    error_code = data.get("error_code", "unknown")
                    msg = f"Freebox API error: {error_code}"
                    raise PVRProviderError(msg)

                return data.get("result", {})

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Freebox authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Freebox API {method} {endpoint}")
                raise

    def add_task_from_url(self, url: str, directory: str | None = None) -> str:
        """Add task from URL or magnet link.

        Parameters
        ----------
        url : str
            Torrent URL or magnet link.
        directory : str | None
            Optional download directory.

        Returns
        -------
        str
            Task ID.
        """
        body: dict[str, Any] = {"download_url": url}
        if directory:
            body["download_dir"] = directory

        response = self._request("POST", "downloads/add", json_data=body)
        return str(response.get("id", ""))

    def add_task_from_file(
        self, file_content: bytes, filename: str, directory: str | None = None
    ) -> str:
        """Add task from file.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        filename : str
            Torrent filename.
        directory : str | None
            Optional download directory.

        Returns
        -------
        str
            Task ID.
        """
        url = urljoin(self.api_url.rstrip("/") + "/", "downloads/add")
        self.authenticate()

        # Use multipart/form-data for file upload
        files = {"download_file": (filename, file_content, "application/x-bittorrent")}
        data: dict[str, Any] = {}
        if directory:
            data["download_dir"] = directory

        with self._get_client() as client:
            try:
                headers = {"X-Fbx-App-Auth": self._session_token or ""}
                response = client.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code in (401, 403):
                    logger.debug("Session expired, re-authenticating")
                    self.authenticate(force=True)
                    headers["X-Fbx-App-Auth"] = self._session_token or ""
                    response = client.post(
                        url,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=self.settings.timeout_seconds,
                    )

                response.raise_for_status()
                result = response.json()

                if not result.get("success", False):
                    error_code = result.get("error_code", "unknown")
                    msg = f"Freebox API error: {error_code}"
                    raise PVRProviderError(msg)

                return str(result.get("result", {}).get("id", ""))

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Freebox authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "Freebox API add file")
                raise

    def get_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks.

        Returns
        -------
        list[dict[str, Any]]
            List of task dictionaries.
        """
        response = self._request("GET", "downloads/")
        return response if isinstance(response, list) else []

    def delete_task(self, task_id: str, delete_data: bool = False) -> None:
        """Delete task.

        Parameters
        ----------
        task_id : str
            Task ID.
        delete_data : bool
            Whether to delete downloaded data.
        """
        endpoint = f"downloads/{task_id}"
        if delete_data:
            endpoint += "/erase"
        self._request("DELETE", endpoint)


class FreeboxDownloadClient(BaseDownloadClient):
    """Freebox Download client implementation.

    Implements BaseDownloadClient interface for Freebox Download API.
    """

    def __init__(
        self,
        settings: FreeboxDownloadSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize Freebox Download client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, FreeboxDownloadSettings
        ):
            settings = FreeboxDownloadSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/api/v1/",
                api_url="/api/v1/",
                app_id=None,
                app_token=None,
            )

        super().__init__(settings, enabled)
        self.settings: FreeboxDownloadSettings = settings  # type: ignore[assignment]
        self._proxy = FreeboxDownloadProxy(self.settings)
        self._status_mapper = StatusMapper(
            {
                "done": DownloadStatus.COMPLETED,
                "error": DownloadStatus.FAILED,
                "stopped": DownloadStatus.PAUSED,
                "queued": DownloadStatus.QUEUED,
                "downloading": DownloadStatus.DOWNLOADING,
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Freebox Download"

    def _add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        directory = download_path or self.settings.download_path
        return self._proxy.add_task_from_url(magnet_url, directory=directory)

    def _add_url(
        self,
        url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        directory = download_path or self.settings.download_path
        return self._proxy.add_task_from_url(url, directory=directory)

    def _add_file(
        self,
        filepath: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        filename = Path(filepath).name
        directory = download_path or self.settings.download_path
        return self._proxy.add_task_from_file(
            file_content, filename, directory=directory
        )

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
            tasks = self._proxy.get_tasks()

            items = []
            for task in tasks:
                task_id = str(task.get("id", ""))
                if not task_id:
                    continue

                # Map Freebox status to our status
                status_str = task.get("status", "unknown")
                status = self._status_mapper.map(status_str)

                # Calculate progress
                size = task.get("size", 0)
                received_bytes = task.get("rx_bytes", 0)
                received_pct = task.get("rx_pct", 0)
                progress = (
                    received_pct / 100.0
                    if received_pct > 0
                    else (received_bytes / size if size > 0 else 0.0)
                )
                if progress > 1.0:
                    progress = 1.0

                # Get download speed
                received_rate = task.get("rx_rate", 0)
                speed = int(received_rate) if received_rate > 0 else None

                # Get ETA
                eta = task.get("eta", -1)
                eta_seconds = int(eta) if eta > 0 else None

                # Get download directory (base64 encoded)
                download_dir = task.get("download_dir", "")
                file_path = ""
                if download_dir:
                    try:
                        file_path = base64.b64decode(download_dir).decode("utf-8")
                    except (ValueError, UnicodeDecodeError):
                        file_path = download_dir

                item: DownloadItem = {
                    "client_item_id": task_id,
                    "title": task.get("name", ""),
                    "status": status,
                    "progress": progress,
                    "size_bytes": int(size) if size > 0 else None,
                    "downloaded_bytes": int(received_bytes)
                    if received_bytes > 0
                    else None,
                    "download_speed_bytes_per_sec": speed,
                    "eta_seconds": eta_seconds,
                    "file_path": file_path,
                }
                items.append(item)

        except Exception as e:
            msg = f"Failed to get downloads from Freebox Download: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Freebox Download.

        Parameters
        ----------
        client_item_id : str
            Task ID.
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
            msg = "Freebox Download client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.delete_task(client_item_id, delete_files)
        except Exception as e:
            msg = f"Failed to remove download from Freebox Download: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Freebox Download.

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
            # Authenticate and verify API access
            self._proxy.authenticate()
            self._proxy.get_tasks()
        except Exception as e:
            msg = f"Failed to connect to Freebox Download: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_status_to_status(self, status_str: str) -> str:
        """Map Freebox status to standardized status.

        Parameters
        ----------
        status_str : str
            Freebox status string.

        Returns
        -------
        str
            Standardized status string.

        Notes
        -----
        Freebox status values:
        - stopped: Stopped
        - queued: Queued
        - starting: Starting
        - downloading: Downloading
        - stopping: Stopping
        - error: Error
        - done: Done
        - checking: Checking
        - repairing: Repairing
        - extracting: Extracting
        - seeding: Seeding
        - retry: Retry
        """
        status_lower = status_str.lower()
        # Completed states
        if status_lower == "done" or status_lower == "seeding":
            return "completed"

        # Downloading
        if status_lower == "downloading":
            return "downloading"

        # Paused/Stopped
        if status_lower in ("stopped", "stopping"):
            return "paused"

        # Error
        if status_lower == "error":
            return "failed"

        # Queued states
        if status_lower in (
            "queued",
            "starting",
            "checking",
            "repairing",
            "extracting",
            "retry",
        ):
            return "queued"

        # Default to queued
        return "queued"

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

"""SABnzbd download client implementation.

SABnzbd is a popular usenet client that uses a REST API with JSON responses.
This implementation supports adding NZB files, monitoring queue/history,
and managing downloads.

Documentation: https://sabnzbd.org/wiki/configuration/api
"""

import json
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
from bookcard.pvr.utils.status import DownloadStatus, StatusMapper

logger = logging.getLogger(__name__)


class SabnzbdSettings(DownloadClientSettings):
    """Settings for SABnzbd download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (e.g., '/sabnzbd').
    api_key : str | None
        API key for authentication (alternative to username/password).
    """

    url_base: str | None = None
    api_key: str | None = None


class SabnzbdProxy:
    """Low-level proxy for SABnzbd REST API.

    Handles authentication, request building, and API communication.
    Follows SRP by separating API communication from business logic.
    """

    def __init__(self, settings: SabnzbdSettings) -> None:
        """Initialize SABnzbd proxy.

        Parameters
        ----------
        settings : SabnzbdSettings
            SABnzbd client settings.
        """
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

    def _build_request_params(self, mode: str) -> dict[str, Any]:
        """Build request parameters for SABnzbd API.

        Parameters
        ----------
        mode : str
            API mode (e.g., 'queue', 'history', 'addfile').

        Returns
        -------
        dict[str, Any]
            Request parameters dictionary.
        """
        params: dict[str, Any] = {
            "mode": mode,
            "output": "json",
        }

        # Authentication: prefer API key, fallback to username/password
        if self.settings.api_key:
            params["apikey"] = self.settings.api_key
        elif self.settings.username and self.settings.password:
            params["ma_username"] = self.settings.username
            params["ma_password"] = self.settings.password
        else:
            msg = "SABnzbd requires either API key or username/password"
            raise PVRProviderAuthenticationError(msg)

        return params

    def _execute_request(
        self,
        client: httpx.Client,
        method: str,
        request_params: dict[str, Any],
        mode: str,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        method : str
            HTTP method (GET, POST).
        request_params : dict[str, Any]
            Request parameters.
        mode : str
            API mode.
        files : dict[str, Any] | None
            Files to upload.

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
            return client.get(self.api_url, params=request_params)
        if method_upper == "POST":
            if files:
                # For file uploads, use form data
                data = {k: v for k, v in request_params.items() if k != "mode"}
                return client.post(
                    self.api_url, params={"mode": mode}, data=data, files=files
                )
            return client.post(self.api_url, params=request_params)
        msg = f"Unsupported HTTP method: {method}"
        raise PVRProviderError(msg)

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON response and check for errors.

        Parameters
        ----------
        response : httpx.Response
            HTTP response.

        Returns
        -------
        dict[str, Any]
            Parsed JSON response.

        Raises
        ------
        PVRProviderError
            If parsing fails or response contains error.
        """
        # Parse JSON response
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            # SABnzbd sometimes returns plain text errors
            if response.text.strip().lower().startswith("error"):
                error_msg = response.text.strip()
                msg = f"SABnzbd API error: {error_msg}"
                raise PVRProviderError(msg) from e
            msg = f"Failed to parse SABnzbd response: {e}"
            raise PVRProviderError(msg) from e

        # Check for API errors in response
        if isinstance(result, dict):
            status = result.get("status", True)
            if status is False or (
                isinstance(status, str) and status.lower() == "false"
            ):
                error = result.get("error", "Unknown error")
                msg = f"SABnzbd API error: {error}"
                raise PVRProviderError(msg)

        return result

    def _request(
        self,
        method: str,
        mode: str,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST).
        mode : str
            API mode.
        params : dict[str, Any] | None
            Additional query parameters.
        files : dict[str, Any] | None
            Files to upload.

        Returns
        -------
        dict[str, Any]
            JSON response as dictionary.

        Raises
        ------
        PVRProviderError
            If request fails.
        """
        request_params = self._build_request_params(mode)
        if params:
            request_params.update(params)

        with self._get_client() as client:
            try:
                response = self._execute_request(
                    client, method, request_params, mode, files
                )
                response.raise_for_status()
                result = self._parse_response(response)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "SABnzbd authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"SABnzbd API {method} {mode}")
                raise
            else:
                return result

    def get_version(self) -> str:
        """Get SABnzbd version.

        Returns
        -------
        str
            Version string.
        """
        response = self._request("GET", "version")
        return response.get("version", "unknown")

    def add_nzb(
        self,
        nzb_data: bytes,
        filename: str,
        category: str | None = None,
        priority: int = 0,
    ) -> str:
        """Add NZB file to queue.

        Parameters
        ----------
        nzb_data : bytes
            NZB file content.
        filename : str
            NZB filename.
        category : str | None
            Optional category.
        priority : int
            Priority (0=default, 1=high, -1=low, -2=paused).

        Returns
        -------
        str
            Queue ID.
        """
        params: dict[str, Any] = {}
        if category:
            params["cat"] = category
        if priority != 0:
            params["priority"] = priority

        files = {"name": (filename, nzb_data, "application/x-nzb")}

        response = self._request("POST", "addfile", params=params, files=files)

        # Extract ID from response
        nzo_ids = response.get("nzo_ids", [])
        if nzo_ids:
            return str(nzo_ids[0])

        # Fallback: try to get ID from status
        status = response.get("status", "")
        if status:
            return status

        msg = "SABnzbd did not return a queue ID"
        raise PVRProviderError(msg)

    def get_queue(self, start: int = 0, limit: int = 0) -> list[dict[str, Any]]:
        """Get queue items.

        Parameters
        ----------
        start : int
            Start index (default: 0).
        limit : int
            Limit results (0 = all, default: 0).

        Returns
        -------
        list[dict[str, Any]]
            List of queue items.
        """
        params: dict[str, Any] = {}
        if start > 0:
            params["start"] = start
        if limit > 0:
            params["limit"] = limit

        response = self._request("GET", "queue", params=params)
        queue_data = response.get("queue", {})
        return queue_data.get("slots", [])

    def get_history(self, start: int = 0, limit: int = 0) -> list[dict[str, Any]]:
        """Get history items.

        Parameters
        ----------
        start : int
            Start index (default: 0).
        limit : int
            Limit results (0 = all, default: 0).

        Returns
        -------
        list[dict[str, Any]]
            List of history items.
        """
        params: dict[str, Any] = {}
        if start > 0:
            params["start"] = start
        if limit > 0:
            params["limit"] = limit

        response = self._request("GET", "history", params=params)
        history_data = response.get("history", {})
        return history_data.get("slots", [])

    def remove_from_queue(self, nzo_id: str, delete_files: bool = False) -> None:
        """Remove item from queue.

        Parameters
        ----------
        nzo_id : str
            Queue item ID.
        delete_files : bool
            Whether to delete downloaded files.
        """
        params: dict[str, Any] = {
            "name": "delete",
            "value": nzo_id,
            "del_files": 1 if delete_files else 0,
        }
        self._request("GET", "queue", params=params)

    def remove_from_history(
        self, nzo_id: str, delete_files: bool = False, delete_permanently: bool = False
    ) -> None:
        """Remove item from history.

        Parameters
        ----------
        nzo_id : str
            History item ID.
        delete_files : bool
            Whether to delete downloaded files.
        delete_permanently : bool
            Whether to permanently delete (not archive).
        """
        params: dict[str, Any] = {
            "name": "delete",
            "value": nzo_id,
            "del_files": 1 if delete_files else 0,
            "archive": 0 if delete_permanently else 1,
        }
        self._request("GET", "history", params=params)


class SabnzbdClient(BaseDownloadClient):
    """SABnzbd download client implementation.

    Implements BaseDownloadClient interface for SABnzbd REST API.
    """

    def __init__(
        self,
        settings: SabnzbdSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize SABnzbd client.

        Parameters
        ----------
        settings : SabnzbdSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to SabnzbdSettings.
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
            settings, SabnzbdSettings
        ):
            sab_settings = SabnzbdSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base=None,
                api_key=None,
            )
            settings = sab_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: SabnzbdSettings = settings
        self._proxy: SabnzbdProxy = SabnzbdProxy(self.settings)
        self._status_mapper = StatusMapper(
            {
                # Queue statuses
                "Paused": DownloadStatus.PAUSED,
                "paused": DownloadStatus.PAUSED,
                "Queued": DownloadStatus.QUEUED,
                "queued": DownloadStatus.QUEUED,
                "Grabbing": DownloadStatus.QUEUED,
                "grabbing": DownloadStatus.QUEUED,
                # History statuses
                "Completed": DownloadStatus.COMPLETED,
                "completed": DownloadStatus.COMPLETED,
                "Failed": DownloadStatus.FAILED,
                "failed": DownloadStatus.FAILED,
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "SABnzbd"

    def add_magnet(
        self,
        _magnet_url: str,
        _title: str | None,
        _category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from magnet link (not supported by SABnzbd)."""
        msg = "SABnzbd does not support magnet links"
        raise PVRProviderError(msg)

    def add_url(
        self,
        url: str,
        title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        nzb_data, filename = self._file_fetcher.fetch_with_filename(
            url, title or "download.nzb"
        )
        cat = category or self.settings.category
        return self._proxy.add_nzb(nzb_data, filename, category=cat)

    def add_file(
        self,
        filepath: str,
        title: str | None,
        category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from local file."""
        nzb_data = Path(filepath).read_bytes()
        filename = title or Path(filepath).name
        cat = category or self.settings.category
        return self._proxy.add_nzb(nzb_data, filename, category=cat)

    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads from queue and history.

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
            items = []

            # Get queue items
            queue_items = self._proxy.get_queue()
            for item in queue_items:
                status = item.get("status", "")
                nzo_id = item.get("nzo_id", "")

                # Map SABnzbd status to our status
                item_status = self._map_sabnzbd_status(status, is_queue=True)

                # Calculate progress
                mb = item.get("mb", 0.0)
                mbleft = item.get("mbleft", 0.0)
                total_bytes = int(mb * 1024 * 1024) if mb else None
                remaining_bytes = int(mbleft * 1024 * 1024) if mbleft else None

                progress = 0.0
                if total_bytes and total_bytes > 0:
                    downloaded = total_bytes - (remaining_bytes or 0)
                    progress = downloaded / total_bytes
                    if progress > 1.0:
                        progress = 1.0

                # Get ETA
                timeleft = item.get("timeleft", "")
                eta_seconds = None
                if timeleft and isinstance(timeleft, (int, float)):
                    eta_seconds = int(timeleft)

                download_item: DownloadItem = {
                    "client_item_id": str(nzo_id),
                    "title": item.get("filename", ""),
                    "status": item_status,
                    "progress": progress,
                    "size_bytes": total_bytes,
                    "downloaded_bytes": total_bytes - remaining_bytes
                    if total_bytes and remaining_bytes
                    else None,
                    "download_speed_bytes_per_sec": None,  # SABnzbd doesn't provide this directly
                    "eta_seconds": eta_seconds,
                    "file_path": None,  # Will be available in history
                }
                items.append(download_item)

            # Get history items (recently completed)
            history_items = self._proxy.get_history(limit=50)
            for item in history_items:
                status = item.get("status", "")
                nzo_id = item.get("nzo_id", "")

                # Only include completed/failed items
                if status not in ("Completed", "Failed"):
                    continue

                item_status = self._map_sabnzbd_status(status, is_queue=False)

                storage = item.get("storage", "")
                mb = item.get("mb", 0.0)
                total_bytes = int(mb * 1024 * 1024) if mb else None

                history_item: DownloadItem = {
                    "client_item_id": str(nzo_id),
                    "title": item.get("name", ""),
                    "status": item_status,
                    "progress": 1.0 if item_status == DownloadStatus.COMPLETED else 0.0,
                    "size_bytes": total_bytes,
                    "downloaded_bytes": total_bytes,
                    "download_speed_bytes_per_sec": None,
                    "eta_seconds": None,
                    "file_path": storage if storage else None,
                }
                items.append(history_item)
        except Exception as e:
            msg = f"Failed to get downloads from SABnzbd: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from SABnzbd.

        Parameters
        ----------
        client_item_id : str
            Queue/History item ID.
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
            msg = "SABnzbd client is disabled"
            raise PVRProviderError(msg)

        try:
            # Try queue first, then history
            try:
                self._proxy.remove_from_queue(client_item_id, delete_files=delete_files)
            except PVRProviderError:
                # Not in queue, try history
                self._proxy.remove_from_history(
                    client_item_id, delete_files=delete_files, delete_permanently=True
                )
        except Exception as e:
            msg = f"Failed to remove download from SABnzbd: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to SABnzbd.

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
            logger.debug("SABnzbd version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to SABnzbd: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _map_sabnzbd_status(self, status: str, is_queue: bool) -> str:
        """Map SABnzbd status to standardized status.

        Parameters
        ----------
        status : str
            SABnzbd status string.
        is_queue : bool
            Whether this is a queue item (True) or history item (False).

        Returns
        -------
        str
            Standardized status string.
        """
        if is_queue:
            # Queue statuses
            if status in ("Paused", "paused"):
                return DownloadStatus.PAUSED
            if status in ("Queued", "queued", "Grabbing", "grabbing"):
                return DownloadStatus.QUEUED
            return DownloadStatus.DOWNLOADING
        # History statuses
        if status in ("Completed", "completed"):
            return DownloadStatus.COMPLETED
        if status in ("Failed", "failed"):
            return DownloadStatus.FAILED
        return DownloadStatus.DOWNLOADING

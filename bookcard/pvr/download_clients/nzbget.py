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

"""NZBGet download client implementation.

NZBGet is a usenet client that uses XML-RPC API (JSON-RPC in newer versions).
This implementation supports adding NZB files, monitoring queue/history,
and managing downloads.

Documentation: https://nzbget.net/RPC_API
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


class NzbgetSettings(DownloadClientSettings):
    """Settings for NZBGet download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    """

    url_base: str | None = None


class NzbgetProxy:
    """Low-level proxy for NZBGet JSON-RPC API.

    Handles authentication, JSON-RPC request building, and API communication.
    """

    def __init__(self, settings: NzbgetSettings) -> None:
        """Initialize NZBGet proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = urljoin(self.base_url.rstrip("/") + "/", "jsonrpc")

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _request(
        self, method: str, *args: str | float | bool | dict[str, Any] | list[Any] | None
    ) -> str | int | float | bool | dict[str, Any] | list[Any] | None:
        """Make JSON-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *args : Any
            Method arguments.

        Returns
        -------
        Any
            RPC response result.
        """
        # Build JSON-RPC request
        rpc_request: dict[str, Any] = {
            "method": method,
            "params": list(args),
            "id": 1,
        }

        # Build auth header
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.username and self.settings.password:
            credentials = f"{self.settings.username}:{self.settings.password}"
            auth_bytes = base64.b64encode(credentials.encode("utf-8"))
            headers["Authorization"] = f"Basic {auth_bytes.decode('utf-8')}"

        with self._get_client() as client:
            try:
                response = client.post(
                    self.rpc_url,
                    headers=headers,
                    json=rpc_request,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code == 401:
                    msg = "NZBGet authentication failed: invalid credentials"
                    raise PVRProviderAuthenticationError(msg)

                response.raise_for_status()

                # Parse JSON-RPC response
                rpc_response = response.json()

                # Check for RPC errors
                if "error" in rpc_response:
                    error = rpc_response["error"]
                    error_msg = error.get("message", "Unknown error")
                    msg = f"NZBGet RPC error: {error_msg}"
                    raise PVRProviderError(msg)

                return rpc_response.get("result")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "NZBGet authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"NZBGet RPC {method}")
                raise

    def get_version(self) -> str:
        """Get NZBGet version."""
        return str(self._request("version"))

    def append_nzb(
        self,
        nzb_data: bytes,
        filename: str,
        category: str | None = None,
        priority: int = 0,
        add_paused: bool = False,
    ) -> int:
        """Append NZB to queue.

        Parameters
        ----------
        nzb_data : bytes
            NZB file content.
        filename : str
            NZB filename.
        category : str | None
            Optional category.
        priority : int
            Priority (0=normal, positive=higher, negative=lower).
        add_paused : bool
            Whether to add in paused state.

        Returns
        -------
        int
            NZB ID.
        """
        # Encode NZB data as base64
        nzb_base64 = base64.b64encode(nzb_data).decode("utf-8")

        # Build parameters
        params: list[Any] = [
            filename,
            nzb_base64,
            category or "",
            priority,
            False,
            add_paused,
            "",
            0,
            "all",
        ]

        # For NZBGet 16+, we can add custom parameters
        # Add a "drone" parameter to track downloads
        import uuid

        drone_id = str(uuid.uuid4()).replace("-", "")
        params.append(["drone", drone_id])

        nzb_id = self._request("append", *params)

        if not nzb_id or (isinstance(nzb_id, (int, float)) and nzb_id <= 0):
            msg = "NZBGet failed to add NZB"
            raise PVRProviderError(msg)

        return int(nzb_id)

    def get_queue(self) -> list[dict[str, Any]]:
        """Get queue items.

        Returns
        -------
        list[dict[str, Any]]
            List of queue items.
        """
        result = self._request("listgroups")
        if isinstance(result, list):
            return result
        return []

    def get_history(self) -> list[dict[str, Any]]:
        """Get history items.

        Returns
        -------
        list[dict[str, Any]]
            List of history items.
        """
        result = self._request("history")
        if isinstance(result, list):
            return result
        return []

    def get_global_status(self) -> dict[str, Any]:
        """Get global status.

        Returns
        -------
        dict[str, Any]
            Global status dictionary.
        """
        result = self._request("status")
        if isinstance(result, dict):
            return result
        return {}

    def edit_queue(
        self, command: str, offset: int, edit_text: str, nzb_id: int
    ) -> bool:
        """Edit queue item.

        Parameters
        ----------
        command : str
            Command (e.g., 'GroupFinalDelete', 'GroupPause', 'GroupResume').
        offset : int
            Offset (usually 0).
        edit_text : str
            Edit text (usually empty).
        nzb_id : int
            NZB ID.

        Returns
        -------
        bool
            True if successful.
        """
        return bool(self._request("editqueue", command, offset, edit_text, nzb_id))

    def remove_item(self, nzb_id: int) -> None:
        """Remove item from queue.

        Parameters
        ----------
        nzb_id : int
            NZB ID.
        """
        self.edit_queue("GroupFinalDelete", 0, "", nzb_id)


class NzbgetClient(BaseDownloadClient):
    """NZBGet download client implementation.

    Implements BaseDownloadClient interface for NZBGet JSON-RPC API.
    """

    def __init__(
        self,
        settings: NzbgetSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize NZBGet client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, NzbgetSettings
        ):
            nzbget_settings = NzbgetSettings(
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
            settings = nzbget_settings

        super().__init__(settings, enabled)
        self.settings: NzbgetSettings = settings  # type: ignore[assignment]
        self._proxy = NzbgetProxy(self.settings)

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,
        _download_path: str | None = None,
    ) -> str:
        """Add a download to NZBGet.

        Parameters
        ----------
        download_url : str
            URL or file path to NZB file.
        title : str | None
            Optional title.
        category : str | None
            Optional category.
        download_path : str | None
            Optional download path (not used by NZBGet).

        Returns
        -------
        str
            NZB ID as string.

        Raises
        ------
        PVRProviderError
            If adding the download fails.
        """
        if not self.is_enabled():
            msg = "NZBGet client is disabled"
            raise PVRProviderError(msg)

        def _raise_invalid_url_error() -> None:
            """Raise error for invalid download URL."""
            msg = f"Invalid download URL: {download_url}"
            raise PVRProviderError(msg)

        try:
            # Use category from settings if not provided
            cat = category or self.settings.category

            # Get NZB file content
            if download_url.startswith("http"):
                import httpx

                with httpx.Client() as client:
                    response = client.get(download_url, timeout=30)
                    response.raise_for_status()
                    nzb_data = response.content
                    filename = title or download_url.split("/")[-1] or "download.nzb"
            elif Path(download_url).is_file():
                nzb_data = Path(download_url).read_bytes()
                filename = title or Path(download_url).name
            else:
                _raise_invalid_url_error()

            # Add to NZBGet
            nzb_id = self._proxy.append_nzb(nzb_data, filename, category=cat)
            return str(nzb_id)

        except Exception as e:
            msg = f"Failed to add download to NZBGet: {e}"
            raise PVRProviderError(msg) from e

    def get_items(self) -> Sequence[dict[str, str | int | float | None]]:
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
            global_status = self._proxy.get_global_status()

            # Get queue items
            queue_items = self._proxy.get_queue()
            for item in queue_items:
                nzb_id = item.get("NZBID", 0)
                status = item.get("Status", "")

                # Map NZBGet status to our status
                item_status = self._map_status_to_status(status, is_queue=True)

                # Calculate progress from file sizes
                file_size_hi = item.get("FileSizeHi", 0)
                file_size_lo = item.get("FileSizeLo", 0)
                remaining_size_hi = item.get("RemainingSizeHi", 0)
                remaining_size_lo = item.get("RemainingSizeLo", 0)

                total_bytes = self._make_int64(file_size_hi, file_size_lo)
                remaining_bytes = self._make_int64(remaining_size_hi, remaining_size_lo)

                progress = 0.0
                if total_bytes and total_bytes > 0:
                    remaining = remaining_bytes if remaining_bytes is not None else 0
                    downloaded = total_bytes - remaining
                    progress = downloaded / total_bytes
                    if progress > 1.0:
                        progress = 1.0

                # Calculate ETA from download rate
                download_rate = global_status.get("DownloadRate", 0)
                eta_seconds = None
                if (
                    download_rate
                    and download_rate > 0
                    and remaining_bytes is not None
                    and remaining_bytes > 0
                ):
                    eta_seconds = int(remaining_bytes / download_rate)

                download_item = {
                    "client_item_id": str(nzb_id),
                    "title": item.get("NZBName", ""),
                    "status": item_status,
                    "progress": progress,
                    "size_bytes": total_bytes,
                    "downloaded_bytes": (
                        total_bytes
                        - (remaining_bytes if remaining_bytes is not None else 0)
                        if total_bytes
                        else None
                    ),
                    "download_speed_bytes_per_sec": (
                        download_rate if download_rate and download_rate > 0 else None
                    ),
                    "eta_seconds": eta_seconds,
                    "file_path": None,  # Will be available in history
                }
                items.append(download_item)

            # Get history items (recently completed)
            history_items = self._proxy.get_history()
            for item in history_items[:50]:  # Limit to recent 50
                nzb_id = item.get("ID", 0)
                status = item.get("Status", "")

                # Only include completed/failed items
                if status not in ("SUCCESS", "FAILURE", "BAD"):
                    continue

                item_status = self._map_status_to_status(status, is_queue=False)

                file_size_hi = item.get("FileSizeHi", 0)
                file_size_lo = item.get("FileSizeLo", 0)
                total_bytes = self._make_int64(file_size_hi, file_size_lo)

                final_dir = item.get("FinalDir", "")
                dest_dir = item.get("DestDir", "")
                file_path = final_dir if final_dir else dest_dir

                history_item = {
                    "client_item_id": str(nzb_id),
                    "title": item.get("Name", ""),
                    "status": item_status,
                    "progress": 1.0 if item_status == "completed" else 0.0,
                    "size_bytes": total_bytes,
                    "downloaded_bytes": total_bytes,
                    "download_speed_bytes_per_sec": None,
                    "eta_seconds": None,
                    "file_path": file_path if file_path else None,
                }
                items.append(history_item)
        except Exception as e:
            msg = f"Failed to get downloads from NZBGet: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, _delete_files: bool = False) -> bool:
        """Remove a download from NZBGet.

        Parameters
        ----------
        client_item_id : str
            NZB ID.
        delete_files : bool
            Whether to delete downloaded files (not directly supported).

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
            msg = "NZBGet client is disabled"
            raise PVRProviderError(msg)

        try:
            nzb_id = int(client_item_id)
            self._proxy.remove_item(nzb_id)
        except Exception as e:
            msg = f"Failed to remove download from NZBGet: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to NZBGet.

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
            logger.debug("NZBGet version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to NZBGet: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _make_int64(self, hi: int, lo: int) -> int | None:
        """Combine high and low 32-bit integers into 64-bit integer.

        Parameters
        ----------
        hi : int
            High 32 bits.
        lo : int
            Low 32 bits.

        Returns
        -------
        int | None
            Combined 64-bit integer or None if invalid.
        """
        if hi is None or lo is None:
            return None
        return (hi << 32) | (lo & 0xFFFFFFFF)

    def _map_status_to_status(self, status: str, is_queue: bool) -> str:
        """Map NZBGet status to standardized status.

        Parameters
        ----------
        status : str
            NZBGet status string.
        is_queue : bool
            Whether this is a queue item (True) or history item (False).

        Returns
        -------
        str
            Standardized status string.
        """
        if is_queue:
            # Queue statuses
            if "PAUSED" in status.upper():
                return "paused"
            if "QUEUED" in status.upper() or "FETCHING" in status.upper():
                return "queued"
            return "downloading"
        # History statuses
        if status == "SUCCESS":
            return "completed"
        if status in ("FAILURE", "BAD"):
            return "failed"
        return "downloading"

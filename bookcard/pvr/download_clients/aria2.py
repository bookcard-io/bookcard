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

"""Aria2 download client implementation.

Aria2 is a lightweight multi-protocol download utility that uses XML-RPC API.
This implementation supports adding torrents, monitoring downloads,
and managing torrents.

Documentation: https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface
"""

import logging
from collections.abc import Callable, Sequence
from contextlib import suppress
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

import httpx

from bookcard.pvr.base import (
    DownloadClientSettings,
    TrackingDownloadClient,
)
from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.download_clients._http_client import (
    build_base_url,
    handle_httpx_exception,
)
from bookcard.pvr.error_handlers import handle_http_error_response
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
)
from bookcard.pvr.models import DownloadItem
from bookcard.pvr.utils.status import DownloadStatus, StatusMapper
from bookcard.pvr.utils.xmlrpc import XmlRpcBuilder, XmlRpcParser, XmlRpcValue

logger = logging.getLogger(__name__)


class Aria2Settings(DownloadClientSettings):
    """Settings for Aria2 download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/jsonrpc').
    secret : str | None
        RPC secret token for authentication.
    """

    url_base: str | None = "/jsonrpc"
    secret: str | None = None


class Aria2Proxy:
    """Low-level proxy for Aria2 XML-RPC API.

    Handles XML-RPC request building and API communication.
    """

    def __init__(
        self,
        settings: Aria2Settings,
        http_client_factory: Callable[[], HttpClientProtocol],
    ) -> None:
        """Initialize Aria2 proxy."""
        self.settings = settings
        self.http_client_factory = http_client_factory
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = self.base_url.rstrip("/")
        self.builder = XmlRpcBuilder()
        self.parser = XmlRpcParser()

    def _get_token(self) -> str:
        """Get RPC token (secret).

        Returns
        -------
        str
            RPC token.
        """
        if self.settings.secret:
            return f"token:{self.settings.secret}"
        return ""

    def _raise_auth_error(self) -> None:
        """Raise authentication error.

        Raises
        ------
        PVRProviderAuthenticationError
            Always raises with authentication error message.
        """
        auth_error_msg = "Aria2 authentication failed"
        raise PVRProviderAuthenticationError(auth_error_msg)

    def _prepare_request(
        self, method: str, *params: XmlRpcValue
    ) -> tuple[str, dict[str, str], tuple[str, str] | None]:
        """Prepare XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : XmlRpcValue
            Method parameters.

        Returns
        -------
        tuple[str, dict[str, str], tuple[str, str] | None]
            Tuple of (xml_request, headers, auth).
        """
        token = self._get_token()
        xml_request = self.builder.build_request(
            method, *params, rpc_token=token if token else None
        )

        headers: dict[str, str] = {
            "Content-Type": "text/xml",
            "Content-Length": str(len(xml_request)),
        }

        auth = None
        if self.settings.username and self.settings.password:
            auth = (self.settings.username, self.settings.password)

        return xml_request, headers, auth

    def _parse_response(
        self, response_text: str
    ) -> (
        str
        | int
        | list[str | int | dict[str, str | int | None]]
        | dict[str, str | int | None]
        | None
    ):
        """Parse XML-RPC response.

        Parameters
        ----------
        response_text : str
            XML response text.

        Returns
        -------
        str | int | list[str | int | dict[str, str | int | None]] | dict[str, str | int | None] | None
            Parsed response result.

        Raises
        ------
        PVRProviderError
            If parsing fails.
        """
        try:
            return self.parser.parse_response(response_text)
        except ET.ParseError as e:
            msg = f"Failed to parse Aria2 XML-RPC response: {e}"
            raise PVRProviderError(msg) from e

    def _handle_request_exceptions(
        self, error: httpx.HTTPError | PVRProviderError, method: str
    ) -> None:
        """Handle exceptions from XML-RPC request.

        Parameters
        ----------
        error : httpx.HTTPError | PVRProviderError
            The exception to handle.
        method : str
            RPC method name for error context.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication failed.
        PVRProviderError
            For other errors.
        """
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code in (401, 403):
                auth_error_msg = "Aria2 authentication failed"
                raise PVRProviderAuthenticationError(auth_error_msg) from error
            handle_http_error_response(
                error.response.status_code, error.response.text[:200]
            )
        elif isinstance(error, (httpx.RequestError, httpx.TimeoutException)):
            handle_httpx_exception(error, f"Aria2 XML-RPC {method}")
        elif isinstance(error, PVRProviderError):
            raise

    def _request(
        self,
        method: str,
        *params: XmlRpcValue,
    ) -> (
        str
        | int
        | list[str | int | dict[str, str | int | None]]
        | dict[str, str | int | None]
        | None
    ):
        """Make XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : XmlRpcValue
            Method parameters.

        Returns
        -------
        str | int | list[str | int | dict[str, str | int | None]] | dict[str, str | int | None] | None
            RPC response result.
        """
        xml_request, headers, auth = self._prepare_request(method, *params)

        with self.http_client_factory() as client:
            try:
                response = client.post(
                    self.rpc_url,
                    content=xml_request,
                    headers=headers,
                    auth=auth,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code == 401:
                    self._raise_auth_error()

                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()

                return self._parse_response(response.text)

            except (httpx.HTTPError, PVRProviderError) as e:
                self._handle_request_exceptions(e, method)
            except Exception as e:
                # Defensive fallback for unexpected exceptions from underlying calls
                # (e.g., AttributeError from response.text, etc.)
                msg = f"Aria2 request failed: {e}"
                raise PVRProviderError(msg) from e

    def get_version(self) -> str:
        """Get Aria2 version."""
        result = self._request("aria2.getVersion")
        if isinstance(result, dict):
            return str(result.get("version", "unknown"))
        return str(result) if result else "unknown"

    def add_magnet(
        self, magnet_link: str, options: dict[str, str | int | None] | None = None
    ) -> str:
        """Add magnet link.

        Parameters
        ----------
        magnet_link : str
            Magnet link.
        options : dict[str, str | int | None] | None
            Optional download options.

        Returns
        -------
        str
            GID (download identifier).
        """
        if options is None:
            options = {}

        uris = [magnet_link]
        result = self._request("aria2.addUri", uris, options)  # type: ignore[arg-type]
        return str(result) if result else ""

    def add_torrent(
        self, file_content: bytes, options: dict[str, str | int | None] | None = None
    ) -> str:
        """Add torrent file.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        options : dict[str, str | int | None] | None
            Optional download options.

        Returns
        -------
        str
            GID (download identifier).
        """
        if options is None:
            options = {}

        # Aria2 requires empty URI list when options are provided
        uris: list[str | int] = []
        result = self._request("aria2.addTorrent", file_content, uris, options)  # type: ignore[arg-type]
        return str(result) if result else ""

    def get_torrents(self) -> list[dict[str, str | int | None]]:
        """Get all active, waiting, and stopped downloads.

        Returns
        -------
        list[dict[str, Any]]
            List of download dictionaries.
        """
        active = self._request("aria2.tellActive") or []
        waiting = self._request("aria2.tellWaiting", 0, 10240) or []
        stopped = self._request("aria2.tellStopped", 0, 10240) or []

        items: list[dict[str, str | int | None]] = []
        # Ensure we only append lists (API should return lists)
        if isinstance(active, list):
            items.extend(active)  # type: ignore[arg-type]
        if isinstance(waiting, list):
            items.extend(waiting)  # type: ignore[arg-type]
        if isinstance(stopped, list):
            items.extend(stopped)  # type: ignore[arg-type]

        # Type narrowing for mypy/safety
        # The parser returns list[str | int | dict] but we expect dicts here
        return [item for item in items if isinstance(item, dict)]

    def remove_torrent(self, gid: str, force: bool = False) -> bool:
        """Remove download.

        Parameters
        ----------
        gid : str
            Download GID.
        force : bool
            Whether to force remove.

        Returns
        -------
        bool
            True if successful.
        """
        method = "aria2.forceRemove" if force else "aria2.remove"
        result = self._request(method, gid)
        return str(result) == gid

    def remove_completed(self, gid: str) -> bool:
        """Remove completed download from history.

        Parameters
        ----------
        gid : str
            Download GID.

        Returns
        -------
        bool
            True if successful.
        """
        result = self._request("aria2.removeDownloadResult", gid)
        return str(result) == "OK"


class Aria2Client(TrackingDownloadClient):
    """Aria2 download client implementation.

    Implements BaseDownloadClient interface for Aria2 XML-RPC API.
    """

    def __init__(
        self,
        settings: Aria2Settings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize Aria2 client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, Aria2Settings
        ):
            aria2_settings = Aria2Settings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/jsonrpc",
                secret=None,
            )
            settings = aria2_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: Aria2Settings = settings

        if self._http_client_factory is None:
            # Fallback if not injected (though factory should always inject)
            from bookcard.pvr.download_clients._http_client import create_httpx_client

            self._http_client_factory = lambda: create_httpx_client(
                timeout=self.settings.timeout_seconds
            )

        self._proxy = Aria2Proxy(self.settings, self._http_client_factory)
        self._status_mapper = StatusMapper(
            {
                "complete": DownloadStatus.COMPLETED,
                "error": DownloadStatus.FAILED,
                "paused": DownloadStatus.PAUSED,
                "waiting": DownloadStatus.QUEUED,
                "active": DownloadStatus.DOWNLOADING,
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Aria2"

    def _calculate_progress(
        self, total_length: str | int | None, completed_length: str | int | None
    ) -> float:
        """Calculate download progress.

        Parameters
        ----------
        total_length : str | int | None
            Total length.
        completed_length : str | int | None
            Completed length.

        Returns
        -------
        float
            Progress as a float between 0.0 and 1.0.
        """
        try:
            total = int(total_length) if total_length else 0
            completed = int(completed_length) if completed_length else 0
        except (ValueError, TypeError):
            total = 0
            completed = 0

        if total > 0:
            progress = completed / total
            return min(progress, 1.0)
        return 0.0

    def _get_download_speed(self, download: dict[str, str | int | None]) -> int | None:
        """Get download speed from download dict.

        Parameters
        ----------
        download : dict[str, str | int | None]
            Download dictionary.

        Returns
        -------
        int | None
            Download speed in bytes per second, or None.
        """
        download_speed = download.get("downloadSpeed", "0")
        speed = None
        with suppress(ValueError, TypeError):
            if download_speed:
                speed = int(str(download_speed))
        return speed

    def _get_eta(self, download: dict[str, str | int | None]) -> int | None:
        """Get ETA from download dict.

        Parameters
        ----------
        download : dict[str, str | int | None]
            Download dictionary.

        Returns
        -------
        int | None
            ETA in seconds, or None.
        """
        eta = download.get("eta", "")
        eta_seconds = None
        if eta:
            with suppress(ValueError, TypeError):
                eta_seconds = int(str(eta))
        return eta_seconds

    def _get_download_title(self, download: dict[str, str | int | None]) -> str:
        """Get download title from download dict.

        Parameters
        ----------
        download : dict[str, str | int | None]
            Download dictionary.

        Returns
        -------
        str
            Download title.
        """
        bittorrent = download.get("bittorrent")
        if isinstance(bittorrent, dict):
            info = bittorrent.get("info")
            if isinstance(info, dict):
                name = info.get("name", "")
                if isinstance(name, str) and name:
                    return name

        files = download.get("files")
        if isinstance(files, list) and len(files) > 0:
            first_file = files[0]
            if isinstance(first_file, dict):
                path = first_file.get("path", "")
                if isinstance(path, str) and path:
                    return path.split("/")[-1]

        return ""

    def _build_download_item(
        self, download: dict[str, str | int | None]
    ) -> DownloadItem:
        """Build download item dict from download data.

        Parameters
        ----------
        download : dict[str, str | int | None]
            Download dictionary from Aria2.

        Returns
        -------
        DownloadItem
            Formatted download item.
        """
        gid = download.get("gid", "")
        status = download.get("status", "")
        item_status = self._status_mapper.map(str(status) if status else "")

        total_length = download.get("totalLength", "0")
        completed_length = download.get("completedLength", "0")
        progress = self._calculate_progress(total_length, completed_length)

        try:
            total = int(str(total_length)) if total_length else 0
            completed = int(str(completed_length)) if completed_length else 0
        except (ValueError, TypeError):
            total = 0
            completed = 0

        speed = self._get_download_speed(download)
        eta_seconds = self._get_eta(download)
        title = self._get_download_title(download)

        item: DownloadItem = {
            "client_item_id": str(gid),
            "title": title,
            "status": item_status,
            "progress": progress,
            "size_bytes": total if total > 0 else None,
            "downloaded_bytes": completed if completed > 0 else None,
            "download_speed_bytes_per_sec": speed,
            "eta_seconds": eta_seconds,
            "file_path": str(download.get("dir", "")) if download.get("dir") else None,
        }
        return item

    def _build_options(self, download_path: str | None) -> dict[str, str | int | None]:
        """Build Aria2 options dictionary.

        Parameters
        ----------
        download_path : str | None
            Download path.

        Returns
        -------
        dict[str, str | int | None]
            Options dictionary.
        """
        options: dict[str, str | int | None] = {}
        path = download_path or self.settings.download_path
        if path:
            options["dir"] = path
        return options

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        options = self._build_options(download_path)
        return self._proxy.add_magnet(magnet_url, options)

    def add_url(
        self,
        url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        # Aria2 can download directly from URL
        options = self._build_options(download_path)
        return self._proxy.add_magnet(url, options)

    def add_file(
        self,
        filepath: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        options = self._build_options(download_path)
        return self._proxy.add_torrent(file_content, options)

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
            downloads = self._proxy.get_torrents()

            items = []
            for download in downloads:
                gid = download.get("gid", "")
                if not gid:
                    continue

                item = self._build_download_item(download)
                items.append(item)

        except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            get_error_msg = f"Failed to get downloads from Aria2: {e}"
            raise PVRProviderError(get_error_msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from Aria2.

        Parameters
        ----------
        client_item_id : str
            Download GID.
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
            msg = "Aria2 client is disabled"
            raise PVRProviderError(msg)

        try:
            result = self._proxy.remove_torrent(client_item_id, force=delete_files)
        except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            remove_error_msg = f"Failed to remove download from Aria2: {e}"
            raise PVRProviderError(remove_error_msg) from e
        else:
            return result

    def test_connection(self) -> bool:
        """Test connectivity to Aria2.

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
            logger.debug("Aria2 version: %s", version)
        except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            connect_error_msg = f"Failed to connect to Aria2: {e}"
            raise PVRProviderError(connect_error_msg) from e
        else:
            return True

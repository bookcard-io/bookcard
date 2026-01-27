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

"""Synology Download Station client implementation.

Download Station is Synology's download manager that supports
both torrent and usenet downloads via Synology's WebAPI.
This implementation supports adding downloads, monitoring downloads,
and managing downloads via Synology's WebAPI.

Documentation: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/DownloadStation/All/enu/Synology_Download_Station_Web_API.pdf
"""

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


class DownloadStationSettings(DownloadClientSettings):
    """Settings for Synology Download Station client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/webapi').
    """

    url_base: str | None = "/webapi"


class DownloadStationProxy:
    """Low-level proxy for Synology Download Station WebAPI.

    Handles authentication, request building, and API communication.
    """

    def __init__(self, settings: DownloadStationSettings) -> None:
        """Initialize Download Station proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.webapi_url = urljoin(self.base_url.rstrip("/") + "/", "webapi")
        self._session_id: str | None = None
        self._api_info: dict[str, Any] = {}

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=False,
        )

    def _query_api_info(self) -> dict[str, Any]:
        """Query API information.

        Returns
        -------
        dict[str, Any]
            API information dictionary.
        """
        url = urljoin(self.webapi_url, "query.cgi")
        params = {
            "api": "SYNO.API.Info",
            "version": "1",
            "method": "query",
            "query": "SYNO.API.Auth,SYNO.DownloadStation.Task",
        }

        with self._get_client() as client:
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    msg = "Failed to query Download Station API info"
                    raise PVRProviderError(msg)

                return data.get("data", {})

            except httpx.HTTPStatusError as e:
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "Download Station API query")

        # Should be unreachable if handle_httpx_exception raises, but for typing:
        msg = "Failed to query API info"
        raise PVRProviderError(msg)

    def authenticate(self, force: bool = False) -> None:
        """Authenticate with Download Station and get session ID.

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
            msg = "Download Station requires username and password"
            raise PVRProviderAuthenticationError(msg)

        # Query API info if needed
        if not self._api_info:
            api_data = self._query_api_info()
            auth_info = api_data.get("SYNO.API.Auth", {})
            self._api_info["auth"] = auth_info

        auth_info = self._api_info.get("auth", {})
        auth_path = auth_info.get("path", "auth.cgi")
        auth_version = min(auth_info.get("maxVersion", 6), 6)

        url = urljoin(self.webapi_url, auth_path)
        params = {
            "api": "SYNO.API.Auth",
            "version": str(auth_version),
            "method": "login",
            "account": self.settings.username,
            "passwd": self.settings.password,
            "format": "sid",
            "session": "DownloadStation",
        }

        with self._get_client() as client:
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    error_code = data.get("error", {}).get("code", 0)
                    if error_code in (400, 401, 403, 105):
                        msg = "Download Station authentication failed"
                        raise PVRProviderAuthenticationError(msg)
                    msg = f"Download Station authentication error: {data.get('error', {})}"
                    raise PVRProviderError(msg)

                self._session_id = data.get("data", {}).get("sid")
                if not self._session_id:
                    msg = "Download Station did not return session ID"
                    raise PVRProviderAuthenticationError(msg)

                logger.debug("Download Station authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Download Station authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "Download Station authentication")
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, "Download Station authentication")

    def _execute_request(
        self,
        client: httpx.Client,
        url: str,
        request_params: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        url : str
            Request URL.
        request_params : dict[str, Any]
            Request parameters.
        files : dict[str, Any] | None
            Optional files to upload.

        Returns
        -------
        httpx.Response
            HTTP response.
        """
        if files:
            return client.post(
                url,
                params=request_params,
                files=files,
                timeout=self.settings.timeout_seconds,
            )
        return client.get(
            url,
            params=request_params,
            timeout=self.settings.timeout_seconds,
        )

    def _request(
        self,
        api: str,
        method: str,
        version: int = 1,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Parameters
        ----------
        api : str
            API name (e.g., 'SYNO.DownloadStation.Task').
        method : str
            Method name (e.g., 'create', 'list').
        version : int
            API version.
        params : dict[str, Any] | None
            Optional query/form parameters.
        files : dict[str, Any] | None
            Optional files to upload.

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

        # Query API info if needed
        if api not in self._api_info:
            api_data = self._query_api_info()
            task_info = api_data.get(api, {})
            self._api_info[api] = task_info

        api_info = self._api_info.get(api, {})
        api_path = api_info.get("path", "DownloadStation/task.cgi")

        url = urljoin(self.webapi_url, api_path)
        request_params: dict[str, Any] = {
            "api": api,
            "version": str(version),
            "method": method,
            "_sid": self._session_id,
        }

        if params:
            request_params.update(params)

        with self._get_client() as client:
            try:
                response = self._execute_request(client, url, request_params, files)

                # Handle auth expiration
                if response.status_code in (401, 403):
                    logger.debug("Session expired, re-authenticating")
                    self.authenticate(force=True)
                    request_params["_sid"] = self._session_id
                    response = self._execute_request(client, url, request_params, files)

                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    error = data.get("error", {})
                    error_code = error.get("code", 0)
                    if error_code in (105, 400, 401, 403):
                        msg = "Download Station authentication failed"
                        raise PVRProviderAuthenticationError(msg)
                    error_msg = error.get("errors", [{}])[0].get(
                        "reason", "Unknown error"
                    )
                    msg = f"Download Station API error: {error_msg}"
                    raise PVRProviderError(msg)

                return data.get("data", {})

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "Download Station authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Download Station API {api}.{method}")

        # Should be unreachable
        msg = f"Request failed: {api}.{method}"
        raise PVRProviderError(msg)

    def add_task_from_url(self, url: str, destination: str | None = None) -> str:
        """Add task from URL or magnet link.

        Parameters
        ----------
        url : str
            Torrent URL or magnet link.
        destination : str | None
            Optional download destination.

        Returns
        -------
        str
            Task ID.
        """
        params: dict[str, Any] = {"uri": url}
        if destination:
            params["destination"] = destination

        response = self._request(
            "SYNO.DownloadStation.Task",
            "create",
            version=1,
            params=params,
        )
        return str(response.get("taskid", ""))

    def add_task_from_file(
        self, file_content: bytes, filename: str, destination: str | None = None
    ) -> str:
        """Add task from file.

        Parameters
        ----------
        file_content : bytes
            Torrent file content.
        filename : str
            Torrent filename.
        destination : str | None
            Optional download destination.

        Returns
        -------
        str
            Task ID.
        """
        files = {"file": (filename, file_content, "application/x-bittorrent")}
        params: dict[str, Any] = {}
        if destination:
            params["destination"] = destination

        response = self._request(
            "SYNO.DownloadStation.Task",
            "create",
            version=1,
            params=params,
            files=files,
        )
        return str(response.get("taskid", ""))

    def get_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks.

        Returns
        -------
        list[dict[str, Any]]
            List of task dictionaries.
        """
        response = self._request("SYNO.DownloadStation.Task", "list", version=1)
        return response.get("tasks", [])

    def remove_task(self, task_id: str) -> None:
        """Remove task.

        Parameters
        ----------
        task_id : str
            Task ID.
        """
        params = {"id": task_id}
        self._request("SYNO.DownloadStation.Task", "delete", version=1, params=params)


class DownloadStationClient(BaseDownloadClient):
    """Synology Download Station client implementation.

    Supports both torrent and usenet downloads via Synology's WebAPI.
    """

    def __init__(
        self,
        settings: DownloadStationSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize Download Station client.

        Parameters
        ----------
        settings : DownloadStationSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to DownloadStationSettings.
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
            settings, DownloadStationSettings
        ):
            settings = DownloadStationSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/webapi",
            )

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: DownloadStationSettings = settings
        self._proxy = DownloadStationProxy(self.settings)
        # Download Station status codes: 0=waiting, 1=downloading, 2=paused,
        # 3=finished, 4=finished (errors), 5=hash checking, 6=extracting, 7=error, 8=seeding
        self._status_mapper = StatusMapper(
            {
                3: DownloadStatus.COMPLETED,  # Finished
                8: DownloadStatus.COMPLETED,  # Seeding
                7: DownloadStatus.FAILED,  # Error
                4: DownloadStatus.FAILED,  # Finished with errors
                2: DownloadStatus.PAUSED,  # Paused
                0: DownloadStatus.QUEUED,  # Waiting
                5: DownloadStatus.QUEUED,  # Hash checking
                6: DownloadStatus.QUEUED,  # Extracting
                1: DownloadStatus.DOWNLOADING,  # Downloading
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "Download Station"

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        destination = download_path or self.settings.download_path
        return self._proxy.add_task_from_url(magnet_url, destination=destination)

    def add_url(
        self,
        url: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        destination = download_path or self.settings.download_path
        return self._proxy.add_task_from_url(url, destination=destination)

    def add_file(
        self,
        filepath: str,
        _title: str | None,
        _category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        filename = Path(filepath).name
        destination = download_path or self.settings.download_path
        return self._proxy.add_task_from_file(
            file_content, filename, destination=destination
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

                # Map Download Station status to our status
                status_code = task.get("status", 0)
                status = self._status_mapper.map(status_code)

                # Get additional info
                additional = task.get("additional", {})
                transfer = additional.get("transfer", {})
                detail = additional.get("detail", {})

                # Calculate progress
                size = task.get("size", 0)
                downloaded = transfer.get("size_downloaded", 0)
                progress = downloaded / size if size > 0 else 0.0
                if progress > 1.0:
                    progress = 1.0

                # Get download speed
                download_speed = transfer.get("speed_download", 0)
                speed = int(download_speed) if download_speed > 0 else None

                # Get ETA
                eta = transfer.get("eta", -1)
                eta_seconds = int(eta) if eta > 0 else None

                item: DownloadItem = {
                    "client_item_id": task_id,
                    "title": task.get("title", ""),
                    "status": status,
                    "progress": progress,
                    "size_bytes": int(size) if size > 0 else None,
                    "downloaded_bytes": int(downloaded) if downloaded > 0 else None,
                    "download_speed_bytes_per_sec": speed,
                    "eta_seconds": eta_seconds,
                    "file_path": detail.get("destination", ""),
                }
                items.append(item)

        except Exception as e:
            msg = f"Failed to get downloads from Download Station: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, _delete_files: bool = False) -> bool:
        """Remove a download from Download Station.

        Parameters
        ----------
        client_item_id : str
            Task ID.
        delete_files : bool
            Whether to delete downloaded files (not supported by API).

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
            msg = "Download Station client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_task(client_item_id)
        except Exception as e:
            msg = f"Failed to remove download from Download Station: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to Download Station.

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
            msg = f"Failed to connect to Download Station: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

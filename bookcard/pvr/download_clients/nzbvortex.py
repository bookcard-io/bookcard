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

"""NZBVortex download client implementation.

NZBVortex is a usenet client for macOS that uses a REST API.
This implementation supports adding NZB files, monitoring queue,
and managing downloads.

Documentation: https://www.nzbvortex.com/
"""

import base64
import hashlib
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


class NzbvortexSettings(DownloadClientSettings):
    """Settings for NZBVortex download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: None).
    api_key : str | None
        API key for authentication.
    """

    url_base: str | None = None
    api_key: str | None = None


class NzbvortexProxy:
    """Low-level proxy for NZBVortex REST API.

    Handles authentication, request building, and API communication.
    """

    def __init__(self, settings: NzbvortexSettings) -> None:
        """Initialize NZBVortex proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.api_url = urljoin(self.base_url.rstrip("/") + "/", "api")
        self._session_id: str | None = None

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def _get_nonce(self, client: httpx.Client) -> str:
        """Get authentication nonce from NZBVortex.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.

        Returns
        -------
        str
            Nonce value.

        Raises
        ------
        PVRProviderAuthenticationError
            If nonce retrieval fails.
        """

        def _raise_no_nonce_error() -> None:
            """Raise error when nonce is not returned."""
            msg = "NZBVortex did not return nonce"
            raise PVRProviderAuthenticationError(msg)

        nonce_url = urljoin(self.api_url.rstrip("/") + "/", "auth/nonce")
        response = client.get(nonce_url, timeout=self.settings.timeout_seconds)
        response.raise_for_status()

        nonce_data = response.json()
        nonce = nonce_data.get("authNonce", "")

        if not nonce:
            _raise_no_nonce_error()

        return nonce

    def _perform_login(
        self, client: httpx.Client, nonce: str, cnonce: str, hash_b64: str
    ) -> httpx.Response:
        """Perform login request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        nonce : str
            Nonce value.
        cnonce : str
            Client nonce value.
        hash_b64 : str
            Base64-encoded hash.

        Returns
        -------
        httpx.Response
            Login response.
        """
        login_url = urljoin(self.api_url.rstrip("/") + "/", "auth/login")
        return client.get(
            login_url,
            params={
                "nonce": nonce,
                "cnonce": cnonce,
                "hash": hash_b64,
            },
            timeout=self.settings.timeout_seconds,
        )

    def _extract_session_id(self, login_response: httpx.Response) -> None:
        """Extract session ID from login response cookies.

        Parameters
        ----------
        login_response : httpx.Response
            Login response.

        Raises
        ------
        PVRProviderAuthenticationError
            If session ID is not found.
        """

        def _raise_no_session_error() -> None:
            """Raise error when session ID is not returned."""
            msg = "NZBVortex did not return session ID"
            raise PVRProviderAuthenticationError(msg)

        for cookie_item in login_response.cookies:
            cookie_name = getattr(cookie_item, "name", None)
            cookie_value = getattr(cookie_item, "value", None)
            if cookie_name == "sessionid" and cookie_value is not None:
                self._session_id = str(cookie_value)
                return

        _raise_no_session_error()

    def _authenticate(self, force: bool = False) -> None:
        """Authenticate with NZBVortex and get session ID.

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

        if not self.settings.api_key:
            msg = "NZBVortex requires API key"
            raise PVRProviderAuthenticationError(msg)

        with self._get_client() as client:
            try:
                nonce = self._get_nonce(client)

                # Generate cnonce and hash
                import uuid

                cnonce = str(uuid.uuid4()).replace("-", "")
                hash_string = f"{nonce}:{cnonce}:{self.settings.api_key}"

                # SHA256 hash
                hash_bytes = hashlib.sha256(hash_string.encode("utf-8")).digest()
                hash_hex = hash_bytes.hex()
                hash_b64 = base64.b64encode(bytes.fromhex(hash_hex)).decode("utf-8")

                # Login
                login_response = self._perform_login(client, nonce, cnonce, hash_b64)
                login_response.raise_for_status()

                login_data = login_response.json()
                if login_data.get("result") != "success":

                    def _raise_auth_failed_error() -> None:
                        """Raise error when authentication fails."""
                        msg = "NZBVortex authentication failed"
                        raise PVRProviderAuthenticationError(msg)

                    _raise_auth_failed_error()

                # Extract session ID from cookies
                self._extract_session_id(login_response)

                logger.debug("NZBVortex authentication succeeded")

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "NZBVortex authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_httpx_exception(e, "NZBVortex authentication")
            except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
                handle_httpx_exception(e, "NZBVortex authentication")

    def _execute_request(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        cookies: dict[str, str],
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request.

        Parameters
        ----------
        client : httpx.Client
            HTTP client instance.
        method : str
            HTTP method (GET, POST, DELETE).
        url : str
            Request URL.
        params : dict[str, Any] | None
            Optional query parameters.
        cookies : dict[str, str]
            Request cookies.
        files : dict[str, Any] | None
            Optional files to upload.

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
                url,
                params=params,
                cookies=cookies,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "POST":
            if files:
                return client.post(
                    url,
                    params=params,
                    files=files,
                    cookies=cookies,
                    timeout=self.settings.timeout_seconds,
                )
            return client.post(
                url,
                params=params,
                cookies=cookies,
                timeout=self.settings.timeout_seconds,
            )
        if method_upper == "DELETE":
            return client.delete(
                url,
                params=params,
                cookies=cookies,
                timeout=self.settings.timeout_seconds,
            )
        msg = f"Unsupported HTTP method: {method}"
        raise PVRProviderError(msg)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, DELETE).
        endpoint : str
            API endpoint path.
        params : dict[str, Any] | None
            Optional query parameters.
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
        self._authenticate()

        url = urljoin(self.api_url.rstrip("/") + "/", endpoint.lstrip("/"))

        cookies: dict[str, str] = {}
        if self._session_id:
            cookies["sessionid"] = self._session_id

        with self._get_client() as client:
            try:
                response = self._execute_request(
                    client, method, url, params, cookies, files
                )

                # Handle session expiration
                if response.status_code == 401:
                    logger.debug("Session expired, re-authenticating")
                    self._authenticate(force=True)
                    if self._session_id:
                        cookies["sessionid"] = self._session_id

                    response = self._execute_request(
                        client, method, url, params, cookies, files
                    )

                response.raise_for_status()

                result = response.json()

                # Check for errors
                if result.get("result") == "notLoggedIn":
                    msg = "NZBVortex session expired"
                    raise PVRProviderAuthenticationError(msg)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "NZBVortex authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise  # Unreachable, but needed for type checker
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"NZBVortex API {method} {endpoint}")
                raise  # Unreachable, but needed for type checker
            else:
                return result

    def add_nzb(
        self,
        nzb_data: bytes,
        filename: str,
        priority: int = 0,
        groupname: str | None = None,
    ) -> str:
        """Add NZB file.

        Parameters
        ----------
        nzb_data : bytes
            NZB file content.
        filename : str
            NZB filename.
        priority : int
            Priority (0=normal).
        groupname : str | None
            Optional group name.

        Returns
        -------
        str
            NZB ID.
        """
        params: dict[str, Any] = {"priority": priority}
        if groupname:
            params["groupname"] = groupname

        files = {"name": (filename, nzb_data, "application/x-nzb")}

        response = self._request("POST", "nzb/add", params=params, files=files)
        return str(response.get("id", ""))

    def get_queue(self, limit_done: int = 50) -> list[dict[str, Any]]:
        """Get queue items.

        Parameters
        ----------
        limit_done : int
            Limit for completed items.

        Returns
        -------
        list[dict[str, Any]]
            List of queue items.
        """
        params: dict[str, Any] = {"limitDone": limit_done}
        if self.settings.category:
            params["groupName"] = self.settings.category

        response = self._request("GET", "nzb", params=params)
        return response.get("items", [])

    def remove_nzb(self, nzb_id: int, delete_data: bool = False) -> None:
        """Remove NZB from queue.

        Parameters
        ----------
        nzb_id : int
            NZB ID.
        delete_data : bool
            Whether to delete downloaded data.
        """
        endpoint = (
            f"nzb/{nzb_id}/cancelDelete" if delete_data else f"nzb/{nzb_id}/cancel"
        )
        self._request("GET", endpoint)


class NzbvortexClient(BaseDownloadClient):
    """NZBVortex download client implementation.

    Implements BaseDownloadClient interface for NZBVortex REST API.
    """

    def __init__(
        self,
        settings: NzbvortexSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize NZBVortex client.

        Parameters
        ----------
        settings : NzbvortexSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to NzbvortexSettings.
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
            settings, NzbvortexSettings
        ):
            nzbvortex_settings = NzbvortexSettings(
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
            settings = nzbvortex_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: NzbvortexSettings = settings  # type: ignore[assignment]
        self._proxy = NzbvortexProxy(self.settings)
        self._status_mapper = StatusMapper(
            {
                "completed": DownloadStatus.COMPLETED,
                "failed": DownloadStatus.FAILED,
                "paused": DownloadStatus.PAUSED,
                "queued": DownloadStatus.QUEUED,
                "downloading": DownloadStatus.DOWNLOADING,
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "NZBVortex"

    def add_magnet(
        self,
        _magnet_url: str,
        _title: str | None,
        _category: str | None,
        _download_path: str | None,
    ) -> str:
        """Add download from magnet link (not supported by NZBVortex)."""
        msg = "NZBVortex does not support magnet links"
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
        groupname = category or self.settings.category
        nzb_id = self._proxy.add_nzb(nzb_data, filename, groupname=groupname)
        return str(nzb_id)

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
        groupname = category or self.settings.category
        nzb_id = self._proxy.add_nzb(nzb_data, filename, groupname=groupname)
        return str(nzb_id)

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
            queue_items = self._proxy.get_queue()

            items = []
            for item in queue_items:
                nzb_id = item.get("id", 0)
                if not nzb_id:
                    continue

                # Map NZBVortex status to our status
                state = item.get("state", "")
                item_status = self._status_mapper.map(state)

                # Calculate progress
                progress = float(item.get("progress", 0.0)) / 100.0
                if progress > 1.0:
                    progress = 1.0

                size_bytes = item.get("size", 0)
                downloaded_bytes = int(size_bytes * progress) if size_bytes else None

                item_dict: DownloadItem = {
                    "client_item_id": str(nzb_id),
                    "title": item.get("name", ""),
                    "status": item_status,
                    "progress": progress,
                    "size_bytes": int(size_bytes) if size_bytes else None,
                    "downloaded_bytes": downloaded_bytes,
                    "download_speed_bytes_per_sec": None,
                    "eta_seconds": None,
                    "file_path": None,
                }
                items.append(item_dict)
        except Exception as e:
            msg = f"Failed to get downloads from NZBVortex: {e}"
            raise PVRProviderError(msg) from e

        return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove a download from NZBVortex.

        Parameters
        ----------
        client_item_id : str
            NZB ID.
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
            msg = "NZBVortex client is disabled"
            raise PVRProviderError(msg)

        try:
            nzb_id = int(client_item_id)
            self._proxy.remove_nzb(nzb_id, delete_files)
        except Exception as e:
            msg = f"Failed to remove download from NZBVortex: {e}"
            raise PVRProviderError(msg) from e

        return True

    def test_connection(self) -> bool:
        """Test connectivity to NZBVortex.

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
            # Try to get queue as connection test
            self._proxy.get_queue(limit_done=1)
        except Exception as e:
            msg = f"Failed to connect to NZBVortex: {e}"
            raise PVRProviderError(msg) from e

        return True

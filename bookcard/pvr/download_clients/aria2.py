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

import base64
import logging
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

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

    def __init__(self, settings: Aria2Settings) -> None:
        """Initialize Aria2 proxy."""
        self.settings = settings
        self.base_url = build_base_url(
            settings.host, settings.port, settings.use_ssl, settings.url_base
        )
        self.rpc_url = self.base_url.rstrip("/")

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client."""
        return create_httpx_client(
            timeout=self.settings.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

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

    def _add_xmlrpc_array(self, data_elem: ET.Element, param: list[str | int]) -> None:
        """Add array parameter to XML-RPC request.

        Parameters
        ----------
        data_elem : ET.Element
            Data element to add items to.
        param : list[str | int]
            Array parameter values.
        """
        for item in param:
            item_param = ET.SubElement(data_elem, "value")
            if isinstance(item, str):
                string_elem = ET.SubElement(item_param, "string")
                string_elem.text = item
            elif isinstance(item, int):
                int_elem = ET.SubElement(item_param, "int")
                int_elem.text = str(item)

    def _add_xmlrpc_struct(
        self, struct_elem: ET.Element, param: dict[str, str | int | None]
    ) -> None:
        """Add struct parameter to XML-RPC request.

        Parameters
        ----------
        struct_elem : ET.Element
            Struct element to add members to.
        param : dict[str, str | int]
            Struct parameter values.
        """
        for key, val in param.items():
            member = ET.SubElement(struct_elem, "member")
            name_elem = ET.SubElement(member, "name")
            name_elem.text = str(key)
            value_elem2 = ET.SubElement(member, "value")
            if isinstance(val, str):
                string_elem = ET.SubElement(value_elem2, "string")
                string_elem.text = val
            elif isinstance(val, int):
                int_elem = ET.SubElement(value_elem2, "int")
                int_elem.text = str(val)

    def _add_xmlrpc_param(
        self,
        params_elem: ET.Element,
        param: str | bytes | int | list[str | int] | dict[str, str | int | None],
    ) -> None:
        """Add a parameter to XML-RPC request.

        Parameters
        ----------
        params_elem : ET.Element
            Params element to add parameter to.
        param : str | bytes | int | list[str | int] | dict[str, str | int]
            Parameter value.
        """
        param_elem = ET.SubElement(params_elem, "param")
        value_elem = ET.SubElement(param_elem, "value")

        if isinstance(param, str):
            string_elem = ET.SubElement(value_elem, "string")
            string_elem.text = param
        elif isinstance(param, bytes):
            base64_elem = ET.SubElement(value_elem, "base64")
            base64_elem.text = base64.b64encode(param).decode("utf-8")
        elif isinstance(param, int):
            int_elem = ET.SubElement(value_elem, "int")
            int_elem.text = str(param)
        elif isinstance(param, (list, tuple)):
            array_elem = ET.SubElement(value_elem, "array")
            data_elem = ET.SubElement(array_elem, "data")
            self._add_xmlrpc_array(data_elem, param)
        elif isinstance(param, dict):
            struct_elem = ET.SubElement(value_elem, "struct")
            self._add_xmlrpc_struct(struct_elem, param)

    def _build_xmlrpc_request(
        self,
        method: str,
        *params: str | bytes | int | list[str | int] | dict[str, str | int | None],
    ) -> str:
        """Build XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : str | bytes | int | list[str | int] | dict[str, str | int]
            Method parameters.

        Returns
        -------
        str
            XML-RPC request body.
        """
        root = ET.Element("methodCall")
        method_name = ET.SubElement(root, "methodName")
        method_name.text = method

        params_elem = ET.SubElement(root, "params")

        # Add token as first parameter if secret is set
        token = self._get_token()
        if token:
            param_elem = ET.SubElement(params_elem, "param")
            value_elem = ET.SubElement(param_elem, "value")
            string_elem = ET.SubElement(value_elem, "string")
            string_elem.text = token

        for param in params:
            self._add_xmlrpc_param(params_elem, param)

        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def _check_xmlrpc_fault(self, root: ET.Element) -> None:
        """Check for XML-RPC fault and raise if found.

        Parameters
        ----------
        root : ET.Element
            XML root element.

        Raises
        ------
        PVRProviderError
            If fault is found.
        """
        fault = root.find(".//fault")
        if fault is not None:
            fault_value = fault.find("value")
            if fault_value is not None:
                fault_struct = fault_value.find("struct")
                if fault_struct is not None:
                    fault_string = fault_struct.find(".//string")
                    if fault_string is not None:
                        error_msg = fault_string.text or "Unknown error"
                        msg = f"Aria2 XML-RPC fault: {error_msg}"
                        raise PVRProviderError(msg)

    def _parse_xmlrpc_struct_value(self, value_elem: ET.Element) -> str | int | None:
        """Parse XML-RPC struct value element.

        Parameters
        ----------
        value_elem : ET.Element
            Value element to parse.

        Returns
        -------
        str | int | None
            Parsed value.
        """
        val = None
        string_elem = value_elem.find("string")
        if string_elem is not None and string_elem.text is not None:
            val = string_elem.text
        else:
            int_elem = value_elem.find("int")
            if int_elem is not None and int_elem.text is not None:
                val = int(int_elem.text)
            else:
                i8_elem = value_elem.find("i8")
                if i8_elem is not None and i8_elem.text is not None:
                    val = int(i8_elem.text)
        return val

    def _parse_xmlrpc_array(
        self, data: ET.Element
    ) -> list[dict[str, str | int | None]]:
        """Parse XML-RPC array element.

        Parameters
        ----------
        data : ET.Element
            Data element containing array values.

        Returns
        -------
        list[dict[str, str | int | None]]
            List of parsed struct dictionaries.
        """
        results = []
        for value_elem in data.findall("value"):
            struct_elem = value_elem.find("struct")
            if struct_elem is not None:
                struct_dict: dict[str, str | int | None] = {}
                for member in struct_elem.findall("member"):
                    name_elem = member.find("name")
                    value_elem2 = member.find("value")
                    if name_elem is not None and value_elem2 is not None:
                        name = name_elem.text or ""
                        val = self._parse_xmlrpc_struct_value(value_elem2)
                        struct_dict[name] = val
                results.append(struct_dict)
        return results

    def _parse_xmlrpc_response(
        self, xml_content: str
    ) -> str | int | list[dict[str, str | int | None]] | None:
        """Parse XML-RPC response.

        Parameters
        ----------
        xml_content : str
            XML response content.

        Returns
        -------
        Any
            Parsed response value.

        Raises
        ------
        PVRProviderError
            If parsing fails or response contains fault.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except ET.ParseError as e:
            msg = f"Failed to parse Aria2 XML-RPC response: {e}"
            raise PVRProviderError(msg) from e

        self._check_xmlrpc_fault(root)

        # Extract return value
        params = root.find(".//params/param/value")
        if params is None:
            return None

        # Simple value extraction
        string_elem = params.find("string")
        if string_elem is not None:
            return string_elem.text

        int_elem = params.find("int")
        if int_elem is not None:
            return int(int_elem.text or "0")

        # For arrays
        array_elem = params.find("array")
        if array_elem is not None:
            data = array_elem.find("data")
            if data is not None:
                return self._parse_xmlrpc_array(data)

        return None

    def _request(
        self,
        method: str,
        *params: str | bytes | int | list[str | int] | dict[str, str | int | None],
    ) -> str | int | list[dict[str, str | int | None]] | None:
        """Make XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : Any
            Method parameters.

        Returns
        -------
        Any
            RPC response result.
        """
        xml_request = self._build_xmlrpc_request(method, *params)

        headers: dict[str, str] = {
            "Content-Type": "text/xml",
            "Content-Length": str(len(xml_request)),
        }

        # Add basic auth if provided
        if self.settings.username and self.settings.password:
            credentials = f"{self.settings.username}:{self.settings.password}"
            auth_bytes = base64.b64encode(credentials.encode("utf-8"))
            headers["Authorization"] = f"Basic {auth_bytes.decode('utf-8')}"

        with self._get_client() as client:
            try:
                response = client.post(
                    self.rpc_url,
                    content=xml_request,
                    headers=headers,
                    timeout=self.settings.timeout_seconds,
                )

                if response.status_code == 401:
                    auth_error_msg = "Aria2 authentication failed"
                    raise PVRProviderAuthenticationError(auth_error_msg)

                response.raise_for_status()
                results = self._parse_xmlrpc_response(response.text)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    auth_error_msg = "Aria2 authentication failed"
                    raise PVRProviderAuthenticationError(auth_error_msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"Aria2 XML-RPC {method}")
                raise
            else:
                return results

    def get_version(self) -> str:
        """Get Aria2 version."""
        result = self._request("aria2.getVersion")
        if isinstance(result, dict):
            return result.get("version", "unknown")
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
        result = self._request("aria2.addUri", uris, options)
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
        result = self._request("aria2.addTorrent", file_content, uris, options)
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
        items.extend(active if isinstance(active, list) else [])
        items.extend(waiting if isinstance(waiting, list) else [])
        items.extend(stopped if isinstance(stopped, list) else [])

        return items

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


class Aria2Client(BaseDownloadClient):
    """Aria2 download client implementation.

    Implements BaseDownloadClient interface for Aria2 XML-RPC API.
    """

    def __init__(
        self,
        settings: Aria2Settings | DownloadClientSettings,
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

        super().__init__(settings, enabled)
        self.settings: Aria2Settings = settings  # type: ignore[assignment]
        self._proxy = Aria2Proxy(self.settings)

    def _raise_invalid_url_error(self, download_url: str) -> None:
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
        invalid_url_msg = f"Invalid download URL: {download_url}"
        raise PVRProviderError(invalid_url_msg)

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
                speed = int(download_speed)
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
                eta_seconds = int(eta)
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
    ) -> dict[str, str | int | float | None]:
        """Build download item dict from download data.

        Parameters
        ----------
        download : dict[str, str | int | None]
            Download dictionary from Aria2.

        Returns
        -------
        dict[str, str | int | float | None]
            Formatted download item.
        """
        gid = download.get("gid", "")
        status = download.get("status", "")
        item_status = self._map_status_to_status(str(status) if status else "")

        total_length = download.get("totalLength", "0")
        completed_length = download.get("completedLength", "0")
        progress = self._calculate_progress(total_length, completed_length)

        try:
            total = int(total_length) if total_length else 0
            completed = int(completed_length) if completed_length else 0
        except (ValueError, TypeError):
            total = 0
            completed = 0

        speed = self._get_download_speed(download)
        eta_seconds = self._get_eta(download)
        title = self._get_download_title(download)

        return {
            "client_item_id": str(gid),
            "title": title,
            "status": item_status,
            "progress": progress,
            "size_bytes": total if total > 0 else None,
            "downloaded_bytes": completed if completed > 0 else None,
            "download_speed_bytes_per_sec": speed,
            "eta_seconds": eta_seconds,
            "file_path": download.get("dir", ""),
        }

    def add_download(
        self,
        download_url: str,
        title: str | None = None,  # noqa: ARG002
        category: str | None = None,  # noqa: ARG002
        download_path: str | None = None,
    ) -> str:
        """Add a download to Aria2.

        Parameters
        ----------
        download_url : str
            URL, magnet link, or file path.
        title : str | None
            Optional title.
        category : str | None
            Optional category (not used by Aria2).
        download_path : str | None
            Optional download path.

        Returns
        -------
        str
            Download GID.

        Raises
        ------
        PVRProviderError
            If adding the download fails.
        """
        if not self.is_enabled():
            msg = "Aria2 client is disabled"
            raise PVRProviderError(msg)

        try:
            # Build options
            options: dict[str, str | int | None] = {}
            path = download_path or self.settings.download_path
            if path:
                options["dir"] = path

            # Add download
            if download_url.startswith("magnet:"):
                gid = self._proxy.add_magnet(download_url, options)
            elif download_url.startswith("http"):
                # Aria2 can download directly from URL
                gid = self._proxy.add_magnet(download_url, options)
            elif Path(download_url).is_file():
                file_content = Path(download_url).read_bytes()
                gid = self._proxy.add_torrent(file_content, options)
            else:
                self._raise_invalid_url_error(download_url)
        except PVRProviderError:
            raise
        except Exception as e:
            add_error_msg = f"Failed to add download to Aria2: {e}"
            raise PVRProviderError(add_error_msg) from e
        else:
            return gid

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

    def _map_status_to_status(self, status: str) -> str:
        """Map Aria2 status to standardized status.

        Parameters
        ----------
        status : str
            Aria2 status string.

        Returns
        -------
        str
            Standardized status string.
        """
        # Aria2 statuses: active, waiting, paused, error, complete, removed
        if status == "complete":
            return "completed"
        if status == "error":
            return "failed"
        if status == "paused":
            return "paused"
        if status == "waiting":
            return "queued"
        if status == "active":
            return "downloading"
        return "downloading"

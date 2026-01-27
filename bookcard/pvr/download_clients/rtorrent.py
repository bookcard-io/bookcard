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

"""rTorrent download client implementation.

rTorrent is a torrent client that uses XML-RPC API.
This implementation supports adding torrents, monitoring downloads,
and managing torrents.

Documentation: https://github.com/rakshasa/rtorrent/wiki/RPC-Setup-XMLRPC
"""

import base64
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET  # noqa: S405

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


class RTorrentSettings(DownloadClientSettings):
    """Settings for rTorrent download client.

    Attributes
    ----------
    url_base : str | None
        Optional URL base path (default: '/RPC2' for XML-RPC).
    """

    url_base: str | None = "/RPC2"


class RTorrentProxy:
    """Low-level proxy for rTorrent XML-RPC API.

    Handles XML-RPC request building and API communication.
    """

    def __init__(self, settings: RTorrentSettings) -> None:
        """Initialize rTorrent proxy."""
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
        self, struct_elem: ET.Element, param: dict[str, str | int]
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
        param: str | bytes | int | list[str | int] | dict[str, str | int],
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
        *params: str | bytes | int | list[str | int] | dict[str, str | int],
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
                        msg = f"rTorrent XML-RPC fault: {error_msg}"
                        raise PVRProviderError(msg)

    def _parse_xmlrpc_array(self, data: ET.Element) -> list[str | int]:
        """Parse XML-RPC array element.

        Parameters
        ----------
        data : ET.Element
            Data element containing array values.

        Returns
        -------
        list[str | int]
            Parsed array values.
        """
        results = []
        for value_elem in data.findall("value"):
            # Extract first child value
            for child in value_elem:
                if child.tag == "string":
                    results.append(child.text)
                elif child.tag == "int" or child.tag == "i8":
                    results.append(int(child.text or "0"))
        return results

    def _parse_xmlrpc_response(
        self, xml_content: str
    ) -> str | int | list[str | int] | None:
        """Parse XML-RPC response.

        Parameters
        ----------
        xml_content : str
            XML response content.

        Returns
        -------
        str | int | list[str | int] | None
            Parsed response value.

        Raises
        ------
        PVRProviderError
            If parsing fails or response contains fault.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except ET.ParseError as e:
            msg = f"Failed to parse rTorrent XML-RPC response: {e}"
            raise PVRProviderError(msg) from e

        self._check_xmlrpc_fault(root)

        # Extract return value
        params = root.find(".//params/param/value")
        if params is None:
            return None

        # Simple value extraction (can be extended for complex types)
        string_elem = params.find("string")
        if string_elem is not None:
            return string_elem.text

        int_elem = params.find("int")
        if int_elem is not None:
            return int(int_elem.text or "0")

        # For arrays (multicall results)
        array_elem = params.find("array")
        if array_elem is not None:
            data = array_elem.find("data")
            if data is not None:
                return self._parse_xmlrpc_array(data)

        return None

    def _request(
        self,
        method: str,
        *params: str | bytes | int | list[str | int] | dict[str, str | int],
    ) -> str | int | list[str | int] | None:
        """Make XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : str | bytes | int | list[str | int] | dict[str, str | int]
            Method parameters.

        Returns
        -------
        str | int | list[str | int] | None
            RPC response result.
        """
        xml_request = self._build_xmlrpc_request(method, *params)

        headers: dict[str, str] = {
            "Content-Type": "text/xml",
            "Content-Length": str(len(xml_request)),
        }

        # Add basic auth if provided
        if self.settings.username and self.settings.password:
            import base64

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

                    def _raise_auth_error() -> None:
                        """Raise authentication error."""
                        msg = "rTorrent authentication failed"
                        raise PVRProviderAuthenticationError(msg)

                    _raise_auth_error()

                response.raise_for_status()

                return self._parse_xmlrpc_response(response.text)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    msg = "rTorrent authentication failed"
                    raise PVRProviderAuthenticationError(msg) from e
                handle_http_error_response(
                    e.response.status_code, e.response.text[:200]
                )
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                handle_httpx_exception(e, f"rTorrent XML-RPC {method}")
                raise

    def get_version(self) -> str:
        """Get rTorrent version."""
        result = self._request("system.client_version")
        return str(result) if result else "unknown"

    def add_torrent_url(
        self,
        torrent_url: str,
        label: str | None = None,
        directory: str | None = None,
    ) -> None:
        """Add torrent from URL.

        Parameters
        ----------
        torrent_url : str
            Torrent URL or magnet link.
        label : str | None
            Optional label (custom1).
        directory : str | None
            Optional download directory.
        """
        commands: list[str] = []
        if directory:
            commands.append(f'd.directory.set="{directory}"')
        if label:
            commands.append(f'd.custom1.set="{label}"')

        args: list[Any] = ["", torrent_url]
        args.extend(commands)

        result = self._request("load.start", *args)
        if result != 0:
            msg = f"rTorrent failed to add torrent: {torrent_url}"
            raise PVRProviderError(msg)

    def add_torrent_file(
        self,
        filename: str,
        file_content: bytes,
        label: str | None = None,
        directory: str | None = None,
    ) -> None:
        """Add torrent from file.

        Parameters
        ----------
        filename : str
            Torrent filename.
        file_content : bytes
            Torrent file content.
        label : str | None
            Optional label (custom1).
        directory : str | None
            Optional download directory.
        """
        commands: list[str] = []
        if directory:
            commands.append(f'd.directory.set="{directory}"')
        if label:
            commands.append(f'd.custom1.set="{label}"')

        args: list[Any] = ["", file_content]
        args.extend(commands)

        result = self._request("load.raw_start", *args)
        if result != 0:
            msg = f"rTorrent failed to add torrent: {filename}"
            raise PVRProviderError(msg)

    def get_torrents(self) -> list[dict[str, Any]]:
        """Get all torrents.

        Returns
        -------
        list[dict[str, Any]]
            List of torrent dictionaries.
        """
        # Use multicall to get multiple fields at once
        result = self._request(
            "d.multicall2",
            "",
            "",
            "d.name=",  # string
            "d.hash=",  # string
            "d.base_path=",  # string
            "d.custom1=",  # string (label)
            "d.size_bytes=",  # i8
            "d.left_bytes=",  # i8
            "d.down.rate=",  # i8 (bytes/s)
            "d.ratio=",  # i8
            "d.is_open=",  # int
            "d.is_active=",  # int
            "d.complete=",  # int
            "d.timestamp.finished=",  # i8
        )

        if not result or not isinstance(result, list):
            return []

        torrents = []
        for item in result:
            if not isinstance(item, list) or len(item) < 12:
                continue

            torrent = {
                "name": item[0] if len(item) > 0 else "",
                "hash": item[1] if len(item) > 1 else "",
                "base_path": item[2] if len(item) > 2 else "",
                "label": item[3] if len(item) > 3 else "",
                "size_bytes": item[4] if len(item) > 4 else 0,
                "left_bytes": item[5] if len(item) > 5 else 0,
                "down_rate": item[6] if len(item) > 6 else 0,
                "ratio": item[7] if len(item) > 7 else 0,
                "is_open": item[8] if len(item) > 8 else 0,
                "is_active": item[9] if len(item) > 9 else 0,
                "complete": item[10] if len(item) > 10 else 0,
                "finished": item[11] if len(item) > 11 else 0,
            }
            torrents.append(torrent)

        return torrents

    def remove_torrent(self, hash_str: str) -> None:
        """Remove torrent.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        """
        result = self._request("d.erase", hash_str)
        if result != 0:
            msg = f"rTorrent failed to remove torrent: {hash_str}"
            raise PVRProviderError(msg)

    def set_torrent_label(self, hash_str: str, label: str) -> None:
        """Set torrent label.

        Parameters
        ----------
        hash_str : str
            Torrent hash.
        label : str
            Label name (custom1).
        """
        result = self._request("d.custom1.set", hash_str, label)
        if result != label:
            msg = f"rTorrent failed to set label for torrent: {hash_str}"
            raise PVRProviderError(msg)


class RTorrentClient(BaseDownloadClient):
    """rTorrent download client implementation.

    Implements BaseDownloadClient interface for rTorrent XML-RPC API.
    """

    def __init__(
        self,
        settings: RTorrentSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize rTorrent client.

        Parameters
        ----------
        settings : RTorrentSettings | DownloadClientSettings
            Client settings. If DownloadClientSettings, converts to RTorrentSettings.
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
            settings, RTorrentSettings
        ):
            rtorrent_settings = RTorrentSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                url_base="/RPC2",
            )
            settings = rtorrent_settings

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: RTorrentSettings = settings
        self._proxy = RTorrentProxy(self.settings)
        self._status_mapper = StatusMapper(
            {
                # Status determined by complete and is_active flags
                # We'll map in get_items based on torrent dict
            },
            default=DownloadStatus.DOWNLOADING,
        )

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "rTorrent"

    def _extract_hash_from_magnet(self, magnet_url: str) -> str:
        """Extract hash from magnet link.

        Parameters
        ----------
        magnet_url : str
            Magnet URL.

        Returns
        -------
        str
            Extracted hash or empty string.
        """
        for part in magnet_url.split("&"):
            if "xt=urn:btih:" in part:
                return part.split(":")[-1].upper()
        return ""

    def add_magnet(
        self,
        magnet_url: str,
        _title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from magnet link."""
        label = category or self.settings.category
        directory = download_path or self.settings.download_path
        hash_str = self._extract_hash_from_magnet(magnet_url)
        self._proxy.add_torrent_url(magnet_url, label=label, directory=directory)
        return hash_str if hash_str else "pending"

    def add_url(
        self,
        url: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from HTTP/HTTPS URL."""
        file_content, filename = self._file_fetcher.fetch_with_filename(
            url, title or "download.torrent"
        )
        label = category or self.settings.category
        directory = download_path or self.settings.download_path
        self._proxy.add_torrent_file(
            filename, file_content, label=label, directory=directory
        )
        return "pending"

    def add_file(
        self,
        filepath: str,
        title: str | None,
        category: str | None,
        download_path: str | None,
    ) -> str:
        """Add download from local file."""
        file_content = Path(filepath).read_bytes()
        filename = title or Path(filepath).name
        label = category or self.settings.category
        directory = download_path or self.settings.download_path
        self._proxy.add_torrent_file(
            filename, file_content, label=label, directory=directory
        )
        return "pending"

    def _map_torrent_status(self, torrent: dict[str, str | int]) -> str:
        """Map rTorrent state to standardized status.

        Parameters
        ----------
        torrent : dict[str, str | int]
            Torrent dictionary.

        Returns
        -------
        str
            Standardized status string.
        """
        is_complete = torrent.get("complete", 0) == 1
        is_active = torrent.get("is_active", 0) == 1

        if is_complete:
            return DownloadStatus.COMPLETED
        if is_active:
            return DownloadStatus.DOWNLOADING
        return DownloadStatus.PAUSED

    def _calculate_progress(
        self, total_bytes: int | None, remaining_bytes: int | None
    ) -> float:
        """Calculate download progress.

        Parameters
        ----------
        total_bytes : int | None
            Total size in bytes.
        remaining_bytes : int | None
            Remaining bytes to download.

        Returns
        -------
        float
            Progress as a float between 0.0 and 1.0.
        """
        if total_bytes and total_bytes > 0:
            downloaded = total_bytes - (remaining_bytes or 0)
            progress = downloaded / total_bytes
            return min(progress, 1.0)
        return 0.0

    def _build_download_item(
        self, torrent: dict[str, str | int]
    ) -> dict[str, str | int | float | None]:
        """Build download item dict from torrent data.

        Parameters
        ----------
        torrent : dict[str, str | int]
            Torrent dictionary from rTorrent.

        Returns
        -------
        dict[str, str | int | float | None]
            Formatted download item.
        """
        hash_str = torrent.get("hash", "")
        status = self._map_torrent_status(torrent)

        size_bytes = torrent.get("size_bytes", 0)
        left_bytes = torrent.get("left_bytes", 0)
        total_bytes = int(size_bytes) if size_bytes else None
        remaining_bytes = int(left_bytes) if left_bytes else None

        progress = self._calculate_progress(total_bytes, remaining_bytes)

        down_rate = torrent.get("down_rate", 0)
        download_speed = int(down_rate) if down_rate else None

        eta_seconds = None
        if download_speed and download_speed > 0 and remaining_bytes:
            eta_seconds = int(remaining_bytes / download_speed)

        name = torrent.get("name", "")
        base_path = torrent.get("base_path")
        return {
            "client_item_id": str(hash_str).upper(),
            "title": str(name) if name else "",
            "status": status,
            "progress": progress,
            "size_bytes": total_bytes,
            "downloaded_bytes": total_bytes - remaining_bytes
            if total_bytes and remaining_bytes
            else None,
            "download_speed_bytes_per_sec": download_speed,
            "eta_seconds": eta_seconds,
            "file_path": str(base_path) if base_path else None,
        }

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
            # Get torrents (filter by category if set)
            torrents = self._proxy.get_torrents()

            items = []
            for torrent in torrents:
                hash_str = torrent.get("hash", "")
                if not hash_str:
                    continue

                # Filter by category if set
                if self.settings.category:
                    label = torrent.get("label", "")
                    if label != self.settings.category:
                        continue

                item = self._build_download_item(torrent)
                items.append(item)
        except Exception as e:
            msg = f"Failed to get downloads from rTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:  # noqa: ARG002
        """Remove a download from rTorrent.

        Parameters
        ----------
        client_item_id : str
            Torrent hash.
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
            msg = "rTorrent client is disabled"
            raise PVRProviderError(msg)

        try:
            self._proxy.remove_torrent(client_item_id.lower())
        except Exception as e:
            msg = f"Failed to remove download from rTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def test_connection(self) -> bool:
        """Test connectivity to rTorrent.

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
            logger.debug("rTorrent version: %s", version)
        except Exception as e:
            msg = f"Failed to connect to rTorrent: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

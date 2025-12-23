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

"""Complete XML-RPC client for PVR download clients.

This module provides a complete XML-RPC client implementation following DRY
principles by consolidating XML-RPC request/response handling used across
multiple download clients.
"""

from contextlib import suppress
from typing import Any

import httpx

from bookcard.pvr.download_clients._http_client import (
    create_httpx_client,
    handle_httpx_exception,
)
from bookcard.pvr.error_handlers import handle_http_error_response
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.xmlrpc import XmlRpcBuilder, XmlRpcParser


class XmlRpcClient:
    """Complete XML-RPC client with request/response handling.

    This class consolidates XML-RPC logic following DRY principles,
    providing a complete client for XML-RPC communication.

    Parameters
    ----------
    url : str
        XML-RPC endpoint URL.
    timeout_seconds : int
        Request timeout in seconds (default: 30).
    auth : tuple[str, str] | None
        Optional HTTP basic auth credentials (username, password).
    rpc_token : str | None
        Optional RPC token to prepend to all method calls.

    Examples
    --------
    >>> client = XmlRpcClient(
    ...     "http://localhost:8080/RPC2"
    ... )
    >>> version = client.call(
    ...     "system.getVersion"
    ... )
    >>> client.call(
    ...     "download.add",
    ...     "magnet:?xt=urn:btih:...",
    ... )
    """

    def __init__(
        self,
        url: str,
        timeout_seconds: int = 30,
        auth: tuple[str, str] | None = None,
        rpc_token: str | None = None,
    ) -> None:
        """Initialize XML-RPC client.

        Parameters
        ----------
        url : str
            XML-RPC endpoint URL.
        timeout_seconds : int
            Request timeout in seconds.
        auth : tuple[str, str] | None
            Optional HTTP basic auth credentials.
        rpc_token : str | None
            Optional RPC token to prepend to all method calls.
        """
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.auth = auth
        self.rpc_token = rpc_token
        self.builder = XmlRpcBuilder()
        self.parser = XmlRpcParser()

    def _get_client(self) -> httpx.Client:
        """Get configured HTTP client.

        Returns
        -------
        httpx.Client
            Configured HTTP client.
        """
        return create_httpx_client(
            timeout=self.timeout_seconds,
            verify=True,
            follow_redirects=True,
        )

    def call(
        self,
        method: str,
        *params: str | bytes | int | list[str | int] | dict[str, str | int | None],
    ) -> Any:  # noqa: ANN401
        """Call XML-RPC method.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : str | bytes | int | list[str | int] | dict[str, str | int | None]
            Method parameters.

        Returns
        -------
        Any
            Parsed response value.

        Raises
        ------
        PVRProviderError
            If the RPC call fails or response cannot be parsed.
        """
        xml_request = self.builder.build_request(
            method, *params, rpc_token=self.rpc_token
        )

        try:
            with self._get_client() as client:
                response = client.post(
                    self.url,
                    content=xml_request,
                    headers={"Content-Type": "text/xml"},
                    auth=self.auth,
                )

                if response.status_code >= 400:
                    response_text = ""
                    with suppress(Exception):
                        response_text = response.text[:200]
                    handle_http_error_response(response.status_code, response_text)

                return self.parser.parse_response(response.text)

        except httpx.HTTPError as e:
            handle_httpx_exception(e, f"XML-RPC call to {method}")
            raise
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error during XML-RPC call {method}: {e}"
            raise PVRProviderError(msg) from e

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

"""Response classes for bypass client."""

from collections.abc import Iterator
from urllib.parse import urlparse

import httpx

from bookcard.pvr.download_clients.direct_http.bypass.constants import BypassConstants


class BypassResponse:
    """Wrapper for bypass response to match StreamingResponse protocol.

    Parameters
    ----------
    status_code : int
        HTTP status code.
    text : str
        Response body as text.
    headers : httpx.Headers | dict[str, str] | None
        Response headers.
    url : str | None
        Request URL.
    """

    def __init__(
        self,
        status_code: int,
        text: str,
        headers: httpx.Headers | dict[str, str] | None = None,
        url: str | None = None,
    ) -> None:
        self._status_code = status_code
        self._text = text
        self._url = url or ""
        if isinstance(headers, dict):
            self._headers = httpx.Headers(headers)
        elif headers is None:
            self._headers = httpx.Headers()
        else:
            self._headers = headers

    @property
    def headers(self) -> httpx.Headers:
        """Return response headers.

        Returns
        -------
        httpx.Headers
            Response headers.
        """
        return self._headers

    @property
    def status_code(self) -> int:
        """Return status code.

        Returns
        -------
        int
            HTTP status code.
        """
        return self._status_code

    @property
    def text(self) -> str:
        """Return response text.

        Returns
        -------
        str
            Response body as text.
        """
        return self._text

    def raise_for_status(self) -> None:
        """Raise exception if status code is error."""
        if 400 <= self._status_code < 600:
            request = httpx.Request("GET", self._url)
            response = httpx.Response(self._status_code, request=request)
            error_msg = f"HTTP {self._status_code}"
            raise httpx.HTTPStatusError(
                error_msg,
                request=request,
                response=response,
            )

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """Iterate over response bytes.

        Parameters
        ----------
        chunk_size : int | None
            Size of each chunk. Defaults to DEFAULT_CHUNK_SIZE.

        Yields
        ------
        bytes
            Chunks of response bytes.
        """
        if chunk_size is None:
            chunk_size = BypassConstants.DEFAULT_CHUNK_SIZE
        text_bytes = self._text.encode("utf-8")
        for i in range(0, len(text_bytes), chunk_size):
            yield text_bytes[i : i + chunk_size]


class BypassResponseFactory:
    """Factory for creating BypassResponse instances."""

    @staticmethod
    def create_error(
        url: str,
        status_code: int = BypassConstants.HTTP_STATUS_SERVICE_UNAVAILABLE,
    ) -> BypassResponse:
        """Create error response.

        Parameters
        ----------
        url : str
            Request URL.
        status_code : int
            HTTP status code for error. Defaults to 503.

        Returns
        -------
        BypassResponse
            Error response instance.
        """
        return BypassResponse(
            status_code=status_code,
            text="",
            headers={},
            url=url,
        )

    @staticmethod
    def create_success(url: str, html: str) -> BypassResponse:
        """Create success response.

        Parameters
        ----------
        url : str
            Request URL.
        html : str
            HTML content.

        Returns
        -------
        BypassResponse
            Success response instance.
        """
        parsed = urlparse(url)
        headers = {
            "Content-Type": BypassConstants.CONTENT_TYPE_HTML,
            "Host": parsed.netloc or "",
        }
        return BypassResponse(
            status_code=BypassConstants.HTTP_STATUS_OK,
            text=html,
            headers=headers,
            url=url,
        )

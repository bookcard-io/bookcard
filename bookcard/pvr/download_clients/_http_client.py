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

"""Shared HTTP client utilities for download clients.

This module provides reusable HTTP client functionality following DRY principles.
"""

import logging
from contextlib import suppress
from urllib.parse import urljoin

import httpx

from bookcard.pvr.error_handlers import handle_http_error_response
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderNetworkError,
    PVRProviderTimeoutError,
)

logger = logging.getLogger(__name__)


def build_base_url(
    host: str, port: int, use_ssl: bool, url_base: str | None = None
) -> str:
    """Build base URL for download client.

    Parameters
    ----------
    host : str
        Hostname or IP address.
    port : int
        Port number.
    use_ssl : bool
        Whether to use HTTPS.
    url_base : str | None
        Optional URL base path.

    Returns
    -------
    str
        Base URL string.
    """
    host = host.strip()

    # Strip protocol if user included it in the host field
    if host.lower().startswith("http://"):
        host = host[7:]
    elif host.lower().startswith("https://"):
        host = host[8:]

    # Strip trailing slashes
    host = host.rstrip("/")

    scheme = "https" if use_ssl else "http"
    base = f"{scheme}://{host}:{port}"
    if url_base:
        url_base = url_base.strip("/")
        if url_base:
            base = urljoin(base, f"/{url_base}/")
    return base


def create_httpx_client(
    timeout: int,
    verify: bool = True,
    follow_redirects: bool = True,
) -> httpx.Client:
    """Create configured httpx client.

    Parameters
    ----------
    timeout : int
        Request timeout in seconds.
    verify : bool
        Whether to verify SSL certificates (default: True).
    follow_redirects : bool
        Whether to follow redirects (default: True).

    Returns
    -------
    httpx.Client
        Configured HTTP client.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    return httpx.Client(
        timeout=timeout,
        verify=verify,
        follow_redirects=follow_redirects,
        headers=headers,
    )


def handle_httpx_exception(error: Exception, context: str = "Request") -> None:
    """Handle httpx exceptions and raise appropriate PVR exceptions.

    Parameters
    ----------
    error : Exception
        The httpx exception to handle.
    context : str
        Context description for error messages.

    Raises
    ------
    PVRProviderTimeoutError
        If request timed out.
    PVRProviderAuthenticationError
        If authentication failed.
    PVRProviderNetworkError
        For other network errors.
    """
    if isinstance(error, httpx.TimeoutException):
        msg = f"{context} timed out: {error}"
        raise PVRProviderTimeoutError(msg) from error

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        response_text = ""
        with suppress(Exception):
            response_text = error.response.text[:200]

        if status_code in (401, 403):
            auth_failed_msg = f"{context} authentication failed: HTTP {status_code}"
            raise PVRProviderAuthenticationError(auth_failed_msg) from error

        handle_http_error_response(status_code, response_text)
        return

    if isinstance(error, httpx.RequestError):
        msg = f"{context} failed: {error}"
        raise PVRProviderNetworkError(msg) from error

    # Fallback for unknown exceptions
    msg = f"{context} error: {error}"
    raise PVRProviderNetworkError(msg) from error

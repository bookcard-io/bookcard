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

"""Error handling utilities for PVR providers.

This module provides reusable error handling functions following DRY principles.
"""

from collections.abc import Generator
from contextlib import contextmanager, suppress

import httpx

from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
)


def handle_api_error_response(
    error_code: int, description: str, provider_name: str = "Indexer"
) -> None:
    """Handle API error response and raise appropriate exception.

    Parameters
    ----------
    error_code : int
        Error code from API response.
    description : str
        Error description from API response.
    provider_name : str
        Name of the provider (for error messages).

    Raises
    ------
    PVRProviderAuthenticationError
        If error code is 100-199 (authentication errors).
    PVRProviderError
        For other API errors.
    """
    if 100 <= error_code <= 199:
        error_msg = f"Invalid API key: {description}"
        raise PVRProviderAuthenticationError(error_msg)

    if description == "Request limit reached":
        error_msg = f"API limit reached: {description}"
        raise PVRProviderError(error_msg)

    error_msg = f"{provider_name} error: {description}"
    raise PVRProviderError(error_msg)


def handle_http_error_response(status_code: int, response_text: str = "") -> None:
    """Handle HTTP error response and raise appropriate exception.

    Parameters
    ----------
    status_code : int
        HTTP status code.
    response_text : str
        Response text (truncated to 200 chars).

    Raises
    ------
    PVRProviderAuthenticationError
        If status code is 401 or 403.
    PVRProviderNetworkError
        For other HTTP errors (>= 400).
    """
    if status_code == 401:
        msg = "Unauthorized"
        raise PVRProviderAuthenticationError(msg)
    if status_code == 403:
        msg = "Forbidden"
        raise PVRProviderAuthenticationError(msg)
    if status_code >= 400:
        error_msg = f"HTTP {status_code}: {response_text[:200]}"
        raise PVRProviderNetworkError(error_msg)


@contextmanager
def handle_http_errors(context: str = "Request") -> Generator[None, None, None]:
    """Context manager for handling HTTP errors consistently.

    This context manager wraps HTTP operations and automatically handles
    httpx exceptions, converting them to appropriate PVR exceptions.

    Parameters
    ----------
    context : str
        Context description for error messages (e.g., "qBittorrent API").

    Yields
    ------
    None
        Yields control to the wrapped code block.

    Raises
    ------
    PVRProviderAuthenticationError
        If HTTP status is 401 or 403.
    PVRProviderNetworkError
        For other network errors.
    PVRProviderTimeoutError
        If request times out.

    Examples
    --------
    >>> with handle_http_errors(
    ...     "qBittorrent API"
    ... ):
    ...     response = (
    ...         client.get(
    ...             url
    ...         )
    ...     )
    """
    try:
        yield
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        response_text = ""
        with suppress(Exception):
            response_text = e.response.text[:200]

        if status_code in (401, 403):
            msg = f"{context} authentication failed"
            raise PVRProviderAuthenticationError(msg) from e
        handle_http_error_response(status_code, response_text)
        raise
    except httpx.TimeoutException as e:
        msg = f"{context} timed out: {e}"
        from bookcard.pvr.exceptions import PVRProviderTimeoutError

        raise PVRProviderTimeoutError(msg) from e
    except httpx.RequestError as e:
        msg = f"{context} failed: {e}"
        raise PVRProviderNetworkError(msg) from e

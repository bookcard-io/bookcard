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

"""HTTP client implementations for PVR system.

This module provides concrete HTTP client implementations following DIP
by implementing the HttpClientProtocol interface.
"""

from typing import Any, Self

import httpx


class HttpxClient:
    """httpx-based HTTP client implementation.

    This class wraps httpx.Client to implement HttpClientProtocol,
    allowing it to be used interchangeably with other HTTP client
    implementations.

    Parameters
    ----------
    timeout : int
        Request timeout in seconds.
    verify : bool
        Whether to verify SSL certificates (default: True).
    follow_redirects : bool
        Whether to follow redirects (default: True).

    Examples
    --------
    >>> client = (
    ...     HttpxClient(
    ...         timeout=30
    ...     )
    ... )
    >>> with client:
    ...     response = client.get(
    ...         "https://example.com"
    ...     )
    """

    def __init__(
        self,
        timeout: int,
        verify: bool = True,
        follow_redirects: bool = True,
    ) -> None:
        """Initialize httpx client.

        Parameters
        ----------
        timeout : int
            Request timeout in seconds.
        verify : bool
            Whether to verify SSL certificates.
        follow_redirects : bool
            Whether to follow redirects.
        """
        self._client = httpx.Client(
            timeout=timeout,
            verify=verify,
            follow_redirects=follow_redirects,
        )

    def get(self, url: str, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        """Perform GET request.

        Parameters
        ----------
        url : str
            Request URL.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        httpx.Response
            HTTP response.
        """
        return self._client.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        """Perform POST request.

        Parameters
        ----------
        url : str
            Request URL.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        httpx.Response
            HTTP response.
        """
        return self._client.post(url, **kwargs)

    def stream(self, method: str, url: str, **kwargs: Any) -> Any:  # noqa: ANN401
        """Stream HTTP response.

        Parameters
        ----------
        method : str
            HTTP method.
        url : str
            Request URL.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        Any
            Streaming context manager.
        """
        return self._client.stream(method, url, **kwargs)

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self._client.close()


# Type alias for backward compatibility
HttpClient = HttpxClient

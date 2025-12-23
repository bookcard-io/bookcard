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

"""HTTP client protocol for dependency injection.

This module defines the HTTP client protocol interface following DIP
by allowing implementations to be swapped without modifying client code.
"""

from typing import Any, Protocol


class HttpClientProtocol(Protocol):
    """Protocol for HTTP client implementations.

    This protocol defines the interface that HTTP clients must implement,
    allowing different implementations (httpx, requests, etc.) to be used
    interchangeably.

    Methods
    -------
    get(url, **kwargs)
        Perform GET request.
    post(url, **kwargs)
        Perform POST request.
    """

    def get(self, url: str, **kwargs: Any) -> Any:  # noqa: ANN401
        """Perform GET request.

        Parameters
        ----------
        url : str
            Request URL.
        **kwargs : Any
            Additional request parameters (headers, params, cookies, etc.).

        Returns
        -------
        Any
            Response object with status_code, text, content, cookies attributes.
        """
        ...

    def post(self, url: str, **kwargs: Any) -> Any:  # noqa: ANN401
        """Perform POST request.

        Parameters
        ----------
        url : str
            Request URL.
        **kwargs : Any
            Additional request parameters (headers, data, files, cookies, etc.).

        Returns
        -------
        Any
            Response object with status_code, text, content, cookies attributes.
        """
        ...

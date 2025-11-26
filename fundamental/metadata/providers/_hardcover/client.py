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

"""HTTP client for Hardcover GraphQL API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import httpx

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = __import__("logging").getLogger(__name__)


class HttpClient(Protocol):
    """Protocol for HTTP client interface."""

    def post(
        self,
        url: str,
        *,
        json: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make a POST request."""
        ...


class HardcoverGraphQLClient:
    """Handles HTTP communication with Hardcover GraphQL API.

    This class encapsulates all HTTP/GraphQL communication concerns,
    making it easy to test and swap implementations.
    """

    def __init__(
        self,
        endpoint: str,
        bearer_token: str,
        timeout: int = 10,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize GraphQL client.

        Parameters
        ----------
        endpoint : str
            GraphQL API endpoint URL.
        bearer_token : str
            API bearer token for authentication.
        timeout : int
            Request timeout in seconds.
        http_client : HttpClient | None
            HTTP client to use. If None, creates a new httpx client.
        """
        self.endpoint = endpoint
        self.bearer_token = bearer_token
        self.timeout = timeout
        self._http_client = http_client or httpx

    def execute_query(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        operation_name: str | None = None,
    ) -> dict:
        """Execute a GraphQL query and return the response data.

        Parameters
        ----------
        query : str
            GraphQL query string.
        variables : dict[str, object] | None
            GraphQL query variables.
        operation_name : str | None
            Operation name for the query.

        Returns
        -------
        dict
            Parsed JSON response data.

        Raises
        ------
        MetadataProviderNetworkError
            If network request fails or bearer token is missing.
        MetadataProviderParseError
            If the response contains GraphQL errors.
        """
        if not self.bearer_token:
            msg = (
                "Hardcover API bearer token is required. "
                "Set HARDCOVER_API_TOKEN environment variable."
            )
            raise MetadataProviderNetworkError(msg)

        # Sanitize bearer token: remove any existing "Bearer " prefix and add it back
        token = self.bearer_token.strip()
        if token.startswith("Bearer "):
            token = token[7:]  # Remove "Bearer " prefix
        auth_header = f"Bearer {token}"

        headers = {
            "Content-Type": "application/json",
            "authorization": auth_header,
        }

        payload: dict[str, object] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        try:
            response = self._http_client.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_messages = [
                    err.get("message", "Unknown error") for err in data["errors"]
                ]
                msg = f"Hardcover GraphQL API errors: {', '.join(error_messages)}"
                raise MetadataProviderParseError(msg)
        except httpx.TimeoutException as e:
            msg = f"Hardcover API request timed out: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except httpx.RequestError as e:
            msg = f"Hardcover API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        else:
            return data

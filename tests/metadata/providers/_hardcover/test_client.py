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

"""Tests for Hardcover GraphQL client to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from bookcard.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)
from bookcard.metadata.providers._hardcover.client import (
    HardcoverGraphQLClient,
    HttpClient,
)


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create a mock HTTP client."""
    return MagicMock(spec=HttpClient)


@pytest.fixture
def graphql_client(mock_http_client: MagicMock) -> HardcoverGraphQLClient:
    """Create a HardcoverGraphQLClient with mocked HTTP client."""
    return HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="test-token",
        timeout=10,
        http_client=mock_http_client,
    )


@pytest.fixture
def graphql_client_default() -> HardcoverGraphQLClient:
    """Create a HardcoverGraphQLClient with default HTTP client."""
    return HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="test-token",
        timeout=10,
    )


@pytest.fixture
def graphql_client_token_with_bearer() -> HardcoverGraphQLClient:
    """Create a HardcoverGraphQLClient with token that already has Bearer prefix."""
    return HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="Bearer test-token",
        timeout=10,
    )


@pytest.fixture
def graphql_client_empty_token() -> HardcoverGraphQLClient:
    """Create a HardcoverGraphQLClient with empty token."""
    return HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="",
        timeout=10,
    )


@pytest.fixture
def graphql_client_whitespace_token(
    mock_http_client: MagicMock,
) -> HardcoverGraphQLClient:
    """Create a HardcoverGraphQLClient with whitespace-only token."""
    return HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="   ",
        timeout=10,
        http_client=mock_http_client,
    )


@pytest.fixture
def successful_response() -> MagicMock:
    """Create a mock successful HTTP response."""
    response = MagicMock()
    response.json.return_value = {"data": {"test": "value"}}
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def error_response() -> MagicMock:
    """Create a mock HTTP response with GraphQL errors."""
    response = MagicMock()
    response.json.return_value = {
        "errors": [
            {"message": "Error 1"},
            {"message": "Error 2"},
        ]
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def error_response_no_message() -> MagicMock:
    """Create a mock HTTP response with GraphQL errors without messages."""
    response = MagicMock()
    response.json.return_value = {"errors": [{}]}
    response.raise_for_status = MagicMock()
    return response


def test_client_init_with_custom_http_client(
    mock_http_client: MagicMock,
) -> None:
    """Test client initialization with custom HTTP client (covers lines 57-80)."""
    client = HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="test-token",
        timeout=5,
        http_client=mock_http_client,
    )
    assert client.endpoint == "https://api.hardcover.app/graphql"
    assert client.bearer_token == "test-token"
    assert client.timeout == 5
    assert client._http_client == mock_http_client


def test_client_init_with_default_http_client() -> None:
    """Test client initialization with default HTTP client (covers lines 57-80)."""
    client = HardcoverGraphQLClient(
        endpoint="https://api.hardcover.app/graphql",
        bearer_token="test-token",
    )
    assert client.endpoint == "https://api.hardcover.app/graphql"
    assert client.bearer_token == "test-token"
    assert client.timeout == 10
    assert client._http_client == httpx


@pytest.mark.parametrize(
    ("token", "expected_header"),
    [
        ("test-token", "Bearer test-token"),
        ("Bearer test-token", "Bearer test-token"),
        ("Bearer Bearer test-token", "Bearer Bearer test-token"),
    ],
)
def test_execute_query_token_sanitization(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    successful_response: MagicMock,
    token: str,
    expected_header: str,
) -> None:
    """Test token sanitization in execute_query (covers lines 118-122)."""
    graphql_client.bearer_token = token
    mock_http_client.post.return_value = successful_response

    graphql_client.execute_query("query { test }")

    call_args = mock_http_client.post.call_args
    assert call_args is not None
    headers = call_args.kwargs.get("headers", {})
    assert headers.get("authorization") == expected_header


def test_execute_query_empty_token(
    graphql_client_empty_token: HardcoverGraphQLClient,
) -> None:
    """Test execute_query raises error with empty token (covers lines 111-116)."""
    with pytest.raises(MetadataProviderNetworkError) as exc_info:
        graphql_client_empty_token.execute_query("query { test }")
    assert "bearer token is required" in str(exc_info.value).lower()


def test_execute_query_whitespace_token(
    graphql_client_whitespace_token: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
) -> None:
    """Test execute_query raises error with whitespace-only token (covers lines 111-116)."""
    # Whitespace token passes the initial check but fails when creating header
    mock_http_client.post.side_effect = httpx.RequestError("Illegal header value")
    with pytest.raises(MetadataProviderNetworkError) as exc_info:
        graphql_client_whitespace_token.execute_query("query { test }")
    assert "request failed" in str(exc_info.value).lower()


def test_execute_query_success(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    successful_response: MagicMock,
) -> None:
    """Test successful query execution (covers lines 135-158)."""
    mock_http_client.post.return_value = successful_response

    result = graphql_client.execute_query("query { test }")

    assert result == {"data": {"test": "value"}}
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert call_args is not None
    assert call_args.kwargs["json"] == {"query": "query { test }"}
    assert call_args.kwargs["headers"]["Content-Type"] == "application/json"
    assert call_args.kwargs["headers"]["authorization"] == "Bearer test-token"
    assert call_args.kwargs["timeout"] == 10


def test_execute_query_with_variables(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    successful_response: MagicMock,
) -> None:
    """Test query execution with variables (covers lines 130-131)."""
    mock_http_client.post.return_value = successful_response

    graphql_client.execute_query("query { test }", variables={"var1": "value1"})

    call_args = mock_http_client.post.call_args
    assert call_args is not None
    payload = call_args.kwargs["json"]
    assert payload["query"] == "query { test }"
    assert payload["variables"] == {"var1": "value1"}


def test_execute_query_with_operation_name(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    successful_response: MagicMock,
) -> None:
    """Test query execution with operation name (covers lines 132-133)."""
    mock_http_client.post.return_value = successful_response

    graphql_client.execute_query("query { test }", operation_name="TestOperation")

    call_args = mock_http_client.post.call_args
    assert call_args is not None
    payload = call_args.kwargs["json"]
    assert payload["query"] == "query { test }"
    assert payload["operationName"] == "TestOperation"


def test_execute_query_with_variables_and_operation_name(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    successful_response: MagicMock,
) -> None:
    """Test query execution with both variables and operation name."""
    mock_http_client.post.return_value = successful_response

    graphql_client.execute_query(
        "query { test }",
        variables={"var1": "value1"},
        operation_name="TestOperation",
    )

    call_args = mock_http_client.post.call_args
    assert call_args is not None
    payload = call_args.kwargs["json"]
    assert payload["query"] == "query { test }"
    assert payload["variables"] == {"var1": "value1"}
    assert payload["operationName"] == "TestOperation"


def test_execute_query_graphql_errors(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    error_response: MagicMock,
) -> None:
    """Test query execution with GraphQL errors (covers lines 145-150)."""
    mock_http_client.post.return_value = error_response

    with pytest.raises(MetadataProviderParseError) as exc_info:
        graphql_client.execute_query("query { test }")
    assert "Error 1" in str(exc_info.value)
    assert "Error 2" in str(exc_info.value)


def test_execute_query_graphql_errors_no_message(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
    error_response_no_message: MagicMock,
) -> None:
    """Test query execution with GraphQL errors without messages (covers lines 145-150)."""
    mock_http_client.post.return_value = error_response_no_message

    with pytest.raises(MetadataProviderParseError) as exc_info:
        graphql_client.execute_query("query { test }")
    assert "Unknown error" in str(exc_info.value)


def test_execute_query_timeout_exception(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
) -> None:
    """Test query execution with timeout exception (covers lines 151-153)."""
    mock_http_client.post.side_effect = httpx.TimeoutException("Timeout")

    with pytest.raises(MetadataProviderNetworkError) as exc_info:
        graphql_client.execute_query("query { test }")
    assert "timed out" in str(exc_info.value).lower()


def test_execute_query_request_error(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
) -> None:
    """Test query execution with request error (covers lines 154-156)."""
    mock_http_client.post.side_effect = httpx.RequestError("Request failed")

    with pytest.raises(MetadataProviderNetworkError) as exc_info:
        graphql_client.execute_query("query { test }")
    assert "request failed" in str(exc_info.value).lower()


def test_execute_query_http_error(
    graphql_client: HardcoverGraphQLClient,
    mock_http_client: MagicMock,
) -> None:
    """Test query execution with HTTP error status (covers line 142)."""
    response = MagicMock()
    response.json.return_value = {"data": {"test": "value"}}
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=response
    )
    mock_http_client.post.return_value = response

    with pytest.raises(httpx.HTTPStatusError):
        graphql_client.execute_query("query { test }")

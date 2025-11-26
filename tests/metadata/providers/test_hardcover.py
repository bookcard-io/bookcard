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

"""Tests for Hardcover metadata provider to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from fundamental.metadata.providers.hardcover import HardcoverProvider


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create a mock HTTP client."""
    return MagicMock()


@pytest.fixture
def hardcover_provider(mock_http_client: MagicMock) -> HardcoverProvider:
    """Create a HardcoverProvider instance for testing."""
    return HardcoverProvider(
        enabled=True,
        bearer_token="test-token",
        http_client=mock_http_client,
    )


@pytest.fixture
def hardcover_provider_disabled() -> HardcoverProvider:
    """Create a disabled HardcoverProvider instance for testing."""
    return HardcoverProvider(enabled=False, bearer_token="test-token")


@pytest.fixture
def hardcover_provider_no_token() -> HardcoverProvider:
    """Create a HardcoverProvider instance without bearer token."""
    return HardcoverProvider(enabled=True, bearer_token="")


@pytest.fixture
def hardcover_provider_custom_timeout(mock_http_client: MagicMock) -> HardcoverProvider:
    """Create a HardcoverProvider instance with custom timeout."""
    return HardcoverProvider(
        enabled=True,
        bearer_token="test-token",
        timeout=15,
        http_client=mock_http_client,
    )


@pytest.fixture
def mock_search_response() -> dict:
    """Create a mock Hardcover search response."""
    return {
        "data": {
            "search": {
                "results": {
                    "hits": [
                        {
                            "document": {
                                "id": 1,
                                "title": "Test Book 1",
                                "contributions": [{"author": {"name": "Author 1"}}],
                            }
                        },
                        {
                            "document": {
                                "id": 2,
                                "title": "Test Book 2",
                                "contributions": [{"author": {"name": "Author 2"}}],
                            }
                        },
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_edition_response() -> dict:
    """Create a mock Hardcover edition response."""
    return {
        "data": {
            "books": [
                {
                    "id": 1,
                    "description": "Enhanced description",
                    "book_series": [
                        {
                            "position": 1,
                            "series": {"name": "Test Series"},
                        }
                    ],
                    "editions": [
                        {
                            "isbn_13": "9781234567890",
                            "image": {"url": "https://example.com/cover.jpg"},
                        }
                    ],
                }
            ]
        }
    }


def test_hardcover_provider_init(mock_http_client: MagicMock) -> None:
    """Test HardcoverProvider initialization (covers lines 80-124)."""
    provider = HardcoverProvider(
        enabled=True,
        bearer_token="test-token",
        timeout=15,
        http_client=mock_http_client,
    )
    assert provider.is_enabled() is True
    assert provider.timeout == 15
    assert provider.bearer_token == "test-token"


def test_hardcover_provider_init_no_token() -> None:
    """Test initialization without bearer token (covers lines 105-111)."""
    with (
        patch("fundamental.metadata.providers.hardcover.logger") as mock_logger,
        patch(
            "fundamental.metadata.providers.hardcover.HardcoverProvider.DEFAULT_BEARER_TOKEN",
            "",
        ),
    ):
        provider = HardcoverProvider(enabled=True, bearer_token="")
        assert provider.is_enabled() is False
        mock_logger.warning.assert_called_once()


def test_hardcover_provider_init_no_token_disabled() -> None:
    """Test initialization without bearer token when already disabled (covers lines 105-111)."""
    with (
        patch("fundamental.metadata.providers.hardcover.logger") as mock_logger,
        patch(
            "fundamental.metadata.providers.hardcover.HardcoverProvider.DEFAULT_BEARER_TOKEN",
            "",
        ),
    ):
        provider = HardcoverProvider(enabled=False, bearer_token="")
        assert provider.is_enabled() is False
        mock_logger.warning.assert_not_called()


def test_hardcover_provider_get_source_info(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test get_source_info (covers lines 126-139)."""
    source_info = hardcover_provider.get_source_info()
    assert source_info.id == "hardcover"
    assert source_info.name == "Hardcover"
    assert source_info.description == "Hardcover GraphQL API"
    assert source_info.base_url == "https://hardcover.app"


def test_hardcover_provider_search_disabled(
    hardcover_provider_disabled: HardcoverProvider,
) -> None:
    """Test search returns empty when disabled (covers lines 173-174)."""
    result = hardcover_provider_disabled.search("test query")
    assert result == []


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "\t\n",
    ],
)
def test_hardcover_provider_search_empty_query(
    hardcover_provider: HardcoverProvider,
    query: str,
) -> None:
    """Test search returns empty for empty query (covers lines 176-177)."""
    result = hardcover_provider.search(query)
    assert result == []


def test_hardcover_provider_search_success(
    hardcover_provider: HardcoverProvider,
    mock_search_response: dict,
    mock_edition_response: dict,
) -> None:
    """Test successful search (covers lines 179-211)."""
    # Mock client responses - need one for search and one for each book's edition
    mock_edition_response_2 = {
        "data": {
            "books": [
                {
                    "id": 2,
                    "description": "Book 2 description",
                    "editions": [],
                }
            ]
        }
    }
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=[
            mock_search_response,
            mock_edition_response,
            mock_edition_response_2,
        ]
    )

    results = hardcover_provider.search("test query", max_results=10)

    assert len(results) == 2
    assert results[0].title == "Test Book 1"
    assert results[0].authors == ["Author 1"]
    assert results[1].title == "Test Book 2"
    assert results[1].authors == ["Author 2"]


def test_hardcover_provider_search_no_results(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with no results (covers lines 191-192)."""
    mock_response = {"data": {"search": {"results": {"hits": []}}}}
    hardcover_provider._client.execute_query = MagicMock(return_value=mock_response)  # type: ignore[assignment]

    results = hardcover_provider.search("test query")
    assert results == []


def test_hardcover_provider_search_timeout(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with timeout exception (covers lines 201-203)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=httpx.TimeoutException("Timeout")
    )

    with pytest.raises(MetadataProviderTimeoutError) as exc_info:
        hardcover_provider.search("test query")
    assert "timed out" in str(exc_info.value).lower()


def test_hardcover_provider_search_request_error(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with request error (covers lines 204-206)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=httpx.RequestError("Request failed")
    )

    with pytest.raises(MetadataProviderNetworkError) as exc_info:
        hardcover_provider.search("test query")
    assert "request failed" in str(exc_info.value).lower()


def test_hardcover_provider_search_parse_error_keyerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with KeyError parse error (covers lines 207-209)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=KeyError("Missing key")
    )

    with pytest.raises(MetadataProviderParseError) as exc_info:
        hardcover_provider.search("test query")
    assert "failed to parse" in str(exc_info.value).lower()


def test_hardcover_provider_search_parse_error_valueerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with ValueError parse error (covers lines 207-209)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("Invalid value")
    )

    with pytest.raises(MetadataProviderParseError) as exc_info:
        hardcover_provider.search("test query")
    assert "failed to parse" in str(exc_info.value).lower()


def test_hardcover_provider_search_parse_error_typeerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test search with TypeError parse error (covers lines 207-209)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=TypeError("Type error")
    )

    with pytest.raises(MetadataProviderParseError) as exc_info:
        hardcover_provider.search("test query")
    assert "failed to parse" in str(exc_info.value).lower()


def test_hardcover_provider_search_max_results(
    hardcover_provider: HardcoverProvider,
    mock_search_response: dict,
    mock_edition_response: dict,
) -> None:
    """Test search respects max_results limit."""
    # Create response with 3 books
    mock_search_response["data"]["search"]["results"]["hits"].append({
        "document": {
            "id": 3,
            "title": "Test Book 3",
            "contributions": [{"author": {"name": "Author 3"}}],
        }
    })
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=[mock_search_response, mock_edition_response, mock_edition_response]
    )

    results = hardcover_provider.search("test query", max_results=2)
    assert len(results) == 2


def test_enrich_books_with_editions_success(
    hardcover_provider: HardcoverProvider,
    mock_edition_response: dict,
) -> None:
    """Test enriching books with edition details (covers lines 226-240)."""
    books_data = [
        {"id": 1, "title": "Book 1"},
        {"id": 2, "title": "Book 2"},
    ]
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        return_value=mock_edition_response
    )

    enriched = hardcover_provider._enrich_books_with_editions(books_data)

    assert len(enriched) == 2
    assert "editions" in enriched[0]
    assert enriched[1]["title"] == "Book 2"


def test_enrich_books_with_editions_no_edition_data(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test enriching books when edition fetch returns None (covers lines 236-237)."""
    books_data = [{"id": 1, "title": "Book 1"}]
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        return_value={"data": {"books": []}}
    )

    enriched = hardcover_provider._enrich_books_with_editions(books_data)

    assert len(enriched) == 1
    assert enriched[0]["title"] == "Book 1"


def test_enrich_books_with_editions_no_id(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test enriching books without id (covers lines 238-239)."""
    books_data = [{"title": "Book 1"}]
    # Mock the client to track calls
    mock_execute = MagicMock()
    hardcover_provider._client.execute_query = mock_execute  # type: ignore[assignment]

    enriched = hardcover_provider._enrich_books_with_editions(books_data)

    assert len(enriched) == 1
    assert enriched[0]["title"] == "Book 1"
    mock_execute.assert_not_called()


def test_fetch_edition_details_success(
    hardcover_provider: HardcoverProvider,
    mock_edition_response: dict,
) -> None:
    """Test fetching edition details successfully (covers lines 255-262)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        return_value=mock_edition_response
    )

    result = hardcover_provider._fetch_edition_details(1)

    assert result is not None
    assert result["id"] == 1
    assert "editions" in result


def test_fetch_edition_details_string_id(
    hardcover_provider: HardcoverProvider,
    mock_edition_response: dict,
) -> None:
    """Test fetching edition details with string ID (covers lines 255-262)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        return_value=mock_edition_response
    )

    result = hardcover_provider._fetch_edition_details("1")

    assert result is not None
    hardcover_provider._client.execute_query.assert_called_once()
    call_args = hardcover_provider._client.execute_query.call_args
    assert call_args is not None
    assert call_args.kwargs["variables"]["bookId"] == 1


def test_fetch_edition_details_valueerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test fetching edition details with ValueError (covers lines 263-273)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("Invalid ID")
    )

    with patch("fundamental.metadata.providers.hardcover.logger") as mock_logger:
        result = hardcover_provider._fetch_edition_details("invalid")
        assert result is None
        mock_logger.warning.assert_called_once()


def test_fetch_edition_details_typeerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test fetching edition details with TypeError (covers lines 263-273)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=TypeError("Type error")
    )

    with patch("fundamental.metadata.providers.hardcover.logger") as mock_logger:
        result = hardcover_provider._fetch_edition_details(1)
        assert result is None
        mock_logger.warning.assert_called_once()


def test_fetch_edition_details_keyerror(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test fetching edition details with KeyError (covers lines 263-273)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=KeyError("Missing key")
    )

    with patch("fundamental.metadata.providers.hardcover.logger") as mock_logger:
        result = hardcover_provider._fetch_edition_details(1)
        assert result is None
        mock_logger.warning.assert_called_once()


def test_fetch_edition_details_parse_error(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test fetching edition details with MetadataProviderParseError (covers lines 263-273)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=MetadataProviderParseError("Parse error")
    )

    with patch("fundamental.metadata.providers.hardcover.logger") as mock_logger:
        result = hardcover_provider._fetch_edition_details(1)
        assert result is None
        mock_logger.warning.assert_called_once()


def test_fetch_edition_details_network_error(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test fetching edition details with MetadataProviderNetworkError (covers lines 263-273)."""
    hardcover_provider._client.execute_query = MagicMock(  # type: ignore[assignment]
        side_effect=MetadataProviderNetworkError("Network error")
    )

    with patch("fundamental.metadata.providers.hardcover.logger") as mock_logger:
        result = hardcover_provider._fetch_edition_details(1)
        assert result is None
        mock_logger.warning.assert_called_once()


def test_map_books_to_records_success(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test mapping books to records (covers lines 288-293)."""
    books_data = [
        {"id": 1, "title": "Book 1"},
        {"id": 2, "title": "Book 2"},
    ]

    records = hardcover_provider._map_books_to_records(books_data)

    assert len(records) == 2
    assert records[0].title == "Book 1"
    assert records[1].title == "Book 2"


def test_map_books_to_records_with_none(
    hardcover_provider: HardcoverProvider,
) -> None:
    """Test mapping books to records when mapper returns None (covers lines 288-293)."""
    books_data = [
        {"id": 1, "title": "Book 1"},
        {},  # This will result in None from mapper
    ]

    records = hardcover_provider._map_books_to_records(books_data)

    assert len(records) == 1
    assert records[0].title == "Book 1"


def test_hardcover_provider_init_default_token(mock_http_client: MagicMock) -> None:
    """Test initialization with default token from environment."""
    with (
        patch.dict("os.environ", {"HARDCOVER_API_TOKEN": "env-token"}),
        patch(
            "fundamental.metadata.providers.hardcover.HardcoverProvider.DEFAULT_BEARER_TOKEN",
            "env-token",
        ),
    ):
        provider = HardcoverProvider(
            enabled=True,
            http_client=mock_http_client,
        )
        assert provider.bearer_token == "env-token"

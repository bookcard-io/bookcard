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

"""Tests for Hardcover data source to achieve 100% coverage."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import httpx
import pytest

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)
from fundamental.services.library_scanning.data_sources.base import (
    DataSourceNetworkError,
)
from fundamental.services.library_scanning.data_sources.hardcover import (
    HardcoverDataSource,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_graphql_client() -> MagicMock:
    """Create a mock HardcoverGraphQLClient."""
    client = MagicMock()
    client.execute_query.return_value = {"data": {}}
    return client


@pytest.fixture
def mock_parser() -> MagicMock:
    """Create a mock HardcoverResponseParser."""
    parser = MagicMock()
    parser.extract_search_data.return_value = {}
    parser.parse_search_results.return_value = []
    parser.extract_edition_data.return_value = None
    return parser


@pytest.fixture
def mock_enrichment() -> MagicMock:
    """Create a mock HardcoverEnrichment."""
    enrichment = MagicMock()
    enrichment.merge_book_with_editions.return_value = {}
    return enrichment


@pytest.fixture
def mock_extractors() -> dict[str, MagicMock]:
    """Create mock extractors."""
    return {
        "authors": MagicMock(return_value=[]),
        "cover": MagicMock(return_value=None),
        "identifiers": MagicMock(return_value={}),
        "published_date": MagicMock(return_value=None),
        "publisher": MagicMock(return_value=None),
        "tags": MagicMock(return_value=[]),
    }


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create a mock HTTP client."""
    return MagicMock()


@pytest.fixture
@patch.dict(os.environ, {"HARDCOVER_API_TOKEN": "test-token"}, clear=False)
def data_source_with_token(
    mock_graphql_client: MagicMock,
    mock_parser: MagicMock,
    mock_enrichment: MagicMock,
    mock_extractors: dict[str, MagicMock],
    mock_http_client: MagicMock,
) -> HardcoverDataSource:
    """Create HardcoverDataSource with bearer token."""
    with (
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverGraphQLClient",
            return_value=mock_graphql_client,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverResponseParser",
            return_value=mock_parser,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverEnrichment",
            return_value=mock_enrichment,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.AuthorsExtractor",
            return_value=mock_extractors["authors"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.CoverExtractor",
            return_value=mock_extractors["cover"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.IdentifiersExtractor",
            return_value=mock_extractors["identifiers"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublishedDateExtractor",
            return_value=mock_extractors["published_date"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublisherExtractor",
            return_value=mock_extractors["publisher"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.TagsExtractor",
            return_value=mock_extractors["tags"],
        ),
    ):
        return HardcoverDataSource(
            base_url="https://test.api.hardcover.app/v1/graphql",
            timeout=5.0,
            bearer_token="test-token",
            http_client=mock_http_client,
        )


@pytest.fixture
@patch.dict(os.environ, {}, clear=True)
def data_source_without_token(
    mock_graphql_client: MagicMock,
    mock_parser: MagicMock,
    mock_enrichment: MagicMock,
    mock_extractors: dict[str, MagicMock],
) -> HardcoverDataSource:
    """Create HardcoverDataSource without bearer token."""
    with (
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverGraphQLClient",
            return_value=mock_graphql_client,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverResponseParser",
            return_value=mock_parser,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverEnrichment",
            return_value=mock_enrichment,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.AuthorsExtractor",
            return_value=mock_extractors["authors"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.CoverExtractor",
            return_value=mock_extractors["cover"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.IdentifiersExtractor",
            return_value=mock_extractors["identifiers"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublishedDateExtractor",
            return_value=mock_extractors["published_date"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublisherExtractor",
            return_value=mock_extractors["publisher"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.TagsExtractor",
            return_value=mock_extractors["tags"],
        ),
    ):
        return HardcoverDataSource()


@pytest.fixture
def sample_author_search_data() -> dict[str, object]:
    """Sample author data from search results."""
    return {
        "id": 123,
        "name": "Test Author",
        "born_date": "1950-01-01",
        "born_year": 1950,
        "death_date": "2020-01-01",
        "death_year": 2020,
        "alternate_names": ["Alt Name 1", "Alt Name 2"],
        "bio": "Test biography",
        "books_count": 10,
        "identifiers": [
            {"type": "goodreads", "value": "12345"},
            {"type": "wikidata", "value": "Q123"},
        ],
    }


@pytest.fixture
def sample_book_search_data() -> dict[str, object]:
    """Sample book data from search results."""
    return {
        "id": 456,
        "title": "Test Book",
        "slug": "test-book",
        "editions": [
            {
                "title": "Test Book",
                "isbn": "1234567890",
                "isbn13": "9781234567890",
                "publish_date": "2020-01-01",
                "publisher": "Test Publisher",
                "cover_url": "https://example.com/cover.jpg",
            }
        ],
        "description": "Test description",
    }


@pytest.fixture
def sample_author_full_data() -> dict[str, object]:
    """Sample full author data from get_author query."""
    return {
        "id": 123,
        "name": "Test Author",
        "born_date": "1950-01-01",
        "death_date": "2020-01-01",
        "alternate_names": ["Alt Name 1"],
        "bio": "Full biography",
        "books_count": 10,
        "identifiers": [
            {"type": "viaf", "value": "123456"},
            {"type": "goodreads", "value": "789012"},
        ],
        "contributions": [
            {
                "contributable_type": "Book",
                "book": {"id": 100},
            },
            {
                "contributable_type": "Book",
                "book": {"id": 200},
            },
            {
                "contributable_type": "Edition",
                "book": {"id": 300},
            },
        ],
    }


@pytest.fixture
def sample_book_edition_data() -> dict[str, object]:
    """Sample book edition data."""
    return {
        "id": 456,
        "title": "Test Book",
        "slug": "test-book-slug",
        "editions": [
            {
                "title": "Test Book Edition",
                "isbn": "1234567890",
                "isbn13": "9781234567890",
                "publish_date": "2020-01-01",
                "publisher": "Test Publisher",
                "cover_url": "https://example.com/cover.jpg",
            }
        ],
        "description": "Test description",
    }


# ============================================================================
# Tests for __init__
# ============================================================================


@patch.dict(os.environ, {"HARDCOVER_API_TOKEN": "env-token"}, clear=False)
def test_init_with_env_token(
    mock_graphql_client: MagicMock,
    mock_parser: MagicMock,
    mock_enrichment: MagicMock,
    mock_extractors: dict[str, MagicMock],
) -> None:
    """Test initialization with token from environment."""
    with (
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverGraphQLClient",
            return_value=mock_graphql_client,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverResponseParser",
            return_value=mock_parser,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverEnrichment",
            return_value=mock_enrichment,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.AuthorsExtractor",
            return_value=mock_extractors["authors"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.CoverExtractor",
            return_value=mock_extractors["cover"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.IdentifiersExtractor",
            return_value=mock_extractors["identifiers"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublishedDateExtractor",
            return_value=mock_extractors["published_date"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublisherExtractor",
            return_value=mock_extractors["publisher"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.TagsExtractor",
            return_value=mock_extractors["tags"],
        ),
    ):
        ds = HardcoverDataSource()
        assert ds.bearer_token == "env-token"


@patch.dict(os.environ, {}, clear=True)
def test_init_without_token_warning(
    mock_graphql_client: MagicMock,
    mock_parser: MagicMock,
    mock_enrichment: MagicMock,
    mock_extractors: dict[str, MagicMock],
) -> None:
    """Test initialization without token logs warning."""
    with (
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverGraphQLClient",
            return_value=mock_graphql_client,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverResponseParser",
            return_value=mock_parser,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverEnrichment",
            return_value=mock_enrichment,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.AuthorsExtractor",
            return_value=mock_extractors["authors"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.CoverExtractor",
            return_value=mock_extractors["cover"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.IdentifiersExtractor",
            return_value=mock_extractors["identifiers"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublishedDateExtractor",
            return_value=mock_extractors["published_date"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublisherExtractor",
            return_value=mock_extractors["publisher"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.TagsExtractor",
            return_value=mock_extractors["tags"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.logger"
        ) as mock_logger,
    ):
        HardcoverDataSource()
        mock_logger.warning.assert_called_once()


def test_init_with_custom_params(
    mock_graphql_client: MagicMock,
    mock_parser: MagicMock,
    mock_enrichment: MagicMock,
    mock_extractors: dict[str, MagicMock],
    mock_http_client: MagicMock,
) -> None:
    """Test initialization with custom parameters."""
    with (
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverGraphQLClient",
            return_value=mock_graphql_client,
        ) as mock_client_class,
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverResponseParser",
            return_value=mock_parser,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.HardcoverEnrichment",
            return_value=mock_enrichment,
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.AuthorsExtractor",
            return_value=mock_extractors["authors"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.CoverExtractor",
            return_value=mock_extractors["cover"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.IdentifiersExtractor",
            return_value=mock_extractors["identifiers"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublishedDateExtractor",
            return_value=mock_extractors["published_date"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.PublisherExtractor",
            return_value=mock_extractors["publisher"],
        ),
        patch(
            "fundamental.services.library_scanning.data_sources.hardcover.TagsExtractor",
            return_value=mock_extractors["tags"],
        ),
    ):
        ds = HardcoverDataSource(
            base_url="https://custom.url/graphql",
            timeout=15.0,
            bearer_token="custom-token",
            http_client=mock_http_client,
        )
        assert ds.base_url == "https://custom.url/graphql"
        assert ds.timeout == 15.0
        assert ds.bearer_token == "custom-token"
        mock_client_class.assert_called_once_with(
            endpoint="https://custom.url/graphql",
            bearer_token="custom-token",
            timeout=15,
            http_client=mock_http_client,
        )


# ============================================================================
# Tests for name property
# ============================================================================


def test_name_property(data_source_with_token: HardcoverDataSource) -> None:
    """Test name property returns 'Hardcover'."""
    assert data_source_with_token.name == "Hardcover"


# ============================================================================
# Tests for search_author
# ============================================================================


@pytest.mark.parametrize(
    ("name", "expected_empty"),
    [
        ("", True),
        ("   ", True),
        ("Test Author", False),
        ("  Test Author  ", False),
    ],
)
def test_search_author_empty_name(
    data_source_with_token: HardcoverDataSource,
    name: str,
    expected_empty: bool,
) -> None:
    """Test search_author with empty or whitespace-only names."""
    result = data_source_with_token.search_author(name)
    assert result == []
    if expected_empty:
        data_source_with_token._client.execute_query.assert_not_called()  # type: ignore[attr-defined]


def test_search_author_without_token(
    data_source_without_token: HardcoverDataSource,
) -> None:
    """Test search_author without bearer token returns empty."""
    result = data_source_without_token.search_author("Test Author")
    assert result == []
    data_source_without_token._client.execute_query.assert_not_called()  # type: ignore[attr-defined]


def test_search_author_success(
    data_source_with_token: HardcoverDataSource,
    sample_author_search_data: dict[str, object],
) -> None:
    """Test successful author search."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"search": {"results": [sample_author_search_data]}}
    }
    data_source_with_token._parser.extract_search_data.return_value = {  # type: ignore[attr-defined]
        "results": [sample_author_search_data]
    }
    data_source_with_token._parser.parse_search_results.return_value = [  # type: ignore[attr-defined]
        sample_author_search_data
    ]

    # Mock _map_to_author_data to return AuthorData
    with patch.object(
        data_source_with_token,
        "_map_to_author_data",
        return_value=AuthorData(key="123", name="Test Author", birth_date="1950-01-01"),
    ):
        result = data_source_with_token.search_author("Test Author")
        assert len(result) == 1
        assert isinstance(result[0], AuthorData)
        data_source_with_token._client.execute_query.assert_called_once()  # type: ignore[attr-defined]


def test_search_author_no_results(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_author with no results."""
    data_source_with_token._parser.parse_search_results.return_value = []  # type: ignore[attr-defined]
    result = data_source_with_token.search_author("Nonexistent Author")
    assert result == []


def test_search_author_network_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_author raises DataSourceNetworkError on network error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderNetworkError("Network error")
    )
    with pytest.raises(DataSourceNetworkError, match="Hardcover API request failed"):
        data_source_with_token.search_author("Test Author")


def test_search_author_parse_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_author raises DataSourceNetworkError on parse error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderParseError("Parse error")
    )
    with pytest.raises(DataSourceNetworkError, match="Error searching authors"):
        data_source_with_token.search_author("Test Author")


@pytest.mark.parametrize(
    "error",
    [
        KeyError("missing key"),
        ValueError("invalid value"),
        TypeError("wrong type"),
    ],
)
def test_search_author_parsing_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test search_author handles parsing exceptions."""
    data_source_with_token._parser.parse_search_results.side_effect = error  # type: ignore[attr-defined]
    with pytest.raises(DataSourceNetworkError, match="Error searching authors"):
        data_source_with_token.search_author("Test Author")


# ============================================================================
# Tests for get_author
# ============================================================================


def test_get_author_without_token(
    data_source_without_token: HardcoverDataSource,
) -> None:
    """Test get_author without bearer token returns None."""
    result = data_source_without_token.get_author("123")
    assert result is None


@pytest.mark.parametrize(
    "key",
    [
        "invalid",
        "not-a-number",
        "",
        "abc123",
    ],
)
def test_get_author_invalid_key(
    data_source_with_token: HardcoverDataSource,
    key: str,
) -> None:
    """Test get_author with invalid key returns None."""
    result = data_source_with_token.get_author(key)
    assert result is None
    data_source_with_token._client.execute_query.assert_not_called()  # type: ignore[attr-defined]


def test_get_author_success(
    data_source_with_token: HardcoverDataSource,
    sample_author_full_data: dict[str, object],
) -> None:
    """Test successful get_author."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [sample_author_full_data]}
    }

    with patch.object(
        data_source_with_token,
        "_map_to_author_data",
        return_value=AuthorData(key="123", name="Test Author"),
    ):
        result = data_source_with_token.get_author("123")
        assert result is not None
        assert isinstance(result, AuthorData)


def test_get_author_empty_response(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author with empty response."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": []}
    }
    result = data_source_with_token.get_author("123")
    assert result is None


def test_get_author_invalid_response_structure(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author with invalid response structure."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": "not-a-list"}
    }
    result = data_source_with_token.get_author("123")
    assert result is None


def test_get_author_network_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author raises DataSourceNetworkError on network error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderNetworkError("Network error")
    )
    with pytest.raises(DataSourceNetworkError, match="Hardcover API request failed"):
        data_source_with_token.get_author("123")


def test_get_author_parse_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author raises DataSourceNetworkError on parse error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderParseError("Parse error")
    )
    with pytest.raises(DataSourceNetworkError, match="Error fetching author"):
        data_source_with_token.get_author("123")


@pytest.mark.parametrize(
    "error",
    [
        KeyError("missing key"),
        ValueError("invalid value"),
        TypeError("wrong type"),
    ],
)
def test_get_author_parsing_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test get_author handles parsing exceptions."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [{"id": 123}]}
    }
    data_source_with_token._map_to_author_data = MagicMock(side_effect=error)  # type: ignore[attr-defined]
    with pytest.raises(DataSourceNetworkError, match="Error fetching author"):
        data_source_with_token.get_author("123")


# ============================================================================
# Tests for search_book
# ============================================================================


def test_search_book_without_token(
    data_source_without_token: HardcoverDataSource,
) -> None:
    """Test search_book without bearer token returns empty."""
    result = data_source_without_token.search_book(title="Test Book")
    assert result == []


@pytest.mark.parametrize(
    ("title", "isbn", "authors", "expected_empty"),
    [
        (None, None, None, True),
        ("", None, None, True),  # Empty string is falsy
        (None, "", None, True),  # Empty string is falsy
        (None, None, [], True),  # Empty list is falsy
        ("Test", None, None, False),
        (None, "1234567890", None, False),
        (None, None, ["Author"], False),
    ],
)
def test_search_book_empty_params(
    data_source_with_token: HardcoverDataSource,
    title: str | None,
    isbn: str | None,
    authors: Sequence[str] | None,
    expected_empty: bool,
) -> None:
    """Test search_book with empty parameters."""
    result = data_source_with_token.search_book(title=title, isbn=isbn, authors=authors)
    if expected_empty:
        assert result == []
        data_source_with_token._client.execute_query.assert_not_called()  # type: ignore[attr-defined]
    else:
        data_source_with_token._client.execute_query.assert_called_once()  # type: ignore[attr-defined]


def test_search_book_success(
    data_source_with_token: HardcoverDataSource,
    sample_book_search_data: dict[str, object],
) -> None:
    """Test successful book search."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"search": {"results": [sample_book_search_data]}}
    }
    data_source_with_token._parser.extract_search_data.return_value = {  # type: ignore[attr-defined]
        "results": [sample_book_search_data]
    }
    data_source_with_token._parser.parse_search_results.return_value = [  # type: ignore[attr-defined]
        sample_book_search_data
    ]
    data_source_with_token._enrich_books_with_editions = MagicMock(  # type: ignore[attr-defined]
        return_value=[sample_book_search_data]
    )
    data_source_with_token._map_books_to_book_data = MagicMock(  # type: ignore[attr-defined]
        return_value=[BookData(key="456", title="Test Book", authors=["Test Author"])]
    )

    result = data_source_with_token.search_book(title="Test Book")
    assert len(result) == 1
    assert isinstance(result[0], BookData)


def test_search_book_no_results(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_book with no results."""
    data_source_with_token._parser.parse_search_results.return_value = []  # type: ignore[attr-defined]
    result = data_source_with_token.search_book(title="Nonexistent Book")
    assert result == []


def test_search_book_network_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_book raises DataSourceNetworkError on network error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderNetworkError("Network error")
    )
    with pytest.raises(DataSourceNetworkError, match="Hardcover API request failed"):
        data_source_with_token.search_book(title="Test Book")


def test_search_book_parse_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test search_book raises DataSourceNetworkError on parse error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderParseError("Parse error")
    )
    with pytest.raises(DataSourceNetworkError, match="Error searching books"):
        data_source_with_token.search_book(title="Test Book")


@pytest.mark.parametrize(
    "error",
    [
        KeyError("missing key"),
        ValueError("invalid value"),
        TypeError("wrong type"),
    ],
)
def test_search_book_parsing_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test search_book handles parsing exceptions."""
    data_source_with_token._parser.parse_search_results.side_effect = error  # type: ignore[attr-defined]
    with pytest.raises(DataSourceNetworkError, match="Error searching books"):
        data_source_with_token.search_book(title="Test Book")


# ============================================================================
# Tests for get_book
# ============================================================================


def test_get_book_without_token(
    data_source_without_token: HardcoverDataSource,
) -> None:
    """Test get_book without bearer token returns None."""
    result = data_source_without_token.get_book("456")
    assert result is None


@pytest.mark.parametrize(
    "key",
    [
        "invalid",
        "not-a-number",
        "",
        "abc123",
    ],
)
def test_get_book_invalid_key(
    data_source_with_token: HardcoverDataSource,
    key: str,
) -> None:
    """Test get_book with invalid key returns None."""
    result = data_source_with_token.get_book(key)
    assert result is None
    data_source_with_token._client.execute_query.assert_not_called()  # type: ignore[attr-defined]


def test_get_book_success(
    data_source_with_token: HardcoverDataSource,
    sample_book_edition_data: dict[str, object],
) -> None:
    """Test successful get_book."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [sample_book_edition_data]}
    }
    data_source_with_token._parser.extract_edition_data.return_value = (  # type: ignore[attr-defined]
        sample_book_edition_data
    )

    with patch.object(
        data_source_with_token,
        "_map_to_book_data",
        return_value=BookData(key="456", title="Test Book"),
    ):
        result = data_source_with_token.get_book("456")
        assert result is not None
        assert isinstance(result, BookData)


def test_get_book_empty_books_array(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_book with empty books array."""
    data_source_with_token._client.execute_query.return_value = {"data": {"books": []}}  # type: ignore[attr-defined]
    result = data_source_with_token.get_book("456")
    assert result is None


def test_get_book_no_edition_data(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_book when extract_edition_data returns None."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [{"id": 456}]}
    }
    data_source_with_token._parser.extract_edition_data.return_value = None  # type: ignore[attr-defined]
    result = data_source_with_token.get_book("456")
    assert result is None


def test_get_book_network_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_book raises DataSourceNetworkError on network error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderNetworkError("Network error")
    )
    with pytest.raises(DataSourceNetworkError, match="Hardcover API request failed"):
        data_source_with_token.get_book("456")


def test_get_book_parse_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_book raises DataSourceNetworkError on parse error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderParseError("Parse error")
    )
    with pytest.raises(DataSourceNetworkError, match="Error fetching book"):
        data_source_with_token.get_book("456")


@pytest.mark.parametrize(
    "error",
    [
        KeyError("missing key"),
        ValueError("invalid value"),
        TypeError("wrong type"),
    ],
)
def test_get_book_parsing_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test get_book handles parsing exceptions."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [{"id": 456}]}
    }
    data_source_with_token._parser.extract_edition_data.side_effect = error  # type: ignore[attr-defined]
    with pytest.raises(DataSourceNetworkError, match="Error fetching book"):
        data_source_with_token.get_book("456")


def test_get_book_else_clause(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_book else clause (when extract_edition_data returns None)."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [{"id": 456}]}
    }
    data_source_with_token._parser.extract_edition_data.return_value = None  # type: ignore[attr-defined]
    result = data_source_with_token.get_book("456")
    assert result is None


# ============================================================================
# Tests for _enrich_books_with_editions
# ============================================================================


def test_enrich_books_with_editions_success(
    data_source_with_token: HardcoverDataSource,
    sample_book_search_data: dict[str, object],
    sample_book_edition_data: dict[str, object],
) -> None:
    """Test _enrich_books_with_editions successfully enriches books."""
    data_source_with_token._fetch_edition_details = MagicMock(  # type: ignore[attr-defined]
        return_value=sample_book_edition_data
    )
    data_source_with_token._enrichment.merge_book_with_editions.return_value = {  # type: ignore[attr-defined]
        **sample_book_search_data,
        **sample_book_edition_data,
    }

    result = data_source_with_token._enrich_books_with_editions([
        sample_book_search_data
    ])
    assert len(result) == 1
    data_source_with_token._fetch_edition_details.assert_called_once_with(456)  # type: ignore[attr-defined]


def test_enrich_books_with_editions_no_book_id(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _enrich_books_with_editions with book without ID."""
    book_data = {"title": "Test Book"}
    result = data_source_with_token._enrich_books_with_editions([book_data])
    assert len(result) == 1
    assert result[0] == book_data


def test_enrich_books_with_editions_fetch_fails(
    data_source_with_token: HardcoverDataSource,
    sample_book_search_data: dict[str, object],
) -> None:
    """Test _enrich_books_with_editions when fetch fails."""
    data_source_with_token._fetch_edition_details = MagicMock(return_value=None)  # type: ignore[attr-defined]
    result = data_source_with_token._enrich_books_with_editions([
        sample_book_search_data
    ])
    assert len(result) == 1
    assert result[0] == sample_book_search_data


# ============================================================================
# Tests for _fetch_edition_details
# ============================================================================


def test_fetch_edition_details_success(
    data_source_with_token: HardcoverDataSource,
    sample_book_edition_data: dict[str, object],
) -> None:
    """Test _fetch_edition_details successfully fetches edition."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [sample_book_edition_data]}
    }
    data_source_with_token._parser.extract_edition_data.return_value = (  # type: ignore[attr-defined]
        sample_book_edition_data
    )

    result = data_source_with_token._fetch_edition_details(456)
    assert result == sample_book_edition_data


def test_fetch_edition_details_string_id(
    data_source_with_token: HardcoverDataSource,
    sample_book_edition_data: dict[str, object],
) -> None:
    """Test _fetch_edition_details with string ID."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"books": [sample_book_edition_data]}
    }
    data_source_with_token._parser.extract_edition_data.return_value = (  # type: ignore[attr-defined]
        sample_book_edition_data
    )

    result = data_source_with_token._fetch_edition_details("456")
    assert result == sample_book_edition_data


@pytest.mark.parametrize(
    "error",
    [
        ValueError("invalid value"),
        TypeError("wrong type"),
        KeyError("missing key"),
        httpx.RequestError("request error"),
        httpx.TimeoutException("timeout"),
    ],
)
def test_fetch_edition_details_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test _fetch_edition_details handles exceptions."""
    data_source_with_token._client.execute_query.side_effect = error  # type: ignore[attr-defined]
    result = data_source_with_token._fetch_edition_details(456)
    assert result is None


# ============================================================================
# Tests for _map_books_to_book_data
# ============================================================================


def test_map_books_to_book_data_success(
    data_source_with_token: HardcoverDataSource,
    sample_book_search_data: dict[str, object],
) -> None:
    """Test _map_books_to_book_data successfully maps books."""
    with patch.object(
        data_source_with_token,
        "_map_to_book_data",
        return_value=BookData(key="456", title="Test Book"),
    ):
        result = data_source_with_token._map_books_to_book_data([
            sample_book_search_data
        ])
        assert len(result) == 1
        assert isinstance(result[0], BookData)


def test_map_books_to_book_data_none_mapping(
    data_source_with_token: HardcoverDataSource,
    sample_book_search_data: dict[str, object],
) -> None:
    """Test _map_books_to_book_data filters out None mappings."""
    with patch.object(
        data_source_with_token,
        "_map_to_book_data",
        side_effect=[BookData(key="456", title="Test Book"), None],
    ):
        result = data_source_with_token._map_books_to_book_data([
            sample_book_search_data,
            sample_book_search_data,
        ])
        assert len(result) == 1


# ============================================================================
# Tests for _map_to_book_data
# ============================================================================


def test_map_to_book_data_no_id(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data with book without ID."""
    result = data_source_with_token._map_to_book_data({"title": "Test Book"})
    assert result is None


def test_map_to_book_data_with_title(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data with title."""
    data_source_with_token._authors_extractor.extract.return_value = ["Author"]  # type: ignore[attr-defined]
    data_source_with_token._identifiers_extractor.extract.return_value = {  # type: ignore[attr-defined]
        "isbn": "1234567890",
        "isbn13": "9781234567890",
    }
    data_source_with_token._cover_extractor.extract.return_value = "https://cover.jpg"  # type: ignore[attr-defined]
    data_source_with_token._published_date_extractor.extract.return_value = "2020-01-01"  # type: ignore[attr-defined]
    data_source_with_token._publisher_extractor.extract.return_value = "Publisher"  # type: ignore[attr-defined]
    data_source_with_token._tags_extractor.extract.return_value = ["Tag1"]  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "title": "Test Book",
        "description": "Test description",
    })
    assert result is not None
    assert result.key == "456"
    assert result.title == "Test Book"


def test_map_to_book_data_title_from_edition(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data gets title from first edition."""
    data_source_with_token._authors_extractor.extract.return_value = []  # type: ignore[attr-defined]
    data_source_with_token._identifiers_extractor.extract.return_value = {}  # type: ignore[attr-defined]
    data_source_with_token._cover_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._published_date_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._publisher_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._tags_extractor.extract.return_value = []  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "editions": [{"title": "Edition Title"}],
    })
    assert result is not None
    assert result.title == "Edition Title"


def test_map_to_book_data_title_from_slug(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data uses slug as fallback for title."""
    data_source_with_token._authors_extractor.extract.return_value = []  # type: ignore[attr-defined]
    data_source_with_token._identifiers_extractor.extract.return_value = {}  # type: ignore[attr-defined]
    data_source_with_token._cover_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._published_date_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._publisher_extractor.extract.return_value = None  # type: ignore[attr-defined]
    data_source_with_token._tags_extractor.extract.return_value = []  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "slug": "test-book-title",
        "editions": [],
    })
    assert result is not None
    assert result.title == "Test Book Title"


def test_map_to_book_data_no_title_or_slug(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data returns None when no title or slug."""
    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "editions": [],
    })
    assert result is None


def test_map_to_book_data_extractors_return_wrong_types(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data handles extractors returning wrong types."""
    data_source_with_token._authors_extractor.extract.return_value = "not-a-list"  # type: ignore[attr-defined]
    data_source_with_token._identifiers_extractor.extract.return_value = "not-a-dict"  # type: ignore[attr-defined]
    data_source_with_token._cover_extractor.extract.return_value = 123  # type: ignore[attr-defined]
    data_source_with_token._published_date_extractor.extract.return_value = 456  # type: ignore[attr-defined]
    data_source_with_token._publisher_extractor.extract.return_value = []  # type: ignore[attr-defined]
    data_source_with_token._tags_extractor.extract.return_value = "not-a-list"  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "title": "Test Book",
    })
    assert result is not None
    assert result.authors == []
    assert result.isbn is None
    assert result.cover_url is None


def test_map_to_book_data_exception(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_book_data handles exceptions."""
    data_source_with_token._authors_extractor.extract.side_effect = KeyError("missing")  # type: ignore[attr-defined]
    result = data_source_with_token._map_to_book_data({
        "id": 456,
        "title": "Test Book",
    })
    assert result is None


# ============================================================================
# Tests for _map_to_author_data
# ============================================================================


def test_map_to_author_data_no_id(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data with author without ID."""
    result = data_source_with_token._map_to_author_data({"name": "Test Author"})
    assert result is None


def test_map_to_author_data_no_name(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data with author without name."""
    result = data_source_with_token._map_to_author_data({"id": 123})
    assert result is None


def test_map_to_author_data_success(
    data_source_with_token: HardcoverDataSource,
    sample_author_full_data: dict[str, object],
) -> None:
    """Test _map_to_author_data successfully maps author."""
    data_source_with_token._extract_author_identifiers = MagicMock(  # type: ignore[attr-defined]
        return_value=IdentifierDict(goodreads="12345")
    )

    result = data_source_with_token._map_to_author_data(sample_author_full_data)
    assert result is not None
    assert result.key == "123"
    assert result.name == "Test Author"
    assert result.birth_date == "1950-01-01"
    assert result.death_date == "2020-01-01"


def test_map_to_author_data_birth_year_only(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data uses birth_year when birth_date missing."""
    data_source_with_token._extract_author_identifiers = MagicMock(return_value=None)  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_author_data({
        "id": 123,
        "name": "Test Author",
        "born_year": 1950,
    })
    assert result is not None
    assert result.birth_date == "1950"


def test_map_to_author_data_death_year_only(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data uses death_year when death_date missing."""
    data_source_with_token._extract_author_identifiers = MagicMock(return_value=None)  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_author_data({
        "id": 123,
        "name": "Test Author",
        "death_year": 2020,
    })
    assert result is not None
    assert result.death_date == "2020"


def test_map_to_author_data_alternate_names_not_list(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data handles alternate_names not being a list."""
    data_source_with_token._extract_author_identifiers = MagicMock(return_value=None)  # type: ignore[attr-defined]

    result = data_source_with_token._map_to_author_data({
        "id": 123,
        "name": "Test Author",
        "alternate_names": "not-a-list",
    })
    assert result is not None
    assert result.alternate_names == []


def test_map_to_author_data_exception(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _map_to_author_data handles exceptions."""
    with patch.object(
        data_source_with_token,
        "_extract_author_identifiers",
        side_effect=KeyError("missing"),
    ):
        result = data_source_with_token._map_to_author_data({
            "id": 123,
            "name": "Test Author",
        })
        assert result is None


# ============================================================================
# Tests for get_author_works
# ============================================================================


def test_get_author_works_without_token(
    data_source_without_token: HardcoverDataSource,
) -> None:
    """Test get_author_works without bearer token returns empty."""
    result = data_source_without_token.get_author_works("123")
    assert result == []


@pytest.mark.parametrize(
    "key",
    [
        "invalid",
        "not-a-number",
        "",
        "abc123",
    ],
)
def test_get_author_works_invalid_key(
    data_source_with_token: HardcoverDataSource,
    key: str,
) -> None:
    """Test get_author_works with invalid key returns empty."""
    result = data_source_with_token.get_author_works(key)
    assert result == []


def test_get_author_works_success(
    data_source_with_token: HardcoverDataSource,
    sample_author_full_data: dict[str, object],
) -> None:
    """Test successful get_author_works."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [sample_author_full_data]}
    }

    result = data_source_with_token.get_author_works("123")
    assert len(result) == 2
    assert "100" in result
    assert "200" in result
    assert "300" not in result  # Edition type should be filtered


def test_get_author_works_with_limit(
    data_source_with_token: HardcoverDataSource,
    sample_author_full_data: dict[str, object],
) -> None:
    """Test get_author_works with limit."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [sample_author_full_data]}
    }

    result = data_source_with_token.get_author_works("123", limit=1)
    assert len(result) == 1


def test_get_author_works_empty_response(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works with empty response."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": []}
    }
    result = data_source_with_token.get_author_works("123")
    assert result == []


def test_get_author_works_invalid_response_structure(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works with invalid response structure."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": "not-a-list"}
    }
    result = data_source_with_token.get_author_works("123")
    assert result == []


def test_get_author_works_no_contributions(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works with no contributions."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [{"id": 123, "name": "Author"}]}
    }
    result = data_source_with_token.get_author_works("123")
    assert result == []


def test_get_author_works_contributions_not_list(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works with contributions not a list."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [{"id": 123, "contributions": "not-a-list"}]}
    }
    result = data_source_with_token.get_author_works("123")
    assert result == []


def test_get_author_works_network_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works raises DataSourceNetworkError on network error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderNetworkError("Network error")
    )
    with pytest.raises(DataSourceNetworkError, match="Hardcover API request failed"):
        data_source_with_token.get_author_works("123")


def test_get_author_works_parse_error(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test get_author_works raises DataSourceNetworkError on parse error."""
    data_source_with_token._client.execute_query.side_effect = (  # type: ignore[attr-defined]
        MetadataProviderParseError("Parse error")
    )
    with pytest.raises(DataSourceNetworkError, match="Error parsing author works"):
        data_source_with_token.get_author_works("123")


@pytest.mark.parametrize(
    "error",
    [
        KeyError("missing key"),
        ValueError("invalid value"),
        TypeError("wrong type"),
    ],
)
def test_get_author_works_parsing_exceptions(
    data_source_with_token: HardcoverDataSource,
    error: Exception,
) -> None:
    """Test get_author_works handles parsing exceptions."""
    data_source_with_token._client.execute_query.return_value = {  # type: ignore[attr-defined]
        "data": {"authors": [{"id": 123, "contributions": []}]}
    }
    with (
        patch.object(
            data_source_with_token,
            "_extract_work_keys_from_contributions",
            side_effect=error,
        ),
        pytest.raises(DataSourceNetworkError, match="Error extracting author works"),
    ):
        data_source_with_token.get_author_works("123")


# ============================================================================
# Tests for _extract_work_keys_from_contributions
# ============================================================================


def test_extract_work_keys_from_contributions_success(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions successfully extracts keys."""
    data = {
        "data": {
            "authors": [
                {
                    "contributions": [
                        {"contributable_type": "Book", "book": {"id": 100}},
                        {"contributable_type": "Book", "book": {"id": 200}},
                        {"contributable_type": "Edition", "book": {"id": 300}},
                    ]
                }
            ]
        }
    }
    result = data_source_with_token._extract_work_keys_from_contributions(data)
    assert len(result) == 2
    assert "100" in result
    assert "200" in result


def test_extract_work_keys_from_contributions_with_limit(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with limit."""
    data = {
        "data": {
            "authors": [
                {
                    "contributions": [
                        {"contributable_type": "Book", "book": {"id": 100}},
                        {"contributable_type": "Book", "book": {"id": 200}},
                    ]
                }
            ]
        }
    }
    result = data_source_with_token._extract_work_keys_from_contributions(data, limit=1)
    assert len(result) == 1


def test_extract_work_keys_from_contributions_empty_authors(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with empty authors."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {"authors": []}
    })
    assert result == []


def test_extract_work_keys_from_contributions_invalid_authors(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with invalid authors."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {"authors": "not-a-list"}
    })
    assert result == []


def test_extract_work_keys_from_contributions_no_contributions(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with no contributions."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {"authors": [{"id": 123}]}
    })
    assert result == []


def test_extract_work_keys_from_contributions_contributions_not_list(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with contributions not a list."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {"authors": [{"contributions": "not-a-list"}]}
    })
    assert result == []


def test_extract_work_keys_from_contributions_contribution_not_dict(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with contribution not a dict."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {
            "authors": [
                {
                    "contributions": [
                        "not-a-dict",
                        {"contributable_type": "Book", "book": {"id": 100}},
                    ]
                }
            ]
        }
    })
    assert len(result) == 1


def test_extract_work_keys_from_contributions_no_book_id(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_work_keys_from_contributions with book without ID."""
    result = data_source_with_token._extract_work_keys_from_contributions({
        "data": {
            "authors": [
                {
                    "contributions": [
                        {"contributable_type": "Book", "book": {}},
                    ]
                }
            ]
        }
    })
    assert result == []


# ============================================================================
# Tests for _extract_author_identifiers
# ============================================================================


def test_extract_author_identifiers_no_identifiers(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers with no identifiers."""
    result = data_source_with_token._extract_author_identifiers({})
    assert result is None


def test_extract_author_identifiers_not_list(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers with identifiers not a list."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": "not-a-list"
    })
    assert result is None


def test_extract_author_identifiers_success(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers successfully extracts identifiers."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": [
            {"type": "goodreads", "value": "12345"},
            {"type": "wikidata", "value": "Q123"},
            {"type": "viaf", "id": "67890"},
            {"type": "unknown", "value": "999"},
        ]
    })
    assert result is not None
    assert result.goodreads == "12345"
    assert result.wikidata == "Q123"
    assert result.viaf == "67890"


@pytest.mark.parametrize(
    "identifier_type",
    [
        "goodreads",
        "wikidata",
        "viaf",
        "isni",
        "librarything",
        "amazon",
        "imdb",
        "musicbrainz",
        "lc_naf",
        "opac_sbn",
        "storygraph",
    ],
)
def test_extract_author_identifiers_all_types(
    data_source_with_token: HardcoverDataSource,
    identifier_type: str,
) -> None:
    """Test _extract_author_identifiers with all identifier types."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": [
            {"type": identifier_type, "value": "12345"},
        ]
    })
    assert result is not None
    assert getattr(result, identifier_type) == "12345"


def test_extract_author_identifiers_no_matching_types(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers returns None when no matching types."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": [
            {"type": "unknown", "value": "12345"},
        ]
    })
    assert result is None


def test_extract_author_identifiers_identifier_not_dict(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers with identifier not a dict."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": [
            "not-a-dict",
            {"type": "goodreads", "value": "12345"},
        ]
    })
    assert result is not None
    assert result.goodreads == "12345"


def test_extract_author_identifiers_no_value(
    data_source_with_token: HardcoverDataSource,
) -> None:
    """Test _extract_author_identifiers with identifier without value."""
    result = data_source_with_token._extract_author_identifiers({
        "identifiers": [
            {"type": "goodreads"},
        ]
    })
    assert result is None

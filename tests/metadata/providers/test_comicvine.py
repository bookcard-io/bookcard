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

"""Tests for ComicVine metadata provider to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from fundamental.metadata.providers.comicvine import ComicVineProvider


@pytest.fixture
def comicvine_provider() -> ComicVineProvider:
    """Create a ComicVineProvider instance for testing."""
    return ComicVineProvider(enabled=True)


def test_comicvine_provider_init() -> None:
    """Test ComicVineProvider initialization."""
    provider = ComicVineProvider(enabled=True, timeout=20, api_key="test_key")
    assert provider.enabled is True
    assert provider.timeout == 20
    assert provider.api_key == "test_key"


def test_comicvine_provider_init_default_api_key() -> None:
    """Test ComicVineProvider uses default API key when None."""
    provider = ComicVineProvider(enabled=True, api_key=None)
    assert provider.api_key is not None


def test_comicvine_provider_get_source_info(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test get_source_info."""
    source_info = comicvine_provider.get_source_info()
    assert source_info.id == "comicvine"
    assert source_info.name == "ComicVine"
    assert source_info.base_url == "https://comicvine.gamespot.com/"


def test_comicvine_provider_search_disabled(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search returns empty when disabled."""
    comicvine_provider.enabled = False
    result = comicvine_provider.search("test query")
    assert result == []


def test_comicvine_provider_search_empty_query(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search returns empty for empty query."""
    result = comicvine_provider.search("")
    assert result == []

    result = comicvine_provider.search("   ")
    assert result == []


def test_comicvine_provider_search_no_tokens(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search returns empty when no tokens after processing."""
    # "a" with strip_joiners=False will still produce ["a"] as a token
    # We need a query that produces no tokens after all processing
    # Let's use a query that gets filtered out completely
    result = comicvine_provider.search("   ")
    assert result == []


def test_comicvine_provider_search_success(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search succeeds with valid response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "id": "12345",
                "name": "Issue #1",
                "issue_number": "1",
                "volume": {"name": "Test Series"},
                "authors": [{"name": "Author 1"}],
                "image": {"original_url": "http://example.com/cover.jpg"},
                "description": "Test description",
                "site_detail_url": "http://example.com/issue/12345",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        results = comicvine_provider.search("test query", max_results=10)
        assert len(results) == 1
        assert results[0].title == "Test Series#1 - Issue #1"
        assert results[0].external_id == "12345"


def test_comicvine_provider_search_timeout(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search raises TimeoutError."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch("httpx.Client", return_value=mock_client),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        comicvine_provider.search("test query")


def test_comicvine_provider_search_network_error(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search raises NetworkError."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.RequestError("Network error")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch("httpx.Client", return_value=mock_client),
        pytest.raises(MetadataProviderNetworkError),
    ):
        comicvine_provider.search("test query")


def test_comicvine_provider_search_parse_error(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search raises ParseError."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch("httpx.Client", return_value=mock_client),
        pytest.raises(MetadataProviderParseError),
    ):
        comicvine_provider.search("test query")


def test_comicvine_provider_get_title_tokens(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _get_title_tokens."""
    tokens = comicvine_provider._get_title_tokens(
        "Test Book (2020)", strip_joiners=True
    )
    assert "Test" in tokens
    assert "Book" in tokens
    assert "2020" not in tokens


def test_comicvine_provider_get_title_tokens_strip_joiners(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _get_title_tokens with strip_joiners=False."""
    tokens = comicvine_provider._get_title_tokens("a and the book", strip_joiners=False)
    assert "a" in tokens
    assert "and" in tokens
    assert "the" in tokens


def test_comicvine_provider_get_title_tokens_strip_joiners_true(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _get_title_tokens with strip_joiners=True filters joiners."""
    tokens = comicvine_provider._get_title_tokens("a and the book", strip_joiners=True)
    assert "a" not in tokens
    assert "and" not in tokens
    assert "the" not in tokens
    assert "book" in tokens


def test_comicvine_provider_parse_search_result_success(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result with valid result."""
    result = {
        "id": "12345",
        "name": "Issue #1",
        "issue_number": "1",
        "volume": {"name": "Test Series"},
        "authors": [{"name": "Author 1"}],
        "image": {"original_url": "http://example.com/cover.jpg"},
        "description": "Test description",
        "site_detail_url": "http://example.com/issue/12345",
        "store_date": "2024-01-01",
    }
    record = comicvine_provider._parse_search_result(result)
    assert record is not None
    assert record.title == "Test Series#1 - Issue #1"
    assert record.external_id == "12345"
    assert record.series == "Test Series"
    assert record.series_index == 1.0


def test_comicvine_provider_parse_search_result_no_id(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result returns None when no ID."""
    result = {"name": "Issue #1"}
    record = comicvine_provider._parse_search_result(result)
    assert record is None


def test_comicvine_provider_parse_search_result_no_series(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result handles missing series."""
    result = {
        "id": "12345",
        "name": "Issue #1",
        "issue_number": "1",
        "volume": {},
    }
    record = comicvine_provider._parse_search_result(result)
    assert record is not None
    # When series is empty, the code goes to: if series: ... else: return issue_name or "Unknown"
    # So it returns "Issue #1", not "#1 - Issue #1"
    assert record.title == "Issue #1"


def test_comicvine_provider_parse_search_result_no_issue_number(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result handles missing issue number."""
    result = {
        "id": "12345",
        "name": "Issue #1",
        "volume": {"name": "Test Series"},
    }
    record = comicvine_provider._parse_search_result(result)
    assert record is not None
    assert record.title == "Test Series - Issue #1"


def test_comicvine_provider_parse_search_result_no_volume(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result handles missing volume."""
    result = {
        "id": "12345",
        "name": "Issue #1",
        "issue_number": "1",
    }
    record = comicvine_provider._parse_search_result(result)
    assert record is not None
    assert record.title == "Issue #1"


def test_comicvine_provider_parse_search_result_error(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result handles parsing errors."""
    result = {"id": None}
    record = comicvine_provider._parse_search_result(result)
    assert record is None


def test_comicvine_provider_extract_series(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_series."""
    result = {"volume": {"name": "Test Series"}}
    series = comicvine_provider._extract_series(result)
    assert series == "Test Series"


def test_comicvine_provider_extract_series_not_dict(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_series handles non-dict volume."""
    result = {"volume": "not a dict"}
    series = comicvine_provider._extract_series(result)
    assert series == ""


def test_comicvine_provider_extract_series_empty(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_series handles empty volume."""
    result = {"volume": {}}
    series = comicvine_provider._extract_series(result)
    assert series == ""


def test_comicvine_provider_build_title(comicvine_provider: ComicVineProvider) -> None:
    """Test _build_title."""
    title = comicvine_provider._build_title("Series", 1.0, "Issue #1")
    # The code uses f"{series}#{issue_number}" which for 1.0 becomes "Series#1.0"
    assert title == "Series#1.0 - Issue #1"


def test_comicvine_provider_build_title_no_issue_number(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _build_title without issue number."""
    title = comicvine_provider._build_title("Series", 0, "Issue #1")
    assert title == "Series - Issue #1"


def test_comicvine_provider_build_title_no_series(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _build_title without series."""
    title = comicvine_provider._build_title("", 1.0, "Issue #1")
    assert title == "Issue #1"


def test_comicvine_provider_build_title_no_issue_name(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _build_title without issue name."""
    title = comicvine_provider._build_title("Series", 0, "")
    assert title == "Series"


def test_comicvine_provider_build_title_unknown(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _build_title with all empty."""
    title = comicvine_provider._build_title("", 0, "")
    assert title == "Unknown"


def test_comicvine_provider_extract_authors_list(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_authors with list."""
    result = {"authors": [{"name": "Author 1"}, {"name": "Author 2"}]}
    authors = comicvine_provider._extract_authors(result)
    assert authors == ["Author 1", "Author 2"]


def test_comicvine_provider_extract_authors_string(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_authors with string."""
    result = {"authors": ["Author 1", "Author 2"]}
    authors = comicvine_provider._extract_authors(result)
    assert authors == ["Author 1", "Author 2"]


def test_comicvine_provider_extract_authors_not_list(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_authors with non-list."""
    result = {"authors": "not a list"}
    authors = comicvine_provider._extract_authors(result)
    assert authors == []


def test_comicvine_provider_extract_authors_empty(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_authors with empty list."""
    result = {"authors": []}
    authors = comicvine_provider._extract_authors(result)
    assert authors == []


def test_comicvine_provider_extract_authors_missing_name(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_authors with missing name."""
    result = {"authors": [{"not_name": "value"}]}
    authors = comicvine_provider._extract_authors(result)
    assert authors == []


def test_comicvine_provider_extract_cover_url_original(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_cover_url with original_url."""
    result = {"image": {"original_url": "http://example.com/cover.jpg"}}
    cover_url = comicvine_provider._extract_cover_url(result)
    assert cover_url == "http://example.com/cover.jpg"


def test_comicvine_provider_extract_cover_url_super(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_cover_url falls back to super_url."""
    result = {"image": {"super_url": "http://example.com/super.jpg"}}
    cover_url = comicvine_provider._extract_cover_url(result)
    assert cover_url == "http://example.com/super.jpg"


def test_comicvine_provider_extract_cover_url_not_dict(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _extract_cover_url handles non-dict image."""
    result = {"image": "not a dict"}
    cover_url = comicvine_provider._extract_cover_url(result)
    assert cover_url is None


def test_comicvine_provider_parse_series_index(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_series_index."""
    index = comicvine_provider._parse_series_index(1.0)
    assert index == 1.0


def test_comicvine_provider_parse_series_index_none(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_series_index with None."""
    index = comicvine_provider._parse_series_index(None)
    assert index is None


def test_comicvine_provider_parse_series_index_invalid(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_series_index with invalid value."""
    index = comicvine_provider._parse_series_index("invalid")  # type: ignore[assignment]
    assert index is None


def test_comicvine_provider_build_tags(comicvine_provider: ComicVineProvider) -> None:
    """Test _build_tags."""
    tags = comicvine_provider._build_tags("Test Series")
    assert "Comics" in tags
    assert "Test Series" in tags


def test_comicvine_provider_build_tags_no_series(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _build_tags without series."""
    tags = comicvine_provider._build_tags("")
    assert "Comics" in tags
    assert len(tags) == 1


def test_comicvine_provider_search_parse_error_in_result(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search handles parse errors in individual results."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"id": "valid", "name": "Valid Issue"},
            {"id": None},  # Will fail to parse
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        results = comicvine_provider.search("test query", max_results=10)
        # Should return only valid results
        assert len(results) == 1


def test_comicvine_provider_search_max_results(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search respects max_results limit."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"id": str(i), "name": f"Issue {i}", "volume": {"name": "Series"}}
            for i in range(20)
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        results = comicvine_provider.search("test query", max_results=5)
        assert len(results) == 5


def test_comicvine_provider_parse_search_result_date_added(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result uses date_added when store_date missing."""
    result = {
        "id": "12345",
        "name": "Issue #1",
        "issue_number": "1",
        "volume": {"name": "Test Series"},
        "date_added": "2024-01-01",
    }
    record = comicvine_provider._parse_search_result(result)
    assert record is not None
    assert record.published_date == "2024-01-01"


def test_comicvine_provider_search_empty_tokens_after_processing(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search returns empty when no tokens after processing (covers line 153)."""
    # Use a query that produces no tokens after tokenization
    # A query with only joiners when strip_joiners=False should still produce tokens
    # But if all tokens are filtered out, it should return empty
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    # Mock _get_title_tokens to return empty list
    with (
        patch("httpx.Client", return_value=mock_client),
        patch.object(comicvine_provider, "_get_title_tokens", return_value=[]),
    ):
        result = comicvine_provider.search("test query")
        assert result == []


def test_comicvine_provider_search_parse_result_exception(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test search handles exceptions in result parsing (covers lines 185-187)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "id": "12345",
                "name": "Valid Issue",
                "issue_number": "1",
                "volume": {"name": "Test Series"},
            },
            {
                "id": "67890",
                "name": "Error Issue",
                "issue_number": "2",
                "volume": {"name": "Test Series"},
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    # Make _parse_search_result raise an exception for the second result
    call_count = {"count": 0}
    original_parse = comicvine_provider._parse_search_result

    def failing_parse(result: dict) -> object:
        call_count["count"] += 1
        if call_count["count"] == 2:  # Second result
            raise AttributeError("Test error")
        return original_parse(result)

    with (
        patch("httpx.Client", return_value=mock_client),
        patch.object(
            comicvine_provider, "_parse_search_result", side_effect=failing_parse
        ),
    ):
        results = comicvine_provider.search("test query", max_results=10)
        # Should handle the exception from the second result and continue
        # The first result should be parsed successfully
        assert len(results) == 1
        # The exception from the second result should be caught and logged (lines 185-187)


def test_comicvine_provider_parse_search_result_exception(
    comicvine_provider: ComicVineProvider,
) -> None:
    """Test _parse_search_result handles exceptions (covers lines 297-299)."""
    # Result that will cause an exception during parsing
    result = {"id": "12345", "volume": None}
    # Make _extract_series raise an exception
    with patch.object(
        comicvine_provider, "_extract_series", side_effect=ValueError("Test error")
    ):
        record = comicvine_provider._parse_search_result(result)
        assert record is None

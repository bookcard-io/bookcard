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

"""Tests for Google Books metadata provider to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import httpx
import pytest

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from fundamental.metadata.providers.google import GoogleBooksProvider

if TYPE_CHECKING:
    from fundamental.models.metadata import MetadataRecord


@pytest.fixture
def google_provider() -> GoogleBooksProvider:
    """Create a GoogleBooksProvider instance for testing."""
    return GoogleBooksProvider(enabled=True)


def test_google_provider_init() -> None:
    """Test GoogleBooksProvider initialization (covers lines 68-79)."""
    provider = GoogleBooksProvider(enabled=True, timeout=15)
    assert provider.enabled is True
    assert provider.timeout == 15


def test_google_provider_get_source_info(google_provider: GoogleBooksProvider) -> None:
    """Test get_source_info (covers lines 81-94)."""
    source_info = google_provider.get_source_info()
    assert source_info.id == "google"
    assert source_info.name == "Google Books"
    assert source_info.base_url == "https://books.google.com/"


def test_google_provider_search_disabled(google_provider: GoogleBooksProvider) -> None:
    """Test search returns empty when disabled (covers line 127-128)."""
    google_provider.enabled = False
    result = google_provider.search("test query")
    assert result == []


def test_google_provider_search_empty_query(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search returns empty for empty query (covers lines 130-131)."""
    result = google_provider.search("")
    assert result == []

    result = google_provider.search("   ")
    assert result == []


def test_google_provider_search_success(google_provider: GoogleBooksProvider) -> None:
    """Test search succeeds with valid response (covers lines 133-173)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {
                "id": "test123",
                "volumeInfo": {
                    "title": "Test Book",
                    "authors": ["Test Author"],
                    "description": "Test description",
                },
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = google_provider.search("test query", max_results=10)

        assert len(results) == 1
        assert results[0].title == "Test Book"
        assert results[0].authors == ["Test Author"]


def test_google_provider_search_timeout(google_provider: GoogleBooksProvider) -> None:
    """Test search raises TimeoutError (covers lines 163-165)."""
    with (
        patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        google_provider.search("test query")


def test_google_provider_search_network_error(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search raises NetworkError (covers lines 166-168)."""
    with (
        patch("httpx.get", side_effect=httpx.RequestError("Network error")),
        pytest.raises(MetadataProviderNetworkError),
    ):
        google_provider.search("test query")


def test_google_provider_search_parse_error(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search raises ParseError (covers lines 169-171)."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(MetadataProviderParseError),
    ):
        google_provider.search("test query")


def test_google_provider_build_search_query(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _build_search_query (covers lines 175-190)."""
    result = google_provider._build_search_query("  test query  ")
    assert result == "test query"


def test_google_provider_parse_item_success(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item with valid item (covers lines 192-259)."""
    item = {
        "id": "test123",
        "volumeInfo": {
            "title": "Test Book",
            "authors": ["Author 1", "Author 2"],
            "description": "Test description",
            "publisher": "Test Publisher",
            "publishedDate": "2024-01-01",
            "averageRating": 4.5,
            "language": "en",
            "categories": ["Fiction", "Science Fiction"],
            "imageLinks": {
                "thumbnail": "http://example.com/thumb.jpg",
            },
            "industryIdentifiers": [
                {"type": "ISBN_13", "identifier": "9781234567890"},
            ],
        },
    }

    record = google_provider._parse_item(item)

    assert record is not None
    assert record.title == "Test Book"
    assert record.authors == ["Author 1", "Author 2"]
    assert record.external_id == "test123"
    assert record.url == "https://books.google.com/books?id=test123"
    assert record.publisher == "Test Publisher"
    assert record.rating == 4.5


def test_google_provider_parse_item_no_id(google_provider: GoogleBooksProvider) -> None:
    """Test _parse_item returns None when no ID (covers lines 209-210)."""
    item = {"volumeInfo": {"title": "Test Book"}}
    result = google_provider._parse_item(item)
    assert result is None


def test_google_provider_parse_item_no_title(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item returns None when no title (covers lines 219-220)."""
    item = {"id": "test123", "volumeInfo": {}}
    result = google_provider._parse_item(item)
    assert result is None


def test_google_provider_parse_item_no_volume_info(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles missing volumeInfo (covers lines 212-213)."""
    item = {"id": "test123"}
    result = google_provider._parse_item(item)
    assert result is None


def test_google_provider_parse_item_parse_error(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles parse errors (covers lines 261-263)."""
    # Item that will cause parsing error
    item = {"id": "test123", "volumeInfo": None}
    result = google_provider._parse_item(item)
    assert result is None


def test_google_provider_parse_item_exception(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles exceptions during parsing (covers lines 261-263)."""
    # Item that will raise an exception during parsing
    # Use a MagicMock for volumeInfo that raises an exception when accessed
    volume_info_mock = MagicMock()
    item = {
        "id": "test123",
        "volumeInfo": volume_info_mock,
    }
    # Make accessing volumeInfo raise an exception
    volume_info_mock.get.side_effect = KeyError("Missing title")

    result = google_provider._parse_item(item)
    assert result is None


def test_google_provider_extract_cover_url_thumbnail(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url with thumbnail (covers lines 265-298)."""
    volume_info = {
        "imageLinks": {
            "thumbnail": "http://example.com/thumb.jpg&edge=curl",
        },
    }
    result = google_provider._extract_cover_url(volume_info)
    assert result is not None
    assert "https://" in result
    assert "&edge=curl" not in result
    assert "&fife=w800-h900" in result


def test_google_provider_extract_cover_url_small(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url falls back to small (covers lines 283-286)."""
    volume_info = {
        "imageLinks": {
            "small": "http://example.com/small.jpg",
        },
    }
    result = google_provider._extract_cover_url(volume_info)
    assert result is not None
    assert "https://" in result


def test_google_provider_extract_cover_url_medium(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url falls back to medium (covers lines 283-286)."""
    volume_info = {
        "imageLinks": {
            "medium": "http://example.com/medium.jpg",
        },
    }
    result = google_provider._extract_cover_url(volume_info)
    assert result is not None
    assert "https://" in result


def test_google_provider_extract_cover_url_none(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url returns None when no images (covers lines 279-280)."""
    volume_info = {}
    result = google_provider._extract_cover_url(volume_info)
    assert result is None


def test_google_provider_extract_cover_url_empty_links(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url returns None when imageLinks exists but all values are None (covers line 290)."""
    # imageLinks exists but all get() calls return None, so cover_url will be falsy
    volume_info = {
        "imageLinks": {
            "thumbnail": None,
            "small": None,
            "medium": None,
        },
    }
    result = google_provider._extract_cover_url(volume_info)
    assert result is None


def test_google_provider_extract_cover_url_no_fife(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_cover_url adds fife parameter (covers lines 294-295)."""
    volume_info = {
        "imageLinks": {
            "thumbnail": "http://example.com/thumb.jpg",
        },
    }
    result = google_provider._extract_cover_url(volume_info)
    assert result is not None
    assert "&fife=w800-h900" in result


def test_google_provider_extract_identifiers(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_identifiers (covers lines 300-326)."""
    volume_info = {
        "industryIdentifiers": [
            {"type": "ISBN_13", "identifier": "9781234567890"},
            {"type": "ISBN_10", "identifier": "1234567890"},
            {"type": "OTHER", "identifier": "other123"},
        ],
    }
    result = google_provider._extract_identifiers(volume_info)
    assert "isbn" in result
    # The code processes identifiers in order and the last ISBN overwrites previous ones
    # Since ISBN_10 comes after ISBN_13, it will be the final value
    assert result["isbn"] == "1234567890"
    assert "other" in result
    assert result["other"] == "other123"


def test_google_provider_extract_identifiers_empty(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_identifiers with empty identifiers (covers lines 300-326)."""
    volume_info = {}
    result = google_provider._extract_identifiers(volume_info)
    assert result == {}


def test_google_provider_extract_series_info(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _extract_series_info (covers lines 328-346)."""
    volume_info = {}
    series, series_index = google_provider._extract_series_info(volume_info)
    assert series is None
    assert series_index is None


def test_google_provider_search_max_results_limit(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search respects API max results limit (covers line 138)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        google_provider.search("test", max_results=100)  # Request more than API limit

        # Verify maxResults is capped at 40
        call_args = mock_get.call_args
        assert call_args is not None
        assert call_args[1]["params"]["maxResults"] == 40


def test_google_provider_search_parse_item_error(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search handles item parse errors gracefully (covers lines 160-162)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"id": "valid", "volumeInfo": {"title": "Valid Book"}},
            {"id": "invalid", "volumeInfo": None},  # Will fail to parse
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = google_provider.search("test query")

        # Should return only valid items
        assert len(results) == 1
        assert results[0].title == "Valid Book"


def test_google_provider_search_parse_item_exception(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test search handles exceptions during item parsing (covers lines 160-162)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"id": "valid", "volumeInfo": {"title": "Valid Book"}},
            {
                "id": "error",
                "volumeInfo": {"title": "Error Book"},
            },  # Will raise exception
        ]
    }
    mock_response.raise_for_status = MagicMock()

    # Make _parse_item raise an exception for the second item
    original_parse = google_provider._parse_item
    call_count = [0]

    def parse_item_side_effect(item: dict) -> MetadataRecord | None:
        call_count[0] += 1
        if item.get("id") == "error":
            raise KeyError("Missing required field")
        return original_parse(item)

    with (
        patch("httpx.get", return_value=mock_response),
        patch.object(
            google_provider, "_parse_item", side_effect=parse_item_side_effect
        ),
    ):
        results = google_provider.search("test query")
        # Should return only valid items, exception should be caught and logged
        assert len(results) == 1
        assert results[0].title == "Valid Book"


def test_google_provider_parse_item_non_list_authors(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles non-list authors (covers line 245)."""
    item = {
        "id": "test123",
        "volumeInfo": {
            "title": "Test Book",
            "authors": "Single Author",  # Not a list
        },
    }
    record = google_provider._parse_item(item)
    assert record is not None
    assert record.authors == []  # Should default to empty list


def test_google_provider_parse_item_non_list_categories(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles non-list categories (covers line 258)."""
    item = {
        "id": "test123",
        "volumeInfo": {
            "title": "Test Book",
            "categories": "Fiction",  # Not a list
        },
    }
    record = google_provider._parse_item(item)
    assert record is not None
    assert record.tags == []  # Should default to empty list


def test_google_provider_parse_item_string_language(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles string language (covers lines 255-257)."""
    item = {
        "id": "test123",
        "volumeInfo": {
            "title": "Test Book",
            "language": "en",
        },
    }
    record = google_provider._parse_item(item)
    assert record is not None
    assert record.languages == ["en"]


def test_google_provider_parse_item_none_language(
    google_provider: GoogleBooksProvider,
) -> None:
    """Test _parse_item handles None language (covers lines 255-257)."""
    item = {
        "id": "test123",
        "volumeInfo": {
            "title": "Test Book",
            "language": None,
        },
    }
    record = google_provider._parse_item(item)
    assert record is not None
    assert record.languages == []

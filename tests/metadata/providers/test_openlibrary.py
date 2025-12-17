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

"""Tests for OpenLibrary metadata provider to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.metadata.providers.openlibrary import OpenLibraryProvider

if TYPE_CHECKING:
    from bookcard.models.metadata import MetadataRecord


@pytest.fixture
def openlibrary_provider() -> OpenLibraryProvider:
    """Create an OpenLibraryProvider instance for testing."""
    return OpenLibraryProvider(enabled=True)


@pytest.fixture
def openlibrary_provider_disabled() -> OpenLibraryProvider:
    """Create a disabled OpenLibraryProvider instance for testing."""
    return OpenLibraryProvider(enabled=False)


@pytest.fixture
def openlibrary_provider_custom_timeout() -> OpenLibraryProvider:
    """Create an OpenLibraryProvider instance with custom timeout."""
    return OpenLibraryProvider(enabled=True, timeout=15)


@pytest.fixture
def mock_search_response() -> dict:
    """Create a mock OpenLibrary search response."""
    return {
        "docs": [
            {
                "key": "/works/OL123456W",
                "title": "Test Book",
                "author_name": ["Test Author"],
                "cover_i": 123456,
                "isbn": ["9781234567890", "1234567890"],
                "publisher": ["Test Publisher"],
                "first_publish_year": 2024,
                "language": ["eng", "fre"],
                "subject": ["Fiction", "Science Fiction"],
                "first_sentence": [{"value": "This is a test description."}],
            }
        ]
    }


@pytest.fixture
def mock_search_response_empty() -> dict:
    """Create a mock empty OpenLibrary search response."""
    return {"docs": []}


@pytest.fixture
def mock_search_response_no_docs() -> dict:
    """Create a mock OpenLibrary response without docs key."""
    return {}


def test_openlibrary_provider_init() -> None:
    """Test OpenLibraryProvider initialization (covers lines 60-71)."""
    provider = OpenLibraryProvider(enabled=True, timeout=15)
    assert provider.enabled is True
    assert provider.timeout == 15


def test_openlibrary_provider_get_source_info(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test get_source_info (covers lines 73-86)."""
    source_info = openlibrary_provider.get_source_info()
    assert source_info.id == "openlibrary"
    assert source_info.name == "OpenLibrary"
    assert source_info.description == "OpenLibrary API"
    assert source_info.base_url == "https://openlibrary.org"


def test_openlibrary_provider_search_disabled(
    openlibrary_provider_disabled: OpenLibraryProvider,
) -> None:
    """Test search returns empty when disabled (covers lines 121-122)."""
    result = openlibrary_provider_disabled.search("test query")
    assert result == []


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "\t\n",
    ],
)
def test_openlibrary_provider_search_empty_query(
    openlibrary_provider: OpenLibraryProvider,
    query: str,
) -> None:
    """Test search returns empty for empty query (covers lines 124-125)."""
    result = openlibrary_provider.search(query)
    assert result == []


def test_openlibrary_provider_search_success(
    openlibrary_provider: OpenLibraryProvider,
    mock_search_response: dict,
) -> None:
    """Test search succeeds with valid response (covers lines 127-166)."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_search_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = openlibrary_provider.search("test query", max_results=10)

        assert len(results) == 1
        assert results[0].title == "Test Book"
        assert results[0].authors == ["Test Author"]
        assert results[0].external_id == "OL123456W"
        assert results[0].url == "https://openlibrary.org/works/OL123456W"
        assert (
            results[0].cover_url == "https://covers.openlibrary.org/b/id/123456-L.jpg"
        )
        assert results[0].publisher == "Test Publisher"
        assert results[0].published_date == "2024"
        assert results[0].languages == ["eng", "fre"]
        assert results[0].tags == ["Fiction", "Science Fiction"]
        assert results[0].description == "This is a test description."


def test_openlibrary_provider_search_timeout(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search raises TimeoutError (covers lines 156-158)."""
    with (
        patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        openlibrary_provider.search("test query")


def test_openlibrary_provider_search_network_error(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search raises NetworkError (covers lines 159-161)."""
    with (
        patch("httpx.get", side_effect=httpx.RequestError("Network error")),
        pytest.raises(MetadataProviderNetworkError),
    ):
        openlibrary_provider.search("test query")


def test_openlibrary_provider_search_parse_error(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search raises ParseError (covers lines 162-164)."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(MetadataProviderParseError),
    ):
        openlibrary_provider.search("test query")


def test_openlibrary_provider_search_parse_error_keyerror(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search raises ParseError on KeyError (covers lines 162-164)."""
    # Test with response that causes KeyError during parsing
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    # Make json() raise a KeyError which will be caught and re-raised as ParseError
    mock_response.json.side_effect = KeyError("Missing key")

    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(MetadataProviderParseError),
    ):
        openlibrary_provider.search("test query")


def test_openlibrary_provider_search_max_results_limit(
    openlibrary_provider: OpenLibraryProvider,
    mock_search_response: dict,
) -> None:
    """Test search respects API max results limit (covers line 132)."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_search_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        openlibrary_provider.search(
            "test", max_results=200
        )  # Request more than API limit

        # Verify limit is capped at 100
        call_args = mock_get.call_args
        assert call_args is not None
        assert call_args[1]["params"]["limit"] == 100


def test_openlibrary_provider_search_limits_results(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search limits results to max_results (covers line 148)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "docs": [{"key": "/works/OL1W", "title": f"Book {i}"} for i in range(20)]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = openlibrary_provider.search("test", max_results=5)
        assert len(results) == 5


def test_openlibrary_provider_build_search_query(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _build_search_query (covers lines 168-182)."""
    result = openlibrary_provider._build_search_query("  test query  ")
    assert result == "test query"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("test", "test"),
        ("  test  ", "test"),
        ("\ttest\n", "test"),
    ],
)
def test_openlibrary_provider_build_search_query_variations(
    openlibrary_provider: OpenLibraryProvider,
    query: str,
    expected: str,
) -> None:
    """Test _build_search_query with various inputs (covers line 182)."""
    result = openlibrary_provider._build_search_query(query)
    assert result == expected


def test_openlibrary_provider_parse_search_doc_success(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc with valid doc (covers lines 184-269)."""
    doc = {
        "key": "/works/OL123456W",
        "title": "Test Book",
        "author_name": ["Author 1", "Author 2"],
        "cover_i": 123456,
        "isbn": ["9781234567890", "1234567890"],
        "oclc": ["123456"],
        "lccn": ["987654"],
        "publisher": ["Test Publisher"],
        "first_publish_year": 2024,
        "language": ["eng", "fre"],
        "subject": ["Fiction", "Science Fiction"],
        "first_sentence": [{"value": "This is a test description."}],
    }

    record = openlibrary_provider._parse_search_doc(doc)

    assert record is not None
    assert record.title == "Test Book"
    assert record.authors == ["Author 1", "Author 2"]
    assert record.external_id == "OL123456W"
    assert record.url == "https://openlibrary.org/works/OL123456W"
    assert record.cover_url == "https://covers.openlibrary.org/b/id/123456-L.jpg"
    assert record.description == "This is a test description."
    assert record.publisher == "Test Publisher"
    assert record.published_date == "2024"
    assert record.languages == ["eng", "fre"]
    assert record.tags == ["Fiction", "Science Fiction"]
    assert "isbn" in record.identifiers
    assert "isbn13" in record.identifiers
    assert record.identifiers["oclc"] == "123456"
    assert record.identifiers["lccn"] == "987654"
    assert record.rating is None
    assert record.series is None
    assert record.series_index is None


def test_openlibrary_provider_parse_search_doc_no_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc returns None when no key (covers lines 199-201)."""
    doc = {"title": "Test Book"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_parse_search_doc_empty_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc returns None when key is empty (covers lines 199-201)."""
    doc = {"key": "", "title": "Test Book"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_parse_search_doc_no_title(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc returns None when no title (covers lines 209-213)."""
    doc = {"key": "/works/OL123456W"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_parse_search_doc_empty_title(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc returns None when title is empty (covers lines 209-213)."""
    doc = {"key": "/works/OL123456W", "title": ""}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_parse_search_doc_normalized_key_works(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc normalizes /works/ key (covers lines 203-206)."""
    doc = {"key": "/works/OL123456W", "title": "Test Book"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is not None
    assert result.external_id == "OL123456W"


def test_openlibrary_provider_parse_search_doc_normalized_key_books(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc normalizes /books/ key (covers lines 203-206)."""
    doc = {"key": "/books/OL123456B", "title": "Test Book"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is not None
    assert result.external_id == "OL123456B"


def test_openlibrary_provider_parse_search_doc_normalized_key_empty(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc returns None when normalized key is empty (covers lines 203-206)."""
    doc = {"key": "/works/", "title": "Test Book"}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


@pytest.mark.parametrize(
    ("first_sentence", "expected"),
    [
        ([{"value": "Test description."}], "Test description."),
        ({"value": "Test description."}, "Test description."),
        ("Test description.", "Test description."),
        ([], None),
        (None, None),
        ([{"value": ""}], ""),
    ],
)
def test_openlibrary_provider_parse_search_doc_description_variations(
    openlibrary_provider: OpenLibraryProvider,
    first_sentence: list | dict | str | None,
    expected: str | None,
) -> None:
    """Test _parse_search_doc handles various description formats (covers lines 219-229)."""
    doc = {
        "key": "/works/OL123456W",
        "title": "Test Book",
        "first_sentence": first_sentence,
    }
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is not None
    assert result.description == expected


def test_openlibrary_provider_parse_search_doc_description_list_non_dict(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc handles list with non-dict first element (covers lines 220-225)."""
    doc = {
        "key": "/works/OL123456W",
        "title": "Test Book",
        "first_sentence": ["Test description."],
    }
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is not None
    assert result.description == "Test description."


def test_openlibrary_provider_parse_search_doc_parse_error(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc handles parse errors (covers lines 271-273)."""
    # Doc that will cause parsing error
    doc = {"key": "/works/OL123456W", "title": None}
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_parse_search_doc_exception(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _parse_search_doc handles exceptions during parsing (covers lines 271-273)."""
    # Doc that will raise an exception during parsing
    doc = MagicMock()
    doc.get.side_effect = KeyError("Missing field")
    result = openlibrary_provider._parse_search_doc(doc)
    assert result is None


def test_openlibrary_provider_search_parse_doc_error(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search handles doc parse errors gracefully (covers lines 149-155)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "docs": [
            {"key": "/works/OL1W", "title": "Valid Book"},
            {"key": "/works/OL2W"},  # Missing title, will fail to parse
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = openlibrary_provider.search("test query")

        # Should return only valid items
        assert len(results) == 1
        assert results[0].title == "Valid Book"


def test_openlibrary_provider_search_parse_doc_exception(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test search handles exceptions during doc parsing (covers lines 149-155)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "docs": [
            {"key": "/works/OL1W", "title": "Valid Book"},
            {"key": "/works/OL2W", "title": "Error Book"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    # Make _parse_search_doc raise an exception for the second doc
    original_parse = openlibrary_provider._parse_search_doc
    call_count = [0]

    def parse_doc_side_effect(doc: dict) -> MetadataRecord | None:
        call_count[0] += 1
        if doc.get("key") == "/works/OL2W":
            raise KeyError("Missing required field")
        return original_parse(doc)

    with (
        patch("httpx.get", return_value=mock_response),
        patch.object(
            openlibrary_provider,
            "_parse_search_doc",
            side_effect=parse_doc_side_effect,
        ),
    ):
        results = openlibrary_provider.search("test query")
        # Should return only valid items, exception should be caught and logged
        assert len(results) == 1
        assert results[0].title == "Valid Book"


@pytest.mark.parametrize(
    ("author_name", "expected"),
    [
        (["Author 1", "Author 2"], ["Author 1", "Author 2"]),
        (["Author 1"], ["Author 1"]),
        ([], []),
        (["Author 1", "", "Author 2"], ["Author 1", "Author 2"]),
        (["Author 1", None, "Author 2"], ["Author 1", "Author 2"]),
    ],
)
def test_openlibrary_provider_extract_authors(
    openlibrary_provider: OpenLibraryProvider,
    author_name: list,
    expected: list[str],
) -> None:
    """Test _extract_authors (covers lines 275-291)."""
    doc = {"author_name": author_name}
    result = openlibrary_provider._extract_authors(doc)
    assert result == expected


def test_openlibrary_provider_extract_authors_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_authors returns empty list when not a list (covers lines 288-291)."""
    doc = {"author_name": "Single Author"}
    result = openlibrary_provider._extract_authors(doc)
    assert result == []


def test_openlibrary_provider_extract_authors_missing_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_authors returns empty list when key missing (covers lines 288-291)."""
    doc = {}
    result = openlibrary_provider._extract_authors(doc)
    assert result == []


@pytest.mark.parametrize(
    ("cover_i", "expected"),
    [
        (123456, "https://covers.openlibrary.org/b/id/123456-L.jpg"),
        (1, "https://covers.openlibrary.org/b/id/1-L.jpg"),
        (None, None),
    ],
)
def test_openlibrary_provider_extract_cover_url(
    openlibrary_provider: OpenLibraryProvider,
    cover_i: int | None,
    expected: str | None,
) -> None:
    """Test _extract_cover_url (covers lines 293-309)."""
    doc = {"cover_i": cover_i}
    result = openlibrary_provider._extract_cover_url(doc)
    assert result == expected


def test_openlibrary_provider_extract_cover_url_not_int(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_cover_url returns None when not int (covers lines 306-309)."""
    doc = {"cover_i": "123456"}
    result = openlibrary_provider._extract_cover_url(doc)
    assert result is None


def test_openlibrary_provider_extract_cover_url_zero(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_cover_url returns None when cover_i is 0 (covers lines 306-309)."""
    # 0 is falsy in Python, so the check `if cover_id and isinstance(cover_id, int)` fails
    doc = {"cover_i": 0}
    result = openlibrary_provider._extract_cover_url(doc)
    assert result is None


def test_openlibrary_provider_extract_cover_url_missing_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_cover_url returns None when key missing (covers lines 306-309)."""
    doc = {}
    result = openlibrary_provider._extract_cover_url(doc)
    assert result is None


@pytest.mark.parametrize(
    ("isbn", "expected_isbn", "expected_isbn13"),
    [
        (["1234567890"], "1234567890", None),
        (["9781234567890"], None, "9781234567890"),
        (["1234567890", "9781234567890"], "1234567890", "9781234567890"),
        (["12345"], "12345", None),  # Unclear type, uses first
        ([], None, None),
    ],
)
def test_openlibrary_provider_extract_identifiers_isbn(
    openlibrary_provider: OpenLibraryProvider,
    isbn: list[str],
    expected_isbn: str | None,
    expected_isbn13: str | None,
) -> None:
    """Test _extract_identifiers with ISBNs (covers lines 311-350)."""
    doc = {"isbn": isbn}
    result = openlibrary_provider._extract_identifiers(doc)
    if expected_isbn:
        assert result["isbn"] == expected_isbn
    if expected_isbn13:
        assert result["isbn13"] == expected_isbn13


def test_openlibrary_provider_extract_identifiers_isbn_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers handles non-list ISBN (covers lines 327-340)."""
    doc = {"isbn": "1234567890"}
    result = openlibrary_provider._extract_identifiers(doc)
    assert result == {}


def test_openlibrary_provider_extract_identifiers_isbn_empty_strings(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers filters empty ISBN strings (covers lines 327-340)."""
    doc = {"isbn": ["", "   ", "1234567890"]}
    result = openlibrary_provider._extract_identifiers(doc)
    assert result["isbn"] == "1234567890"


def test_openlibrary_provider_extract_identifiers_oclc(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers with OCLC (covers lines 342-344)."""
    doc = {"oclc": ["123456"]}
    result = openlibrary_provider._extract_identifiers(doc)
    assert result["oclc"] == "123456"


def test_openlibrary_provider_extract_identifiers_oclc_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers handles non-list OCLC (covers lines 342-344)."""
    doc = {"oclc": "123456"}
    result = openlibrary_provider._extract_identifiers(doc)
    assert "oclc" not in result


def test_openlibrary_provider_extract_identifiers_oclc_empty(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers handles empty OCLC list (covers lines 342-344)."""
    doc = {"oclc": []}
    result = openlibrary_provider._extract_identifiers(doc)
    assert "oclc" not in result


def test_openlibrary_provider_extract_identifiers_lccn(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers with LCCN (covers lines 346-348)."""
    doc = {"lccn": ["987654"]}
    result = openlibrary_provider._extract_identifiers(doc)
    assert result["lccn"] == "987654"


def test_openlibrary_provider_extract_identifiers_lccn_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers handles non-list LCCN (covers lines 346-348)."""
    doc = {"lccn": "987654"}
    result = openlibrary_provider._extract_identifiers(doc)
    assert "lccn" not in result


def test_openlibrary_provider_extract_identifiers_lccn_empty(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers handles empty LCCN list (covers lines 346-348)."""
    doc = {"lccn": []}
    result = openlibrary_provider._extract_identifiers(doc)
    assert "lccn" not in result


def test_openlibrary_provider_extract_identifiers_all(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_identifiers with all identifier types (covers lines 324-350)."""
    doc = {
        "isbn": ["1234567890", "9781234567890"],
        "oclc": ["123456"],
        "lccn": ["987654"],
    }
    result = openlibrary_provider._extract_identifiers(doc)
    assert result["isbn"] == "1234567890"
    assert result["isbn13"] == "9781234567890"
    assert result["oclc"] == "123456"
    assert result["lccn"] == "987654"


def test_openlibrary_provider_extract_series_info(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_series_info (covers lines 352-368)."""
    doc = {}
    series, series_index = openlibrary_provider._extract_series_info(doc)
    assert series is None
    assert series_index is None


@pytest.mark.parametrize(
    ("publisher", "expected"),
    [
        (["Publisher 1"], "Publisher 1"),
        (["Publisher 1", "Publisher 2"], "Publisher 1"),
        ([], None),
        (None, None),
    ],
)
def test_openlibrary_provider_extract_publisher(
    openlibrary_provider: OpenLibraryProvider,
    publisher: list[str] | None,
    expected: str | None,
) -> None:
    """Test _extract_publisher (covers lines 370-386)."""
    doc = {"publisher": publisher}
    result = openlibrary_provider._extract_publisher(doc)
    assert result == expected


def test_openlibrary_provider_extract_publisher_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_publisher returns None when not a list (covers lines 383-386)."""
    doc = {"publisher": "Single Publisher"}
    result = openlibrary_provider._extract_publisher(doc)
    assert result is None


def test_openlibrary_provider_extract_publisher_missing_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_publisher returns None when key missing (covers lines 383-386)."""
    doc = {}
    result = openlibrary_provider._extract_publisher(doc)
    assert result is None


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (["eng", "fre"], ["eng", "fre"]),
        (["eng"], ["eng"]),
        ([], []),
        (["eng", "", "fre"], ["eng", "fre"]),
        (["eng", None, "fre"], ["eng", "fre"]),
    ],
)
def test_openlibrary_provider_extract_languages(
    openlibrary_provider: OpenLibraryProvider,
    language: list,
    expected: list[str],
) -> None:
    """Test _extract_languages (covers lines 388-404)."""
    doc = {"language": language}
    result = openlibrary_provider._extract_languages(doc)
    assert result == expected


def test_openlibrary_provider_extract_languages_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_languages returns empty list when not a list (covers lines 401-404)."""
    doc = {"language": "eng"}
    result = openlibrary_provider._extract_languages(doc)
    assert result == []


def test_openlibrary_provider_extract_languages_missing_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_languages returns empty list when key missing (covers lines 401-404)."""
    doc = {}
    result = openlibrary_provider._extract_languages(doc)
    assert result == []


@pytest.mark.parametrize(
    ("subject", "expected"),
    [
        (["Fiction", "Science Fiction"], ["Fiction", "Science Fiction"]),
        (["Fiction"], ["Fiction"]),
        ([], []),
        (["Fiction", "", "Science Fiction"], ["Fiction", "Science Fiction"]),
        (["Fiction", None, "Science Fiction"], ["Fiction", "Science Fiction"]),
    ],
)
def test_openlibrary_provider_extract_tags(
    openlibrary_provider: OpenLibraryProvider,
    subject: list,
    expected: list[str],
) -> None:
    """Test _extract_tags (covers lines 406-422)."""
    doc = {"subject": subject}
    result = openlibrary_provider._extract_tags(doc)
    assert result == expected


def test_openlibrary_provider_extract_tags_not_list(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_tags returns empty list when not a list (covers lines 419-422)."""
    doc = {"subject": "Fiction"}
    result = openlibrary_provider._extract_tags(doc)
    assert result == []


def test_openlibrary_provider_extract_tags_missing_key(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test _extract_tags returns empty list when key missing (covers lines 419-422)."""
    doc = {}
    result = openlibrary_provider._extract_tags(doc)
    assert result == []


def test_openlibrary_provider_search_empty_docs(
    openlibrary_provider: OpenLibraryProvider,
    mock_search_response_empty: dict,
) -> None:
    """Test search with empty docs (covers lines 145-166)."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_search_response_empty
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = openlibrary_provider.search("test query")
        assert results == []


def test_openlibrary_provider_search_no_docs_key(
    openlibrary_provider: OpenLibraryProvider,
    mock_search_response_no_docs: dict,
) -> None:
    """Test search with no docs key (covers lines 145-166)."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_search_response_no_docs
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = openlibrary_provider.search("test query")
        assert results == []


def test_openlibrary_provider_search_http_status_error_escapes(
    openlibrary_provider: OpenLibraryProvider,
) -> None:
    """Test that HTTPStatusError from raise_for_status escapes (covers line 141).

    Note: HTTPStatusError is not a subclass of RequestError, so it won't be caught
    by the current exception handler. This test documents the current behavior.
    The raise_for_status() call on line 141 is covered by successful search tests.
    """
    mock_request = MagicMock()
    mock_response_obj = MagicMock()
    mock_response_obj.status_code = 404

    def raise_http_error() -> None:
        raise httpx.HTTPStatusError(
            "Not Found", request=mock_request, response=mock_response_obj
        )

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = raise_http_error

    # HTTPStatusError is not caught by RequestError handler, so it escapes
    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(httpx.HTTPStatusError),
    ):
        openlibrary_provider.search("test query")

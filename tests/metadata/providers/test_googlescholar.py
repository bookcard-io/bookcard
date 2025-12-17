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

"""Tests for Google Scholar metadata provider to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.metadata.base import (
    MetadataProviderError,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)
from bookcard.metadata.providers.googlescholar import GoogleScholarProvider

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import ModuleType


@pytest.fixture
def googlescholar_provider() -> GoogleScholarProvider:
    """Create a GoogleScholarProvider instance for testing."""
    return GoogleScholarProvider(enabled=True)


def test_googlescholar_provider_init() -> None:
    """Test GoogleScholarProvider initialization."""
    provider = GoogleScholarProvider(enabled=True, timeout=25)
    assert provider.enabled is True
    assert provider.timeout == 25


def test_googlescholar_provider_init_scholarly_unavailable() -> None:
    """Test GoogleScholarProvider initialization when scholarly unavailable."""
    with patch("bookcard.metadata.providers.googlescholar.scholarly", None):
        provider = GoogleScholarProvider(enabled=True)
        assert provider.enabled is False


def test_googlescholar_provider_get_source_info(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test get_source_info."""
    source_info = googlescholar_provider.get_source_info()
    assert source_info.id == "googlescholar"
    assert source_info.name == "Google Scholar"
    assert source_info.base_url == "https://scholar.google.com/"


def test_googlescholar_provider_is_enabled(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test is_enabled."""
    assert googlescholar_provider.is_enabled() is True

    googlescholar_provider.enabled = False
    assert googlescholar_provider.is_enabled() is False


def test_googlescholar_provider_is_enabled_scholarly_unavailable() -> None:
    """Test is_enabled returns False when scholarly unavailable."""
    with patch("bookcard.metadata.providers.googlescholar.scholarly", None):
        provider = GoogleScholarProvider(enabled=True)
        assert provider.is_enabled() is False


def test_googlescholar_provider_search_disabled(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search returns empty when disabled."""
    googlescholar_provider.enabled = False
    result = googlescholar_provider.search("test query")
    assert result == []


def test_googlescholar_provider_search_empty_query(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search returns empty for empty query."""
    result = googlescholar_provider.search("")
    assert result == []

    result = googlescholar_provider.search("   ")
    assert result == []


def test_googlescholar_provider_search_scholarly_unavailable(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search raises error when scholarly unavailable."""
    # The code checks is_enabled() first, which returns False if scholarly is None
    # So it returns [] instead of raising an error
    # To test the error case, we need to make is_enabled() return True but scholarly be None
    # This can happen if scholarly becomes None after initialization
    googlescholar_provider.enabled = True
    # Patch scholarly to be None at search time
    with (
        patch("bookcard.metadata.providers.googlescholar.scholarly", None),
        patch.object(googlescholar_provider, "is_enabled", return_value=True),
        pytest.raises(MetadataProviderError),
    ):
        googlescholar_provider.search("test query")


def test_googlescholar_provider_search_success(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search succeeds with valid response."""
    mock_result = {
        "bib": {
            "title": "Test Paper",
            "author": ["Author 1", "Author 2"],
            "abstract": "Test abstract",
            "venue": "Test Journal",
            "pub_year": "2024",
        },
        "pub_url": "http://example.com/paper",
        "pub_id": "test123",
        "num_citations": 10,
    }

    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.return_value = iter([mock_result])
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly):
        results = googlescholar_provider.search("test query", max_results=1)
        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].authors == ["Author 1", "Author 2"]


def test_googlescholar_provider_search_timeout(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search raises NetworkError on timeout."""
    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.side_effect = TimeoutError("Timeout")
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with (
        patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly),
        pytest.raises(MetadataProviderNetworkError),
    ):
        googlescholar_provider.search("test query")


def test_googlescholar_provider_search_connection_error(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search raises NetworkError on connection error."""
    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.side_effect = ConnectionError("Connection error")
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with (
        patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly),
        pytest.raises(MetadataProviderNetworkError),
    ):
        googlescholar_provider.search("test query")


def test_googlescholar_provider_search_parse_error(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search raises ParseError on other exceptions."""
    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.side_effect = ValueError("Parse error")
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with (
        patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly),
        pytest.raises(MetadataProviderParseError),
    ):
        googlescholar_provider.search("test query")


def test_googlescholar_provider_prepare_query(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _prepare_query."""
    query = googlescholar_provider._prepare_query("test book query")
    assert "test" in query
    assert "book" in query
    assert "query" in query


def test_googlescholar_provider_prepare_query_short_tokens(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _prepare_query filters short tokens."""
    query = googlescholar_provider._prepare_query("a b c")
    assert query == ""


def test_googlescholar_provider_parse_search_result_success(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _parse_search_result with valid result."""
    result = {
        "bib": {
            "title": "Test Paper",
            "author": ["Author 1", "Author 2"],
            "abstract": "Test%20abstract",
            "venue": "Test Journal",
            "pub_year": "2024",
        },
        "pub_url": "http://example.com/paper",
        "pub_id": "test123",
        "num_citations": 10,
    }
    record = googlescholar_provider._parse_search_result(result)
    assert record is not None
    assert record.title == "Test Paper"
    assert record.authors == ["Author 1", "Author 2"]
    assert record.external_id == "http://example.com/paper"


def test_googlescholar_provider_parse_search_result_no_bib(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _parse_search_result returns None when no bib."""
    result = {}
    record = googlescholar_provider._parse_search_result(result)
    assert record is None


def test_googlescholar_provider_parse_search_result_error(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _parse_search_result handles parsing errors."""
    result = {"bib": None}
    record = googlescholar_provider._parse_search_result(result)
    assert record is None


def test_googlescholar_provider_extract_authors_list(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_authors with list."""
    bib = {"author": ["Author 1", "Author 2"]}
    authors = googlescholar_provider._extract_authors(bib)
    assert authors == ["Author 1", "Author 2"]


def test_googlescholar_provider_extract_authors_string(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_authors with string."""
    bib = {"author": "Author 1 and Author 2"}
    authors = googlescholar_provider._extract_authors(bib)
    assert "Author 1" in authors
    assert "Author 2" in authors


def test_googlescholar_provider_extract_authors_not_list(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_authors with non-list."""
    bib = {"author": 123}
    authors = googlescholar_provider._extract_authors(bib)
    assert authors == []


def test_googlescholar_provider_extract_urls_pub_url(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_urls with pub_url."""
    result = {"pub_url": "http://example.com/paper", "pub_id": "test123"}
    url, external_id = googlescholar_provider._extract_urls(result)
    assert url == "http://example.com/paper"
    assert external_id == "http://example.com/paper"


def test_googlescholar_provider_extract_urls_eprint_url(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_urls with eprint_url."""
    result = {"eprint_url": "http://example.com/eprint", "pub_id": "test123"}
    url, external_id = googlescholar_provider._extract_urls(result)
    assert url == "http://example.com/eprint"
    assert external_id == "http://example.com/eprint"


def test_googlescholar_provider_extract_urls_pub_id(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_urls generates URL from pub_id."""
    result = {"pub_id": "test123"}
    url, external_id = googlescholar_provider._extract_urls(result)
    assert "test123" in url
    # The code does: external_id = url or result.get("pub_id", "")
    # Since url is generated from pub_id, external_id will be the URL, not just pub_id
    assert external_id == url  # external_id is the generated URL


def test_googlescholar_provider_extract_urls_fallback(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_urls fallback."""
    result = {}
    url, external_id = googlescholar_provider._extract_urls(result)
    assert url == ""
    assert external_id == ""


def test_googlescholar_provider_extract_cover_url(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_cover_url."""
    result = {"image": {"original_url": "http://example.com/image.jpg"}}
    cover_url = googlescholar_provider._extract_cover_url(result)
    assert cover_url == "http://example.com/image.jpg"


def test_googlescholar_provider_extract_cover_url_not_dict(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_cover_url handles non-dict image."""
    result = {"image": "not a dict"}
    cover_url = googlescholar_provider._extract_cover_url(result)
    assert cover_url is None


def test_googlescholar_provider_extract_description(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_description."""
    bib = {"abstract": "Test%20abstract"}
    description = googlescholar_provider._extract_description(bib)
    assert "Test abstract" in description


def test_googlescholar_provider_extract_description_empty(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_description with empty abstract."""
    bib = {"abstract": ""}
    description = googlescholar_provider._extract_description(bib)
    assert description == ""


def test_googlescholar_provider_extract_published_date(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_published_date."""
    bib = {"pub_year": "2024"}
    published_date = googlescholar_provider._extract_published_date(bib)
    assert published_date == "2024-01-01"


def test_googlescholar_provider_extract_published_date_none(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_published_date returns None when no year."""
    bib = {}
    published_date = googlescholar_provider._extract_published_date(bib)
    assert published_date is None


def test_googlescholar_provider_build_identifiers(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _build_identifiers."""
    identifiers = googlescholar_provider._build_identifiers("test123")
    assert "scholar" in identifiers
    assert identifiers["scholar"] == "test123"


def test_googlescholar_provider_build_identifiers_empty(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _build_identifiers with empty external_id."""
    identifiers = googlescholar_provider._build_identifiers("")
    assert identifiers == {}


def test_googlescholar_provider_extract_tags(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_tags."""
    result = {"num_citations": 10}
    tags = googlescholar_provider._extract_tags(result)
    assert len(tags) == 1
    assert "10" in tags[0]


def test_googlescholar_provider_extract_tags_zero(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_tags with zero citations."""
    result = {"num_citations": 0}
    tags = googlescholar_provider._extract_tags(result)
    assert tags == []


def test_googlescholar_provider_extract_tags_missing(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _extract_tags with missing num_citations."""
    result = {}
    tags = googlescholar_provider._extract_tags(result)
    assert tags == []


def test_googlescholar_provider_search_parse_error_in_result(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search handles parse errors in individual results."""
    mock_result1 = {
        "bib": {
            "title": "Valid Paper",
            "author": ["Author 1"],
        },
        "pub_url": "http://example.com/paper1",
    }
    mock_result2 = {"bib": None}  # Will fail to parse

    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.return_value = iter([mock_result1, mock_result2])
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly):
        results = googlescholar_provider.search("test query", max_results=10)
        # Should return only valid results
        assert len(results) == 1
        assert results[0].title == "Valid Paper"


def test_googlescholar_provider_search_max_results(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test search respects max_results limit."""
    mock_results = [
        {
            "bib": {
                "title": f"Paper {i}",
                "author": ["Author"],
            },
            "pub_url": f"http://example.com/paper{i}",
        }
        for i in range(20)
    ]

    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.return_value = iter(mock_results)
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly):
        results = googlescholar_provider.search("test query", max_results=5)
        assert len(results) == 5


def test_googlescholar_provider_prepare_query_empty(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _prepare_query returns empty for invalid query."""
    query = googlescholar_provider._prepare_query("")
    assert query == ""


def test_googlescholar_provider_import_error_handling() -> None:
    """Test ImportError handling when scholarly is not available (covers lines 38-39, 82-86)."""
    import importlib
    import sys

    # Store original module if it exists
    module_name = "bookcard.metadata.providers.googlescholar"
    original_module = sys.modules.get(module_name)

    # Remove from sys.modules to allow reimport
    if module_name in sys.modules:
        del sys.modules[module_name]

    try:
        # Create a mock that raises ImportError when importing scholarly
        def mock_import(
            name: str,
            globals_dict: Mapping[str, object] | None = None,
            locals_dict: Mapping[str, object] | None = None,
            fromlist: Sequence[str] | None = (),
            level: int = 0,
        ) -> ModuleType:
            if name == "scholarly":
                raise ImportError("No module named 'scholarly'")
            # For other imports, use the real import
            # Type ignore needed because __import__ has complex overloads
            return importlib.__import__(  # type: ignore[call-overload]
                name, globals_dict, locals_dict, fromlist, level
            )

        # Patch __import__ to raise ImportError for scholarly
        with patch("builtins.__import__", side_effect=mock_import):
            # Reimport the module - this will trigger the ImportError handling
            importlib.import_module(module_name)
            # Import the class after the module is loaded
            from bookcard.metadata.providers.googlescholar import (
                GoogleScholarProvider,
            )

            provider = GoogleScholarProvider(enabled=True)
            assert provider.enabled is False
    finally:
        # Restore the original module
        if module_name in sys.modules:
            del sys.modules[module_name]
        if original_module is not None:
            sys.modules[module_name] = original_module
        # Reimport to restore original state
        if original_module is None:
            importlib.import_module(module_name)


def test_googlescholar_provider_perform_search_empty_query(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _perform_search returns empty when query is empty (covers line 184)."""
    mock_scholarly = MagicMock()
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    with patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly):
        results = googlescholar_provider._perform_search("a", max_results=10)
        assert results == []


def test_googlescholar_provider_perform_search_parse_exception(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _perform_search handles parse exceptions (covers lines 200-202)."""
    mock_result = {
        "bib": {
            "title": "Test Paper",
            "author": ["Author 1"],
        },
        "pub_url": "http://example.com/paper",
    }

    mock_scholarly = MagicMock()
    mock_scholarly.search_pubs.return_value = iter([mock_result])
    mock_scholarly.set_timeout = MagicMock()
    mock_scholarly.set_retries = MagicMock()

    # Make _parse_search_result raise an exception
    with (
        patch("bookcard.metadata.providers.googlescholar.scholarly", mock_scholarly),
        patch.object(
            googlescholar_provider,
            "_parse_search_result",
            side_effect=KeyError("Test error"),
        ),
    ):
        results = googlescholar_provider._perform_search("test query", max_results=10)
        # Should handle the exception and continue
        assert len(results) == 0


def test_googlescholar_provider_parse_search_result_no_title(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _parse_search_result returns None when no title (covers line 250)."""
    result = {
        "bib": {
            "author": ["Author 1"],
        },
    }
    record = googlescholar_provider._parse_search_result(result)
    assert record is None


def test_googlescholar_provider_parse_search_result_exception(
    googlescholar_provider: GoogleScholarProvider,
) -> None:
    """Test _parse_search_result handles exceptions (covers lines 280-282)."""
    # Result that will cause an exception during parsing
    # Make _extract_authors raise an exception
    result = {
        "bib": {
            "title": "Test Paper",
            "author": None,  # Will cause exception in _extract_authors
        },
        "pub_url": "http://example.com/paper",
    }

    # Mock _extract_authors to raise an exception
    with patch.object(
        googlescholar_provider, "_extract_authors", side_effect=TypeError("Test error")
    ):
        record = googlescholar_provider._parse_search_result(result)
        assert record is None

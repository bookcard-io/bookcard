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

"""Tests for IdentifiersExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.metadata.providers._hardcover.extractors.identifiers import (
    IdentifiersExtractor,
)


@pytest.fixture
def book_data_with_edition_isbns() -> dict:
    """Create book data with edition ISBNs."""
    return {
        "editions": [
            {
                "isbn_13": "9781234567890",
                "isbn_10": "1234567890",
            }
        ]
    }


@pytest.fixture
def book_data_with_isbns() -> dict:
    """Create book data with isbns array."""
    return {
        "isbns": ["9781234567890", "1234567890", "9780987654321"],
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_editions(
    book_data_with_edition_isbns: dict,
) -> None:
    """Test extraction from editions (covers lines 38-44)."""
    result = IdentifiersExtractor.extract(book_data_with_edition_isbns)
    assert result["isbn13"] == "9781234567890"
    assert result["isbn"] == "1234567890"


def test_extract_from_editions_isbn13_only(
    book_data_with_edition_isbns: dict,
) -> None:
    """Test extraction from editions with only ISBN-13 (covers lines 60-72)."""
    book_data_with_edition_isbns["editions"][0].pop("isbn_10")
    result = IdentifiersExtractor.extract(book_data_with_edition_isbns)
    assert result["isbn13"] == "9781234567890"
    assert "isbn" not in result


def test_extract_from_editions_isbn10_only(
    book_data_with_edition_isbns: dict,
) -> None:
    """Test extraction from editions with only ISBN-10 (covers lines 60-72)."""
    book_data_with_edition_isbns["editions"][0].pop("isbn_13")
    result = IdentifiersExtractor.extract(book_data_with_edition_isbns)
    assert result["isbn"] == "1234567890"
    assert "isbn13" not in result


def test_extract_from_editions_no_edition() -> None:
    """Test extraction with no edition (covers lines 60-63)."""
    book_data = {"editions": []}
    result = IdentifiersExtractor._extract_from_editions(book_data)
    assert result == {}


def test_extract_from_isbns_10_digit(
    book_data_with_isbns: dict,
) -> None:
    """Test extraction from isbns array with 10-digit ISBN (covers lines 88-107)."""
    book_data = {"isbns": ["1234567890"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn"] == "1234567890"


def test_extract_from_isbns_13_digit(
    book_data_with_isbns: dict,
) -> None:
    """Test extraction from isbns array with 13-digit ISBN (covers lines 88-107)."""
    book_data = {"isbns": ["9781234567890"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn13"] == "9781234567890"


def test_extract_from_isbns_mixed(
    book_data_with_isbns: dict,
) -> None:
    """Test extraction from isbns array with mixed ISBNs (covers lines 88-107)."""
    result = IdentifiersExtractor._extract_from_isbns(book_data_with_isbns)
    assert result["isbn13"] == "9781234567890"
    assert result["isbn"] == "1234567890"


def test_extract_from_isbns_other_length(
    book_data_with_isbns: dict,
) -> None:
    """Test extraction from isbns array with other length ISBN (covers lines 88-107)."""
    book_data = {"isbns": ["12345"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn"] == "12345"


def test_extract_from_isbns_not_list() -> None:
    """Test extraction from isbns not a list (covers lines 88-91)."""
    book_data = {"isbns": "not a list"}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result == {}


def test_extract_from_isbns_empty_list() -> None:
    """Test extraction from empty isbns list (covers lines 88-107)."""
    book_data = {"isbns": []}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result == {}


def test_extract_from_isbns_with_falsy() -> None:
    """Test extraction from isbns with falsy values (covers lines 88-107)."""
    book_data = {"isbns": ["", None, 0, "1234567890"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn"] == "1234567890"


def test_extract_from_isbns_whitespace() -> None:
    """Test extraction from isbns with whitespace (covers lines 88-107)."""
    book_data = {"isbns": ["  1234567890  "]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn"] == "1234567890"


def test_extract_from_isbns_duplicate_10() -> None:
    """Test extraction from isbns with duplicate 10-digit ISBNs (covers lines 88-107)."""
    book_data = {"isbns": ["1234567890", "1234567890"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn"] == "1234567890"
    assert len(result) == 1


def test_extract_from_isbns_duplicate_13() -> None:
    """Test extraction from isbns with duplicate 13-digit ISBNs (covers lines 88-107)."""
    book_data = {"isbns": ["9781234567890", "9781234567890"]}
    result = IdentifiersExtractor._extract_from_isbns(book_data)
    assert result["isbn13"] == "9781234567890"
    assert len(result) == 1


def test_extract_fallback_to_isbns() -> None:
    """Test fallback to isbns when no editions (covers lines 38-44)."""
    book_data = {"isbns": ["1234567890"]}
    result = IdentifiersExtractor.extract(book_data)
    assert result["isbn"] == "1234567890"


def test_extract_priority_editions() -> None:
    """Test that editions take priority over isbns (covers lines 38-44)."""
    book_data = {
        "editions": [{"isbn_13": "9781234567890"}],
        "isbns": ["9999999999"],
    }
    result = IdentifiersExtractor.extract(book_data)
    assert result["isbn13"] == "9781234567890"
    assert "isbn" not in result or result.get("isbn") != "9999999999"

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

"""Tests for metadata utils to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.services.ingest.metadata_utils import (
    StringNormalizer,
    StringSimilarityCalculator,
)


@pytest.mark.parametrize(
    ("isbn", "expected"),
    [
        ("123-456-7890", "1234567890"),
        ("123 456 7890", "1234567890"),
        ("ISBN: 123-456-7890", "ISBN1234567890"),
        ("1234567890", "1234567890"),
        ("", ""),
    ],
)
def test_normalize_isbn(isbn: str, expected: str) -> None:
    """Test ISBN normalization."""
    result = StringNormalizer.normalize_isbn(isbn)
    assert result == expected.lower()


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("John Smith", "john smith"),
        ("  John  Smith  ", "john  smith"),
        ("JOHN SMITH", "john smith"),
        ("", ""),
    ],
)
def test_normalize_name(name: str, expected: str) -> None:
    """Test name normalization."""
    result = StringNormalizer.normalize_name(name)
    assert result == expected


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["John Smith", "Jane Doe"], {"john smith", "jane doe"}),
        (["  John  ", "  Jane  "], {"john", "jane"}),
        (["JOHN", "JANE"], {"john", "jane"}),
        ([], set()),
        (["", "  ", "John"], {"john"}),
    ],
)
def test_normalize_name_set(names: list[str], expected: set[str]) -> None:
    """Test name set normalization."""
    result = StringNormalizer.normalize_name_set(names)
    assert result == expected


@pytest.mark.parametrize(
    ("str1", "str2", "expected_min", "expected_max"),
    [
        ("test", "test", 1.0, 1.0),
        ("test", "Test", 0.0, 1.0),  # Case-sensitive, so < 1.0
        ("test", "testing", 0.0, 1.0),  # Will be > 0 but less than 1
        ("", "", 0.0, 0.0),
        ("test", "", 0.0, 0.0),
        ("", "test", 0.0, 0.0),
        ("test", "different", 0.0, 1.0),  # Different strings
    ],
)
def test_similarity(
    str1: str, str2: str, expected_min: float, expected_max: float
) -> None:
    """Test string similarity calculation."""
    result = StringSimilarityCalculator.similarity(str1, str2)
    assert expected_min <= result <= expected_max


@pytest.mark.parametrize(
    ("query_authors", "record_authors", "expected"),
    [
        (["John Smith"], ["John Smith"], True),
        (["John Smith"], ["Jane Doe"], False),
        (["John Smith"], ["john smith"], True),
        (["John", "Smith"], ["Smith", "John"], True),
        ([], ["John Smith"], False),
        (["John Smith"], [], False),
        ([], [], False),
    ],
)
def test_authors_match(
    query_authors: list[str],
    record_authors: list[str],
    expected: bool,
) -> None:
    """Test authors match calculation."""
    result = StringSimilarityCalculator.authors_match(query_authors, record_authors)
    assert result == expected

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

"""Tests for AuthorsExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.metadata.providers._hardcover.extractors.authors import (
    AuthorsExtractor,
)


@pytest.fixture
def book_data_with_contributions() -> dict:
    """Create book data with contributions."""
    return {
        "contributions": [
            {"author": {"name": "Author 1"}},
            {"author": {"name": "Author 2"}},
        ]
    }


@pytest.fixture
def book_data_with_author_names() -> dict:
    """Create book data with author_names."""
    return {
        "author_names": ["Author 1", "Author 2", "Author 3"],
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_contributions(
    book_data_with_contributions: dict,
) -> None:
    """Test extraction from contributions (covers lines 36-46)."""
    result = AuthorsExtractor.extract(book_data_with_contributions)
    assert len(result) == 2
    assert "Author 1" in result
    assert "Author 2" in result


def test_extract_from_contributions_duplicate(
    book_data_with_contributions: dict,
) -> None:
    """Test extraction from contributions with duplicates (covers lines 36-46)."""
    book_data_with_contributions["contributions"].append({
        "author": {"name": "Author 1"}
    })
    result = AuthorsExtractor.extract(book_data_with_contributions)
    assert len(result) == 2
    assert result.count("Author 1") == 1


def test_extract_from_contributions_no_author(
    book_data_with_contributions: dict,
) -> None:
    """Test extraction from contributions without author (covers lines 36-46)."""
    book_data_with_contributions["contributions"].append({})
    result = AuthorsExtractor.extract(book_data_with_contributions)
    assert len(result) == 2


def test_extract_from_contributions_author_not_dict(
    book_data_with_contributions: dict,
) -> None:
    """Test extraction from contributions with author not a dict (covers lines 36-46)."""
    book_data_with_contributions["contributions"].append({"author": "not a dict"})
    result = AuthorsExtractor.extract(book_data_with_contributions)
    assert len(result) == 2


def test_extract_from_contributions_no_name(
    book_data_with_contributions: dict,
) -> None:
    """Test extraction from contributions without name (covers lines 36-46)."""
    book_data_with_contributions["contributions"].append({"author": {"other": "value"}})
    result = AuthorsExtractor.extract(book_data_with_contributions)
    assert len(result) == 2


def test_extract_from_author_names(
    book_data_with_author_names: dict,
) -> None:
    """Test extraction from author_names (covers lines 48-52)."""
    result = AuthorsExtractor.extract(book_data_with_author_names)
    assert len(result) == 3
    assert "Author 1" in result
    assert "Author 2" in result
    assert "Author 3" in result


def test_extract_from_author_names_empty(
    book_data_empty: dict,
) -> None:
    """Test extraction with no author data (covers lines 48-52)."""
    result = AuthorsExtractor.extract(book_data_empty)
    assert result == []


def test_extract_from_author_names_not_list() -> None:
    """Test extraction with author_names not a list (covers lines 48-52)."""
    book_data = {"author_names": "not a list"}
    result = AuthorsExtractor.extract(book_data)
    assert result == []


def test_extract_from_author_names_with_falsy() -> None:
    """Test extraction with falsy author names (covers lines 48-52)."""
    book_data = {"author_names": ["Author 1", "", None, 0, "Author 2"]}
    result = AuthorsExtractor.extract(book_data)
    assert len(result) == 2
    assert "Author 1" in result
    assert "Author 2" in result


def test_extract_contributions_not_list() -> None:
    """Test extraction with contributions not a list (covers lines 38-46)."""
    book_data = {"contributions": "not a list"}
    result = AuthorsExtractor.extract(book_data)
    assert result == []


def test_extract_contributions_fallback_to_author_names() -> None:
    """Test that author_names is used when contributions is empty (covers lines 48-52)."""
    book_data = {
        "contributions": [],
        "author_names": ["Author 1"],
    }
    result = AuthorsExtractor.extract(book_data)
    assert result == ["Author 1"]


def test_extract_contributions_priority() -> None:
    """Test that contributions take priority over author_names (covers lines 36-52)."""
    book_data = {
        "contributions": [{"author": {"name": "Contrib Author"}}],
        "author_names": ["Name Author"],
    }
    result = AuthorsExtractor.extract(book_data)
    assert result == ["Contrib Author"]

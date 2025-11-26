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

"""Tests for TagsExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.extractors.tags import (
    TagsExtractor,
)


@pytest.fixture
def book_data_with_genres() -> dict:
    """Create book data with genres."""
    return {
        "genres": ["Genre 1", "Genre 2"],
    }


@pytest.fixture
def book_data_with_moods() -> dict:
    """Create book data with moods."""
    return {
        "moods": ["Mood 1", "Mood 2"],
    }


@pytest.fixture
def book_data_with_tags() -> dict:
    """Create book data with tags."""
    return {
        "tags": ["Tag 1", "Tag 2"],
    }


@pytest.fixture
def book_data_all() -> dict:
    """Create book data with all tag types."""
    return {
        "genres": ["Genre 1"],
        "moods": ["Mood 1"],
        "tags": ["Tag 1"],
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_genres(
    book_data_with_genres: dict,
) -> None:
    """Test extraction from genres (covers lines 36-51)."""
    result = TagsExtractor.extract(book_data_with_genres)
    assert len(result) == 2
    assert "Genre 1" in result
    assert "Genre 2" in result


def test_extract_from_moods(
    book_data_with_moods: dict,
) -> None:
    """Test extraction from moods (covers lines 36-51)."""
    result = TagsExtractor.extract(book_data_with_moods)
    assert len(result) == 2
    assert "Mood 1" in result
    assert "Mood 2" in result


def test_extract_from_tags(
    book_data_with_tags: dict,
) -> None:
    """Test extraction from tags (covers lines 36-51)."""
    result = TagsExtractor.extract(book_data_with_tags)
    assert len(result) == 2
    assert "Tag 1" in result
    assert "Tag 2" in result


def test_extract_all_types(
    book_data_all: dict,
) -> None:
    """Test extraction from all tag types (covers lines 36-51)."""
    result = TagsExtractor.extract(book_data_all)
    assert len(result) == 3
    assert "Genre 1" in result
    assert "Mood 1" in result
    assert "Tag 1" in result


def test_extract_no_tags(book_data_empty: dict) -> None:
    """Test extraction with no tags (covers lines 36-51)."""
    result = TagsExtractor.extract(book_data_empty)
    assert result == []


def test_extract_genres_not_list() -> None:
    """Test extraction with genres not a list (covers lines 36-51)."""
    book_data = {"genres": "not a list"}
    result = TagsExtractor.extract(book_data)
    assert result == []


def test_extract_moods_not_list() -> None:
    """Test extraction with moods not a list (covers lines 36-51)."""
    book_data = {"moods": "not a list"}
    result = TagsExtractor.extract(book_data)
    assert result == []


def test_extract_tags_not_list() -> None:
    """Test extraction with tags not a list (covers lines 36-51)."""
    book_data = {"tags": "not a list"}
    result = TagsExtractor.extract(book_data)
    assert result == []


def test_extract_with_falsy_values() -> None:
    """Test extraction with falsy tag values (covers lines 36-51)."""
    book_data = {
        "genres": ["Genre 1", "", None, 0],
        "moods": ["Mood 1", False],
        "tags": ["Tag 1", []],
    }
    result = TagsExtractor.extract(book_data)
    assert "Genre 1" in result
    assert "Mood 1" in result
    assert "Tag 1" in result
    assert "" not in result
    assert None not in result
    assert 0 not in result
    assert False not in result
    assert [] not in result

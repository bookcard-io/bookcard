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

"""Tests for Hardcover parser to achieve 100% coverage."""

from __future__ import annotations

import json

import pytest

from bookcard.metadata.providers._hardcover.parser import (
    HardcoverResponseParser,
)


@pytest.fixture
def search_results_dict() -> dict:
    """Create search results as dict with hits."""
    return {
        "hits": [
            {"document": {"id": 1, "title": "Book 1"}},
            {"document": {"id": 2, "title": "Book 2"}},
        ]
    }


@pytest.fixture
def search_results_list() -> list:
    """Create search results as list."""
    return [
        {"id": 1, "title": "Book 1"},
        {"id": 2, "title": "Book 2"},
    ]


@pytest.fixture
def search_results_json_string() -> str:
    """Create search results as JSON string."""
    return json.dumps({
        "hits": [
            {"document": {"id": 1, "title": "Book 1"}},
        ]
    })


def test_parse_search_results_none() -> None:
    """Test parsing None results (covers lines 49-50)."""
    result = HardcoverResponseParser.parse_search_results(None)
    assert result == []


def test_parse_search_results_dict(
    search_results_dict: dict,
) -> None:
    """Test parsing dict results (covers lines 63-75)."""
    result = HardcoverResponseParser.parse_search_results(search_results_dict)
    assert len(result) == 2
    assert result[0] == {"id": 1, "title": "Book 1"}
    assert result[1] == {"id": 2, "title": "Book 2"}


def test_parse_search_results_dict_no_hits() -> None:
    """Test parsing dict with no hits (covers lines 63-75)."""
    result = HardcoverResponseParser.parse_search_results({})
    assert result == []


def test_parse_search_results_dict_hits_not_list() -> None:
    """Test parsing dict with hits not a list (covers lines 64-69)."""
    result = HardcoverResponseParser.parse_search_results({"hits": "not a list"})
    assert result == []


def test_parse_search_results_dict_hit_no_document() -> None:
    """Test parsing dict with hit without document (covers lines 71-75)."""
    result = HardcoverResponseParser.parse_search_results({
        "hits": [{"not_document": "value"}]
    })
    assert result == []


def test_parse_search_results_dict_hit_not_dict() -> None:
    """Test parsing dict with hit not a dict (covers lines 71-75)."""
    result = HardcoverResponseParser.parse_search_results({"hits": ["not a dict"]})
    assert result == []


def test_parse_search_results_list(
    search_results_list: list,
) -> None:
    """Test parsing list results (covers lines 77-79)."""
    result = HardcoverResponseParser.parse_search_results(search_results_list)
    assert len(result) == 2
    assert result == search_results_list


def test_parse_search_results_json_string(
    search_results_json_string: str,
) -> None:
    """Test parsing JSON string results (covers lines 52-60)."""
    result = HardcoverResponseParser.parse_search_results(search_results_json_string)
    assert len(result) == 1
    assert result[0] == {"id": 1, "title": "Book 1"}


def test_parse_search_results_invalid_json_string() -> None:
    """Test parsing invalid JSON string (covers lines 52-60)."""
    result = HardcoverResponseParser.parse_search_results("not valid json")
    assert result == []


def test_parse_search_results_unexpected_type() -> None:
    """Test parsing unexpected type (covers lines 81-85)."""
    result = HardcoverResponseParser.parse_search_results(123)  # type: ignore[arg-type]
    assert result == []


def test_extract_search_data() -> None:
    """Test extracting search data from GraphQL response (covers lines 100-102)."""
    data = {"data": {"search": {"results": {"hits": [{"document": {"id": 1}}]}}}}
    result = HardcoverResponseParser.extract_search_data(data)
    assert result == {"hits": [{"document": {"id": 1}}]}


def test_extract_search_data_no_data() -> None:
    """Test extracting search data with no data key (covers lines 100-102)."""
    data = {}
    result = HardcoverResponseParser.extract_search_data(data)
    assert result is None


def test_extract_search_data_no_search() -> None:
    """Test extracting search data with no search key (covers lines 100-102)."""
    data = {"data": {}}
    result = HardcoverResponseParser.extract_search_data(data)
    assert result is None


def test_extract_search_data_no_results() -> None:
    """Test extracting search data with no results key (covers lines 100-102)."""
    data = {"data": {"search": {}}}
    result = HardcoverResponseParser.extract_search_data(data)
    assert result is None


def test_extract_edition_data() -> None:
    """Test extracting edition data from GraphQL response (covers lines 118-121)."""
    data = {
        "data": {
            "books": [
                {
                    "id": 1,
                    "title": "Test Book",
                    "editions": [{"id": 1}],
                }
            ]
        }
    }
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result == {
        "id": 1,
        "title": "Test Book",
        "editions": [{"id": 1}],
    }


def test_extract_edition_data_no_data() -> None:
    """Test extracting edition data with no data key (covers lines 118-121)."""
    data = {}
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result is None


def test_extract_edition_data_no_books() -> None:
    """Test extracting edition data with no books key (covers lines 118-121)."""
    data = {"data": {}}
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result is None


def test_extract_edition_data_empty_books() -> None:
    """Test extracting edition data with empty books list (covers lines 118-121)."""
    data = {"data": {"books": []}}
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result is None


def test_extract_edition_data_books_not_list() -> None:
    """Test extracting edition data with books not a list (covers lines 118-121)."""
    data = {"data": {"books": "not a list"}}
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result is None


def test_extract_edition_data_first_book_none() -> None:
    """Test extracting edition data with first book None (covers lines 118-121)."""
    data = {"data": {"books": [None]}}
    result = HardcoverResponseParser.extract_edition_data(data)
    assert result is None

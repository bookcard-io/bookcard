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

"""Tests for Hardcover enrichment to achieve 100% coverage."""

from __future__ import annotations

import json

import pytest

from bookcard.metadata.providers._hardcover.enrichment import (
    HardcoverEnrichment,
)


@pytest.fixture
def book_data() -> dict:
    """Create sample book data."""
    return {
        "id": 1,
        "title": "Test Book",
        "description": "Original description",
        "series_names": ["Original Series"],
        "series_index": 1,
        "tags": ["tag1", "tag2"],
    }


@pytest.fixture
def edition_data() -> dict:
    """Create sample edition data."""
    return {
        "description": "Enhanced description",
        "book_series": [
            {
                "position": 2,
                "series": {"name": "Enhanced Series"},
            }
        ],
        "cached_tags": json.dumps([{"tag": "tag3"}, {"name": "tag4"}]),
        "editions": [{"id": 1, "title": "Edition 1"}],
    }


@pytest.fixture
def edition_data_no_series() -> dict:
    """Create edition data without series."""
    return {
        "description": "Enhanced description",
        "book_series": [],
        "cached_tags": [],
        "editions": [],
    }


@pytest.fixture
def edition_data_empty_series() -> dict:
    """Create edition data with empty series list."""
    return {
        "description": "Enhanced description",
        "book_series": [None],
        "cached_tags": [],
        "editions": [],
    }


@pytest.fixture
def edition_data_invalid_series() -> dict:
    """Create edition data with invalid series structure."""
    return {
        "description": "Enhanced description",
        "book_series": "not a list",
        "cached_tags": [],
        "editions": [],
    }


def test_merge_book_with_editions_description_merge(
    book_data: dict, edition_data: dict
) -> None:
    """Test merging description from edition data (covers lines 45-49)."""
    book_data_no_desc = book_data.copy()
    book_data_no_desc.pop("description")
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data_no_desc, edition_data
    )
    assert result["description"] == "Enhanced description"


def test_merge_book_with_editions_description_preserved(
    book_data: dict, edition_data: dict
) -> None:
    """Test that existing description is preserved (covers lines 48-49)."""
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["description"] == "Original description"


def test_merge_book_with_editions_series_merge(
    book_data: dict, edition_data: dict
) -> None:
    """Test merging series info from edition data (covers lines 52, 75-87)."""
    book_data_no_series = book_data.copy()
    book_data_no_series.pop("series_names")
    book_data_no_series.pop("series_index")
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data_no_series, edition_data
    )
    assert result["series_names"] == ["Enhanced Series"]
    assert result["series_index"] == 2


def test_merge_book_with_editions_series_index_only(
    book_data: dict, edition_data: dict
) -> None:
    """Test merging only series index when series_names exists (covers lines 84-87)."""
    # The enrichment only updates series_index if it's None in book_data
    # Since book_data has series_index: 1, it won't be updated
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["series_names"] == ["Original Series"]
    assert result["series_index"] == 1


def test_merge_book_with_editions_no_series(
    book_data: dict, edition_data_no_series: dict
) -> None:
    """Test merge when edition data has no series (covers lines 75-77)."""
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data, edition_data_no_series
    )
    assert result["series_names"] == ["Original Series"]
    assert result["series_index"] == 1


def test_merge_book_with_editions_empty_series(
    book_data: dict, edition_data_empty_series: dict
) -> None:
    """Test merge when edition data has empty series list (covers lines 75-77)."""
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data, edition_data_empty_series
    )
    assert result["series_names"] == ["Original Series"]
    assert result["series_index"] == 1


def test_merge_book_with_editions_invalid_series(
    book_data: dict, edition_data_invalid_series: dict
) -> None:
    """Test merge when edition data has invalid series structure (covers lines 75-77)."""
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data, edition_data_invalid_series
    )
    assert result["series_names"] == ["Original Series"]
    assert result["series_index"] == 1


def test_merge_book_with_editions_series_no_name(
    book_data: dict,
) -> None:
    """Test merge when series has no name (covers lines 81-83)."""
    edition_data = {
        "book_series": [{"position": 2, "series": {}}],
    }
    book_data_no_series = book_data.copy()
    book_data_no_series.pop("series_names")
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data_no_series, edition_data
    )
    assert "series_names" not in result or result.get("series_names") is None


def test_merge_book_with_editions_tags_merge(
    book_data: dict, edition_data: dict
) -> None:
    """Test merging tags from cached_tags (covers lines 54-55, 100-112)."""
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert "tag1" in result["tags"]
    assert "tag2" in result["tags"]
    assert "tag3" in result["tags"]
    assert "tag4" in result["tags"]
    assert len(result["tags"]) == 4


def test_merge_book_with_editions_tags_no_cached_tags(
    book_data: dict, edition_data_no_series: dict
) -> None:
    """Test merge when no cached_tags (covers lines 100-102)."""
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data, edition_data_no_series
    )
    assert result["tags"] == ["tag1", "tag2"]


def test_merge_book_with_editions_tags_string_list(
    book_data: dict,
) -> None:
    """Test merge with cached_tags as string list (covers lines 129-133)."""
    edition_data = {
        "cached_tags": json.dumps(["tag3", "tag4"]),
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert "tag3" in result["tags"]
    assert "tag4" in result["tags"]


def test_merge_book_with_editions_tags_invalid_json(
    book_data: dict,
) -> None:
    """Test merge with invalid JSON in cached_tags (covers lines 129-133)."""
    edition_data = {
        "cached_tags": "not valid json",
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert "not valid json" in result["tags"]


def test_merge_book_with_editions_tags_empty_string(
    book_data: dict,
) -> None:
    """Test merge with empty string cached_tags (covers lines 129-133)."""
    edition_data = {
        "cached_tags": "",
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["tags"] == ["tag1", "tag2"]


def test_merge_book_with_editions_tags_list_format(
    book_data: dict,
) -> None:
    """Test merge with cached_tags as list (covers lines 135-148)."""
    edition_data = {
        "cached_tags": [{"tag": "tag3"}, {"name": "tag4"}, "tag5"],
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert "tag3" in result["tags"]
    assert "tag4" in result["tags"]
    assert "tag5" in result["tags"]


def test_merge_book_with_editions_tags_not_list(
    book_data: dict,
) -> None:
    """Test merge with cached_tags not a list (covers lines 135-136)."""
    edition_data = {
        "cached_tags": {"tag": "tag3"},
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["tags"] == ["tag1", "tag2"]


def test_merge_book_with_editions_tags_existing_not_list(
    book_data: dict,
) -> None:
    """Test merge when existing tags is not a list (covers lines 108-110)."""
    book_data["tags"] = "not a list"
    edition_data = {
        "cached_tags": [{"tag": "tag3"}],
    }
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["tags"] == ["tag3"]


def test_merge_book_with_editions_editions_merge(
    book_data: dict, edition_data: dict
) -> None:
    """Test merging editions data (covers lines 57-60)."""
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result["editions"] == [{"id": 1, "title": "Edition 1"}]


def test_merge_book_with_editions_no_editions(
    book_data: dict, edition_data_no_series: dict
) -> None:
    """Test merge when no editions (covers lines 58-60)."""
    result = HardcoverEnrichment.merge_book_with_editions(
        book_data, edition_data_no_series
    )
    assert "editions" not in result


def test_parse_cached_tags_json_string() -> None:
    """Test parsing cached_tags as JSON string (covers lines 129-133)."""
    result = HardcoverEnrichment._parse_cached_tags(
        json.dumps([{"tag": "tag1"}, {"name": "tag2"}])
    )
    assert "tag1" in result
    assert "tag2" in result


def test_parse_cached_tags_list() -> None:
    """Test parsing cached_tags as list (covers lines 135-148)."""
    result = HardcoverEnrichment._parse_cached_tags([
        {"tag": "tag1"},
        {"name": "tag2"},
        "tag3",
    ])
    assert "tag1" in result
    assert "tag2" in result
    assert "tag3" in result


def test_parse_cached_tags_invalid_json() -> None:
    """Test parsing invalid JSON (covers lines 129-133)."""
    result = HardcoverEnrichment._parse_cached_tags("not json")
    assert result == ["not json"]


def test_parse_cached_tags_empty_string() -> None:
    """Test parsing empty string (covers lines 129-133)."""
    result = HardcoverEnrichment._parse_cached_tags("")
    assert result == []


def test_parse_cached_tags_not_list() -> None:
    """Test parsing non-list cached_tags (covers lines 135-136)."""
    result = HardcoverEnrichment._parse_cached_tags({"tag": "tag1"})  # type: ignore[arg-type]
    assert result == []


def test_parse_cached_tags_dict_with_tag_key() -> None:
    """Test parsing dict with 'tag' key (covers lines 141-144)."""
    result = HardcoverEnrichment._parse_cached_tags([{"tag": "tag1"}])
    assert result == ["tag1"]


def test_parse_cached_tags_dict_with_name_key() -> None:
    """Test parsing dict with 'name' key (covers lines 141-144)."""
    result = HardcoverEnrichment._parse_cached_tags([{"name": "tag1"}])
    assert result == ["tag1"]


def test_parse_cached_tags_dict_no_tag_or_name() -> None:
    """Test parsing dict without tag or name (covers lines 141-144)."""
    result = HardcoverEnrichment._parse_cached_tags([{"other": "value"}])
    assert result == []


def test_parse_cached_tags_string_in_list() -> None:
    """Test parsing string in list (covers lines 145-146)."""
    result = HardcoverEnrichment._parse_cached_tags(["tag1", "tag2"])
    assert result == ["tag1", "tag2"]


def test_merge_book_with_editions_copy() -> None:
    """Test that merge creates a copy (covers line 45)."""
    book_data = {"id": 1, "title": "Test"}
    edition_data = {}
    result = HardcoverEnrichment.merge_book_with_editions(book_data, edition_data)
    assert result is not book_data
    assert result == book_data

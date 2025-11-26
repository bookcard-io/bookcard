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

"""Tests for Hardcover mapper to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.metadata.providers._hardcover.mapper import HardcoverBookMapper
from fundamental.models.metadata import MetadataRecord


@pytest.fixture
def mapper() -> HardcoverBookMapper:
    """Create a HardcoverBookMapper instance."""
    return HardcoverBookMapper()


@pytest.fixture
def minimal_book_data() -> dict:
    """Create minimal valid book data."""
    return {
        "id": 1,
        "title": "Test Book",
    }


@pytest.fixture
def complete_book_data() -> dict:
    """Create complete book data with all fields."""
    return {
        "id": 1,
        "title": "Test Book",
        "slug": "test-book",
        "description": "Test description",
        "rating": 4.5,
        "contributions": [
            {"author": {"name": "Author 1"}},
            {"author": {"name": "Author 2"}},
        ],
        "series_names": ["Test Series"],
        "series_index": 1,
        "editions": [
            {
                "isbn_13": "9781234567890",
                "isbn_10": "1234567890",
                "image": {"url": "https://example.com/cover.jpg"},
                "publisher": {"name": "Test Publisher"},
                "release_date": "2024-01-01",
                "language": {"code3": "eng"},
            }
        ],
        "tags": ["tag1", "tag2"],
    }


@pytest.fixture
def book_data_no_id() -> dict:
    """Create book data without id."""
    return {"title": "Test Book"}


@pytest.fixture
def book_data_no_title() -> dict:
    """Create book data without title."""
    return {"id": 1}


@pytest.fixture
def book_data_empty_title() -> dict:
    """Create book data with empty title."""
    return {"id": 1, "title": ""}


def test_mapper_init(mapper: HardcoverBookMapper) -> None:
    """Test mapper initialization (covers lines 48-59)."""
    assert len(mapper._extractors) == 8
    assert "authors" in mapper._extractors
    assert "cover_url" in mapper._extractors
    assert "identifiers" in mapper._extractors
    assert "series" in mapper._extractors
    assert "publisher" in mapper._extractors
    assert "published_date" in mapper._extractors
    assert "tags" in mapper._extractors
    assert "languages" in mapper._extractors


def test_map_to_record_minimal(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping minimal book data (covers lines 74-150)."""
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert isinstance(result, MetadataRecord)
    assert result.source_id == "hardcover"
    assert result.external_id == "1"
    assert result.title == "Test Book"
    assert result.url == "https://hardcover.app/book/1"


def test_map_to_record_complete(
    mapper: HardcoverBookMapper, complete_book_data: dict
) -> None:
    """Test mapping complete book data (covers lines 74-150)."""
    result = mapper.map_to_record(complete_book_data)
    assert result is not None
    assert isinstance(result, MetadataRecord)
    assert result.source_id == "hardcover"
    assert result.external_id == "1"
    assert result.title == "Test Book"
    assert result.url == "https://hardcover.app/book/test-book"
    assert result.description == "Test description"
    assert result.rating == 4.5
    assert len(result.authors) == 2
    assert result.series == "Test Series"
    # SeriesExtractor doesn't extract series_index from book_data, only series_names
    assert result.series_index is None


def test_map_to_record_no_id(
    mapper: HardcoverBookMapper, book_data_no_id: dict
) -> None:
    """Test mapping with no id (covers lines 76-78)."""
    result = mapper.map_to_record(book_data_no_id)
    assert result is None


def test_map_to_record_no_title(
    mapper: HardcoverBookMapper, book_data_no_title: dict
) -> None:
    """Test mapping with no title (covers lines 80-82)."""
    result = mapper.map_to_record(book_data_no_title)
    assert result is None


def test_map_to_record_empty_title(
    mapper: HardcoverBookMapper, book_data_empty_title: dict
) -> None:
    """Test mapping with empty title (covers lines 80-82)."""
    result = mapper.map_to_record(book_data_empty_title)
    assert result is None


def test_map_to_record_with_slug(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with slug (covers lines 123-127)."""
    minimal_book_data["slug"] = "test-book"
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.url == "https://hardcover.app/book/test-book"


def test_map_to_record_without_slug(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping without slug (covers lines 123-127)."""
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.url == "https://hardcover.app/book/1"


def test_map_to_record_rating_valid(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with valid rating (covers lines 115-120)."""
    minimal_book_data["rating"] = 4.5
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.rating == 4.5


def test_map_to_record_rating_string(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with string rating (covers lines 115-120)."""
    minimal_book_data["rating"] = "4.5"
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.rating == 4.5


def test_map_to_record_rating_invalid(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with invalid rating (covers lines 115-120)."""
    minimal_book_data["rating"] = "invalid"
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.rating is None


def test_map_to_record_rating_none(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with None rating (covers lines 115-120)."""
    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.rating is None


def test_map_to_record_parse_exception(
    mapper: HardcoverBookMapper,
) -> None:
    """Test mapping with parse exception (covers lines 148-150)."""
    # Create a mock extractor that raises KeyError
    mock_extractor = MagicMock()
    mock_extractor.extract.side_effect = KeyError("test error")
    mapper._extractors["authors"] = mock_extractor

    book_data = {"id": 1, "title": "Test Book"}
    result = mapper.map_to_record(book_data)
    assert result is None


def test_map_to_record_value_error(
    mapper: HardcoverBookMapper,
) -> None:
    """Test mapping with ValueError exception (covers lines 148-150)."""
    mock_extractor = MagicMock()
    mock_extractor.extract.side_effect = ValueError("test error")
    mapper._extractors["authors"] = mock_extractor

    book_data = {"id": 1, "title": "Test Book"}
    result = mapper.map_to_record(book_data)
    assert result is None


def test_map_to_record_type_error(
    mapper: HardcoverBookMapper,
) -> None:
    """Test mapping with TypeError exception (covers lines 148-150)."""
    mock_extractor = MagicMock()
    mock_extractor.extract.side_effect = TypeError("test error")
    mapper._extractors["authors"] = mock_extractor

    book_data = {"id": 1, "title": "Test Book"}
    result = mapper.map_to_record(book_data)
    assert result is None


def test_map_to_record_attribute_error(
    mapper: HardcoverBookMapper,
) -> None:
    """Test mapping with AttributeError exception (covers lines 148-150)."""
    mock_extractor = MagicMock()
    mock_extractor.extract.side_effect = AttributeError("test error")
    mapper._extractors["authors"] = mock_extractor

    book_data = {"id": 1, "title": "Test Book"}
    result = mapper.map_to_record(book_data)
    assert result is None


@pytest.mark.parametrize(
    ("extractor_key", "expected_type"),
    [
        ("authors", list),
        ("cover_url", str),
        ("identifiers", dict),
        ("series", tuple),
        ("publisher", str),
        ("published_date", str),
        ("tags", list),
        ("languages", list),
    ],
)
def test_map_to_record_extractor_types(
    mapper: HardcoverBookMapper,
    minimal_book_data: dict,
    extractor_key: str,
    expected_type: type,
) -> None:
    """Test that extractors return correct types."""
    # Mock all extractors to return None to test type checking
    for key in mapper._extractors:
        if key != extractor_key:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = None
            mapper._extractors[key] = mock_extractor

    result = mapper.map_to_record(minimal_book_data)
    assert result is not None


def test_map_to_record_series_tuple(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with series tuple (covers lines 94-98)."""
    mock_series_extractor = MagicMock()
    mock_series_extractor.extract.return_value = ("Series Name", 1.0)
    mapper._extractors["series"] = mock_series_extractor

    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.series == "Series Name"
    assert result.series_index == 1.0


def test_map_to_record_series_invalid(
    mapper: HardcoverBookMapper, minimal_book_data: dict
) -> None:
    """Test mapping with invalid series result (covers lines 94-98)."""
    mock_series_extractor = MagicMock()
    mock_series_extractor.extract.return_value = "not a tuple"
    mapper._extractors["series"] = mock_series_extractor

    result = mapper.map_to_record(minimal_book_data)
    assert result is not None
    assert result.series is None
    assert result.series_index is None

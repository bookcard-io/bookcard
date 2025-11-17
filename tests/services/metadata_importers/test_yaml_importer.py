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

"""Tests for YAML importer to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from fundamental.services.metadata_importers.yaml_importer import YamlImporter


@pytest.fixture
def yaml_importer() -> YamlImporter:
    """Create YAML importer instance."""
    return YamlImporter()


def test_can_handle_yaml(yaml_importer: YamlImporter) -> None:
    """Test can_handle returns True for yaml/yml formats."""
    assert yaml_importer.can_handle("yaml") is True
    assert yaml_importer.can_handle("yml") is True
    assert yaml_importer.can_handle("YAML") is True
    assert yaml_importer.can_handle("YML") is True


def test_can_handle_other_formats(yaml_importer: YamlImporter) -> None:
    """Test can_handle returns False for other formats."""
    assert yaml_importer.can_handle("json") is False
    assert yaml_importer.can_handle("opf") is False
    assert yaml_importer.can_handle("xml") is False


def test_import_metadata_full_metadata() -> None:
    """Test import_metadata with full metadata."""
    yaml_content = """title: Test Book
authors:
  - Author One
  - Author Two
series: Test Series
series_index: 1.5
description: Test description
publisher: Test Publisher
pubdate: 2020-01-01
languages:
  - en
  - fr
identifiers:
  - type: isbn
    val: 978-1234567890
  - type: asin
    val: B01234567
tags:
  - Fiction
  - Science Fiction
rating: 4
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.title == "Test Book"
    assert result.author_names == ["Author One", "Author Two"]
    assert result.series_name == "Test Series"
    assert result.series_index == 1.5
    assert result.description == "Test description"
    assert result.publisher_name == "Test Publisher"
    assert result.pubdate is not None
    assert result.pubdate.replace(tzinfo=None) == datetime(2020, 1, 1, tzinfo=None)  # noqa: DTZ001
    assert result.pubdate.tzinfo == UTC
    assert result.language_codes == ["en", "fr"]
    assert result.identifiers is not None
    assert len(result.identifiers) == 2
    assert result.tag_names == ["Fiction", "Science Fiction"]
    assert result.rating_value == 4


def test_import_metadata_minimal() -> None:
    """Test import_metadata with minimal metadata."""
    yaml_content = """title: Minimal Book
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.title == "Minimal Book"
    assert result.author_names is None
    assert result.publisher_name is None


def test_import_metadata_pyyaml_not_installed() -> None:
    """Test import_metadata raises error when PyYAML is not installed."""
    with patch("fundamental.services.metadata_importers.yaml_importer.yaml", None):
        importer = YamlImporter()
        with pytest.raises(ValueError, match="YAML import requires PyYAML"):
            importer.import_metadata("title: Test")


def test_import_metadata_invalid_yaml() -> None:
    """Test import_metadata with invalid YAML."""
    importer = YamlImporter()
    with pytest.raises(ValueError, match="Invalid YAML format"):
        importer.import_metadata("invalid: yaml: content: [unclosed")


def test_import_metadata_not_dict() -> None:
    """Test import_metadata with YAML that is not a dictionary."""
    importer = YamlImporter()
    with pytest.raises(TypeError, match="YAML content must be a dictionary"):
        importer.import_metadata("- item1\n- item2")


def test_import_metadata_identifiers_as_list() -> None:
    """Test import_metadata with identifiers as list."""
    yaml_content = """title: Test Book
identifiers:
  - type: isbn
    val: 978-1234567890
  - type: asin
    val: B01234567
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.identifiers is not None
    assert len(result.identifiers) == 2
    assert result.identifiers[0]["type"] == "isbn"
    assert result.identifiers[0]["val"] == "978-1234567890"


def test_import_metadata_identifiers_as_dict() -> None:
    """Test import_metadata with identifiers as dict."""
    yaml_content = """title: Test Book
identifiers:
  isbn: 978-1234567890
  asin: B01234567
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.identifiers is not None
    assert len(result.identifiers) == 2
    identifier_types = [id_item["type"] for id_item in result.identifiers]
    assert "isbn" in identifier_types
    assert "asin" in identifier_types


def test_import_metadata_isbn_separate() -> None:
    """Test import_metadata with separate ISBN field."""
    yaml_content = """title: Test Book
isbn: 978-1234567890
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.identifiers is not None
    assert len(result.identifiers) == 1
    assert result.identifiers[0]["type"] == "isbn"
    assert result.identifiers[0]["val"] == "978-1234567890"


def test_import_metadata_isbn_already_in_identifiers() -> None:
    """Test import_metadata with ISBN already in identifiers."""
    yaml_content = """title: Test Book
identifiers:
  - type: isbn
    val: 978-1234567890
isbn: 978-9999999999
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    # Should not add duplicate ISBN
    assert result.identifiers is not None
    isbn_count = sum(1 for id_item in result.identifiers if id_item["type"] == "isbn")
    assert isbn_count == 1


def test_import_metadata_authors_not_list() -> None:
    """Test import_metadata with authors that is not a list."""
    yaml_content = """title: Test Book
authors: Single Author
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.author_names is None


def test_import_metadata_languages_not_list() -> None:
    """Test import_metadata with languages that is not a list."""
    yaml_content = """title: Test Book
languages: en
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.language_codes is None


def test_import_metadata_tags_not_list() -> None:
    """Test import_metadata with tags that is not a list."""
    yaml_content = """title: Test Book
tags: Fiction
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.tag_names is None


def test_import_metadata_identifiers_list_with_non_dict() -> None:
    """Test import_metadata with identifiers list containing non-dict items."""
    yaml_content = """title: Test Book
identifiers:
  - type: isbn
    val: 978-1234567890
  - not a dict
  - another string
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    # Should only include dict items
    assert result.identifiers is not None
    assert len(result.identifiers) == 1
    assert result.identifiers[0]["type"] == "isbn"


def test_import_metadata_rating_out_of_range() -> None:
    """Test import_metadata with rating out of range."""
    yaml_content = """title: Test Book
rating: 10
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.rating_value == 5


def test_import_metadata_rating_negative() -> None:
    """Test import_metadata with negative rating."""
    yaml_content = """title: Test Book
rating: -5
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.rating_value == 0


def test_import_metadata_rating_invalid() -> None:
    """Test import_metadata with invalid rating."""
    yaml_content = """title: Test Book
rating: invalid
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.rating_value is None


def test_import_metadata_series_index_invalid() -> None:
    """Test import_metadata with invalid series_index."""
    yaml_content = """title: Test Book
series_index: invalid
"""
    importer = YamlImporter()
    result = importer.import_metadata(yaml_content)

    assert result.series_index is None


def test_parse_date_datetime_object() -> None:
    """Test _parse_date with datetime object."""
    dt = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    result = YamlImporter._parse_date(dt)
    assert result == dt


def test_parse_date_iso_string() -> None:
    """Test _parse_date with ISO string."""
    result = YamlImporter._parse_date("2020-01-01T12:00:00+00:00")
    assert result == datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_parse_date_iso_with_z() -> None:
    """Test _parse_date with ISO string ending in Z."""
    result = YamlImporter._parse_date("2020-01-01T12:00:00Z")
    assert result is not None
    assert result.tzinfo is not None


def test_parse_date_common_formats() -> None:
    """Test _parse_date with common date formats."""
    result1 = YamlImporter._parse_date("2020-01-01")
    assert result1 == datetime(2020, 1, 1, tzinfo=UTC)

    result2 = YamlImporter._parse_date("2020-01-01T12:00:00")
    assert result2 is not None
    assert result2.replace(tzinfo=None) == datetime(2020, 1, 1, 12, 0, 0, tzinfo=None)  # noqa: DTZ001
    assert result2.tzinfo == UTC

    result3 = YamlImporter._parse_date("2020-01-01T12:00:00+05:00")
    assert result3 is not None
    assert result3.tzinfo is not None


def test_parse_date_invalid() -> None:
    """Test _parse_date with invalid date."""
    result = YamlImporter._parse_date("invalid-date")
    assert result is None


def test_parse_date_not_string_or_datetime() -> None:
    """Test _parse_date with non-string, non-datetime value."""
    result = YamlImporter._parse_date(12345)  # type: ignore[arg-type]
    assert result is None


def test_convert_identifier_list() -> None:
    """Test _convert_identifier_list."""
    identifiers = [
        {"type": "isbn", "val": "978-1234567890"},
        {"type": "asin", "val": "B01234567"},
    ]
    result = YamlImporter._convert_identifier_list(identifiers)

    assert len(result) == 2
    assert result[0]["type"] == "isbn"
    assert result[0]["val"] == "978-1234567890"


def test_convert_identifier_list_with_missing_keys() -> None:
    """Test _convert_identifier_list with missing keys."""
    identifiers = [
        {"type": "isbn"},
        {"val": "978-1234567890"},
        {},
    ]
    result = YamlImporter._convert_identifier_list(identifiers)

    assert len(result) == 3
    assert result[0]["type"] == "isbn"
    assert result[0]["val"] == ""


def test_convert_identifier_dict() -> None:
    """Test _convert_identifier_dict."""
    identifiers = {
        "isbn": "978-1234567890",
        "asin": "B01234567",
    }
    result = YamlImporter._convert_identifier_dict(identifiers)

    assert len(result) == 2
    identifier_types = [id_item["type"] for id_item in result]
    assert "isbn" in identifier_types
    assert "asin" in identifier_types

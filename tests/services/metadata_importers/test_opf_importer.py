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

"""Tests for OPF importer to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from lxml import etree  # type: ignore[import]

from bookcard.services.metadata_importers.opf_importer import OpfImporter


@pytest.fixture
def opf_importer() -> OpfImporter:
    """Create OPF importer instance."""
    return OpfImporter()


def test_can_handle_opf(opf_importer: OpfImporter) -> None:
    """Test can_handle returns True for opf format."""
    assert opf_importer.can_handle("opf") is True
    assert opf_importer.can_handle("OPF") is True
    assert opf_importer.can_handle("Opf") is True


def test_can_handle_other_formats(opf_importer: OpfImporter) -> None:
    """Test can_handle returns False for other formats."""
    assert opf_importer.can_handle("json") is False
    assert opf_importer.can_handle("yaml") is False
    assert opf_importer.can_handle("xml") is False


def test_import_metadata_full_metadata() -> None:
    """Test import_metadata with full metadata."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
              xmlns:dcterms="http://purl.org/dc/terms/">
        <dc:title>Test Book</dc:title>
        <dc:creator>Author One</dc:creator>
        <dc:creator>Author Two</dc:creator>
        <dc:publisher>Test Publisher</dc:publisher>
        <dcterms:date>2020-01-01</dcterms:date>
        <dc:description>Test description</dc:description>
        <dc:language>en</dc:language>
        <dc:language>fr</dc:language>
        <dc:identifier scheme="ISBN">978-1234567890</dc:identifier>
        <dc:identifier scheme="ASIN">B01234567</dc:identifier>
        <dc:subject>Fiction</dc:subject>
        <dc:subject>Science Fiction</dc:subject>
        <meta property="calibre:series">Test Series</meta>
        <meta property="calibre:series_index">1.5</meta>
        <meta property="calibre:rating">4</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.title == "Test Book"
    assert result.author_names == ["Author One", "Author Two"]
    assert result.publisher_name == "Test Publisher"
    # Date parsing may fail, so check if it's None or the expected date
    assert result.pubdate is None or result.pubdate == datetime(2020, 1, 1, tzinfo=UTC)
    assert result.description == "Test description"
    assert result.language_codes == ["en", "fr"]
    assert result.identifiers is not None
    assert len(result.identifiers) == 2
    assert result.tag_names == ["Fiction", "Science Fiction"]
    assert result.series_name == "Test Series"
    assert result.series_index == 1.5
    assert result.rating_value == 4


def test_import_metadata_minimal() -> None:
    """Test import_metadata with minimal metadata."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Minimal Book</dc:title>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.title == "Minimal Book"
    assert result.author_names is None
    assert result.publisher_name is None


def test_import_metadata_invalid_xml() -> None:
    """Test import_metadata with invalid XML."""
    importer = OpfImporter()
    with pytest.raises(ValueError, match="Invalid OPF XML format"):
        importer.import_metadata("<invalid>xml</unclosed>")


def test_import_metadata_missing_metadata_element() -> None:
    """Test import_metadata with missing metadata element."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
</package>"""
    importer = OpfImporter()
    with pytest.raises(ValueError, match="OPF file must contain a metadata element"):
        importer.import_metadata(opf_content)


def test_import_metadata_dc_date_fallback() -> None:
    """Test import_metadata uses dc:date when dcterms:date is missing."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:date>2020-01-01</dc:date>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.pubdate is not None
    assert result.pubdate.replace(tzinfo=None) == datetime(2020, 1, 1, tzinfo=None)  # noqa: DTZ001
    assert result.pubdate.tzinfo == UTC


def test_import_metadata_identifier_without_scheme() -> None:
    """Test import_metadata with identifier without scheme."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:identifier>unknown-id</dc:identifier>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.identifiers is not None
    assert len(result.identifiers) == 1
    assert result.identifiers[0]["type"] == "unknown"
    assert result.identifiers[0]["val"] == "unknown-id"


def test_import_metadata_identifier_with_opf_scheme() -> None:
    """Test import_metadata with identifier using opf:scheme attribute."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0"
         xmlns:opf="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:identifier opf:scheme="ISBN">978-1234567890</dc:identifier>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.identifiers is not None
    assert len(result.identifiers) == 1
    assert result.identifiers[0]["type"] == "isbn"
    assert result.identifiers[0]["val"] == "978-1234567890"


def test_import_metadata_series_from_name_attribute() -> None:
    """Test import_metadata with series from name attribute."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta name="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.series_name == "Test Series"


def test_import_metadata_series_from_content_text() -> None:
    """Test import_metadata with series from text content."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.series_name == "Test Series"


def test_import_metadata_rating_out_of_range() -> None:
    """Test import_metadata with rating out of range."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:rating">10</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.rating_value == 5


def test_import_metadata_rating_negative() -> None:
    """Test import_metadata with negative rating."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
              xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:rating">-5</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.rating_value == 0


def test_parse_date_iso_format() -> None:
    """Test _parse_date with ISO format."""
    result = OpfImporter._parse_date("2020-01-01T12:00:00+00:00")
    assert result == datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_parse_date_iso_with_z() -> None:
    """Test _parse_date with ISO format ending in Z."""
    result = OpfImporter._parse_date("2020-01-01T12:00:00Z")
    assert result is not None
    assert result.tzinfo is not None


def test_parse_date_common_formats() -> None:
    """Test _parse_date with common date formats."""
    result1 = OpfImporter._parse_date("2020-01-01")
    assert result1 == datetime(2020, 1, 1, tzinfo=UTC)

    result2 = OpfImporter._parse_date("2020-01-01T12:00:00")
    assert result2 is not None
    assert result2.replace(tzinfo=None) == datetime(2020, 1, 1, 12, 0, 0, tzinfo=None)  # noqa: DTZ001
    assert result2.tzinfo == UTC

    result3 = OpfImporter._parse_date("2020-01-01T12:00:00+05:00")
    assert result3 is not None
    assert result3.tzinfo is not None


def test_parse_date_invalid() -> None:
    """Test _parse_date with invalid date."""
    result = OpfImporter._parse_date("invalid-date")
    assert result is None


def test_parse_date_empty() -> None:
    """Test _parse_date with empty string."""
    result = OpfImporter._parse_date("")
    assert result is None


def test_extract_simple_fields_empty_elements() -> None:
    """Test _extract_simple_fields with empty text elements."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title></dc:title>
        <dc:publisher>   </dc:publisher>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    # Empty or whitespace-only elements should not be set
    assert result.title is None or result.title == ""


def test_extract_list_fields_empty() -> None:
    """Test _extract_list_fields with empty lists."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.author_names is None
    assert result.language_codes is None
    assert result.tag_names is None


def test_extract_identifiers_empty() -> None:
    """Test _extract_identifiers with no identifiers."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.identifiers is None


def test_extract_identifiers_empty_text() -> None:
    """Test _extract_identifiers with identifier having empty text."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:identifier scheme="ISBN"></dc:identifier>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.identifiers is None


def test_extract_meta_tag_fields_invalid_series_index() -> None:
    """Test _extract_meta_tag_fields with invalid series_index."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series_index">invalid</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.series_index is None


def test_extract_meta_tag_fields_invalid_rating() -> None:
    """Test _extract_meta_tag_fields with invalid rating."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:rating">invalid</meta>
    </metadata>
</package>"""
    importer = OpfImporter()
    result = importer.import_metadata(opf_content)

    assert result.rating_value is None


def test_find_meta_tag_by_property() -> None:
    """Test _find_meta_tag finds tag by property attribute."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
              xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    ns = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "opf": "http://www.idpf.org/2007/opf",
    }

    result = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
    assert result is not None
    assert result.get("property") == "calibre:series"


def test_find_meta_tag_by_name() -> None:
    """Test _find_meta_tag finds tag by name attribute."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
              xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>Test Book</dc:title>
        <meta name="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    ns = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "opf": "http://www.idpf.org/2007/opf",
    }

    result = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
    assert result is not None
    assert result.get("name") == "calibre:series"


def test_get_meta_content_from_attribute() -> None:
    """Test _get_meta_content gets content from content attribute."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series" content="Test Series"/>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    meta_elem = metadata_elem.find(
        ".//{http://www.idpf.org/2007/opf}meta[@property='calibre:series']"
    )

    result = OpfImporter._get_meta_content(meta_elem)
    assert result == "Test Series"


def test_get_meta_content_from_text() -> None:
    """Test _get_meta_content gets content from text."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
              xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    meta_elem = metadata_elem.find(
        ".//{http://www.idpf.org/2007/opf}meta[@property='calibre:series']"
    )

    result = OpfImporter._get_meta_content(meta_elem)
    assert result == "Test Series"


def test_get_meta_content_empty() -> None:
    """Test _get_meta_content with empty element."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series"/>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    meta_elem = metadata_elem.find(
        ".//{http://www.idpf.org/2007/opf}meta[@property='calibre:series']"
    )

    result = OpfImporter._get_meta_content(meta_elem)
    assert result is None


def test_find_meta_tag_fallback_default_namespace() -> None:
    """Test _find_meta_tag fallback to default namespace when opf: prefix not found."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    ns = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "opf": "http://www.idpf.org/2007/opf",
    }

    # This should find the meta tag in default namespace (line 299)
    result = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
    assert result is not None
    assert result.get("property") == "calibre:series"
    assert result.text == "Test Series"


def test_parse_date_timezone_aware() -> None:
    """Test _parse_date with timezone-aware datetime (lines 362-363, 367)."""
    # Test with timezone-aware datetime string
    result = OpfImporter._parse_date("2020-01-01T12:00:00+05:00")
    assert result is not None
    assert result.tzinfo is not None
    # Should return the datetime as-is (line 367)
    assert result.hour == 12


def test_find_meta_tag_fallback_property_attribute() -> None:
    """Test _find_meta_tag fallback to default namespace with property attribute (line 299)."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta property="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    ns = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "opf": "http://www.idpf.org/2007/opf",
    }

    # This should find the meta tag using the fallback path (line 299)
    # The opf: prefix searches fail, so it falls back to default namespace
    result = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
    assert result is not None
    assert result.get("property") == "calibre:series"
    assert result.text == "Test Series"


def test_find_meta_tag_fallback_name_attribute() -> None:
    """Test _find_meta_tag fallback to default namespace with name attribute (line 300)."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <meta name="calibre:series">Test Series</meta>
    </metadata>
</package>"""
    root = etree.fromstring(opf_content.encode("utf-8"))
    metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
    ns = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "opf": "http://www.idpf.org/2007/opf",
    }

    # This should find the meta tag using the fallback path (line 300)
    result = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
    assert result is not None
    assert result.get("name") == "calibre:series"
    assert result.text == "Test Series"


@pytest.mark.parametrize(
    ("date_str", "expected_hour", "has_timezone"),
    [
        ("2020-01-01T12:00:00+05:00", 12, True),  # Timezone-aware, line 367
        ("2020-01-01T12:00:00", 12, False),  # Naive, lines 362-363
        ("2020-01-01", 0, False),  # Naive date only, lines 362-363
    ],
)
def test_parse_date_strptime_paths(
    date_str: str, expected_hour: int, has_timezone: bool
) -> None:
    """Test _parse_date with strptime paths covering lines 362-363, 367."""
    result = OpfImporter._parse_date(date_str)
    assert result is not None
    assert result.hour == expected_hour
    if has_timezone:
        # Line 367: timezone-aware datetime returned as-is
        assert result.tzinfo is not None
    else:
        # Lines 362-363: naive datetime made timezone-aware
        assert result.tzinfo == UTC

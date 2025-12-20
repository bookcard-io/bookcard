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

"""Tests for MARC21 parser to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from lxml import etree  # type: ignore[attr-defined]

from bookcard.metadata.providers.dnb._marc21_parser import MARC21Parser


def test_marc21_parser_init(marc21_parser: MARC21Parser) -> None:
    """Test MARC21Parser initialization."""
    assert marc21_parser is not None
    assert hasattr(marc21_parser, "MARC21_NS")
    assert hasattr(marc21_parser, "ISO639_2B_TO_3")


def test_marc21_parser_parse_success(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test parsing a valid MARC21 record."""
    book_data = marc21_parser.parse(sample_marc21_record)
    assert book_data is not None
    assert book_data["idn"] == "123456789"
    assert book_data["isbn"] == "9783123456789"
    assert book_data["title"] == "Test Book Title : A Subtitle"
    assert "Mustermann, Max" in book_data["authors"]


def test_marc21_parser_parse_audio_content(
    marc21_parser: MARC21Parser,
    sample_marc21_record_audio: etree._Element,
) -> None:
    """Test parsing skips audio content."""
    book_data = marc21_parser.parse(sample_marc21_record_audio)
    assert book_data is None


def test_marc21_parser_parse_with_series(
    marc21_parser: MARC21Parser,
    sample_marc21_record_with_series: etree._Element,
) -> None:
    """Test parsing record with series information."""
    book_data = marc21_parser.parse(sample_marc21_record_with_series)
    assert book_data is not None
    assert book_data["series"] is not None
    assert book_data["series_index"] == "1"


def test_marc21_parser_is_media_content_audio(
    marc21_parser: MARC21Parser,
    sample_marc21_record_audio: etree._Element,
) -> None:
    """Test media content detection for audio."""
    is_media = marc21_parser._is_media_content(sample_marc21_record_audio)
    assert is_media is True


def test_marc21_parser_is_media_content_video(marc21_parser: MARC21Parser) -> None:
    """Test media content detection for video."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="337" ind1=" " ind2=" ">
            <subfield code="a">video</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    is_media = marc21_parser._is_media_content(record)
    assert is_media is True


def test_marc21_parser_is_media_content_book(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test media content detection for book."""
    is_media = marc21_parser._is_media_content(sample_marc21_record)
    assert is_media is False


def test_marc21_parser_extract_idn(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test IDN extraction."""
    idn = marc21_parser._extract_idn(sample_marc21_record)
    assert idn == "123456789"


def test_marc21_parser_extract_idn_missing(
    marc21_parser: MARC21Parser,
) -> None:
    """Test IDN extraction when missing."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Test Book</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    idn = marc21_parser._extract_idn(record)
    assert idn is None


def test_marc21_parser_extract_title_and_series(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test title and series extraction."""
    book: dict = {"title": None, "series": None, "series_index": None}
    marc21_parser._extract_title_and_series(sample_marc21_record, book)
    assert book["title"] is not None
    assert "Test Book Title" in book["title"]


def test_marc21_parser_extract_authors(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test author extraction."""
    book: dict = {"authors": []}
    marc21_parser._extract_authors(sample_marc21_record, book)
    assert len(book["authors"]) > 0
    assert any("Mustermann" in author for author in book["authors"])


def test_marc21_parser_extract_authors_secondary(marc21_parser: MARC21Parser) -> None:
    """Test author extraction with secondary authors (field 700 with role 'aut')."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="700" ind1=" " ind2=" ">
            <subfield code="4">aut</subfield>
            <subfield code="a">Secondary Author</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    book: dict = {"authors": []}
    marc21_parser._extract_authors(record, book)
    assert len(book["authors"]) > 0
    assert "Secondary Author" in book["authors"]


def test_marc21_parser_extract_authors_fallback(marc21_parser: MARC21Parser) -> None:
    """Test author extraction falls back to all involved persons."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="700" ind1=" " ind2=" ">
            <subfield code="a">Involved Person [comment]</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    book: dict = {"authors": []}
    marc21_parser._extract_authors(record, book)
    assert len(book["authors"]) > 0
    assert "Involved Person" in book["authors"][0]


def test_marc21_parser_extract_publisher_info(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test publisher information extraction."""
    book: dict = {
        "publisher_name": None,
        "publisher_location": None,
        "pubdate": None,
    }
    marc21_parser._extract_publisher_info(sample_marc21_record, book)
    assert book["publisher_name"] == "Test Verlag"
    assert book["publisher_location"] == "Berlin"
    assert book["pubdate"] is not None


def test_marc21_parser_extract_isbn(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test ISBN extraction."""
    isbn = marc21_parser._extract_isbn(sample_marc21_record)
    assert isbn == "9783123456789"


def test_marc21_parser_extract_isbn_missing(marc21_parser: MARC21Parser) -> None:
    """Test ISBN extraction when missing."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Test Book</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    isbn = marc21_parser._extract_isbn(record)
    assert isbn is None


@pytest.mark.parametrize(
    ("isbn_text", "expected"),
    [
        ("978-3-123456-78-9", "9783123456789"),
        ("ISBN 9783123456789", "9783123456789"),
        ("9783123456789", "9783123456789"),
    ],
)
def test_marc21_parser_extract_isbn_variations(
    marc21_parser: MARC21Parser,
    isbn_text: str,
    expected: str,
) -> None:
    """Test ISBN extraction with various formats."""
    xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="020" ind1=" " ind2=" ">
            <subfield code="a">{isbn_text}</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    isbn = marc21_parser._extract_isbn(record)
    assert isbn == expected


def test_marc21_parser_extract_subjects(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test subject extraction."""
    book: dict = {"tags": []}
    marc21_parser._extract_subjects(sample_marc21_record, book)
    assert len(book["tags"]) > 0
    assert "Fiction" in book["tags"]


def test_marc21_parser_extract_languages(
    marc21_parser: MARC21Parser,
    sample_marc21_record: etree._Element,
) -> None:
    """Test language extraction."""
    book: dict = {"languages": []}
    marc21_parser._extract_languages(sample_marc21_record, book)
    assert len(book["languages"]) > 0
    assert book["languages"][0] == "deu"  # ger converted to deu


def test_marc21_parser_extract_languages_iso639_conversion(
    marc21_parser: MARC21Parser,
) -> None:
    """Test ISO 639-2/B to ISO 639-3 conversion."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="041" ind1=" " ind2=" ">
            <subfield code="a">ger</subfield>
            <subfield code="a">fre</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    book: dict = {"languages": []}
    marc21_parser._extract_languages(record, book)
    assert "deu" in book["languages"]
    assert "fra" in book["languages"]


def test_marc21_parser_extract_comments_success(marc21_parser: MARC21Parser) -> None:
    """Test comment extraction from deposit URL."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="856" ind1=" " ind2=" ">
            <subfield code="u">https://deposit.dnb.de/book/123</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))

    mock_response = MagicMock()
    mock_response.text = "Test description content"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        comments = marc21_parser._extract_comments(record)
        assert comments == "Test description content"


def test_marc21_parser_extract_comments_not_available(
    marc21_parser: MARC21Parser,
) -> None:
    """Test comment extraction when access is not available."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="856" ind1=" " ind2=" ">
            <subfield code="u">https://deposit.dnb.de/book/123</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))

    mock_response = MagicMock()
    mock_response.text = "Zugriff derzeit nicht möglich"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        comments = marc21_parser._extract_comments(record)
        assert comments is None


def test_marc21_parser_extract_comments_no_url(marc21_parser: MARC21Parser) -> None:
    """Test comment extraction when no deposit URL."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Test Book</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    comments = marc21_parser._extract_comments(record)
    assert comments is None


def test_marc21_parser_extract_comments_http_error(marc21_parser: MARC21Parser) -> None:
    """Test comment extraction handles HTTP errors."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="856" ind1=" " ind2=" ">
            <subfield code="u">https://deposit.dnb.de/book/123</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))

    with patch("httpx.get", side_effect=httpx.RequestError("Error")):
        comments = marc21_parser._extract_comments(record)
        assert comments is None


def test_marc21_parser_extract_subfield_a(marc21_parser: MARC21Parser) -> None:
    """Test subfield a extraction."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <datafield tag="245" xmlns="http://www.loc.gov/MARC21/slim">
        <subfield code="a">Title Part 1</subfield>
        <subfield code="a">Title Part 2</subfield>
    </datafield>
    """
    field = etree.XML(xml_str.encode("utf-8"))
    result = marc21_parser._extract_subfield_a(field)
    assert len(result) == 2
    assert "Title Part 1" in result
    assert "Title Part 2" in result


def test_marc21_parser_extract_subfield_n(marc21_parser: MARC21Parser) -> None:
    """Test subfield n extraction."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <datafield tag="245" xmlns="http://www.loc.gov/MARC21/slim">
        <subfield code="n">1</subfield>
        <subfield code="n">Volume 2.5</subfield>
    </datafield>
    """
    field = etree.XML(xml_str.encode("utf-8"))
    result = marc21_parser._extract_subfield_n(field)
    assert len(result) == 2
    assert "1" in result
    assert "2.5" in result


def test_marc21_parser_extract_subfield_p(marc21_parser: MARC21Parser) -> None:
    """Test subfield p extraction."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <datafield tag="245" xmlns="http://www.loc.gov/MARC21/slim">
        <subfield code="p">Part One</subfield>
        <subfield code="p">Part Two</subfield>
    </datafield>
    """
    field = etree.XML(xml_str.encode("utf-8"))
    result = marc21_parser._extract_subfield_p(field)
    assert len(result) == 2
    assert "Part One" in result
    assert "Part Two" in result


def test_marc21_parser_build_series_info(marc21_parser: MARC21Parser) -> None:
    """Test series info building."""
    code_a = ["Series Name"]
    code_n = ["1", "2"]
    code_p = ["Volume One", "Volume Two"]
    _title_parts, series_info = marc21_parser._build_series_info(code_a, code_n, code_p)
    assert series_info["series"] is not None
    assert series_info["series_index"] == "2"


def test_marc21_parser_add_subtitle(marc21_parser: MARC21Parser) -> None:
    """Test subtitle addition."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <datafield tag="245" xmlns="http://www.loc.gov/MARC21/slim">
        <subfield code="a">Title</subfield>
        <subfield code="b">Subtitle</subfield>
    </datafield>
    """
    field = etree.XML(xml_str.encode("utf-8"))
    title_parts: list[str] = ["Title"]
    marc21_parser._add_subtitle(field, title_parts)
    assert len(title_parts) == 2
    assert "Subtitle" in title_parts


def test_marc21_parser_extract_gnd_subjects_689(marc21_parser: MARC21Parser) -> None:
    """Test GND subjects extraction from field 689."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="689" ind1=" " ind2=" ">
            <subfield code="a">Subject 1</subfield>
            <subfield code="a">Subject 2</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    subjects = marc21_parser._extract_gnd_subjects_689(record)
    assert len(subjects) == 2
    assert "Subject 1" in subjects
    assert "Subject 2" in subjects


def test_marc21_parser_extract_gnd_subjects_600_655(
    marc21_parser: MARC21Parser,
) -> None:
    """Test GND subjects extraction from fields 600-655."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="600" ind1=" " ind2=" ">
            <subfield code="2">gnd</subfield>
            <subfield code="a">GND Subject</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    subjects = marc21_parser._extract_gnd_subjects_600_655(record)
    assert len(subjects) > 0
    assert "GND Subject" in subjects


def test_marc21_parser_extract_non_gnd_subjects(marc21_parser: MARC21Parser) -> None:
    """Test non-GND subjects extraction."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="650" ind1=" " ind2=" ">
            <subfield code="a">Subject 1, Subject 2; Subject 3</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    subjects = marc21_parser._extract_non_gnd_subjects(record)
    assert len(subjects) >= 3
    assert any("Subject 1" in s for s in subjects)

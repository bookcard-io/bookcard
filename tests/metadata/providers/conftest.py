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

"""Shared fixtures for metadata provider tests."""

import datetime

import pytest
from lxml import etree  # type: ignore[attr-defined]

from bookcard.metadata.providers.dnb._cover_validator import CoverValidator
from bookcard.metadata.providers.dnb._marc21_parser import MARC21Parser
from bookcard.metadata.providers.dnb._query_builder import SRUQueryBuilder
from bookcard.metadata.providers.dnb._text_cleaner import TextCleaner
from bookcard.metadata.providers.dnb_provider import DNBProvider


@pytest.fixture
def dnb_provider() -> DNBProvider:
    """Create a DNBProvider instance for testing."""
    return DNBProvider(enabled=True)


@pytest.fixture
def dnb_provider_disabled() -> DNBProvider:
    """Create a disabled DNBProvider instance for testing."""
    return DNBProvider(enabled=False)


@pytest.fixture
def dnb_provider_custom_timeout() -> DNBProvider:
    """Create a DNBProvider instance with custom timeout."""
    return DNBProvider(enabled=True, timeout=20, max_results=5)


@pytest.fixture
def query_builder() -> SRUQueryBuilder:
    """Create an SRUQueryBuilder instance for testing."""
    from bookcard.metadata.providers.dnb._query_builder import SRUQueryBuilder

    return SRUQueryBuilder()


@pytest.fixture
def marc21_parser() -> MARC21Parser:
    """Create a MARC21Parser instance for testing."""
    from bookcard.metadata.providers.dnb._marc21_parser import MARC21Parser

    return MARC21Parser()


@pytest.fixture
def text_cleaner() -> TextCleaner:
    """Create a TextCleaner instance for testing."""
    from bookcard.metadata.providers.dnb._text_cleaner import TextCleaner

    return TextCleaner()


@pytest.fixture
def cover_validator() -> CoverValidator:
    """Create a CoverValidator instance for testing."""
    from bookcard.metadata.providers.dnb._cover_validator import CoverValidator

    return CoverValidator(timeout=10)


@pytest.fixture
def sample_marc21_record() -> etree._Element:
    """Create a sample MARC21 XML record for testing."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="016" ind1=" " ind2=" ">
            <subfield code="a">123456789</subfield>
        </datafield>
        <datafield tag="020" ind1=" " ind2=" ">
            <subfield code="a">978-3-123456-78-9</subfield>
        </datafield>
        <datafield tag="041" ind1=" " ind2=" ">
            <subfield code="a">ger</subfield>
        </datafield>
        <datafield tag="100" ind1="1" ind2=" ">
            <subfield code="4">aut</subfield>
            <subfield code="a">Mustermann, Max</subfield>
        </datafield>
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Test Book Title</subfield>
            <subfield code="b">A Subtitle</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="1">
            <subfield code="a">Berlin</subfield>
            <subfield code="b">Test Verlag</subfield>
            <subfield code="c">2024</subfield>
        </datafield>
        <datafield tag="689" ind1=" " ind2=" ">
            <subfield code="a">Fiction</subfield>
        </datafield>
    </record>
    """
    return etree.XML(xml_str.encode("utf-8"))


@pytest.fixture
def sample_marc21_record_with_series() -> etree._Element:
    """Create a sample MARC21 XML record with series information."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="016" ind1=" " ind2=" ">
            <subfield code="a">987654321</subfield>
        </datafield>
        <datafield tag="100" ind1="1" ind2=" ">
            <subfield code="4">aut</subfield>
            <subfield code="a">Author, Test</subfield>
        </datafield>
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Series Name</subfield>
            <subfield code="n">1</subfield>
            <subfield code="p">Volume One</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="1">
            <subfield code="b">Publisher Name</subfield>
            <subfield code="c">2023</subfield>
        </datafield>
    </record>
    """
    return etree.XML(xml_str.encode("utf-8"))


@pytest.fixture
def sample_marc21_record_audio() -> etree._Element:
    """Create a sample MARC21 XML record for audio content."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="336" ind1=" " ind2=" ">
            <subfield code="a">gesprochenes wort</subfield>
        </datafield>
        <datafield tag="337" ind1=" " ind2=" ">
            <subfield code="a">audio</subfield>
        </datafield>
    </record>
    """
    return etree.XML(xml_str.encode("utf-8"))


@pytest.fixture
def sample_sru_response() -> bytes:
    """Create a sample SRU XML response."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/" xmlns:marc21="http://www.loc.gov/MARC21/slim">
        <zs:numberOfRecords>1</zs:numberOfRecords>
        <zs:records>
            <zs:record>
                <zs:recordData>
                    <marc21:record>
                        <marc21:datafield tag="016" ind1=" " ind2=" ">
                            <marc21:subfield code="a">123456789</marc21:subfield>
                        </marc21:datafield>
                        <marc21:datafield tag="245" ind1="1" ind2="0">
                            <marc21:subfield code="a">Test Book</marc21:subfield>
                        </marc21:datafield>
                    </marc21:record>
                </zs:recordData>
            </zs:record>
        </zs:records>
    </zs:searchRetrieveResponse>
    """


@pytest.fixture
def sample_sru_response_empty() -> bytes:
    """Create a sample empty SRU XML response."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/">
        <zs:numberOfRecords>0</zs:numberOfRecords>
        <zs:records />
    </zs:searchRetrieveResponse>
    """


@pytest.fixture
def sample_book_data() -> dict:
    """Create sample book data dictionary."""
    return {
        "idn": "123456789",
        "isbn": "9783123456789",
        "title": "Test Book Title",
        "authors": ["Mustermann, Max"],
        "publisher_name": "Test Verlag",
        "publisher_location": "Berlin",
        "pubdate": datetime.datetime(2024, 1, 1, 12, 30, 0, tzinfo=datetime.UTC),
        "series": None,
        "series_index": None,
        "languages": ["deu"],
        "tags": ["Fiction"],
        "comments": None,
    }


@pytest.fixture
def sample_book_data_with_series() -> dict:
    """Create sample book data dictionary with series."""
    return {
        "idn": "987654321",
        "isbn": None,
        "title": "Volume One",
        "authors": ["Author, Test"],
        "publisher_name": "Publisher Name",
        "publisher_location": None,
        "pubdate": datetime.datetime(2023, 1, 1, 12, 30, 0, tzinfo=datetime.UTC),
        "series": "Series Name",
        "series_index": "1",
        "languages": [],
        "tags": [],
        "comments": None,
    }

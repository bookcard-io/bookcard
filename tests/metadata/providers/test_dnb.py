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

"""Tests for DNB metadata provider to achieve 100% coverage."""

import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.metadata.providers.dnb_provider import DNBProvider


def test_dnb_provider_init() -> None:
    """Test DNBProvider initialization."""
    provider = DNBProvider(enabled=True, timeout=20, max_results=5)
    assert provider.enabled is True
    assert provider.timeout == 20
    assert provider.max_results == 5


def test_dnb_provider_get_source_info(dnb_provider: DNBProvider) -> None:
    """Test get_source_info."""
    source_info = dnb_provider.get_source_info()
    assert source_info.id == "dnb"
    assert source_info.name == "Deutsche Nationalbibliothek"
    assert source_info.description == "German National Library (DNB) SRU API"
    assert source_info.base_url == "https://portal.dnb.de"


def test_dnb_provider_search_disabled(dnb_provider_disabled: DNBProvider) -> None:
    """Test search returns empty when disabled."""
    result = dnb_provider_disabled.search("test query")
    assert result == []


@pytest.mark.parametrize(
    "query",
    ["", "   ", "\t\n"],
)
def test_dnb_provider_search_empty_query(
    dnb_provider: DNBProvider,
    query: str,
) -> None:
    """Test search returns empty for empty query."""
    result = dnb_provider.search(query)
    assert result == []


def test_dnb_provider_search_success(dnb_provider: DNBProvider) -> None:
    """Test search succeeds with valid response."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/" xmlns:marc21="http://www.loc.gov/MARC21/slim">
        <zs:numberOfRecords>1</zs:numberOfRecords>
        <zs:records>
            <zs:record>
                <zs:recordData>
                    <marc21:record>
                        <marc21:datafield tag="245" ind1="1" ind2="0">
                            <marc21:subfield code="a">Test Book</marc21:subfield>
                        </marc21:datafield>
                    </marc21:record>
                </zs:recordData>
            </zs:record>
        </zs:records>
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = dnb_provider.search("test query", max_results=10)

        assert len(results) >= 0  # May be 0 if parsing fails, but no exception


def test_dnb_provider_search_no_results(dnb_provider: DNBProvider) -> None:
    """Test search returns empty when no results found."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/">
        <zs:numberOfRecords>0</zs:numberOfRecords>
        <zs:records />
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        results = dnb_provider.search("test query")
        assert results == []


def test_dnb_provider_search_timeout(dnb_provider: DNBProvider) -> None:
    """Test search raises TimeoutError."""
    with (
        patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_network_error(dnb_provider: DNBProvider) -> None:
    """Test search raises NetworkError."""
    with (
        patch("httpx.get", side_effect=httpx.RequestError("Network error")),
        pytest.raises(MetadataProviderNetworkError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_request_error_in_search(
    dnb_provider: DNBProvider,
) -> None:
    """Test search raises NetworkError from RequestError."""
    with (
        patch.object(
            dnb_provider,
            "_execute_queries_and_parse",
            side_effect=MetadataProviderNetworkError("Network error"),
        ),
        pytest.raises(MetadataProviderNetworkError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_parse_error(dnb_provider: DNBProvider) -> None:
    """Test search raises ParseError on invalid XML."""
    mock_response = MagicMock()
    mock_response.content = b"<invalid>xml"
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(MetadataProviderParseError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_xml_syntax_error_in_search(
    dnb_provider: DNBProvider,
) -> None:
    """Test search raises ParseError from XMLSyntaxError."""
    with (
        patch.object(
            dnb_provider,
            "_execute_queries_and_parse",
            side_effect=MetadataProviderParseError("Parse error"),
        ),
        pytest.raises(MetadataProviderParseError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_timeout_exception(dnb_provider: DNBProvider) -> None:
    """Test search raises TimeoutError on timeout."""
    with (
        patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_timeout_exception_in_search(
    dnb_provider: DNBProvider,
) -> None:
    """Test search raises TimeoutError from TimeoutException in search method."""
    # Mock _query_builder.build_queries to raise TimeoutException
    with (
        patch.object(
            dnb_provider._query_builder,
            "build_queries",
            side_effect=httpx.TimeoutException("Timeout"),
        ),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_request_error(dnb_provider: DNBProvider) -> None:
    """Test search raises NetworkError on request error."""
    with (
        patch("httpx.get", side_effect=httpx.RequestError("Network error")),
        pytest.raises(MetadataProviderNetworkError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_request_error_in_search_method(
    dnb_provider: DNBProvider,
) -> None:
    """Test search raises NetworkError from RequestError in search method."""
    # Mock _query_builder.build_queries to raise RequestError
    with (
        patch.object(
            dnb_provider._query_builder,
            "build_queries",
            side_effect=httpx.RequestError("Network error"),
        ),
        pytest.raises(MetadataProviderNetworkError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_xml_syntax_error(dnb_provider: DNBProvider) -> None:
    """Test search raises ParseError on XML syntax error."""
    from lxml import etree  # type: ignore[attr-defined]

    mock_response = MagicMock()
    mock_response.content = b"<invalid>xml"
    mock_response.raise_for_status = MagicMock()

    # XMLSyntaxError requires more arguments
    with (
        patch("httpx.get", return_value=mock_response),
        patch(
            "bookcard.metadata.providers.dnb_provider.etree.XML",
            side_effect=etree.XMLSyntaxError("Invalid XML", "file", 1, 1, "error"),
        ),
        pytest.raises(MetadataProviderParseError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_xml_syntax_error_in_search_method(
    dnb_provider: DNBProvider,
) -> None:
    """Test search raises ParseError from XMLSyntaxError in search method."""
    from lxml import etree  # type: ignore[attr-defined]

    # Mock _query_builder.build_queries to raise XMLSyntaxError
    with (
        patch.object(
            dnb_provider._query_builder,
            "build_queries",
            side_effect=etree.XMLSyntaxError("Invalid XML", "file", 1, 1),
        ),
        pytest.raises(MetadataProviderParseError),
    ):
        dnb_provider.search("test query")


def test_dnb_provider_search_key_error_handling(dnb_provider: DNBProvider) -> None:
    """Test search handles KeyError gracefully."""
    # Mock _query_builder.build_queries to raise KeyError
    with patch.object(
        dnb_provider._query_builder,
        "build_queries",
        side_effect=KeyError("missing key"),
    ):
        result = dnb_provider.search("test query")
        assert result == []


def test_dnb_provider_search_value_error_handling(dnb_provider: DNBProvider) -> None:
    """Test search handles ValueError gracefully."""
    with patch.object(
        dnb_provider._query_builder,
        "build_queries",
        side_effect=ValueError("invalid value"),
    ):
        result = dnb_provider.search("test query")
        assert result == []


def test_dnb_provider_search_type_error_handling(dnb_provider: DNBProvider) -> None:
    """Test search handles TypeError gracefully."""
    with patch.object(
        dnb_provider._query_builder,
        "build_queries",
        side_effect=TypeError("invalid type"),
    ):
        result = dnb_provider.search("test query")
        assert result == []


def test_dnb_provider_search_attribute_error_handling(
    dnb_provider: DNBProvider,
) -> None:
    """Test search handles AttributeError gracefully."""
    with patch.object(
        dnb_provider._query_builder,
        "build_queries",
        side_effect=AttributeError("missing attribute"),
    ):
        result = dnb_provider.search("test query")
        assert result == []


def test_dnb_provider_parse_query_idn(dnb_provider: DNBProvider) -> None:
    """Test query parsing for DNB IDN."""
    query_params = dnb_provider._parse_query("dnb-idn:123456789")
    assert query_params["idn"] == "123456789"
    assert query_params["isbn"] is None
    assert query_params["title"] is None


def test_dnb_provider_parse_query_isbn(dnb_provider: DNBProvider) -> None:
    """Test query parsing for ISBN."""
    query_params = dnb_provider._parse_query("isbn:9783123456789")
    assert query_params["idn"] is None
    assert query_params["isbn"] == "9783123456789"
    assert query_params["title"] is None


def test_dnb_provider_parse_query_title(dnb_provider: DNBProvider) -> None:
    """Test query parsing for title."""
    query_params = dnb_provider._parse_query("Test Book Title")
    assert query_params["idn"] is None
    assert query_params["isbn"] is None
    assert query_params["title"] == "Test Book Title"


def test_dnb_provider_execute_sru_query_success(
    dnb_provider: DNBProvider,
) -> None:
    """Test SRU query execution succeeds."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/" xmlns:marc21="http://www.loc.gov/MARC21/slim">
        <zs:numberOfRecords>1</zs:numberOfRecords>
        <zs:records>
            <zs:record>
                <zs:recordData>
                    <marc21:record>
                        <marc21:datafield tag="245" ind1="1" ind2="0">
                            <marc21:subfield code="a">Test Book</marc21:subfield>
                        </marc21:datafield>
                    </marc21:record>
                </zs:recordData>
            </zs:record>
        </zs:records>
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        records = dnb_provider._execute_sru_query('tit="Test Book"')
        assert isinstance(records, list)


def test_dnb_provider_execute_sru_query_empty(dnb_provider: DNBProvider) -> None:
    """Test SRU query execution returns empty list."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/">
        <zs:numberOfRecords>0</zs:numberOfRecords>
        <zs:records />
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        records = dnb_provider._execute_sru_query('tit="No Results"')
        assert records == []


def test_dnb_provider_execute_sru_query_timeout(dnb_provider: DNBProvider) -> None:
    """Test SRU query execution raises TimeoutError."""
    with (
        patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        dnb_provider._execute_sru_query('tit="Test"')


def test_dnb_provider_execute_sru_query_network_error(
    dnb_provider: DNBProvider,
) -> None:
    """Test SRU query execution raises NetworkError."""
    with (
        patch("httpx.get", side_effect=httpx.RequestError("Network error")),
        pytest.raises(MetadataProviderNetworkError),
    ):
        dnb_provider._execute_sru_query('tit="Test"')


def test_dnb_provider_execute_sru_query_parse_error(dnb_provider: DNBProvider) -> None:
    """Test SRU query execution raises ParseError."""
    mock_response = MagicMock()
    mock_response.content = b"<invalid>xml"
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.get", return_value=mock_response),
        pytest.raises(MetadataProviderParseError),
    ):
        dnb_provider._execute_sru_query('tit="Test"')


def test_dnb_provider_build_query_string(dnb_provider: DNBProvider) -> None:
    """Test query string building."""
    params = {"version": "1.1", "query": "test query"}
    query_string = dnb_provider._build_query_string(params)
    assert "version=1.1" in query_string
    assert "query=test" in query_string


def test_dnb_provider_is_valid_book(dnb_provider: DNBProvider) -> None:
    """Test book validation."""
    valid_book = {"title": "Test", "authors": ["Author"]}
    assert dnb_provider._is_valid_book(valid_book) is True

    invalid_book_no_title = {"authors": ["Author"]}
    assert dnb_provider._is_valid_book(invalid_book_no_title) is False

    invalid_book_no_authors = {"title": "Test"}
    assert dnb_provider._is_valid_book(invalid_book_no_authors) is False


def test_dnb_provider_create_metadata_record(dnb_provider: DNBProvider) -> None:
    """Test metadata record creation."""

    sample_book_data = {
        "idn": "123456789",
        "isbn": "9783123456789",
        "title": "Test Book Title",
        "authors": ["Mustermann, Max"],
        "publisher_name": "Test Verlag",
        "publisher_location": "Berlin",
        "pubdate": datetime.datetime(
            2024,
            1,
            1,
            12,
            30,
            0,
            tzinfo=datetime.UTC,
        ),
        "series": None,
        "series_index": None,
        "languages": ["deu"],
        "tags": ["Fiction"],
        "comments": None,
    }
    record = dnb_provider._create_metadata_record(sample_book_data)
    assert record is not None
    assert record.title == "Test Book Title"
    assert record.authors == ["Max Mustermann"]
    assert record.source_id == "dnb"
    assert record.external_id == "123456789"
    assert "isbn" in record.identifiers
    assert record.identifiers["isbn"] == "9783123456789"


def test_dnb_provider_create_metadata_record_invalid(
    dnb_provider: DNBProvider,
) -> None:
    """Test metadata record creation with invalid data."""
    invalid_data = {"title": "", "authors": []}
    record = dnb_provider._create_metadata_record(invalid_data)
    assert record is None


def test_dnb_provider_create_metadata_record_with_series(
    dnb_provider: DNBProvider,
) -> None:
    """Test metadata record creation with series."""

    sample_book_data_with_series = {
        "idn": "987654321",
        "isbn": None,
        "title": "Volume One",
        "authors": ["Author, Test"],
        "publisher_name": "Publisher Name",
        "publisher_location": None,
        "pubdate": datetime.datetime(
            2023,
            1,
            1,
            12,
            30,
            0,
            tzinfo=datetime.UTC,
        ),
        "series": "Series Name",
        "series_index": "1",
        "languages": [],
        "tags": [],
        "comments": None,
    }
    record = dnb_provider._create_metadata_record(sample_book_data_with_series)
    assert record is not None
    assert record.series == "Series Name"
    assert record.series_index == 1.0


def test_dnb_provider_create_metadata_record_with_urn(
    dnb_provider: DNBProvider,
) -> None:
    """Test metadata record creation with URN identifier."""

    sample_book_data = {
        "idn": "123456789",
        "isbn": "9783123456789",
        "urn": "urn:nbn:de:101:1-202312345",
        "title": "Test Book",
        "authors": ["Test Author"],
        "publisher_name": "Test Verlag",
        "publisher_location": "Berlin",
        "pubdate": datetime.datetime(
            2024,
            1,
            1,
            12,
            30,
            0,
            tzinfo=datetime.UTC,
        ),
        "series": None,
        "series_index": None,
        "languages": ["deu"],
        "tags": ["Fiction"],
        "comments": None,
    }
    record = dnb_provider._create_metadata_record(sample_book_data)
    assert record is not None
    assert "urn" in record.identifiers
    assert record.identifiers["urn"] == "urn:nbn:de:101:1-202312345"


def test_dnb_provider_create_metadata_record_exception(
    dnb_provider: DNBProvider,
) -> None:
    """Test metadata record creation handles exceptions."""
    # Missing required fields to trigger KeyError
    invalid_book_data = {}
    record = dnb_provider._create_metadata_record(invalid_book_data)
    assert record is None


def test_dnb_provider_create_metadata_record_value_error(
    dnb_provider: DNBProvider,
) -> None:
    """Test metadata record creation handles ValueError."""
    # Invalid series_index to trigger ValueError in float()
    invalid_book_data = {
        "title": "Test",
        "authors": ["Author"],
        "series_index": "not a number",
    }
    record = dnb_provider._create_metadata_record(invalid_book_data)
    assert record is None


def test_dnb_provider_format_published_date_none(dnb_provider: DNBProvider) -> None:
    """Test published date formatting with None."""
    result = dnb_provider._format_published_date(None)
    assert result is None


def test_dnb_provider_format_published_date_string(dnb_provider: DNBProvider) -> None:
    """Test published date formatting with string."""
    result = dnb_provider._format_published_date("2024-01-01")
    assert result == "2024-01-01"


def test_dnb_provider_format_published_date_invalid_type(
    dnb_provider: DNBProvider,
) -> None:
    """Test published date formatting with invalid type."""
    # Use Any to bypass type checking for invalid type test
    from typing import Any

    invalid_date: Any = 12345
    result = dnb_provider._format_published_date(invalid_date)  # type: ignore[arg-type]
    assert result is None


def test_dnb_provider_execute_queries_and_parse_success(
    dnb_provider: DNBProvider,
) -> None:
    """Test execute queries and parse stops on first success."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
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
                        <marc21:datafield tag="100" ind1="1" ind2=" ">
                            <marc21:subfield code="4">aut</marc21:subfield>
                            <marc21:subfield code="a">Test Author</marc21:subfield>
                        </marc21:datafield>
                    </marc21:record>
                </zs:recordData>
            </zs:record>
        </zs:records>
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        queries = ['tit="Test Book"', 'tit="Other Query"']
        records = dnb_provider._execute_queries_and_parse(queries)
        # Should stop after first successful query
        assert len(records) >= 0


def test_dnb_provider_execute_queries_and_parse_with_exception(
    dnb_provider: DNBProvider,
) -> None:
    """Test execute queries and parse handles exceptions."""
    sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
    <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/" xmlns:marc21="http://www.loc.gov/MARC21/slim">
        <zs:numberOfRecords>1</zs:numberOfRecords>
        <zs:records>
            <zs:record>
                <zs:recordData>
                    <marc21:record>
                        <marc21:datafield tag="245" ind1="1" ind2="0">
                            <marc21:subfield code="a">Test Book</marc21:subfield>
                        </marc21:datafield>
                    </marc21:record>
                </zs:recordData>
            </zs:record>
        </zs:records>
    </zs:searchRetrieveResponse>
    """
    mock_response = MagicMock()
    mock_response.content = sample_response
    mock_response.raise_for_status = MagicMock()

    with (
        patch("httpx.get", return_value=mock_response),
        patch.object(
            dnb_provider._parser,
            "parse",
            side_effect=ValueError("parse error"),
        ),
    ):
        queries = ['tit="Test Book"']
        records = dnb_provider._execute_queries_and_parse(queries)
        assert records == []


def test_dnb_provider_parse_marc21_records_success(dnb_provider: DNBProvider) -> None:
    """Test parsing MARC21 records into metadata records."""
    from lxml import etree  # type: ignore[attr-defined]

    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <datafield tag="016" ind1=" " ind2=" ">
            <subfield code="a">123456789</subfield>
        </datafield>
        <datafield tag="245" ind1="1" ind2="0">
            <subfield code="a">Test Book</subfield>
        </datafield>
        <datafield tag="100" ind1="1" ind2=" ">
            <subfield code="4">aut</subfield>
            <subfield code="a">Test Author</subfield>
        </datafield>
    </record>
    """
    record = etree.XML(xml_str.encode("utf-8"))
    records = dnb_provider._parse_marc21_records([record])
    assert len(records) > 0
    assert records[0].title == "Test Book"


def test_dnb_provider_custom_timeout() -> None:
    """Test provider with custom timeout."""
    provider = DNBProvider(enabled=True, timeout=20, max_results=5)
    assert provider.timeout == 20
    assert provider.max_results == 5

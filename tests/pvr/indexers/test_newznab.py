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

"""Tests for Newznab indexer implementation."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET  # noqa: S405

import httpx
import pytest

from bookcard.pvr.base import (
    IndexerSettings,
    PVRProviderAuthenticationError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.indexers.newznab import (
    NEWZNAB_NS,
    NewznabIndexer,
    NewznabParser,
    NewznabRequestGenerator,
    NewznabSettings,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def newznab_settings_fixture() -> NewznabSettings:
    """Create Newznab settings for testing."""
    return NewznabSettings(
        base_url="https://newznab.example.com",
        api_key="test-key",
        timeout_seconds=30,
        retry_count=3,
        categories=[7000, 7020],
        api_path="/api",
    )


@pytest.fixture
def newznab_indexer(newznab_settings_fixture: NewznabSettings) -> NewznabIndexer:
    """Create Newznab indexer instance."""
    return NewznabIndexer(settings=newznab_settings_fixture, enabled=True)


@pytest.fixture
def newznab_parser() -> NewznabParser:
    """Create Newznab parser instance."""
    return NewznabParser()


@pytest.fixture
def newznab_request_generator(
    newznab_settings_fixture: NewznabSettings,
) -> NewznabRequestGenerator:
    """Create Newznab request generator instance."""
    return NewznabRequestGenerator(settings=newznab_settings_fixture)


@pytest.fixture
def sample_item_xml() -> ET.Element:
    """Create sample XML item element."""
    item = ET.Element("item")
    ET.SubElement(item, "title").text = "Test Book Title"
    ET.SubElement(item, "link").text = "https://example.com/item"
    ET.SubElement(item, "description").text = "Test description"
    ET.SubElement(item, "category").text = "Books"
    ET.SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 12:00:00 +0000"
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", "https://example.com/file.nzb")
    enclosure.set("length", "1000000")
    return item


# ============================================================================
# NewznabSettings Tests
# ============================================================================


class TestNewznabSettings:
    """Test NewznabSettings class."""

    def test_newznab_settings_default_api_path(self) -> None:
        """Test NewznabSettings with default api_path."""
        settings = NewznabSettings(base_url="https://example.com")
        assert settings.api_path == "/api"

    def test_newznab_settings_custom_api_path(self) -> None:
        """Test NewznabSettings with custom api_path."""
        settings = NewznabSettings(
            base_url="https://example.com", api_path="/custom/api"
        )
        assert settings.api_path == "/custom/api"


# ============================================================================
# NewznabRequestGenerator Tests
# ============================================================================


class TestNewznabRequestGenerator:
    """Test NewznabRequestGenerator class."""

    def test_init(self, newznab_settings_fixture: NewznabSettings) -> None:
        """Test NewznabRequestGenerator initialization."""
        generator = NewznabRequestGenerator(settings=newznab_settings_fixture)
        assert generator.settings == newznab_settings_fixture

    @pytest.mark.parametrize(
        ("query", "title", "author", "isbn", "expected_q"),
        [
            ("test query", None, None, None, "test query"),
            (None, "Test Title", None, None, "Test Title"),
            (None, None, "Author Name", None, "Author Name"),
            (None, None, None, "1234567890", "1234567890"),
            ("query", "title", None, None, "query"),  # query takes precedence
        ],
    )
    def test_build_search_url_query_params(
        self,
        newznab_request_generator: NewznabRequestGenerator,
        query: str | None,
        title: str | None,
        author: str | None,
        isbn: str | None,
        expected_q: str,
    ) -> None:
        """Test build_search_url with various query parameters."""
        from urllib.parse import parse_qs, urlparse

        url = newznab_request_generator.build_search_url(
            query=query, title=title, author=author, isbn=isbn
        )
        assert "t=search" in url
        assert "extended=1" in url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params.get("q") == [expected_q]
        assert "apikey=test-key" in url

    def test_build_search_url_with_categories(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_search_url with categories."""
        url = newznab_request_generator.build_search_url(
            query="test", categories=[7000, 7020]
        )
        assert "cat=7000%2C7020" in url or "cat=7000,7020" in url

    def test_build_search_url_default_categories(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_search_url with default categories."""
        url = newznab_request_generator.build_search_url(query="test")
        assert "cat=" in url

    def test_build_search_url_pagination(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_search_url with pagination."""
        url = newznab_request_generator.build_search_url(
            query="test", offset=10, limit=50
        )
        assert "offset=10" in url
        assert "limit=50" in url

    def test_build_search_url_no_api_key(
        self, newznab_settings_fixture: NewznabSettings
    ) -> None:
        """Test build_search_url without API key."""
        newznab_settings_fixture.api_key = None
        generator = NewznabRequestGenerator(settings=newznab_settings_fixture)
        url = generator.build_search_url(query="test")
        assert "apikey" not in url

    def test_build_rss_url(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_rss_url."""
        url = newznab_request_generator.build_rss_url()
        assert "t=rss" in url
        assert "extended=1" in url
        assert "apikey=test-key" in url

    def test_build_rss_url_with_categories(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_rss_url with categories."""
        url = newznab_request_generator.build_rss_url(categories=[7000])
        assert "cat=7000" in url

    def test_build_rss_url_with_limit(
        self, newznab_request_generator: NewznabRequestGenerator
    ) -> None:
        """Test build_rss_url with limit."""
        url = newznab_request_generator.build_rss_url(limit=25)
        assert "limit=25" in url


# ============================================================================
# NewznabParser Tests
# ============================================================================


class TestNewznabParser:
    """Test NewznabParser class."""

    def test_init(self, newznab_parser: NewznabParser) -> None:
        """Test NewznabParser initialization."""
        assert newznab_parser.ns == NEWZNAB_NS

    def test_parse_response_bytes(
        self, newznab_parser: NewznabParser, sample_newznab_xml: bytes
    ) -> None:
        """Test parse_response with bytes input."""
        releases = newznab_parser.parse_response(sample_newznab_xml)
        assert len(releases) == 1
        assert releases[0].title == "Test Book - Author Name [EPUB]"

    def test_parse_response_str(
        self, newznab_parser: NewznabParser, sample_newznab_xml: bytes
    ) -> None:
        """Test parse_response with string input."""
        releases = newznab_parser.parse_response(sample_newznab_xml.decode())
        assert len(releases) == 1

    def test_parse_response_with_indexer_id(
        self, newznab_parser: NewznabParser, sample_newznab_xml: bytes
    ) -> None:
        """Test parse_response with indexer_id."""
        releases = newznab_parser.parse_response(sample_newznab_xml, indexer_id=1)
        assert releases[0].indexer_id == 1

    def test_parse_response_error_element(self, newznab_parser: NewznabParser) -> None:
        """Test parse_response with error element."""
        # Error element in channel (standard RSS format)
        xml = b"""<?xml version="1.0"?>
<rss><channel><error code="100" description="API key required"/></channel></rss>"""
        with pytest.raises(PVRProviderAuthenticationError):
            newznab_parser.parse_response(xml)

    def test_parse_response_invalid_xml(self, newznab_parser: NewznabParser) -> None:
        """Test parse_response with invalid XML."""
        with pytest.raises(PVRProviderParseError):
            newznab_parser.parse_response(b"<invalid>xml")

    def test_parse_response_empty_items(self, newznab_parser: NewznabParser) -> None:
        """Test parse_response with no items."""
        xml = b"""<?xml version="1.0"?><rss><channel></channel></rss>"""
        releases = newznab_parser.parse_response(xml)
        assert releases == []

    def test_parse_response_item_parse_error(
        self, newznab_parser: NewznabParser
    ) -> None:
        """Test parse_response with item parse error."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><invalid/></item>
        </channel></rss>"""
        releases = newznab_parser.parse_response(xml)
        assert len(releases) == 1  # Only valid item parsed

    def test_parse_item_complete(
        self, newznab_parser: NewznabParser, sample_item_xml: ET.Element
    ) -> None:
        """Test _parse_item with complete item."""
        release = newznab_parser._parse_item(sample_item_xml, indexer_id=1)
        assert release is not None
        assert release.title == "Test Book Title"
        assert release.download_url == "https://example.com/file.nzb"
        assert release.indexer_id == 1

    def test_parse_item_no_title(self, newznab_parser: NewznabParser) -> None:
        """Test _parse_item with no title."""
        item = ET.Element("item")
        release = newznab_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_parse_item_no_download_url(self, newznab_parser: NewznabParser) -> None:
        """Test _parse_item with no download URL."""
        item = ET.Element("item")
        ET.SubElement(item, "title").text = "Test"
        release = newznab_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_extract_publish_date_valid(self, newznab_parser: NewznabParser) -> None:
        """Test _extract_publish_date with valid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 12:00:00 +0000"
        date = newznab_parser._extract_publish_date(item)
        assert date is not None
        assert isinstance(date, datetime)

    def test_extract_publish_date_invalid(self, newznab_parser: NewznabParser) -> None:
        """Test _extract_publish_date with invalid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "invalid date"
        date = newznab_parser._extract_publish_date(item)
        assert date is None

    def test_extract_publish_date_missing(self, newznab_parser: NewznabParser) -> None:
        """Test _extract_publish_date with missing date."""
        item = ET.Element("item")
        date = newznab_parser._extract_publish_date(item)
        assert date is None

    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Book Title [EPUB]", "epub"),
            ("Book Title [PDF]", "pdf"),
            ("Book Title [MOBI]", "mobi"),
            ("Book Title [AZW]", "azw"),
            ("Book Title [KINDLE]", "azw"),
            ("Book Title", None),
        ],
    )
    def test_infer_quality_from_title(
        self, newznab_parser: NewznabParser, title: str, expected: str | None
    ) -> None:
        """Test _infer_quality_from_title."""
        quality = newznab_parser._infer_quality_from_title(title)
        assert quality == expected

    def test_extract_metadata_with_attributes(
        self, newznab_parser: NewznabParser
    ) -> None:
        """Test _extract_metadata with Newznab attributes."""
        item = ET.Element("item")
        attr1 = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr1.set("name", "author")
        attr1.set("value", "Test Author")
        attr2 = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr2.set("name", "isbn")
        attr2.set("value", "1234567890")
        attr3 = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr3.set("name", "format")
        attr3.set("value", "epub")

        author, isbn, quality = newznab_parser._extract_metadata(item, "Test Title")
        assert author == "Test Author"
        assert isbn == "1234567890"
        assert quality == "epub"

    def test_extract_metadata_infer_quality(
        self, newznab_parser: NewznabParser
    ) -> None:
        """Test _extract_metadata infers quality from title."""
        item = ET.Element("item")
        _author, _isbn, quality = newznab_parser._extract_metadata(
            item, "Test Book [EPUB]"
        )
        assert quality == "epub"

    def test_get_download_url_enclosure(self, newznab_parser: NewznabParser) -> None:
        """Test _get_download_url from enclosure."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", "https://example.com/file.nzb")
        url = newznab_parser._get_download_url(item)
        assert url == "https://example.com/file.nzb"

    def test_get_download_url_link(self, newznab_parser: NewznabParser) -> None:
        """Test _get_download_url from link."""
        item = ET.Element("item")
        ET.SubElement(item, "link").text = "https://example.com/file.nzb"
        url = newznab_parser._get_download_url(item)
        assert url == "https://example.com/file.nzb"

    def test_get_download_url_none(self, newznab_parser: NewznabParser) -> None:
        """Test _get_download_url with no URL."""
        item = ET.Element("item")
        url = newznab_parser._get_download_url(item)
        assert url is None

    def test_get_size_from_attribute(self, newznab_parser: NewznabParser) -> None:
        """Test _get_size from Newznab attribute."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr.set("name", "size")
        attr.set("value", "1000000")
        size = newznab_parser._get_size(item)
        assert size == 1000000

    def test_get_size_from_enclosure(self, newznab_parser: NewznabParser) -> None:
        """Test _get_size from enclosure length."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("length", "2000000")
        size = newznab_parser._get_size(item)
        assert size == 2000000

    def test_get_size_invalid(self, newznab_parser: NewznabParser) -> None:
        """Test _get_size with invalid value."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr.set("name", "size")
        attr.set("value", "invalid")
        size = newznab_parser._get_size(item)
        assert size is None

    def test_get_newznab_attribute_found(self, newznab_parser: NewznabParser) -> None:
        """Test _get_newznab_attribute when found."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{NEWZNAB_NS}attr")
        attr.set("name", "author")
        attr.set("value", "Test Author")
        value = newznab_parser._get_newznab_attribute(item, "author")
        assert value == "Test Author"

    def test_get_newznab_attribute_not_found(
        self, newznab_parser: NewznabParser
    ) -> None:
        """Test _get_newznab_attribute when not found."""
        item = ET.Element("item")
        value = newznab_parser._get_newznab_attribute(item, "author", default="default")
        assert value == "default"


# ============================================================================
# NewznabIndexer Tests
# ============================================================================


class TestNewznabIndexer:
    """Test NewznabIndexer class."""

    def test_init_with_newznab_settings(
        self, newznab_settings_fixture: NewznabSettings
    ) -> None:
        """Test initialization with NewznabSettings."""
        indexer = NewznabIndexer(settings=newznab_settings_fixture)
        assert indexer.settings == newznab_settings_fixture
        assert isinstance(indexer.request_generator, NewznabRequestGenerator)
        assert isinstance(indexer.parser, NewznabParser)

    def test_init_with_indexer_settings(
        self, indexer_settings: IndexerSettings
    ) -> None:
        """Test initialization with IndexerSettings."""
        indexer = NewznabIndexer(settings=indexer_settings)
        assert isinstance(indexer.settings, NewznabSettings)
        assert indexer.settings.api_path == "/api"

    def test_init_disabled(self, newznab_settings_fixture: NewznabSettings) -> None:
        """Test initialization with disabled=True."""
        indexer = NewznabIndexer(settings=newznab_settings_fixture, enabled=False)
        assert not indexer.is_enabled()

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_search_success(
        self,
        mock_client: MagicMock,
        newznab_indexer: NewznabIndexer,
        sample_newznab_xml: bytes,
    ) -> None:
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.content = sample_newznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = newznab_indexer.search(query="test")
        assert len(results) == 1
        assert results[0].title == "Test Book - Author Name [EPUB]"

    @pytest.mark.parametrize(
        ("query", "title", "author", "isbn"),
        [
            ("test", None, None, None),
            (None, "Title", None, None),
            (None, None, "Author", None),
            (None, None, None, "1234567890"),
        ],
    )
    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_search_with_params(
        self,
        mock_client: MagicMock,
        newznab_indexer: NewznabIndexer,
        sample_newznab_xml: bytes,
        query: str | None,
        title: str | None,
        author: str | None,
        isbn: str | None,
    ) -> None:
        """Test search with various parameters."""
        mock_response = MagicMock()
        mock_response.content = sample_newznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = newznab_indexer.search(
            query=query or "", title=title, author=author, isbn=isbn
        )
        assert len(results) > 0

    def test_search_disabled(self, newznab_indexer: NewznabIndexer) -> None:
        """Test search when indexer is disabled."""
        newznab_indexer.set_enabled(False)
        results = newznab_indexer.search(query="test")
        assert results == []

    def test_search_no_query(self, newznab_indexer: NewznabIndexer) -> None:
        """Test search with no query parameters."""
        results = newznab_indexer.search(query="")
        assert results == []

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_search_max_results(
        self,
        mock_client: MagicMock,
        newznab_indexer: NewznabIndexer,
        sample_newznab_xml: bytes,
    ) -> None:
        """Test search with max_results limit."""
        mock_response = MagicMock()
        mock_response.content = sample_newznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = newznab_indexer.search(query="test", max_results=1)
        assert len(results) <= 1

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_search_network_error(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test search with network error."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.RequestError("Network error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            newznab_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_search_timeout(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test search with timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            newznab_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_test_connection_success(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.content = (
            b"""<?xml version="1.0"?><rss><channel></channel></rss>"""
        )
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        result = newznab_indexer.test_connection()
        assert result is True

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_test_connection_error(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test connection test with error."""
        mock_response = MagicMock()
        # Error element in channel (standard RSS format)
        mock_response.content = b"""<?xml version="1.0"?>
<rss><channel><error code="100" description="API key required"/></channel></rss>"""
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderAuthenticationError):
            newznab_indexer.test_connection()

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_make_request_success(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test _make_request success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        response = newznab_indexer._make_request("https://example.com")
        assert response.status_code == 200

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_make_request_timeout(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test _make_request timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            newznab_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.newznab.httpx.Client")
    def test_make_request_http_error(
        self, mock_client: MagicMock, newznab_indexer: NewznabIndexer
    ) -> None:
        """Test _make_request HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            newznab_indexer._make_request("https://example.com")

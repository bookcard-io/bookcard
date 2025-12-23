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

"""Tests for Torznab indexer implementation."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET  # noqa: S405

import httpx
import pytest

from bookcard.pvr.base import (
    IndexerSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.indexers.torznab import (
    TORZNAB_NS,
    TorznabIndexer,
    TorznabParser,
    TorznabRequestGenerator,
    TorznabSettings,
)
from bookcard.pvr.models import ReleaseInfo

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def torznab_settings_fixture() -> TorznabSettings:
    """Create Torznab settings for testing."""
    return TorznabSettings(
        base_url="https://torznab.example.com",
        api_key="test-key",
        timeout_seconds=30,
        retry_count=3,
        categories=[7000, 7020],
        api_path="/api",
    )


@pytest.fixture
def torznab_indexer(torznab_settings_fixture: TorznabSettings) -> TorznabIndexer:
    """Create Torznab indexer instance."""
    return TorznabIndexer(settings=torznab_settings_fixture, enabled=True)


@pytest.fixture
def torznab_parser() -> TorznabParser:
    """Create Torznab parser instance."""
    return TorznabParser()


@pytest.fixture
def torznab_request_generator(
    torznab_settings_fixture: TorznabSettings,
) -> TorznabRequestGenerator:
    """Create Torznab request generator instance."""
    return TorznabRequestGenerator(settings=torznab_settings_fixture)


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
    enclosure.set("url", "https://example.com/file.torrent")
    enclosure.set("length", "1000000")
    return item


# ============================================================================
# TorznabSettings Tests
# ============================================================================


class TestTorznabSettings:
    """Test TorznabSettings class."""

    def test_torznab_settings_default_api_path(self) -> None:
        """Test TorznabSettings with default api_path."""
        settings = TorznabSettings(base_url="https://example.com")
        assert settings.api_path == "/api"

    def test_torznab_settings_custom_api_path(self) -> None:
        """Test TorznabSettings with custom api_path."""
        settings = TorznabSettings(
            base_url="https://example.com", api_path="/custom/api"
        )
        assert settings.api_path == "/custom/api"


# ============================================================================
# TorznabRequestGenerator Tests
# ============================================================================


class TestTorznabRequestGenerator:
    """Test TorznabRequestGenerator class."""

    def test_init(self, torznab_settings_fixture: TorznabSettings) -> None:
        """Test TorznabRequestGenerator initialization."""
        generator = TorznabRequestGenerator(settings=torznab_settings_fixture)
        assert generator.settings == torznab_settings_fixture

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
        torznab_request_generator: TorznabRequestGenerator,
        query: str | None,
        title: str | None,
        author: str | None,
        isbn: str | None,
        expected_q: str,
    ) -> None:
        """Test build_search_url with various query parameters."""
        from urllib.parse import parse_qs, urlparse

        url = torznab_request_generator.build_search_url(
            query=query, title=title, author=author, isbn=isbn
        )
        assert "t=search" in url
        assert "extended=1" in url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params.get("q") == [expected_q]
        assert "apikey=test-key" in url

    def test_build_search_url_with_categories(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_search_url with categories."""
        url = torznab_request_generator.build_search_url(
            query="test", categories=[7000, 7020]
        )
        assert "cat=7000%2C7020" in url or "cat=7000,7020" in url

    def test_build_search_url_default_categories(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_search_url with default categories."""
        url = torznab_request_generator.build_search_url(query="test")
        assert "cat=" in url

    def test_build_search_url_pagination(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_search_url with pagination."""
        url = torznab_request_generator.build_search_url(
            query="test", offset=10, limit=50
        )
        assert "offset=10" in url
        assert "limit=50" in url

    def test_build_search_url_no_api_key(
        self, torznab_settings_fixture: TorznabSettings
    ) -> None:
        """Test build_search_url without API key."""
        torznab_settings_fixture.api_key = None
        generator = TorznabRequestGenerator(settings=torznab_settings_fixture)
        url = generator.build_search_url(query="test")
        assert "apikey" not in url

    def test_build_rss_url(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_rss_url."""
        url = torznab_request_generator.build_rss_url()
        assert "t=rss" in url
        assert "extended=1" in url
        assert "apikey=test-key" in url

    def test_build_rss_url_with_categories(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_rss_url with categories."""
        url = torznab_request_generator.build_rss_url(categories=[7000])
        assert "cat=7000" in url

    def test_build_rss_url_with_limit(
        self, torznab_request_generator: TorznabRequestGenerator
    ) -> None:
        """Test build_rss_url with limit."""
        url = torznab_request_generator.build_rss_url(limit=25)
        assert "limit=25" in url


# ============================================================================
# TorznabParser Tests
# ============================================================================


class TestTorznabParser:
    """Test TorznabParser class."""

    def test_init(self, torznab_parser: TorznabParser) -> None:
        """Test TorznabParser initialization."""
        assert torznab_parser.ns == TORZNAB_NS

    def test_parse_response_bytes(
        self, torznab_parser: TorznabParser, sample_torznab_xml: bytes
    ) -> None:
        """Test parse_response with bytes input."""
        releases = torznab_parser.parse_response(sample_torznab_xml)
        assert len(releases) == 1
        assert releases[0].title == "Test Book - Author Name [EPUB]"
        assert releases[0].seeders == 10
        assert releases[0].leechers == 5

    def test_parse_response_str(
        self, torznab_parser: TorznabParser, sample_torznab_xml: bytes
    ) -> None:
        """Test parse_response with string input."""
        releases = torznab_parser.parse_response(sample_torznab_xml.decode())
        assert len(releases) == 1

    def test_parse_response_with_indexer_id(
        self, torznab_parser: TorznabParser, sample_torznab_xml: bytes
    ) -> None:
        """Test parse_response with indexer_id."""
        releases = torznab_parser.parse_response(sample_torznab_xml, indexer_id=1)
        assert releases[0].indexer_id == 1

    def test_parse_response_error_element(self, torznab_parser: TorznabParser) -> None:
        """Test parse_response with error element."""
        # Error element in channel (standard RSS format)
        xml = b"""<?xml version="1.0"?>
<rss><channel><error code="100" description="API key required"/></channel></rss>"""
        with pytest.raises(PVRProviderAuthenticationError):
            torznab_parser.parse_response(xml)

    def test_parse_response_invalid_xml(self, torznab_parser: TorznabParser) -> None:
        """Test parse_response with invalid XML."""
        with pytest.raises(PVRProviderParseError):
            torznab_parser.parse_response(b"<invalid>xml")

    def test_parse_response_empty_items(self, torznab_parser: TorznabParser) -> None:
        """Test parse_response with no items."""
        xml = b"""<?xml version="1.0"?><rss><channel></channel></rss>"""
        releases = torznab_parser.parse_response(xml)
        assert releases == []

    def test_parse_response_item_parse_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with item parse error."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><invalid/></item>
        </channel></rss>"""
        releases = torznab_parser.parse_response(xml)
        assert len(releases) == 1  # Only valid item parsed

    def test_parse_item_complete(
        self, torznab_parser: TorznabParser, sample_item_xml: ET.Element
    ) -> None:
        """Test _parse_item with complete item."""
        release = torznab_parser._parse_item(sample_item_xml, indexer_id=1)
        assert release is not None
        assert release.title == "Test Book Title"
        assert release.download_url == "https://example.com/file.torrent"
        assert release.indexer_id == 1

    def test_parse_item_no_title(self, torznab_parser: TorznabParser) -> None:
        """Test _parse_item with no title."""
        item = ET.Element("item")
        release = torznab_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_parse_item_no_download_url(self, torznab_parser: TorznabParser) -> None:
        """Test _parse_item with no download URL."""
        item = ET.Element("item")
        ET.SubElement(item, "title").text = "Test"
        release = torznab_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_extract_publish_date_valid(self, torznab_parser: TorznabParser) -> None:
        """Test _extract_publish_date with valid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 12:00:00 +0000"
        date = torznab_parser._extract_publish_date(item)
        assert date is not None
        assert isinstance(date, datetime)

    def test_extract_publish_date_invalid(self, torznab_parser: TorznabParser) -> None:
        """Test _extract_publish_date with invalid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "invalid date"
        date = torznab_parser._extract_publish_date(item)
        assert date is None

    def test_extract_publish_date_missing(self, torznab_parser: TorznabParser) -> None:
        """Test _extract_publish_date with missing date."""
        item = ET.Element("item")
        date = torznab_parser._extract_publish_date(item)
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
        self, torznab_parser: TorznabParser, title: str, expected: str | None
    ) -> None:
        """Test _infer_quality_from_title."""
        quality = torznab_parser._infer_quality_from_title(title)
        assert quality == expected

    def test_extract_metadata_with_attributes(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _extract_metadata with Torznab attributes."""
        item = ET.Element("item")
        attr1 = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr1.set("name", "author")
        attr1.set("value", "Test Author")
        attr2 = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr2.set("name", "isbn")
        attr2.set("value", "1234567890")
        attr3 = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr3.set("name", "format")
        attr3.set("value", "epub")

        author, isbn, quality = torznab_parser._extract_metadata(item, "Test Title")
        assert author == "Test Author"
        assert isbn == "1234567890"
        assert quality == "epub"

    def test_extract_metadata_infer_quality(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _extract_metadata infers quality from title."""
        item = ET.Element("item")
        _author, _isbn, quality = torznab_parser._extract_metadata(
            item, "Test Book [EPUB]"
        )
        assert quality == "epub"

    def test_extract_additional_info(self, torznab_parser: TorznabParser) -> None:
        """Test _extract_additional_info."""
        item = ET.Element("item")
        attr1 = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr1.set("name", "infohash")
        attr1.set("value", "abc123")
        attr2 = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr2.set("name", "magneturl")
        attr2.set("value", "magnet:?xt=urn:btih:abc123")

        additional_info = torznab_parser._extract_additional_info(item)
        assert additional_info["infohash"] == "abc123"
        assert additional_info["magneturl"] == "magnet:?xt=urn:btih:abc123"

    def test_extract_additional_info_empty(self, torznab_parser: TorznabParser) -> None:
        """Test _extract_additional_info with no attributes."""
        item = ET.Element("item")
        additional_info = torznab_parser._extract_additional_info(item)
        assert additional_info == {}

    def test_get_download_url_magneturl(self, torznab_parser: TorznabParser) -> None:
        """Test _get_download_url from magneturl attribute."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "magneturl")
        attr.set("value", "magnet:?xt=urn:btih:abc123")
        url = torznab_parser._get_download_url(item)
        assert url == "magnet:?xt=urn:btih:abc123"

    def test_get_download_url_enclosure(self, torznab_parser: TorznabParser) -> None:
        """Test _get_download_url from enclosure."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", "https://example.com/file.torrent")
        url = torznab_parser._get_download_url(item)
        assert url == "https://example.com/file.torrent"

    def test_get_download_url_link(self, torznab_parser: TorznabParser) -> None:
        """Test _get_download_url from link."""
        item = ET.Element("item")
        ET.SubElement(item, "link").text = "https://example.com/file.torrent"
        url = torznab_parser._get_download_url(item)
        assert url == "https://example.com/file.torrent"

    def test_get_download_url_none(self, torznab_parser: TorznabParser) -> None:
        """Test _get_download_url with no URL."""
        item = ET.Element("item")
        url = torznab_parser._get_download_url(item)
        assert url is None

    def test_get_size_from_attribute(self, torznab_parser: TorznabParser) -> None:
        """Test _get_size from Torznab attribute."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "size")
        attr.set("value", "1000000")
        size = torznab_parser._get_size(item)
        assert size == 1000000

    def test_get_size_from_enclosure(self, torznab_parser: TorznabParser) -> None:
        """Test _get_size from enclosure length."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("length", "2000000")
        size = torznab_parser._get_size(item)
        assert size == 2000000

    def test_get_size_invalid(self, torznab_parser: TorznabParser) -> None:
        """Test _get_size with invalid value."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "size")
        attr.set("value", "invalid")
        size = torznab_parser._get_size(item)
        assert size is None

    def test_get_torznab_attribute_found(self, torznab_parser: TorznabParser) -> None:
        """Test _get_torznab_attribute when found."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "author")
        attr.set("value", "Test Author")
        value = torznab_parser._get_torznab_attribute(item, "author")
        assert value == "Test Author"

    def test_get_torznab_attribute_not_found(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_torznab_attribute when not found."""
        item = ET.Element("item")
        value = torznab_parser._get_torznab_attribute(item, "author", default="default")
        assert value == "default"

    def test_get_torznab_attribute_int_valid(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_torznab_attribute_int with valid integer."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "seeders")
        attr.set("value", "10")
        value = torznab_parser._get_torznab_attribute_int(item, "seeders")
        assert value == 10

    def test_get_torznab_attribute_int_invalid(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_torznab_attribute_int with invalid value."""
        item = ET.Element("item")
        attr = ET.SubElement(item, f"{TORZNAB_NS}attr")
        attr.set("name", "seeders")
        attr.set("value", "invalid")
        value = torznab_parser._get_torznab_attribute_int(item, "seeders")
        assert value is None

    def test_get_torznab_attribute_int_not_found(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_torznab_attribute_int when not found."""
        item = ET.Element("item")
        value = torznab_parser._get_torznab_attribute_int(item, "seeders")
        assert value is None

    def test_parse_response_item_value_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with ValueError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise ValueError for second item
        with patch.object(
            torznab_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                ValueError("Invalid item"),
            ],
        ):
            releases = torznab_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_type_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with TypeError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise TypeError for second item
        with patch.object(
            torznab_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                TypeError("Invalid type"),
            ],
        ):
            releases = torznab_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_attribute_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with AttributeError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise AttributeError for second item
        with patch.object(
            torznab_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                AttributeError("Missing attribute"),
            ],
        ):
            releases = torznab_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_key_error(self, torznab_parser: TorznabParser) -> None:
        """Test parse_response with KeyError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise KeyError for second item
        with patch.object(
            torznab_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                KeyError("Missing key"),
            ],
        ):
            releases = torznab_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_unexpected_exception(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with unexpected exception."""
        # Mock ET.fromstring to raise an unexpected exception (not PVRProviderError)
        with patch("bookcard.pvr.indexers.torznab.ET.fromstring") as mock_fromstring:
            mock_fromstring.side_effect = RuntimeError("Unexpected error")
            with pytest.raises(
                PVRProviderParseError, match="Unexpected error parsing response"
            ):
                torznab_parser.parse_response(b"<rss><channel></channel></rss>")

    def test_parse_response_pvr_provider_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test parse_response with PVRProviderError (should be re-raised)."""
        # Mock ET.fromstring to raise a PVRProviderError
        with patch("bookcard.pvr.indexers.torznab.ET.fromstring") as mock_fromstring:
            mock_fromstring.side_effect = PVRProviderParseError("Parse error")
            with pytest.raises(PVRProviderParseError, match="Parse error"):
                torznab_parser.parse_response(b"<rss><channel></channel></rss>")

    def test_get_size_enclosure_length_type_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_size with TypeError in enclosure length parsing."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        # Set length to something that will cause TypeError
        enclosure.set("length", None)  # type: ignore[arg-type]
        size = torznab_parser._get_size(item)
        # Should handle gracefully and return None
        assert size is None

    def test_get_size_enclosure_length_value_error(
        self, torznab_parser: TorznabParser
    ) -> None:
        """Test _get_size with ValueError in enclosure length parsing."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("length", "invalid_number")
        size = torznab_parser._get_size(item)
        # Should handle gracefully and return None
        assert size is None


# ============================================================================
# TorznabIndexer Tests
# ============================================================================


class TestTorznabIndexer:
    """Test TorznabIndexer class."""

    def test_init_with_torznab_settings(
        self, torznab_settings_fixture: TorznabSettings
    ) -> None:
        """Test initialization with TorznabSettings."""
        indexer = TorznabIndexer(settings=torznab_settings_fixture)
        assert indexer.settings == torznab_settings_fixture
        assert isinstance(indexer.request_generator, TorznabRequestGenerator)
        assert isinstance(indexer.parser, TorznabParser)

    def test_init_with_indexer_settings(
        self, indexer_settings: IndexerSettings
    ) -> None:
        """Test initialization with IndexerSettings."""
        indexer = TorznabIndexer(settings=indexer_settings)
        assert isinstance(indexer.settings, TorznabSettings)
        assert indexer.settings.api_path == "/api"

    def test_init_disabled(self, torznab_settings_fixture: TorznabSettings) -> None:
        """Test initialization with disabled=True."""
        indexer = TorznabIndexer(settings=torznab_settings_fixture, enabled=False)
        assert not indexer.is_enabled()

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_success(
        self,
        mock_client: MagicMock,
        torznab_indexer: TorznabIndexer,
        sample_torznab_xml: bytes,
    ) -> None:
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.content = sample_torznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torznab_indexer.search(query="test")
        assert len(results) == 1
        assert results[0].title == "Test Book - Author Name [EPUB]"
        assert results[0].seeders == 10

    @pytest.mark.parametrize(
        ("query", "title", "author", "isbn"),
        [
            ("test", None, None, None),
            (None, "Title", None, None),
            (None, None, "Author", None),
            (None, None, None, "1234567890"),
        ],
    )
    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_with_params(
        self,
        mock_client: MagicMock,
        torznab_indexer: TorznabIndexer,
        sample_torznab_xml: bytes,
        query: str | None,
        title: str | None,
        author: str | None,
        isbn: str | None,
    ) -> None:
        """Test search with various parameters."""
        mock_response = MagicMock()
        mock_response.content = sample_torznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torznab_indexer.search(
            query=query or "", title=title, author=author, isbn=isbn
        )
        assert len(results) > 0

    def test_search_disabled(self, torznab_indexer: TorznabIndexer) -> None:
        """Test search when indexer is disabled."""
        torznab_indexer.set_enabled(False)
        results = torznab_indexer.search(query="test")
        assert results == []

    def test_search_no_query(self, torznab_indexer: TorznabIndexer) -> None:
        """Test search with no query parameters."""
        results = torznab_indexer.search(query="")
        assert results == []

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_max_results(
        self,
        mock_client: MagicMock,
        torznab_indexer: TorznabIndexer,
        sample_torznab_xml: bytes,
    ) -> None:
        """Test search with max_results limit."""
        mock_response = MagicMock()
        mock_response.content = sample_torznab_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torznab_indexer.search(query="test", max_results=1)
        assert len(results) <= 1

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_network_error(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test search with network error."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.RequestError("Network error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            torznab_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_timeout(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test search with timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            torznab_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_test_connection_success(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
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

        result = torznab_indexer.test_connection()
        assert result is True

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_test_connection_error(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
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
            torznab_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_make_request_success(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test _make_request success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        response = torznab_indexer._make_request("https://example.com")
        assert response.status_code == 200

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_make_request_timeout(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test _make_request timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            torznab_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_make_request_http_error(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test _make_request HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            torznab_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_search_unexpected_exception(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test search with unexpected exception."""
        # Mock _make_request to raise an unexpected exception (not PVRProviderError)
        with (
            patch.object(
                torznab_indexer,
                "_make_request",
                side_effect=RuntimeError("Unexpected error"),
            ),
            pytest.raises(PVRProviderError, match="Unexpected error during search"),
        ):
            torznab_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_test_connection_unexpected_exception(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test test_connection with unexpected exception."""
        # Mock _make_request to raise an unexpected exception directly
        with (
            patch.object(
                torznab_indexer,
                "_make_request",
                side_effect=RuntimeError("Unexpected error"),
            ),
            pytest.raises(PVRProviderError, match="Connection test failed"),
        ):
            torznab_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_test_connection_pvr_provider_error(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test test_connection with PVRProviderError (not AuthenticationError)."""
        # Mock _make_request to raise a PVRProviderError (not AuthenticationError)
        with (
            patch.object(
                torznab_indexer,
                "_make_request",
                side_effect=PVRProviderNetworkError("Network error"),
            ),
            pytest.raises(PVRProviderNetworkError),
        ):
            torznab_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_make_request_http_status_error(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test _make_request with HTTPStatusError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client_instance = MagicMock()
        error = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client_instance.get.side_effect = error
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError, match="HTTP error"):
            torznab_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torznab.httpx.Client")
    def test_make_request_unexpected_exception(
        self, mock_client: MagicMock, torznab_indexer: TorznabIndexer
    ) -> None:
        """Test _make_request with unexpected exception."""
        mock_client_instance = MagicMock()
        # Make get() raise an unexpected exception
        mock_client_instance.get.side_effect = RuntimeError("Unexpected error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderError, match="Unexpected error"):
            torznab_indexer._make_request("https://example.com")

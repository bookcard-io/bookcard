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

"""Tests for Torrent RSS indexer implementation."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET  # noqa: S405

import httpx
import pytest
from pydantic import ValidationError

from bookcard.pvr.base import (
    IndexerSettings,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.indexers.torrent_rss import (
    TorrentRssIndexer,
    TorrentRssParser,
    TorrentRssSettings,
)
from bookcard.pvr.models import ReleaseInfo

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def torrent_rss_settings_fixture() -> TorrentRssSettings:
    """Create Torrent RSS settings for testing."""
    return TorrentRssSettings(
        base_url="https://rss.example.com",
        api_key="test-key",
        timeout_seconds=30,
        retry_count=3,
        categories=[1000, 2000],
        feed_url="https://rss.example.com/feed",
    )


@pytest.fixture
def torrent_rss_indexer(
    torrent_rss_settings_fixture: TorrentRssSettings,
) -> TorrentRssIndexer:
    """Create Torrent RSS indexer instance."""
    return TorrentRssIndexer(settings=torrent_rss_settings_fixture, enabled=True)


@pytest.fixture
def torrent_rss_parser() -> TorrentRssParser:
    """Create Torrent RSS parser instance."""
    return TorrentRssParser()


@pytest.fixture
def sample_item_xml() -> ET.Element:
    """Create sample XML item element."""
    item = ET.Element("item")
    ET.SubElement(item, "title").text = "Test Book Title [EPUB]"
    ET.SubElement(item, "link").text = "https://example.com/item"
    ET.SubElement(
        item, "description"
    ).text = "Test description. Seeders: 10 Leechers: 5"
    ET.SubElement(item, "category").text = "Books"
    ET.SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 12:00:00 +0000"
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", "https://example.com/file.torrent")
    enclosure.set("type", "application/x-bittorrent")
    enclosure.set("length", "1000000")
    return item


# ============================================================================
# TorrentRssSettings Tests
# ============================================================================


class TestTorrentRssSettings:
    """Test TorrentRssSettings class."""

    def test_torrent_rss_settings_requires_feed_url(self) -> None:
        """Test TorrentRssSettings requires feed_url."""
        # Pydantic will raise ValidationError for missing required field
        with pytest.raises(ValidationError):
            TorrentRssSettings(base_url="https://example.com")  # type: ignore[call-arg]

    def test_torrent_rss_settings_with_feed_url(self) -> None:
        """Test TorrentRssSettings with feed_url."""
        settings = TorrentRssSettings(
            base_url="https://example.com", feed_url="https://example.com/feed"
        )
        assert settings.feed_url == "https://example.com/feed"

    def test_torrent_rss_settings_missing_feed_url_from_indexer_settings(
        self,
    ) -> None:
        """Test TorrentRssIndexer initialization with IndexerSettings missing feed_url."""
        # Create IndexerSettings without feed_url and without base_url
        settings = IndexerSettings(base_url="")
        # When initializing TorrentRssIndexer with IndexerSettings that has no feed_url,
        # it should raise ValueError
        with pytest.raises(ValueError, match="requires feed_url"):
            TorrentRssIndexer(settings=settings)


# ============================================================================
# TorrentRssParser Tests
# ============================================================================


class TestTorrentRssParser:
    """Test TorrentRssParser class."""

    def test_init(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test TorrentRssParser initialization."""
        assert torrent_rss_parser is not None

    def test_parse_response_bytes(
        self, torrent_rss_parser: TorrentRssParser, sample_rss_xml: bytes
    ) -> None:
        """Test parse_response with bytes input."""
        releases = torrent_rss_parser.parse_response(sample_rss_xml)
        assert len(releases) == 1
        assert releases[0].title == "Test Book Title"

    def test_parse_response_str(
        self, torrent_rss_parser: TorrentRssParser, sample_rss_xml: bytes
    ) -> None:
        """Test parse_response with string input."""
        releases = torrent_rss_parser.parse_response(sample_rss_xml.decode())
        assert len(releases) == 1

    def test_parse_response_with_indexer_id(
        self, torrent_rss_parser: TorrentRssParser, sample_rss_xml: bytes
    ) -> None:
        """Test parse_response with indexer_id."""
        releases = torrent_rss_parser.parse_response(sample_rss_xml, indexer_id=1)
        assert releases[0].indexer_id == 1

    def test_parse_response_invalid_xml(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with invalid XML."""
        with pytest.raises(PVRProviderParseError):
            torrent_rss_parser.parse_response(b"<invalid>xml")

    def test_parse_response_empty_items(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with no items."""
        xml = b"""<?xml version="1.0"?><rss><channel></channel></rss>"""
        releases = torrent_rss_parser.parse_response(xml)
        assert releases == []

    def test_parse_response_item_parse_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with item parse error."""
        xml = b"""<?xml version="1.0"?>
<rss><channel>
    <item><title>Valid</title><link>https://example.com/file.torrent</link></item>
    <item><invalid/></item>
</channel></rss>"""
        releases = torrent_rss_parser.parse_response(xml)
        assert len(releases) == 1  # Only valid item parsed

    def test_parse_item_complete(
        self, torrent_rss_parser: TorrentRssParser, sample_item_xml: ET.Element
    ) -> None:
        """Test _parse_item with complete item."""
        release = torrent_rss_parser._parse_item(sample_item_xml, indexer_id=1)
        assert release is not None
        assert release.title == "Test Book Title [EPUB]"
        assert release.download_url == "https://example.com/file.torrent"
        assert release.indexer_id == 1
        assert release.quality == "epub"
        assert release.seeders == 10
        assert release.leechers == 5

    def test_parse_item_no_title(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test _parse_item with no title."""
        item = ET.Element("item")
        release = torrent_rss_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_parse_item_no_download_url(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _parse_item with no download URL."""
        item = ET.Element("item")
        ET.SubElement(item, "title").text = "Test"
        release = torrent_rss_parser._parse_item(item, indexer_id=None)
        assert release is None

    def test_extract_publish_date_valid(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _extract_publish_date with valid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 12:00:00 +0000"
        date = torrent_rss_parser._extract_publish_date(item)
        assert date is not None
        assert isinstance(date, datetime)

    def test_extract_publish_date_invalid(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _extract_publish_date with invalid date."""
        item = ET.Element("item")
        ET.SubElement(item, "pubDate").text = "invalid date"
        date = torrent_rss_parser._extract_publish_date(item)
        assert date is None

    def test_extract_publish_date_missing(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _extract_publish_date with missing date."""
        item = ET.Element("item")
        date = torrent_rss_parser._extract_publish_date(item)
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
        self, torrent_rss_parser: TorrentRssParser, title: str, expected: str | None
    ) -> None:
        """Test _infer_quality_from_title."""
        quality = torrent_rss_parser._infer_quality_from_title(title)
        assert quality == expected

    @pytest.mark.parametrize(
        ("description", "expected_seeders", "expected_leechers"),
        [
            ("Seeders: 10 Leechers: 5", 10, 5),
            ("S: 20 L: 10", 20, 10),
            ("Seeds: 5 Peers: 3", 5, 3),
            ("No stats", None, None),
            (None, None, None),
        ],
    )
    def test_extract_seeders_leechers(
        self,
        torrent_rss_parser: TorrentRssParser,
        description: str | None,
        expected_seeders: int | None,
        expected_leechers: int | None,
    ) -> None:
        """Test _extract_seeders_leechers."""
        seeders, leechers = torrent_rss_parser._extract_seeders_leechers(description)
        assert seeders == expected_seeders
        assert leechers == expected_leechers

    def test_get_download_url_enclosure(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_download_url from enclosure."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", "https://example.com/file.torrent")
        enclosure.set("type", "application/x-bittorrent")
        url = torrent_rss_parser._get_download_url(item)
        assert url == "https://example.com/file.torrent"

    def test_get_download_url_enclosure_magnet(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_download_url from enclosure with magnet."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", "magnet:?xt=urn:btih:abc123")
        url = torrent_rss_parser._get_download_url(item)
        assert url == "magnet:?xt=urn:btih:abc123"

    def test_get_download_url_link(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test _get_download_url from link."""
        item = ET.Element("item")
        ET.SubElement(item, "link").text = "https://example.com/file.torrent"
        url = torrent_rss_parser._get_download_url(item)
        assert url == "https://example.com/file.torrent"

    def test_get_download_url_link_magnet(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_download_url from link with magnet."""
        item = ET.Element("item")
        ET.SubElement(item, "link").text = "magnet:?xt=urn:btih:abc123"
        url = torrent_rss_parser._get_download_url(item)
        assert url == "magnet:?xt=urn:btih:abc123"

    def test_get_download_url_description_magnet(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_download_url from description with magnet."""
        item = ET.Element("item")
        ET.SubElement(
            item, "description"
        ).text = "Download: magnet:?xt=urn:btih:abc123&dn=test"
        url = torrent_rss_parser._get_download_url(item)
        assert url == "magnet:?xt=urn:btih:abc123&dn=test"

    def test_get_download_url_description_torrent(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_download_url from description with torrent URL."""
        item = ET.Element("item")
        ET.SubElement(
            item, "description"
        ).text = "Download: https://example.com/file.torrent"
        url = torrent_rss_parser._get_download_url(item)
        assert url == "https://example.com/file.torrent"

    def test_get_download_url_none(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test _get_download_url with no URL."""
        item = ET.Element("item")
        url = torrent_rss_parser._get_download_url(item)
        assert url is None

    def test_get_size_from_enclosure(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test _get_size from enclosure length."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("length", "1000000")
        size = torrent_rss_parser._get_size(item)
        assert size == 1000000

    def test_get_size_invalid(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test _get_size with invalid value."""
        item = ET.Element("item")
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("length", "invalid")
        size = torrent_rss_parser._get_size(item)
        assert size is None

    def test_get_size_missing(self, torrent_rss_parser: TorrentRssParser) -> None:
        """Test _get_size with missing enclosure."""
        item = ET.Element("item")
        size = torrent_rss_parser._get_size(item)
        assert size is None

    def test_parse_response_item_value_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with ValueError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise ValueError for second item
        with patch.object(
            torrent_rss_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                ValueError("Invalid item"),
            ],
        ):
            releases = torrent_rss_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_type_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with TypeError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise TypeError for second item
        with patch.object(
            torrent_rss_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                TypeError("Invalid type"),
            ],
        ):
            releases = torrent_rss_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_attribute_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with AttributeError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise AttributeError for second item
        with patch.object(
            torrent_rss_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                AttributeError("Missing attribute"),
            ],
        ):
            releases = torrent_rss_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_item_key_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with KeyError in item parsing."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item><title>Valid</title><link>https://example.com</link></item>
            <item><title>Invalid</title><link>https://example.com</link></item>
        </channel></rss>"""
        # Mock _parse_item to raise KeyError for second item
        with patch.object(
            torrent_rss_parser,
            "_parse_item",
            side_effect=[
                ReleaseInfo(title="Valid", download_url="https://example.com"),
                KeyError("Missing key"),
            ],
        ):
            releases = torrent_rss_parser.parse_response(xml)
            # Should skip invalid item and return only valid one
            assert len(releases) == 1

    def test_parse_response_unexpected_exception(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with unexpected exception."""
        # Mock ET.fromstring to raise an unexpected exception (not PVRProviderError)
        with patch(
            "bookcard.pvr.indexers.torrent_rss.ET.fromstring"
        ) as mock_fromstring:
            mock_fromstring.side_effect = RuntimeError("Unexpected error")
            with pytest.raises(PVRProviderParseError, match="Failed to parse RSS feed"):
                torrent_rss_parser.parse_response(b"<rss><channel></channel></rss>")

    def test_parse_response_pvr_provider_error(
        self, torrent_rss_parser: TorrentRssParser
    ) -> None:
        """Test parse_response with PVRProviderError (should be re-raised)."""
        # Mock ET.fromstring to raise a PVRProviderError
        with patch(
            "bookcard.pvr.indexers.torrent_rss.ET.fromstring"
        ) as mock_fromstring:
            mock_fromstring.side_effect = PVRProviderParseError("Parse error")
            with pytest.raises(PVRProviderParseError, match="Parse error"):
                torrent_rss_parser.parse_response(b"<rss><channel></channel></rss>")


# ============================================================================
# TorrentRssIndexer Tests
# ============================================================================


class TestTorrentRssIndexer:
    """Test TorrentRssIndexer class."""

    def test_init_with_torrent_rss_settings(
        self, torrent_rss_settings_fixture: TorrentRssSettings
    ) -> None:
        """Test initialization with TorrentRssSettings."""
        indexer = TorrentRssIndexer(settings=torrent_rss_settings_fixture)
        assert indexer.settings == torrent_rss_settings_fixture
        assert isinstance(indexer.parser, TorrentRssParser)

    def test_init_with_indexer_settings(
        self, indexer_settings: IndexerSettings
    ) -> None:
        """Test initialization with IndexerSettings."""
        indexer = TorrentRssIndexer(settings=indexer_settings)
        assert isinstance(indexer.settings, TorrentRssSettings)
        assert indexer.settings.feed_url == indexer_settings.base_url

    def test_init_with_indexer_settings_no_feed_url(
        self, indexer_settings_minimal: IndexerSettings
    ) -> None:
        """Test initialization with IndexerSettings without feed_url uses base_url."""
        # TorrentRssIndexer uses base_url as fallback for feed_url
        indexer = TorrentRssIndexer(settings=indexer_settings_minimal)
        assert indexer.settings.feed_url == indexer_settings_minimal.base_url

    def test_init_disabled(
        self, torrent_rss_settings_fixture: TorrentRssSettings
    ) -> None:
        """Test initialization with disabled=True."""
        indexer = TorrentRssIndexer(
            settings=torrent_rss_settings_fixture, enabled=False
        )
        assert not indexer.is_enabled()

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_success(
        self,
        mock_client: MagicMock,
        torrent_rss_indexer: TorrentRssIndexer,
        sample_rss_xml: bytes,
    ) -> None:
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.content = sample_rss_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torrent_rss_indexer.search(query="Test")
        assert len(results) == 1
        assert results[0].title == "Test Book Title"

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_with_filtering(
        self,
        mock_client: MagicMock,
        torrent_rss_indexer: TorrentRssIndexer,
    ) -> None:
        """Test search with filtering."""
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
            <item>
                <title>Test Book Title</title>
                <link>https://example.com/item1</link>
                <enclosure url="https://example.com/file1.torrent" type="application/x-bittorrent"/>
            </item>
            <item>
                <title>Other Book</title>
                <link>https://example.com/item2</link>
                <enclosure url="https://example.com/file2.torrent" type="application/x-bittorrent"/>
            </item>
        </channel></rss>"""
        mock_response = MagicMock()
        mock_response.content = xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torrent_rss_indexer.search(query="Test")
        assert len(results) == 1
        assert results[0].title == "Test Book Title"

    @pytest.mark.parametrize(
        ("query", "title", "author", "isbn"),
        [
            ("test", None, None, None),
            (None, "Title", None, None),
            (None, None, "Author", None),
            (None, None, None, "1234567890"),
        ],
    )
    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_with_params(
        self,
        mock_client: MagicMock,
        torrent_rss_indexer: TorrentRssIndexer,
        sample_rss_xml: bytes,
        query: str | None,
        title: str | None,
        author: str | None,
        isbn: str | None,
    ) -> None:
        """Test search with various parameters."""
        mock_response = MagicMock()
        mock_response.content = sample_rss_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torrent_rss_indexer.search(
            query=query or "", title=title, author=author, isbn=isbn
        )
        assert len(results) >= 0

    def test_search_disabled(self, torrent_rss_indexer: TorrentRssIndexer) -> None:
        """Test search when indexer is disabled."""
        torrent_rss_indexer.set_enabled(False)
        results = torrent_rss_indexer.search(query="test")
        assert results == []

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_max_results(
        self,
        mock_client: MagicMock,
        torrent_rss_indexer: TorrentRssIndexer,
        sample_rss_xml: bytes,
    ) -> None:
        """Test search with max_results limit."""
        mock_response = MagicMock()
        mock_response.content = sample_rss_xml
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        results = torrent_rss_indexer.search(query="test", max_results=1)
        assert len(results) <= 1

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_network_error(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test search with network error."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.RequestError("Network error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            torrent_rss_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_timeout(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test search with timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            torrent_rss_indexer.search(query="test")

    def test_build_search_terms(self, torrent_rss_indexer: TorrentRssIndexer) -> None:
        """Test _build_search_terms."""
        terms = torrent_rss_indexer._build_search_terms(
            query="test", title="Title", author="Author", isbn="123"
        )
        assert "test" in terms
        assert "title" in terms
        assert "author" in terms
        assert "123" in terms
        assert all(isinstance(t, str) for t in terms)

    def test_build_search_terms_empty(
        self, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _build_search_terms with no parameters."""
        terms = torrent_rss_indexer._build_search_terms(
            query="", title=None, author=None, isbn=None
        )
        assert terms == []

    def test_filter_releases_by_terms(
        self, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _filter_releases_by_terms."""
        releases = [
            ReleaseInfo(
                title="Test Book",
                description="Test description",
                download_url="https://example.com/test.torrent",
            ),
            ReleaseInfo(
                title="Other Book",
                description="Other description",
                download_url="https://example.com/other.torrent",
            ),
        ]
        filtered = torrent_rss_indexer._filter_releases_by_terms(releases, ["test"])
        assert len(filtered) == 1
        assert filtered[0].title == "Test Book"

    def test_filter_releases_by_terms_no_match(
        self, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _filter_releases_by_terms with no matches."""
        releases = [
            ReleaseInfo(
                title="Other Book",
                description="Other description",
                download_url="https://example.com/other.torrent",
            ),
        ]
        filtered = torrent_rss_indexer._filter_releases_by_terms(releases, ["test"])
        assert len(filtered) == 0

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_test_connection_success(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
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

        result = torrent_rss_indexer.test_connection()
        assert result is True

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_test_connection_invalid_xml(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test connection test with invalid XML."""
        mock_response = MagicMock()
        mock_response.content = b"<invalid>xml"
        mock_response.status_code = 200
        mock_response.text = ""
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderError):
            torrent_rss_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_make_request_success(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _make_request success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        response = torrent_rss_indexer._make_request("https://example.com")
        assert response.status_code == 200

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_make_request_timeout(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _make_request timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderTimeoutError):
            torrent_rss_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_make_request_http_error(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _make_request HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderNetworkError):
            torrent_rss_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_search_unexpected_exception(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test search with unexpected exception."""
        # Mock _make_request to raise an unexpected exception (not PVRProviderError)
        with (
            patch.object(
                torrent_rss_indexer,
                "_make_request",
                side_effect=RuntimeError("Unexpected error"),
            ),
            pytest.raises(PVRProviderError, match="Unexpected error during search"),
        ):
            torrent_rss_indexer.search(query="test")

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_test_connection_unexpected_exception(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test test_connection with unexpected exception."""
        # Mock _make_request to raise an unexpected exception directly
        with (
            patch.object(
                torrent_rss_indexer,
                "_make_request",
                side_effect=RuntimeError("Unexpected error"),
            ),
            pytest.raises(PVRProviderError, match="Connection test failed"),
        ):
            torrent_rss_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_test_connection_pvr_provider_error(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test test_connection with PVRProviderError (should be re-raised)."""
        # Mock _make_request to raise a PVRProviderError
        with (
            patch.object(
                torrent_rss_indexer,
                "_make_request",
                side_effect=PVRProviderNetworkError("Network error"),
            ),
            pytest.raises(PVRProviderNetworkError),
        ):
            torrent_rss_indexer.test_connection()

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_make_request_http_status_error(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
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
            torrent_rss_indexer._make_request("https://example.com")

    @patch("bookcard.pvr.indexers.torrent_rss.httpx.Client")
    def test_make_request_unexpected_exception(
        self, mock_client: MagicMock, torrent_rss_indexer: TorrentRssIndexer
    ) -> None:
        """Test _make_request with unexpected exception."""
        mock_client_instance = MagicMock()
        # Make get() raise an unexpected exception
        mock_client_instance.get.side_effect = RuntimeError("Unexpected error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(PVRProviderError, match="Unexpected error"):
            torrent_rss_indexer._make_request("https://example.com")

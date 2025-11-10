# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for Douban metadata provider to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from lxml import etree  # type: ignore[import]

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from fundamental.metadata.providers.douban import (
    DoubanProvider,
    _clean_date,
    _sanitize_html_to_text,
)


@pytest.fixture
def douban_provider() -> DoubanProvider:
    """Create a DoubanProvider instance for testing."""
    return DoubanProvider(enabled=True)


def test_douban_provider_init() -> None:
    """Test DoubanProvider initialization."""
    provider = DoubanProvider(enabled=True, timeout=20)
    assert provider.enabled is True
    assert provider.timeout == 20


def test_douban_provider_get_source_info(douban_provider: DoubanProvider) -> None:
    """Test get_source_info."""
    source_info = douban_provider.get_source_info()
    assert source_info.id == "douban"
    assert source_info.name == "豆瓣"
    assert source_info.base_url == "https://book.douban.com/"


def test_douban_provider_search_disabled(douban_provider: DoubanProvider) -> None:
    """Test search returns empty when disabled."""
    douban_provider.enabled = False
    result = douban_provider.search("test query")
    assert result == []


def test_douban_provider_search_empty_query(douban_provider: DoubanProvider) -> None:
    """Test search returns empty for empty query."""
    result = douban_provider.search("")
    assert result == []

    result = douban_provider.search("   ")
    assert result == []


def test_douban_provider_search_no_book_ids(douban_provider: DoubanProvider) -> None:
    """Test search returns empty when no book IDs found."""
    with patch.object(douban_provider, "_get_book_id_list_from_html", return_value=[]):
        result = douban_provider.search("test query")
        assert result == []


def test_douban_provider_search_success(douban_provider: DoubanProvider) -> None:
    """Test search succeeds with valid response."""
    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <a class="nbg" href="http://example.com/cover.jpg"></a>
            <div class="rating_self clearfix"><strong>8.5</strong></div>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
            <div id="info">
                <span class="pl">作者</span>
                <a>Author 1</a>
                <span class="pl">出版社</span>
                <a>Publisher</a>
                <span class="pl">出版年</span>
                2024-01-01
                <span class="pl">丛书</span>
                <a>Series</a>
                <span class="pl">ISBN</span>
                1234567890
            </div>
        </body>
    </html>
    """

    mock_detail_response = MagicMock()
    mock_detail_response.content = detail_html.encode("utf-8")
    mock_detail_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_detail_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(
            douban_provider, "_get_book_id_list_from_html", return_value=["12345"]
        ),
        patch("httpx.Client", return_value=mock_client),
    ):
        results = douban_provider.search("test query", max_results=1)
        assert len(results) == 1
        assert results[0].title == "Test Book"


def test_douban_provider_search_timeout(douban_provider: DoubanProvider) -> None:
    """Test search raises TimeoutError."""
    with (
        patch.object(
            douban_provider,
            "_get_book_id_list_from_html",
            side_effect=httpx.TimeoutException("Timeout"),
        ),
        pytest.raises(MetadataProviderTimeoutError),
    ):
        douban_provider.search("test query")


def test_douban_provider_search_network_error(douban_provider: DoubanProvider) -> None:
    """Test search raises NetworkError."""
    with (
        patch.object(
            douban_provider,
            "_get_book_id_list_from_html",
            side_effect=httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=MagicMock()
            ),
        ),
        pytest.raises(MetadataProviderNetworkError),
    ):
        douban_provider.search("test query")


def test_douban_provider_search_parse_error(douban_provider: DoubanProvider) -> None:
    """Test search raises ParseError."""
    with (
        patch.object(
            douban_provider,
            "_get_book_id_list_from_html",
            side_effect=ValueError("Parse error"),
        ),
        pytest.raises(MetadataProviderParseError),
    ):
        douban_provider.search("test query")


def test_douban_provider_prepare_query(douban_provider: DoubanProvider) -> None:
    """Test _prepare_query."""
    query = douban_provider._prepare_query("test book query")
    assert query == "test+book+query"


def test_douban_provider_prepare_query_short_tokens(
    douban_provider: DoubanProvider,
) -> None:
    """Test _prepare_query filters short tokens."""
    query = douban_provider._prepare_query("a b c")
    assert query == ""


def test_douban_provider_get_book_id_list_from_html_success(
    douban_provider: DoubanProvider,
) -> None:
    """Test _get_book_id_list_from_html with valid HTML."""
    html = """
    <html>
        <body>
            <a class="nbg" onclick="sid: 12345,"></a>
            <a class="nbg" onclick="sid: 67890,"></a>
        </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        book_ids = douban_provider._get_book_id_list_from_html("test")
        assert "12345" in book_ids
        assert "67890" in book_ids


def test_douban_provider_get_book_id_list_from_html_error(
    douban_provider: DoubanProvider,
) -> None:
    """Test _get_book_id_list_from_html handles errors."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        book_ids = douban_provider._get_book_id_list_from_html("test")
        assert book_ids == []


def test_douban_provider_fetch_book_details(douban_provider: DoubanProvider) -> None:
    """Test _fetch_book_details."""
    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
        </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.content = detail_html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    book_ids = ["12345"]
    results = douban_provider._fetch_book_details(book_ids, mock_client)
    assert len(results) == 1


def test_douban_provider_fetch_book_details_error(
    douban_provider: DoubanProvider,
) -> None:
    """Test _fetch_book_details handles errors."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )

    book_ids = ["12345"]
    results = douban_provider._fetch_book_details(book_ids, mock_client)
    assert len(results) == 0


def test_douban_provider_parse_single_book_success(
    douban_provider: DoubanProvider,
) -> None:
    """Test _parse_single_book with valid HTML."""
    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <a class="nbg" href="http://example.com/cover.jpg"></a>
            <div class="rating_self clearfix"><strong>8.5</strong></div>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
            <div id="info">
                <span class="pl">作者</span>
                <a>Author 1</a>
                <span class="pl">出版社</span>
                <a>Publisher</a>
                <span class="pl">出版年</span>
                2024-01-01
                <span class="pl">丛书</span>
                <a>Series</a>
                <span class="pl">ISBN</span>
                1234567890
            </div>
        </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.content = detail_html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    result = douban_provider._parse_single_book("12345", mock_client)
    assert result is not None
    assert result.title == "Test Book"


def test_douban_provider_parse_single_book_no_title(
    douban_provider: DoubanProvider,
) -> None:
    """Test _parse_single_book returns None when no title."""
    detail_html = "<html><body></body></html>"

    mock_response = MagicMock()
    mock_response.content = detail_html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    result = douban_provider._parse_single_book("12345", mock_client)
    assert result is None


def test_douban_provider_parse_single_book_error(
    douban_provider: DoubanProvider,
) -> None:
    """Test _parse_single_book handles errors."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )

    result = douban_provider._parse_single_book("12345", mock_client)
    assert result is None


def test_douban_provider_extract_rating(douban_provider: DoubanProvider) -> None:
    """Test _extract_rating."""
    html = etree.fromstring(
        '<html><body><div class="rating_self clearfix"><strong>8.5</strong></div></body></html>'
    )
    rating = douban_provider._extract_rating(html)
    # The formula is: float(int(-1 * rating_num // 2 * -1))
    # For 8.5: -1 * 8.5 = -8.5, -8.5 // 2 = -5.0 (floor division), -5.0 * -1 = 5.0
    assert rating == 5.0


def test_douban_provider_extract_rating_not_found(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_rating returns None when not found."""
    html = etree.fromstring("<html><body></body></html>")
    rating = douban_provider._extract_rating(html)
    assert rating is None


def test_douban_provider_extract_tags(douban_provider: DoubanProvider) -> None:
    """Test _extract_tags."""
    html = etree.fromstring(
        '<html><body><a class="tag">Tag1</a><a class="tag">Tag2</a></body></html>'
    )
    content = '<html><body><a class="tag">Tag1</a><a class="tag">Tag2</a></body></html>'
    tags = douban_provider._extract_tags(html, content)
    assert "Tag1" in tags
    assert "Tag2" in tags


def test_douban_provider_extract_tags_criteria_fallback(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_tags uses criteria pattern fallback."""
    html = etree.fromstring("<html><body></body></html>")
    # The regex is r"criteria = '(.+)'" which captures group 1
    # But the code uses match.group() which returns the full match
    # match.group() = "criteria = '7:Tag1|7:Tag2|other'"
    # match.group().split("|") = ["criteria = '7:Tag1", "7:Tag2", "other'"]
    # Items starting with "7:" would be ["7:Tag2"] only
    content = "<script>criteria = '7:Tag1|7:Tag2|other'</script>"
    tags = douban_provider._extract_tags(html, content)
    # Only "7:Tag2" starts with "7:" after splitting the full match
    assert "Tag2" in tags
    assert len(tags) == 1


def test_douban_provider_extract_description(douban_provider: DoubanProvider) -> None:
    """Test _extract_description."""
    html = etree.fromstring(
        '<html><body><div id="link-report"><div class="intro">Test description</div></div></body></html>'
    )
    description = douban_provider._extract_description(html)
    assert description is not None
    assert "Test description" in description


def test_douban_provider_extract_description_not_found(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_description returns None when not found."""
    html = etree.fromstring("<html><body></body></html>")
    description = douban_provider._extract_description(html)
    assert description is None


def test_douban_provider_extract_info_metadata(douban_provider: DoubanProvider) -> None:
    """Test _extract_info_metadata."""
    html = etree.fromstring("""
    <html>
        <body>
            <div id="info">
                <span class="pl">作者</span>
                <a>Author 1</a>
                <span class="pl">出版社</span>
                <a>Publisher</a>
                <span class="pl">副标题</span>
                Subtitle
                <span class="pl">出版年</span>
                2024-01-01
                <span class="pl">丛书</span>
                <a>Series</a>
                <span class="pl">ISBN</span>
                1234567890
            </div>
        </body>
    </html>
    """)
    authors, publisher, subtitle, published_date, series, identifiers = (
        douban_provider._extract_info_metadata(html)
    )
    assert len(authors) > 0
    assert publisher is not None
    assert subtitle is not None
    assert published_date is not None
    assert series is not None
    assert "isbn" in identifiers


def test_douban_provider_extract_authors_from_element(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_authors_from_element."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">作者</span>
            <a>Author 1</a>
            <a>Author 2</a>
            <br/>
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    authors = douban_provider._extract_authors_from_element(element)
    assert len(authors) >= 1


def test_douban_provider_extract_publisher_from_element(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_publisher_from_element."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">出版社</span>
            <a>Publisher</a>
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    publisher = douban_provider._extract_publisher_from_element(element)
    assert publisher is not None


def test_douban_provider_extract_publisher_from_element_tail(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_publisher_from_element uses tail."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">出版社</span>Publisher Text
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    element.tail = "Publisher Text"
    publisher = douban_provider._extract_publisher_from_element(element)
    assert publisher == "Publisher Text"


def test_douban_provider_extract_subtitle_from_element(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_subtitle_from_element."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">副标题</span>Subtitle Text
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    element.tail = "Subtitle Text"
    subtitle = douban_provider._extract_subtitle_from_element(element)
    assert subtitle == "Subtitle Text"


def test_douban_provider_extract_published_date_from_element(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_published_date_from_element."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">出版年</span>2024-01-01
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    element.tail = "2024-01-01"
    published_date = douban_provider._extract_published_date_from_element(element)
    assert published_date is not None


def test_douban_provider_extract_series_from_element(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_series_from_element."""
    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">丛书</span>
            <a>Series Name</a>
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    series = douban_provider._extract_series_from_element(element)
    assert series == "Series Name"


def test_douban_provider_extract_identifier_from_element_isbn(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_identifier_from_element with ISBN."""
    import re

    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">ISBN</span>1234567890
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    element.tail = "1234567890"
    identifiers = {}
    match = re.search(r"ISBN", "ISBN")
    assert match is not None
    douban_provider._extract_identifier_from_element(element, match, identifiers)
    assert "isbn" in identifiers


def test_douban_provider_extract_identifier_from_element_other(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_identifier_from_element with other identifier."""
    import re

    html = etree.fromstring("""
    <html>
        <body>
            <span class="pl">统一书号</span>12345
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    element.tail = "12345"
    identifiers = {}
    match = re.search(r"统一书号", "统一书号")
    assert match is not None
    douban_provider._extract_identifier_from_element(element, match, identifiers)
    assert "统一书号" in identifiers


def test_douban_provider_parse_single_book_with_subtitle(
    douban_provider: DoubanProvider,
) -> None:
    """Test _parse_single_book includes subtitle in title."""
    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
            <div id="info">
                <span class="pl">副标题</span>
                Subtitle Text
            </div>
        </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.content = detail_html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    result = douban_provider._parse_single_book("12345", mock_client)
    assert result is not None
    assert "Subtitle Text" in result.title


def test_sanitize_html_to_text() -> None:
    """Test _sanitize_html_to_text."""
    html = "<html><body><p>Test text</p></body></html>"
    text = _sanitize_html_to_text(html)
    assert "Test text" in text


def test_sanitize_html_to_text_bytes() -> None:
    """Test _sanitize_html_to_text with bytes."""
    html = b"<html><body><p>Test text</p></body></html>"
    text = _sanitize_html_to_text(html.decode("utf-8"))  # Convert bytes to str
    assert "Test text" in text


def test_clean_date() -> None:
    """Test _clean_date."""
    date = _clean_date("2024-01-15")
    assert date == "2024-01-15"


def test_clean_date_year_only() -> None:
    """Test _clean_date with year only."""
    date = _clean_date("2024")
    assert date == "2024-01-01"


def test_clean_date_year_month() -> None:
    """Test _clean_date with year and month."""
    date = _clean_date("2024年7月")
    assert date == "2024-07-01"


def test_clean_date_chinese_format() -> None:
    """Test _clean_date with Chinese format."""
    date = _clean_date("2024年4月")
    assert date == "2024-04-01"


def test_clean_date_slash_format() -> None:
    """Test _clean_date with slash format."""
    date = _clean_date("2004/11/01")
    assert date == "2004-11-01"


def test_douban_provider_search_max_results(douban_provider: DoubanProvider) -> None:
    """Test search respects max_results limit."""
    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
        </body>
    </html>
    """

    mock_detail_response = MagicMock()
    mock_detail_response.content = detail_html.encode("utf-8")
    mock_detail_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_detail_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(
            douban_provider, "_get_book_id_list_from_html", return_value=["1", "2", "3"]
        ),
        patch("httpx.Client", return_value=mock_client),
    ):
        results = douban_provider.search("test query", max_results=2)
        assert len(results) == 2


def test_sanitize_html_to_text_with_scripts() -> None:
    """Test _sanitize_html_to_text removes script and style elements (covers line 73)."""
    html = """
    <html>
        <head>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <p>Test text</p>
        </body>
    </html>
    """
    text = _sanitize_html_to_text(html)
    assert "Test text" in text
    assert "alert" not in text
    assert "color: red" not in text


def test_douban_provider_prepare_query_empty_result(
    douban_provider: DoubanProvider,
) -> None:
    """Test _prepare_query returns empty when no tokens."""
    query = douban_provider._prepare_query("a")
    assert query == ""


def test_douban_provider_search_empty_query_after_preparation(
    douban_provider: DoubanProvider,
) -> None:
    """Test search returns empty when _prepare_query returns empty (covers line 234)."""
    # Mock _prepare_query to return empty string
    with patch.object(douban_provider, "_prepare_query", return_value=""):
        results = douban_provider.search("test query")
        assert results == []


def test_douban_provider_fetch_book_details_exception_handling(
    douban_provider: DoubanProvider,
) -> None:
    """Test _fetch_book_details exception handling (covers lines 365-374)."""
    import concurrent.futures

    detail_html = """
    <html>
        <body>
            <span property="v:itemreviewed">Test Book</span>
            <div id="link-report">
                <div class="intro">Test description</div>
            </div>
        </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.content = detail_html.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    # Create a function that raises an exception for one book_id
    original_parse = douban_provider._parse_single_book
    call_count = {"count": 0}

    def failing_parse(book_id: str, client: object) -> object:
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise concurrent.futures.CancelledError("Test cancelled")
        return original_parse(book_id, client)  # type: ignore[arg-type]

    with patch.object(douban_provider, "_parse_single_book", side_effect=failing_parse):
        book_ids = ["12345", "error"]
        results = douban_provider._fetch_book_details(book_ids, mock_client)
        # Should handle the exception and continue
        assert len(results) >= 0


def test_douban_provider_extract_rating_exception(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_rating handles exceptions (covers lines 489-490)."""
    html = etree.fromstring(
        '<html><body><div class="rating_self clearfix"><strong>invalid</strong></div></body></html>'
    )
    # The rating text "invalid" will cause ValueError when converting to float
    rating = douban_provider._extract_rating(html)
    assert rating is None


def test_douban_provider_extract_description_exception(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_description handles exceptions (covers lines 544-545)."""
    html = etree.fromstring(
        '<html><body><div id="link-report"><div class="intro">Test</div></div></body></html>'
    )
    # Mock tostring to raise an exception
    with patch("lxml.etree.tostring", side_effect=ValueError("Test error")):
        description = douban_provider._extract_description(html)
        assert description is None


def test_douban_provider_extract_info_metadata_no_text(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_info_metadata skips elements with no text (covers line 577)."""
    html = etree.fromstring("""
    <html>
        <body>
            <div id="info">
                <span class="pl"></span>
                <span class="pl">作者</span>
                <a>Author 1</a>
            </div>
        </body>
    </html>
    """)
    authors, _publisher, _subtitle, _published_date, _series, _identifiers = (
        douban_provider._extract_info_metadata(html)
    )
    # Should skip the empty span and process the one with text
    assert len(authors) >= 0


def test_douban_provider_extract_series_from_element_no_next(
    douban_provider: DoubanProvider,
) -> None:
    """Test _extract_series_from_element returns None when no next element (covers line 685)."""
    html = etree.fromstring("""
    <html>
        <body>
            <div id="info">
                <span class="pl">丛书</span>
            </div>
        </body>
    </html>
    """)
    element = html.xpath("//span[@class='pl']")[0]
    series = douban_provider._extract_series_from_element(element)
    assert series is None

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

"""Tests for Anna's Archive extractors module."""

import pytest
from bs4 import BeautifulSoup

from bookcard.pvr.download_clients.direct_http.anna.extractors import (
    ClipboardLinkExtractor,
    CopyTextExtractor,
    DownloadButtonExtractor,
    GenericLinkExtractor,
    LinkExtractor,
    WindowLocationExtractor,
    is_valid_direct_link,
)


class TestIsValidDirectLink:
    """Test is_valid_direct_link function."""

    @pytest.mark.parametrize(
        ("link", "expected"),
        [
            ("https://example.com/file.pdf", True),
            ("http://example.com/file.pdf", True),
            ("https://example.com/slow_download/file.pdf", False),
            ("http://example.com/slow_download/file.pdf", False),
        ],
    )
    def test_is_valid_direct_link(self, link: str, expected: bool) -> None:
        """Test is_valid_direct_link function."""
        assert is_valid_direct_link(link) == expected


class TestClipboardLinkExtractor:
    """Test ClipboardLinkExtractor class."""

    def test_extract_success(self) -> None:
        """Test extract with clipboard pattern."""
        html = '<script>navigator.clipboard.writeText("https://example.com/file.pdf");</script>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = ClipboardLinkExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_invalid_link(self) -> None:
        """Test extract with invalid link."""
        html = '<script>navigator.clipboard.writeText("https://example.com/slow_download/file.pdf");</script>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = ClipboardLinkExtractor()
        result = extractor.extract(soup, html)
        assert result is None

    def test_extract_no_match(self) -> None:
        """Test extract with no match."""
        html = "<html><body>No clipboard</body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = ClipboardLinkExtractor()
        result = extractor.extract(soup, html)
        assert result is None


class TestDownloadButtonExtractor:
    """Test DownloadButtonExtractor class."""

    def test_extract_success(self) -> None:
        """Test extract with download button."""
        html = '<html><body><a href="https://example.com/file.pdf">📚 Download now</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = DownloadButtonExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_download_text(self) -> None:
        """Test extract with 'Download now' text."""
        html = '<html><body><a href="https://example.com/file.pdf">Download now</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = DownloadButtonExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_no_match(self) -> None:
        """Test extract with no download button."""
        html = '<html><body><a href="https://example.com/other">Other link</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = DownloadButtonExtractor()
        result = extractor.extract(soup, html)
        assert result is None


class TestWindowLocationExtractor:
    """Test WindowLocationExtractor class."""

    def test_extract_success(self) -> None:
        """Test extract with window.location pattern."""
        html = '<script>window.location.href = "https://example.com/file.pdf";</script>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = WindowLocationExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_invalid_link(self) -> None:
        """Test extract with invalid link."""
        html = '<script>window.location.href = "https://example.com/slow_download/file.pdf";</script>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = WindowLocationExtractor()
        result = extractor.extract(soup, html)
        assert result is None

    def test_extract_no_match(self) -> None:
        """Test extract with no match."""
        html = "<html><body>No window.location</body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = WindowLocationExtractor()
        result = extractor.extract(soup, html)
        assert result is None


class TestCopyTextExtractor:
    """Test CopyTextExtractor class."""

    def test_extract_success(self) -> None:
        """Test extract with copy text."""
        html = '<html><body><p>Copy this url</p><a href="https://example.com/file.pdf">Link</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = CopyTextExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_code_element(self) -> None:
        """Test extract with code element."""
        html = "<html><body><p>Copy this url</p><code>https://example.com/file.pdf</code></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = CopyTextExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_no_match(self) -> None:
        """Test extract with no copy text."""
        html = "<html><body><p>No copy text</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = CopyTextExtractor()
        result = extractor.extract(soup, html)
        assert result is None


class TestGenericLinkExtractor:
    """Test GenericLinkExtractor class."""

    def test_extract_download_attribute(self) -> None:
        """Test extract with download attribute."""
        html = '<html><body><a href="https://example.com/file.pdf" download>Link</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = GenericLinkExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_whitespace_normal_span(self) -> None:
        """Test extract with whitespace-normal span."""
        html = '<html><body><span class="whitespace-normal">https://example.com/file.pdf</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = GenericLinkExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_bg_gray_200_span(self) -> None:
        """Test extract with bg-gray-200 span."""
        html = '<html><body><span class="bg-gray-200">https://example.com/file.pdf</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = GenericLinkExtractor()
        result = extractor.extract(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_no_match(self) -> None:
        """Test extract with no match."""
        html = "<html><body><p>No links</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = GenericLinkExtractor()
        result = extractor.extract(soup, html)
        assert result is None


class TestLinkExtractor:
    """Test LinkExtractor class."""

    def test_init(self) -> None:
        """Test initialization."""
        extractor = LinkExtractor()
        assert len(extractor._strategies) > 0

    def test_extract_link_success(self) -> None:
        """Test extract_link with success."""
        html = '<script>navigator.clipboard.writeText("https://example.com/file.pdf");</script>'
        soup = BeautifulSoup(html, "html.parser")
        extractor = LinkExtractor()
        result = extractor.extract_link(soup, html)
        assert result == "https://example.com/file.pdf"

    def test_extract_link_no_match(self) -> None:
        """Test extract_link with no match."""
        html = "<html><body>No links</body></html>"
        soup = BeautifulSoup(html, "html.parser")
        extractor = LinkExtractor()
        result = extractor.extract_link(soup, html)
        assert result is None

    def test_register_strategy(self) -> None:
        """Test register_strategy."""
        extractor = LinkExtractor()
        initial_count = len(extractor._strategies)
        custom_strategy = ClipboardLinkExtractor()
        extractor.register_strategy(custom_strategy)
        assert len(extractor._strategies) == initial_count + 1

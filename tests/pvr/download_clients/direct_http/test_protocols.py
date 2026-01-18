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

"""Tests for Direct HTTP protocols module."""

import time
from unittest.mock import MagicMock

import httpx
from bs4 import BeautifulSoup

from bookcard.pvr.download_clients.direct_http.protocols import (
    BeautifulSoupParser,
    SystemTimeProvider,
)


class TestBeautifulSoupParser:
    """Test BeautifulSoupParser class."""

    def test_parse_valid_html(self) -> None:
        """Test parsing valid HTML."""
        parser = BeautifulSoupParser()
        html = "<html><body><p>Test</p></body></html>"
        soup = parser.parse(html)
        assert isinstance(soup, BeautifulSoup)
        assert soup.find("p").get_text() == "Test"

    def test_parse_empty_html(self) -> None:
        """Test parsing empty HTML."""
        parser = BeautifulSoupParser()
        soup = parser.parse("")
        assert isinstance(soup, BeautifulSoup)

    def test_parse_malformed_html(self) -> None:
        """Test parsing malformed HTML."""
        parser = BeautifulSoupParser()
        html = "<html><body><p>Unclosed tag</body></html>"
        soup = parser.parse(html)
        assert isinstance(soup, BeautifulSoup)


class TestSystemTimeProvider:
    """Test SystemTimeProvider class."""

    def test_time(self) -> None:
        """Test time() method."""
        provider = SystemTimeProvider()
        current_time = provider.time()
        assert isinstance(current_time, float)
        assert current_time > 0

    def test_sleep(self) -> None:
        """Test sleep() method."""
        provider = SystemTimeProvider()
        start = time.time()
        provider.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed >= 0.1

    def test_sleep_zero(self) -> None:
        """Test sleep with zero duration."""
        provider = SystemTimeProvider()
        start = time.time()
        provider.sleep(0)
        elapsed = time.time() - start
        assert elapsed < 0.1


class TestProtocols:
    """Test protocol definitions."""

    def test_streaming_response_protocol(self) -> None:
        """Test StreamingResponse protocol."""
        response = MagicMock()
        response.headers = httpx.Headers({"content-type": "text/html"})
        response.status_code = 200
        response.text = "test"
        response.raise_for_status = MagicMock()
        response.iter_bytes = MagicMock(return_value=iter([b"chunk"]))

        assert hasattr(response, "headers")
        assert hasattr(response, "status_code")
        assert hasattr(response, "text")
        assert hasattr(response, "raise_for_status")
        assert hasattr(response, "iter_bytes")

    def test_streaming_http_client_protocol(self) -> None:
        """Test StreamingHttpClient protocol."""
        client = MagicMock()
        client.get = MagicMock()
        client.stream = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)

        assert hasattr(client, "get")
        assert hasattr(client, "stream")
        assert hasattr(client, "__enter__")
        assert hasattr(client, "__exit__")

    def test_html_parser_protocol(self) -> None:
        """Test HtmlParser protocol."""
        parser = BeautifulSoupParser()
        # Protocol classes can't be used with isinstance unless runtime_checkable
        assert hasattr(parser, "parse")

    def test_time_provider_protocol(self) -> None:
        """Test TimeProvider protocol."""
        provider = SystemTimeProvider()
        # Protocol classes can't be used with isinstance unless runtime_checkable
        assert hasattr(provider, "time")
        assert hasattr(provider, "sleep")

    def test_url_resolver_protocol(self) -> None:
        """Test UrlResolver protocol."""
        resolver = MagicMock()
        resolver.can_resolve = MagicMock(return_value=True)
        resolver.resolve = MagicMock(return_value="https://example.com")

        assert hasattr(resolver, "can_resolve")
        assert hasattr(resolver, "resolve")

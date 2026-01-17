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

"""Tests for Direct HTTP resolvers module."""

import uuid
from unittest.mock import MagicMock

import httpx
import pytest

from bookcard.pvr.download_clients.direct_http.protocols import StreamingResponse
from bookcard.pvr.download_clients.direct_http.resolvers import (
    DirectUrlResolver,
    FilenameResolver,
)


class TestDirectUrlResolver:
    """Test DirectUrlResolver class."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://example.com/file.pdf", True),
            ("http://example.com/file.pdf", True),
            ("https://annas-archive.li/md5/abc123", False),
            ("https://annas-archive.se/md5/def456", False),
            ("https://other-site.com/file.pdf", True),
        ],
    )
    def test_can_resolve(self, url: str, expected: bool) -> None:
        """Test can_resolve method."""
        resolver = DirectUrlResolver()
        assert resolver.can_resolve(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/file.pdf",
            "http://example.com/file.pdf",
            "https://other-site.com/file.pdf",
        ],
    )
    def test_resolve(self, url: str) -> None:
        """Test resolve method."""
        resolver = DirectUrlResolver()
        result = resolver.resolve(url)
        assert result == url


class TestFilenameResolver:
    """Test FilenameResolver class."""

    def test_resolve_from_title_pdf(self) -> None:
        """Test resolving filename from title with PDF content type."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({"content-type": "application/pdf"})
        result = resolver.resolve(response, "https://example.com/file", "Test Book")
        assert result.endswith(".pdf")
        assert "Test Book" in result

    def test_resolve_from_title_epub(self) -> None:
        """Test resolving filename from title with EPUB content type."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({"content-type": "application/epub+zip"})
        result = resolver.resolve(response, "https://example.com/file", "Test Book")
        assert result.endswith(".epub")
        assert "Test Book" in result

    def test_resolve_from_title_default_ext(self) -> None:
        """Test resolving filename from title with unknown content type."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({"content-type": "application/octet-stream"})
        result = resolver.resolve(response, "https://example.com/file", "Test Book")
        assert result.endswith(".bin")
        assert "Test Book" in result

    def test_resolve_from_url_path(self) -> None:
        """Test resolving filename from URL path."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})
        result = resolver.resolve(
            response, "https://example.com/path/to/file.pdf", None
        )
        assert result == "file.pdf"

    def test_resolve_from_url_path_with_query(self) -> None:
        """Test resolving filename from URL path with query parameters."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})
        result = resolver.resolve(
            response, "https://example.com/path/to/file.pdf?param=value", None
        )
        assert result == "file.pdf"

    def test_resolve_fallback_to_uuid(self) -> None:
        """Test fallback to UUID when no filename available."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})
        result = resolver.resolve(response, "https://example.com/", None)
        assert result.startswith("download-")
        # Should be a valid UUID after "download-"
        uuid_part = result.replace("download-", "")
        # Verify it's a valid UUID format
        uuid.UUID(uuid_part)

    def test_resolve_sanitizes_filename(self) -> None:
        """Test that filenames are sanitized."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({"content-type": "application/pdf"})
        result = resolver.resolve(
            response, "https://example.com/file", "Test/Book:Name"
        )
        # sanitize_filename from common.filesystem only replaces [\\:*?"<>|]
        # It does NOT replace /, so / will remain in the filename
        # But : should be replaced with _
        assert ":" not in result
        # / might remain or be replaced depending on implementation
        # The important thing is that : is sanitized

    def test_resolve_empty_title(self) -> None:
        """Test resolving with empty title."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})
        result = resolver.resolve(response, "https://example.com/file.pdf", "")
        assert result == "file.pdf"

    def test_resolve_empty_path(self) -> None:
        """Test resolving with empty path."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})
        result = resolver.resolve(response, "https://example.com/", None)
        assert result.startswith("download-")

    @pytest.mark.parametrize(
        ("content_type", "expected_ext"),
        [
            ("application/pdf", ".pdf"),
            ("application/epub+zip", ".epub"),
            ("application/x-epub+zip", ".epub"),
            ("text/html", ".bin"),
            ("application/octet-stream", ".bin"),
        ],
    )
    def test_resolve_content_types(self, content_type: str, expected_ext: str) -> None:
        """Test resolving with different content types."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({"content-type": content_type})
        result = resolver.resolve(response, "https://example.com/file", "Test")
        assert result.endswith(expected_ext)

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

from unittest.mock import MagicMock

import httpx

from bookcard.pvr.download_clients.direct_http.protocols import StreamingResponse
from bookcard.pvr.download_clients.direct_http.resolvers import FilenameResolver


class TestFilenameResolverMetadata:
    def test_resolve_from_metadata(self) -> None:
        """Test resolving filename from metadata (author, title, quality)."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})

        result = resolver.resolve(
            response,
            "https://example.com/file",
            title="The Book",
            author="John Doe",
            quality="epub",
        )
        assert result == "John Doe - The Book.epub"

    def test_resolve_from_metadata_no_author(self) -> None:
        """Test resolving filename from metadata without author."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})

        result = resolver.resolve(
            response, "https://example.com/file", title="The Book", quality="pdf"
        )
        assert result == "The Book.pdf"

    def test_resolve_fallback_to_guid(self) -> None:
        """Test fallback to GUID."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})

        result = resolver.resolve(
            response,
            "https://example.com/",
            title=None,
            guid="abcdef123456",
            quality="epub",
        )
        assert result == "abcdef123456.epub"

    def test_resolve_fallback_to_guid_url(self) -> None:
        """Test fallback to GUID when GUID is a URL."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)
        response.headers = httpx.Headers({})

        result = resolver.resolve(
            response,
            "https://example.com/",
            title=None,
            guid="https://site.com/t/12345",
            quality="pdf",
        )
        # Should extract last part of GUID URL
        assert result == "12345.pdf"

    def test_resolve_metadata_precedence(self) -> None:
        """Test that metadata takes precedence over title fallback but not Content-Disposition."""
        resolver = FilenameResolver()
        response = MagicMock(spec=StreamingResponse)

        # 1. Content-Disposition overrides everything
        response.headers = httpx.Headers({
            "content-disposition": 'attachment; filename="server.pdf"'
        })
        result = resolver.resolve(
            response, "https://ex.com", title="Title", author="Author", quality="epub"
        )
        assert result == "server.pdf"

        # 2. Metadata overrides URL path
        response.headers = httpx.Headers({})
        result = resolver.resolve(
            response,
            "https://ex.com/file.pdf",
            title="Title",
            author="Author",
            quality="epub",
        )
        assert result == "Author - Title.epub"

        # 3. URL path overrides GUID
        result = resolver.resolve(
            response, "https://ex.com/file.pdf", title=None, guid="guid"
        )
        assert result == "file.pdf"

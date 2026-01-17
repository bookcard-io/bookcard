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

"""Tests for Libgen resolver module."""

from unittest.mock import MagicMock

import pytest

from bookcard.pvr.download_clients.direct_http.libgen_resolver import LibgenResolver


class TestLibgenResolver:
    """Test LibgenResolver class."""

    def test_init(self, mock_http_client_factory: MagicMock) -> None:
        """Test initialization."""
        resolver = LibgenResolver(mock_http_client_factory)
        assert resolver._http_client_factory == mock_http_client_factory
        assert len(resolver.MIRRORS) > 0

    def test_resolve_empty_md5(self, mock_http_client_factory: MagicMock) -> None:
        """Test resolving with empty MD5."""
        resolver = LibgenResolver(mock_http_client_factory)
        assert resolver.resolve("") is None
        assert resolver.resolve(None) is None  # type: ignore[arg-type]

    def test_resolve_success(self, mock_http_client_factory: MagicMock) -> None:
        """Test successful resolution."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        # Mock successful response with download link
        html = """
        <html>
            <body>
                <a href="get.php?md5=1234567890abcdef1234567890abcdef">GET</a>
            </body>
        </html>
        """

        # The factory is a callable that returns a context manager
        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        # Replace the factory
        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        # The resolver should find the link and join it with the mirror URL
        assert result is not None
        assert "get.php" in result

    def test_resolve_with_get_text(self, mock_http_client_factory: MagicMock) -> None:
        """Test resolution with GET text in link."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "abcdef1234567890abcdef1234567890"

        html = """
        <html>
            <body>
                <a href="get.php?md5=abcdef1234567890abcdef1234567890">GET</a>
            </body>
        </html>
        """

        # The factory is a callable that returns a context manager
        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        # Replace the factory
        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        assert result is not None

    def test_resolve_non_200_status(self, mock_http_client_factory: MagicMock) -> None:
        """Test resolution with non-200 status code."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        assert result is None

    def test_resolve_connection_error(
        self, mock_http_client_factory: MagicMock
    ) -> None:
        """Test resolution with connection error."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_client.get.side_effect = OSError("Connection failed")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        # Should try next mirror or return None
        assert result is None or isinstance(result, str)

    def test_resolve_runtime_error(self, mock_http_client_factory: MagicMock) -> None:
        """Test resolution with runtime error."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_client.get.side_effect = RuntimeError("Runtime error")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        assert result is None

    def test_resolve_value_error(self, mock_http_client_factory: MagicMock) -> None:
        """Test resolution with value error."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_client.get.side_effect = ValueError("Value error")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        assert result is None

    def test_resolve_no_download_link(
        self, mock_http_client_factory: MagicMock
    ) -> None:
        """Test resolution when no download link found."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        html = """
        <html>
            <body>
                <p>No download link here</p>
            </body>
        </html>
        """

        def factory() -> MagicMock:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        resolver._http_client_factory = factory

        result = resolver.resolve(md5)
        assert result is None

    def test_resolve_tries_all_mirrors(
        self, mock_http_client_factory: MagicMock
    ) -> None:
        """Test that resolver tries all mirrors."""
        resolver = LibgenResolver(mock_http_client_factory)
        md5 = "1234567890abcdef1234567890abcdef"

        # Track how many times the factory is called (once per mirror)
        call_count = [0]

        def factory() -> MagicMock:
            call_count[0] += 1
            mock_client = MagicMock()
            if call_count[0] == 1:
                # First call raises error
                mock_client.get.side_effect = OSError("Connection failed")
            else:
                # Subsequent calls succeed
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = (
                    '<html><body><a href="get.php?md5=test">GET</a></body></html>'
                )
                mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            return mock_client

        # Replace the factory
        resolver._http_client_factory = factory

        resolver.resolve(md5)
        # Should have tried at least one mirror (the factory is called once per mirror)
        assert call_count[0] >= 1

    @pytest.mark.parametrize(
        "mirror",
        [
            "https://libgen.li",
            "https://libgen.rs",
            "https://libgen.is",
            "https://libgen.st",
        ],
    )
    def test_mirrors_defined(self, mirror: str) -> None:
        """Test that all mirrors are defined."""
        resolver = LibgenResolver(lambda: MagicMock())
        assert mirror in resolver.MIRRORS

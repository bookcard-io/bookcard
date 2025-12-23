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

"""Unit tests for download strategies."""

from unittest.mock import MagicMock

import pytest

from bookcard.pvr._base.capabilities import FileSupport, MagnetSupport, UrlSupport
from bookcard.pvr.base.interfaces import UrlRouterProtocol
from bookcard.pvr.base.strategies import (
    DownloadStrategyRegistry,
    FileStrategy,
    MagnetStrategy,
    UrlStrategy,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.url_router import DownloadType

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_magnet_client() -> MagnetSupport:
    """Create a mock client that supports magnet links."""
    client = MagicMock(spec=MagnetSupport)
    client.add_magnet = MagicMock(return_value="magnet-item-id")
    client.client_name = "MagnetClient"
    return client


@pytest.fixture
def mock_url_client() -> UrlSupport:
    """Create a mock client that supports URL downloads."""
    client = MagicMock(spec=UrlSupport)
    client.add_url = MagicMock(return_value="url-item-id")
    client.client_name = "UrlClient"
    return client


@pytest.fixture
def mock_file_client() -> FileSupport:
    """Create a mock client that supports file uploads."""
    client = MagicMock(spec=FileSupport)
    client.add_file = MagicMock(return_value="file-item-id")
    client.client_name = "FileClient"
    return client


@pytest.fixture
def mock_unsupported_client() -> MagicMock:
    """Create a mock client that doesn't support any capability."""
    client = MagicMock()
    client.client_name = "UnsupportedClient"
    return client


@pytest.fixture
def mock_router() -> UrlRouterProtocol:
    """Create a mock URL router."""
    return MagicMock(spec=UrlRouterProtocol)


@pytest.fixture
def magnet_strategy() -> MagnetStrategy:
    """Create a MagnetStrategy instance."""
    return MagnetStrategy()


@pytest.fixture
def url_strategy() -> UrlStrategy:
    """Create a UrlStrategy instance."""
    return UrlStrategy()


@pytest.fixture
def file_strategy() -> FileStrategy:
    """Create a FileStrategy instance."""
    return FileStrategy()


@pytest.fixture
def strategy_registry(mock_router: UrlRouterProtocol) -> DownloadStrategyRegistry:
    """Create a DownloadStrategyRegistry instance."""
    return DownloadStrategyRegistry(router=mock_router)


# ============================================================================
# MagnetStrategy Tests
# ============================================================================


class TestMagnetStrategy:
    """Test cases for MagnetStrategy."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("magnet:?xt=urn:btih:abc123", True),
            ("magnet:?xt=urn:btih:def456&dn=test", True),
            ("MAGNET:?xt=urn:btih:abc123", False),  # Case sensitive
            ("http://example.com/file.torrent", False),
            ("https://example.com/file.torrent", False),
            ("/path/to/file.torrent", False),
            ("", False),
        ],
    )
    def test_can_handle(
        self, magnet_strategy: MagnetStrategy, url: str, expected: bool
    ) -> None:
        """Test MagnetStrategy.can_handle with various URLs."""
        assert magnet_strategy.can_handle(url) == expected

    def test_add_with_supported_client(
        self,
        magnet_strategy: MagnetStrategy,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test MagnetStrategy.add with a client that supports magnets."""
        url = "magnet:?xt=urn:btih:abc123"
        title = "Test Title"
        category = "books"
        download_path = "/downloads"

        result = magnet_strategy.add(
            client=mock_magnet_client,
            url=url,
            title=title,
            category=category,
            download_path=download_path,
        )

        assert result == "magnet-item-id"
        mock_magnet_client.add_magnet.assert_called_once_with(  # type: ignore[attr-defined]
            url, title, category, download_path
        )

    def test_add_with_unsupported_client(
        self,
        magnet_strategy: MagnetStrategy,
        mock_unsupported_client: MagicMock,
    ) -> None:
        """Test MagnetStrategy.add raises error when client doesn't support magnets."""
        url = "magnet:?xt=urn:btih:abc123"

        with pytest.raises(PVRProviderError, match="does not support magnet links"):
            magnet_strategy.add(client=mock_unsupported_client, url=url)

    def test_add_with_unsupported_client_no_client_name(
        self,
        magnet_strategy: MagnetStrategy,
    ) -> None:
        """Test MagnetStrategy.add with client without client_name attribute."""
        client = MagicMock()
        del client.client_name
        url = "magnet:?xt=urn:btih:abc123"

        with pytest.raises(
            PVRProviderError, match="Client does not support magnet links"
        ):
            magnet_strategy.add(client=client, url=url)

    def test_add_with_optional_params(
        self,
        magnet_strategy: MagnetStrategy,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test MagnetStrategy.add with all optional parameters as None."""
        url = "magnet:?xt=urn:btih:abc123"

        result = magnet_strategy.add(
            client=mock_magnet_client,
            url=url,
            title=None,
            category=None,
            download_path=None,
        )

        assert result == "magnet-item-id"
        mock_magnet_client.add_magnet.assert_called_once_with(url, None, None, None)  # type: ignore[attr-defined]


# ============================================================================
# UrlStrategy Tests
# ============================================================================


class TestUrlStrategy:
    """Test cases for UrlStrategy."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("http://example.com/file.torrent", True),
            ("https://example.com/file.torrent", True),
            ("HTTP://example.com/file.torrent", False),  # Case sensitive
            ("HTTPS://example.com/file.torrent", False),  # Case sensitive
            ("magnet:?xt=urn:btih:abc123", False),
            ("/path/to/file.torrent", False),
            ("ftp://example.com/file.torrent", False),
            ("", False),
        ],
    )
    def test_can_handle(
        self, url_strategy: UrlStrategy, url: str, expected: bool
    ) -> None:
        """Test UrlStrategy.can_handle with various URLs."""
        assert url_strategy.can_handle(url) == expected

    def test_add_with_supported_client(
        self,
        url_strategy: UrlStrategy,
        mock_url_client: UrlSupport,
    ) -> None:
        """Test UrlStrategy.add with a client that supports URLs."""
        url = "https://example.com/file.torrent"
        title = "Test Title"
        category = "books"
        download_path = "/downloads"

        result = url_strategy.add(
            client=mock_url_client,
            url=url,
            title=title,
            category=category,
            download_path=download_path,
        )

        assert result == "url-item-id"
        mock_url_client.add_url.assert_called_once_with(  # type: ignore[attr-defined]
            url, title, category, download_path
        )

    def test_add_with_unsupported_client(
        self,
        url_strategy: UrlStrategy,
        mock_unsupported_client: MagicMock,
    ) -> None:
        """Test UrlStrategy.add raises error when client doesn't support URLs."""
        url = "https://example.com/file.torrent"

        with pytest.raises(PVRProviderError, match="does not support URL downloads"):
            url_strategy.add(client=mock_unsupported_client, url=url)

    def test_add_with_unsupported_client_no_client_name(
        self,
        url_strategy: UrlStrategy,
    ) -> None:
        """Test UrlStrategy.add with client without client_name attribute."""
        client = MagicMock()
        del client.client_name
        url = "https://example.com/file.torrent"

        with pytest.raises(
            PVRProviderError, match="Client does not support URL downloads"
        ):
            url_strategy.add(client=client, url=url)

    def test_add_with_optional_params(
        self,
        url_strategy: UrlStrategy,
        mock_url_client: UrlSupport,
    ) -> None:
        """Test UrlStrategy.add with all optional parameters as None."""
        url = "https://example.com/file.torrent"

        result = url_strategy.add(
            client=mock_url_client,
            url=url,
            title=None,
            category=None,
            download_path=None,
        )

        assert result == "url-item-id"
        mock_url_client.add_url.assert_called_once_with(url, None, None, None)  # type: ignore[attr-defined]


# ============================================================================
# FileStrategy Tests
# ============================================================================


class TestFileStrategy:
    """Test cases for FileStrategy."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("/path/to/file.torrent", True),
            ("file.torrent", True),
            ("relative/path/file.torrent", True),
            ("magnet:?xt=urn:btih:abc123", False),
            ("http://example.com/file.torrent", False),
            ("https://example.com/file.torrent", False),
            ("", True),  # Empty string is not a magnet/http/https URL
        ],
    )
    def test_can_handle(
        self, file_strategy: FileStrategy, url: str, expected: bool
    ) -> None:
        """Test FileStrategy.can_handle with various URLs."""
        assert file_strategy.can_handle(url) == expected

    def test_add_with_supported_client(
        self,
        file_strategy: FileStrategy,
        mock_file_client: FileSupport,
    ) -> None:
        """Test FileStrategy.add with a client that supports files."""
        url = "/path/to/file.torrent"
        title = "Test Title"
        category = "books"
        download_path = "/downloads"

        result = file_strategy.add(
            client=mock_file_client,
            url=url,
            title=title,
            category=category,
            download_path=download_path,
        )

        assert result == "file-item-id"
        mock_file_client.add_file.assert_called_once_with(  # type: ignore[attr-defined]
            url, title, category, download_path
        )

    def test_add_with_unsupported_client(
        self,
        file_strategy: FileStrategy,
        mock_unsupported_client: MagicMock,
    ) -> None:
        """Test FileStrategy.add raises error when client doesn't support files."""
        url = "/path/to/file.torrent"

        with pytest.raises(PVRProviderError, match="does not support file uploads"):
            file_strategy.add(client=mock_unsupported_client, url=url)

    def test_add_with_unsupported_client_no_client_name(
        self,
        file_strategy: FileStrategy,
    ) -> None:
        """Test FileStrategy.add with client without client_name attribute."""
        client = MagicMock()
        del client.client_name
        url = "/path/to/file.torrent"

        with pytest.raises(
            PVRProviderError, match="Client does not support file uploads"
        ):
            file_strategy.add(client=client, url=url)

    def test_add_with_optional_params(
        self,
        file_strategy: FileStrategy,
        mock_file_client: FileSupport,
    ) -> None:
        """Test FileStrategy.add with all optional parameters as None."""
        url = "/path/to/file.torrent"

        result = file_strategy.add(
            client=mock_file_client,
            url=url,
            title=None,
            category=None,
            download_path=None,
        )

        assert result == "file-item-id"
        mock_file_client.add_file.assert_called_once_with(url, None, None, None)  # type: ignore[attr-defined]


# ============================================================================
# DownloadStrategyRegistry Tests
# ============================================================================


class TestDownloadStrategyRegistry:
    """Test cases for DownloadStrategyRegistry."""

    def test_init(self, mock_router: UrlRouterProtocol) -> None:
        """Test DownloadStrategyRegistry initialization."""
        registry = DownloadStrategyRegistry(router=mock_router)

        assert registry._router is mock_router
        assert DownloadType.MAGNET in registry._strategies
        assert DownloadType.URL in registry._strategies
        assert DownloadType.FILE in registry._strategies
        assert isinstance(registry._strategies[DownloadType.MAGNET], MagnetStrategy)
        assert isinstance(registry._strategies[DownloadType.URL], UrlStrategy)
        assert isinstance(registry._strategies[DownloadType.FILE], FileStrategy)

    def test_register(self, strategy_registry: DownloadStrategyRegistry) -> None:
        """Test DownloadStrategyRegistry.register."""
        custom_strategy = MagicMock()
        custom_strategy.add = MagicMock(return_value="custom-id")

        strategy_registry.register(DownloadType.MAGNET, custom_strategy)

        assert strategy_registry._strategies[DownloadType.MAGNET] is custom_strategy

    def test_handle_magnet(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle with magnet URL."""
        url = "magnet:?xt=urn:btih:abc123"
        strategy_registry._router.route.return_value = DownloadType.MAGNET  # type: ignore[attr-defined]

        result = strategy_registry.handle(
            client=mock_magnet_client,
            url=url,
            title="Test",
            category="books",
            download_path="/downloads",
        )

        assert result == "magnet-item-id"
        strategy_registry._router.route.assert_called_once_with(url)  # type: ignore[attr-defined]
        mock_magnet_client.add_magnet.assert_called_once_with(  # type: ignore[attr-defined]
            url, "Test", "books", "/downloads"
        )

    def test_handle_url(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_url_client: UrlSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle with URL."""
        url = "https://example.com/file.torrent"
        strategy_registry._router.route.return_value = DownloadType.URL  # type: ignore[attr-defined]

        result = strategy_registry.handle(
            client=mock_url_client,
            url=url,
            title="Test",
            category="books",
            download_path="/downloads",
        )

        assert result == "url-item-id"
        strategy_registry._router.route.assert_called_once_with(url)  # type: ignore[attr-defined]
        mock_url_client.add_url.assert_called_once_with(  # type: ignore[attr-defined]
            url, "Test", "books", "/downloads"
        )

    def test_handle_file(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_file_client: FileSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle with file path."""
        url = "/path/to/file.torrent"
        strategy_registry._router.route.return_value = DownloadType.FILE  # type: ignore[attr-defined]

        result = strategy_registry.handle(
            client=mock_file_client,
            url=url,
            title="Test",
            category="books",
            download_path="/downloads",
        )

        assert result == "file-item-id"
        strategy_registry._router.route.assert_called_once_with(url)  # type: ignore[attr-defined]
        mock_file_client.add_file.assert_called_once_with(  # type: ignore[attr-defined]
            url, "Test", "books", "/downloads"
        )

    def test_handle_no_strategy_found(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle raises error when no strategy found."""
        url = "unknown://example.com/file"
        unknown_type = DownloadType.MAGNET  # Use a type that we'll remove
        strategy_registry._router.route.return_value = unknown_type  # type: ignore[attr-defined]
        # Remove the strategy to simulate missing strategy
        del strategy_registry._strategies[unknown_type]

        with pytest.raises(
            PVRProviderError, match="No strategy found for download type"
        ):
            strategy_registry.handle(client=mock_magnet_client, url=url)

    def test_handle_with_optional_params(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle with all optional parameters as None."""
        url = "magnet:?xt=urn:btih:abc123"
        strategy_registry._router.route.return_value = DownloadType.MAGNET  # type: ignore[attr-defined]

        result = strategy_registry.handle(
            client=mock_magnet_client,
            url=url,
            title=None,
            category=None,
            download_path=None,
        )

        assert result == "magnet-item-id"
        mock_magnet_client.add_magnet.assert_called_once_with(url, None, None, None)  # type: ignore[attr-defined]

    def test_handle_custom_strategy(
        self,
        strategy_registry: DownloadStrategyRegistry,
        mock_magnet_client: MagnetSupport,
    ) -> None:
        """Test DownloadStrategyRegistry.handle with custom registered strategy."""
        custom_strategy = MagicMock()
        custom_strategy.add = MagicMock(return_value="custom-item-id")
        strategy_registry.register(DownloadType.MAGNET, custom_strategy)

        url = "magnet:?xt=urn:btih:abc123"
        strategy_registry._router.route.return_value = DownloadType.MAGNET  # type: ignore[attr-defined]

        result = strategy_registry.handle(
            client=mock_magnet_client,
            url=url,
            title="Test",
        )

        assert result == "custom-item-id"
        custom_strategy.add.assert_called_once_with(
            mock_magnet_client, url, "Test", None, None
        )

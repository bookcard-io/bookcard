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

"""Tests for PVR base classes and settings."""

from abc import ABC

import pytest
from pydantic import ValidationError

from bookcard.pvr.base import (
    BaseDownloadClient,
    BaseIndexer,
    DownloadClientSettings,
    IndexerSettings,
    ManagedIndexer,
)
from bookcard.pvr.error_handlers import (
    handle_api_error_response,
    handle_http_error_response,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from tests.pvr.conftest import MockDownloadClient, MockIndexer


class TestIndexerSettings:
    """Test IndexerSettings Pydantic model."""

    def test_indexer_settings_minimal(self) -> None:
        """Test IndexerSettings with minimal required fields."""
        settings = IndexerSettings(base_url="https://indexer.example.com")

        assert settings.base_url == "https://indexer.example.com"
        assert settings.api_key is None
        assert settings.timeout_seconds == 30
        assert settings.retry_count == 3
        assert settings.categories is None

    def test_indexer_settings_complete(self) -> None:
        """Test IndexerSettings with all fields."""
        settings = IndexerSettings(
            base_url="https://indexer.example.com",
            api_key="test-api-key",
            timeout_seconds=60,
            retry_count=5,
            categories=[1000, 2000, 3000],
        )

        assert settings.base_url == "https://indexer.example.com"
        assert settings.api_key == "test-api-key"
        assert settings.timeout_seconds == 60
        assert settings.retry_count == 5
        assert settings.categories == [1000, 2000, 3000]

    @pytest.mark.parametrize(
        ("timeout", "should_raise"),
        [
            (1, False),
            (30, False),
            (300, False),
            (0, True),
            (-1, True),
            (301, True),
        ],
    )
    def test_indexer_settings_timeout_validation(
        self, timeout: int, should_raise: bool
    ) -> None:
        """Test IndexerSettings timeout validation (1-300 seconds)."""
        if should_raise:
            with pytest.raises(ValidationError):
                _ = IndexerSettings(
                    base_url="https://indexer.example.com",
                    timeout_seconds=timeout,
                )
        else:
            settings = IndexerSettings(
                base_url="https://indexer.example.com", timeout_seconds=timeout
            )
            assert settings.timeout_seconds == timeout

    @pytest.mark.parametrize(
        ("retry_count", "should_raise"),
        [
            (0, False),
            (3, False),
            (10, False),
            (-1, True),
            (11, True),
        ],
    )
    def test_indexer_settings_retry_validation(
        self, retry_count: int, should_raise: bool
    ) -> None:
        """Test IndexerSettings retry_count validation (0-10)."""
        if should_raise:
            with pytest.raises(ValidationError):
                _ = IndexerSettings(
                    base_url="https://indexer.example.com",
                    retry_count=retry_count,
                )
        else:
            settings = IndexerSettings(
                base_url="https://indexer.example.com", retry_count=retry_count
            )
            assert settings.retry_count == retry_count

    def test_indexer_settings_missing_base_url(self) -> None:
        """Test IndexerSettings validation with missing base_url."""
        with pytest.raises(ValidationError) as exc_info:
            _ = IndexerSettings()
        assert "base_url" in str(exc_info.value).lower()


class TestDownloadClientSettings:
    """Test DownloadClientSettings Pydantic model."""

    def test_download_client_settings_minimal(self) -> None:
        """Test DownloadClientSettings with minimal required fields."""
        settings = DownloadClientSettings(host="localhost", port=8080)

        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.username is None
        assert settings.password is None
        assert settings.use_ssl is False
        assert settings.timeout_seconds == 30
        assert settings.category is None
        assert settings.download_path is None

    def test_download_client_settings_complete(self) -> None:
        """Test DownloadClientSettings with all fields."""
        settings = DownloadClientSettings(
            host="example.com",
            port=443,
            username="admin",
            password="secret",
            use_ssl=True,
            timeout_seconds=60,
            category="bookcard",
            download_path="/downloads/books",
        )

        assert settings.host == "example.com"
        assert settings.port == 443
        assert settings.username == "admin"
        assert settings.password == "secret"
        assert settings.use_ssl is True
        assert settings.timeout_seconds == 60
        assert settings.category == "bookcard"
        assert settings.download_path == "/downloads/books"

    @pytest.mark.parametrize(
        ("port", "should_raise"),
        [
            (1, False),
            (8080, False),
            (65535, False),
            (0, True),
            (-1, True),
            (65536, True),
        ],
    )
    def test_download_client_settings_port_validation(
        self, port: int, should_raise: bool
    ) -> None:
        """Test DownloadClientSettings port validation (1-65535)."""
        if should_raise:
            with pytest.raises(ValidationError):
                _ = DownloadClientSettings(host="localhost", port=port)
        else:
            settings = DownloadClientSettings(host="localhost", port=port)
            assert settings.port == port

    @pytest.mark.parametrize(
        ("timeout", "should_raise"),
        [
            (1, False),
            (30, False),
            (300, False),
            (0, True),
            (-1, True),
            (301, True),
        ],
    )
    def test_download_client_settings_timeout_validation(
        self, timeout: int, should_raise: bool
    ) -> None:
        """Test DownloadClientSettings timeout validation (1-300 seconds)."""
        if should_raise:
            with pytest.raises(ValidationError):
                _ = DownloadClientSettings(
                    host="localhost", port=8080, timeout_seconds=timeout
                )
        else:
            settings = DownloadClientSettings(
                host="localhost", port=8080, timeout_seconds=timeout
            )
            assert settings.timeout_seconds == timeout

    def test_download_client_settings_missing_required_fields(self) -> None:
        """Test DownloadClientSettings validation with missing required fields."""
        # Missing host
        with pytest.raises(ValidationError) as exc_info:
            _ = DownloadClientSettings(port=8080)
        assert "host" in str(exc_info.value).lower()

        # Missing port
        with pytest.raises(ValidationError) as exc_info:
            _ = DownloadClientSettings(host="localhost")
        assert "port" in str(exc_info.value).lower()


class TestBaseIndexer:
    """Test BaseIndexer abstract base class."""

    def test_base_indexer_is_abstract(self) -> None:
        """Test that BaseIndexer is abstract and cannot be instantiated."""
        assert issubclass(BaseIndexer, ABC)
        with pytest.raises(TypeError):
            _ = BaseIndexer(settings=IndexerSettings(base_url="https://test.com"))

    def test_base_indexer_init(
        self, indexer_settings: IndexerSettings, mock_indexer: MockIndexer
    ) -> None:
        """Test BaseIndexer initialization."""
        assert mock_indexer.settings == indexer_settings

    def test_managed_indexer_enabled(self, indexer_settings: IndexerSettings) -> None:
        """Test ManagedIndexer enabled functionality."""
        indexer = MockIndexer(settings=indexer_settings)
        managed = ManagedIndexer(indexer, enabled=True)
        assert managed.is_enabled() is True

    def test_managed_indexer_disabled(self, indexer_settings: IndexerSettings) -> None:
        """Test ManagedIndexer disabled functionality."""
        indexer = MockIndexer(settings=indexer_settings)
        managed = ManagedIndexer(indexer, enabled=False)
        assert managed.is_enabled() is False

    def test_managed_indexer_set_enabled(
        self, indexer_settings: IndexerSettings
    ) -> None:
        """Test ManagedIndexer set_enabled method."""
        indexer = MockIndexer(settings=indexer_settings)
        managed = ManagedIndexer(indexer, enabled=True)
        assert managed.is_enabled() is True

        managed.set_enabled(False)
        assert managed.is_enabled() is False

        managed.set_enabled(True)
        assert managed.is_enabled() is True

    def test_base_indexer_search_abstract(self) -> None:
        """Test that BaseIndexer.search is abstract."""

        # Create a class that doesn't implement search
        class IncompleteIndexer(BaseIndexer):  # type: ignore[abstract]
            def test_connection(self) -> bool:  # type: ignore[override]
                return True

        with pytest.raises(TypeError):
            _ = IncompleteIndexer(settings=IndexerSettings(base_url="https://test.com"))

    def test_base_indexer_test_connection_abstract(self) -> None:
        """Test that BaseIndexer.test_connection is abstract."""

        # Create a class that doesn't implement test_connection
        class IncompleteIndexer(BaseIndexer):  # type: ignore[abstract]
            def search(
                self,
                query: str,
                title: str | None = None,
                author: str | None = None,
                isbn: str | None = None,
                max_results: int = 100,
            ) -> list:  # type: ignore[return,override,misc]
                return []  # type: ignore[return-value]

        with pytest.raises(TypeError):
            _ = IncompleteIndexer(settings=IndexerSettings(base_url="https://test.com"))

    def test_base_indexer_search_implementation(
        self, mock_indexer: MockIndexer
    ) -> None:
        """Test BaseIndexer search implementation."""
        results = mock_indexer.search("test query")
        assert len(results) == 1
        assert results[0].title == "Result for test query"

    def test_base_indexer_test_connection_implementation(
        self, mock_indexer: MockIndexer
    ) -> None:
        """Test BaseIndexer test_connection implementation."""
        assert mock_indexer.test_connection() is True


class TestBaseDownloadClient:
    """Test BaseDownloadClient abstract base class."""

    def test_base_download_client_is_abstract(self) -> None:
        """Test that BaseDownloadClient is abstract and cannot be instantiated."""
        assert issubclass(BaseDownloadClient, ABC)
        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        with pytest.raises(TypeError):
            _ = BaseDownloadClient(
                settings=DownloadClientSettings(host="localhost", port=8080),
                file_fetcher=file_fetcher,
                url_router=url_router,
            )

    def test_base_download_client_init(
        self,
        download_client_settings: DownloadClientSettings,
        mock_download_client: MockDownloadClient,
    ) -> None:
        """Test BaseDownloadClient initialization."""
        assert mock_download_client.settings == download_client_settings
        assert mock_download_client.enabled is True

    def test_base_download_client_init_disabled(
        self, download_client_settings: DownloadClientSettings
    ) -> None:
        """Test BaseDownloadClient initialization with disabled=True."""
        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        client = MockDownloadClient(
            settings=download_client_settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            enabled=False,
        )
        assert client.enabled is False

    def test_base_download_client_is_enabled(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient is_enabled method."""
        assert mock_download_client.is_enabled() is True

        mock_download_client.set_enabled(False)
        assert mock_download_client.is_enabled() is False

    def test_base_download_client_set_enabled(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient set_enabled method."""
        mock_download_client.set_enabled(False)
        assert mock_download_client.enabled is False

        mock_download_client.set_enabled(True)
        assert mock_download_client.enabled is True

    def test_base_download_client_add_download_abstract(self) -> None:
        """Test that BaseDownloadClient.add_download is abstract."""

        # Create a class that doesn't implement add_download
        class IncompleteClient(BaseDownloadClient):  # type: ignore[abstract]
            def get_items(
                self,
            ) -> list[dict[str, str | int | float | None]]:  # type: ignore[override]
                return []

            def remove_item(
                self, client_item_id: str, delete_files: bool = False
            ) -> bool:  # type: ignore[override]
                return True

            def test_connection(self) -> bool:  # type: ignore[override]
                return True

        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        with pytest.raises(TypeError):
            _ = IncompleteClient(
                settings=DownloadClientSettings(host="localhost", port=8080),
                file_fetcher=file_fetcher,
                url_router=url_router,
            )

    def test_base_download_client_get_items_abstract(self) -> None:
        """Test that BaseDownloadClient.get_items is abstract."""

        # Create a class that doesn't implement get_items
        class IncompleteClient(BaseDownloadClient):  # type: ignore[abstract]
            def add_download(
                self,
                download_url: str,
                title: str | None = None,
                category: str | None = None,
                download_path: str | None = None,
            ) -> str:  # type: ignore[override]
                return "item-id"

            def remove_item(
                self, client_item_id: str, delete_files: bool = False
            ) -> bool:  # type: ignore[override]
                return True

            def test_connection(self) -> bool:
                return True

        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        with pytest.raises(TypeError):
            _ = IncompleteClient(
                settings=DownloadClientSettings(host="localhost", port=8080),
                file_fetcher=file_fetcher,
                url_router=url_router,
            )

    def test_base_download_client_remove_item_abstract(self) -> None:
        """Test that BaseDownloadClient.remove_item is abstract."""

        # Create a class that doesn't implement remove_item
        class IncompleteClient(BaseDownloadClient):  # type: ignore[abstract]
            def add_download(
                self,
                download_url: str,
                title: str | None = None,
                category: str | None = None,
                download_path: str | None = None,
            ) -> str:  # type: ignore[override]
                return "item-id"

            def get_items(
                self,
            ) -> list[dict[str, str | int | float | None]]:  # type: ignore[override]
                return []

            def test_connection(self) -> bool:
                return True

        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        with pytest.raises(TypeError):
            _ = IncompleteClient(
                settings=DownloadClientSettings(host="localhost", port=8080),
                file_fetcher=file_fetcher,
                url_router=url_router,
            )

    def test_base_download_client_test_connection_abstract(self) -> None:
        """Test that BaseDownloadClient.test_connection is abstract."""

        # Create a class that doesn't implement test_connection
        class IncompleteClient(BaseDownloadClient):  # type: ignore[abstract]
            def add_download(
                self,
                download_url: str,
                title: str | None = None,
                category: str | None = None,
                download_path: str | None = None,
            ) -> str:  # type: ignore[override]
                return "item-id"

            def get_items(
                self,
            ) -> list[dict[str, str | int | float | None]]:  # type: ignore[override]
                return []

            def remove_item(
                self, client_item_id: str, delete_files: bool = False
            ) -> bool:  # type: ignore[override]
                return True

        from bookcard.pvr.services.file_fetcher import FileFetcher
        from bookcard.pvr.utils.url_router import DownloadUrlRouter

        file_fetcher = FileFetcher(timeout=30)
        url_router = DownloadUrlRouter()
        with pytest.raises(TypeError):
            _ = IncompleteClient(
                settings=DownloadClientSettings(host="localhost", port=8080),
                file_fetcher=file_fetcher,
                url_router=url_router,
            )

    def test_base_download_client_add_download_implementation(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient add_download implementation."""
        item_id = mock_download_client.add_download(
            "https://example.com/torrent.torrent"
        )
        assert item_id == "mock-item-id-123"

    def test_base_download_client_get_items_implementation(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient get_items implementation."""
        items = mock_download_client.get_items()
        assert len(items) == 1
        assert items[0]["client_item_id"] == "item-1"
        assert items[0]["status"] == "downloading"

    def test_base_download_client_remove_item_implementation(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient remove_item implementation."""
        result = mock_download_client.remove_item("item-1", delete_files=False)
        assert result is True

    def test_base_download_client_test_connection_implementation(
        self, mock_download_client: MockDownloadClient
    ) -> None:
        """Test BaseDownloadClient test_connection implementation."""
        assert mock_download_client.test_connection() is True


class TestPVRProviderExceptions:
    """Test PVR provider exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            PVRProviderError,
            PVRProviderNetworkError,
            PVRProviderParseError,
            PVRProviderTimeoutError,
            PVRProviderAuthenticationError,
        ],
    )
    def test_exception_inheritance(self, exception_class: type[Exception]) -> None:
        """Test that all PVR exceptions inherit from PVRProviderError."""
        assert issubclass(exception_class, PVRProviderError)
        assert issubclass(exception_class, Exception)

    @pytest.mark.parametrize(
        ("exception_class", "message"),
        [
            (PVRProviderError, "Generic error"),
            (PVRProviderNetworkError, "Network error"),
            (PVRProviderParseError, "Parse error"),
            (PVRProviderTimeoutError, "Timeout error"),
            (PVRProviderAuthenticationError, "Auth error"),
        ],
    )
    def test_exception_creation(
        self, exception_class: type[Exception], message: str
    ) -> None:
        """Test that exceptions can be created with messages."""
        exc = exception_class(message)
        assert str(exc) == message
        assert isinstance(exc, PVRProviderError)


class TestUtilityFunctions:
    """Test utility functions for raising exceptions and handling errors."""

    @pytest.mark.parametrize(
        (
            "error_code",
            "description",
            "provider_name",
            "expected_exception",
            "expected_message",
        ),
        [
            (
                100,
                "Invalid API key",
                "Indexer",
                PVRProviderAuthenticationError,
                "Invalid API key: Invalid API key",
            ),
            (
                150,
                "Auth error",
                "Indexer",
                PVRProviderAuthenticationError,
                "Invalid API key: Auth error",
            ),
            (
                199,
                "Token expired",
                "Indexer",
                PVRProviderAuthenticationError,
                "Invalid API key: Token expired",
            ),
            (
                200,
                "Request limit reached",
                "Indexer",
                PVRProviderError,
                "API limit reached: Request limit reached",
            ),
            (
                200,
                "Other error",
                "Indexer",
                PVRProviderError,
                "Indexer error: Other error",
            ),
            (
                500,
                "Server error",
                "DownloadClient",
                PVRProviderError,
                "DownloadClient error: Server error",
            ),
        ],
    )
    def test_handle_api_error_response(
        self,
        error_code: int,
        description: str,
        provider_name: str,
        expected_exception: type[Exception],
        expected_message: str,
    ) -> None:
        """Test handle_api_error_response function."""
        with pytest.raises(expected_exception, match=expected_message):
            handle_api_error_response(error_code, description, provider_name)

    @pytest.mark.parametrize(
        ("status_code", "response_text", "expected_exception", "expected_message"),
        [
            (401, "", PVRProviderAuthenticationError, "Unauthorized"),
            (403, "", PVRProviderAuthenticationError, "Forbidden"),
            (400, "Bad Request", PVRProviderNetworkError, "HTTP 400: Bad Request"),
            (404, "Not Found", PVRProviderNetworkError, "HTTP 404: Not Found"),
            (
                500,
                "Internal Server Error",
                PVRProviderNetworkError,
                "HTTP 500: Internal Server Error",
            ),
            (400, "A" * 300, PVRProviderNetworkError, "HTTP 400: " + "A" * 200),
        ],
    )
    def test_handle_http_error_response(
        self,
        status_code: int,
        response_text: str,
        expected_exception: type[Exception],
        expected_message: str,
    ) -> None:
        """Test handle_http_error_response function."""
        with pytest.raises(expected_exception, match=expected_message):
            handle_http_error_response(status_code, response_text)
